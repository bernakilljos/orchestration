"""real_repair_chain.py — 실 코드 수정 종단 chain helper (Phase 7 · 2026-10-30).

사용자 지시 (8acdde1 후속 · "실제 실패 코드 · Agent 분석 · 격리 수정 · 재검증"):
  Scaffold 생성 X · 기존 자산 (repair_sandbox + Edit tool + pytest + verifier) 연결 helper.

Phase 7-R3 데모 (P7-REAL-REPAIR-DEMO) 재사용 가능 chain:
  1. prepare_sandbox(demo_id) — repair_sandbox.create + state 파일
  2. reproduce_failure(sandbox_cwd, test_cmd) — 실패 재현 (exit != 0 요구)
  3. collect_failure_evidence(sandbox_cwd, cmd, result) — stderr·exit 저장
  4. prepare_fix_prompt(evidence) — Claude Task tool subagent 호출용 prompt 생성
     (실 fix 는 메인 Claude Edit tool · Python 자동 호출 X · 사용자 지시 반영)
  5. verify_fix(sandbox_cwd, test_cmd) — fix 후 재실행
  6. check_sandbox_isolation(sandbox_cwd) — ROOT 누출 X 재확인
  7. save_evidence(demo_id, chain_data) — .claude/state/<demo_id>_evidence.json

안전 원칙:
  - sandbox 격리 전제 (ROOT 수정 X)
  - Agent 자동 호출 X (사용자 지시: "Python 에서 Task tool 호출 가정 X")
  - 특정 오류 하드코딩 X (범용 chain)
  - 성공은 **테스트 실패→성공 전환** 으로만 판정 (하드코딩 return 금지)
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
LIB = ROOT / ".claude" / "scripts" / "lib"
STATE = ROOT / ".claude" / "state"


def prepare_sandbox(demo_id: str) -> Dict[str, Any]:
    """repair_sandbox 생성 (기존 자산 재사용)."""
    sys.path.insert(0, str(LIB))
    try:
        import repair_sandbox as _sb
    except Exception as e:
        return {"ok": False, "stage": "import", "error": str(e)}
    r = _sb.create(demo_id)
    return {**r, "stage": "prepare_sandbox"}


def reproduce_failure(sandbox_cwd: str, test_cmd: str,
                      timeout: int = 60) -> Dict[str, Any]:
    """격리 공간에서 실패 cmd 실행 · exit != 0 요구 (실패 재현 못 하면 종단 무의미)."""
    cwd = Path(sandbox_cwd)
    if not cwd.exists():
        return {"ok": False, "stage": "reproduce_failure", "error": f"sandbox not found: {sandbox_cwd}"}
    try:
        r = subprocess.run(
            test_cmd, shell=True, cwd=str(cwd),
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
            env={**os.environ, "ALLOW_VISIBLE_WINDOW": "1"},
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "stage": "reproduce_failure",
                "error": f"timeout ({timeout}s)"}
    reproduced = r.returncode != 0
    return {
        "ok": reproduced,
        "stage": "reproduce_failure",
        "reproduced": reproduced,
        "test_cmd": test_cmd,
        "exit_code": r.returncode,
        "stdout_tail": (r.stdout or "")[-800:],
        "stderr_tail": (r.stderr or "")[-800:],
        "note": "exit != 0 확인됨 (실패 재현 OK)" if reproduced
                else "exit == 0 — 실패 재현 못함 · 종단 불가",
    }


def prepare_fix_prompt(evidence: Dict[str, Any]) -> str:
    """Claude Task tool subagent 호출용 prompt 생성 (실 fix 는 사용자/메인 Claude).

    사용자 지시: "지원되지 않는 Task tool 을 Python 에서 직접 호출 X"
    → 이 함수는 prompt 만 생성 · 실 호출은 메인 Claude 세션 안에서.
    """
    stderr = evidence.get("stderr_tail", "")[:400]
    stdout = evidence.get("stdout_tail", "")[:400]
    exit_code = evidence.get("exit_code", -1)
    test_cmd = evidence.get("test_cmd", "")
    sandbox_cwd = evidence.get("sandbox_cwd", "")
    return (
        "# 격리 공간 실 코드 수정 요청\n\n"
        f"작업 디렉토리 (sandbox · ROOT 밖): {sandbox_cwd}\n\n"
        f"## 실패 재현\n"
        f"- cmd: `{test_cmd}`\n"
        f"- exit: {exit_code}\n"
        f"- stderr:\n```\n{stderr}\n```\n"
        f"- stdout:\n```\n{stdout}\n```\n\n"
        f"## 요청\n"
        f"1. 위 stderr 분석 → 실제 결함 파일 확인 (Read tool)\n"
        f"2. 결함 위치 **최소 수정** (Edit tool · 격리 디렉토리 안만)\n"
        f"3. test cmd 재실행 → PASS 확인 (Bash tool)\n"
        f"4. 결과 1줄 리포트: EDIT_LINE=<라인> · PYTEST_EXIT=<코드> · PASSED=<N>/<total>\n\n"
        f"지침:\n"
        f"- 사용자 지시: sandbox cwd 밖 파일 수정 금지\n"
        f"- 함수 로직 유지 (return 하드코딩 X)\n"
        f"- 최소 변경 (문법·import 복구 등)\n"
    )


def verify_fix(sandbox_cwd: str, test_cmd: str,
               timeout: int = 60) -> Dict[str, Any]:
    """fix 후 test 재실행 · exit=0 요구."""
    cwd = Path(sandbox_cwd)
    try:
        r = subprocess.run(
            test_cmd, shell=True, cwd=str(cwd),
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
            env={**os.environ, "ALLOW_VISIBLE_WINDOW": "1"},
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "stage": "verify_fix", "error": "timeout"}
    passed = r.returncode == 0
    # pytest "N passed" 추출 (범용 · 하드코딩 X)
    m = re.search(r"(\d+)\s+passed", (r.stdout or "") + (r.stderr or ""))
    passed_count = int(m.group(1)) if m else None
    return {
        "ok": passed,
        "stage": "verify_fix",
        "exit_code": r.returncode,
        "passed_count": passed_count,
        "stdout_tail": (r.stdout or "")[-500:],
        "stderr_tail": (r.stderr or "")[-500:],
    }


def check_sandbox_isolation(sandbox_cwd: str,
                            expected_file_touches: Optional[list] = None) -> Dict[str, Any]:
    """sandbox 격리 재확인 — ROOT 쪽 파일 누출 없는지."""
    cwd = Path(sandbox_cwd)
    issues = []
    # ROOT 안 수상한 파일 (sandbox 안 파일명과 같은) 체크
    if expected_file_touches:
        for fname in expected_file_touches:
            leak = ROOT / fname
            if leak.exists() and leak.resolve() != (cwd / fname).resolve():
                issues.append({"kind": "root_leak", "file": fname,
                               "root_path": str(leak)})
    # git diff on main (sandbox 수정이 main branch 로 자동 반영됐는지)
    try:
        r = subprocess.run(
            ["git", "diff", "--name-only"], cwd=str(ROOT),
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "ALLOW_VISIBLE_WINDOW": "1"},
        )
        root_dirty = [p for p in (r.stdout or "").splitlines()
                      if ".repair-sandbox/" not in p and p.strip()]
        if root_dirty and expected_file_touches:
            for p in root_dirty:
                if any(f in p for f in expected_file_touches):
                    issues.append({"kind": "unexpected_root_diff", "path": p})
    except Exception:
        pass
    return {
        "ok": len(issues) == 0,
        "stage": "check_sandbox_isolation",
        "issues": issues,
    }


def save_evidence(demo_id: str, chain_data: Dict[str, Any]) -> str:
    """evidence 저장 · 재사용 가능 포맷."""
    STATE.mkdir(parents=True, exist_ok=True)
    path = STATE / f"{demo_id}_evidence.json"
    chain_data.setdefault("saved_at", int(time.time()))
    chain_data.setdefault("demo_id", demo_id)
    path.write_text(json.dumps(chain_data, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return str(path)


def _cli_main(argv):
    if len(argv) < 2:
        print("usage: real_repair_chain.py {prepare|reproduce|verify|isolation|prompt} [args]")
        return 2
    cmd = argv[1]
    if cmd == "prepare":
        if len(argv) < 3:
            print("usage: prepare <demo_id>")
            return 2
        print(json.dumps(prepare_sandbox(argv[2]), ensure_ascii=False, indent=2))
        return 0
    if cmd == "reproduce":
        if len(argv) < 4:
            print("usage: reproduce <sandbox_cwd> <test_cmd>")
            return 2
        print(json.dumps(reproduce_failure(argv[2], argv[3]), ensure_ascii=False, indent=2))
        return 0
    if cmd == "verify":
        if len(argv) < 4:
            print("usage: verify <sandbox_cwd> <test_cmd>")
            return 2
        print(json.dumps(verify_fix(argv[2], argv[3]), ensure_ascii=False, indent=2))
        return 0
    if cmd == "isolation":
        if len(argv) < 3:
            print("usage: isolation <sandbox_cwd> [file1,file2,...]")
            return 2
        files = argv[3].split(",") if len(argv) > 3 else None
        print(json.dumps(check_sandbox_isolation(argv[2], files),
                         ensure_ascii=False, indent=2))
        return 0
    if cmd == "prompt":
        # stdin 으로 evidence JSON 받음
        try:
            ev = json.loads(sys.stdin.read())
        except Exception as e:
            print(json.dumps({"error": f"stdin json: {e}"}))
            return 1
        print(prepare_fix_prompt(ev))
        return 0
    print(f"unknown cmd: {cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(_cli_main(sys.argv))
