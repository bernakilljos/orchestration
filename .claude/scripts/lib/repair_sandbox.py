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
import tempfile
from pathlib import Path
from datetime import datetime

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
# 2026-10-30 Phase 10-R1: 테스트/운영 Sandbox Root 분리.
#   운영 = ROOT/.repair-sandbox (state: .claude/state/repair-sandboxes.json)
#   테스트 = REPAIR_SANDBOX_ROOT env (기본 TEMP 아래) · state 도 그 root 안 별도 파일
#   → 테스트의 cleanup/discard 는 운영 state·worktree 를 볼 수조차 없다.
OPERATIONAL_SANDBOX_ROOT = ROOT / ".repair-sandbox"
OPERATIONAL_STATE_FILE = ROOT / ".claude" / "state" / "repair-sandboxes.json"
TEST_SANDBOX_ROOT = Path(tempfile.gettempdir()) / "orca-repair-sandbox-test" / ROOT.name


def _resolve_roots():
    env_root = os.environ.get("REPAIR_SANDBOX_ROOT", "").strip()
    root = Path(env_root).resolve() if env_root else OPERATIONAL_SANDBOX_ROOT
    operational = root.resolve() == OPERATIONAL_SANDBOX_ROOT.resolve()
    state = OPERATIONAL_STATE_FILE if operational else root / "_sandbox-state.json"
    return root, state, operational


SANDBOX_ROOT, STATE_FILE, IS_OPERATIONAL_ROOT = _resolve_roots()


def use_test_root() -> Path:
    """테스트 전용 root 로 전환. env 도 설정하므로 supervisor 가 파일로 재로딩한 사본도 같은 root 를 쓴다."""
    global SANDBOX_ROOT, STATE_FILE, IS_OPERATIONAL_ROOT
    os.environ["REPAIR_SANDBOX_ROOT"] = str(TEST_SANDBOX_ROOT)
    SANDBOX_ROOT, STATE_FILE, IS_OPERATIONAL_ROOT = _resolve_roots()
    return SANDBOX_ROOT


def _inside_root(path: Path) -> bool:
    """현재 SANDBOX_ROOT 아래 경로인지 — 다른 root(운영↔테스트) 의 worktree 삭제 차단."""
    try:
        Path(path).resolve().relative_to(SANDBOX_ROOT.resolve())
        return True
    except Exception:
        return False


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


def create(goal_id: str, base_ref: str = "HEAD") -> dict:
    """격리 sandbox 생성: git worktree add .repair-sandbox/<goal_id> (base_ref 기준 · 기본 HEAD)."""
    SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
    sandbox_path = SANDBOX_ROOT / str(goal_id)
    branch = f"repair/{goal_id}"

    if sandbox_path.exists():
        return {"ok": False, "reason": f"sandbox 이미 존재: {sandbox_path}", "path": str(sandbox_path)}

    # 2026-10-30: sandbox 1개 = kit 전체 checkout (~2.5GB). 여유 공간 부족 시 생성 거부 (fail-closed).
    # 실측 사고: sandbox 누적으로 C: 여유 1.85GB → worktree add 가 "No space left on device" 로 중단.
    min_free_gb = float(os.environ.get("REPAIR_SANDBOX_MIN_FREE_GB", "10"))
    free_gb = shutil.disk_usage(str(SANDBOX_ROOT)).free / 1024 ** 3
    if free_gb < min_free_gb:
        return {"ok": False, "reason": f"디스크 여유 {free_gb:.1f}GB < {min_free_gb:.0f}GB · sandbox 생성 거부",
                "free_gb": round(free_gb, 2)}

    # git worktree add -b <branch> <path> HEAD · timeout 600s (큰 kit · Windows)
    # core.longpaths: 테스트 root(TEMP) 는 경로가 길어 kit 의 259자 파일이 MAX_PATH 초과 → 이 명령에만 적용
    r = _git("-c", "core.longpaths=true", "worktree", "add", "-b", branch, str(sandbox_path), base_ref, timeout=600)

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


def commit_changes(goal_id: str, message: str) -> dict:
    """sandbox 작업 트리 변경을 repair branch 에 commit (apply 전 단계).
    worktree 수정은 commit 전엔 branch 에 없으므로 merge 해도 반영되지 않는다."""
    entry = _load_state().get(str(goal_id))
    if not entry:
        return {"ok": False, "reason": f"sandbox 없음: goal {goal_id}"}
    cwd = Path(entry["path"])
    st = _git("status", "--porcelain", cwd=cwd, timeout=60)
    if not st.stdout.strip():
        return {"ok": True, "committed": False, "reason": "변경 없음"}
    _git("add", "-A", cwd=cwd, timeout=60)
    r = _git("commit", "-m", message, cwd=cwd, timeout=60)
    if r.returncode != 0:
        return {"ok": False, "reason": f"commit 실패: {r.stderr.strip()[:200]}"}
    sha = _git("rev-parse", "HEAD", cwd=cwd, timeout=30).stdout.strip()
    return {"ok": True, "committed": True, "commit": sha}


def _branch_checked_out(branch: str) -> bool:
    wl = _git("worktree", "list", "--porcelain", timeout=30)
    return f"branch refs/heads/{branch}" in wl.stdout


def apply_merge(goal_id: str, target_branch: str = "main") -> dict:
    """테스트 PASS 한 변경만 target_branch 에 fast-forward merge.

    target_branch="main" (기본) 은 기존 동작 그대로.
    그 외 target 은 checkout 없이 ff 여부 확인 후 update-ref 로만 이동 (작업 트리 무변경).
    """
    state = _load_state()
    entry = state.get(str(goal_id))
    if not entry:
        return {"ok": False, "reason": f"sandbox 없음: goal {goal_id}"}

    last_test = entry.get("last_test") or {}
    if last_test.get("exit_code") != 0:
        return {"ok": False, "reason": "테스트 미통과 — apply 불가 (먼저 test PASS 필요)"}

    branch = entry["branch"]
    if target_branch != "main":
        if _branch_checked_out(target_branch):
            return {"ok": False, "reason": f"{target_branch} 가 worktree 에 checkout 됨 · update-ref 불가"}
        new_sha = _git("rev-parse", branch).stdout.strip()
        old = _git("rev-parse", "--verify", "-q", f"refs/heads/{target_branch}")
        old_sha = old.stdout.strip() if old.returncode == 0 else ""
        if old_sha:
            anc = _git("merge-base", "--is-ancestor", old_sha, new_sha)
            if anc.returncode != 0:
                return {"ok": False, "reason": f"fast-forward 불가 ({target_branch} 가 {branch} 의 조상 아님) · 원본 보호"}
        r = _git("update-ref", f"refs/heads/{target_branch}", new_sha, old_sha)
        if r.returncode != 0:
            return {"ok": False, "reason": f"update-ref 실패: {r.stderr.strip()[:200]}"}
        entry["status"] = "applied"
        entry["applied_at"] = int(time.time())
        entry["applied_to"] = target_branch
        state[str(goal_id)] = entry
        _save_state(state)
        return {"ok": True, "branch": branch, "merged_to": target_branch,
                "from_sha": old_sha, "to_sha": new_sha}
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


def preserve(goal_id: str, keep: bool = True) -> dict:
    """보존 표시 — cleanup_orphans·discard 가 건드리지 않는다 (force 제외)."""
    state = _load_state()
    entry = state.get(str(goal_id))
    if not entry:
        return {"ok": False, "reason": f"sandbox 없음: goal {goal_id}"}
    entry["preserve"] = bool(keep)
    state[str(goal_id)] = entry
    _save_state(state)
    return {"ok": True, "goal_id": goal_id, "preserve": bool(keep)}


def discard(goal_id: str, force: bool = False) -> dict:
    """sandbox 폐기 — worktree remove + branch 삭제. 원본 보호."""
    state = _load_state()
    entry = state.get(str(goal_id))
    if not entry:
        return {"ok": False, "reason": f"sandbox 없음: goal {goal_id}"}
    if entry.get("preserve") and not force:
        return {"ok": False, "reason": f"preserve 표시된 sandbox · discard 거부: {goal_id}"}
    sandbox_path = Path(entry["path"])
    if not _inside_root(sandbox_path):
        return {"ok": False, "reason": f"현재 root({SANDBOX_ROOT}) 밖 경로 · discard 거부: {sandbox_path}"}
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
        # 2. active 상태로 max_age 초과 → discard (preserve·다른 root 경로는 제외)
        if entry.get("preserve") or not _inside_root(path):
            continue
        if entry.get("status") == "active":
            age = now - int(entry.get("created_at", now))
            if age > max_age_sec:
                dr = discard(gid)
                state[gid] = _load_state().get(gid, entry)   # discard() 가 저장한 최신 상태로 (덮어쓰기 방지)
                stale_discarded.append({
                    "goal_id": gid, "age_sec": age,
                    "discard_ok": dr.get("ok", False),
                })
        # 2b. applied 후 max_age 지난 sandbox → checkout 폴더만 제거 (branch·commit 은 유지)
        #     기존엔 applied 상태가 정리 대상이 아니어서 2.5GB checkout 이 영구 누적됐다.
        elif entry.get("status") == "applied":
            age = now - int(entry.get("applied_at") or entry.get("created_at", now))
            if age > max_age_sec:
                r = _git("worktree", "remove", "--force", str(path), timeout=120)
                if r.returncode == 0:
                    entry["status"] = "applied_checkout_removed"
                    entry["checkout_removed_at"] = now
                    stale_discarded.append({"goal_id": gid, "age_sec": age, "checkout_removed": True})

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
        r = discard(goal_id, force="--force" in argv)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif cmd == "preserve":
        r = preserve(goal_id, keep="--off" not in argv)
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
