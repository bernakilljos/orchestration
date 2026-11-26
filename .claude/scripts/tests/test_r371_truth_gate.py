"""R371 C1 — 보고 진실 게이트: 실제 상태와 어긋난 보고 주장을 막는다."""
import importlib.util
from pathlib import Path

_P = Path(__file__).resolve().parents[1] / "ai-collab-report.py"
_spec = importlib.util.spec_from_file_location("ai_collab_report_truth", _P)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)
import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _known_remote_branch(monkeypatch):
    """ea40d9c9(2026-11-26) 뒤로 원격 기본 브랜치를 모르면 BLOCKED — 이 파일의 시험은 _git 을 가짜로 바꿔
    origin/HEAD 확인까지 빈 값이 되어 watermark 검사 전에 BLOCKED 로 끝났다 (CI run 45643771016 Windows 3건).
    여기 시험의 대상은 브랜치 해석이 아니라 시각 비교이므로 브랜치를 고정한다 (lottoclaude 동일 수정 역반영)."""
    monkeypatch.setattr(m, "_remote_ref", lambda: "origin/main")


import subprocess

# R375 2차 검토 P1 (2026-11-25): 고정 SHA(f0a81e76…) 는 얕은 checkout(CI · fetch-depth 1) 에 없어 «없는 커밋» 위반이
#   덤으로 붙어 Windows 필수 job 이 4회 연속 실패 → 어느 checkout 에나 있는 현재 HEAD 를 쓴다 (게이트 판정은 그대로)
SHA = subprocess.run(["git", "-C", str(Path(__file__).resolve().parent), "rev-parse", "HEAD"],
                     capture_output=True, text=True, check=True).stdout.strip()


def doc(status="PARTIAL", head=SHA, body=""):
    return f'---\nrequest_id: "R1"\nhead_commit: "{head}"\nstatus: "{status}"\n---\n# 보고\n{body}\n'


def test_installed_claim_blocked_when_not_installed():
    t = doc(body="관리자 실행기 **INSTALLED** · installed:true")
    assert m.truth_violations(t, installed=False)
    assert not m.truth_violations(t, installed=True)
    assert m.truth_violations(t, installed=None)           # R371 후속: 확인 불가(UNKNOWN)인데 설치 주장 = 위반


def test_followup_multiline_delete_missing_head_fake_sha():
    """R371 후속 리뷰 3건: 주장·경로가 다른 줄 · head 누락 · 형식만 40자리인 없는 커밋."""
    t = doc(body="R363 결과: 삭제 완료\n대상: C:\\Windows\\System32\\powershell")
    assert m.truth_violations(t, exists=lambda p: True)
    assert not m.truth_violations(t, exists=lambda p: False)
    no_head = '---\nrequest_id: "R1"\nstatus: "PASS"\n---\n# 보고\n'
    assert any("누락" in v for v in m.truth_violations(no_head))
    fake = doc("PASS", head="0" * 40)
    assert any("없는 커밋" in v for v in m.truth_violations(fake, commit_exists=lambda s: False))
    assert not m.truth_violations(doc("PASS"), commit_exists=lambda s: True)


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


def _batch_log(times):
    rows = sorted(times.items(), key=lambda kv: -int(kv[1]))
    return chr(10).join(f"@@CT {t}{chr(10)}{chr(10)}{path}" for path, t in rows)


def test_r372_pending_watermark_by_git_history(monkeypatch):
    """R372: 세션 시작 미처리 목록 — 보고서가 지시·리뷰보다 나중에 올라갔으면 처리된 판 · 리뷰 approved 는 제외."""
    times = {".ai-collab/requests/R1.md": "100", ".ai-collab/reports/R1.md": "200",       # 보고됨
             ".ai-collab/requests/R2.md": "300", ".ai-collab/reports/R2.md": "200",       # 보고 뒤 지시가 바뀜
             ".ai-collab/reviews/R3.md": "500", ".ai-collab/reports/R3.md": "400",        # 리뷰가 더 새로움
             ".ai-collab/reviews/R4.md": "500"}

    def fake_git(*a):
        if a[:2] == ("log", "-1"):
            return times.get(a[-1], "")
        if a[:2] == ("log", "--format=@@CT %ct"):                    # R375 5차: 경로별 시각을 git log 한 번으로
            return _batch_log(times)
        if a[0] == "fetch":
            return ""
        return ""
    monkeypatch.setattr(m, "_git", fake_git)
    monkeypatch.setattr(m, "_remote_files", lambda: {p: "b" + p[-4] for p in times if "/reports/" not in p})
    monkeypatch.setattr(m, "_state", lambda: {"seen": {}, "handled": {}, "requests": {}})
    monkeypatch.setattr(m, "_review_verdict", lambda blob: "판정 approved" if blob == "b4" else "판정 changes_requested")
    monkeypatch.setattr(m.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": 0})())
    lines = m.pending_lines()
    assert not any("R1" in x for x in lines)
    assert any("지시 R2" in x for x in lines)
    assert any("리뷰 R3" in x and "changes_requested" in x for x in lines)
    assert not any("R4" in x for x in lines)


def test_r375_poll_uses_same_git_watermark_as_pending(monkeypatch):
    """R375 후속: 대기(poll)가 손으로 쓴 보고서를 몰라 옛 지시를 계속 «새 것» 으로 돌려 wait 가 바로 끝나던 결함."""
    times = {".ai-collab/requests/R1.md": "100", ".ai-collab/reports/R1.md": "200",     # 보고됨 (state 기록 없음)
             ".ai-collab/reviews/R2.md": "300", ".ai-collab/reports/R2.md": "250",      # 리뷰가 더 새로움 → 새 것
             ".ai-collab/reviews/R3.md": "300"}                                          # approved → 할 일 없음

    def fake_git(*a):
        if a[:2] == ("log", "-1"):
            return times.get(a[-1], "")
        if a[:2] == ("log", "--format=@@CT %ct"):                    # R375 5차: 경로별 시각을 git log 한 번으로
            return _batch_log(times)
        return "body"
    saved = {}
    monkeypatch.setattr(m, "_git", fake_git)
    monkeypatch.setattr(m, "_remote_files", lambda: {p: "b" + p[-4] for p in times if "/reports/" not in p})
    monkeypatch.setattr(m, "_state", lambda: {"seen": {}, "handled": {}, "inflight": {}})
    monkeypatch.setattr(m, "_save_state", lambda st: saved.update(st))
    monkeypatch.setattr(m, "cmd_queue", lambda quiet=True: 0)
    monkeypatch.setattr(m, "_review_verdict", lambda blob: "판정 approved" if blob == "b3" else "판정 changes_requested")
    monkeypatch.setattr(m.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": 0, "stderr": ""})())
    out = []
    monkeypatch.setattr("builtins.print", lambda *a, **k: out.append(" ".join(map(str, a))))
    assert m.cmd_poll() == 0
    body = "\n".join(out)
    assert "reviews/R2.md" in body
    assert "requests/R1.md" not in body and "reviews/R3.md" not in body


def test_r375e_pending_reads_commit_times_with_one_git_log(monkeypatch):
    """R375 5차: 파일마다 git log 2회(실측 54회·7초 → 세션 시작 훅 10초 제한에서 잘림) → 한 번으로 · 결과는 같다."""
    times = {f".ai-collab/requests/R{i}.md": str(100 + i) for i in range(20)}
    times.update({f".ai-collab/reports/R{i}.md": str(300) for i in range(10)})      # 앞 10개는 보고됨
    calls = []

    def fake_git(*a):
        calls.append(a[:2])
        if a[:2] == ("log", "--format=@@CT %ct"):
            return _batch_log(times)
        return ""
    monkeypatch.setattr(m, "_git", fake_git)
    monkeypatch.setattr(m, "_remote_files", lambda: {p: "b" + p for p in times if "/reports/" not in p})
    monkeypatch.setattr(m, "_state", lambda: {"seen": {}, "handled": {}, "requests": {}})
    monkeypatch.setattr(m.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": 0})())
    lines = m.pending_lines()
    assert sum(1 for c in calls if c[0] == "log") == 1                # 20개 파일 · git log 1회
    assert sorted(int(x.split("지시 R")[1].split(":")[0]) for x in lines) == list(range(10, 20))
