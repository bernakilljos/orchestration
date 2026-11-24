"""R371 C1 — 보고 진실 게이트: 실제 상태와 어긋난 보고 주장을 막는다."""
import importlib.util
from pathlib import Path

_P = Path(__file__).resolve().parents[1] / "ai-collab-report.py"
_spec = importlib.util.spec_from_file_location("ai_collab_report_truth", _P)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

SHA = "f0a81e7690132d7458d9c59a2dcc4cd90b496b47"


def doc(status="PARTIAL", head=SHA, body=""):
    return f'---\nrequest_id: "R1"\nhead_commit: "{head}"\nstatus: "{status}"\n---\n# 보고\n{body}\n'


def test_installed_claim_blocked_when_not_installed():
    t = doc(body="관리자 실행기 **INSTALLED** · installed:true")
    assert m.truth_violations(t, installed=False)
    assert not m.truth_violations(t, installed=True)
    assert not m.truth_violations(t, installed=None)       # 확인 불가는 위반으로 단정하지 않음


def test_not_installed_statement_is_not_claim():
    assert not m.truth_violations(doc(body="실행기 installed:false · 미설치"), installed=False)


def test_delete_claim_blocked_when_target_exists():
    t = doc(body="삭제 완료 C:\\Windows\\System32\\powershell (Test-Path False)")
    assert m.truth_violations(t, exists=lambda p: True)
    assert not m.truth_violations(t, exists=lambda p: False)


def test_delete_claim_checks_path_exactly(tmp_path):
    f = tmp_path / "shadow"
    f.write_text("")
    t = doc(body=f"DELETE_DONE {f}")
    assert m.truth_violations(t)                            # 실제 파일 존재 → 위반
    f.unlink()
    assert not m.truth_violations(t)


def test_running_regression_cannot_be_pass():
    assert m.truth_violations(doc("PASS", body="회귀 게이트 2차 RUNNING"))
    assert m.truth_violations(doc("PASS"), gate_status="running")
    assert not m.truth_violations(doc("PARTIAL", body="회귀 게이트 2차 RUNNING"))
    assert not m.truth_violations(doc("PASS"), gate_status="pass")


def test_pending_head_cannot_be_pass_or_deployed():
    assert m.truth_violations(doc("PASS", head="PENDING"))
    assert m.truth_violations(doc("PARTIAL", head="PENDING", body="전파 DEPLOYED"))
    assert m.truth_violations(doc("PARTIAL", head="PENDING", body="사용자 목표 DONE"))
    assert not m.truth_violations(doc("PARTIAL", head="PENDING", body="코드 커밋은 회귀 게이트 뒤"))
    assert not m.truth_violations(doc("PASS", body="DEPLOYED"))


def test_cli_truth_check_exit_code(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text(doc("PASS", head="PENDING"), encoding="utf-8")
    good = tmp_path / "good.md"
    good.write_text(doc("PARTIAL"), encoding="utf-8")
    assert m.main(["truth-check", str(bad)]) == 1
    assert m.main(["truth-check", str(good)]) == 0
