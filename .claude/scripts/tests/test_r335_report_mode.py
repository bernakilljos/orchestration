"""R335 사용자 보고 시점 지시 우선 — 실제 등록 훅(run)·원장 CLI·Stop 원장 게이트를 임시 폴더에서 끝까지 (모의 결과 연결 없음).

'전부 끝내고 마지막에 한 번 보고' 면 하위 1/N 완료·PARTIAL 로 Stop 이 통과하지 않고, '하나씩 보고'·'멈춰' 면 중간 멈춤을 막지 않으며,
지시가 없으면 기존 기본 동작 그대로다. 진행 불가(BLOCKED)·같은 미완료 반복은 무한 차단하지 않는다."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_r314_e2e_scenarios import LEDGER_PY, _cli, _prompt, _reqs  # noqa: E402 — 같은 격리 실행 도우미 재사용

SID = "s335"


def _gate(tmp, active=False):
    return _cli(tmp, LEDGER_PY, "gate", stdin=json.dumps({"session_id": SID, "stop_hook_active": active}))


def _item(tmp, rid, n, state="done"):
    assert _cli(tmp, LEDGER_PY, "item", rid, str(n), state, "--evidence", "임시 폴더 시험 통과").returncode == 0


def test_final_once_partial_after_first_of_three_keeps_working(tmp_path):
    out = _prompt(tmp_path, "1. 로그인 오류 수정\n2. 목록 정렬 수정\n3. 저장 버튼 수정\n3개 전부 끝내고 마지막에 보고해", SID)
    assert "[ledger] +" in out
    r = _reqs(tmp_path)[-1]
    rid = r["id"]
    assert r["report_mode"] == "final_once" and len(r["items"]) == 3
    _item(tmp_path, rid, 1)
    # 1개만 끝내고 PARTIAL 로 적으면 — 종전엔 '사실대로 적은 미완료' 로 Stop 통과(최종 보고처럼 멈춤)
    assert _cli(tmp_path, LEDGER_PY, "complete", rid, "--evidence", "1번만 완료", "--verification", "PARTIAL").returncode == 1
    g = _gate(tmp_path)
    assert g.returncode == 2 and "[사용자 지시]" in g.stderr and rid in g.stderr
    # 남은 2·3번까지 하면 PASS · Stop 통과 (최종 1회 보고 시점)
    _item(tmp_path, rid, 2)
    _item(tmp_path, rid, 3)
    assert _cli(tmp_path, LEDGER_PY, "complete", rid, "--evidence", "3개 완료·검증", "--verification", "PASS").returncode == 0
    assert _gate(tmp_path).returncode == 0


def test_five_sub_items_one_open_refuses_pass(tmp_path):
    _prompt(tmp_path, "1. a 수정\n2. b 수정\n3. c 수정\n4. d 수정\n5. e 수정\n전부 끝내고 보고해", SID)
    rid = _reqs(tmp_path)[-1]["id"]
    for n in (1, 2, 3, 4):
        _item(tmp_path, rid, n)
    assert _cli(tmp_path, LEDGER_PY, "complete", rid, "--evidence", "4개", "--verification", "PASS").returncode == 2
    assert _reqs(tmp_path)[-1]["status"] != "completed"
    assert _gate(tmp_path).returncode == 2


def test_each_mode_allows_intermediate_report(tmp_path):
    _prompt(tmp_path, "1. a 수정\n2. b 수정\n하나씩 보고하면서 진행해", SID)
    r = _reqs(tmp_path)[-1]
    assert r["report_mode"] == "each" and r["status"] == "pending"
    g = _gate(tmp_path)
    assert g.returncode == 0 and "완료 처리 아님" in g.stderr     # 중간 보고 허용 · 완료로 세지 않음
    assert _reqs(tmp_path)[-1]["status"] == "pending"


def test_default_without_report_instruction_unchanged(tmp_path):
    _prompt(tmp_path, "로그인 버그 고쳐줘", SID)
    r = _reqs(tmp_path)[-1]
    assert "report_mode" not in r
    assert _gate(tmp_path).returncode == 2                         # 미완료 = 차단 (기존)
    assert _cli(tmp_path, LEDGER_PY, "complete", r["id"], "--evidence", "원인 미확인", "--verification", "PARTIAL").returncode == 1
    assert _gate(tmp_path).returncode == 0                         # 근거 있는 PARTIAL = 멈춤 허용 (기존)


def test_latest_user_instruction_changes_contract(tmp_path):
    _prompt(tmp_path, "1. a 수정\n2. b 수정\n전부 끝내고 마지막에 한 번만 보고해", SID)
    rid = _reqs(tmp_path)[-1]["id"]
    assert _gate(tmp_path).returncode == 2
    out = _prompt(tmp_path, "이제 하나씩 보고해", SID)              # 최신 명시 지시 → 같은 세션 열린 요청 계약 변경
    assert rid in out and next(r for r in _reqs(tmp_path) if r["id"] == rid)["report_mode"] == "each"
    assert _gate(tmp_path).returncode == 0
    _prompt(tmp_path, "멈춰", SID)
    assert next(r for r in _reqs(tmp_path) if r["id"] == rid)["report_mode"] == "stop"
    assert _gate(tmp_path).returncode == 0
    # 다른 세션의 지시는 이 세션 계약을 바꾸지 않음
    _prompt(tmp_path, "1. x 수정\n전부 끝내고 보고해", SID)
    rid2 = _reqs(tmp_path)[-1]["id"]
    _prompt(tmp_path, "하나씩 보고해", "other-session")
    assert next(r for r in _reqs(tmp_path) if r["id"] == rid2)["report_mode"] == "final_once"


def test_final_once_blocked_and_repeat_do_not_loop_forever(tmp_path):
    _prompt(tmp_path, "1. 외부 연동 수정\n2. 문서 갱신\n전부 끝내고 보고해", SID)
    rid = _reqs(tmp_path)[-1]["id"]
    # 진행 불가 사유가 있는 BLOCKED = 멈춤 허용 (사실대로 · 완료 아님)
    assert _cli(tmp_path, LEDGER_PY, "complete", rid, "--evidence", "승인 대기 appr-x", "--verification", "BLOCKED").returncode == 1
    assert _gate(tmp_path).returncode == 0
    # 같은 미완료(PARTIAL)로 Stop 이 연달아 막히면 3회 뒤 통과 — 모델 비용 무한 소모 방지 (항목은 미완료 유지)
    _prompt(tmp_path, "1. c 수정\n2. d 수정\n모두 완료한 뒤 보고해줘", SID)
    rid2 = _reqs(tmp_path)[-1]["id"]
    _cli(tmp_path, LEDGER_PY, "complete", rid2, "--evidence", "진행 중", "--verification", "PARTIAL")
    rcs = [_gate(tmp_path, active=(i > 0)).returncode for i in range(5)]
    assert rcs[:3] == [2, 2, 2] and 0 in rcs[3:]
    assert next(r for r in _reqs(tmp_path) if r["id"] == rid2)["status"] != "completed"


def test_pasted_reference_does_not_set_mode_without_own_instruction(tmp_path):
    """붙여 넣은 참고 글 속 '전부 끝내고 보고' 문구가 아니라, 사용자가 직접 쓴 지시가 계약을 정한다."""
    text = ("버그 고쳐줘\n<pasted_content id=\"a1\">\n예전 대화: 전부 끝내고 마지막에 보고해 라고 했었음\n</pasted_content id=\"a1\">")
    _prompt(tmp_path, text, SID)
    assert "report_mode" not in _reqs(tmp_path)[-1]
