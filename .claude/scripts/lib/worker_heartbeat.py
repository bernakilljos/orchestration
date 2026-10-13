#!/usr/bin/env python3
"""Worker heartbeat reporter for .bat child workers.

Called from codex-auto.bat to update worker heartbeat in SQLite.

Usage:
    python worker_heartbeat.py <worker_id> <ai_type> [<pid>]

Example:
    python worker_heartbeat.py codex-1 codex 12345
"""

import sys
import os
from pathlib import Path

# Add parent dir to path for state_db import
sys.path.insert(0, str(Path(__file__).parent))

try:
    from state_db import register_worker, update_heartbeat
except ImportError:
    # Graceful fallback if state_db unavailable
    sys.exit(0)


def main():
    """Parse args and update heartbeat."""
    if len(sys.argv) < 3:
        sys.exit(1)

    worker_id = sys.argv[1]
    ai_type = sys.argv[2]
    pid = int(sys.argv[3]) if len(sys.argv) > 3 else os.getpid()

    try:
        # Register or update worker (idempotent)
        register_worker(worker_id, ai_type, pid)
        # Update heartbeat timestamp
        update_heartbeat(worker_id)
    except Exception:
        # Fail silently - workers should not crash if DB is unavailable
        pass


if __name__ == "__main__":
    main()
