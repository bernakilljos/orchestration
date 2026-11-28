"""Phase 17 회귀 (2026-11-02 · 24h 운영 보고서 결함 4건) — 실 DB·실 ledger·실 Agent·유료 API 사용 X.

1. commit(가상 메모리) 부족 → 신규 sandbox·Agent 시작 보류 (retryable) · 10분 루프는 WinError 1455 로 죽지 않고 단계 실패로 기록
2. 10분 루프 subprocess 출력 utf-8 디코딩 (cp949 UnicodeDecodeError 144회) · 하위 명령 실패를 0 으로 숨기지 않음
3. 사용량 미측정 = cost NULL(UNKNOWN) · 측정된 0 비용은 0 · 예전 0/0/0 행은 DB 수정 없이 집계에서만 미측정
4. approval_required(사용자 승인 대기) 는 Stop 을 막지 않음 · stop_hook_active 무한 차단 해소 · 실제 미완료는 계속 차단
"""
import ast
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / ".claude" / "scripts" / "lib"
sys.path.insert(0, str(LIB))
import repair_sandbox as sb  # noqa: E402

LOW = {"measured": True, "used_gb": 19.5, "limit_gb": 19.7, "free_gb": 0.2, "percent": 99.0}
OK = {"measured": True, "used_gb": 10.0, "limit_gb": 20.0, "free_gb": 10.0, "percent": 50.0}
POL = {"min_commit_free_gb": 2, "max_commit_percent": 90}


# ---------- 1. commit 메모리 ----------

def test_commit_memory_measures_real_machine():
    cm = sb.commit_memory()
    if not cm.get("measured"):
        pytest.skip(f"commit 측정 불가 환경: {cm}")
    assert 0 < cm["used_gb"] <= cm["limit_gb"] and 0 <= cm["percent"] <= 100


def test_memory_gate_low_ok_unknown():
    low = sb.memory_gate(POL, LOW)
    assert low and low["ok"] is False and low["retryable"] and low["deferred"] and "commit" in low["reason"]
    assert sb.memory_gate(POL, OK) is None
    assert sb.memory_gate(POL, {"measured": False, "reason": "x"}) is None   # 측정 불가 = 막지 않음


def test_sandbox_create_deferred_on_low_commit(monkeypatch):
    sb.use_test_root()
    monkeypatch.setattr(sb, "commit_memory", lambda: LOW)
    gid = f"p17-mem-{time.time_ns()}"
    r = sb.create(gid)
    assert r["ok"] is False and r["retryable"] and r.get("deferred")
    assert not (sb.SANDBOX_ROOT / gid).exists()      # worktree 를 만들지 않았다


def test_agent_dispatch_deferred_without_launch(monkeypatch):
    import real_repair_chain as rc
    monkeypatch.setattr(sb, "commit_memory", lambda: LOW)

    def boom(*a, **k):
        raise AssertionError("commit 부족인데 Agent 프로세스를 띄웠다")
    monkeypatch.setattr(rc.subprocess, "run", boom)
    r = rc.dispatch_agent("x", str(ROOT), "haiku", ["Read"], role="p17")
    assert r["ok"] is False and r["deferred"] and r["retryable"]


def test_dag_deferred_is_skipped_not_failed():
    import agent_registry as ar
    deferred = lambda *a, **k: {"ok": False, "deferred": True, "retryable": True, "error": "commit 부족"}
    out = ar.run_dag([{"id": "t1", "needs": ["read"], "prompt": "p"}], str(ROOT), max_parallel=1, dispatch=deferred)
    assert out["results"]["t1"]["status"] == "skipped" and out["results"]["t1"]["deferred"]
    assert out["metrics"]["failed"] == 0 and out["metrics"]["deferred"] == 1


# ---------- 1·2. 10분 루프 ----------

def _load_loop(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("orca_loop_p17", ROOT / ".claude" / "scripts" / "orca-10min-loop.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setattr(m, "LOG_FILE", tmp_path / "loop.log")
    monkeypatch.setattr(m, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(m, "STATE_DIR", tmp_path)
    monkeypatch.setattr(m, "DRY_RUN", False)
    monkeypatch.setattr(m, "optimize_orca_db", lambda: True)
    monkeypatch.setattr(m, "run_cleanup_pollution", lambda: True)
    monkeypatch.setattr(m, "detect_idle_sessions", lambda: [])
    return m


def test_loop_survives_winerror_1455_and_reports_failure(tmp_path, monkeypatch):
    m = _load_loop(tmp_path, monkeypatch)
    calls = []

    def reap():
        raise OSError(22, "페이징 파일이 너무 작습니다", None, 1455)
    monkeypatch.setattr(m, "reap_stuck_orphans", reap)
    monkeypatch.setattr(m.subprocess, "run",
                        lambda argv, **k: calls.append(argv) or subprocess.CompletedProcess(argv, 0, "ok", ""))
    rc = m.main()
    assert rc == 2                                     # 성공(0)으로 숨기지 않음
    assert len(calls) == 3                             # 이후 단계(to-goals·advance-all·heal-tick)는 계속 실행
    st = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert any("reap_stuck_orphans" in s for s in st["step_failures"])
    assert "commit" in st["metrics"]


def test_loop_substep_nonzero_rc_not_masked(tmp_path, monkeypatch):
    m = _load_loop(tmp_path, monkeypatch)
    monkeypatch.setattr(m, "reap_stuck_orphans", lambda: 0)
    monkeypatch.setattr(m.subprocess, "run",
                        lambda argv, **k: subprocess.CompletedProcess(argv, 3 if "advance-all" in argv else 0, "", "에러 원문"))
    assert m.main() == 2
    log = (tmp_path / "loop.log").read_text(encoding="utf-8")
    assert "advance-all FAIL rc=3" in log and "에러 원문" in log


def test_loop_low_commit_alert(tmp_path, monkeypatch):
    m = _load_loop(tmp_path, monkeypatch)
    monkeypatch.setattr(m, "reap_stuck_orphans", lambda: 0)
    monkeypatch.setattr(m.subprocess, "run", lambda argv, **k: subprocess.CompletedProcess(argv, 0, "", ""))
    monkeypatch.setattr(sb, "commit_memory", lambda: LOW)
    monkeypatch.setattr(sb, "_policy", lambda: POL)
    assert m.main() == 0                               # 경고는 실패가 아님
    st = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert any(a.startswith("COMMIT LOW") for a in st["alerts"])


def test_loop_all_subprocess_calls_decode_utf8():
    tree = ast.parse((ROOT / ".claude" / "scripts" / "orca-10min-loop.py").read_text(encoding="utf-8"))
    runs = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "run"
            and getattr(n.func.value, "id", "") == "subprocess"]
    assert len(runs) == 4
    for n in runs:
        kw = {k.arg: k.value for k in n.keywords}
        assert getattr(kw.get("encoding"), "value", None) == "utf-8", f"line {n.lineno}"


def test_utf8_decode_keeps_korean_bad_bytes_and_rc():
    child = ("import sys;sys.stdout.buffer.write('한글 ✓ '.encode('utf-8')+b'\\xe2\\x28\\xa1');"
             "sys.stderr.buffer.write('실패 원문'.encode('utf-8'));sys.exit(5)")
    r = subprocess.run([sys.executable, "-c", child], capture_output=True, text=True,
                       encoding="utf-8", errors="backslashreplace", timeout=30)
    assert r.returncode == 5 and "한글 ✓" in r.stdout and "\\xe2" in r.stdout and r.stderr == "실패 원문"


# ---------- 3. 비용 관측 ----------

def _tmp_db(tmp_path):
    env = {**os.environ, "ORCHESTRATION_ROOT": str(tmp_path), "PYTHONUTF8": "1"}
    subprocess.run([sys.executable, "-c", f"import sys;sys.path.insert(0,{str(LIB)!r});import state_db;state_db.init_schema()"],
                   env=env, check=True, timeout=60)
    return env, tmp_path / ".claude" / "state" / "orca.db"


def test_usage_unknown_records_null_and_no_spend(tmp_path):
    env, db = _tmp_db(tmp_path)
    out = subprocess.run([sys.executable, str(LIB / "record_call.py"), "--ai", "claude", "--model", "subagent-x",
                          "--usage-unknown", "--latency-ms", "10", "--success", "1"],
                         env=env, capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert out.returncode == 0 and "cost=UNKNOWN" in out.stdout
    with sqlite3.connect(str(db)) as c:
        assert c.execute("SELECT cost_usd FROM metrics").fetchall() == [(None,)]
        assert c.execute("SELECT today_spent_usd FROM budget").fetchone()[0] in (0, 0.0, None)


def test_ops_metrics_measured_vs_unknown(tmp_path, monkeypatch):
    import ops_metrics
    _, db = _tmp_db(tmp_path)
    now = int(time.time())
    with sqlite3.connect(str(db)) as c:
        rows = [("a", "agent", 100, 50, 0.0, now),     # 측정된 0 비용 (토큰 있음) → 0
                ("b", "agent", 200, 0, 0.25, now),     # 측정
                ("c", "agent", 0, 0, None, now),       # UNKNOWN (NULL)
                ("d", "legacy", 0, 0, 0.0, now)]       # 예전 hook 0/0/0 → 미측정 (DB 는 그대로)
        c.executemany("INSERT INTO metrics (task_id, ai, tokens_in, tokens_out, cost_usd, recorded_at, model_id, "
                      "latency_ms, success, cache_hit) VALUES (?,?,?,?,?,?,'m',1,1,0)", rows)
    monkeypatch.setattr(ops_metrics, "DB", db)
    tc = ops_metrics.report(1)["tokens_cost"]
    assert tc["agent"]["cost_usd"] == 0.25 and tc["agent"]["tokens_in"] == 300
    assert tc["agent"]["measured_calls"] == 2 and tc["agent"]["unmeasured_calls"] == 1
    assert tc["legacy"]["cost_usd"] == "UNKNOWN" and tc["legacy"]["unmeasured_calls"] == 1
    with sqlite3.connect(str(db)) as c:          # 기존 0 기록은 수정하지 않았다
        assert c.execute("SELECT cost_usd FROM metrics WHERE task_id='d'").fetchone()[0] == 0.0


# ---------- 4. Stop gate ----------

def _gate(tmp_path, reqs, payload=None):
    st = tmp_path / ".claude" / "state"
    st.mkdir(parents=True, exist_ok=True)
    (st / "request-ledger.json").write_text(json.dumps({"session_id": "s1", "requests": reqs}, ensure_ascii=False),
                                            encoding="utf-8")
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path), "PYTHONUTF8": "1"}
    return subprocess.run([sys.executable, str(ROOT / ".claude" / "scripts" / "request-ledger.py"), "gate"],
                          input=json.dumps(payload) if payload is not None else "", env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=60)


def _r(rid, status):
    return {"id": rid, "desc": f"{rid} desc", "status": status}


def test_gate_approval_required_does_not_block(tmp_path):
    r = _gate(tmp_path, [_r("R1", "completed"), _r("R2", "approval_required")], {"session_id": "s1"})
    assert r.returncode == 0 and "R2" in r.stderr                  # 알리되 막지 않음
    led = json.loads((tmp_path / ".claude/state/request-ledger.json").read_text(encoding="utf-8"))
    assert led["requests"][1]["status"] == "approval_required"     # 완료 처리하지 않음


def test_gate_still_blocks_real_pending(tmp_path):
    r = _gate(tmp_path, [_r("R1", "pending"), _r("R2", "approval_required")], {"session_id": "s1"})
    assert r.returncode == 2 and "R1" in r.stderr


def test_gate_breaks_stop_hook_active_loop_but_resets_on_progress(tmp_path):
    reqs = [_r("R1", "pending")]
    assert _gate(tmp_path, reqs, {"session_id": "s1", "stop_hook_active": False}).returncode == 2
    assert _gate(tmp_path, reqs, {"session_id": "s1", "stop_hook_active": True}).returncode == 2
    assert _gate(tmp_path, reqs, {"session_id": "s1", "stop_hook_active": True}).returncode == 2
    last = _gate(tmp_path, reqs, {"session_id": "s1", "stop_hook_active": True})
    assert last.returncode == 0 and "loop" in last.stderr          # 진전 없는 4번째 → 통과
    assert (tmp_path / ".claude/logs/stop-gate-loop.log").exists()
    # 진전(상태 변경)이 있으면 카운터 초기화 → 다시 막는다
    assert _gate(tmp_path, [_r("R1", "implemented")], {"session_id": "s1", "stop_hook_active": True}).returncode == 2


def test_r371_c2_released_loop_not_rearmed_next_turn(tmp_path):
    """R364 D6: 반복 해제 뒤 다음 턴(stop_hook_active 없음) 같은 미완료로 다시 3회 막지 않는다 · 진전·새 세션은 다시 막음."""
    reqs = [_r("R1", "pending")]
    assert _gate(tmp_path, reqs, {"session_id": "s1"}).returncode == 2
    for _ in range(2):
        assert _gate(tmp_path, reqs, {"session_id": "s1", "stop_hook_active": True}).returncode == 2
    assert _gate(tmp_path, reqs, {"session_id": "s1", "stop_hook_active": True}).returncode == 0   # 해제
    assert _gate(tmp_path, reqs, {"session_id": "s1"}).returncode == 0                            # 다음 턴: 재차단 X
    assert _gate(tmp_path, [_r("R1", "implemented")], {"session_id": "s1"}).returncode == 2        # 진전 → 다시 막음
    assert _gate(tmp_path, reqs, {"session_id": "s2"}).returncode == 2                            # 새 세션 → 다시 막음


def test_gate_without_stop_hook_active_always_blocks(tmp_path):
    for _ in range(6):
        assert _gate(tmp_path, [_r("R1", "pending")], {"session_id": "s1"}).returncode == 2


def test_six_guards_does_not_rerun_ledger_gate():
    txt = (ROOT / ".claude" / "hooks" / "stop-six-guards.sh").read_text(encoding="utf-8")
    assert "stop-request-ledger-gate.sh" in txt and "</dev/null" in txt
    hook = (ROOT / ".claude" / "hooks" / "stop-request-ledger-gate.sh").read_text(encoding="utf-8")
    assert "gate 2>/dev/null" not in hook


def test_gate_ignores_other_sessions_pending(tmp_path):
    """2026-11-18: 다른 세션이 남긴 옛 미완료로 이 세션 Stop 이 매 회차 막혔다 — 남의 것은 안 막고 자기 것·세션 없는 것은 막는다."""
    other = dict(_r("R1", "pending"), session_id="s-old")
    mine = dict(_r("R2", "pending"), session_id="s1")
    assert _gate(tmp_path, [other, _r("R3", "completed")], {"session_id": "s1"}).returncode == 0
    assert _gate(tmp_path, [other, mine], {"session_id": "s1"}).returncode == 2
    assert _gate(tmp_path, [other], {}).returncode == 2          # 세션 id 를 못 받으면 종전대로 전체


def test_r356_six_guards_golden_runs_in_background_unless_block_flag(tmp_path):
    """R356: 골든 시험(0.8초)+지문(0.4초)+supervisor(0.2초)가 응답마다 Stop 을 동기로 붙잡던 것 (11-23 실측 six-guards ≈1.6초)
    → 골든은 기본이 경고 전용이라 백그라운드 갱신 + 직전 결과로 경고 · 차단 플래그가 있으면 종전대로 동기 실행·차단."""
    import shutil
    import time
    (tmp_path / "plugins").mkdir()
    for d in (".claude/hooks", ".claude/scripts/lib", ".claude/state", ".claude/logs"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / ".claude/hooks/stop-six-guards.sh", tmp_path / ".claude/hooks/stop-six-guards.sh")
    (tmp_path / ".claude/settings.json").write_text('{"x":"stop-request-ledger-gate.sh stop-standing-gate.sh"}', encoding="utf-8")
    (tmp_path / ".claude/scripts/golden-test.py").write_text(
        "import time,sys\ntime.sleep(3)\nprint('총 1/2 PASS')\n", encoding="utf-8")
    (tmp_path / ".claude/scripts/lib/supervisor.py").write_text("import time\ntime.sleep(2)\n", encoding="utf-8")
    for a in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", "-C", str(tmp_path), *a], check=True)
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path), "PYTHONUTF8": "1"}
    bash = shutil.which("bash") or "bash"

    def hook():
        t = time.time()
        r = subprocess.run([bash, str(tmp_path / ".claude/hooks/stop-six-guards.sh")], input="{}", capture_output=True,
                           text=True, encoding="utf-8", env=env, timeout=60, cwd=tmp_path)
        return r, time.time() - t
    r, dt = hook()
    assert r.returncode == 0 and dt < 2.5, (dt, r.stderr)                   # 3초 골든·2초 supervisor 를 기다리지 않음
    cache = tmp_path / ".claude/state/six-guards-golden.txt"
    for _ in range(40):
        if cache.exists() and "1/2" in cache.read_text(encoding="utf-8"):
            break
        time.sleep(0.25)
    assert "1/2" in cache.read_text(encoding="utf-8")                       # 백그라운드가 결과를 남김
    r, _ = hook()
    assert r.returncode == 0 and "Golden Test 1/2" in r.stderr               # 직전 결과로 경고 (차단 X)
    (tmp_path / ".claude/state/golden-test.block-on-fail").write_text("", encoding="utf-8")
    cache.unlink()
    r, dt = hook()
    assert r.returncode == 2 and "block-on-fail" in r.stderr and dt >= 3     # 차단 플래그 = 동기 실행·차단 (종전 계약)


def test_r356_standing_gate_parallel_checks_and_shell_path_parse(tmp_path):
    """R356: gate·lang-check 동시 실행(종료 코드·출력 순서 종전과 같음) · transcript_path 를 python 없이 셸로 추출
    (공백·백슬래시 든 Windows 경로가 그대로 전달돼야 함)."""
    import shutil
    import time
    (tmp_path / "plugins").mkdir()
    (tmp_path / ".claude/hooks").mkdir(parents=True)
    (tmp_path / ".claude/scripts").mkdir()
    shutil.copy(ROOT / ".claude/hooks/stop-standing-gate.sh", tmp_path / ".claude/hooks/stop-standing-gate.sh")
    rec = tmp_path / "qsc.txt"
    (tmp_path / ".claude/scripts/standing-requirements.py").write_text(
        "import sys,time,os\nop=sys.argv[1]\nsys.stdin.read()\ntime.sleep(3)\n"
        "print(op+'-out')\nprint(op+'-err',file=sys.stderr)\n"
        "sys.exit(int(os.environ.get('RC_'+op.replace('-','_').upper(),'0')))\n", encoding="utf-8")
    (tmp_path / ".claude/scripts/quality-self-check.py").write_text(
        f"import sys\nopen(r'{rec}','w',encoding='utf-8').write(sys.argv[2])\n", encoding="utf-8")
    bash = shutil.which("bash") or "bash"
    path = r"C:\Users\u x\.claude\projects\p q\s.jsonl"

    def hook(**rc):
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path), "PYTHONUTF8": "1", **rc}
        t = time.time()
        r = subprocess.run([bash, str(tmp_path / ".claude/hooks/stop-standing-gate.sh")],
                           input=json.dumps({"transcript_path": path, "stop_hook_active": False}),
                           capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)
        return r, time.time() - t
    r, dt = hook()
    assert r.returncode == 0 and dt < 5.0, dt                                       # 3초 검사 2개가 동시에 (순차면 6초+ · 부하 여유 1초+)
    assert r.stdout.split() == ["gate-out", "lang-check-out"] and r.stderr.split() == ["gate-err", "lang-check-err"]
    for _ in range(150):
        if rec.exists():
            break
        time.sleep(0.1)
    assert rec.read_text(encoding="utf-8") == path                                 # 셸 추출 경로 = 원래 경로
    assert hook(RC_GATE="2")[0].returncode == 2                                    # gate 차단 그대로
    assert hook(RC_LANG_CHECK="1")[0].returncode == 2                              # 언어 검사 실패 = 2 (종전 계약)


# ---------- R357: Edit 마다 뜨던 훅 프로세스 줄이기 (판정·기록은 같게) ----------
def _tool_mod(name, monkeypatch, proj):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(proj))
    sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "prompt"))
    spec = importlib.util.spec_from_file_location("r357_" + name, ROOT / ".claude" / "hooks" / "tool" / (name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    from _common import Ctx
    return m, Ctx


@pytest.mark.parametrize("path,smoke,index", [
    (r"C:\x\.claude\rules\a.md", False, True),          # 역슬래시 경로 (index-rule-on-edit 시험과 같은 사례 · 입력은 json.dumps)
    (r"C:\x\\.claude\rules\a.md", False, True),         # 연속 구분자 → 하나로
    ("C:/x/.claude/rules/a.md", False, True),
    ("C:/x/CLAUDE.md", False, True),
    ("C:/u/memory/m.md", False, True),
    (r"C:\x\guide.txt", False, False),
    ("C:/app/UserController.java", True, False),
    ("C:/app/api/router_v1.py", True, False),
    ("C:/app/page.vue", True, False),
    ("C:/app/Page.VUE", False, False),                             # 원본 case 는 대소문자 구분
    ("C:/app/util.py", False, False),
])
def test_r357_post_edit_bg_same_filters_and_detaches(tmp_path, monkeypatch, path, smoke, index):
    """R357: auto-smoke-test.sh · index-rule-on-edit.sh (Edit 마다 bash 2벌) → 디스패처 안 판정 · 대상일 때만 분리 실행."""
    (tmp_path / "plugins").mkdir()
    (tmp_path / ".claude" / "scripts").mkdir(parents=True)
    (tmp_path / ".claude" / "logs").mkdir()
    (tmp_path / ".claude" / "state").mkdir()
    mi, ms = tmp_path / "rebuilt.txt", tmp_path / "smoked.txt"
    (tmp_path / ".claude" / "scripts" / "lookup-rule.py").write_text(
        "import pathlib,os\npathlib.Path(%r).write_text(os.environ.get('RULE_INDEX_ACTIVE',''))\n" % str(mi), encoding="utf-8")
    (tmp_path / ".claude" / "scripts" / "smoke-test-screen.sh").write_text(
        '#!/usr/bin/env bash\nprintf "%%s|%%s" "$1" "$SMOKE_TEST_ACTIVE" > "%s"\n' % ms.as_posix(), encoding="utf-8")
    (tmp_path / ".claude" / "state" / "python-path.txt").write_text(sys.executable, encoding="utf-8")
    monkeypatch.delenv("RULE_INDEX_ACTIVE", raising=False)
    monkeypatch.delenv("SMOKE_TEST_ACTIVE", raising=False)
    m, Ctx = _tool_mod("post_edit_bg", monkeypatch, tmp_path)
    ctx = Ctx(json.dumps({"tool_name": "Edit", "tool_input": {"file_path": path}}))
    assert m.run(ctx) is None                                      # 결과는 로그 전용 — 디스패처 출력 없음
    for _ in range(80):
        if mi.exists() == index and ms.exists() == smoke:
            break
        time.sleep(0.1)
    time.sleep(0.3)
    assert mi.exists() == index and ms.exists() == smoke
    if index:
        assert mi.read_text() == "1"                               # 재귀 가드 환경 변수 전달
    if smoke:
        assert ms.read_text().endswith("|1") and "\\" not in ms.read_text()   # 경로 / 정규화 · 가드 전달


def test_r357_post_edit_bg_respects_recursion_guard(tmp_path, monkeypatch):
    (tmp_path / ".claude" / "scripts").mkdir(parents=True)
    mi = tmp_path / "rebuilt.txt"
    (tmp_path / ".claude" / "scripts" / "lookup-rule.py").write_text(
        "import pathlib\npathlib.Path(%r).write_text('x')\n" % str(mi), encoding="utf-8")
    monkeypatch.setenv("RULE_INDEX_ACTIVE", "1")
    m, Ctx = _tool_mod("post_edit_bg", monkeypatch, tmp_path)
    m.run(Ctx('{"tool_name":"Edit","tool_input":{"file_path":"C:/x/.claude/rules/a.md"}}'))
    time.sleep(1.0)
    assert not mi.exists()


def test_r357_post_edit_ping_pong_in_process_keeps_korean(tmp_path, monkeypatch):
    """R357: post-edit-ping-pong.sh (동기 · bash 1 + python 3) → 디스패처 안 record · 종전 셸 경로는 한국어 미리보기를 깨뜨려 저장했다."""
    import shutil
    (tmp_path / "plugins").mkdir()
    (tmp_path / ".claude" / "scripts").mkdir(parents=True)
    (tmp_path / ".claude" / "state").mkdir()
    (tmp_path / ".claude" / "logs").mkdir()
    shutil.copy(ROOT / ".claude" / "scripts" / "anti-ping-pong.py", tmp_path / ".claude" / "scripts" / "anti-ping-pong.py")
    monkeypatch.setenv("CLAUDE_SESSION_ID", "sess-r357")
    m, Ctx = _tool_mod("post_edit_ping_pong", monkeypatch, tmp_path)
    pl = {"tool_name": "Edit", "tool_input": {"file_path": "C:/x/a.py", "new_string": "한글 수정\n" + "x" * 300}}
    assert m.run(Ctx(json.dumps(pl, ensure_ascii=False))) is None
    assert m.run(Ctx(json.dumps(pl, ensure_ascii=False))) is None
    c = sqlite3.connect(str(tmp_path / ".claude" / "state" / "orca.db"))
    rows = c.execute("select path, session_id, diff_preview from ping_pong_tracker").fetchall()
    c.close()
    assert len(rows) == 2 and rows[0] == ("C:/x/a.py", "sess-r357", ("한글 수정\n" + "x" * 300)[:200])
    assert m.run(Ctx('{"tool_name":"Edit","tool_input":{}}')) is None   # 경로 없음 = 기록 안 함


def test_r357_post_impl_verify_skips_unrelated_edit_and_batches(tmp_path):
    """R357: post-impl-verify.sh 가 Edit 마다 변경 파일 전체를 다시 검사 (kit 실측 3.7초) →
    검사 대상 종류가 아닌 파일 수정이면 바로 끝 · 대상이면 종전과 같은 문구·순서 (파일마다 띄우던 python·file·grep 은 한 번씩)."""
    sh = ROOT / "plugins" / "review_qa" / "hooks" / "post-impl-verify.sh"
    r = tmp_path / "repo"
    r.mkdir()
    g = lambda *a: subprocess.run(["git", *a], cwd=r, capture_output=True)   # noqa: E731
    g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
    (r / "base.py").write_text("x=1\n"); g("add", "."); g("commit", "-qm", "i")
    (r / "base.py").write_text("x=2\n"); g("commit", "-qam", "c")
    (r / "good.py").write_text("ok=1\n")
    (r / "bad.py").write_text("def (:\n")
    (r / "sp ace.py").write_text("def (:\n")
    (r / "u16.md").write_bytes("한글".encode("utf-16"))
    (r / "fine.md").write_text("fine\n")
    sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "prompt"))
    from _common import bash_exe  # noqa: E402

    def run(inp):
        p = subprocess.run([bash_exe(), str(sh)], input=inp.encode(), cwd=r, capture_output=True, timeout=120)
        return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")
    rc, out = run('{"tool_input":{"file_path":"C:\\x\\a.json"}}')
    assert (rc, out) == (0, "")                                    # 대상 아님 = 바로 끝
    want = ["[VERIFY FAIL] Python syntax error: bad.py", "[VERIFY FAIL] Python syntax error: sp ace.py",
            "[VERIFY FAIL] Wrong encoding (not UTF-8): u16.md", "[VERIFY] 3 errors found — task NOT complete"]
    for inp in ('{"tool_input":{"file_path":"C:\\x\\a.PY"}}', "{}", ""):
        rc, out = run(inp)
        assert rc == 2 and [l for l in out.splitlines() if l.strip()] == want, (inp, out)


def test_r357_settings_edit_hooks_folded_into_dispatcher():
    s = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    cmds = [h["command"] for ev in s["hooks"].values() for g in ev for h in g["hooks"]]
    for gone in ("post-edit-ping-pong.sh", "auto-smoke-test.sh", "index-rule-on-edit.sh"):
        assert not any(gone in c for c in cmds), gone
    assert not any("verify-after-edit-logger" in c and "bash -c" in c for c in cmds)   # bash 한 겹 제거
    src = (ROOT / ".claude" / "hooks" / "tool-dispatch.py").read_text(encoding="utf-8")
    assert '"post_edit_ping_pong", "Edit|Write|MultiEdit"' in src and '"post_edit_bg", "Edit|Write"' in src


def _mdl():
    spec = importlib.util.spec_from_file_location("mdl_r357", ROOT / ".claude" / "scripts" / "mcp-direct-launch.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_r357_mcp_direct_parse_and_entry(tmp_path):
    """R357: cmd /c npx -y <패키지> 등록 → 패키지·나머지 인자 해석 · package.json bin 으로 진입 파일 (npx 캐시 해시 폴더는 쓰지 않음)."""
    m = _mdl()
    P = m.parse_npx
    assert P({"command": "cmd", "args": ["/c", "npx", "-y", "@playwright/mcp"]}) == ("@playwright/mcp", "@playwright/mcp", [])
    assert P({"command": "cmd", "args": ["/c", "npx", "-y", "@canva/cli@latest", "mcp"]}) == ("@canva/cli@latest", "@canva/cli", ["mcp"])
    assert P({"command": "cmd", "args": ["/c", "npx", "pkg-a@1.2", "C:/x", "C:/y"]}) == ("pkg-a@1.2", "pkg-a", ["C:/x", "C:/y"])
    assert P({"command": "npx", "args": ["--yes", "mermaid-mcp-server"]}) == ("mermaid-mcp-server", "mermaid-mcp-server", [])
    for not_npx in ({"command": "uvx", "args": ["mcp-server-fetch"]}, {"command": "node", "args": ["x.js"]},
                    {"command": "cmd", "args": ["/c", "npx", "-y"]}, {"command": "cmd", "args": ["/c", "npx", "--flag"]}):
        assert P(not_npx) is None
    b = tmp_path / "orca-mcp"
    d = b / "node_modules" / "@canva" / "cli"
    d.mkdir(parents=True)
    (d / "cli.js").write_text("//")
    (d / "package.json").write_text('{"bin": {"canva": "./cli.js"}}')
    assert m.entry_file(b, "@canva/cli") == (d / "cli.js").resolve()
    d2 = b / "node_modules" / "mermaid-mcp-server"
    (d2 / "build").mkdir(parents=True)
    (d2 / "build" / "index.js").write_text("//")
    (d2 / "package.json").write_text('{"bin": "build/index.js"}')
    assert m.entry_file(b, "mermaid-mcp-server") == (d2 / "build" / "index.js").resolve()
    assert m.entry_file(b, "none-pkg") is None


def test_r357_mcp_direct_plan_user_and_local_scope(tmp_path, monkeypatch):
    m = _mdl()
    proj = tmp_path / "proj"
    proj.mkdir()
    cfg = {"mcpServers": {"a": {"command": "cmd", "args": ["/c", "npx", "-y", "pkg-a"]},
                          "f": {"command": "uvx", "args": ["mcp-server-fetch"]},
                          "done": {"command": "node", "args": ["C:/orca-mcp/x.js"]}},
           "projects": {str(proj).replace("\\", "/"): {"mcpServers": {"fs": {"command": "cmd", "args": ["/c", "npx", "pkg-fs", "C:/d"]}}},
                        "C:/other": {"mcpServers": {"o": {"command": "cmd", "args": ["/c", "npx", "pkg-o"]}}}}}
    (tmp_path / ".claude.json").write_text(json.dumps(cfg), encoding="utf-8")
    monkeypatch.setattr(m.Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(proj))
    got = sorted((s, n, spec, rest) for s, n, _e, spec, _p, rest in m.plan())
    assert got == [("local", "fs", "pkg-fs", ["C:/d"]), ("user", "a", "pkg-a", [])]   # uvx·이미 node·다른 프로젝트 = 제외


def _stop_kit(tmp_path):
    import shutil
    w = tmp_path / "kit"
    (w / ".claude" / "hooks").mkdir(parents=True)
    shutil.copy(ROOT / ".claude" / "hooks" / "tool-dispatch.py", w / ".claude" / "hooks" / "tool-dispatch.py")
    shutil.copytree(ROOT / ".claude" / "hooks" / "prompt", w / ".claude" / "hooks" / "prompt",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (w / ".claude" / "logs").mkdir()
    (w / "plugins").mkdir()
    spec = importlib.util.spec_from_file_location("td_r363", w / ".claude" / "hooks" / "tool-dispatch.py")
    sys.path.insert(0, str(w / ".claude" / "hooks" / "prompt"))
    td = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(td)
    return w, td


def test_r363_stop_dispatcher_blocks_runs_async_and_kills_timeout(tmp_path):
    """R363: Stop 훅 18개(각각 Git 실행기+bash+conhost) → tool-dispatch stop 1개 · 동기 3개 차단 사유(exit 2·JSON block) 설정 순서로 보존 ·
    비동기 15개는 분리 실행기가 병렬 실행(응답 안 붙잡음 · 환경 변수·인자 전달) · timeout 넘으면 종료."""
    w, td = _stop_kit(tmp_path)
    m = (tmp_path / "marks")
    m.mkdir()
    M = m.as_posix()

    def put(rel, body):
        p = w.joinpath(*rel.split("/"))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8", newline="\n")
    for name, interp, rel, args, tmo, env in td.STOP_ASYNC:
        if interp == "python":
            put(rel, "import sys\nd=sys.stdin.read()\nopen(r'%s/%s','w').write('ok:'+str(len(d)))\n" % (M, name))
        elif name == "auto-compact-check":
            put(rel, '#!/usr/bin/env bash\ncat >/dev/null\necho s > "%s/%s.start"\nsleep 25\necho d > "%s/%s"\n' % (M, name, M, name))
        else:
            put(rel, '#!/usr/bin/env bash\nd="$(cat)"\nprintf "ok|%%s|%%s|%%s" "${#d}" "${SYNC_IF_CHANGED:-}" "$*" > "%s/%s"\n' % (M, name))
    put(".claude/hooks/stop-request-ledger-gate.sh", '#!/usr/bin/env bash\ncat >/dev/null\necho "LEDGER-BLOCK 미완료" >&2\nexit 2\n')
    put(".claude/hooks/stop-standing-gate.sh", '#!/usr/bin/env bash\ncat >/dev/null\necho \'{"decision":"block","reason":"STANDING-REASON"}\'\n')
    put(".claude/hooks/stop-six-guards.sh", '#!/usr/bin/env bash\ncat >/dev/null\necho "[six-guards] WARN 참고" >&2\nexit 0\n')
    t0 = time.perf_counter()
    r = subprocess.run([sys.executable, "-X", "utf8", str(w / ".claude" / "hooks" / "tool-dispatch.py"), "stop"],
                       input=b'{"hook_event_name":"Stop","stop_hook_active":false}', capture_output=True, timeout=60)
    dt = time.perf_counter() - t0
    err = r.stderr.decode("utf-8", "replace")
    assert r.returncode == 2 and err.index("LEDGER-BLOCK") < err.index("STANDING-REASON") and "WARN 참고" not in err
    assert dt < 8                                                                   # 25초 잠드는 비동기 훅을 기다리지 않음
    names = [e[0] for e in td.STOP_ASYNC if e[0] != "auto-compact-check"]
    for _ in range(100):
        if all((m / n).exists() for n in names):
            break
        time.sleep(0.1)
    assert all((m / n).exists() for n in names), [n for n in names if not (m / n).exists()]
    assert (m / "sync-to-team").read_text().split("|")[2] == "1" and (m / "hook-08-ai-handoff").read_text().endswith("|auto")
    for _ in range(150):
        if "auto-compact-check: TIMEOUT" in ((w / ".claude" / "logs" / "tool-dispatch.log").read_text(encoding="utf-8")
                                             if (w / ".claude" / "logs" / "tool-dispatch.log").exists() else ""):
            break
        time.sleep(0.1)
    assert (m / "auto-compact-check.start").exists() and not (m / "auto-compact-check").exists()
    assert "auto-compact-check: TIMEOUT" in (w / ".claude" / "logs" / "tool-dispatch.log").read_text(encoding="utf-8")


def test_r363_stop_dispatcher_passes_when_no_block(tmp_path):
    w, td = _stop_kit(tmp_path)
    for name, interp, rel, args, tmo, env in td.STOP_SYNC + td.STOP_ASYNC:
        p = w.joinpath(*rel.split("/"))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("import sys\nsys.stdin.read()\n" if interp == "python" else "#!/usr/bin/env bash\ncat >/dev/null\nexit 0\n",
                     encoding="utf-8", newline="\n")
    r = subprocess.run([sys.executable, "-X", "utf8", str(w / ".claude" / "hooks" / "tool-dispatch.py"), "stop"],
                       input=b"{}", capture_output=True, timeout=60)
    assert r.returncode == 0 and r.stdout == b"" and r.stderr == b""


def test_r363_settings_stop_is_single_dispatcher_and_retired_for_targets():
    s = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    cmds = [h["command"] for g in s["hooks"]["Stop"] for h in g["hooks"]]
    assert cmds == ['python -X utf8 "$CLAUDE_PROJECT_DIR/.claude/hooks/tool-dispatch.py" stop']
    t = json.loads((ROOT / "setup" / "templates" / "settings.template.json").read_text(encoding="utf-8"))
    assert [h["command"] for g in t["hooks"]["Stop"] for h in g["hooks"]] == cmds
    ret = json.loads((ROOT / ".claude" / "scripts" / "retired-hooks.json").read_text(encoding="utf-8"))["Stop"]
    gone = set().union(*[set(x.get("hooks") or []) for x in (ret if isinstance(ret, list) else [ret])])
    sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "prompt"))
    spec = importlib.util.spec_from_file_location("td_r363c", ROOT / ".claude" / "hooks" / "tool-dispatch.py")
    td = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(td)
    assert {e[2].rsplit("/", 1)[-1] for e in td.STOP_SYNC + td.STOP_ASYNC} <= gone   # 대상에서도 옛 18개 제거


def test_r363_child_creationflags_inherits_console_when_present():
    """R363: 콘솔이 붙은 부모 = 0 (자식이 숨은 콘솔 상속 → conhost 안 생김) · 콘솔 없는 부모 = CREATE_NO_WINDOW (창 안 뜸)."""
    if os.name != "nt":
        pytest.skip("Windows 전용")
    code = ("import sys;sys.path.insert(0,sys.argv[1]);import _common as c;print(c.child_creationflags())")
    pdir = str(ROOT / ".claude" / "hooks" / "prompt")
    no_console = subprocess.run([sys.executable, "-c", code, pdir], capture_output=True, text=True,
                                creationflags=0x08000000 | 0x00000008).stdout.strip()      # DETACHED = 콘솔 없음
    with_console = subprocess.run([sys.executable, "-c", code, pdir], capture_output=True, text=True,
                                  creationflags=0x08000000).stdout.strip()                 # 숨은 새 콘솔
    assert no_console == str(0x08000000) and with_console == "0"


def test_r375_edit_logger_and_teaching_folded_into_dispatcher(tmp_path, monkeypatch):
    """R375 Hook 경량화: Edit 마다 따로 뜨던 python 2개 → tool-dispatch in-process (5차 검토: logger 는 POST·시간 제한)."""
    for f in (ROOT / ".claude" / "settings.json", ROOT / "setup" / "templates" / "settings.template.json"):
        s = json.loads(f.read_text(encoding="utf-8"))
        cmds = [h["command"] for ev in s["hooks"].values() for g in ev for h in g["hooks"]]
        assert not any("verify-after-edit-logger" in c or "verify-teaching-doc-sections" in c for c in cmds), f
        assert any("post-impl-verify.sh" in c for c in cmds)                    # async 무거운 검사는 그대로
    src = (ROOT / ".claude" / "hooks" / "tool-dispatch.py").read_text(encoding="utf-8")
    pre, post = src.split("POST = [", 1)[0], src.split("POST = [", 1)[1].split("]\n", 1)[0]
    assert "verify_after_edit_logger" not in pre and '"verify_after_edit_logger", "Edit|Write"' in post   # 성공한 Edit 만
    assert '"post_edit_checks", "Edit|Write"' in post
    ret = json.loads((ROOT / ".claude" / "scripts" / "retired-hooks.json").read_text(encoding="utf-8"))
    flat = [h for ev in ("PreToolUse", "PostToolUse") for spec in ret[ev] for h in spec.get("hooks", [])]
    assert "verify-after-edit-logger.py" in flat and "verify-teaching-doc-sections.py" in flat


def _logger_script():
    spec = importlib.util.spec_from_file_location("veal_r375", ROOT / ".claude" / "scripts" / "verify-after-edit-logger.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_r375_record_edit_bounded_utc_normalized(tmp_path):
    import re
    import sqlite3
    m = _logger_script()
    db = tmp_path / "orca.db"
    sqlite3.connect(db).close()
    a1, a2 = ("C:\\X\\a.py", "c:/x/./a.py") if os.name == "nt" else ("/x/a.py", "/x/./a.py")   # 플랫폼별 동등 표기
    assert m.record_edit(a1, db_path=db) == "ok"
    assert m.record_edit(a2, db_path=db) == "ok"                             # 같은 파일 다른 표기 → 같은 경로로 셈
    if os.name != "nt":
        assert m.normalize_path("/X/A\\b.py") == "/X/A\\b.py"              # POSIX: 대소문자·역슬래시 유지 (파일명 글자)
    rows = sqlite3.connect(db).execute("SELECT ts, file_path, edit_count, requery_pattern, reason FROM "
                                       "verify_after_edit_patterns ORDER BY id").fetchall()
    assert [r[2] for r in rows] == [1, 2] and len({r[1] for r in rows}) == 1
    assert all(r[3] is None for r in rows)                                    # 반복 수정만으로 재질의 단정 X
    assert rows[1][4] == "repeat_edit_1h" and re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d", rows[0][0])   # UTC 한 형식
    lock = sqlite3.connect(db, isolation_level=None)
    lock.execute("BEGIN EXCLUSIVE")                                           # 다른 쪽이 DB 를 잠금
    try:
        t0 = time.time()
        r = m.record_edit("C:/x/b.py", db_path=db)
        assert r == "spooled" and time.time() - t0 < 2.0                     # 응답 경로를 오래 붙잡지 않음 · 버리지 않고 스풀
    finally:
        lock.execute("ROLLBACK")
        lock.close()
    assert m.record_edit("C:/x/c.py", db_path=db) == "ok+replay1"              # 다음 성공 때 스풀분 이어 씀
    assert not (tmp_path / "hook-db-spool.jsonl").exists()
    assert m.record_edit("", db_path=db) == "skip:경로 없음"
    assert m.record_edit("C:/x/a.py", db_path=tmp_path / "none.db") == "skip:DB 없음"


def test_r375_doc_section_check_bounded_and_delivered(tmp_path, monkeypatch):
    m, Ctx = _tool_mod("post_edit_checks", monkeypatch, tmp_path)
    d = tmp_path / "docs"
    d.mkdir()

    def ctx_of(p):
        r = m.run(Ctx(json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(p)}})))
        return None if r is None else json.loads(r.out)["hookSpecificOutput"]["additionalContext"]
    g = d / "guide.md"
    g.write_text("# 제목\n본문에 흐름 강점 약점 확인 단계 같은 단어만 있음\n", encoding="utf-8")
    msg = ctx_of(g)
    assert msg and "8개" in msg                                                # 본문 키워드는 섹션으로 안 침 (제목·표만)
    g.write_text("# 핵심 한 줄\n| a | b |\n## 흐름\n## 강점\n## 약점\n## 강추\n## 우리 시스템\n## 점검\n", encoding="utf-8")
    assert ctx_of(g) is None
    big = d / "big_guide.md"
    big.write_bytes(b"# x\n" + b"a" * (2 * 1024 * 1024 + 10))
    assert "UNKNOWN" in ctx_of(big) and "상한" in ctx_of(big)                 # 큰 문서 = 미검사 진단
    dx = d / "guide.docx"
    dx.write_bytes(b"PK")
    assert "UNKNOWN" in ctx_of(dx)                                             # docx·pdf 는 응답 경로에서 추출 안 함
    assert ctx_of(d / "missing_guide.md") is not None and "읽기 실패" in ctx_of(d / "missing_guide.md")
    other = tmp_path / "src" / "a.md"
    other.parent.mkdir()
    other.write_text("x", encoding="utf-8")
    assert ctx_of(other) is None                                               # 교재 경로 아님 = 건너뜀


def test_r375_dispatcher_delivers_doc_context_end_to_end(tmp_path):
    """디스패처 실제 실행: 비차단 안내가 stdout JSON additionalContext 로 나간다 (예전 exit 1 stderr 는 Claude 에 안 감)."""
    d = tmp_path / "docs"
    d.mkdir()
    g = d / "guide.md"
    g.write_text("# 제목\n", encoding="utf-8")
    payload = json.dumps({"session_id": "t", "hook_event_name": "PostToolUse", "tool_name": "Edit",
                          "tool_input": {"file_path": str(g)}, "tool_response": {"success": True}})
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)}
    t0 = time.time()
    r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / ".claude" / "hooks" / "tool-dispatch.py"), "post"],
                       input=payload.encode(), capture_output=True, env=env, timeout=60)
    assert r.returncode == 0
    out = json.loads(r.stdout.decode("utf-8"))
    assert "[teaching-doc]" in out["hookSpecificOutput"]["additionalContext"]
    assert time.time() - t0 < 30


def test_r375_hook_db_writes_bounded_under_lock(tmp_path, monkeypatch):
    """R375 실측: orca.db 잠금 시 enforce-file-naming·post-edit-ping-pong 이 각 약 7.5초 응답 경로를 붙잡았다
    (sqlite 기본 5초 × 여러 문장) → 기록 전용 연결 대기 ORCA_HOOK_DB_TIMEOUT(기본 0.5초) · 못 잡으면 생략."""
    import importlib
    db = tmp_path / "orca.db"
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE file_audit(ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,session_id,action,path,size,hash,actor,reason)")  # 실제 스키마
    c.commit()
    c.close()
    out = {}
    for name in ("audit_file_write", "anti-ping-pong"):
        spec = importlib.util.spec_from_file_location("r375db_" + name.replace("-", "_"), ROOT / ".claude" / "scripts" / (name + ".py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        assert m._DB_TIMEOUT == 0.5 and hasattr(m, "_sdb")
        monkeypatch.setattr(m, "DB", db)
        out[name] = m
    lock = sqlite3.connect(db, isolation_level=None)
    lock.execute("BEGIN EXCLUSIVE")
    try:
        t0 = time.time()
        out["audit_file_write"].log_action("write", str(tmp_path / "x.py"), "t")     # 실패는 stderr 기록만
        try:
            out["anti-ping-pong"].record(str(tmp_path / "x.py"), "d", None, "s")
        except Exception:  # noqa: BLE001 — 훅 모듈이 예외를 삼키는 경로 (post_edit_ping_pong)
            pass
        assert time.time() - t0 < 3.0
    finally:
        lock.execute("ROLLBACK")
        lock.close()
    out["audit_file_write"].log_action("write", str(tmp_path / "x.py"), "t")
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM file_audit").fetchone()[0] == 2   # 잠금 중 1건은 스풀 → 이번에 함께 반영 (유실 0)


def _sdb_mod():
    spec = importlib.util.spec_from_file_location("sdb_r375", ROOT / ".claude" / "scripts" / "lib" / "state_db.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.mark.parametrize("raw,want", [("abc", 0.5), ("nan", 0.5), ("-1", 0.5), ("inf", 0.5), ("99", 0.5),
                                      ("0.01", 0.5), ("1.5", 1.5), ("", 0.5)])
def test_r375_hook_db_budget_env_validated(monkeypatch, raw, want):
    monkeypatch.setenv("ORCA_HOOK_DB_TIMEOUT", raw)
    assert _sdb_mod().hook_db_budget() == want


def test_r375_bounded_session_total_deadline_and_spool_integrity(tmp_path):
    """문장마다 busy_timeout 을 새로 주지 않고 전체 마감 하나 · 스풀 손상 줄은 보존 · INSERT/CREATE 만 재생."""
    m = _sdb_mod()
    db = tmp_path / "orca.db"
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE t(x)")
    c.commit()
    c.close()
    lock = sqlite3.connect(db, isolation_level=None)
    lock.execute("BEGIN EXCLUSIVE")
    try:
        t0 = time.time()
        r = m.bounded_insert(db, "t", [("INSERT INTO t VALUES(?)", [i]) for i in range(5)], budget=0.3)
        assert r == "spooled" and time.time() - t0 < 0.45                  # 5문장이어도 0.3초 마감 하나 (예전: 문장마다·단계마다 대기 2~2.7배)
    finally:
        lock.execute("ROLLBACK")
        lock.close()
    d = m.spool_dir(db)
    assert len(list(d.glob("*.json"))) == 1                                # 이벤트 1건 = 파일 1개
    (d / "00000000000000000001-x.json").write_text("{broken", encoding="utf-8")
    (d / "00000000000000000002-x.json").write_text(json.dumps(
        {"id": "e2", "ops": [["DELETE FROM t", []]]}), encoding="utf-8")   # 재생 허용 안 됨
    assert m.bounded_insert(db, "t", [("INSERT INTO t VALUES(?)", [99])]).startswith("ok+replay1")
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM t").fetchone()[0] == 6
    held = sorted(x.name for x in (d / "held").iterdir())
    assert len(held) == 2 and not list(d.glob("*.json"))                    # 손상·비허용은 지우지 않고 held/ 보존 (앞을 막지 않음)
    assert m.bounded_insert(tmp_path / "none.db", "t", []) == "skip:DB 없음"


def test_r375_audit_hash_capped_and_stat_safe(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("afw_r375", ROOT / ".claude" / "scripts" / "audit_file_write.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setattr(m, "HASH_MAX_BYTES", 100)
    big = tmp_path / "big.bin"
    big.write_bytes(b"x" * 1000)
    assert m._sha16(big) == "skip:size"                                     # 전체 파일 무제한 읽기 X · 실제 해시 아님을 값으로
    small = tmp_path / "s.bin"
    small.write_bytes(b"abc")
    assert len(m._sha16(small)) == 16
    monkeypatch.setattr(m, "DB", tmp_path / "none.db")
    assert m.log_action("write", str(tmp_path / "gone.py"), "t") == "skip:DB 없음"   # 없는 파일·DB 에도 예외 없음


def test_r375_doc_read_capped_even_if_file_grows(tmp_path, monkeypatch):
    m, Ctx = _tool_mod("post_edit_checks", monkeypatch, tmp_path)
    d = tmp_path / "docs"
    d.mkdir()
    g = d / "grow_guide.md"
    g.write_text("# x\n", encoding="utf-8")
    real_open = open
    reads = []

    class Grow:
        def __init__(self, *a, **k):
            self.f = real_open(*a, **k)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            self.f.close()

        def read(self, n=-1):
            reads.append(n)
            return b"#" * (n if n > 0 else 10)                             # stat 뒤 파일이 커진 상황

        def fileno(self):
            return self.f.fileno()
    monkeypatch.setattr(m, "open", Grow, raising=False)
    r = m.run(Ctx(json.dumps({"tool_input": {"file_path": str(g)}})))
    msg = json.loads(r.out)["hookSpecificOutput"]["additionalContext"]
    assert reads == [2 * 1024 * 1024 + 1] and "초과" in msg                  # 읽기량 = 상한+1 바이트로 묶임
    r2 = m.run(Ctx(json.dumps({"tool_input": {"file_path": "//server/share/docs/guide.md"}})))
    assert "네트워크" in json.loads(r2.out)["hookSpecificOutput"]["additionalContext"]


def _t_db(tmp_path):
    db = tmp_path / "orca.db"
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE t(x)")
    c.commit()
    c.close()
    return db


def _t_rows(db):
    return [r[0] for r in sqlite3.connect(db).execute("SELECT x FROM t ORDER BY rowid")]


def _t_spool_one(m, db, x):
    assert m.spool_append(db, "t", [["INSERT INTO t VALUES(?)", [x]]], "test") == "spooled"


def test_r375_spool_permanent_error_does_not_block_queue(tmp_path):
    """영구 오류 이벤트(테이블 없음 등)가 맨 앞에 있어도 뒤 이벤트는 반영 · 그 이벤트는 failed/ 보관 (삭제 X · 진단)."""
    m = _sdb_mod()
    db = _t_db(tmp_path)
    assert m.spool_append(db, "x", [["INSERT INTO no_such_table VALUES(?)", [1]]], "test") == "spooled"
    _t_spool_one(m, db, 7)
    assert m.bounded_insert(db, "t", [("INSERT INTO t VALUES(?)", [8])]) == "ok+replay1"
    assert sorted(_t_rows(db)) == [7, 8]
    d = m.spool_dir(db)
    assert not list(d.glob("*.json"))
    assert "no_such_table" in next((d / "failed").iterdir()).read_text(encoding="utf-8")


def test_r375_spool_append_during_replay_not_lost(tmp_path, monkeypatch):
    """7차 검토 P0-1 반례: 재생 도중(점유·삭제 직전) 다른 writer 가 스풀 → 예전 판은 그 기록이 사라짐(DB=[9,1]·스풀 없음)."""
    m = _sdb_mod()
    db = _t_db(tmp_path)
    _t_spool_one(m, db, 1)
    real_replace, real_unlink, fired = m.os.replace, m.os.unlink, []

    def rep(a, b):
        if str(b).endswith(".inflight") and "claim" not in fired:
            fired.append("claim")
            _t_spool_one(m, db, 2)                                          # 점유 직전 끼어든 기록
        return real_replace(a, b)

    def unl(x):
        if str(x).endswith(".inflight") and "ack" not in fired:
            fired.append("ack")
            _t_spool_one(m, db, 3)                                          # 반영 후 삭제 직전 끼어든 기록
        return real_unlink(x)
    monkeypatch.setattr(m.os, "replace", rep)
    monkeypatch.setattr(m.os, "unlink", unl)
    m.bounded_insert(db, "t", [("INSERT INTO t VALUES(?)", [9])])
    monkeypatch.setattr(m.os, "replace", real_replace)
    monkeypatch.setattr(m.os, "unlink", real_unlink)
    for _ in range(3):
        m.bounded_insert(db, "t", [("INSERT INTO t VALUES(?)", [10])])
    rows = _t_rows(db)
    assert sorted(x for x in rows if x < 9) == [1, 2, 3]                    # 끼어든 기록 유실 0 · 중복 0
    assert not list(m.spool_dir(db).glob("*.json"))


@pytest.mark.parametrize("done_fails", [False, True])
def test_r375_spool_ack_failure_no_duplicate(tmp_path, monkeypatch, done_fails):
    """7차 검토 P0-2 반례: DB commit 뒤 스풀 정리 실패 → 예전 판은 다음 회차에 같은 기록 재반영(DB=[9,1,10,1])."""
    m = _sdb_mod()
    db = _t_db(tmp_path)
    _t_spool_one(m, db, 1)
    real_replace, real_unlink = m.os.replace, m.os.unlink

    def unl(x):
        if str(x).endswith(".inflight"):
            raise OSError("injected")
        return real_unlink(x)

    def rep(a, b):
        if done_fails and str(b).endswith(".done"):
            raise OSError("injected")
        return real_replace(a, b)
    monkeypatch.setattr(m.os, "unlink", unl)
    monkeypatch.setattr(m.os, "replace", rep)
    assert m.bounded_insert(db, "t", [("INSERT INTO t VALUES(?)", [9])]) == "ok+replay1"
    monkeypatch.setattr(m.os, "unlink", real_unlink)
    monkeypatch.setattr(m.os, "replace", real_replace)
    assert m.bounded_insert(db, "t", [("INSERT INTO t VALUES(?)", [10])]) == "ok"
    assert _t_rows(db) == [9, 1, 10]                                       # 중복 반영 없음
    d = m.spool_dir(db)
    assert not list(d.glob("*.done")) and not list(d.glob("*.inflight"))
    assert (len(list((d / "unknown").iterdir())) == 1) if done_fails else not (d / "unknown").exists()


def test_r375_spool_event_prevalidated_no_partial_commit(tmp_path):
    """7차 검토 P0-3 반례: 한 이벤트에 INSERT(1)+DELETE → 예전 판은 앞 INSERT 까지 커밋(DB=[9,1,2])."""
    m = _sdb_mod()
    db = _t_db(tmp_path)
    d = m.spool_dir(db)
    d.mkdir()
    (d / "00000000000000000001-a.json").write_text(json.dumps(
        {"id": "a", "ops": [["INSERT INTO t VALUES(?)", [1]], ["DELETE FROM t", []]]}), encoding="utf-8")
    (d / "00000000000000000002-b.json").write_text(json.dumps(
        {"id": "b", "ops": [["INSERT INTO t VALUES(?); DELETE FROM t", [2]]]}), encoding="utf-8")
    _t_spool_one(m, db, 3)
    assert m.bounded_insert(db, "t", [("INSERT INTO t VALUES(?)", [9])]) == "ok+replay1"
    assert _t_rows(db) == [9, 3]                                           # 비허용 이벤트는 한 문장도 실행 안 함
    assert len(list((d / "held").iterdir())) == 2


def test_r375_spool_legacy_file_migrated_once(tmp_path):
    """예전 단일 파일 스풀(JSON 줄)은 이벤트 파일로 1회 이관 후 반영 · 손상 줄은 held/ 보존."""
    m = _sdb_mod()
    db = _t_db(tmp_path)
    m.spool_path(db).write_text(json.dumps({"kind": "t", "ops": [["INSERT INTO t VALUES(?)", [5]]]}) + "\n{bad\n",
                                encoding="utf-8")
    assert m.bounded_insert(db, "t", [("INSERT INTO t VALUES(?)", [9])]) == "ok+replay1"
    assert m.bounded_insert(db, "t", [("INSERT INTO t VALUES(?)", [10])]) == "ok"
    assert _t_rows(db) == [9, 5, 10] and not m.spool_path(db).exists()
    assert len(list((m.spool_dir(db) / "held").iterdir())) == 1


def test_r375_ping_pong_spool_keeps_event_time_and_schema(tmp_path, monkeypatch):
    """스풀 재생 때 발생 시각 보존(DEFAULT CURRENT_TIMESTAMP 아님) · 표 생성문 동봉 · 미확인은 None(실제 0 과 구분)."""
    spec = importlib.util.spec_from_file_location("app_r375", ROOT / ".claude" / "scripts" / "anti-ping-pong.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    db = tmp_path / "orca.db"
    sqlite3.connect(db).close()                                             # 표 없음
    monkeypatch.setattr(m, "DB", db)
    lock = sqlite3.connect(db, isolation_level=None)
    lock.execute("BEGIN EXCLUSIVE")
    try:
        assert m.record("a.py", "d", None, "s") is None                    # 미확인 (예전 판: 0)
    finally:
        lock.execute("ROLLBACK")
        lock.close()
    ev = json.loads(next(m._sdb.spool_dir(db).glob("*.json")).read_text(encoding="utf-8"))
    ts = ev["ops"][0][1][0]
    assert ev["setup"] and len(ts) == 19
    time.sleep(1.1)
    assert m.record("b.py", "d", None, "s") == 1
    got = dict(sqlite3.connect(db).execute("SELECT path, ts FROM ping_pong_tracker"))
    assert got["a.py"] == ts                                                # 재생돼도 발생 시각 그대로

