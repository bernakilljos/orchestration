"""R314 종단 시나리오 5종 — 실제 등록 훅·원장 CLI·재발 추적기·Stop 원장 게이트를 임시 폴더에서 끝까지 (모의 결과 연결 없음)."""
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEDGER_PY = ROOT / ".claude" / "scripts" / "request-ledger.py"
RT = ROOT / ".claude" / "scripts" / "recurrence-tracker.py"
HOOK = ROOT / ".claude" / "hooks" / "prompt" / "ledger_auto_register.py"
NA = "이 변경과 무관한 경계라 해당 없음"


def _env(tmp):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp), "PYTHONUTF8": "1"}
    env.pop("ORCA_TEST_MODE", None)
    return env


def _cli(tmp, script, *args, stdin=None):
    (tmp / ".claude" / "state").mkdir(parents=True, exist_ok=True)
    return subprocess.run([sys.executable, "-X", "utf8", str(script), *args], env=_env(tmp), input=stdin,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300, cwd=str(tmp))


def _prompt(tmp, text, sid="s"):
    """실제 UserPromptSubmit 등록 함수 run(ctx) 를 그대로 호출."""
    code = ("import importlib.util,sys,types,json;sp=importlib.util.spec_from_file_location('h',sys.argv[1]);"
            "m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);"
            "print(m.run(types.SimpleNamespace(payload=json.loads(sys.stdin.read()))))")
    (tmp / ".claude" / "state").mkdir(parents=True, exist_ok=True)
    return subprocess.run([sys.executable, "-X", "utf8", "-c", code, str(HOOK)], env=_env(tmp),
                          input=json.dumps({"prompt": text, "session_id": sid}), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120).stdout


def _reqs(tmp):
    p = tmp / ".claude" / "state" / "request-ledger.json"
    return json.loads(p.read_text(encoding="utf-8"))["requests"] if p.exists() else []


def _close_items(tmp, rid, r):
    for it in r.get("items", []):
        assert _cli(tmp, LEDGER_PY, "item", rid, str(it["n"]), "done", "--evidence", "임시 폴더 시험 통과").returncode == 0


def test_s1_feature_request_to_pass(tmp_path):
    """기능 개발: 4개 요구 지시 → 항목·반례 자동 저장 → 항목 완료 → 반례 시험 연결 → PASS 때 재실행 → 완료 · 게이트 통과."""
    (tmp_path / "t_ok.py").write_text("def test_ok():\n    assert 1 + 1 == 2\n", encoding="utf-8")
    out = _prompt(tmp_path, "1. 원장 동시 저장 시 손실 방지\n2. 손상 파일 복구\n3. 승인 우회 차단\n4. 상태줄 표시 유지\n다 하고 push해")
    assert "[ledger] +" in out
    r = _reqs(tmp_path)[-1]
    rid = r["id"]
    assert len(r["items"]) == 4 and len(r["counterexamples"]) >= 3
    _close_items(tmp_path, rid, r)
    assert _cli(tmp_path, LEDGER_PY, "complete", rid, "--evidence", "e", "--verification", "PASS").returncode == 2  # 반례 열림
    assert _cli(tmp_path, LEDGER_PY, "cx", rid, "1", "tested", "--test", "t_ok.py::test_ok").returncode == 0
    for c in range(2, len(r["counterexamples"]) + 1):
        assert _cli(tmp_path, LEDGER_PY, "cx", rid, str(c), "na", "--evidence", NA).returncode == 0
    ok = _cli(tmp_path, LEDGER_PY, "complete", rid, "--evidence", "임시 폴더 종단 시험", "--verification", "PASS")
    assert ok.returncode == 0, ok.stderr
    assert _reqs(tmp_path)[-1]["status"] == "completed"
    assert _cli(tmp_path, LEDGER_PY, "gate", stdin="{}").returncode == 0


def test_s2_regression_found_at_completion(tmp_path):
    """버그 수정 중 회귀: 연결 시험이 완료 시점에 실패 → PASS 거부 · PARTIAL 사실 기록 → 고친 뒤 재실행 통과."""
    t = tmp_path / "t_reg.py"
    t.write_text("def test_reg():\n    assert 'kg' * 2 == 'kgkgkg'\n", encoding="utf-8")
    _prompt(tmp_path, "1. 단위 변환 동시 실행 오류 수정\n2. 잘못된 입력 처리\n3. 캐시 무효화 확인\n고쳐줘")
    r = _reqs(tmp_path)[-1]
    rid = r["id"]
    _close_items(tmp_path, rid, r)
    _cli(tmp_path, LEDGER_PY, "cx", rid, "1", "tested", "--test", "t_reg.py::test_reg")
    for c in range(2, len(r["counterexamples"]) + 1):
        _cli(tmp_path, LEDGER_PY, "cx", rid, str(c), "na", "--evidence", NA)
    bad = _cli(tmp_path, LEDGER_PY, "complete", rid, "--evidence", "e", "--verification", "PASS")
    assert bad.returncode == 2 and "시험 실패" in bad.stderr
    assert _reqs(tmp_path)[-1]["status"] == "pending"
    t.write_text("def test_reg():\n    assert 'kg' * 3 == 'kgkgkg'\n", encoding="utf-8")
    assert _cli(tmp_path, LEDGER_PY, "complete", rid, "--evidence", "고친 뒤 재실행 통과", "--verification", "PASS").returncode == 0


def test_s3_recurrence_full_cycle(tmp_path):
    """재발: 기록 → 원인 확정 → 해결 시험 실패(FIX_FAILED) → 통과(VERIFIED) → 같은 원인 재발(REOPENED) → 재검증."""
    (tmp_path / "t_fix.py").write_text("def test_ok():\n    assert True\n\ndef test_bad():\n    assert False\n", encoding="utf-8")
    ev = json.loads(_cli(tmp_path, RT, "record", "미반영", "dev", "반영 안 됐잖아").stdout)["event_id"]
    _cli(tmp_path, RT, "root-cause", str(ev), "--cause", "전파 누락", "--evidence", "merge-to-target 대상 목록 누락", "--status", "confirmed")
    db = sqlite3.connect(tmp_path / ".claude" / "state" / "orca.db")
    st = lambda: db.execute("SELECT status, verified FROM recurrence_improvements").fetchone()
    assert _cli(tmp_path, RT, "fix-result", str(ev), "passed", "--evidence", "대상 목록에 경로 추가함", "--test", "t_fix.py::test_bad").returncode == 2
    assert st()[0] == "FIX_FAILED"
    assert _cli(tmp_path, RT, "fix-result", str(ev), "passed", "--evidence", "대상 목록에 경로 추가함", "--test", "t_fix.py::test_ok").returncode == 0
    assert st() == ("VERIFIED", 1)
    ev2 = json.loads(_cli(tmp_path, RT, "record", "미반영", "dev", "또 반영 안 됐잖아").stdout)["event_id"]
    _cli(tmp_path, RT, "root-cause", str(ev2), "--cause", "전파 누락", "--evidence", "같은 목록 다시 빠짐", "--status", "confirmed")
    assert st() == ("REOPENED", 0)
    assert _cli(tmp_path, RT, "fix-result", str(ev2), "passed", "--evidence", "목록 생성을 자동화함", "--test", "t_fix.py::test_ok").returncode == 0


def test_s4_questions_not_registered_directives_are(tmp_path):
    """질문·조회는 원장에 안 들어가고 원본 기록에만 · 실행 지시는 등록 · 원본 기록은 긴 지시도 보존."""
    for q in ("push했어?", "지금 상태 어때?"):
        assert "[ledger] +" not in _prompt(tmp_path, q)
    assert _reqs(tmp_path) == []
    long_directive = "\n".join(f"{i}. 항목 {i} 고쳐" for i in range(1, 150)) + "\n끝까지 하고 커밋해"
    assert "[ledger] +" in _prompt(tmp_path, long_directive)
    raw = [json.loads(x) for x in (tmp_path / ".claude" / "logs" / "ledger-raw.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(raw) == 3 and raw[-1]["prompt"].endswith("커밋해")


def test_s5_corrupt_ledger_blocks_stop(tmp_path):
    """원장 손상: Stop 게이트가 통과시키지 않음(fail-closed) · 미완료 요청도 막음 · 다른 세션 것은 막지 않음."""
    p = tmp_path / ".claude" / "state" / "request-ledger.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('{"requests": [ {"id": "R1", ', encoding="utf-8")
    assert _cli(tmp_path, LEDGER_PY, "gate", stdin="{}").returncode != 0
    p.unlink()
    _prompt(tmp_path, "1. 로그 정리\n2. 시험 추가\n3. 문서 갱신\n해줘", sid="mine")
    assert _cli(tmp_path, LEDGER_PY, "gate", stdin=json.dumps({"session_id": "mine"})).returncode == 2
    assert _cli(tmp_path, LEDGER_PY, "gate", stdin=json.dumps({"session_id": "other"})).returncode == 0


def test_cx_rerun_ignores_stale_bytecode(tmp_path, monkeypatch):
    """R314: 같은 크기로 고친 시험(kg * 3 → kg * 2 · 실패하게)을 완료 시점 재실행이 옛 .pyc(통과) 로 판정하지 않음."""
    # R315: 결함 재현 전제 = 바이트코드 캐시 쓰기 허용 — 실행 환경에 캐시 차단 변수가 있으면 재현 단계가 성립하지 않아 실패하던 것 (환경 의존 · D15)
    monkeypatch.delenv("PYTHONDONTWRITEBYTECODE", raising=False)
    monkeypatch.delenv("PYTHONPYCACHEPREFIX", raising=False)
    t = tmp_path / "t_pyc.py"
    t.write_text("def test_x():\n    assert 'kg' * 3 == 'kgkgkg'\n", encoding="utf-8")
    subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "t_pyc.py"], cwd=str(tmp_path),
                   capture_output=True, timeout=120)                       # __pycache__ 에 통과 버전 캐시를 남김
    st = t.stat()
    t.write_text("def test_x():\n    assert 'kg' * 2 == 'kgkgkg'\n", encoding="utf-8")   # 같은 크기 · 이제 실패
    os.utime(t, ns=(st.st_atime_ns, st.st_mtime_ns))                          # 같은 수정 시각 → 캐시가 그대로 맞아 보임
    sys.path.insert(0, str(ROOT / ".claude" / "scripts" / "lib"))
    from independent_verifier import _pytest_failures
    stale = _pytest_failures(tmp_path, ["t_pyc.py::test_x"], 120)
    fresh = _pytest_failures(tmp_path, ["t_pyc.py::test_x"], 120, nopyc=True)
    assert fresh[2] == 1 and fresh[0]                                         # 지금 코드 기준 실패
    assert stale[2] == 0                                                      # 캐시 차단 없으면 옛 결과로 통과 (결함 재현)


def test_fresh_source_cache_not_reused_between_runs(tmp_path, monkeypatch):
    """R334: 공유 캐시 폴더로 바꾼 뒤에도, 신선 실행 → 같은 크기·같은 시각으로 수정 → 신선 실행이 옛 .pyc 를 쓰지 않음
    (공유 캐시에 남은 대상 사본을 실행 직전에 지우는지) · 대상 폴더 소스 옆에는 __pycache__ 를 만들지 않음."""
    monkeypatch.delenv("PYTHONDONTWRITEBYTECODE", raising=False)
    monkeypatch.delenv("PYTHONPYCACHEPREFIX", raising=False)
    sys.path.insert(0, str(ROOT / ".claude" / "scripts" / "lib"))
    from independent_verifier import _pytest_failures
    t = tmp_path / "t_pyc.py"
    t.write_text("def test_x():\n    assert 'kg' * 3 == 'kgkgkg'\n", encoding="utf-8")
    first = _pytest_failures(tmp_path, ["t_pyc.py::test_x"], 120, nopyc=True)
    assert first[2] == 0
    st = t.stat()
    t.write_text("def test_x():\n    assert 'kg' * 2 == 'kgkgkg'\n", encoding="utf-8")
    os.utime(t, ns=(st.st_atime_ns, st.st_mtime_ns))
    second = _pytest_failures(tmp_path, ["t_pyc.py::test_x"], 120, nopyc=True)
    assert second[2] == 1 and second[0]                                       # 지금 코드 기준 실패
    assert not (tmp_path / "__pycache__").exists()                            # 캐시는 임시 폴더 쪽에만


def test_manual_add_moves_current_request(tmp_path):
    """R315: 자동 등록이 놓친 지시를 손으로 add 하면 상태줄 현재 요청이 직전 요청에 멈춰 있던 것 → add 도 현재 요청·세션 기록."""
    st = tmp_path / ".claude" / "state"
    st.mkdir(parents=True, exist_ok=True)
    (st / "current-trace.json").write_text(json.dumps({"trace_id": "old", "rid": "R1"}), encoding="utf-8")   # 직전 요청
    r = _cli(tmp_path, LEDGER_PY, "add", "--session", "s1", "놓친 지시 손 등록")
    assert r.returncode == 0, r.stderr
    cur = json.loads((st / "current-trace.json").read_text(encoding="utf-8"))
    rec = _reqs(tmp_path)[-1]
    assert cur["rid"] == rec["id"] and cur["trace_id"] != "old" and rec["session_id"] == "s1"   # 상태줄이 새 요청을 가리킴
    assert "duplicate" in _cli(tmp_path, LEDGER_PY, "add", "--session", "s1", "놓친 지시 손 등록").stdout   # 중복은 그대로 건너뜀
