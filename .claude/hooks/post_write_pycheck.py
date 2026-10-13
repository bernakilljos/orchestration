#!/usr/bin/env python3
"""
PostToolUse hook: quick Python sanity checks after Claude writes/edits files.

- If the touched file is a .py file, run a fast compile check on that file.
- Optionally, for core paths (engine/, storage/, web/, tools/), also run `tools/run_quick_tests.py` in background-friendly mode.

This hook reads JSON from stdin (Claude Code hook payload).
"""
import json
import os
import subprocess
import sys
from datetime import datetime

# Windows 콘솔 cp949 회피 — UTF-8 강제 (ASCII 출력 사용 + 이중 안전망)
try:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, Exception):
    pass

def _run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=False)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    tool_input = payload.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path") or ""
    if not isinstance(file_path, str):
        return 0

    # Only act on .py
    if not file_path.endswith(".py"):
        return 0

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    abs_path = file_path
    if not os.path.isabs(abs_path):
        abs_path = os.path.normpath(os.path.join(project_dir, file_path))

    # Compile check on just that file
    rc, out, err = _run([sys.executable, "-c", "import py_compile,sys; py_compile.compile(sys.argv[1], doraise=True); print('OK')", abs_path], cwd=project_dir)

    msg_lines = []
    if rc == 0:
        msg_lines.append(f"[OK] py_compile OK: {file_path}")
    else:
        msg_lines.append(f"[FAIL] py_compile FAIL: {file_path}")
        if err:
            msg_lines.append(err)

    # If core area changed, run quick tests (best-effort, short)
    core_prefixes = ("engine" + os.sep, "storage" + os.sep, "web" + os.sep, "tools" + os.sep, "app" + os.sep)
    rel_norm = os.path.normpath(file_path)
    if rel_norm.startswith(core_prefixes):
        qt = os.path.join(project_dir, "tools", "run_quick_tests.py")
        if os.path.exists(qt):
            rc2, out2, err2 = _run([sys.executable, qt], cwd=project_dir)
            if rc2 == 0:
                msg_lines.append("[OK] quick_tests OK")
            else:
                msg_lines.append("[FAIL] quick_tests FAIL")
                if out2:
                    msg_lines.append(out2[-1200:])
                if err2:
                    msg_lines.append(err2[-1200:])

    # Report back to Claude as a lightweight systemMessage (async-friendly)
    return {
        "systemMessage": "\n".join(msg_lines).strip()
    }

if __name__ == "__main__":
    try:
        result = main()
        if isinstance(result, dict):
            sys.stdout.write(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
    except Exception as e:
        sys.stdout.write(json.dumps({"systemMessage": f"Hook error: {e}"}, ensure_ascii=False))
        sys.exit(0)
