"""§78 요청 단위 추적 — 접수부터 시도(실패→대체→성공)·시간·근거 · 가림 · 기록 장애 · 복원 (격리 폴더)."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / ".claude" / "scripts"
HOOKS = ROOT / ".claude" / "hooks"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture
def proj(tmp_path, monkeypatch):
    (tmp_path / ".claude" / "state").mkdir(parents=True)
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def tm(proj):
    return _load("trace_under_test", SCRIPTS / "lib" / "trace.py")


def test_no_trace_id_records_nothing(tm, proj):
    assert tm.emit("tool", step="Bash", status="success") == "none"
    assert not (proj / ".claude" / "logs" / "trace-events.jsonl").exists()


def test_jsonl_when_table_absent_then_db_after_init(tm, proj):
    tm.set_current("tid-1", "R1", "guide 고쳐줘")
    assert tm.emit("tool", step="Bash", status="success", duration_ms=12.3) == "jsonl"
    subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "lib" / "trace.py"), "init-db",
                    str(proj / ".claude" / "state" / "orca.db")], check=True, env=dict(os.environ))
    assert tm.emit("tool", step="Bash", status="fail", error="exit 1") == "db"
    evs = tm.events("tid-1")
    assert [e["status"] for e in evs] == ["success", "fail"]


def test_failure_then_fallback_success_is_chained(tm, proj):
    tm.set_current("tid-2", "R2", "x")
    tm.emit("tool", step="Bash", status="fail", error="UIA 대기 30s 초과")
    tm.emit("tool", step="Bash", status="fail", error="win32 경로 권한 없음")
    tm.emit("tool", step="Bash", status="success")
    tm.emit("test", step="regression-gate", status="fail", error="신규 실패 1")
    ch = tm.chains(tm.events("tid-2"))
    bash = [c for c in ch if c["step"] == "Bash"][0]
    assert len(bash["failures"]) == 2 and bash["success"]["status"] == "success"
    gate = [c for c in ch if c["step"] == "regression-gate"][0]
    assert gate["success"] is None     # 성공 기록 없음 = 연결을 만들지 않음


def test_secrets_masked(tm, proj):
    tm.set_current("tid-3", "R3", "")
    secret = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
    tm.emit("tool", step="Bash", status="fail", error="token=" + secret, detail={"cmd": "curl -H " + secret})
    raw = (proj / ".claude" / "logs" / "trace-events.jsonl").read_text(encoding="utf-8")
    assert secret not in raw


def test_corrupt_db_falls_back_to_jsonl(tm, proj):
    (proj / ".claude" / "state" / "orca.db").write_bytes(b"not a database")
    tm.set_current("tid-4", "R4", "")
    assert tm.emit("tool", step="Edit", status="success") == "jsonl"


def test_ledger_registration_starts_trace(proj):
    sys.path.insert(0, str(HOOKS / "prompt"))
    try:
        lar = _load("lar_under_test", HOOKS / "prompt" / "ledger_auto_register.py")
        r = lar._append_ledger_entry("guide.txt 오타 고쳐줘", "sess-abc", "execute")
    finally:
        sys.path.remove(str(HOOKS / "prompt"))
    assert r["status"] == "registered"
    cur = json.loads((proj / ".claude" / "state" / "current-trace.json").read_text(encoding="utf-8"))
    assert cur["trace_id"] == r["event_id"] and cur["rid"] == r["request_id"]
    tm = _load("trace_after_ledger", SCRIPTS / "lib" / "trace.py")
    evs = tm.events(r["request_id"])           # R 번호로도 조회
    assert evs and evs[0]["kind"] == "request" and evs[0]["status"] == "start"
    # 종료 기록 (request-ledger complete) → 같은 추적번호에 partial
    subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "request-ledger.py"), "complete", r["request_id"],
                    "--evidence", "시험", "--verification", "PARTIAL"], env=dict(os.environ), capture_output=True)
    assert [e["status"] for e in tm.events(r["event_id"])][-1] == "partial"


def test_hook_failure_cli_and_resume_section(proj, tm):
    tm.set_current("tid-5", "R5", "SAP 연결")
    inp = json.dumps({"tool_name": "Bash", "tool_input": {"command": "python sap_connect.py"}, "error": "RFC 연결 실패", "tool_use_id": "tu_1"})
    subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "lib" / "trace.py"), "hook-failure"], input=inp, text=True,
                   encoding="utf-8", env=dict(os.environ), check=True)
    tm.emit("tool", step="Bash", status="success")
    out = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "lib" / "trace.py"), "show", "tid-5"],
                         capture_output=True, text=True, encoding="utf-8", env=dict(os.environ)).stdout
    assert "RFC 연결 실패" in out and "실패 1회" in out
    rs = _load("resume_under_test", SCRIPTS / "resume-last-24h.py")
    sec = rs.section_current_trace()
    assert "tid-5" in sec and "대체 성공" in sec


@pytest.mark.parametrize("path,expect", [
    ("C:\\\\x\\\\.claude\\\\rules\\\\a.md", True),     # Windows 역슬래시 경로 (종전엔 재색인 안 됨)
    ("C:/x/.claude/rules/a.md", True),
    ("C:\\\\x\\\\guide.txt", False),
])
def test_index_rule_on_edit_windows_paths(tmp_path, path, expect):
    (tmp_path / ".claude" / "scripts").mkdir(parents=True)
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    marker = tmp_path / "rebuilt.txt"
    (tmp_path / ".claude" / "scripts" / "lookup-rule.py").write_text(
        "import pathlib,sys\npathlib.Path(%r).write_text('x')\n" % str(marker), encoding="utf-8")
    payload = '{"tool_name":"Edit","tool_input":{"file_path":"%s"}}' % path
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(tmp_path))
    env.pop("RULE_INDEX_ACTIVE", None)
    subprocess.run(["bash", str(HOOKS / "index-rule-on-edit.sh")], input=payload, text=True, env=env, timeout=60)
    import time
    for _ in range(50):
        if marker.exists():
            break
        time.sleep(0.1)
    assert marker.exists() == expect


def test_interrupted_request_marked_unknown_and_risky_tool_flagged(proj):
    """§79 응답이 끊겨 종료 기록 없이 다음 요청이 오면 이전 요청 = unknown · 마지막 비멱등 도구 표시."""
    tm = _load("trace_int", SCRIPTS / "lib" / "trace.py")
    tm.set_current("tid-old", "R7", "push 해줘")
    tm.emit("request", step="R7", status="start", trace_id="tid-old")
    tm.emit("tool", step="Bash", status="success", detail={"input": "git push origin main"})
    rs = _load("resume_int", SCRIPTS / "resume-last-24h.py")
    sec = rs.section_current_trace()
    assert "완료 여부 불명" in sec and "비멱등" in sec
    sys.path.insert(0, str(HOOKS / "prompt"))
    try:
        lar = _load("lar_int", HOOKS / "prompt" / "ledger_auto_register.py")
        r = lar._append_ledger_entry("다음 작업 해줘", "sess-x", "execute")
    finally:
        sys.path.remove(str(HOOKS / "prompt"))
    old = tm.events("tid-old")
    assert old[-1]["status"] == "unknown" and "종료 기록 없음" in old[-1]["error"]
    assert tm.get_current()["trace_id"] == r["event_id"]


def test_completed_request_not_marked_unknown(proj):
    tm = _load("trace_done", SCRIPTS / "lib" / "trace.py")
    tm.set_current("tid-done", "R8", "x")
    tm.emit("request", step="R8", status="start", trace_id="tid-done")
    tm.emit("request", step="R8", status="success", trace_id="tid-done")
    sys.path.insert(0, str(HOOKS / "prompt"))
    try:
        lar = _load("lar_done", HOOKS / "prompt" / "ledger_auto_register.py")
        lar._append_ledger_entry("새 작업", "sess-y", "execute")
    finally:
        sys.path.remove(str(HOOKS / "prompt"))
    assert [e["status"] for e in tm.events("tid-done")] == ["start", "success"]


# ── §80 요청 집계 정본 — 상태줄·READY 상한·health-check·Stop 게이트가 같은 함수 ──
def _ledger(proj, reqs, rid=""):
    (proj / ".claude" / "state" / "request-ledger.json").write_text(
        json.dumps({"session_id": "s", "requests": reqs}, ensure_ascii=False), encoding="utf-8")
    if rid:
        (proj / ".claude" / "state" / "current-trace.json").write_text(
            json.dumps({"trace_id": "t", "rid": rid, "desc": "x"}), encoding="utf-8")


_MIX = [{"id": "R1", "status": "completed"}, {"id": "R2", "status": "approval_required"},
        {"id": "R3", "status": "invalid_registration"}, {"id": "R4", "status": "out_of_scope"},
        {"id": "R5", "status": "verified", "verification": "PARTIAL", "evidence": "e"},
        {"id": "R6", "status": "deferred"}]


def test_summarize_counts_only_completed_as_done(proj):
    rl = _load("rl80", SCRIPTS / "request-ledger.py")
    c = rl.summarize(_MIX, "R2")
    assert (c["completed"], c["total"], c["approval_required"], c["invalid_registration"],
            c["out_of_scope"], c["verified"], c["deferred"], c["blocking"]) == (1, 6, 1, 1, 1, 1, 1, 0)
    assert c["current_status"] == "approval_required" and c["current_blocking"] is False
    assert rl.summarize(_MIX, "R99")["current_status"] == "UNKNOWN"
    assert rl.summarize(_MIX + [{"id": "R7", "status": "pending"}], "R7")["current_blocking"] is True


def test_statusline_line_and_ready_cap_follow_current_request(proj):
    _ledger(proj, _MIX + [{"id": "R7", "status": "pending"}], "R1")
    sl = _load("sl80", SCRIPTS / "statusline_context.py")
    assert sl._ledger_summary(str(proj)) is None        # 정본 스크립트 없음 = 집계 불가 (상한 유지 쪽)
    (proj / ".claude" / "scripts").mkdir(parents=True, exist_ok=True)
    (proj / ".claude" / "scripts" / "request-ledger.py").write_bytes((SCRIPTS / "request-ledger.py").read_bytes())
    sl._MEMO.clear()                                      # 렌더 1회 메모 — 실제는 렌더마다 새 프로세스
    c = sl._ledger_summary(str(proj))
    assert c["completed"] == 1 and c["current_rid"] == "R1" and c["blocking"] == 1
    # 현재 요청 완료 → 지난 미완료가 있어도 상한 대상 아님 · 현재 요청 미완료 → 대상
    assert not c["current_blocking"]
    _ledger(proj, _MIX + [{"id": "R7", "status": "pending"}], "R7")
    sl._MEMO.clear()
    assert sl._ledger_summary(str(proj))["current_blocking"]
    hc = _load("hc80", SCRIPTS / "health-check.py")
    hc.STATE_DIR = str(proj / ".claude" / "state")
    assert hc.check_request_ledger()["value"] == "1/7"


# ── §81 사용자 보고 한글 고정 (STD-KOREAN-001) — 원인: 사용자 전역 settings language=English ──
def test_project_settings_force_korean_language():
    # 전파 대상은 고유 settings.json 을 보존하고 전역에서 language 를 받는다 → «실제 적용 값» 으로 확인 (§84)
    m = _load("sr_eff", SCRIPTS / "standing-requirements.py")
    val, src = m._effective_setting("language")
    assert str(val).lower() == "korean", (val, src)
    tpl = ROOT / "setup" / "templates" / "settings.template.json"
    if tpl.exists():                                             # 설치 템플릿은 kit 에만 있다
        assert json.loads(tpl.read_text(encoding="utf-8")).get("language") == "Korean", tpl
    seed = json.loads((SCRIPTS / "standing-requirements.seed.json").read_text(encoding="utf-8"))["requirements"]
    k = seed["STD-KOREAN-001"]                                   # §84 문자열 유무가 아니라 실효 설정
    assert k["verify_kind"] == "effective_setting" and k["setting_key"] == "language" and k["expect"] == "Korean"
    assert "verify_target" not in k


@pytest.mark.parametrize("local,proj_,user,want", [
    (None, {"language": "Korean"}, {"language": "English"}, "PASS"),      # 프로젝트가 사용자 전역을 덮음
    ({"language": "English"}, {"language": "Korean"}, None, "FAIL"),      # local 이 프로젝트를 덮음
    (None, None, {"language": "korean"}, "PASS"),                         # 전역만 (대소문자 무관)
    (None, {"model": "x"}, None, "FAIL"),                                 # 어디에도 없음 = 미적용
])
def test_effective_language_follows_official_precedence(tmp_path, monkeypatch, local, proj_, user, want):
    proj = tmp_path / "p"
    home = tmp_path / "h"
    (proj / ".claude").mkdir(parents=True)
    (home / ".claude").mkdir(parents=True)
    for d, f in ((local, proj / ".claude" / "settings.local.json"), (proj_, proj / ".claude" / "settings.json"),
                 (user, home / ".claude" / "settings.json")):
        if d is not None:
            f.write_text(json.dumps(d), encoding="utf-8")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(proj))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    m = _load("sr84", SCRIPTS / "standing-requirements.py")
    assert m._verify({"verify_kind": "effective_setting", "setting_key": "language", "expect": "Korean"}) == want


def _lang(proj, payload):
    return subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "standing-requirements.py"), "lang-check"],
                          input=json.dumps(payload, ensure_ascii=False), text=True, encoding="utf-8",
                          capture_output=True, env=dict(os.environ))


def test_lang_check_blocks_english_report_once_and_logs(proj):
    en = "I'll report when finished. The regression gate passed and the statusline audit is still running now."
    ko = "회귀 게이트를 통과했습니다. `statusline_context.py` 수정을 계속하고 끝나면 한 번에 보고합니다. 아직 진행 중입니다."
    r = _lang(proj, {"last_assistant_message": en})
    assert r.returncode == 2 and "STD-KOREAN-001" in r.stderr
    assert _lang(proj, {"last_assistant_message": en, "stop_hook_active": True}).returncode == 0   # 무한 차단 X
    assert _lang(proj, {"last_assistant_message": ko}).returncode == 0
    assert _lang(proj, {"last_assistant_message": "```bash\ngit status --porcelain && python -m pytest -q tests/\n```"}).returncode == 0
    log = (proj / ".claude" / "logs" / "language-violations.log").read_text(encoding="utf-8").splitlines()
    st = [json.loads(x)["status"] for x in log]          # 현재 요청 추적이 없으면 옛 로그 파일에 덧붙임
    assert st == ["fail", "fail", "success"]              # 차단 · 두 번째(기록만) · 한국어 정정 기록


def test_lang_check_reads_transcript_main_thread_only(proj):
    tr = proj / "t.jsonl"
    rows = [{"type": "assistant", "message": {"content": [{"type": "text", "text": "작업을 마쳤습니다. 결과를 한국어로 보고드립니다. 회귀 시험은 모두 통과했습니다."}]}},
            {"type": "assistant", "isSidechain": True, "message": {"content": [{"type": "text", "text": "Background agent finished the inventory and all nine claims hold true here."}]}}]
    tr.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows), encoding="utf-8")
    assert _lang(proj, {"transcript_path": str(tr)}).returncode == 0     # 서브에이전트 영어 원문은 사용자 보고가 아님


def test_standing_stats_counts_real_failures(proj):
    st = proj / ".claude" / "state"
    (proj / "a.txt").write_text("OK-MARK", encoding="utf-8")
    reqs = {"A": {"status": "ACTIVE", "verify_target": "a.txt", "verify_pattern": "OK-MARK"},
            "B": {"status": "ACTIVE", "verify_target": "a.txt", "verify_pattern": "NOPE"},
            "C": {"status": "ACTIVE", "judge": "human"},
            "D": {"status": "ACTIVE"}}
    (st / "standing-requirements.json").write_text(json.dumps(reqs), encoding="utf-8")
    out = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "standing-requirements.py"), "stats"],
                         capture_output=True, text=True, encoding="utf-8", env=dict(os.environ)).stdout
    s = json.loads(out)
    # 시드(STD-*)가 함께 합쳐진다 — 결과별 합 = 전체 · 실패가 있으면 만점 아님 (종전: 항상 ok == active)
    assert s["ok"] + s["failed"] + s["human"] + s["unknown"] == s["active"]
    assert s["failed"] >= 1 and s["human"] >= 1 and s["unknown"] >= 1 and s["ok"] < s["active"]


# ── §81 상태줄 데이터 계층 — 미측정·조회 실패·오래된 값이 0·✅ 로 보이지 않는다 (격리 폴더 · 저장소 아님) ──
import re as _re81


def _plain(x):
    return _re81.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", x or "")


@pytest.fixture
def sl(proj):
    (proj / "plugins").mkdir()
    m = _load("sl81", SCRIPTS / "statusline_context.py")
    m._MEMO.clear()
    return m


def test_no_git_no_logs_no_agents_are_unmeasured_not_zero(sl, proj):
    import shutil as _sh
    _sh.rmtree(proj / ".claude" / "logs")
    g = sl.extra_gauges(str(proj), {})
    assert "git 조회 실패" in _plain(g["impact"]) and "API 0" not in _plain(g["impact"])
    assert "git ⏳" in _plain(g["proof"]) and "git ✅" not in _plain(g["proof"])
    assert "미측정" in _plain(g["errors"]) and "error 0" not in _plain(g["errors"])
    assert "UNKNOWN" in _plain(g["agents"])
    assert "미구현" in _plain(g["control"]) and "미구현" in _plain(g["reuse"])


def test_stale_test_cache_is_not_current_success(sl, proj):
    (proj / ".claude" / "state" / "test-cache.json").write_text(
        json.dumps({"passed": 13, "total": 13, "ts": "2023-01-01T00:00:00"}), encoding="utf-8")
    score, grade, icon, _ = sl._compute_readiness(str(proj), 0, 0, 0, 0)
    assert icon == "⏳"
    (proj / ".claude" / "state" / "test-cache.json").write_text(
        json.dumps({"passed": 13, "total": 13, "ts": datetime_now_iso()}), encoding="utf-8")
    assert sl._compute_readiness(str(proj), 0, 0, 0, 0)[2] == "✅"
    assert int(_plain(str(sl._compute_readiness(str(proj), 0, 0, 0, 0, logs_unmeasured=True)[0])).split("/")[0]) <= 85


def datetime_now_iso():
    from datetime import datetime
    return datetime.now().isoformat(timespec="seconds")


def test_verify_line_reads_regression_record_with_age(sl, proj):
    import time as _t
    f = proj / ".claude" / "state" / "regression-gate.json"
    f.write_text(json.dumps({"status": "pass", "at": _t.time(), "summary": "== 447 passed in 3s ==", "new_failures": []}), encoding="utf-8")
    v = _plain(sl.extra_gauges(str(proj), {})["verify"])
    assert "447통과" in v and "신규실패 0" in v
    f.write_text(json.dumps({"status": "pass", "at": _t.time() - 9 * 86400, "summary": "== 447 passed ==", "new_failures": []}), encoding="utf-8")
    sl._MEMO.clear()
    v = _plain(sl.extra_gauges(str(proj), {})["verify"])
    assert "447통과" not in v and "9일 전" in v


def test_rate_limit_cache_keeps_collection_time(sl, proj, monkeypatch):
    home = proj / "home"
    home.mkdir()
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    rl = {"rate_limits": {"five_hour": {"used_percentage": 10}, "seven_day": {"used_percentage": 20}}}
    sl.extra_gauges(str(proj), rl)
    sl._MEMO.clear()
    sl.extra_gauges(str(proj), {})          # 새 값 없는 렌더 — 종전엔 여기서 ts=지금·key_ts 삭제
    d = json.loads((home / ".claude" / "state" / "rate-limits.json").read_text(encoding="utf-8"))
    assert "key_ts" in d and set(d["key_ts"]) == {"five_hour", "seven_day"}


def test_stop_standing_hook_runs_lang_check_with_same_stdin(tmp_path):
    import shutil
    for rel in (".claude/scripts/standing-requirements.py", ".claude/scripts/standing-requirements.seed.json",
                ".claude/hooks/stop-standing-gate.sh", ".claude/settings.json"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)
    (tmp_path / "plugins").mkdir()
    (tmp_path / "CLAUDE.md").write_text("| D22 |", encoding="utf-8")
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path), "PYTHONUTF8": "1"}
    bash = shutil.which("bash") or "bash"
    en = "The audit finished and all checks passed so I will report the final results when everything is done here."

    def hook(payload):
        return subprocess.run([bash, str(tmp_path / ".claude/hooks/stop-standing-gate.sh")], input=json.dumps(payload),
                              capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)
    r = hook({"stop_hook_active": False, "last_assistant_message": en})
    assert r.returncode == 2 and "STD-KOREAN-001" in r.stderr
    assert hook({"stop_hook_active": True, "last_assistant_message": en}).returncode == 0
    ko = hook({"stop_hook_active": False, "last_assistant_message": "점검을 마쳤고 모든 검사가 통과했습니다. 최종 결과를 한 번에 보고드립니다."})
    assert "STD-KOREAN-001" not in ko.stderr      # 한글 보고는 언어 검사에 걸리지 않음 (기준 게이트 차단은 격리 폴더 시드 대상 부재)


def test_lang_check_catches_english_mid_turn_report(proj):
    """§81 실측: 이 세션 보고 132건 중 45건 영어 — 대부분 턴 중간 진행 보고. 마지막 보고만 보면 놓친다."""
    tr = proj / "t2.jsonl"
    rows = [{"type": "user", "message": {"content": "상태줄 고쳐줘"}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "It compiles. Next I'll render on the same data and compare before and after output."}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "수정을 마쳤습니다. 같은 데이터로 수정 전후를 비교했고 모든 시험이 통과했습니다."}]}}]
    tr.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows), encoding="utf-8")
    r = _lang(proj, {"transcript_path": str(tr)})
    assert r.returncode == 2 and "1건" in r.stderr
    rows[1]["message"]["content"][0]["text"] = "컴파일했습니다. 같은 데이터로 전후 출력을 비교합니다. 잠시만 기다려 주세요 진행 중입니다."
    tr.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows), encoding="utf-8")
    assert _lang(proj, {"transcript_path": str(tr)}).returncode == 0
    # 이전 턴(사람 입력 이전)의 영어는 이번 턴 판정에 넣지 않는다
    rows2 = [{"type": "assistant", "message": {"content": [{"type": "text", "text": "Old English report from a previous turn that was already handled before."}]}}] + rows
    tr.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows2), encoding="utf-8")
    assert _lang(proj, {"transcript_path": str(tr)}).returncode == 0



def test_lang_check_is_incremental_and_records_to_trace(proj, tm):
    """§82 이미 검사·지적한 영어 보고는 다시 세지 않는다 · 위반·정정 = 요청 추적(trace)."""
    tm.set_current("tid-lang", "R9", "상태줄")
    tr = proj / "t3.jsonl"
    rows = [{"type": "user", "message": {"content": "고쳐줘"}},
            {"type": "assistant", "uuid": "a1", "message": {"content": [{"type": "text", "text": "Now I'm reading the assembly code for the remaining areas before editing anything."}]}}]
    tr.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows), encoding="utf-8")
    pl = {"transcript_path": str(tr), "session_id": "s1"}
    assert _lang(proj, pl).returncode == 2
    assert _lang(proj, pl).returncode == 0                 # 같은 보고 재검사 X (stop_hook_active 없어도)
    rows += [{"type": "user", "message": {"content": "Stop hook feedback: [STD-KOREAN-001] ..."}},
             {"type": "assistant", "uuid": "a2", "message": {"content": [{"type": "text", "text": "남은 영역의 조립 코드를 읽고 있습니다. 수정 전에 전부 확인하고 한 번에 고치겠습니다."}]}}]
    tr.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows), encoding="utf-8")
    assert _lang(proj, pl).returncode == 0
    ev = [e for e in tm.events("tid-lang") if e.get("step") == "STD-KOREAN-001"]
    assert [e["status"] for e in ev] == ["fail", "success"] and "정정" in (ev[-1].get("evidence") or "")


def test_post_tool_drift_reminds_once_on_english_mid_turn_report(proj):
    """§83 턴 중간 영어 보고 → 다음 도구 실행 직후 한 줄 안내 (같은 보고엔 1회 · 한국어면 출력 없음)."""
    (proj / ".claude" / "scripts").mkdir(parents=True, exist_ok=True)
    (proj / ".claude" / "scripts" / "standing-requirements.py").write_bytes((SCRIPTS / "standing-requirements.py").read_bytes())
    sys.path.insert(0, str(HOOKS / "prompt"))
    try:
        mod = _load("krd", HOOKS / "tool" / "korean_report_drift.py")
    finally:
        sys.path.remove(str(HOOKS / "prompt"))
    tr = proj / "t4.jsonl"

    def write(rows):
        tr.write_text(chr(10).join(json.dumps(x, ensure_ascii=False) for x in rows), encoding="utf-8")

    class C:
        raw = json.dumps({"transcript_path": str(tr), "session_id": "s4"})
    base = [{"type": "user", "message": {"content": "고쳐줘"}}]
    write(base + [{"type": "assistant", "uuid": "k1", "message": {"content": [{"type": "text", "text": "수정을 계속합니다. 다음으로 시험을 실행하고 결과를 확인한 뒤 한 번에 보고하겠습니다."}]}}])
    assert mod.run(C) is None
    write(base + [{"type": "assistant", "uuid": "e1", "message": {"content": [{"type": "text", "text": "Memory is updated. Not yet verified, when it passes I will commit and report the results."}]}}])
    r = mod.run(C)
    assert r is not None and "STD-KOREAN-001" in r.out and json.loads(r.out)["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert mod.run(C) is None                                  # 같은 보고에 두 번 안내하지 않음
