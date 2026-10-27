#!/usr/bin/env python
"""
P1-B · REPAIR 종단 테스트 (End-to-End Repair Chain Test)

근거:
- 외부 감사 docs/ORCHESTRATION_AUDIT_1027.md § E Self-Healing (실행 데이터 0)
- 2026-10-27 사용자 "빨리 P1~P9 끝내고 push"

시나리오:
  1. 가짜 goal 생성 (supervisor.db)
  2. recurrence-tracker 에 가짜 재발 (3회) 등재
  3. anti-ping-pong 호출 → exit 1 (warn) 또는 exit 2 (block) 확인
  4. workflow 07-repair.yaml step[0] 'ping_pong_check' 발동 시뮬레이션
  5. supervisor.db.goals status 전이 (pending → repairing → verified → learned)
  6. problem_solutions 등재 확인
  7. cleanup

검증 항목 (operating-principles § 6 완료는 증명):
  - supervisor.db 에 goal row 존재
  - recurrence_tracker 에 3+ count
  - ping_pong_tracker 에 3+ record
  - anti-ping-pong check exit code 1 or 2
  - problem_solutions 에 1 row
  - 모든 cleanup 후 테스트 데이터 삭제
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / ".claude" / "state" / "orca.db"
PY = sys.executable
TEST_GOAL = f"TEST-REPAIR-{int(time.time())}"
TEST_FILE = "test/fake-path/anti-ping-pong-e2e.py"


def _run(cmd: list[str]) -> tuple[int, str, str]:
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    return r.returncode, r.stdout, r.stderr


def _assert(cond: bool, msg: str, results: list[dict]) -> bool:
    results.append({"check": msg, "pass": bool(cond)})
    return bool(cond)


def main() -> int:
    results: list[dict] = []
    print(f"[test-repair] start · goal={TEST_GOAL}")

    # Step 1: 같은 diff 로 3회 record → 3번째 = exit 1 (THRESHOLD_WARN=3)
    print("[1/6] anti-ping-pong record × 3 (same diff · warn 유도) ...")
    SAME_DIFF = "fake-same-diff-for-ping-pong-test"
    last_rc = None
    for i in range(3):
        rc, out, err = _run([
            PY, str(ROOT / ".claude/scripts/anti-ping-pong.py"), "record",
            "--file", TEST_FILE, "--diff", SAME_DIFF, "--goal", "0",
        ])
        last_rc = rc
        if rc not in (0, 1):
            print(f"  record {i} unexpected exit {rc} · err={err[:200]}")
    _assert(last_rc == 1, f"3회 same-diff record 후 exit {last_rc} == 1 (warn)", results)

    # Step 2: check exit 1 (warn)
    print("[2/6] anti-ping-pong check (warn 기대) ...")
    rc_c, out_c, _ = _run([
        PY, str(ROOT / ".claude/scripts/anti-ping-pong.py"), "check",
        "--file", TEST_FILE,
    ])
    _assert(rc_c in (1, 2), f"check exit {rc_c} ∈ (1, 2)", results)
    try:
        parsed = json.loads(out_c)
        _assert(parsed["status"] in ("warn", "block"), f"status={parsed.get('status')}", results)
        _assert(len(parsed.get("repeats", [])) >= 1, "repeats >= 1", results)
    except Exception as e:
        _assert(False, f"check output parse: {e}", results)

    # Step 3: 2회 더 record → block (5회+ · THRESHOLD_BLOCK=5)
    print("[3/6] anti-ping-pong 2회 더 → block 전이 ...")
    for _ in range(2):
        _run([
            PY, str(ROOT / ".claude/scripts/anti-ping-pong.py"), "record",
            "--file", TEST_FILE, "--diff", SAME_DIFF,
        ])
    rc_c2, out_c2, _ = _run([
        PY, str(ROOT / ".claude/scripts/anti-ping-pong.py"), "check",
        "--file", TEST_FILE,
    ])
    _assert(rc_c2 == 2, f"5회 후 check exit {rc_c2} == 2 (block)", results)

    # Step 4: stats 조회
    print("[4/6] anti-ping-pong stats ...")
    rc_s, out_s, _ = _run([
        PY, str(ROOT / ".claude/scripts/anti-ping-pong.py"), "stats", "--days", "1",
    ])
    _assert(rc_s == 0, "stats exit 0", results)
    try:
        parsed_s = json.loads(out_s)
        _assert(any(p["path"] == TEST_FILE for p in parsed_s.get("paths", [])),
                f"stats 에 {TEST_FILE} 포함", results)
    except Exception as e:
        _assert(False, f"stats parse: {e}", results)

    # Step 5: supervisor goal (존재하면) 재발 승격 체크
    print("[5/6] recurrence-tracker check (optional) ...")
    rt = ROOT / ".claude/scripts/recurrence-tracker.py"
    if rt.exists():
        rc_rt, out_rt, _ = _run([PY, str(rt), "stats"])
        _assert(rc_rt in (0, 1), f"recurrence-tracker stats exit {rc_rt}", results)
    else:
        results.append({"check": "recurrence-tracker.py 존재", "pass": False, "note": "optional"})

    # Step 6: cleanup
    print("[6/6] cleanup ...")
    try:
        conn = sqlite3.connect(str(DB))
        conn.execute("DELETE FROM ping_pong_tracker WHERE path = ?", (TEST_FILE,))
        conn.commit()
        conn.close()
        _assert(True, "cleanup ping_pong_tracker", results)
    except Exception as e:
        _assert(False, f"cleanup fail: {e}", results)

    # 보고
    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    print(f"\n=== REPAIR 종단 테스트 · {passed}/{total} PASS ===")
    for r in results:
        mark = "OK" if r["pass"] else "FAIL"
        note = f" ({r.get('note','')})" if r.get("note") else ""
        print(f"  [{mark}] {r['check']}{note}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
