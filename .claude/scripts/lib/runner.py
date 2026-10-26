"""runner.py — 2026-10-26 외부 AI P1 (공통 실행 계층 · Unified Runner).

모든 워커·sandbox·테스트가 사용하는 통합 subprocess 실행 계층.

외부 AI 핵심 원칙 6:
  1. 기존 CAS·워커 상태머신 재사용 (중복 X)
  2. shell=False + 인수 배열 default · shell=True 명시 필요시만
  3. 모든 실행에 task_id·worker_id·timeout·정책 결과 연결
  4. 오류 발생 시 stdout·stderr·종료 코드 보존 (실패를 성공으로 X)
  5. 비용 한도·승인 정책 공통 적용 (approval-gate 재사용 가능)
  6. 종료 코드 0 ≠ VERIFIED — verified 는 별도 플래그 · 호출자 판정

사용:
  from runner import run
  r = run(["pytest", "-q"], task_id="task-x", worker_id="haiku-1", timeout=600, cwd="/path")
  if r["exit_code"] == 0:
      # 호출자가 verify
      pass

executions 테이블 (orca.db) 자동 적재.
"""
from __future__ import annotations
import os
import sys
import time
import json
import sqlite3
import subprocess
from pathlib import Path
from typing import Union, List, Dict, Any, Optional

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
DB = ROOT / ".claude" / "state" / "orca.db"
LOG = ROOT / ".claude" / "logs" / "runner.log"


def _ensure_schema() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sqlite3.connect(str(DB), timeout=10) as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS executions (
              exec_id INTEGER PRIMARY KEY AUTOINCREMENT,
              task_id TEXT,
              worker_id TEXT,
              cmd TEXT NOT NULL,
              shell INTEGER DEFAULT 0,
              cwd TEXT,
              timeout_s INTEGER,
              exit_code INTEGER,
              timed_out INTEGER DEFAULT 0,
              stdout_tail TEXT,
              stderr_tail TEXT,
              verified INTEGER DEFAULT 0,
              policy_result TEXT,
              duration_ms INTEGER,
              started_at INTEGER NOT NULL,
              ended_at INTEGER
            );
            CREATE INDEX IF NOT EXISTS idx_exec_task ON executions(task_id, started_at DESC);
            CREATE INDEX IF NOT EXISTS idx_exec_worker ON executions(worker_id, started_at DESC);
            """)
    except Exception:
        pass


def _log(msg: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def _record_start(task_id: str, worker_id: str, cmd_str: str, shell: bool, cwd: str, timeout: int, policy: str) -> int:
    _ensure_schema()
    now = int(time.time())
    try:
        with sqlite3.connect(str(DB), timeout=10) as c:
            cur = c.execute(
                "INSERT INTO executions (task_id, worker_id, cmd, shell, cwd, timeout_s, "
                "policy_result, started_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (task_id, worker_id, cmd_str[:2000], 1 if shell else 0, cwd[:500] if cwd else "",
                 timeout, policy, now)
            )
            return cur.lastrowid or 0
    except Exception:
        return 0


def _record_end(exec_id: int, exit_code: int, timed_out: bool,
                stdout_tail: str, stderr_tail: str, duration_ms: int) -> None:
    if not exec_id:
        return
    now = int(time.time())
    try:
        with sqlite3.connect(str(DB), timeout=10) as c:
            c.execute(
                "UPDATE executions SET exit_code=?, timed_out=?, stdout_tail=?, stderr_tail=?, "
                "duration_ms=?, ended_at=? WHERE exec_id=?",
                (exit_code, 1 if timed_out else 0, (stdout_tail or "")[-2000:],
                 (stderr_tail or "")[-2000:], duration_ms, now, exec_id)
            )
    except Exception:
        pass


def _policy_check(cmd_str: str) -> str:
    """정책 검사 — 외부 AI 원칙 3 (실행 전 정책 결과 기록).
    현재 scaffold: 위험 패턴만 WARN (block 은 상위 approval-gate 가 담당).
    확장 포인트: block_visible_windows 재사용·cost 예산·승인 상태 체크."""
    danger_patterns = [
        ("rm -rf /", "critical: 시스템 파괴"),
        ("DROP TABLE", "critical: DB 파괴"),
        ("git push --force", "high: force push"),
        ("curl.*|.*bash", "high: 원격 실행"),
    ]
    for pat, note in danger_patterns:
        if pat in cmd_str:
            return f"WARN:{note}"
    return "OK"


def mark_verified(exec_id: int, verified: bool = True) -> bool:
    """외부 AI 원칙 6: 종료 코드 0 ≠ VERIFIED. 호출자가 명시적으로 verified 설정.
    실행 성공 후 테스트·회귀·수동 검토 완료 시만 호출."""
    if not exec_id:
        return False
    try:
        with sqlite3.connect(str(DB), timeout=10) as c:
            c.execute("UPDATE executions SET verified=? WHERE exec_id=?",
                      (1 if verified else 0, exec_id))
        return True
    except Exception:
        return False


def run(cmd: Union[str, List[str]],
        task_id: str = "",
        worker_id: str = "",
        timeout: int = 120,
        shell: bool = False,
        cwd: Optional[Union[str, Path]] = None,
        env_override: Optional[Dict[str, str]] = None,
        capture: bool = True) -> Dict[str, Any]:
    """Unified Runner — 모든 워커의 공통 실행 경로.

    외부 AI 원칙 2: shell=False default · 인수 배열 선호.
    cmd 가 str 이면 shell 자동 True 로 승격 (외부 AI 원칙 2 — 명시 필요).

    Returns dict:
        exec_id, exit_code, timed_out, stdout, stderr, duration_ms, policy_result, verified(False default)
    """
    # cmd 정규화 + shell 결정
    if isinstance(cmd, str):
        cmd_str = cmd
        shell = True  # str cmd 는 shell 필요 (명시적)
    else:
        cmd_str = " ".join(str(x) for x in cmd)

    # 정책 검사 (외부 AI 원칙 3)
    policy = _policy_check(cmd_str)

    # env 설정 (외부 AI 원칙 2 — 명시적)
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    # fail-closed default: ALLOW_VISIBLE_WINDOW 호출자가 명시적으로 설정해야 효과
    env.setdefault("ALLOW_VISIBLE_WINDOW", "0")

    cwd_str = str(cwd) if cwd else ""
    start = time.time()
    exec_id = _record_start(task_id, worker_id, cmd_str, shell, cwd_str, timeout, policy)
    _log(f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] START exec#{exec_id} task={task_id} worker={worker_id} policy={policy} cmd={cmd_str[:120]}")

    timed_out = False
    exit_code = -1
    stdout = ""
    stderr = ""

    try:
        r = subprocess.run(
            cmd,
            shell=shell,
            capture_output=capture,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=cwd_str or None,
            env=env,
        )
        exit_code = r.returncode
        stdout = r.stdout or ""
        stderr = r.stderr or ""
    except subprocess.TimeoutExpired as e:
        timed_out = True
        exit_code = -2
        stderr = f"TimeoutExpired after {timeout}s: {str(e)[:200]}"
        # 외부 AI 원칙 4: 타임아웃 시 자식 프로세스 정리 (subprocess.run 이 이미 처리하지만 확인)
    except Exception as e:  # noqa: BLE001
        exit_code = -3
        stderr = f"[runner] exception {type(e).__name__}: {str(e)[:200]}"

    duration_ms = int((time.time() - start) * 1000)
    _record_end(exec_id, exit_code, timed_out, stdout, stderr, duration_ms)
    _log(f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] END   exec#{exec_id} rc={exit_code} timed_out={timed_out} dur={duration_ms}ms")

    return {
        "exec_id": exec_id,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
        "duration_ms": duration_ms,
        "policy_result": policy,
        "verified": False,  # 외부 AI 원칙 6: 호출자가 mark_verified() 로 설정
    }


def list_recent(limit: int = 20, task_id: str = "", worker_id: str = "") -> List[Dict[str, Any]]:
    _ensure_schema()
    try:
        with sqlite3.connect(str(DB), timeout=10) as c:
            q = "SELECT exec_id, task_id, worker_id, cmd, exit_code, timed_out, verified, " \
                "duration_ms, policy_result, started_at FROM executions"
            where = []
            params = []
            if task_id:
                where.append("task_id=?")
                params.append(task_id)
            if worker_id:
                where.append("worker_id=?")
                params.append(worker_id)
            if where:
                q += " WHERE " + " AND ".join(where)
            q += " ORDER BY started_at DESC LIMIT ?"
            params.append(limit)
            rows = c.execute(q, params).fetchall()
            return [
                {
                    "exec_id": r[0], "task_id": r[1], "worker_id": r[2],
                    "cmd": r[3][:120], "exit_code": r[4], "timed_out": bool(r[5]),
                    "verified": bool(r[6]), "duration_ms": r[7], "policy": r[8],
                    "started_at": r[9],
                }
                for r in rows
            ]
    except Exception:
        return []


def main(argv):
    if len(argv) < 2:
        print("usage: runner.py {run|list|verify|ensure} [args]")
        return 2
    cmd = argv[1]
    if cmd == "ensure":
        _ensure_schema()
        print("[runner] schema ensured")
        return 0
    if cmd == "list":
        limit = 20
        for i, a in enumerate(argv):
            if a == "--limit" and i + 1 < len(argv):
                limit = int(argv[i + 1])
        print(json.dumps(list_recent(limit=limit), ensure_ascii=False, indent=2))
        return 0
    if cmd == "verify":
        if len(argv) < 3:
            print("usage: runner.py verify <exec_id> [true|false]")
            return 2
        exec_id = int(argv[2])
        v = True if len(argv) < 4 else (argv[3].lower() in ("true", "1", "yes"))
        print(json.dumps({"exec_id": exec_id, "verified": v, "ok": mark_verified(exec_id, v)}, ensure_ascii=False))
        return 0
    if cmd == "run":
        if len(argv) < 3:
            print("usage: runner.py run <command_str> [--task-id X] [--worker-id Y] [--timeout N]")
            return 2
        cmd_arg = argv[2]
        task_id = ""
        worker_id = ""
        timeout = 120
        for i, a in enumerate(argv):
            if a == "--task-id" and i + 1 < len(argv):
                task_id = argv[i + 1]
            elif a == "--worker-id" and i + 1 < len(argv):
                worker_id = argv[i + 1]
            elif a == "--timeout" and i + 1 < len(argv):
                timeout = int(argv[i + 1])
        r = run(cmd_arg, task_id=task_id, worker_id=worker_id, timeout=timeout)
        print(json.dumps({k: v for k, v in r.items() if k not in ("stdout", "stderr")}, ensure_ascii=False, indent=2))
        return r.get("exit_code", 1)
    print(f"unknown cmd: {cmd}")
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print(f"[runner] fatal: {e}", file=sys.stderr)
        sys.exit(1)
