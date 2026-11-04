"""Phase 19 회귀 (2026-11-04 · F7 FAIL: R154 → Goal #1464) — 임시 폴더 ledger·DB 만 사용 · 실 DB·유료 API X.

1. 대화·설명 요청은 to-goals 가 Goal 로 승격하지 않음 (UserPromptSubmit 자동 등재와 같은 정본 정책)
2. 명시 실행 요청은 정상 승격 · 중복 Request·반복 실행은 Goal 1개
3. Request 완료 + Goal 미완 → 경고만 · Goal 상태 변경 X (근거 없는 완료·취소 금지)
4. 10분 Scheduler 는 같은 to-goals 를 호출하고 불일치를 WARN 으로 기록
"""
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEDGER_PY = ROOT / ".claude" / "scripts" / "request-ledger.py"
R154 = "지금 여기있는 폴더에서 웹으로 zip만들어서 분석하기를 원하거든... 지금 기준으로 다시 해줄래 그리고 빠진거있으면 복사해주고"


def _proj(tmp_path, reqs, goals=()):
    st = tmp_path / ".claude" / "state"
    st.mkdir(parents=True, exist_ok=True)
    (st / "request-ledger.json").write_text(json.dumps({"session_id": "s1", "requests": reqs}, ensure_ascii=False),
                                            encoding="utf-8")
    with sqlite3.connect(str(st / "orca.db")) as c:
        c.execute("CREATE TABLE goals (goal_id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, status TEXT,"
                  " workflow_type TEXT, source_ref TEXT, max_retry INT, timeout_h INT, created_at INT, updated_at INT)")
        for ref, status in goals:
            c.execute("INSERT INTO goals (description, status, source_ref, created_at, updated_at)"
                      " VALUES ('g', ?, ?, 0, 0)", (status, ref))
    return st / "orca.db"


def _run(tmp_path, *args):
    env = {k: v for k, v in os.environ.items() if k != "AUTO_GOAL_REGISTER"}
    env.update({"CLAUDE_PROJECT_DIR": str(tmp_path), "PYTHONUTF8": "1"})
    return subprocess.run([sys.executable, str(LEDGER_PY), *args], env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=60)


def _goals(db):
    with sqlite3.connect(str(db)) as c:
        return c.execute("SELECT source_ref, status FROM goals ORDER BY goal_id").fetchall()


def test_chat_and_question_requests_not_promoted(tmp_path):
    db = _proj(tmp_path, [{"id": "R1", "desc": R154, "status": "pending"},
                          {"id": "R2", "desc": "이 구조 어떻게 되어 있어? 설명해줘", "status": "pending"},
                          {"id": "R3", "desc": "다 완료 되었어? 한글로 얘기해줘", "status": "pending"}])
    r = _run(tmp_path, "to-goals")
    assert r.returncode == 0, r.stderr
    assert "created=0" in r.stdout and "not_promoted=3" in r.stdout
    assert _goals(db) == []
    led = json.loads((tmp_path / ".claude/state/request-ledger.json").read_text(encoding="utf-8"))
    assert [q["status"] for q in led["requests"]] == ["pending"] * 3      # 원장 항목은 그대로


def test_explicit_execute_request_promoted_once(tmp_path):
    db = _proj(tmp_path, [{"id": "R1", "desc": "[auto-goal] 로그 정리 스크립트 구현", "status": "pending"},
                          {"id": "R2", "desc": R154, "status": "pending"}])
    r1 = _run(tmp_path, "to-goals")
    r2 = _run(tmp_path, "to-goals")                                      # 10분 루프 반복 실행
    assert "created=1" in r1.stdout and "not_promoted=1" in r1.stdout
    assert "created=0" in r2.stdout and "skipped_existing=1" in r2.stdout
    assert _goals(db) == [("ledger:R1", "PENDING")]


def test_duplicate_request_makes_one_entry_and_one_goal(tmp_path):
    db = _proj(tmp_path, [])
    for _ in range(2):
        assert _run(tmp_path, "add", "[auto-goal] 같은 요청 두 번").returncode == 0
    led = json.loads((tmp_path / ".claude/state/request-ledger.json").read_text(encoding="utf-8"))
    assert len(led["requests"]) == 1
    _run(tmp_path, "to-goals")
    _run(tmp_path, "to-goals")
    assert len(_goals(db)) == 1


def test_completed_request_with_running_goal_warns_without_changing_goal(tmp_path):
    db = _proj(tmp_path, [{"id": "R1", "desc": R154, "status": "completed"},
                          {"id": "R2", "desc": "끝난 것", "status": "completed"}],
               goals=[("ledger:R1", "RUNNING"), ("ledger:R2", "VERIFIED")])
    r = _run(tmp_path, "to-goals")
    assert r.returncode == 0, r.stderr
    assert "WARN ledger R1 completed but goal #1 RUNNING" in r.stdout
    assert "R2" not in r.stdout                                           # 증거로 닫힌 Goal 은 경고 없음
    assert _goals(db) == [("ledger:R1", "RUNNING"), ("ledger:R2", "VERIFIED")]   # 자동 완료·취소 X


def test_opt_out_file_blocks_promotion(tmp_path):
    db = _proj(tmp_path, [{"id": "R1", "desc": "[auto-goal] 무엇이든", "status": "pending"}])
    (tmp_path / ".claude/state/no-auto-goal").write_text("", encoding="utf-8")
    assert "created=0" in _run(tmp_path, "to-goals").stdout
    assert _goals(db) == []


def test_scheduler_uses_same_to_goals_and_logs_mismatch_as_warn(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("orca_loop_p19", ROOT / ".claude" / "scripts" / "orca-10min-loop.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for k, v in {"LOG_FILE": tmp_path / "loop.log", "STATE_FILE": tmp_path / "state.json", "STATE_DIR": tmp_path,
                 "DRY_RUN": False, "optimize_orca_db": lambda: True, "run_cleanup_pollution": lambda: True,
                 "detect_idle_sessions": lambda: [], "reap_stuck_orphans": lambda: 0}.items():
        monkeypatch.setattr(m, k, v)
    calls = []
    out = "[ledger→goal] created=0 skipped_existing=0 not_promoted=0 WARN ledger R1 completed but goal #9 RUNNING (상태 변경 안 함)"

    def fake_run(argv, **k):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, out if "to-goals" in argv else "", "")
    monkeypatch.setattr(m.subprocess, "run", fake_run)
    m.main()
    assert any(Path(str(a[1])) == LEDGER_PY and a[-1] == "to-goals" for a in calls)
    log = (tmp_path / "loop.log").read_text(encoding="utf-8")
    assert "[WARN] ledger to-goals:" in log and "goal #9 RUNNING" in log
