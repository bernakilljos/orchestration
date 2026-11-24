"""R258 (2026-11-16) — 자기 산출물 자동 정리 · 불필요한 자기 승인 요청 자동 취소.

사용자 지시: "자동 승인 X · 자기 요청 자동 취소 O · 소유를 확인한 산출물만 삭제". 운영 DB·운영 임시 폴더는 쓰지 않는다
(임시 폴더 = tmp_path 아래 가짜 TEMP · 승인 DB = ORCHESTRATION_ROOT 임시).
"""
from __future__ import annotations

import importlib.util
import os
import re
import sqlite3
import tempfile
import time
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks" / "prompt"))
from _common import bash_exe  # noqa: E402  R346 후속 8: ["bash",…] 는 Windows 에서 System32 WSL 실행기가 먼저 잡힘

KIT = Path(__file__).resolve().parents[3]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


gate = _load("gate_r258", KIT / ".claude/scripts/approval-gate.py")
oc = _load("oc_r258", KIT / ".claude/scripts/own-cleanup.py")
SID = "11111111-2222-3333-4444-555555555555"
REAL_BIRTH = oc._birth
OLD_SID = "99999999-8888-7777-6666-555555555555"


@pytest.fixture
def env(tmp_path, monkeypatch):
    temp = tmp_path / "T"
    proj = tmp_path / "proj"
    for p in (temp, proj / ".claude" / "state", proj / ".claude" / "logs"):
        p.mkdir(parents=True)
    monkeypatch.setattr(tempfile, "tempdir", str(temp))
    monkeypatch.setattr(oc, "ROOT", proj)
    monkeypatch.setattr(oc, "STATE", proj / ".claude/state/own-cleanup.json")
    monkeypatch.setattr(oc, "REG", proj / ".claude/state/own-artifacts.json")
    monkeypatch.setattr(oc, "LOG", proj / ".claude/logs/own-cleanup.log")
    monkeypatch.setattr(oc, "PROG", proj / ".claude/state/own-cleanup-progress.json")
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.setenv("ORCHESTRATION_ROOT", str(proj))
    with sqlite3.connect(proj / ".claude/state/orca.db") as c:
        c.execute("CREATE TABLE tasks (task_id TEXT PRIMARY KEY, task_file TEXT NOT NULL, status TEXT NOT NULL, "
                  "created_at INTEGER NOT NULL, completed_at INTEGER, approval_state TEXT DEFAULT 'not_required', "
                  "risk_category TEXT, risk_detail TEXT, approved_at INTEGER, approved_by TEXT)")
    monkeypatch.setattr(oc, "_gate", lambda: gate)
    # 시험 폴더는 방금 만들어져 같은 PC·CI 러너의 무관한 프로세스(작업 위치 못 읽음)가 «폴더 생성 뒤 시작» 규칙에 걸린다
    #   (CI run 45507681757 · 로컬 find.exe/bash.exe) → 기본은 생성 시각 고정 · 규칙 자체는 real_birth 시험이 검증
    monkeypatch.setattr(oc, "_birth", lambda p: time.time() + 86400)
    return temp, proj


def _old(p: Path, age: float):
    t = time.time() - age
    for base, dirs, files in os.walk(p):
        for n in dirs + files:
            os.utime(os.path.join(base, n), (t, t))
    os.utime(p, (t, t))


def _mk(p: Path, files=("a.txt", "sub/b.txt"), readonly=False):
    for f in files:
        q = p / f
        q.parent.mkdir(parents=True, exist_ok=True)
        q.write_text("x", encoding="utf-8")
        if readonly:
            os.chmod(q, 0o444)
    return p


# ── 1) 정리 ───────────────────────────────────────────────────────────
def test_kit_temp_idle_removed_recent_kept_readonly_ok(env):
    temp, _ = env
    old = _mk(temp / "r256-kit-old1", readonly=True)        # git 객체처럼 읽기 전용
    _old(old, 2 * 3600)
    new = _mk(temp / "agd-kit-new1")                         # 방금 = 사용 중
    other = _mk(temp / "someone-else")                       # kit 이름이 아님
    _old(other, 30 * 86400)
    r = oc.run(SID)
    assert not old.exists() and new.exists() and other.exists()
    assert any(k["path"] == str(new) and "사용 중" in k["why"] for k in r["kept"])


def test_ended_scratchpad_only_same_project_not_current(env):
    temp, _ = env
    mine, other_proj = temp / "claude" / "projA", temp / "claude" / "projB"
    cur = _mk(mine / SID / "scratchpad")
    ended = _mk(mine / OLD_SID / "scratchpad")
    task_out = _mk(mine / OLD_SID / "tasks", ("t.output",))
    live_other = _mk(other_proj / OLD_SID / "scratchpad")
    for p in (cur, ended, task_out, live_other):
        _old(p, 3 * 86400)
    oc.run(SID)
    assert not ended.exists()                       # 같은 프로젝트의 끝난 세션
    assert cur.exists()                             # 지금 세션
    assert task_out.exists()                        # scratchpad 밖 (하네스 출력)
    assert live_other.exists()                      # 다른 프로젝트 세션 (살아 있을 수 있음)


def test_without_session_scratchpads_untouched(env):
    temp, _ = env
    ended = _mk(temp / "claude" / "projA" / OLD_SID / "scratchpad")
    _old(ended, 3 * 86400)
    oc.run("")
    assert ended.exists()


def test_registered_artifact_and_outside_temp_refused(env, tmp_path):
    temp, proj = env
    art = _mk(temp / "my-repro-x")
    assert "registered" in oc.register(str(art), SID)
    assert "error" in oc.register(str(proj / ".claude"), SID)            # 임시 폴더 밖 = 등록 거부
    assert "error" in oc.register(str(temp), SID)                        # 임시 폴더 자체 = 거부
    oc.run(SID)
    assert art.exists()                                                   # 10분 안 = 사용 중
    _old(art, 3600)
    oc.run(SID)
    assert not art.exists() and oc._registered() == []


def test_link_inside_temp_removed_without_following(env, tmp_path):
    temp, proj = env
    keep = _mk(tmp_path / "outside-precious")
    box = _mk(temp / "tgt-iso-link")
    link = box / "lnk"
    try:
        os.symlink(keep, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        import subprocess
        if subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(keep)], capture_output=True).returncode:
            pytest.skip("링크·정션 생성 불가")
    _old(box, 2 * 3600)
    oc.run(SID)
    # 바깥 원본 보존을 먼저 따로 확인 — 예전 한 줄 and 는 box 가 남으면 단락돼 원본 확인을 건너뛰었다 (2026-11-18 3.11 실측)
    assert (keep / "a.txt").exists() and (keep / "sub" / "b.txt").exists()
    assert not box.exists()


def test_protected_project_inside_temp_kept(env, monkeypatch):
    temp, _ = env
    fake_proj = _mk(temp / "tgt-iso-proj")              # 프로젝트가 임시 폴더 안에 있는 경우
    _old(fake_proj, 2 * 3600)
    monkeypatch.setattr(oc, "ROOT", fake_proj)
    r = oc.run(SID)
    assert fake_proj.exists() and any("보호" in k["why"] for k in r["kept"])


def test_dry_run_changes_nothing(env):
    temp, _ = env
    old = _mk(temp / "regress-base-x")
    _old(old, 2 * 3600)
    r = oc.run(SID, dry=True)
    assert old.exists() and r["removed"] and not oc.STATE.exists()


def test_kit_prefixes_match_kit_code():
    """정리 이름 목록 = kit 코드가 실제로 만드는 임시 폴더 이름 (근거 없는 이름을 지우지 않게)."""
    found = set()
    for p in list((KIT / ".claude/scripts").rglob("*.py")):
        if "__pycache__" in str(p):
            continue
        found |= set(re.findall(r"mkdtemp\(prefix=[\"']([^\"']+)", p.read_text(encoding="utf-8", errors="replace")))
    assert set(oc.KIT_TEMP_PREFIXES) <= found, set(oc.KIT_TEMP_PREFIXES) - found


# ── 2) 승인 요청 취소 ─────────────────────────────────────────────────
def _req(cmd, cat="data_loss"):
    return gate.new_request(cmd, cat, "d", None, "base", "scope-" + str(time.time_ns()))


def test_withdraw_only_waiting_gate_rows_keeps_record(env):
    tid = _req("x")
    r = gate.withdraw(tid, "필요 없음")
    assert r["state"] == "expired"
    st = gate.status(tid)
    assert st["approval_state"] == "expired" and st["risk_detail"]["expire_reason"] == "withdrawn_by_requester"
    assert st["risk_detail"]["command"] == "x" and st["risk_detail"]["withdraw_reason"] == "필요 없음"   # 기록 보존
    assert "error" in gate.withdraw(tid, "또")                       # 대기 아님
    assert "error" in gate.withdraw(_req("y"), "  ")                 # 사유 필수
    t2 = _req("z")
    assert gate.approve(t2)["state"] == "approved"                   # (시험용 사용자 승인)
    assert "error" in gate.withdraw(t2, "취소")                       # 승인된 것은 건드리지 않음
    assert gate.status(t2)["approval_state"] == "approved"
    with sqlite3.connect(gate.get_db_path()) as c:
        c.execute("INSERT INTO tasks (task_id, task_file, status, created_at, approval_state) "
                  "VALUES ('worker-1', 'task.md', 'waiting_approval', 1, 'waiting')")
    assert "error" in gate.withdraw("worker-1", "취소")              # 게이트가 만든 요청만


def test_withdraw_never_grants_execution(env):
    tid = _req("rm -rf /c/pjt")
    gate.withdraw(tid, "취소")
    assert gate.consume_approval(tid) != "consumed"
    assert gate.find_request("scope", gate.status(tid)["risk_detail"]["scope"], ("approved", "waiting")) is None


def test_cli_withdraw_and_approve_still_disabled(env, monkeypatch, capsys):
    tid = _req("x")
    monkeypatch.setattr("sys.argv", ["approval-gate.py", "withdraw", tid, "필요", "없음"])
    with pytest.raises(SystemExit) as e:
        gate.main()
    assert e.value.code == 0 and gate.status(tid)["approval_state"] == "expired"
    monkeypatch.setattr("sys.argv", ["approval-gate.py", "approve", _req("y")])
    with pytest.raises(SystemExit) as e:
        gate.main()
    assert e.value.code == 3                                          # 자기 승인 경로는 그대로 비활성


def test_auto_withdraw_temp_only_delete_requests(env):
    temp, _ = env
    t = str(temp).replace("\\", "/")
    own = _req(f'rm -rf "{t}/claude/x/scratchpad/r257"')
    own_ps = _req(f'Remove-Item -Recurse "{t}/tgt-iso-a"')
    real = _req('rm -rf "C:/pjt/orchestration_v1/docs"')
    mixed = _req(f'rm -rf "{t}/a" "C:/IFRS_PJT/src"')
    subst = _req(f'S="{t}/a"; rm -rf $(echo /c/pjt)')
    home = _req(f'rm -rf "{t}/a" ~/x')
    up = _req(f'rm -rf "{t}/../pjt"')
    push = _req("git push origin main", "irreversible")
    r = oc.run(SID)
    assert set(r["approvals"]["withdrawn"]) == {own, own_ps}
    left = {x["task_id"] for x in r["approvals"]["remaining"]}
    assert {real, mixed, subst, home, up, push} <= left
    for tid in (real, mixed, subst, home, up, push):
        assert gate.status(tid)["approval_state"] == "waiting"        # 실제 위험 요청은 그대로 보호
    assert "승인 취소 2" in oc.LOG.read_text(encoding="utf-8")


def test_time_budget_defers_rest_to_next_run(env, monkeypatch):
    temp, _ = env
    olds = [_mk(temp / f"tgt-iso-b{i}") for i in range(3)]
    for p in olds:
        _old(p, 2 * 3600)
    monkeypatch.setattr(oc, "BUDGET_SEC", -1)            # 예산 소진 상태 = 아무것도 지우지 않고 다음으로 미룸
    r = oc.run(SID)
    assert r["deferred"] == 3 and all(p.exists() for p in olds)
    monkeypatch.setattr(oc, "BUDGET_SEC", 6.0)
    r = oc.run(SID)
    assert r["kept"] == [], r["kept"]
    for _ in range(5):   # 느린 러너(CI)에서는 예산 안에 다 못 지워 다음 실행에서 이어 지운다 (R391 · run 45511090552)
        if not any(p.exists() for p in olds):
            break
        _old_all = [p for p in olds if p.exists()]
        for p in _old_all:
            _old(p, 2 * 3600)
        r = oc.run(SID)
    assert not any(p.exists() for p in olds), (r["removed"], r["kept"], r["deferred"])


# R297·R298 쌓이는 것 규칙 정리 — 규칙 파일(base+glob) 로만 판정 · base 밖 불가 · 규칙 밖 큰 폴더는 기록만
def test_retention_rules_from_config_only(tmp_path):
    import json, shutil, subprocess
    proj, temp = tmp_path / "proj", tmp_path / "T"
    (proj / ".claude" / "scripts").mkdir(parents=True)
    (proj / ".claude" / "config").mkdir(parents=True)
    temp.mkdir()
    shutil.copy(KIT / ".claude/scripts/cleanup-pollution.sh", proj / ".claude/scripts/cleanup-pollution.sh")
    bk = proj / ".claude" / "backups"
    for i, ts in enumerate(("20261101-000000", "20261102-000000", "20261103-000000")):
        d = bk / ("kit-merge-" + ts)
        d.mkdir(parents=True)
        (d / "f.txt").write_text("x", encoding="utf-8")
        os.utime(d, (time.time() - 1000 + i, time.time() - 1000 + i))
    old = time.time() - 3 * 86400
    for n, body in (("tmpaaa.json", '{"session_id":"t","requests":[]}'), ("tmpbbb.json", '{"other":1}')):
        (temp / n).write_text(body, encoding="utf-8")
        os.utime(temp / n, (old, old))
    (temp / "tmpccc.json").write_text('{"requests":[]}', encoding="utf-8")   # 새것 — 1일 안 지남
    big = proj / "work" / "old_backup"
    big.mkdir(parents=True)
    (big / "blob.bin").write_bytes(b"0" * (2 * 2 ** 20))
    outside = tmp_path / "outside.json"
    outside.write_text('{"requests":[]}', encoding="utf-8")
    os.utime(outside, (old, old))
    (proj / ".claude/config/retention.json").write_text(json.dumps({
        "rules": [{"name": "전파 백업", "type": "keep_newest", "base": "PROJECT", "glob": ".claude/backups/kit-merge-*", "keep": 1},
                  {"name": "옛 임시", "type": "max_age_days", "base": "TEMP", "glob": "tmp*.json", "days": 1, "content_has": "\"requests\""},
                  {"name": "밖으로 탈출", "type": "max_age_days", "base": "TEMP", "glob": "../outside.json", "days": 1}],
        "discover": {"name_regex": "(?i)backup", "min_mb": 1, "max_depth": 3, "skip": []}}), encoding="utf-8")
    env = dict(os.environ, RETENTION_FORCE="1", TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
    r = subprocess.run([bash_exe(), str(proj / ".claude/scripts/cleanup-pollution.sh")], env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=120)
    assert r.returncode == 0, r.stderr
    assert sorted(p.name for p in bk.iterdir()) == ["kit-merge-20261103-000000"]          # 가장 최근 1개만
    assert not (temp / "tmpaaa.json").exists() and (temp / "tmpbbb.json").exists()          # 내용 조건
    assert (temp / "tmpccc.json").exists()                                                  # 1일 안 지남
    assert outside.exists()                                                                 # base 밖은 지우지 않음
    rep = json.loads((proj / ".claude/state/retention-report.json").read_text(encoding="utf-8"))
    assert [f["path"] for f in rep["large_unruled"]] == ["work/old_backup"] and big.exists()  # 기록만
    assert (proj / ".claude/state/retention.stamp").exists()


def test_merge_to_target_keeps_only_latest_backup(tmp_path):
    mt = _load("mt_r297", KIT / ".claude/scripts/merge-to-target.py")
    bk = tmp_path / ".claude" / "backups"
    for ts in ("20261101-000000", "20261102-000000", "20261103-000000"):
        (bk / ("kit-merge-" + ts)).mkdir(parents=True)
    (bk / "user-own-backup").mkdir()                       # 이 도구가 만든 이름이 아니면 건드리지 않음
    assert "2개 정리" in mt._prune_backups(tmp_path)
    assert sorted(p.name for p in bk.iterdir()) == ["kit-merge-20261103-000000", "user-own-backup"]
    assert mt._prune_backups(tmp_path) == ""


def test_prompt_inject_dedupe_per_session(tmp_path, monkeypatch):
    """R300 같은 세션 20분 안 같은 문단은 다시 넣지 않음 · 다른 세션·새 문단·끄기·TTL 지남은 그대로."""
    import json, types
    pd = _load("pd_r300", KIT / ".claude/hooks/prompt-dispatch.py")
    monkeypatch.setattr(pd, "ROOT", str(tmp_path))
    ctx = lambda sid: types.SimpleNamespace(raw=json.dumps({"session_id": sid}))
    a = "[대상 확정 REQUIRED]\n규칙 문단"
    b = "[ledger] + R1"
    assert pd._dedupe_session(a + "\n\n" + b, ctx("sess-aaaa1")) == a + "\n\n" + b
    assert pd._dedupe_session(a + "\n\n[ledger] + R2", ctx("sess-aaaa1")) == "[ledger] + R2"   # 반복 문단만 빠짐
    assert pd._dedupe_session(a, ctx("sess-bbbb2")) == a                                          # 다른 세션은 처음
    monkeypatch.setenv("PROMPT_INJECT_DEDUPE", "0")
    assert pd._dedupe_session(a, ctx("sess-aaaa1")) == a                                          # 끄기
    monkeypatch.delenv("PROMPT_INJECT_DEDUPE")
    monkeypatch.setattr(pd, "DEDUPE_TTL_SEC", -1)
    assert pd._dedupe_session(a, ctx("sess-aaaa1")) == a                                          # 시간 지나면 다시
    assert pd._dedupe_session(a, types.SimpleNamespace(raw="not json")) == a                       # 세션 모름 = 원문


def test_compact_resets_prompt_inject_dedupe_for_that_session_only(tmp_path):
    """R303 compact 는 세션 ID 가 그대로라 요약으로 사라진 안내가 20분간 다시 안 실렸다 → compact·clear 때 그 세션 기록만 지움."""
    import shutil, subprocess
    d = tmp_path / ".claude/state/prompt-inject.d"
    d.mkdir(parents=True)
    for n in ("abc-123", "other-9"):
        (d / f"{n}.json").write_text("{}", encoding="utf-8")
    bash = shutil.which("bash") or "bash"
    hook = str(KIT / "plugins/exec_orch/hooks/hook-00-init.sh")
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)}
    for stdin in ('{"session_id":"../../x","source":"clear"}', '{"session_id":"abc-123","source":"compact"}'):
        r = subprocess.run([bash, hook, str(tmp_path)], input=stdin, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env, timeout=60)
        assert r.returncode == 0 and "재발 방지 헌장" not in r.stdout
    assert sorted(p.name for p in d.iterdir()) == ["other-9.json"]


# ── R391 (2026-11-24) 끝난 세션 판정 = 대화 기록 시각 · 큰 폴더는 시간 예산 안에서 나눠 지움 ──
def _transcript(tmp_path, monkeypatch, sid, age):
    cfg = tmp_path / "cfg"
    f = cfg / "projects" / "some-proj" / f"{sid}.jsonl"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("{}\n", encoding="utf-8")
    t = time.time() - age
    os.utime(f, (t, t))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfg))
    return f


def test_r391_ended_session_judged_by_transcript_not_touched_files(env, tmp_path, monkeypatch):
    temp, _ = env
    ended = _mk(temp / "claude" / "projA" / OLD_SID / "scratchpad", ("clone/.git/objects/de/x", "a.txt"))
    _old(ended, 4 * 86400)
    (ended / "clone/.git/objects/de/x").write_text("y", encoding="utf-8")   # 바깥 도구가 2시간 전에 건드림 (종전: 영원히 «사용 중»)
    _old(ended / "clone/.git/objects/de/x", 2 * 3600)
    monkeypatch.setattr(oc, "_unpushed", lambda p, deadline=None: None)   # .git 흉내 폴더 (실제 저장소 아님) — git 판정은 아래 R375 시험
    _mk(temp / "claude" / "projA" / SID / "scratchpad")
    _transcript(tmp_path, monkeypatch, OLD_SID, 4 * 86400)                   # 세션 기록은 4일 전에 끝남
    oc.run(SID)
    assert not ended.exists()


def test_r391_active_transcript_keeps_scratchpad_even_if_files_old(env, tmp_path, monkeypatch):
    temp, _ = env
    live = _mk(temp / "claude" / "projA" / OLD_SID / "scratchpad")
    _old(live, 4 * 86400)
    _mk(temp / "claude" / "projA" / SID / "scratchpad")
    _transcript(tmp_path, monkeypatch, OLD_SID, 60)                          # 다른 창에서 그 세션이 1분 전에도 활동
    r = oc.run(SID)
    assert live.exists() and any("세션 활동 중" in k["why"] for k in r["kept"])


def test_r391_remove_respects_deadline_and_resumes(env):
    temp, _ = env
    big = _mk(temp / "r256-kit-big", tuple(f"d{i}/f{j}.txt" for i in range(20) for j in range(10)))
    n1 = oc._remove(big, deadline=time.monotonic() - 1)                       # 이미 지난 예산 = 하나도 안 지움
    assert n1 == 0 and big.exists()
    n2 = oc._remove(big, deadline=time.monotonic() + 30)
    assert n2 > 0 and not big.exists()


# ── R375 2차 검토 P0 (2026-11-25): 오래된 대화 기록만으로 지우지 않는다 — 사용 흔적·불확실하면 보존 · 지우기 직전 재확인 ──
import subprocess as _sp  # noqa: E402
import sys as _sys  # noqa: E402


def _ended(env, tmp_path, monkeypatch, files=("a.txt",), real_birth=False):
    temp, _ = env
    if real_birth:       # «폴더 생성 뒤 시작» 규칙을 직접 보는 시험만 실제 생성 시각 (기본 고정은 env fixture)
        monkeypatch.setattr(oc, "_birth", REAL_BIRTH)
    ended = _mk(temp / "claude" / "projA" / OLD_SID / "scratchpad", files)
    _old(ended, 4 * 86400)
    _mk(temp / "claude" / "projA" / SID / "scratchpad")
    _transcript(tmp_path, monkeypatch, OLD_SID, 4 * 86400)
    return ended


def _why(r):
    return " | ".join(k["why"] for k in r["kept"])


def test_r375_baseline_old_and_idle_is_removed(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    oc.run(SID)
    assert not ended.exists()


def test_r375_recent_file_change_kept(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    (ended / "a.txt").write_text("new", encoding="utf-8")       # 방금 바뀜
    r = oc.run(SID)
    assert ended.exists() and "최근 파일 변경" in _why(r)


def test_r375_live_worker_with_cwd_inside_kept(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    p = _sp.Popen([_sys.executable, "-c", "import time; time.sleep(30)"], cwd=str(ended))
    try:
        r = oc.run(SID)
        assert ended.exists() and "사용 중 프로세스" in _why(r)
    finally:
        p.kill(); p.wait()


def test_r375_process_arg_with_session_id_kept(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    p = _sp.Popen([_sys.executable, "-c", "import time,sys; time.sleep(30)", OLD_SID])
    try:
        r = oc.run(SID)
        assert ended.exists() and "인자" in _why(r)
    finally:
        p.kill(); p.wait()


def test_r375_psutil_missing_is_uncertain_kept(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    monkeypatch.setitem(_sys.modules, "psutil", None)            # import 실패
    r = oc.run(SID)
    assert ended.exists() and "확인 불가" in _why(r)


def test_r375_open_ledger_request_kept(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    _, proj = env
    (proj / ".claude/state/request-ledger.json").write_text(
        '{"requests":[{"id":"R9","session_id":"%s","status":"pending"}]}' % OLD_SID, encoding="utf-8")
    r = oc.run(SID)
    assert ended.exists() and "열린 요청" in _why(r)


def test_r375_broken_ledger_kept(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    _, proj = env
    (proj / ".claude/state/request-ledger.json").write_text("{broken", encoding="utf-8")
    r = oc.run(SID)
    assert ended.exists() and "원장 읽기 실패" in _why(r)


def _git(*a, cwd):
    _sp.run(["git", *a], cwd=cwd, check=True, capture_output=True)


def _repo_pair(ended):
    origin = ended.parent.parent.parent.parent / "origin.git"
    _sp.run(["git", "init", "-q", "--bare", str(origin)], check=True)
    work = ended / "clone"
    _sp.run(["git", "clone", "-q", str(origin), str(work)], check=True, capture_output=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t"), ("commit.gpgsign", "false")):
        _git("config", k, v, cwd=work)
    (work / "f.txt").write_text("1", encoding="utf-8")
    _git("add", ".", cwd=work)
    _git("commit", "-qm", "c1", cwd=work)
    _git("push", "-q", "origin", "HEAD", cwd=work)
    return work


def test_r375_unpushed_commit_and_dirty_tree_kept_pushed_clean_removed(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    work = _repo_pair(ended)
    (work / "f.txt").write_text("2", encoding="utf-8")
    _git("commit", "-qam", "c2", cwd=work)                      # 원격에 없는 커밋
    _old(ended, 4 * 86400)
    r = oc.run(SID)
    assert ended.exists() and "원격에 없는 커밋" in _why(r)
    _git("push", "-q", "origin", "HEAD", cwd=work)
    (work / "g.txt").write_text("x", encoding="utf-8")         # 커밋 안 한 파일
    _old(ended, 4 * 86400)
    r = oc.run(SID)
    assert ended.exists() and "커밋 안 한 변경" in _why(r)
    (work / "g.txt").unlink()
    _old(ended, 4 * 86400)
    r = oc.run(SID)
    assert any(x["path"] == str(ended) for x in r["removed"]), _why(r)   # 깨끗하고 다 올라간 복제본만 지움
    for _ in range(5):   # 느린 디스크(CI)에서는 시간 예산 안에 다 못 지워 다음 실행에서 이어서 지운다 (R391)
        if not ended.exists():
            break
        _old(ended, 4 * 86400)
        r = oc.run(SID)
    assert not ended.exists(), (_why(r), r["removed"], r["deferred"])                                    # 깨끗하고 다 올라간 복제본만 지움


def test_r375_git_failure_is_uncertain_kept(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch, ("clone/.git/HEAD", "clone/a.txt"))   # 깨진 저장소
    r = oc.run(SID)
    assert ended.exists() and "git 확인 실패" in _why(r)


def test_r375_recheck_right_before_delete(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    calls = []
    real = oc.busy_reason

    def flip(p, sid, now, deadline=None):                                       # 판정 땐 한가 → 지우기 직전 워커가 붙음 (경합)
        calls.append(1)
        return None if len(calls) == 1 else "사용 중 프로세스 (경합)"
    monkeypatch.setattr(oc, "busy_reason", flip)
    r = oc.run(SID)
    assert ended.exists() and "삭제 직전 재확인" in _why(r) and len(calls) == 2
    monkeypatch.setattr(oc, "busy_reason", real)


def test_r375_dry_run_does_not_recheck_or_delete(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    r = oc.run(SID, dry=True)
    assert ended.exists() and any(x["kind"] == "ended-scratchpad" for x in r["removed"])


def test_r375_git_check_does_not_rewrite_index(env, tmp_path, monkeypatch):
    """CI 실측 (run 45443022804): 미Push 확인의 git status 가 .git/index 를 새로 써 삭제 직전 재확인이 «최근 파일 변경» 으로
    오판 → 깨끗한 복제본이 영원히 남음. git --no-optional-locks 로 index 를 쓰지 않는다."""
    ended = _ended(env, tmp_path, monkeypatch)
    work = _repo_pair(ended)
    t = time.time() + 5
    os.utime(work / "f.txt", (t, t))                              # 내용 같고 시각만 바뀜 → 일반 status 는 index 를 갱신해 씀
    idx = work / ".git" / "index"
    before = os.stat(idx).st_mtime_ns
    assert oc._unpushed(ended) is None
    assert os.stat(idx).st_mtime_ns == before


# ── R375 3차 검토 P0 (2026-11-25): 탐색 완전성·실제 원격 증거·확인 불가 = 보존 ──
def _clean_pair(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    work = _repo_pair(ended)
    _old(ended, 4 * 86400)
    return ended, work


def test_r375c_ignored_user_file_kept_regenerable_cache_removed(env, tmp_path, monkeypatch):
    ended, work = _clean_pair(env, tmp_path, monkeypatch)
    (work / ".gitignore").write_text(".env\n__pycache__/\n", encoding="utf-8")
    _git("add", ".", cwd=work); _git("commit", "-qm", "ign", cwd=work); _git("push", "-q", "origin", "HEAD", cwd=work)
    (work / "__pycache__").mkdir(); (work / "__pycache__" / "x.pyc").write_bytes(b"0")
    assert "무시된 파일" in (oc._unpushed(ended) or "")                     # 4차 검토: 이름만 맞고 원본 소스 없음 = 보존
    (work / "x.py").write_text("", encoding="utf-8")
    _git("add", ".", cwd=work); _git("commit", "-qm", "src", cwd=work); _git("push", "-q", "origin", "HEAD", cwd=work)
    assert oc._unpushed(ended) is None                                   # 다시 만들 수 있다는 증거(옆 원본 소스)까지 = 지워도 됨
    (work / ".env").write_text("K=1", encoding="utf-8")
    assert "무시된 파일" in (oc._unpushed(ended) or "")                     # .env 같은 무시 파일 = 보존


def test_r375c_untracked_hidden_by_repo_config_still_kept(env, tmp_path, monkeypatch):
    ended, work = _clean_pair(env, tmp_path, monkeypatch)
    _git("config", "status.showUntrackedFiles", "no", cwd=work)          # 저장소 설정이 미추적 파일을 숨겨도
    (work / "new.txt").write_text("x", encoding="utf-8")
    assert "커밋 안 한 변경" in (oc._unpushed(ended) or "")


def test_r375c_detached_head_commit_kept(env, tmp_path, monkeypatch):
    ended, work = _clean_pair(env, tmp_path, monkeypatch)
    _git("checkout", "-q", "--detach", cwd=work)
    (work / "f.txt").write_text("d", encoding="utf-8")
    _git("commit", "-qam", "detached", cwd=work)                         # 어느 브랜치에도 없는 커밋
    assert "원격에 없는 커밋" in (oc._unpushed(ended) or "")


def test_r375c_stale_remote_tracking_ref_not_trusted(env, tmp_path, monkeypatch):
    ended, work = _clean_pair(env, tmp_path, monkeypatch)
    (work / "f.txt").write_text("2", encoding="utf-8")
    _git("commit", "-qam", "c2", cwd=work); _git("push", "-q", "origin", "HEAD", cwd=work)
    origin = ended.parent.parent.parent.parent / "origin.git"
    br = _sp.run(["git", "symbolic-ref", "--short", "HEAD"], cwd=work, capture_output=True, text=True).stdout.strip()
    _sp.run(["git", "--git-dir", str(origin), "update-ref", f"refs/heads/{br}", "HEAD~1"], check=True)   # 원격에서 c2 가 사라짐
    assert "원격에 없는 커밋" in (oc._unpushed(ended) or "")                 # 로컬 origin/<br> 은 아직 c2 (오래된 추적 ref)


def test_r375c_stash_kept(env, tmp_path, monkeypatch):
    ended, work = _clean_pair(env, tmp_path, monkeypatch)
    (work / "f.txt").write_text("s", encoding="utf-8")
    _git("stash", "-q", cwd=work)
    assert "stash" in (oc._unpushed(ended) or "")


def test_r375c_deep_and_nested_repos_found(env, tmp_path, monkeypatch):
    ended, work = _clean_pair(env, tmp_path, monkeypatch)
    deep = ended / "a" / "b" / "c" / "d" / "e" / "deep"
    deep.mkdir(parents=True)
    _sp.run(["git", "init", "-q", str(deep)], check=True)
    (deep / "x.txt").write_text("x", encoding="utf-8")
    assert "커밋 안 한 변경" in (oc._unpushed(ended) or "") and "deep" in oc._unpushed(ended)   # 깊이 6
    inner = work / "vendor" / "inner"
    inner.mkdir(parents=True)
    _sp.run(["git", "init", "-q", str(inner)], check=True)
    repos = [r for r, e in oc._git_repos(ended)]
    assert str(inner) in repos and str(work) in repos                   # 저장소 안의 중첩 저장소도


def test_r375c_unreadable_folder_or_scan_timeout_kept(env, tmp_path, monkeypatch):
    ended, work = _clean_pair(env, tmp_path, monkeypatch)
    real = os.scandir
    bad = str(ended / "clone")

    def flaky(d):
        if str(d) == bad:
            raise PermissionError(13, "denied")
        return real(d)
    monkeypatch.setattr(oc.os, "scandir", flaky)
    assert "폴더 읽기 실패" in (oc._unpushed(ended) or "")
    monkeypatch.setattr(oc.os, "scandir", real)
    monkeypatch.setattr(oc, "SCAN_SEC", -1)
    assert "탐색 미완료" in (oc._unpushed(ended) or "")


def test_r375c_unreachable_remote_kept(env, tmp_path, monkeypatch):
    ended, work = _clean_pair(env, tmp_path, monkeypatch)
    _git("remote", "set-url", "origin", str(tmp_path / "nowhere.git"), cwd=work)
    assert "원격 확인 실패" in (oc._unpushed(ended) or "")


def test_r375c_unreadable_same_user_process_started_after_folder_kept(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch, real_birth=True)
    import psutil
    me = psutil.Process().username()

    class P:
        def __init__(self, info):
            self.info = info

        def is_running(self):
            return True

    def fake_iter(attrs, ad_value=None):
        return [P({"pid": 1, "name": "old", "cmdline": ad_value, "cwd": ad_value, "username": me, "create_time": 1.0}),
                P({"pid": 2, "name": "other", "cmdline": ad_value, "cwd": ad_value, "username": ad_value,
                   "create_time": time.time() + 9})]
    monkeypatch.setattr(psutil, "process_iter", fake_iter)
    assert oc._users_of(ended, OLD_SID) is None          # 폴더보다 먼저 뜬 것 · 사용자 못 읽는 것 = 제외
    def fake_iter2(attrs, ad_value=None):
        return [P({"pid": 3, "name": "elev", "cmdline": ad_value, "cwd": ad_value, "username": me,
                   "create_time": time.time() + 9})]
    monkeypatch.setattr(psutil, "process_iter", fake_iter2)
    assert "확인 불가" in (oc._users_of(ended, OLD_SID) or "")   # 폴더 생긴 뒤 뜬 같은 사용자 프로세스를 못 읽음 = 보존


def test_r375c_partial_delete_resumes_even_with_broken_git(env, tmp_path, monkeypatch):
    ended, work = _clean_pair(env, tmp_path, monkeypatch)
    for i in range(30):
        (work / f"z{i}.txt").write_text("z", encoding="utf-8")
    _git("add", ".", cwd=work); _git("commit", "-qm", "z", cwd=work); _git("push", "-q", "origin", "HEAD", cwd=work)
    _old(ended, 4 * 86400)
    real_remove = oc._remove

    def half(p, deadline=None):                       # 예산 초과로 .git 만 반쯤 지운 상태 흉내
        objs = work / ".git" / "objects"
        n = real_remove(objs, deadline=None)
        return n
    monkeypatch.setattr(oc, "_remove", half)
    r = oc.run(SID)
    assert ended.exists() and r["removed"][0]["partial"]
    assert str(ended) in oc._load_prog()
    assert "git 확인 실패" in (oc._unpushed(ended) or "")   # 이제 일반 판정이면 영원히 보존될 상태
    monkeypatch.setattr(oc, "_remove", real_remove)
    r = oc.run(SID)                                       # 기록이 있어 이어서 지움 (프로세스 확인만)
    assert not ended.exists(), _why(r)
    assert str(ended) not in oc._load_prog()


def test_r375c_resume_still_respects_live_process(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    oc._save_prog({str(ended): 1})
    p = _sp.Popen([_sys.executable, "-c", "import time; time.sleep(30)"], cwd=str(ended))
    try:
        r = oc.run(SID)
        assert ended.exists() and "사용 중 프로세스" in _why(r)
    finally:
        p.kill(); p.wait()


# ── R375 4차 검토 P0·P1 (2026-11-25): 재개 안전성 · 진행 기록 원자성 · 동시 실행 · 오류 = 보존 · 예산 공유 ──
def _rec(p, t):
    return {"t": t, **oc._identity(p)}


def test_r375d_resume_record_for_recreated_path_is_ignored(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    oc._save_prog({str(ended): {"t": time.time() - 100, "ino": 1, "birth": 1.0}})   # 같은 경로 · 다른 폴더의 기록
    _sp.run(["git", "init", "-q", str(ended / "repo")], check=True)
    (ended / "repo" / "x.txt").write_text("x", encoding="utf-8")
    _old(ended, 4 * 86400)
    r = oc.run(SID)
    assert ended.exists() and "커밋 안 한 변경" in _why(r)               # 재개 대신 일반 판정 → 보존
    assert str(ended) not in oc._load_prog()


def test_r375d_resume_kept_when_new_file_after_start(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    oc._save_prog({str(ended): _rec(ended, time.time() - 100)})
    (ended / "new.txt").write_text("after", encoding="utf-8")            # 중단 뒤 새 파일
    r = oc.run(SID)
    assert ended.exists() and "삭제 시작 뒤 새·바뀐 파일" in _why(r)


def test_r375d_resume_kept_when_session_active_after_start(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    oc._save_prog({str(ended): _rec(ended, time.time() - 100)})
    _transcript(tmp_path, monkeypatch, OLD_SID, 10)                      # 중단 뒤 그 세션이 다시 움직임
    r = oc.run(SID)
    assert ended.exists() and "세션 활동" in _why(r)


def test_r375d_resume_kept_when_ledger_open(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    _, proj = env
    oc._save_prog({str(ended): _rec(ended, time.time() - 100)})
    (proj / ".claude/state/request-ledger.json").write_text(
        '{"requests":[{"id":"R9","session_id":"%s","status":"pending"}]}' % OLD_SID, encoding="utf-8")
    r = oc.run(SID)
    assert ended.exists() and "열린 요청" in _why(r)


def test_r375d_progress_save_failure_does_not_delete(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    monkeypatch.setattr(oc, "_save_prog", lambda d: False)
    r = oc.run(SID)
    assert ended.exists() and "재개 기록 저장 실패" in _why(r)


def test_r375d_progress_save_is_atomic(env):
    assert oc._save_prog({"a": 1}) and oc._load_prog() == {"a": 1}
    assert not list(oc.PROG.parent.glob("*.tmp"))                       # 임시 파일 안 남음 (교체 방식)


def test_r375d_concurrent_run_locked_out_dead_lock_taken_over(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch)
    p = _sp.Popen([_sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        oc._lock_path().write_text(str(p.pid), encoding="utf-8")         # 살아 있는 다른 정리 실행
        r = oc.run(SID)
        assert ended.exists() and "잠금" in _why(r)
    finally:
        p.kill(); p.wait()
    r = oc.run(SID)                                                      # 주인이 죽은 잠금 = 넘겨받음
    assert not ended.exists(), _why(r)
    assert not oc._lock_path().exists()


def test_r375d_remote_and_catfile_exit_codes_fail_closed(env, tmp_path, monkeypatch):
    ended, work = _clean_pair(env, tmp_path, monkeypatch)
    real = oc._git

    def bad(sub):
        def g(repo, *a, **k):
            r = real(repo, *a, **k)
            if a and a[0] == sub:
                r.returncode = 1
            return r
        return g
    monkeypatch.setattr(oc, "_git", bad("remote"))
    assert "remote 종료" in (oc._unpushed(ended) or "")
    monkeypatch.setattr(oc, "_git", bad("cat-file"))
    assert "cat-file 종료" in (oc._unpushed(ended) or "")


def test_r375d_unreadable_subfolder_in_mtime_scan_kept(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch, ("a.txt", "sub/b.txt"))
    real = os.scandir
    bad = str(ended / "sub")
    monkeypatch.setattr(oc.os, "scandir", lambda d: (_ for _ in ()).throw(PermissionError(13, "x")) if str(d) == bad else real(d))
    r = oc.run(SID)
    assert ended.exists() and "변경 확인 불완전" in _why(r)


def test_r375d_kit_temp_in_use_by_process_kept(env):
    temp, _ = env
    d = _mk(temp / "r256-kit-busy")
    _old(d, 2 * 3600)
    p = _sp.Popen([_sys.executable, "-c", "import time; time.sleep(30)"], cwd=str(d))
    try:
        r = oc.run(SID)
        assert d.exists() and "사용 중 프로세스" in _why(r)
    finally:
        p.kill(); p.wait()


def test_r375d_shared_deadline_stops_git_and_scan(env, tmp_path, monkeypatch):
    ended, work = _clean_pair(env, tmp_path, monkeypatch)
    assert "시간 예산 소진" in (oc._repo_reason(str(work), deadline=time.monotonic() + 0.05) or "")
    assert "시간 예산 소진" in (oc._unpushed(ended, deadline=time.monotonic() - 1) or "")
    assert "시간 예산 소진" in (oc.busy_reason(ended, OLD_SID, time.time(), deadline=time.monotonic() - 1) or "")


def test_r375d_same_network_remote_queried_once_per_run(env, tmp_path, monkeypatch):
    ended, work = _clean_pair(env, tmp_path, monkeypatch)
    origin = ended.parent.parent.parent.parent / "origin.git"
    url = origin.as_uri()                                                # file:// = 주소로 공유되는 원격
    work2 = ended / "clone2"
    _sp.run(["git", "clone", "-q", url, str(work2)], check=True, capture_output=True)
    _git("remote", "set-url", "origin", url, cwd=work)
    calls = []
    real = oc._git

    def count(repo, *a, **k):
        if a and a[0] == "ls-remote":
            calls.append(repo)
        return real(repo, *a, **k)
    monkeypatch.setattr(oc, "_git", count)
    oc._REMOTE_TIPS.clear()
    assert oc._unpushed(ended) is None and len(calls) == 1               # 복제본 2개 · 원격 조회 1회
    oc._REMOTE_TIPS.clear()


def test_r375d_node_modules_needs_package_json(env, tmp_path, monkeypatch):
    ended, work = _clean_pair(env, tmp_path, monkeypatch)
    (work / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    _git("add", ".", cwd=work); _git("commit", "-qm", "ign", cwd=work); _git("push", "-q", "origin", "HEAD", cwd=work)
    (work / "node_modules" / "m").mkdir(parents=True); (work / "node_modules" / "m" / "i.js").write_text("", encoding="utf-8")
    assert "무시된 파일" in (oc._unpushed(ended) or "")                     # 패키지 정의 없음 = 다시 못 만듦
    (work / "package.json").write_text("{}", encoding="utf-8")
    _git("add", ".", cwd=work); _git("commit", "-qm", "pkg", cwd=work); _git("push", "-q", "origin", "HEAD", cwd=work)
    assert oc._unpushed(ended) is None


def test_r375d_unreadable_process_that_already_exited_is_not_a_user(env, tmp_path, monkeypatch):
    ended = _ended(env, tmp_path, monkeypatch, real_birth=True)
    import psutil
    me = psutil.Process().username()

    class Gone:
        info = {"pid": 7, "name": "find.exe", "cmdline": None, "cwd": None, "username": me, "create_time": time.time() + 9}

        def is_running(self):
            return False
    monkeypatch.setattr(psutil, "process_iter", lambda attrs, ad_value=None: [
        type("G", (Gone,), {"info": {**Gone.info, "cmdline": ad_value, "cwd": ad_value}})()])
    assert oc._users_of(ended, OLD_SID) is None          # 그새 끝난 프로세스 = 폴더를 못 씀
