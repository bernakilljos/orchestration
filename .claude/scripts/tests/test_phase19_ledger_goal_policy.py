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
    # 2026-11-07: R168 은 실제 push 지시 — '승인한다' 문장은 권한이 아니므로 push 는 승인 대기 · 부정된 유료·배포는 여전히 사유 아님
    assert [(r["classification"], r["status"]) for r in reqs] == [("execute", "approval_required")] + [("execute", "pending")] * 2
    assert reqs[0]["approval_reasons"] == ["git push"]
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

# ── 2026-11-07 R184~R186: 위험 단어가 요청이 아닌 줄(표 칸 · "~가 아니라" · 기대 결과 설명)에 있어도 승인 대기가 됐다 ──
# 입력 = orca.db conversations 에 남은 원문 그대로 (ledger prompt_hash 와 sha256 앞자리 일치 확인 후 저장)
FIX = Path(__file__).resolve().parent / "fixtures" / "ledger"


def _fixture(name):
    return (FIX / name).read_text(encoding="utf-8")


def _raw(tmp_path):
    return [json.loads(l) for l in (tmp_path / ".claude/logs/ledger-raw.jsonl").read_text(encoding="utf-8").splitlines()]


def test_r184_status_report_not_registered(tmp_path):
    assert _register(tmp_path, _fixture("r184.txt")) == []          # 이전: execute · approval_required ['유료']
    assert _raw(tmp_path)[-1]["classification"] == "pasted_report"  # 원문은 raw 에 보존


def test_r185_r186_registered_without_extra_approval(tmp_path):
    import hashlib
    for i, name in enumerate(("r185.txt", "r186.txt")):
        text = _fixture(name)
        reqs = _register(tmp_path, text, sid=f"f{i}")
        e = reqs[-1]
        assert (e["classification"], e["status"]) == ("execute", "pending")   # 이전: approval_required ['운영'] · ['유료']
        assert "approval_reasons" not in e
        # 원문은 저장하지 않고 길이·전체 해시로 연결 (앞 16자 = conversations.content_hash) · desc 는 기존처럼 400자
        assert e["prompt_len"] == len(text) and e["prompt_sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()
        assert e["prompt_sha256"].startswith(e["prompt_hash"]) and len(e["desc"]) == 400
        assert e["approval_basis"]["excluded"]                               # 무엇을 왜 뺐는지 남는다


def _own(tmp_path, text, sid):
    return _register(tmp_path, text, sid=sid)[-1]


def test_real_risk_requests_still_need_approval(tmp_path):
    cases = {"유료 Judge 1회 실행해줘": "유료",
             "로컬 커밋을 origin main 으로 git push 해줘": "git push",
             "어제 만든 임시 파일 삭제해줘": "삭제해",
             "운영    서버 설정 변경해줘": "운영",                    # 표처럼 보여도 요청형으로 끝나면 센다
             "승인 필요 항목인 유료 Judge 를 실행해줘": "유료",            # 상태 단어가 있어도 요청형이면 센다
             "운영이 아니라 개발 서버에 배포해줘": "배포",
             "운영 배포 승인 대기 건 진행 부탁드립니다": "운영"}         # 부정 범위 밖의 위험 단어는 센다
    for i, (text, pat) in enumerate(cases.items()):
        e = _own(tmp_path, text, f"k{i}")
        assert e["status"] == "approval_required" and pat in e["approval_reasons"], text
        assert e["approval_basis"]["lines"][0]["text"] == text.strip()


def test_quoted_approval_grants_nothing(tmp_path):
    directive = _paste("대상: C:\\pjt\\orchestration_v1\n\n이번 지시는 유료 Judge 1회 실행을 승인한다.\n유료 Judge 1회를 실행해.")
    quoted = _paste("평가자는 '이번 지시는 유료 Judge 호출을 승인한다.' 라고 썼습니다.\n아직 실행하지 않았습니다.")
    for i, p in enumerate((directive, quoted)):
        e = _register(tmp_path, p, sid=f"q{i}")[-1]
        assert e["status"] == "approval_required" and "유료" in e["approval_reasons"]   # '승인한다' 는 권한이 아니다
    assert e["approval_basis"].get("stated_scope", []) == []                                 # 인용문 속 문장은 범위로도 기록 안 함
    e0 = json.loads((tmp_path / ".claude/state/request-ledger.json").read_text(encoding="utf-8"))["requests"][0]
    assert e0["approval_basis"]["stated_scope"] == ["이번 지시는 유료 Judge 1회 실행을 승인한다."]   # 기록만


def test_constraints_are_not_requests_or_approvals(tmp_path):
    p = _paste("대상: C:\\pjt\\orchestration_v1\n\n문서 오타를 수정한다.\n\n제약:\n- 운영 설정은 그대로 둔다\n- 배포 금지\n"
               "- 유료 호출은 이번 범위 밖")
    e = _register(tmp_path, p, sid="c1")[-1]
    assert e["status"] == "pending" and e["approval_basis"]["excluded"] == {"constraint": 2, "negation": 1}
    statuses = {r["status"] for r in json.loads((tmp_path / ".claude/state/request-ledger.json")
                                                .read_text(encoding="utf-8"))["requests"]}
    assert statuses <= {"pending", "approval_required"}                                # 금지 조건이 승인 상태를 만들지 않음


def test_approval_evidence_masks_secrets(tmp_path):
    e = _own(tmp_path, "운영 DB 접속 password=hunter2pass 로 배포해줘", "m1")
    line = e["approval_basis"]["lines"][0]["text"]
    assert "[MASKED]" in line and "hunter2pass" not in line
    sys.path.insert(0, str(HOOK_PY.parent))
    import ledger_auto_register as M
    for secret in ("sk-proj-abcdefghijklmnopqrstuvwxyz123", '"password": "hunter2pass"', "비밀번호: hunter2 pass",
                   "Authorization: Basic dXNlcjpwYXNzd29yZA==", "eyJhbGciOiJIUzI1.eyJzdWIiOiIxMjM0.sigsig",
                   "postgres://admin:hunter2pass@db.local/x",
                   "glpat" + "-abcdefghijklmnop1234"):   # 가짜 값 — 정적 비밀정보 검사기 오인 방지로 실행 시 조립
        out = M._approval_basis(f"운영 DB {secret} 로 배포해줘")["lines"][0]["text"]
        assert "hunter2" not in out and "abcdefghijklmnop" not in out and "dXNlcjpw" not in out \
            and "eyJzdWIi" not in out, out


# 2026-11-07 독립 검토: 첫 설계(줄 끝 어미만 확인 · 탭/공백 3칸=표 · 줄 끝 '아님' 도 부정 범위)가 만든 우회로.
# 옛 판정기가 잡던 실제 위험 요청은 새 판정기도 잡아야 한다.
BYPASS_CASES = ("운영 DB 수정해줘 (테스트 아님)", "운영 DB 지워줘 농담 아님", "배포 해줘 (승인 대기 아님)",
                "배포 진행해줘 보류 해제", "배포해줘 승인 전이라도", "결제해줘 미확인 건 포함", "운영 반영해줘 blocked 풀고",
                "운영 DB 수정 실행 승인 요청 없이", "배포해줘 대기 중인 거 전부", "배포 진행 (승인 필요 없음)",
                "유료 호출 해줘. 승인 필요 없음", "배포   진행", "운영 DB\t수정", "항목   배포 진행",
                "승인 필요 없이 바로 배포해줘", "삭제해줘, 아니라면 보류")


def test_review_bypass_inputs_still_need_approval():
    sys.path.insert(0, str(HOOK_PY.parent))
    import ledger_auto_register as M
    for text in BYPASS_CASES:
        assert M._needs_approval(text), text


def test_polite_risky_directive_in_report_is_registered(tmp_path):
    p = _paste("작업을 마쳤습니다.\n로그를 확인했습니다.\n결과는 정상입니다.\n운영 DB 를 수정하세요.")
    e = _register(tmp_path, p, sid="p1")[-1]
    assert (e["classification"], e["status"]) == ("execute", "approval_required")   # 등록돼야 게이트가 본다


# ── 2026-11-07 잔여 위험 (5814754 후속): push 표현 누락 · 시험 설명 속 push 문자열 · '없이' 부정 범위 (R187) · 원문 평문 저장 ──
def _M():
    sys.path.insert(0, str(HOOK_PY.parent))
    import ledger_auto_register as M
    return M


DT, RF, FP = "drop" + " table", "rm" + " -rf", "git push " + "--force"   # 위험 문구는 실행 시 조립 (명령 승인 게이트·검사기 오인 방지)


def test_push_variants_need_approval():
    M = _M()
    for text in ("git  push origin main 해줘", "push origin main", "푸시 진행", "push origin main 해줘", "PUSH origin main 해줘",
                 "`git push origin main` 실행해줘", "git push -u origin feature 해줘", "다음 항목 처리:\n- 운영 DB 삭제\n- 배포 진행",
                 "백업 없이 운영 DB 삭제해줘", "아래 표현을 시험한다:\n- git push origin main 해줘"):
        assert M._needs_approval(text), text


# 2026-11-07 독립 검토 2차: 예시 목록 · '없이' · '아니라' · 인용 규칙이 만든 우회로 (직전 판정기는 모두 잡았다)
BYPASS_CASES_2 = ("다음 사례 처리해:\n- 운영 DB 삭제\n- 배포", "다음 케이스 진행:\n- 배포 진행", "아래 문장 실행:\n- git push origin main",
                  "다음 예시 반영:\n- 운영 DB 삭제", "다음 사례를 처리해라:\n- 운영 DB 삭제",
                  "다음 문장 그대로 실행해라\n1. git push origin main\n2. 배포 진행", f"아래 입력 순서대로 수행:\n- {FP} origin main",
                  f"- {RF} /data\n위 입력 처리", "- git push origin main\n위 사례를 실행한다", "- 배포 진행\n위 사례처럼 처리",
                  "git push 확인 없이 진행", "운영 db 삭제 승인 없이 진행", "배포 승인 없이 바로 실행", "삭제 후 배포 — 확인 없이 진행",
                  "배포 확인 없이 진행 바람", "git push 진행 후 결과는 로그가 아니라 요약으로 알려줘",
                  "운영 db 삭제 진행하고 로그가 아니라 요약만 남겨", "`git push origin main`을 처리", "`git push origin main` 를 돌려",
                  f"`{RF} /data` 날려", f"'{RF} /' 를 돌려", '이거 해: "운영 db 삭제해줘"', f"let's {RF} /data and it's fine",
                  f"`{DT} users`", f"`{FP}`")


def test_review2_bypass_inputs_still_need_approval():
    M = _M()
    for text in BYPASS_CASES_2:
        assert M._needs_approval(text), text
    assert DT in M._needs_approval(f"다음 입력 값을 운영 DB 에 반영:\n- {DT} users")


def test_push_mentions_are_not_requests(tmp_path):
    M = _M()
    for text in ("push origin main 은 하지 마", "- push origin main → 승인 필요", "Git  Push    origin main    완료",
                 "유료 실행 없이 검증한다", "배포 진행 없이 문서만 고친다"):
        assert M._needs_approval(text) == [], text
    assert _register(tmp_path, _paste("작업을 마쳤습니다.\ngit  push origin main 완료했습니다.\n결과는 정상입니다.")) == []
    # 의도한 과잉 판정 — 인용·예시 목록 속 push 문자열은 실제 요청과 글자로 구분할 수 없어 승인 필요로 남긴다 (독립 검토 2·3차)
    for text in ("평가에서 'push origin main' 표현을 지적했습니다",
                 "현재 판정기가 아래 표현을 놓친다고 보고했습니다.\n- git  push — 공백 두 칸\n- push origin main"):
        assert M._needs_approval(text), text


# 2026-11-07 독립 검토 3차: '없이' 창 · 인용 · 예시 목록 규칙의 우회로 (직전 판정기는 모두 잡았다)
BYPASS_CASES_3 = ("force push 경고 없이 실행해", f"{DT} 예외 없이 실행해줘", "sudo 비밀번호 없이 실행해줘", "git push 경고 없이 바로 해줘",
                  "git push 에러 없이 완료", "배포 지연 없이 해줘", "배포 사고 없이 하자", f"{RF} 흔적 없이 하자",
                  f"run `{RF} /tmp/x`", "Please run `git push`", f"just `{FP}`", f"do `{DT} users`", "`git push` 하자",
                  f"`{RF} x` 때려", "`배포` 가즈아", "'production' 으로 ㄱ", f"사용자가 `{RF} x` 라고 했어 그대로 하자",
                  f"다음 케이스 순서대로 가자:\n- {RF} build\n- push origin main", f"아래 입력 차례로 돌리자\n1. {RF} dist\n2. {DT} users",
                  f"다음 사례 순서로 하나씩 하자\n- {RF} a", f"아래 문자열 그대로 하자\n- {FP}", "다음 사례 순서로 가자\n- production 배포",
                  f"- {RF} x\n- {FP}\n\n위 사례 쭉 가자")


def test_review3_bypass_inputs_still_need_approval():
    M = _M()
    for text in BYPASS_CASES_3:
        assert M._needs_approval(text), text
    assert FP in M._needs_approval(f"{FP} 오류 없이 하자")                        # force 사유도 유지


def test_r187_paid_false_positive_fixed_push_list_kept(tmp_path):
    # R187 의 '유료 실행 없이' 오탐은 해결 · 시험 대상으로 나열한 "- 푸시 진행" 등은 실제 작업 목록과 글자로 구분할 수 없어 승인 필요 유지
    e = _register(tmp_path, _fixture("r187.txt"), sid="r187")[-1]
    assert (e["classification"], e["status"]) == ("execute", "approval_required")
    assert "유료" not in e["approval_reasons"] and set(e["approval_reasons"]) <= {"git push", "push origin", "push 진행"}


def test_stored_text_is_masked_and_hash_uses_original(tmp_path):
    import hashlib
    secret = "hunter2pass"
    prompt = f"운영 DB 접속 password={secret} 로 배포해줘\n이번 지시는 비번 {secret} 사용을 승인한다."
    e = _register(tmp_path, prompt, sid="s1")[-1]
    assert e["prompt_sha256"] == hashlib.sha256(prompt.encode("utf-8")).hexdigest()   # 감사 연결은 원문 해시
    assert e["prompt_sha256"].startswith(e["prompt_hash"])
    basis = json.dumps(e["approval_basis"], ensure_ascii=False)
    assert secret not in basis and "[MASKED]" in basis                             # 판정 줄 · stated_scope 도 가림
    _register(tmp_path, f"token={secret}AAAA 참고 메모", sid="s2")                 # 분류 불확실 → deferred
    for f in (".claude/state/request-ledger.json", ".claude/logs/ledger-raw.jsonl", ".claude/logs/ledger-deferred.jsonl"):
        text = (tmp_path / f).read_text(encoding="utf-8")
        assert secret not in text and "[MASKED]" in text, f
    M = _M()
    for s in ("비번 hunter2", "pw: hunter2", "passphrase=hunter2", "Authorization: Token hunter2abcdef", "sk_live_" + "hunter2abcdefghijk",
              "ghs_" + "hunter2abcdefghijklmn", "aws_secret_access_key = hunter2", "apikey hunter2", "key=hunter2",
              "dbPassword=hunter2", "accessToken=hunter2", "clientSecret=hunter2", "myApiKey=hunter2", "userPwd=hunter2",
              "--password hunter2", "credential=hunter2", "pw：hunter2", "xoxs-" + "hunter2abcdefg", "ya29." + "hunter2abcdefg"):
        assert "hunter2" not in M._mask(s), s
    assert M._mask("token 사용량 확인해줘") == "token 사용량 확인해줘"            # 일반 문장은 그대로


def test_dispatch_entrypoint_isolated(tmp_path):
    """settings.json 이 부르는 prompt-dispatch.py 전체 경로 — hooks · scripts/lib 를 임시 프로젝트로 복사해 실행.
    save_user_prompt 의 DB 기록까지 임시 orca.db 로 가고 운영 Ledger·DB 에는 남지 않는다."""
    import hashlib
    import shutil
    hooks = tmp_path / ".claude" / "hooks"
    shutil.copytree(HOOK_PY.parents[1], hooks, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / ".claude" / "scripts" / "lib", tmp_path / ".claude" / "scripts" / "lib",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (tmp_path / ".claude" / "state").mkdir(parents=True)
    copied = hooks / "prompt" / "ledger_auto_register.py"
    assert hashlib.sha256(copied.read_bytes()).hexdigest() == hashlib.sha256(HOOK_PY.read_bytes()).hexdigest()
    sid = "phase19-dispatch-isolated"
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path), "PYTHONUTF8": "1", "PROMPT_DISPATCH_NO_SPAWN": "1"}
    inputs = [_fixture(n) for n in ("r184.txt", "r185.txt", "r186.txt")] + ["로컬 커밋을 origin main 으로 git push 해줘"]
    for i, p in enumerate(inputs):
        subprocess.run([sys.executable, "-X", "utf8", str(hooks / "prompt-dispatch.py")],
                       input=json.dumps({"prompt": p, "session_id": f"{sid}-{i}"}), text=True, encoding="utf-8",
                       env=env, capture_output=True, check=True, timeout=120, cwd=str(tmp_path))
    reqs = json.loads((tmp_path / ".claude/state/request-ledger.json").read_text(encoding="utf-8"))["requests"]
    assert [(r["session_id"][-1], r["status"]) for r in reqs] == [("1", "pending"), ("2", "pending"), ("3", "approval_required")]
    assert reqs[-1]["approval_reasons"][0] == "git push" and all("approval_basis" in r for r in reqs)
    log = (tmp_path / ".claude/logs/prompt-dispatch.log").read_text(encoding="utf-8")
    assert "ERROR ledger-auto-register" not in log and "TIMEOUT ledger-auto-register" not in log
    with sqlite3.connect(str(tmp_path / ".claude/state/orca.db")) as c:               # 다른 훅(save_user_prompt)도 임시 DB 로
        assert c.execute("SELECT COUNT(*) FROM conversations WHERE session_id LIKE ?", (sid + "%",)).fetchone()[0] == len(inputs)
    # 운영 저장소에는 이 세션 id 가 없어야 한다
    real = ROOT / ".claude" / "state"
    for f in (real / "request-ledger.json", ROOT / ".claude/logs/ledger-raw.jsonl"):
        if f.exists():
            assert sid not in f.read_text(encoding="utf-8", errors="replace"), f
    if (real / "orca.db").exists():
        with sqlite3.connect(f"file:{real / 'orca.db'}?mode=ro", uri=True) as c:
            assert c.execute("SELECT COUNT(*) FROM conversations WHERE session_id LIKE ?", (sid + "%",)).fetchone()[0] == 0


