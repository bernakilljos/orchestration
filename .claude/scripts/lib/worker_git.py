"""외부 워커(codex-auto) 결과 커밋·push 를 승인 정책에 맞춘다 (2026-11-06 P0).

종전 codex-auto.bat: 작업 뒤 `git add . && commit && push` — 승인 게이트 밖에서 원격 push · 작업 전부터 있던
미커밋 파일까지 섞여 올라갈 수 있었다. 여기서는
  1. snapshot: 워커 실행 직전 미커밋 경로와 내용 해시 기록
  2. commit:   실행 중 새로 바뀐 경로만 커밋 (원래 미커밋이던 경로는 사용자 작업이 섞일 수 있어 제외·보고)
               → push 는 하지 않고 approval-gate 에 `push-<task>` 승인 대기 등록
  3. push-approved: 승인된 건만, 등록한 커밋을 강제 없이 push (원격이 그사이 바뀌었으면 push 안 함)
usage: worker_git.py snapshot <root> <out.json> | commit <root> <task_id> <message> <before.json>
       | push-approved <root>
"""
import importlib.util
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPTS = Path(__file__).resolve().parents[1]
SENSITIVE = (".env", ".pem", ".key", ".p12", ".pfx", "id_rsa", "id_ed25519", "credentials")


def _git(root, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)


def _gate():
    spec = importlib.util.spec_from_file_location("approval_gate_wg", SCRIPTS / "approval-gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dirty(root) -> Dict[str, str]:
    """미커밋 경로 → 내용 해시 (삭제는 '<deleted>')."""
    out = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    items, parts, i = {}, out.split("\0"), 0
    while i < len(parts):
        entry = parts[i]
        i += 1
        if len(entry) < 4:
            continue
        code, path = entry[:2], entry[3:]
        if code[0] in "RC":           # rename/copy: 다음 칸이 원래 경로
            i += 1
        p = Path(root) / path
        items[path] = _git(root, "hash-object", "--", path).stdout.strip() if p.is_file() else "<deleted>"
    return items


def snapshot(root, out_file) -> Dict[str, Any]:
    snap = {"taken_at": int(time.time()), "dirty": dirty(root)}
    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    Path(out_file).write_text(json.dumps(snap, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "dirty": len(snap["dirty"])}


def _upstream(root) -> Optional[Dict[str, str]]:
    up = _git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if up.returncode != 0 or "/" not in up.stdout.strip():
        return None
    remote, branch = up.stdout.strip().split("/", 1)
    return {"remote": remote, "branch": branch}


def commit_owned(root, task_id: str, message: str, before: Dict[str, str]) -> Dict[str, Any]:
    """워커 실행 중 새로 바뀐 경로만 커밋하고 push 는 승인 대기로 등록한다."""
    after = dirty(root)
    owned = [p for p in after if p not in before]
    mixed = [p for p in after if p in before and after[p] != before[p]]
    sensitive = [p for p in owned if any(s in Path(p).name.lower() for s in SENSITIVE)]
    owned = [p for p in owned if p not in sensitive]
    res: Dict[str, Any] = {"task_id": task_id, "owned": owned, "skipped_preexisting_changed": mixed,
                           "skipped_sensitive": sensitive, "committed": False, "push": "not_requested"}
    if not owned:
        return {**res, "reason": "no new changes owned by this task"}
    add = _git(root, "add", "-A", "--", *owned)
    if add.returncode != 0:
        return {**res, "reason": f"git add failed: {add.stderr.strip()[-300:]}"}
    cm = _git(root, "commit", "-m", message, "--", *owned)      # 경로 지정 = 다른 staged 내용은 안 섞임
    if cm.returncode != 0:
        return {**res, "reason": f"git commit failed: {(cm.stderr or cm.stdout).strip()[-300:]}"}
    sha = _git(root, "rev-parse", "HEAD").stdout.strip()
    res.update(committed=True, commit=sha)
    up = _upstream(root)
    if not up:
        return {**res, "push": "no_upstream"}
    push_id = f"push-{task_id}"
    detail = json.dumps({"root": str(root), "commit": sha, **up}, ensure_ascii=False)
    _gate().request_approval(push_id, f"git push {up['remote']} {sha}:refs/heads/{up['branch']}", "irreversible",
                             detail)
    return {**res, "push": "waiting_approval", "push_task_id": push_id}


def _mark(push_id: str, state: str, note: str) -> None:
    gate = _gate()
    with sqlite3.connect(str(gate.get_db_path())) as c:
        row = c.execute("SELECT risk_detail FROM tasks WHERE task_id = ?", (push_id,)).fetchone()
        d = json.loads(row[0]) if row and row[0] else {}
        d["push_result"] = note
        c.execute("UPDATE tasks SET approval_state = ?, status = ?, risk_detail = ? WHERE task_id = ?",
                  (state, "completed" if state == "executed" else "failed", json.dumps(d, ensure_ascii=False),
                   push_id))


def push_approved(root) -> List[Dict[str, Any]]:
    """승인(approved)된 push-* 만 실행. 등록한 커밋이 HEAD 조상이고 원격 브랜치가 그 커밋의 조상일 때만 (강제 없음)."""
    gate = _gate()
    with sqlite3.connect(str(gate.get_db_path())) as c:
        rows = c.execute("SELECT task_id, risk_detail FROM tasks WHERE task_id LIKE 'push-%' "
                         "AND approval_state = 'approved'").fetchall()
    done = []
    for push_id, raw in rows:
        d = json.loads(raw or "{}").get("detail")
        d = json.loads(d) if isinstance(d, str) else (d or {})
        if Path(d.get("root") or "").resolve() != Path(root).resolve():
            continue
        sha, remote, branch = d.get("commit"), d.get("remote"), d.get("branch")
        if not (sha and remote and branch):
            _mark(push_id, "failed", "approval detail incomplete")
            done.append({"task_id": push_id, "pushed": False, "reason": "approval detail incomplete"})
            continue
        if _git(root, "merge-base", "--is-ancestor", sha, "HEAD").returncode != 0:
            _mark(push_id, "failed", "commit not in current HEAD")
            done.append({"task_id": push_id, "pushed": False, "reason": "commit not in current HEAD"})
            continue
        _git(root, "fetch", "-q", remote, branch)
        remote_ref = f"{remote}/{branch}"
        if _git(root, "rev-parse", "--verify", "-q", remote_ref).returncode == 0 and \
                _git(root, "merge-base", "--is-ancestor", remote_ref, sha).returncode != 0:
            _mark(push_id, "failed", "remote branch moved (not fast-forward)")
            done.append({"task_id": push_id, "pushed": False, "reason": "remote branch moved (not fast-forward)"})
            continue
        p = _git(root, "push", remote, f"{sha}:refs/heads/{branch}")
        ok = p.returncode == 0
        _mark(push_id, "executed" if ok else "failed", (p.stderr or p.stdout).strip()[-300:])
        done.append({"task_id": push_id, "pushed": ok, "commit": sha, "remote": remote, "branch": branch})
    return done


def sandbox(task_id: str) -> Dict[str, Any]:
    """Codex 를 운영 작업 폴더 대신 실행할 독립 worktree (기존 repair_sandbox.create · 디스크·메모리 게이트 그대로).
    실패하면 경로를 주지 않는다 → 호출자는 운영 폴더에서 실행하지 않고 작업을 멈춘다."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import repair_sandbox
    r = repair_sandbox.create(f"codex-{task_id}")
    return {"ok": bool(r.get("ok")), "path": r.get("path"), "branch": r.get("branch"),
            "reason": r.get("reason") or r.get("error")}


def _main(argv) -> int:
    if len(argv) >= 3 and argv[1] == "sandbox":      # stdout = 경로 한 줄 (배치 for /f 용) · 실패 시 stdout 비움
        r = sandbox(argv[2])
        if r["ok"] and r["path"]:
            print(r["path"])
            return 0
        print(json.dumps(r, ensure_ascii=False), file=sys.stderr)
        return 1
    if len(argv) >= 4 and argv[1] == "snapshot":
        print(json.dumps(snapshot(argv[2], argv[3]), ensure_ascii=False))
        return 0
    if len(argv) >= 6 and argv[1] == "commit":
        bf = Path(argv[5])
        before = json.loads(bf.read_text(encoding="utf-8")).get("dirty", {}) if bf.is_file() else None
        if before is None:      # 실행 전 기록이 없으면 무엇이 이 작업 소유인지 모름 → 커밋하지 않음
            print(json.dumps({"committed": False, "reason": f"no pre-run snapshot: {bf}"}, ensure_ascii=False))
            return 1
        r = commit_owned(argv[2], argv[3], argv[4], before)
        print(json.dumps(r, ensure_ascii=False))
        return 0 if r["committed"] or not r["owned"] else 1
    if len(argv) >= 3 and argv[1] == "push-approved":
        print(json.dumps(push_approved(argv[2]), ensure_ascii=False))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
