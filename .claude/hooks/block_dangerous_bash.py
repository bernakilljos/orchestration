#!/usr/bin/env python3
"""
PreToolUse hook: block obviously destructive Bash commands.
Reads JSON from stdin and (optionally) returns permissionDecision: deny.

This is conservative by design: it blocks only high-risk patterns.
"""
import json, sys, re

DENY_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\brm\s+-fr\b",
    r"\brm\s+-r\s+-f\b",
    r"\bdel\s+/s\s+/q\b",
    r"\brmdir\s+/s\s+/q\b",
    r"\bformat\s+[a-zA-Z]:\b",
    r"\bmkfs\.",
    r"\bdd\s+if=",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bpoweroff\b",
    r"\bRemove-Item\b.*\s-Recurse\b.*\s-Force\b",
]

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return None

    tool_input = payload.get("tool_input", {}) or {}
    cmd = tool_input.get("command") or ""
    if not isinstance(cmd, str) or not cmd.strip():
        return None

    for pat in DENY_PATTERNS:
        if re.search(pat, cmd, re.IGNORECASE):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"위험 명령 차단: {cmd}"
                }
            }
    return None

if __name__ == "__main__":
    out = main()
    if out:
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
    sys.exit(0)
