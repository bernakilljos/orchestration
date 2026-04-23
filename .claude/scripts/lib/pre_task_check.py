#!/usr/bin/env python3
"""
pre_task_check.py — Pre-flight check before worker executes task.

Usage:
    python pre_task_check.py <ai_type> [task_file]

Exits:
    0: OK, proceed with task
    2: Budget breaker tripped (worker waits 10 min)
    3: Quota exceeded for this AI type (worker waits until backoff)
    1: Error in check (unexpected)

Writes to stderr for error details.
"""

import sys
import time
from pathlib import Path

# Add lib path
sys.path.insert(0, str(Path(__file__).parent))

from state_db import (
    is_breaker_tripped,
    is_quota_exceeded,
    check_daily_rollover,
)


def main():
    if len(sys.argv) < 2:
        print("Usage: pre_task_check.py <ai_type> [task_file]", file=sys.stderr)
        sys.exit(1)

    ai_type = sys.argv[1]
    # task_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        check_daily_rollover()

        # Check breaker first
        if is_breaker_tripped():
            print("BREAKER_TRIPPED", file=sys.stderr)
            sys.exit(2)

        # Check quota for this AI
        if is_quota_exceeded(ai_type):
            print(f"QUOTA_EXCEEDED:{ai_type}", file=sys.stderr)
            sys.exit(3)

        # OK
        sys.exit(0)

    except Exception as e:
        print(f"ERROR in pre_task_check: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
