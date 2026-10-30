"""repair_sandbox.py — 2026-10-26 외부 AI P1 (Verified Repair 격리 실행).

Git worktree 기반 격리 수정 환경. 수정 → 테스트 → 성공 시만 main 반영 · 실패 시 폐기.
외부 AI 완료 기준 #5 (수정 실패 시 원래 코드 안전 복구) 해결.

흐름:
  create <goal_id>  → .repair-sandbox/<goal_id>/ worktree 생성 (repair/<goal_id> branch)
  test   <goal_id>  → 격리 환경에서 pytest/vitest/custom test cmd 실행 → exit code 리턴
  apply  <goal_id>  → fast-forward merge to main (성공한 변경만)
  discard <goal_id> → worktree 폐기 + branch 삭제 (원본 보호)
  list              → 활성 sandbox 목록

Supervisor REPAIR workflow 와 연계:
  Supervisor goal #N (status=RUNNING) → sandbox create → repair agent 수정 → test → VERIFIED or REPAIRING → apply or discard

best-effort: git worktree 미지원·실패 시 fallback (현재 branch 그대로 작업).
"""
from __future__ import annotations
import os
import sys
import json
import time
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
SANDBOX_ROOT = ROOT / ".repair-sandbox"
STATE_FILE = ROOT / ".claude" / "state" / "repair-sandboxes.json"


def _git(*args: str, cwd: Path = None, check: bool = True, timeout: int = 300) -> subprocess.CompletedProcess:
    """git 명령 실행 (ALLOW_VISIBLE_WINDOW env 로 Pre-Execution hook 호환).
    2026-10-26 fix: Python 3.14 Windows subprocess reader thread bug — encoding/errors 명시.
    timeout 300s default (git worktree add 가 Windows + 큰 kit 디렉토리에서 느림)."""
    env = os.environ.copy()
    env["ALLOW_VISIBLE_WINDOW"] = "1"
    try:
        return subprocess.run(
            ["git"] + list(args),
            cwd=str(cwd or ROOT),
            env=env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except Exception as e:
        # subprocess 자체 fail — dummy CompletedProcess 리턴 (호출자 returncode 체크 가능)
        return subprocess.CompletedProcess(
            args=["git"] + list(args),
            returncode=1,
            stdout="",
            stderr=f"[_git subprocess failure] {type(e).__name__}: {e}",
        )


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def create(goal_id: str) -> dict:
    """격리 sandbox 생성: git worktree add .repair-sandbox/<goal_id>."""
    SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
    sandbox_path = SANDBOX_ROOT / str(goal_id)
    branch = f"repair/{goal_id}"

    if sandbox_path.exists():
        return {"ok": False, "reason": f"sandbox 이미 존재: {sandbox_path}", "path": str(sandbox_path)}

    # git worktree add -b <branch> <path> HEAD · timeout 600s (큰 kit · Windows)
    r = _git("worktree", "add", "-b", branch, str(sandbox_path), "HEAD", timeout=600)

    # 2026-10-26 fallback v2: 외부 AI 지적 수용 — .git 존재만 X · git 등록 상태까지 검증
    worktree_exists = False
    if sandbox_path.exists() and (sandbox_path / ".git").exists():
        # git worktree list --porcelain 로 공식 등록 확인
        wl = _git("worktree", "list", "--porcelain", timeout=30)
        if wl.returncode == 0 and str(sandbox_path).replace("\\", "/") in wl.stdout.replace("\\", "/"):
            # rev-parse 로 실제 작업 가능한 worktree 인지 확인
            rp = _git("rev-parse", "--is-inside-work-tree", cwd=sandbox_path, timeout=30)
            if rp.returncode == 0 and "true" in rp.stdout.strip():
                worktree_exists = True
    if r.returncode != 0 and not worktree_exists:
        return {"ok": False, "reason": f"worktree add 실패: {r.stderr.strip()[:200]}", "stderr": r.stderr}

    state = _load_state()
    state[str(goal_id)] = {
        "path": str(sandbox_path),
        "branch": branch,
        "created_at": int(time.time()),
        "status": "active",
        "subprocess_rc": r.returncode,  # 디버깅 참조
    }
    _save_state(state)
    note = "" if r.returncode == 0 else " (subprocess timeout · worktree 실제 생성 확인됨)"
    return {"ok": True, "path": str(sandbox_path), "branch": branch, "goal_id": goal_id, "note": note}


def test(goal_id: str, test_cmd: str = "") -> dict:
    """격리 환경에서 테스트 실행. test_cmd 없으면 project default 자동 감지."""
    state = _load_state()
    entry = state.get(str(goal_id))
    if not entry:
        return {"ok": False, "reason": f"sandbox 없음: goal {goal_id}"}
    sandbox_path = Path(entry["path"])
    if not sandbox_path.exists():
        return {"ok": False, "reason": f"sandbox path 없음: {sandbox_path}"}

    # test_cmd 자동 감지
    if not test_cmd:
        if (sandbox_path / "package.json").exists():
            test_cmd = "npm test --silent"
        elif (sandbox_path / "pyproject.toml").exists() or (sandbox_path / "pytest.ini").exists():
            test_cmd = "pytest -q"
        elif (sandbox_path / "Cargo.toml").exists():
            test_cmd = "cargo test --quiet"
        else:
            test_cmd = "echo 'no test runner detected · 안전상 PASS 처리 X'; exit 1"

    env = os.environ.copy()
    env["ALLOW_VISIBLE_WINDOW"] = "1"
    try:
        r = subprocess.run(
            test_cmd, shell=True, cwd=str(sandbox_path), env=env,
            capture_output=True, text=True, timeout=600  # 10분 상한
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "reason": "test timeout (>600s)", "test_cmd": test_cmd}

    entry["last_test"] = {
        "cmd": test_cmd,
        "exit_code": r.returncode,
        "ts": int(time.time()),
        "stdout_tail": r.stdout[-500:] if r.stdout else "",
        "stderr_tail": r.stderr[-500:] if r.stderr else "",
    }
    state[str(goal_id)] = entry
    _save_state(state)

    return {
        "ok": r.returncode == 0,
        "exit_code": r.returncode,
        "test_cmd": test_cmd,
        "stdout_tail": r.stdout[-500:] if r.stdout else "",
        "stderr_tail": r.stderr[-500:] if r.stderr else "",
    }


def apply_merge(goal_id: str) -> dict:
    """테스트 PASS 한 변경만 main 에 fast-forward merge."""
    state = _load_state()
    entry = state.get(str(goal_id))
    if not entry:
        return {"ok": False, "reason": f"sandbox 없음: goal {goal_id}"}

    last_test = entry.get("last_test") or {}
    if last_test.get("exit_code") != 0:
        return {"ok": False, "reason": "테스트 미통과 — apply 불가 (먼저 test PASS 필요)"}

    branch = entry["branch"]
    # 현재 branch 저장
    cur = _git("branch", "--show-current")
    original_branch = cur.stdout.strip()
    try:
        # main checkout + merge --ff-only
        _git("checkout", "main")
        r = _git("merge", "--ff-only", branch)
        if r.returncode != 0:
            # fallback: 일반 merge (충돌 발생 가능)
            r = _git("merge", "--no-ff", "-m", f"fix(repair): sandbox {goal_id} merge", branch)
            if r.returncode != 0:
                return {"ok": False, "reason": f"merge 실패: {r.stderr.strip()[:200]}"}
        entry["status"] = "applied"
        entry["applied_at"] = int(time.time())
        state[str(goal_id)] = entry
        _save_state(state)
        return {"ok": True, "branch": branch, "merged_to": "main"}
    finally:
        if original_branch and original_branch != "main":
            _git("checkout", original_branch, check=False)


def discard(goal_id: str) -> dict:
    """sandbox 폐기 — worktree remove + branch 삭제. 원본 보호."""
    state = _load_state()
    entry = state.get(str(goal_id))
    if not entry:
        return {"ok": False, "reason": f"sandbox 없음: goal {goal_id}"}
    sandbox_path = Path(entry["path"])
    branch = entry["branch"]

    # worktree 제거
    if sandbox_path.exists():
        r = _git("worktree", "remove", "--force", str(sandbox_path))
        if r.returncode != 0:
            # fallback: 수동 디렉토리 삭제
            try:
                shutil.rmtree(sandbox_path, ignore_errors=True)
            except Exception:
                pass
    # branch 삭제
    _git("branch", "-D", branch, check=False)

    entry["status"] = "discarded"
    entry["discarded_at"] = int(time.time())
    state[str(goal_id)] = entry
    _save_state(state)
    return {"ok": True, "goal_id": goal_id, "status": "discarded"}


def list_sandboxes() -> list:
    state = _load_state()
    result = []
    for gid, entry in state.items():
        result.append({
            "goal_id": gid,
            "status": entry.get("status"),
            "path": entry.get("path"),
            "branch": entry.get("branch"),
            "last_test_exit": (entry.get("last_test") or {}).get("exit_code"),
            "created_at": datetime.fromtimestamp(entry.get("created_at", 0)).isoformat(timespec='seconds'),
        })
    return result


def cleanup_orphans(max_age_sec: int = 86400) -> dict:
    """고아 sandbox 정리 (2026-10-29 Phase 2-B 완결).
    - state 에 등록됐지만 worktree 디렉토리 없음 → 상태만 삭제
    - state 에 없지만 .repair-sandbox/ 안 디렉토리 있음 → worktree remove 시도
    - active 상태로 N 시간+ 방치 → discard 호출 (안전 default)
    """
    state = _load_state()
    removed_entries = []
    removed_dirs = []
    stale_discarded = []
    now = int(time.time())

    # 1. state 안 등록돼 있지만 디렉토리 없음 → state 삭제
    for gid, entry in list(state.items()):
        path = Path(entry.get("path", ""))
        if path and not path.exists():
            del state[gid]
            removed_entries.append({"goal_id": gid, "reason": "path_missing"})
            continue
        # 2. active 상태로 max_age 초과 → discard
        if entry.get("status") == "active":
            age = now - int(entry.get("created_at", now))
            if age > max_age_sec:
                dr = discard(gid)
                stale_discarded.append({
                    "goal_id": gid, "age_sec": age,
                    "discard_ok": dr.get("ok", False),
                })

    _save_state(state)

    # 3. .repair-sandbox/ 안 디렉토리인데 state 에 없음 → worktree remove
    if SANDBOX_ROOT.exists():
        state_paths = {str(Path(e.get("path", "")).resolve()) for e in state.values()
                       if e.get("path")}
        for child in SANDBOX_ROOT.iterdir():
            if not child.is_dir():
                continue
            if str(child.resolve()) in state_paths:
                continue
            # 고아 디렉토리 → git worktree remove 시도 후 수동 삭제
            r = _git("worktree", "remove", "--force", str(child), timeout=30)
            if r.returncode != 0:
                try:
                    shutil.rmtree(child, ignore_errors=True)
                except Exception:
                    pass
            removed_dirs.append({"path": str(child), "worktree_remove_rc": r.returncode})

    # 4. git worktree prune (끊어진 참조 정리)
    _git("worktree", "prune", timeout=30, check=False)

    return {
        "ok": True,
        "removed_state_entries": removed_entries,
        "removed_orphan_dirs": removed_dirs,
        "stale_active_discarded": stale_discarded,
    }


def main(argv):
    if len(argv) < 2:
        print("usage: repair_sandbox.py {create|test|apply|discard|list} [goal_id] [test_cmd]")
        return 2
    cmd = argv[1]
    if cmd == "list":
        print(json.dumps(list_sandboxes(), ensure_ascii=False, indent=2))
        return 0
    if cmd == "cleanup-orphans":
        max_age = 86400
        for i, a in enumerate(argv):
            if a == "--max-age-sec" and i + 1 < len(argv):
                try:
                    max_age = int(argv[i + 1])
                except Exception:
                    pass
        r = cleanup_orphans(max_age_sec=max_age)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    if len(argv) < 3:
        print(f"usage: repair_sandbox.py {cmd} <goal_id> [...]")
        return 2
    goal_id = argv[2]
    if cmd == "create":
        print(json.dumps(create(goal_id), ensure_ascii=False, indent=2))
    elif cmd == "test":
        test_cmd = argv[3] if len(argv) > 3 else ""
        r = test(goal_id, test_cmd)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    elif cmd == "apply":
        r = apply_merge(goal_id)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    elif cmd == "discard":
        r = discard(goal_id)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"unknown cmd: {cmd}")
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print(f"[repair_sandbox] fatal: {e}", file=sys.stderr)
        sys.exit(1)
