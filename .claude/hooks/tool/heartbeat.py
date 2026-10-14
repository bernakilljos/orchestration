"""PostToolUse '.*' 인라인 훅 이식 - .claude/orca-heartbeat 에 현재 시각 기록.

원본: bash -c 'test -d "$CLAUDE_PROJECT_DIR/.claude" && date +%Y-%m-%dT%H:%M:%S > "$CLAUDE_PROJECT_DIR/.claude/orca-heartbeat"'
디렉터리가 없으면 test 가 실패해 exit 1 (비차단 · 출력 없음).
"""
from __future__ import annotations

import os
import time

from _common import Result


def run(ctx):
    cpd = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not cpd or not os.path.isdir(os.path.join(cpd, ".claude")):
        return Result(1, "", "")
    with open(os.path.join(cpd, ".claude", "orca-heartbeat"), "wb") as f:
        f.write((time.strftime("%Y-%m-%dT%H:%M:%S") + "\n").encode("ascii"))
    return None
