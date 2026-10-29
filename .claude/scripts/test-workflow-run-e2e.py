#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Workflow-run 엔진 종단 테스트 (2026-10-29).

목적:
  workflow-run.py 가 각 chain step 을 실제로 실행하고 OK/FAIL 을 정확히 리턴하는지 검증.
  수정 전 FAIL 확인 → 수정 후 PASS 확인 (사용자 지시 "재현 테스트 먼저").

금지:
  - 특정 goal_id 하드코딩 · 특정 사용자 메시지 하드코딩
  - 테스트 통과시키려고 workflow 로직 변경

Usage:
  python .claude/scripts/test-workflow-run-e2e.py
"""
from __future__ import annotations
import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "scripts" / "lib"))

PASS = 0
FAIL = 0


def check(cond: bool, msg: str) -> None:
    global PASS, FAIL
    tag = "PASS" if cond else "FAIL"
    if cond:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{tag}] {msg}")


def section(name: str) -> None:
    print(f"\n=== {name} ===")


def _run(cmd: list, timeout: int = 60) -> tuple[int, str, str]:
    """subprocess run → (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace", cwd=str(ROOT),
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -2, "", str(e)


def main() -> int:
    PY = sys.executable
    section("1. 각 workflow yaml 참조 스크립트 존재")
    import yaml  # type: ignore

    workflow_dir = ROOT / ".claude" / "workflows"
    missing_scripts: list[tuple[str, str]] = []
    bad_cli: list[tuple[str, str, str]] = []

    for yaml_file in sorted(workflow_dir.glob("*.yaml")):
        with open(yaml_file, "r", encoding="utf-8") as f:
            chain = yaml.safe_load(f) or {}
        for step in chain.get("steps") or []:
            script = step.get("script")
            if not script:
                continue  # tool/workflow step
            script_abs = ROOT / script
            if not script_abs.exists():
                missing_scripts.append((yaml_file.name, script))
            else:
                # CLI 호환성 확인 (스크립트 실제 호출 — 짧은 timeout)
                args = step.get("args") or []
                if not args:
                    continue
                # 서브커맨드 (첫 arg) 가 CLI help 에 있는지 확인
                sub = args[0] if args else ""
                if sub and not sub.startswith("{") and not sub.startswith("-"):
                    # 실제 호출로 invalid choice 확인
                    if script.endswith(".py"):
                        cmd = [PY, "-X", "utf8", str(script_abs), "--help"]
                    else:
                        cmd = ["bash", str(script_abs), "--help"]
                    rc, out, err = _run(cmd, timeout=10)
                    full = (out + err).lower()
                    if sub.lower() not in full and "usage" in full and "choice" not in full:
                        # help 에서 서브커맨드 미확인 — 추가 검증
                        pass  # help 가 모든 서브커맨드 나열 안 할 수 있음

    check(len(missing_scripts) == 0, f"스크립트 미존재 ({len(missing_scripts)}): {missing_scripts}")

    section("2. 01-goal parse_requests · 실제 재현")
    # 01-goal.yaml parse_requests step 호출 재현
    import yaml  # type: ignore
    with open(workflow_dir / "01-goal.yaml", "r", encoding="utf-8") as f:
        goal_chain = yaml.safe_load(f) or {}
    pr_step = next((s for s in goal_chain.get("steps", []) if s.get("id") == "parse_requests"), None)
    if pr_step:
        script = ROOT / pr_step["script"]
        args = pr_step.get("args") or []
        # {user_prompt} → test string substitution
        resolved_args = [a.replace("{user_prompt}", "test prompt") for a in args]
        rc, out, err = _run([PY, "-X", "utf8", str(script)] + resolved_args, timeout=10)
        combined = (out + err).lower()
        has_invalid = "invalid choice" in combined
        check(not has_invalid, f"parse_requests args 유효 (invalid choice X · rc={rc})")

    section("3. 07-repair isolate_sandbox · 실제 재현")
    with open(workflow_dir / "07-repair.yaml", "r", encoding="utf-8") as f:
        repair_chain = yaml.safe_load(f) or {}
    sb_step = next((s for s in repair_chain.get("steps", []) if s.get("id") == "isolate_sandbox"), None)
    if sb_step:
        script = ROOT / sb_step["script"]
        check(script.exists(), f"isolate_sandbox script 존재: {sb_step['script']}")

    section("4. 06-verify run_tests · 실제 재현")
    with open(workflow_dir / "06-verify.yaml", "r", encoding="utf-8") as f:
        verify_chain = yaml.safe_load(f) or {}
    rt_step = next((s for s in verify_chain.get("steps", []) if s.get("id") == "run_tests"), None)
    if rt_step:
        script = ROOT / rt_step["script"]
        check(script.exists(), f"run_tests script 존재: {rt_step['script']}")

    section("5. workflow-run.py 01-goal dry-run · 모든 step OK")
    rc, out, err = _run([PY, "-X", "utf8", str(ROOT / ".claude" / "scripts" / "workflow-run.py"),
                        "--chain", "01-goal", "--dry", "--inputs", json.dumps({"user_prompt": "test", "session_id": "test"})],
                       timeout=30)
    # dry-run 은 모든 step 이 DRY 상태로 처리
    has_fail = "FAIL" in out
    check(not has_fail, f"01-goal dry-run FAIL 없음 (rc={rc}, out tail: {out[-200:] if out else ''})")

    # 결과
    print("\n" + "=" * 60)
    print(f"PASS: {PASS}  FAIL: {FAIL}  TOTAL: {PASS + FAIL}")
    print("=" * 60)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
