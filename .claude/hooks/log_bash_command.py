#!/usr/bin/env python3
"""
PreToolUse hook: log Bash commands to .claude/logs/bash_commands.log (append).
"""
import json, os, sys
from datetime import datetime

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    tool_input = payload.get("tool_input", {}) or {}
    cmd = tool_input.get("command") or ""
    desc = tool_input.get("description") or ""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    log_dir = os.path.join(project_dir, ".claude", "logs")
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, "bash_commands.log")
    ts = datetime.now().isoformat(timespec="seconds")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{ts}\t{cmd}\t{desc}\n")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
