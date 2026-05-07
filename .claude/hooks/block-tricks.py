"""
Trick blocker - PreToolUse Edit hook.
Catches multiple known patterns where I (Claude) avoid user intent.

Blocked patterns:
  T1. Korean removal — old has more korean chars than new
  T2. Secret to placeholder — real PAT/key replaced by placeholder text
  T3. PAT to placeholder (specific GITHUB_PAT detection)
  T4. Mojibake bypass — code adds chr(0xFFFD) or escape sequences for U+FFFD
  T5. Auto-prompt regression — choice/timeout reverted to set /p / pause

Bypass: ALLOW_TRICKS=1 environment variable.
"""
import sys
import json
import re
import io
import os

try:
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
except Exception:
    pass

if os.environ.get('ALLOW_TRICKS') == '1':
    sys.exit(0)

try:
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)
    data = json.loads(raw)
except Exception:
    sys.exit(0)

tool = data.get('tool_name', '')
if tool != 'Edit':
    sys.exit(0)

ti = data.get('tool_input', {}) or {}
old = ti.get('old_string', '') or ''
new = ti.get('new_string', '') or ''

violations = []

# T1. Korean char removal
KR = re.compile(r'[' + chr(0xAC00) + '-' + chr(0xD7A3) + ']')
old_kr = len(KR.findall(old))
new_kr = len(KR.findall(new))
if old_kr > 0 and new_kr < old_kr:
    violations.append('T1 KOREAN_REMOVAL: ' + str(old_kr) + ' to ' + str(new_kr))

# T2. Secret to placeholder
SECRET_RE = re.compile(r'(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{30,})')
PLACEHOLDER_HINTS = ['YOUR_TOKEN_HERE', 'YOUR_API_KEY', 'REPLACE_WITH', 'YOUR_GOOGLE_API_KEY']
old_has_secret = bool(SECRET_RE.search(old))
new_has_secret = bool(SECRET_RE.search(new))
new_has_placeholder = any(h in new for h in PLACEHOLDER_HINTS)
if old_has_secret and not new_has_secret and new_has_placeholder:
    violations.append('T2 SECRET_TO_PLACEHOLDER: real secret -> placeholder')

# T3. GITHUB_PAT specific
old_pat_m = re.search(r'GITHUB_PAT=([^\s\r\n]+)', old)
new_pat_m = re.search(r'GITHUB_PAT=([^\s\r\n]+)', new)
if old_pat_m and new_pat_m:
    old_val = old_pat_m.group(1)
    new_val = new_pat_m.group(1)
    if 'YOUR_TOKEN' not in old_val and 'YOUR_TOKEN' in new_val:
        violations.append('T3 PAT_TO_PLACEHOLDER')

# T4. Mojibake bypass detection
# Don't put U+FFFD char directly in source - use byte sequence instead
ffffd_seq = chr(0xFFFD)
ffffd_escape = '\\' + 'u' + 'fffd'
if ffffd_seq in new and ffffd_seq not in old:
    violations.append('T4 MOJIBAKE_LITERAL_ADDED')
if ffffd_escape in new and ffffd_escape not in old:
    violations.append('T4 MOJIBAKE_ESCAPE_ADDED')
if 'chr(0xFFFD)' in new and 'chr(0xFFFD)' not in old:
    violations.append('T4 CHR_BYPASS_ADDED')

# T5. Auto-prompt regression
old_choice = len(re.findall(r'\bchoice\s+/c', old))
new_choice = len(re.findall(r'\bchoice\s+/c', new))
old_setp = len(re.findall(r'\bset\s+/p\b', old))
new_setp = len(re.findall(r'\bset\s+/p\b', new))
old_timeout = len(re.findall(r'\btimeout\s+/t', old))
new_timeout = len(re.findall(r'\btimeout\s+/t', new))
old_pause = len(re.findall(r'\bpause\s*(>nul)?\s*$', old, re.MULTILINE))
new_pause = len(re.findall(r'\bpause\s*(>nul)?\s*$', new, re.MULTILINE))
if old_choice > new_choice and new_setp > old_setp:
    violations.append('T5 CHOICE_TO_SETP_REGRESSION')
if old_timeout > new_timeout and new_pause > old_pause:
    violations.append('T5 TIMEOUT_TO_PAUSE_REGRESSION')

if violations:
    sys.stderr.write('[BLOCK] Trick patterns detected (Edit refused):\n')
    for v in violations:
        sys.stderr.write('  - ' + v + '\n')
    sys.stderr.write('\nIf user explicitly authorized this change:\n')
    sys.stderr.write('  Bypass: set environment variable ALLOW_TRICKS=1\n')
    sys.exit(1)

sys.exit(0)
