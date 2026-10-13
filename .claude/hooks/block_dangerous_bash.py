#!/usr/bin/env python3
"""
PreToolUse hook: block obviously destructive Bash commands.
Reads JSON from stdin and (optionally) returns permissionDecision: deny.

This is conservative by design: it blocks only high-risk patterns.
OS-aware (Windows vs Unix) and skips text inside quotes/heredocs to avoid
false positives on natural-language commit messages.
"""
import json, sys, re, platform

# Cross-platform high-risk
UNIVERSAL = [
    r"\bdd\s+if=",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bpoweroff\b",
]

# Unix-like (also active on Windows Git Bash, which is the common case here)
UNIX_LIKE = [
    r"\brm\s+-rf\b",
    r"\brm\s+-fr\b",
    r"\brm\s+-r\s+-f\b",
    r"\bmkfs\.",
]

# Windows cmd / PowerShell
WINDOWS = [
    r"\bdel\s+/s\s+/q\b",
    r"\brmdir\s+/s\s+/q\b",
    r"\bformat\s+[a-zA-Z]:\b",
    r"\bRemove-Item\b.*\s-Recurse\b.*\s-Force\b",
]


def get_patterns():
    """Pick patterns based on host OS. On Windows we still include UNIX_LIKE
    because Git Bash / WSL are common shells on this project."""
    if platform.system() == "Windows":
        return UNIVERSAL + WINDOWS + UNIX_LIKE
    return UNIVERSAL + UNIX_LIKE


def strip_quoted_strings(cmd: str) -> str:
    """Replace contents of quotes and heredoc bodies with empty placeholders
    so DENY_PATTERNS only match real shell commands — not natural-language
    text inside `git commit -m "..."` or `cat <<EOF ... EOF`.

    NOTE: We intentionally do NOT strip $(...) or `...` since those execute.
    """
    # Heredoc bodies: <<EOF ... EOF  (also accepts 'EOF', "EOF", <<-EOF)
    cmd = re.sub(
        r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?[^\n]*\n.*?\n[ \t]*\1\b",
        r"<<\1>>",
        cmd,
        flags=re.DOTALL,
    )
    # "..." with escapes
    cmd = re.sub(r'"(?:[^"\\]|\\.)*"', '""', cmd)
    # '...' (no escapes in POSIX single quotes)
    cmd = re.sub(r"'[^']*'", "''", cmd)
    return cmd


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return None

    tool_input = payload.get("tool_input", {}) or {}
    cmd = tool_input.get("command") or ""
    if not isinstance(cmd, str) or not cmd.strip():
        return None

    scan_target = strip_quoted_strings(cmd)
    for pat in get_patterns():
        if re.search(pat, scan_target, re.IGNORECASE):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"[BLOCK] 위험 명령 차단: {cmd[:200]}",
                }
            }
    return None

if __name__ == "__main__":
    out = main()
    if out:
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
    sys.exit(0)
