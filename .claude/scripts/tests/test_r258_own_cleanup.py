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

KIT = Path(__file__).resolve().parents[3]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


gate = _load("gate_r258", KIT / ".claude/scripts/approval-gate.py")
oc = _load("oc_r258", KIT / ".claude/scripts/own-cleanup.py")
SID = "11111111-2222-3333-4444-555555555555"
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
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.setenv("ORCHESTRATION_ROOT", str(proj))
    with sqlite3.connect(proj / ".claude/state/orca.db") as c:
        c.execute("CREATE TABLE tasks (task_id TEXT PRIMARY KEY, task_file TEXT NOT NULL, status TEXT NOT NULL, "
                  "created_at INTEGER NOT NULL, completed_at INTEGER, approval_state TEXT DEFAULT 'not_required', "
                  "risk_category TEXT, risk_detail TEXT, approved_at INTEGER, approved_by TEXT)")
    monkeypatch.setattr(oc, "_gate", lambda: gate)
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
    assert not box.exists() and (keep / "a.txt").exists() and (keep / "sub" / "b.txt").exists()


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
    assert r["deferred"] == 0 and not any(p.exists() for p in olds)


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
    r = subprocess.run(["bash", str(proj / ".claude/scripts/cleanup-pollution.sh")], env=env, capture_output=True,
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
