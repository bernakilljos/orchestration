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


# ── 2026-11-06 R167~R170: 붙여 넣은 상태 보고가 실행·승인 요청으로 등록된 오탐 (원문 발췌 · 공식 hooks 문서의 pasted_content 줄 형식) ──
HOOK_PY = ROOT / ".claude" / "hooks" / "prompt" / "ledger_auto_register.py"


def _paste(body):
    return f'\n\n<pasted_content id="efcd">\n{body}\n</pasted_content id="efcd">\n'


R167_REPORT = _paste("좋습니다. 😊 원래 Claude 세션으로 돌아온 뒤에도 기존 개발 내용을 정상적으로 인수했고, B·C의 추가 검증까지 진행됐네요.\n"
                     "dashboard.py에서 문서화 여부가 불확실한 Git 설정 방식을 공식 문서의 GIT_CONFIG_COUNT 방식으로 변경했습니다.\n"
                     "단, 공식 문서와 맞는다는 사실과 실제 운영 환경에서 인증이 성공한다는 사실은 별개입니다.\n"
                     "다음 단계 권고\n1. 로컬 14개 커밋: 비밀정보를 확인한 뒤 Push 여부 결정\n"
                     "2. 유료 Judge 1회: 승인하면 실제 근거 검증을 진행해 B의 남은 공백 확인\n"
                     "현재 잠정 점수는 93/100 유지하겠습니다.")
R169_REPORT = _paste("좋습니다! 😊 이번에는 14개 커밋의 Push가 정상 완료됐고, 원격과 로컬이 일치한다는 증거까지 확보했네요.\n"
                     "운영 기록    R160·R163·R167·R168 및 Goal #77 보존\n"
                     "이번 Push 승인이 유료 호출이나 배포 승인으로 확대되지 않은 점도 적절합니다.\n"
                     "실제 Judge 호출은 이전에 산정한 $1 상한이 있으나, 아직 유료 호출 승인은 하지 않은 상태로 유지하겠습니다.")
R170_REPORT = _paste("좋습니다. 😊 이제 Orchestration V1.1은 새로운 개발을 계속하기보다 남은 검증을 마무리할 단계입니다.\n"
                     "다만 이것 때문에 지금 또 새로운 개발을 시작할 필요는 없습니다. 기존 기록은 보존하고, 다음에 Ledger를 정비할 때 오탐 사례로 활용하면 됩니다.\n"
                     "B는 실제 Judge 1회에 대한 비용 승인, E는 VS Code 화면 캡처가 있어야 합니다. 둘 다 아직 실행하지 않겠습니다.")
R168_DIRECTIVE = _paste("Claude Code에 전달할 승인 문구\n대상: C:\\pjt\\orchestration_v1\n\n"
                        "현재 로컬 HEAD a13c4ff 기준으로 Git Push를 승인한다.\n"
                        "4. force push, reset, rebase, merge는 금지한다.\n"
                        "유료 Judge 호출, 토큰 변경, 임시 파일 삭제, 배포 및 화면 캡처는 승인하지 않는다.")
LEDGER_FIX_DIRECTIVE = _paste("지금은 새로운 개발 지시를 내린 상황이 아닙니다. 😅\n"
                              "이번 메시지는 상태 보고가 아니라 명시적인 개발 지시다.\n\n대상: C:\\pjt\\orchestration_v1\n\n"
                              "Request Ledger가 상태 보고·인용문·붙여 넣은 이전 대화를 실제 실행 지시로 오인하는 문제를 수정해.\n"
                              "- R167~R170 및 기존 Ledger 기록은 수정하거나 삭제하지 마.\n"
                              "Push·삭제·유료 호출·화면 캡처 금지.")
NUMBERED_DIRECTIVE = _paste("이번 7694ecd 보고는 상당히 중요한 진전입니다.\n"
                            "1. PID 18700의 생성 시각, 실행 경로, 부모 프로세스 및 소유권을 다시 확인해.\n"
                            "2. 구버전 remote-agent가 서명 없는 명령을 계속 처리하는지 기존 코드와 로그로 확인해.")


def _register(tmp_path, prompt, sid="s1"):
    (tmp_path / ".claude" / "state").mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path), "PYTHONUTF8": "1"}
    subprocess.run([sys.executable, "-X", "utf8", str(HOOK_PY)], input=json.dumps({"prompt": prompt, "session_id": sid}),
                   text=True, encoding="utf-8", env=env, capture_output=True, check=True, timeout=60)
    led = tmp_path / ".claude" / "state" / "request-ledger.json"
    return json.loads(led.read_text(encoding="utf-8"))["requests"] if led.exists() else []


def test_pasted_status_reports_not_registered(tmp_path):
    for i, p in enumerate((R167_REPORT, R169_REPORT, R170_REPORT)):
        assert _register(tmp_path, p, sid=f"r{i}") == []
    raw = [json.loads(l) for l in (tmp_path / ".claude/logs/ledger-raw.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["classification"] for r in raw] == ["pasted_report"] * 3   # 원문은 raw 에 보존


def test_pasted_directives_registered_without_negated_approval(tmp_path):
    for i, p in enumerate((R168_DIRECTIVE, LEDGER_FIX_DIRECTIVE, NUMBERED_DIRECTIVE)):
        _register(tmp_path, p, sid=f"d{i}")
    reqs = json.loads((tmp_path / ".claude/state/request-ledger.json").read_text(encoding="utf-8"))["requests"]
    assert [(r["classification"], r["status"]) for r in reqs] == [("execute", "pending")] * 3
    assert reqs[0]["desc"].startswith("\n\n<pasted_content")   # desc 는 원문 그대로


def test_own_text_decides_and_real_approval_still_required(tmp_path):
    reqs = _register(tmp_path, "이 로그 보고 고쳐줘" + R169_REPORT, sid="o1")
    assert [(r["classification"], r["status"]) for r in reqs] == [("execute", "pending")]   # 붙여 넣은 '유료' 무시
    reqs = _register(tmp_path, "운영 DB에 오늘 배포해줘", sid="o2")
    assert reqs[-1]["status"] == "approval_required"                                        # 실제 위험 지시는 보호
    assert len(_register(tmp_path, "그만해", sid="o3")) == 2                                  # 짧은 취소는 그대로
    assert len(_register(tmp_path, "This session is being continued from a previous conversation that ran out of"
                                   " context. 수정해줘", sid="o4")) == 2                     # 요약 이어가기 = 사용자 지시 아님


def test_gate_points_to_invalid_registration_and_protects_approval(tmp_path):
    _proj(tmp_path, [{"id": "R1", "desc": "상태 보고", "status": "pending"},
                     {"id": "R2", "desc": "유료 호출", "status": "approval_required"}])
    gate = _run(tmp_path, "gate")
    assert gate.returncode == 2 and "invalid-registration" in gate.stderr and "PASS 로 닫지 말고" in gate.stderr
    refused = _run(tmp_path, "invalid-registration", "R2", "--reason", "x")
    assert refused.returncode == 2
    assert _run(tmp_path, "invalid-registration", "R1", "--reason", "붙여 넣은 상태 보고", "--detected-by", "stop-gate").returncode == 0
    assert _run(tmp_path, "gate").returncode == 0
    reqs = json.loads((tmp_path / ".claude/state/request-ledger.json").read_text(encoding="utf-8"))["requests"]
    assert [r["status"] for r in reqs] == ["invalid_registration", "approval_required"]
