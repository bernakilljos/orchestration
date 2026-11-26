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


@pytest.fixture(autouse=True)
def _isolated_collab_files(monkeypatch, tmp_path):
    """R375 6차: pending·poll 이 결과 캐시·생존 표시를 쓰게 됐다 — 시험이 실제 .claude/state 에 쓰지 않도록 격리."""
    monkeypatch.setattr(m, "PENDING_CACHE", tmp_path / "pending.json", raising=False)
    monkeypatch.setattr(m, "WAIT_HB", tmp_path / "wait.json", raising=False)
    monkeypatch.setattr(m, "REFRESH_LOCK", tmp_path / "refresh.lock", raising=False)
    monkeypatch.setattr(m, "LEDGER", tmp_path / "ledger.json")
    monkeypatch.setattr(m, "GIT_CACHE", tmp_path / "gitcache.json", raising=False)
    monkeypatch.setattr(m, "WAIT_DIR", tmp_path / "wait.d", raising=False)
    if hasattr(m, "_GC"):
        m._GC.clear()


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


def _batch_log(times, hashes=None):
    rows = sorted(times.items(), key=lambda kv: -int(kv[1]))
    hashes = hashes or {}
    return chr(10).join(f"@@CT {t}{(' ' + hashes[path]) if path in hashes else ''}{chr(10)}{chr(10)}{path}"
                        for path, t in rows)


from datetime import timedelta as _td  # noqa: E402

_SEEN_C = "a" * 40
_NEW_C = "b" * 40
_SRC_C = "c" * 40


def _fm(**kv):
    return "---\n" + "".join(f'{k}: "{v}"\n' for k, v in kv.items()) + "---\n본문\n"


class _FakeRepo:
    """공용 가짜 저장소 (R375 7차: 응답 계약 = 보고서 head 커밋 존재 + 지시·리뷰 커밋의 후손).
    times: 경로→커밋 시각 · src: 경로→그 경로를 마지막으로 바꾼 커밋 · blobs: blob→본문 · heads: rid→보고서 head_commit
    commits: 저장소에 있는 커밋 · anc(a, b): a 가 b 의 조상인가 (기본 True)."""

    def __init__(self, times, blobs=None, heads=None, commits=None, src=None, anc=None):
        self.times, self.blobs, self.heads = times, blobs or {}, heads or {}
        self.commits = set(commits if commits is not None else (_SEEN_C, _NEW_C, _SRC_C))
        self.src, self.anc, self.calls = src or {}, anc or (lambda a, b: True), []

    def git(self, *a):
        self.calls.append(a[:2])
        if a[0] == "log" and a[1].startswith("--format=@@CT"):
            return _batch_log(self.times, self.src)
        if a[:2] == ("cat-file", "-p"):
            return self.blobs.get(a[2], "")
        if a[0] == "rev-parse" and a[-1].endswith("^{commit}"):
            ref = a[-1][:-len("^{commit}")].lower()
            hit = [c for c in self.commits if c.startswith(ref)]
            return hit[0] if len(hit) == 1 else ""
        if a[0] == "show" and "/reports/" in a[1]:
            rid = a[1].rsplit("/", 1)[1][:-3]
            return _fm(request_id=rid, head_commit=self.heads[rid], status="PARTIAL") if rid in self.heads else ""
        return ""

    def install(self, monkeypatch, remote, state=None, fetch_rc=0):
        monkeypatch.setattr(m, "_git", self.git)
        monkeypatch.setattr(m, "_git_batch", lambda lines, mode: b"", raising=False)
        monkeypatch.setattr(m, "_git_ok", lambda *a: self.anc(a[-2], a[-1]) if a[:2] == ("merge-base", "--is-ancestor") else True,
                            raising=False)
        monkeypatch.setattr(m, "_remote_files", lambda: dict(remote))
        st = state or {"seen": {}, "handled": {}, "inflight": {}, "requests": {}}
        monkeypatch.setattr(m, "_state", lambda: st)
        monkeypatch.setattr(m.subprocess, "run", lambda *a, **k: type("R", (), {"returncode": fetch_rc, "stderr": ""})())
        if hasattr(m, "_GC"):
            m._GC.clear()
            m.GIT_CACHE.unlink(missing_ok=True)      # 조상 관계 캐시는 실제로는 불변 — 시험마다 다른 가짜 그래프라 비움
        return self


def test_r372_pending_watermark_by_git_history(monkeypatch):
    """R372: 세션 시작 미처리 목록 — 보고서가 지시·리뷰보다 나중에 올라갔으면 처리된 판 · 리뷰 approved 는 제외."""
    times = {".ai-collab/requests/R1.md": "100", ".ai-collab/reports/R1.md": "200",       # 보고됨
             ".ai-collab/requests/R2.md": "300", ".ai-collab/reports/R2.md": "200",       # 보고 뒤 지시가 바뀜
             ".ai-collab/reviews/R3.md": "500", ".ai-collab/reports/R3.md": "400",        # 리뷰가 더 새로움
             ".ai-collab/reviews/R4.md": "500"}
    _FakeRepo(times, heads={"R1": _NEW_C, "R2": _NEW_C, "R3": _NEW_C}).install(
        monkeypatch, {p: "b" + p[-4] for p in times if "/reports/" not in p})
    monkeypatch.setattr(m, "_verdict_of", lambda blob: "approved" if blob == "b4" else "changes_requested")
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
    repo = _FakeRepo(times, heads={"R1": _NEW_C, "R2": _NEW_C})
    repo.install(monkeypatch, {p: "b" + p[-4] for p in times if "/reports/" not in p})
    saved = {}
    monkeypatch.setattr(m, "_save_state", lambda st: saved.update(st))
    monkeypatch.setattr(m, "cmd_queue", lambda quiet=True: 0)
    monkeypatch.setattr(m, "_verdict_of", lambda blob: "approved" if blob == "b3" else "changes_requested")
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
    repo = _FakeRepo(times, heads={f"R{i}": _NEW_C for i in range(10)})
    repo.install(monkeypatch, {p: "b" + p for p in times if "/reports/" not in p})
    lines = m.pending_lines()
    assert sum(1 for c in repo.calls if c[0] == "log") == 1                # 20개 파일 · git log 1회
    assert sorted(int(x.split("지시 R")[1].split(":")[0]) for x in lines) == list(range(10, 20))


# ---- R375 6차 검토 F/G/J: 판정 공통화 · 정확 판정 · 문서만 고친 보고 · fetch 실패 · 완료 요청 · 네트워크 없는 프롬프트 알림 ----
def _review_repo(monkeypatch, report_head, verdict="changes_requested", ledger=None, fetch_rc=0, collab=None,
                 commits=None, anc=None):
    """리뷰(시각 300) 뒤에 보고서(시각 400)가 올라간 상황 · 보고서 head_commit 만 바꿔 가며 본다."""
    times = {".ai-collab/reviews/R9.md": "300", ".ai-collab/reports/R9.md": "400"}
    repo = _FakeRepo(times, blobs={"rv9": _fm(request_id="R9", verdict=verdict, reviewed_commit=_SEEN_C)},
                     heads={"R9": report_head}, commits=commits, src={".ai-collab/reviews/R9.md": _SRC_C}, anc=anc)
    repo.install(monkeypatch, {".ai-collab/reviews/R9.md": "rv9"},
                 state={"seen": {}, "handled": {}, "inflight": {}, "requests": collab or {}}, fetch_rc=fetch_rc)
    monkeypatch.setattr(m, "_load", lambda p, d: ledger if (p == m.LEDGER and ledger is not None) else
                        (d if p == m.LEDGER else m.json.loads(p.read_text(encoding="utf-8")) if p.is_file() else d))
    return repo


def test_r375f_doc_only_report_edit_does_not_hide_review(monkeypatch):
    """보고서를 리뷰 뒤에 다시 올렸어도 head_commit 이 리뷰가 본 커밋 그대로면(문서만 수정) 리뷰는 미처리."""
    _review_repo(monkeypatch, report_head=_SEEN_C)
    assert any("리뷰 R9" in x for x in m.pending_lines())
    _review_repo(monkeypatch, report_head=_NEW_C)                    # 새 작업 커밋으로 답한 보고 = 처리됨
    assert m.pending_lines() == []


def test_r375f_poll_and_pending_share_one_classifier(monkeypatch):
    """같은 입력에서 poll 이 «새 것» 으로 전달하는 집합 = pending 이 알리는 집합 (따로 판정하지 않음)."""
    for head, expect in ((_SEEN_C, True), (_NEW_C, False)):
        _review_repo(monkeypatch, report_head=head)
        monkeypatch.setattr(m, "_save_state", lambda st: None)
        monkeypatch.setattr(m, "cmd_queue", lambda quiet=True: 0)
        out = []
        monkeypatch.setattr("builtins.print", lambda *a, **k: out.append(" ".join(map(str, a))))
        rc = m.cmd_poll()
        delivered = "reviews/R9.md" in "\n".join(out) and rc == 0
        listed = any("리뷰 R9" in x for x in m.pending_lines())
        assert delivered == listed == expect


def test_r375f_verdict_requires_exact_value(monkeypatch):
    """'Approved'·'not_approved' 처럼 비슷한 값은 승인이 아님 (endswith 판정 제거)."""
    for v, want in (("approved", "approved"), ("Approved", ""), ("not_approved", ""), ("changes_requested", "changes_requested")):
        _FakeRepo({}, blobs={"x" * 40: _fm(verdict=v, reviewed_commit=_SEEN_C)}).install(monkeypatch, {})
        assert m._verdict_of("x" * 40) == want, v
    _review_repo(monkeypatch, report_head=_SEEN_C, verdict="not_approved")
    assert any("리뷰 R9" in x for x in m.pending_lines())          # 승인 아님 → 알림 유지


def test_r375f_fetch_failure_is_unknown_not_empty(monkeypatch):
    """fetch 실패 + 받아 둔 판 기준 할 일 없음 → 빈 목록(=없음) 이 아니라 확인 불가를 알림."""
    _review_repo(monkeypatch, report_head=_NEW_C, fetch_rc=128)
    lines = m.pending_lines()
    assert lines and "원격 확인 실패" in lines[0] and "UNKNOWN" in lines[-1]


def test_r375f_review_on_completed_request_is_flagged(monkeypatch):
    """완료(PASS) 보고된 요청에 새 changes_requested 가 오면 «원장 재개» 로 표시 (blob 단위)."""
    _review_repo(monkeypatch, report_head=_SEEN_C, collab={"R9": {"status": "PASS"}})
    line = next(x for x in m.pending_lines() if "리뷰 R9" in x)
    assert "완료 처리된 요청" in line and "blob rv9" in line
    # 원장에 같은 번호의 «다른» 대화 요청이 completed 여도 협업 보고가 PARTIAL 이면 완료 표시 X (ID 충돌 실측)
    _review_repo(monkeypatch, report_head=_SEEN_C, ledger={"requests": [{"id": "R9", "status": "completed"}]},
                 collab={"R9": {"status": "PARTIAL"}})
    assert "완료 처리된 요청" not in next(x for x in m.pending_lines() if "리뷰 R9" in x)


def test_r375f_short_head_sha_same_commit_is_not_answer(monkeypatch):
    """보고서 head_commit 이 8자리 짧은 SHA 여도 리뷰가 본 커밋과 같으면 답한 것이 아님 · SHA 가 아닌 값(PENDING)도 답 아님."""
    for head, pending in ((_SEEN_C[:8], True), ("PENDING", True), (_NEW_C[:8], False)):
        _review_repo(monkeypatch, report_head=head)
        assert any("리뷰 R9" in x for x in m.pending_lines()) == pending, head


# ---- R375 7차 검토 P0 수신: 공통 응답 계약 (커밋 존재·조상 관계) ----
def test_r375g_answer_needs_existing_commit(monkeypatch):
    """형식만 맞는 40자리 head (저장소에 없음) 로는 리뷰·지시가 가려지지 않는다."""
    _review_repo(monkeypatch, report_head="d" * 40)
    assert any("리뷰 R9" in x for x in m.pending_lines())


def test_r375g_answer_needs_descendant_of_review_commit(monkeypatch):
    """보고서 head 가 리뷰를 올린 커밋의 후손이 아니면(이전·무관한 커밋) 답이 아님."""
    _review_repo(monkeypatch, report_head=_NEW_C, anc=lambda a, b: False)
    assert any("리뷰 R9" in x for x in m.pending_lines())
    _review_repo(monkeypatch, report_head=_NEW_C, anc=lambda a, b: (a, b) == (_SRC_C, _NEW_C))
    assert m.pending_lines() == []


def test_r375g_request_time_alone_is_not_answer(monkeypatch):
    """지시도 같은 계약 — 보고서가 나중이어도 head 가 SHA 가 아니면(시각만) 미처리 (state.json reported_at 단독 판정 제거)."""
    times = {".ai-collab/requests/R5.md": "100", ".ai-collab/reports/R5.md": "200"}
    st = {"seen": {}, "handled": {}, "inflight": {}, "requests": {"R5": {"reported_at": "2099-01-01T00:00:00+00:00"}}}
    _FakeRepo(times, heads={"R5": "PENDING"}).install(monkeypatch, {".ai-collab/requests/R5.md": "q5"}, state=st)
    assert any("지시 R5" in x for x in m.pending_lines())


# ---- R375 6·7차: 생존 표시 (프로세스별 파일 · 시작 시각 · 미래·손상) · 갱신 OS 잠금 · UNKNOWN ----
def _hb(pid=None, beat=None, pstart=None, **kw):
    import os as _os
    import socket
    pid = pid or _os.getpid()
    d = {"pid": pid, "host": socket.gethostname(), "root": str(m.ROOT), "interval": 300,
         "beat": (beat or m.datetime.now(m.timezone.utc)).isoformat(),
         "pstart": m._pl().proc_start(pid) if pstart is None else pstart}
    d.update(kw)
    return d


def _put_hb(d, name=None):
    import json as _j
    m.WAIT_DIR.mkdir(parents=True, exist_ok=True)
    f = m.WAIT_DIR / (name or f"{d['host']}-{d['pid']}.json")
    f.write_text(_j.dumps(d) if isinstance(d, dict) else d, encoding="utf-8")
    return f


def test_r375f_prompt_notice_no_network_and_single_refresh(monkeypatch, tmp_path):
    """프롬프트 알림: git·네트워크 호출 0 · 루프 살아 있으면 침묵 · 죽었으면 캐시 줄 · 오래된 캐시는 갱신을 띄움."""
    import json as _j

    def boom(*a, **k):
        raise AssertionError("프롬프트 경로에서 git/subprocess 호출")
    monkeypatch.setattr(m, "_git", boom)
    monkeypatch.setattr(m.subprocess, "run", boom)
    now = m.datetime.now(m.timezone.utc)
    m.PENDING_CACHE.write_text(_j.dumps({"at": (now - _td(hours=1)).isoformat(), "ok": True,
                                         "lines": ["- 리뷰 R9: 판정 changes_requested"]}), encoding="utf-8")
    f = _put_hb(_hb())
    spawned = []
    assert m.prompt_notice(spawn=spawned.append) == "" and not spawned        # 살아 있는 루프 = 침묵 · 중복 X
    _put_hb(_hb(beat=now - _td(hours=2)), f.name)                             # 오래된 박동 = 죽은 루프
    t = m.prompt_notice(spawn=spawned.append)
    assert "리뷰 R9" in t and "대기 루프 꺼짐" in t and len(spawned) == 1


def test_r375f_dead_pid_heartbeat_is_not_alive(monkeypatch):
    _put_hb(_hb(pid=2 ** 22 + 7, pstart=""))
    w = m.wait_alive()
    assert not w["alive"] and "종료" in w["why"]


def test_r375f_wait_writes_heartbeat_and_clears_own(monkeypatch):
    """wait 는 주기마다 생존 표시를 쓰고 끝나면 자기 표시만 지운다."""
    seen = []

    def fake_poll():
        seen.append(m.wait_alive()["alive"])
        return 0
    monkeypatch.setattr(m, "cmd_poll", fake_poll)
    assert m.cmd_wait(interval=1, max_sec=5) == 0
    assert seen == [True] and not m._hb_file().exists()


def test_r375g_two_loops_do_not_clobber_each_other(monkeypatch):
    """다른 세션의 살아 있는 루프 표시는 내 루프가 끝나도 남고, 그 루프 덕에 alive 가 유지된다 (단일 파일 덮어쓰기 경합 제거)."""
    import subprocess as _sp
    import sys as _sys
    other = _sp.Popen([_sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        _put_hb(_hb(pid=other.pid))
        monkeypatch.setattr(m, "cmd_poll", lambda: 0)
        assert m.cmd_wait(interval=1, max_sec=5) == 0
        assert not m._hb_file().exists()
        w = m.wait_alive()
        assert w["alive"] and w["pid"] == other.pid
    finally:
        other.kill()
        other.wait()


def test_r375g_future_corrupt_and_reused_pid_heartbeats(monkeypatch):
    """미래 박동·손상 파일·pid 재사용(시작 시각 다름) = alive 근거 아님 · 루프 시작 때 이 장비의 죽은 표시만 정리."""
    import os as _os
    now = m.datetime.now(m.timezone.utc)
    _put_hb(_hb(beat=now + _td(hours=1)), "fut.json")
    assert not m.wait_alive()["alive"]
    _put_hb("{깨진", "bad.json")
    assert not m.wait_alive()["alive"]
    import socket
    reused = _put_hb(_hb(pstart="1"), f"{socket.gethostname()}-999999.json")   # 살아 있는 pid 이지만 다른 시작 시각
    w = m.wait_alive()
    assert not w["alive"]
    assert m._hb_prune() >= 1 and not reused.exists()


def test_r375g_refresh_lock_held_blocks_spawn_and_is_not_deleted(monkeypatch):
    """갱신 OS 잠금을 다른 프로세스가 쥐고 있으면 띄우지 않고, 갱신 자식도 아무것도 쓰지 않는다 · 잠금 파일은 지우지 않음."""
    import subprocess as _sp
    import sys as _sys
    holder = _sp.Popen([_sys.executable, "-c",
                        "import importlib.util as u,sys,time;"
                        "s=u.spec_from_file_location('p',sys.argv[1]);m=u.module_from_spec(s);s.loader.exec_module(m);"
                        "fd=m.try_lock(sys.argv[2]);print('L' if fd is not None else 'X',flush=True);time.sleep(30)",
                        str(Path(m.__file__).resolve().parent / "lib" / "proc_lock.py"), str(m.REFRESH_LOCK)],
                       stdout=_sp.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "L"
        spawned = []
        assert m._spawn_refresh(spawn=spawned.append) is False and not spawned
        monkeypatch.setattr(m, "pending_lines", lambda *a, **k: (_ for _ in ()).throw(AssertionError("잠금 없이 실행")))
        assert m.cmd_refresh() == 0 and not m.PENDING_CACHE.exists()
    finally:
        holder.kill()
        holder.wait()
    assert m.REFRESH_LOCK.exists()
    spawned = []
    assert m._spawn_refresh(spawn=spawned.append) is True and len(spawned) == 1


def test_r375g_notice_unknown_when_no_cache(monkeypatch):
    """확인 결과가 없거나 손상되면 «없음» 대신 UNKNOWN 을 바로 (응답 지연 없이) 알림."""
    spawned = []
    t = m.prompt_notice(spawn=spawned.append)
    assert "UNKNOWN" in t and "대기 루프 꺼짐" in t and len(spawned) == 1
    m.PENDING_CACHE.write_text("{깨진", encoding="utf-8")
    assert "UNKNOWN" in m.prompt_notice(spawn=spawned.append)
