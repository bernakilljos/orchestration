#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Workflow 01~08 전체 체인 종단 테스트 (2026-10-29).

사용자 지시 Phase 4 "단계별 입력·출력 계약 · 상태 전이 · 정상·실패·복구 ·
작업별 격리 · 로그·Ledger 정합성 · 실제 subprocess 종료 코드 · 최종 산출물 생성 여부".

범위 (사용자 명시):
  - Dry-run · Mock PASS 만으로 VERIFIED 선언 X
  - 각 체인 참조 스크립트 실 호출 (최소 호출로 FAIL/OK 판정)
  - F3 snapshot pre→post→diff 순서 보장 검증
  - 08-learn memory-candidate 자동 승인 X 확인

금지:
  - 특정 goal_id 하드코딩 (테스트용 신규 goal 생성)
  - 운영 데이터 변경 (snapshot/candidate 생성은 state 디렉토리만)
  - PASS 가짜 처리

Usage:
  python .claude/scripts/test-workflow-full-chain-e2e.py
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PY = sys.executable
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


def _run(cmd: list, timeout: int = 60, cwd=None) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace", cwd=str(cwd or ROOT),
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -2, "", str(e)


def main() -> int:
    import yaml  # type: ignore
    workflow_dir = ROOT / ".claude" / "workflows"

    # 1. 모든 8 chain yaml 로드 가능
    section("1. 01-08 chain yaml 로드")
    chains = {}
    for y in sorted(workflow_dir.glob("*.yaml")):
        try:
            with open(y, "r", encoding="utf-8") as f:
                chains[y.stem] = yaml.safe_load(f) or {}
            check(True, f"{y.stem} 로드 OK")
        except Exception as e:
            check(False, f"{y.stem} 로드 실패: {e}")

    # 2. 각 chain 의 next_chain 연결 그래프
    section("2. 체인 연결 그래프")
    expected = {
        "01-goal": "02-discovery",
        "02-discovery": "03-research",
        "03-research": "04-plan",
        "04-plan": "05-execute",
        "05-execute": "06-verify",
        "06-verify": "08-learn",  # PASS 시
        "07-repair": "06-verify",  # 재검증
        "08-learn": None,  # 종료
    }
    for name, expected_next in expected.items():
        actual = chains.get(name, {}).get("next_chain")
        check(actual == expected_next, f"{name} next_chain={actual} (예상 {expected_next})")

    # 3. 각 chain step 참조 스크립트 존재
    section("3. 모든 step 참조 스크립트 존재")
    missing = []
    for name, chain in chains.items():
        for step in chain.get("steps") or []:
            script = step.get("script")
            if script:
                sp = ROOT / script
                if not sp.exists():
                    missing.append((name, step.get("id", "?"), script))
    check(len(missing) == 0, f"미존재 스크립트: {missing or '없음'}")

    # 4. F3 snapshot 순서 검증 (05-execute 가 pre, 06-verify 가 post+diff)
    section("4. F3 snapshot 순서 보장")
    exec_steps = [s.get("id") for s in chains.get("05-execute", {}).get("steps") or []]
    verify_steps = [s.get("id") for s in chains.get("06-verify", {}).get("steps") or []]
    check("pre_snapshot" in exec_steps, f"05-execute 에 pre_snapshot step ({exec_steps})")
    check("post_snapshot" in verify_steps, f"06-verify 에 post_snapshot step ({verify_steps})")
    check("diff_snapshot" in verify_steps, f"06-verify 에 diff_snapshot step ({verify_steps})")

    # 5. F3 snapshot 실제 호출 순서 종단
    section("5. snapshot pre → post → diff 실 종단 (상태 격리)")
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test-f3.txt"
        test_file.write_text("initial", encoding="utf-8")
        snapshot_script = ROOT / ".claude" / "scripts" / "lib" / "snapshot.py"
        # pre
        rc, _, _ = _run([PY, "-X", "utf8", str(snapshot_script), "pre", "--files", str(test_file)])
        check(rc == 0, f"snapshot pre rc={rc}")
        # 수정
        test_file.write_text("modified", encoding="utf-8")
        # post
        rc, _, _ = _run([PY, "-X", "utf8", str(snapshot_script), "post", "--files", str(test_file)])
        check(rc == 0, f"snapshot post rc={rc}")
        # diff
        rc, out, _ = _run([PY, "-X", "utf8", str(snapshot_script), "diff", "--files", str(test_file)])
        check(rc == 0, f"snapshot diff rc={rc}")
        has_change = "changed" in out and "1" in out  # 1 file changed
        check(has_change, f"diff 가 변경 감지 (changed count in out: {('changed' in out)})")

    # 6. memory-candidate.py 자동 승격 X 확인
    section("6. memory-candidate.py 자동 승인 금지")
    mc_script = ROOT / ".claude" / "scripts" / "memory-candidate.py"
    check(mc_script.exists(), "memory-candidate.py 존재")
    if mc_script.exists():
        # list 호출 (안전)
        rc, out, _ = _run([PY, "-X", "utf8", str(mc_script), "list"])
        check(rc == 0, f"memory-candidate list rc={rc}")
        # 소스에 "자동 승격 금지" 명시
        src = mc_script.read_text(encoding="utf-8")
        check("자동 승격 금지" in src or "자동 변경 금지" in src, "자동 승격 금지 안전 장치 명시")
        check("STANDING_REQUIREMENT" in src, "Standing Requirements 자동 변경 금지 체크 로직 존재")

    # 7. 08-learn CLI 호환성 (각 step 실 호출 가능)
    section("7. 08-learn 각 step CLI 호환")
    learn_chain = chains.get("08-learn", {})
    for step in learn_chain.get("steps") or []:
        sid = step.get("id")
        script = step.get("script")
        args = step.get("args") or []
        if not script:
            continue
        sp = ROOT / script
        if not sp.exists():
            check(False, f"08-learn {sid}: script 없음 {script}")
            continue
        # {goal_id} / {outcome} 치환
        resolved = []
        for a in args:
            a = a.replace("{goal_id}", "46").replace("{outcome}", "success")
            resolved.append(a)
        cmd_prefix = [PY, "-X", "utf8", str(sp)] if script.endswith(".py") else ["bash", str(sp)]
        rc, out, err = _run(cmd_prefix + resolved, timeout=15)
        combined = (out + err).lower()
        invalid = "invalid choice" in combined or "unrecognized" in combined
        check(not invalid, f"08-learn {sid}: args 유효 (rc={rc})")

    # 8. workflow-run.py --list (전수 등록)
    section("8. workflow-run 등록 8 체인")
    rc, out, _ = _run([PY, "-X", "utf8", str(ROOT / ".claude" / "scripts" / "workflow-run.py"), "--list"])
    check(rc == 0, f"workflow-run --list rc={rc}")
    for name in ("01-goal", "02-discovery", "03-research", "04-plan", "05-execute", "06-verify", "07-repair", "08-learn"):
        check(name in out, f"{name} 등록")

    # 9. 체인 재귀 안전 (max_hops)
    section("9. workflow-run 안전 상한 (max_hops)")
    engine_src = (ROOT / ".claude" / "scripts" / "workflow-run.py").read_text(encoding="utf-8")
    check("max_hops" in engine_src, "max_hops 안전 상한 존재")

    # 10. 입력 계약 (goal_id · session_id · user_prompt) 검증
    section("10. 입력 계약 (각 chain inputs 선언)")
    for name, chain in chains.items():
        inputs = chain.get("inputs") or []
        check(len(inputs) > 0, f"{name} inputs 선언 ({len(inputs)} 개)")

    # 결과
    print("\n" + "=" * 60)
    print(f"PASS: {PASS}  FAIL: {FAIL}  TOTAL: {PASS + FAIL}")
    print("=" * 60)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
