"""Korean removal blocker - check if Edit removes korean chars."""
import sys
import json
import re
import io
import os

try:
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
    pass

if os.environ.get('ALLOW_KOREAN_REMOVAL') == '1':
    sys.exit(0)

try:
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)
    data = json.loads(raw)
except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
    sys.exit(0)

tool = data.get('tool_name', '')
if tool != 'Edit':
    sys.exit(0)

ti = data.get('tool_input', {}) or {}
old = ti.get('old_string', '') or ''
new = ti.get('new_string', '') or ''

KR = re.compile(r'[媛-??')
old_kr = len(KR.findall(old))
new_kr = len(KR.findall(new))

if old_kr > 0 and new_kr < old_kr:
    sys.stderr.write(f"[BLOCK] korean removal detected: old={old_kr} chars -> new={new_kr} chars\n")
    sys.stderr.write("        Edit refused: explicit user consent required to remove korean.\n")
    sys.stderr.write("        Bypass: set environment variable ALLOW_KOREAN_REMOVAL=1\n")
    sys.exit(1)

sys.exit(0)

