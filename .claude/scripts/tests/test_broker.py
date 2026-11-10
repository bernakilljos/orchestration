"""요청 함 + 독립 Broker 실행기 (§63 S5 · §64) — 임시 bare 저장소를 원격으로 · 운영 DB·계정·ACL 무관."""
import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
BROKER_PY = SCRIPTS / "lib" / "broker.py"
pytestmark = pytest.mark.skipif(not shutil.which("git"), reason="git 필요")


def _load():
    spec = importlib.util.spec_from_file_location("broker_t", BROKER_PY)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def git(cwd, *a):
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *a],
                       cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def remote_tip(remote):
    out = subprocess.run(["git", "ls-remote", str(remote), "refs/heads/main"], capture_output=True, text=True).stdout
    return (out.split() or [None])[0]


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("ORCHESTRATION_ROOT", str(tmp_path / "unused"))   # 시험 뒤 원래 값으로 복원
    monkeypatch.delenv("ORCA_BROKER_INBOX", raising=False)
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    agent = tmp_path / "agent"
    git(tmp_path, "clone", "-q", str(remote), str(agent))
    git(agent, "checkout", "-q", "-b", "main")
    (agent / "a.txt").write_text("1")
    git(agent, "add", "a.txt")
    git(agent, "commit", "-q", "-m", "c1")
    git(agent, "push", "-q", "origin", "main")
    inbox = tmp_path / "broker-io" / "inbox"
    inbox.mkdir(parents=True)
    broker = tmp_path / "broker"
    broker.mkdir()
    (broker / "broker-config.json").write_text(json.dumps(
        {"inbox": str(inbox), "repos": {"kit": {"remote_url": str(remote), "branches": ["main"]}}}), encoding="utf-8")
    b = _load()
    return {"b": b, "remote": remote, "agent": agent, "inbox": inbox, "broker": broker, "tmp": tmp_path}


def _commit(repo, name, body):
    (repo / name).write_text(body)
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", name)
    return git(repo, "rev-parse", "HEAD")


def _db(e):
    return sqlite3.connect(str(e["broker"] / ".claude" / "state" / "orca.db"))


def _ok(b, e, tid):
    """Broker 콘솔 승인 — describe 로 내용 확인 후 커밋 앞 8자리로 확인."""
    info = b.describe(e["broker"], tid)
    r = b.approve(e["broker"], tid, info["confirm_with"])
    assert r.get("state") == "approved", r
    return info


def test_submit_wait_approve_push_once(env):
    b, remote = env["b"], env["remote"]
    before = remote_tip(remote)
    sha = _commit(env["agent"], "b.txt", "2")
    s = b.submit_push(env["agent"], "kit", "main", env["inbox"])
    assert s["status"] == "SUBMITTED" and s["sha"] == sha
    log = b.process(env["broker"])
    tid = log[0]["task_id"]
    assert log[0]["result"] == "waiting" and remote_tip(remote) == before          # 승인 전 push 없음
    assert "error" in b.approve(env["broker"], tid, "")                            # 확인값 없이 승인 불가
    assert "error" in b.approve(env["broker"], tid, "00000000")
    info = _ok(b, env, tid)
    assert info["sha"] == sha and len(info["commits_to_push"]) == 1 and info["remote_url"] == str(remote)
    log2 = b.process(env["broker"])
    assert [x["result"] for x in log2] == ["pushed"] and remote_tip(remote) == sha
    assert b.status(env["broker"], tid)["approval_state"] == "executed"
    assert b.process(env["broker"]) == [] and remote_tip(remote) == sha              # 재처리 = 다시 실행 안 함


def test_forged_request_fields_rejected(env):
    b, inbox = env["b"], env["inbox"]
    before = remote_tip(env["remote"])
    other = _commit(env["agent"], "x.txt", "x")
    s = b.submit_push(env["agent"], "kit", "main", inbox)
    rid = s["request_id"]
    req = json.loads((inbox / f"{rid}.json").read_text(encoding="utf-8"))
    cases = {
        "remote": {**req, "remote_url": "https://evil.example/x.git"},     # 원격 주소 지정
        "approved": {**req, "approved": True},                            # 승인 표시
        "repo": {**req, "repo_id": "unknown"},                            # 등록 안 된 저장소
        "branch": {**req, "branch": "release"},                           # 허용 안 된 브랜치
        "type": {**req, "type": "result"},                                # 결과 위조
    }
    rids = []
    for i, (k, body) in enumerate(cases.items()):
        r2 = "req-%016x" % (0xA000 + i)
        shutil.copy(inbox / f"{rid}.bundle", inbox / f"{r2}.bundle")
        (inbox / f"{r2}.json").write_text(json.dumps(body), encoding="utf-8")
        rids.append(r2)
    (inbox / f"{rid}.json").unlink()
    (inbox / f"{rid}.bundle").unlink()
    (inbox / "not-a-request.json").write_text("{}", encoding="utf-8")
    log = b.process(env["broker"])
    assert sorted(x["request_id"] for x in log if x["result"] == "rejected") == sorted(rids + ["not-a-request"])
    assert not _db(env).execute("SELECT count(*) FROM tasks").fetchone()[0]        # 요청 행 0
    assert remote_tip(env["remote"]) == before and other


def test_bundle_commit_mismatch_rejected(env):
    b, inbox = env["b"], env["inbox"]
    a = _commit(env["agent"], "a2.txt", "a")
    s = b.submit_push(env["agent"], "kit", "main", inbox)
    req = json.loads((inbox / f"{s['request_id']}.json").read_text(encoding="utf-8"))
    req["sha"] = git(env["agent"], "rev-parse", "HEAD~1")                          # 묶음과 다른 커밋 주장
    (inbox / f"{s['request_id']}.json").write_text(json.dumps(req), encoding="utf-8")
    log = b.process(env["broker"])
    assert log[0]["result"] == "rejected" and "묶음" in log[0]["reason"] and a


def test_changed_commit_after_approval_not_pushed(env):
    b, remote = env["b"], env["remote"]
    a = _commit(env["agent"], "c.txt", "A")
    b.submit_push(env["agent"], "kit", "main", env["inbox"])
    tid_a = b.process(env["broker"])[0]["task_id"]
    _ok(b, env, tid_a)
    # 승인 뒤 Agent 가 커밋을 바꾸고 다시 요청 → 새 요청(대기) · 승인된 A 만 실행
    git(env["agent"], "commit", "-q", "--amend", "-m", "changed")
    bsha = git(env["agent"], "rev-parse", "HEAD")
    b.submit_push(env["agent"], "kit", "main", env["inbox"])
    log = b.process(env["broker"])
    waits = [x for x in log if x["result"] == "waiting"]
    assert len(waits) == 1 and waits[0]["task_id"] != tid_a
    assert remote_tip(remote) == a != bsha
    assert b.status(env["broker"], waits[0]["task_id"])["approval_state"] == "waiting"


def test_tampered_mirror_or_config_expires_approval(env):
    b = env["b"]
    before = remote_tip(env["remote"])
    _commit(env["agent"], "d.txt", "D")
    b.submit_push(env["agent"], "kit", "main", env["inbox"])
    tid = b.process(env["broker"])[0]["task_id"]
    _ok(b, env, tid)
    cfg = json.loads((env["broker"] / "broker-config.json").read_text(encoding="utf-8"))
    cfg["repos"]["kit"]["remote_url"] = str(env["tmp"] / "other.git")             # 승인 뒤 원격 변경
    (env["broker"] / "broker-config.json").write_text(json.dumps(cfg), encoding="utf-8")
    log = b.process(env["broker"])
    assert log[0]["result"] == "not_executed" and remote_tip(env["remote"]) == before
    assert b.status(env["broker"], tid)["approval_state"] == "expired"


def test_agent_session_approval_and_forged_result_ignored(env):
    b, remote = env["b"], env["remote"]
    before = remote_tip(remote)
    _commit(env["agent"], "e.txt", "E")
    s = b.submit_push(env["agent"], "kit", "main", env["inbox"])
    tid = b.process(env["broker"])[0]["task_id"]
    # Agent 세션의 /approve 표시(user-prompt)로 승인된 것처럼 바꿔 놓아도 Broker 는 쓰지 않는다
    with _db(env) as c:
        c.execute("UPDATE tasks SET approval_state='approved', approved_by='user-prompt', approved_at=? "
                  "WHERE task_id=?", (int(time.time()), tid))
    # Agent 가 결과 파일을 위조
    out = env["inbox"].parent / "outbox"
    (out / f"{s['request_id']}.json").write_text(json.dumps({"state": "executed", "pushed": True}), encoding="utf-8")
    log = b.process(env["broker"])
    assert log[0]["result"] == "not_executed" and remote_tip(remote) == before
    assert b.status(env["broker"], tid)["approval_state"] == "approved"           # 소비 안 됨 (Broker 승인 아님)


def test_agent_repo_hooks_and_config_never_run_by_broker(env):
    b, agent = env["b"], env["agent"]
    marker = env["tmp"] / "PWNED"
    hook = agent / ".git" / "hooks"
    for name in ("pre-push", "post-checkout", "reference-transaction", "pre-auto-gc"):
        (hook / name).write_text("#!/bin/sh\necho %s >> '%s'\n" % (name, marker.as_posix()))
    git(agent, "config", "core.fsmonitor", "echo fsmonitor >> '%s'" % marker.as_posix())
    git(agent, "config", "core.sshCommand", "echo ssh >> '%s'" % marker.as_posix())
    sha = _commit(agent, "f.txt", "F")
    b.submit_push(agent, "kit", "main", env["inbox"])
    if marker.exists():
        marker.unlink()                                  # Agent 자신의 명령에서 생긴 것은 제외 — Broker 단계만 본다
    tid = b.process(env["broker"])[0]["task_id"]
    _ok(b, env, tid)
    b.process(env["broker"])
    assert remote_tip(env["remote"]) == sha and not marker.exists()


def test_offline_or_unreachable_remote_fails_closed_once(env):
    b = env["b"]
    cfg_p = env["broker"] / "broker-config.json"
    cfg = json.loads(cfg_p.read_text(encoding="utf-8"))
    cfg["repos"]["kit"]["remote_url"] = str(env["tmp"] / "offline.git")           # 연결 불가 원격
    cfg_p.write_text(json.dumps(cfg), encoding="utf-8")
    _commit(env["agent"], "g.txt", "G")
    b.submit_push(env["agent"], "kit", "main", env["inbox"])
    tid = b.process(env["broker"])[0]["task_id"]
    _ok(b, env, tid)
    log = b.process(env["broker"])
    assert log[0]["result"] == "not_executed" and log[0]["reason"] == "remote_unreachable"
    assert b.status(env["broker"], tid)["approval_state"] == "approved"            # 연결 실패로 승인 낭비 안 함
    out = json.loads((env["inbox"].parent / "outbox").glob("*.json").__next__().read_text(encoding="utf-8"))
    assert out["code"] == "remote_unreachable" and str(env["tmp"]) not in json.dumps(out)   # outbox = 고정 코드만
    with _db(env) as c:                                                            # 승인 유효 시간(30분) 지남
        c.execute("UPDATE tasks SET approved_at = approved_at - 4000 WHERE task_id=?", (tid,))
    assert b.process(env["broker"])[0]["reason"] == "approval_ttl"
    assert b.status(env["broker"], tid)["approval_state"] == "expired"             # 중복 판정에 고착 안 됨
    b.submit_push(env["agent"], "kit", "main", env["inbox"])
    again = b.process(env["broker"])
    assert again[0]["result"] == "waiting" and again[0]["task_id"] != tid          # 같은 커밋 새 요청 가능


def test_not_fast_forward_refused(env):
    b, remote = env["b"], env["remote"]
    a = _commit(env["agent"], "h.txt", "H")
    b.submit_push(env["agent"], "kit", "main", env["inbox"])
    tid = b.process(env["broker"])[0]["task_id"]
    other = env["tmp"] / "other"
    git(env["tmp"], "clone", "-q", str(remote), str(other))
    c = _commit(other, "z.txt", "Z")
    git(other, "push", "-q", "origin", "main")                                     # 그사이 원격이 바뀜
    _ok(b, env, tid)
    log = b.process(env["broker"])
    assert log[0]["result"] == "failed" and remote_tip(remote) == c != a


def test_waiting_request_expires_after_24h(env):
    b = env["b"]
    _commit(env["agent"], "i.txt", "I")
    b.submit_push(env["agent"], "kit", "main", env["inbox"])
    tid = b.process(env["broker"])[0]["task_id"]
    with _db(env) as c:
        c.execute("UPDATE tasks SET created_at = created_at - 90000 WHERE task_id=?", (tid,))
    assert "error" in b.approve(env["broker"], tid)


def test_one_bad_request_does_not_stop_others(env):
    """검토 M1: 깊은 중첩 JSON·과대 파일이 처리를 멈추면 뒤의 요청·승인 실행이 막힌다."""
    b, inbox = env["b"], env["inbox"]
    (inbox / "req-00000000000000aa.json").write_text("[" * 3500, encoding="utf-8")    # 상한 안 · 재귀 한도 초과
    (inbox / "req-00000000000000ab.json").write_text("{" + " " * 10000 + "}", encoding="utf-8")
    (inbox / ".tmp-x.partial").write_text("{}", encoding="utf-8")          # 클라이언트 임시 파일은 무시
    sha = _commit(env["agent"], "j.txt", "J")
    b.submit_push(env["agent"], "kit", "main", inbox)
    log = b.process(env["broker"])
    codes = {x["request_id"]: x.get("code") for x in log if x["result"] == "rejected"}
    assert codes == {"req-00000000000000aa": "bad_json", "req-00000000000000ab": "too_large"}
    tid = next(x["task_id"] for x in log if x["result"] == "waiting")
    _ok(b, env, tid)
    assert b.process(env["broker"])[0]["result"] == "pushed" and remote_tip(env["remote"]) == sha
    assert (inbox / ".tmp-x.partial").exists()


def test_bundle_directory_or_reused_id_rejected(env):
    """검토 M2·S1: 묶음 자리의 디렉터리(로컬 저장소 전송 유도) · 처리한 요청 번호 재사용."""
    b, inbox = env["b"], env["inbox"]
    _commit(env["agent"], "k.txt", "K")
    s = b.submit_push(env["agent"], "kit", "main", inbox)
    rid = s["request_id"]
    req = (inbox / f"{rid}.json").read_text(encoding="utf-8")
    (inbox / f"{rid}.bundle").unlink()
    shutil.copytree(env["agent"] / ".git", inbox / f"{rid}.bundle")         # 디렉터리(저장소)를 묶음처럼
    log = b.process(env["broker"])
    assert log[0]["result"] == "rejected" and log[0]["code"] == "not_regular_file"
    s2 = b.submit_push(env["agent"], "kit", "main", inbox)                  # 정상 요청 처리 후 같은 번호로 다시
    b.process(env["broker"])
    (inbox / f"{s2['request_id']}.json").write_text(req.replace(rid, rid), encoding="utf-8")
    shutil.copy(env["broker"] / "processed" / f"{s2['request_id']}.json", inbox / f"{s2['request_id']}.json")
    b2 = env["tmp"] / "x.bundle"
    git(env["agent"], "bundle", "create", str(b2), "HEAD")
    shutil.copy(b2, inbox / f"{s2['request_id']}.bundle")
    log2 = b.process(env["broker"])
    assert log2[0]["result"] == "rejected" and log2[0]["code"] == "reused_id"


def test_branch_removed_after_approval_expires(env):
    """검토 S3: 승인 뒤 허용 목록에서 브랜치를 빼면 실행하지 않는다."""
    b = env["b"]
    before = remote_tip(env["remote"])
    _commit(env["agent"], "l.txt", "L")
    b.submit_push(env["agent"], "kit", "main", env["inbox"])
    tid = b.process(env["broker"])[0]["task_id"]
    _ok(b, env, tid)
    p = env["broker"] / "broker-config.json"
    cfg = json.loads(p.read_text(encoding="utf-8"))
    cfg["repos"]["kit"]["branches"] = ["release"]
    p.write_text(json.dumps(cfg), encoding="utf-8")
    assert b.process(env["broker"])[0]["reason"] == "not_allowed_now"
    assert b.status(env["broker"], tid)["approval_state"] == "expired" and remote_tip(env["remote"]) == before


def test_concurrent_process_locked(env):
    """검토 S4: 동시 실행 방지 — 잠금 중이면 아무것도 처리하지 않는다."""
    b = env["b"]
    _commit(env["agent"], "m.txt", "M")
    b.submit_push(env["agent"], "kit", "main", env["inbox"])
    (env["broker"] / "process.lock").write_text("1")
    assert b.process(env["broker"])[0]["result"] == "locked"
    assert len(list(env["inbox"].glob("*.json"))) == 1                      # 요청 그대로
    (env["broker"] / "process.lock").unlink()
    assert b.process(env["broker"])[0]["result"] == "waiting"


def test_propagation_copies_client_code_but_not_broker_state(tmp_path):
    """기존 merge-to-target 선택 규칙: 클라이언트 코드·가림 정본은 전파 · 요청 함 설정·상태·DB 는 전파 안 함."""
    spec = importlib.util.spec_from_file_location("mtt", SCRIPTS / "merge-to-target.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    kit = tmp_path / "kit"
    for rel in (".claude/scripts/lib/broker.py", ".claude/scripts/lib/redact.py", ".claude/broker-client.json",
                ".claude/state/orca.db", ".claude/state/stage1/x.json", ".claude/scripts/lib/__pycache__/broker.pyc"):
        (kit / rel).parent.mkdir(parents=True, exist_ok=True)
        (kit / rel).write_text("x")
    chosen = {p for t in m.TREES for p in m.walk(kit, t)}
    assert {".claude/scripts/lib/broker.py", ".claude/scripts/lib/redact.py"} <= chosen
    assert not chosen & {".claude/broker-client.json", ".claude/state/orca.db", ".claude/state/stage1/x.json",
                         ".claude/scripts/lib/__pycache__/broker.pyc"}


def test_copied_client_without_broker_or_git_blocks_only_risky_work(tmp_path):
    sol = tmp_path / "rpa-solution"
    (sol / "tools").mkdir(parents=True)
    shutil.copy(BROKER_PY, sol / "tools" / "broker.py")                         # 복사 설치: 클라이언트 파일만
    repo = sol / "work"
    repo.mkdir()
    git(repo, "init", "-q")
    (repo / "a").write_text("1")
    git(repo, "add", "a")
    git(repo, "commit", "-q", "-m", "1")
    base_env = {k: v for k, v in os.environ.items()                    # PYTHONIOENCODING 없이 = 한국어 Windows 기본 cp949 파이프
                if k not in ("ORCA_BROKER_INBOX", "ORCHESTRATION_ROOT", "PYTHONIOENCODING", "PYTHONUTF8")}
    r = subprocess.run([sys.executable, str(sol / "tools" / "broker.py"), "submit", str(repo), "rpa", "main"],
                       capture_output=True, text=True, encoding="utf-8", env=base_env, cwd=str(sol))
    assert r.returncode == 3 and json.loads(r.stdout)["status"] == "BLOCKED"       # Broker 없음 → 위험 작업 차단
    box = tmp_path / "inbox"
    box.mkdir()
    no_git = {**base_env, "PATH": str(tmp_path / "empty-path")}
    r2 = subprocess.run([sys.executable, str(sol / "tools" / "broker.py"), "submit", str(repo), "rpa", "main",
                         "--inbox", str(box)], capture_output=True, text=True, encoding="utf-8", env=no_git)
    assert r2.returncode == 3 and "git 없음" in json.loads(r2.stdout)["reason"]     # git 없음 → 차단 (오프라인 PC)
    (sol / ".claude").mkdir()
    (sol / ".claude" / "broker-client.json").write_text(json.dumps({"inbox": str(box)}), encoding="utf-8")
    r3 = subprocess.run([sys.executable, str(sol / "tools" / "broker.py"), "submit", str(repo), "rpa", "main"],
                        capture_output=True, text=True, encoding="utf-8", env=base_env, cwd=str(sol))
    assert r3.returncode == 0 and json.loads(r3.stdout)["status"] == "SUBMITTED"   # 설정만 있으면 요청 가능
    assert not (sol / "tools" / "approval-gate.py").exists()                       # 승인 DB·게이트 없이 동작
