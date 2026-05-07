"""
Full audit - 10 checks across all .bat / .sh / .md / .py / .json files.

10 categories:
  1. [.bat]  cmd parsing breakage (single-line + context mode)
  2. [.bat]  encoding (UTF-8 + CRLF EOL)
  3. [.sh]   bash syntax (bash -n)
  4. [.sh]   shellcheck (if installed)
  5. [.md]   mojibake (U+FFFD replacement char)
  6. [.md]   frontmatter close check
  7. [.py]   syntax via ast.parse
  8. [.json] valid JSON parse
  9. secret leak detection (PAT/AWS key/private key in repo)
 10. capture/OCR verification (.png screenshots + ocr hook ready)

Progress shown as [N/total].
"""
import subprocess
import re
import sys
import io
import ast
import json
import shutil
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
REPLACEMENT_CHAR = chr(0xFFFD)
KOREAN_RE = re.compile(r'[가-힣]')

issues = []
def add(category, target, info):
    issues.append((category, target, info))

# ===== Collect targets =====
BAT_TARGETS = [
    'install.bat', 'install_codex.bat', 'install_gemini.bat',
    'setup/setup.bat', 'setup/install-from-git.bat',
] + sorted(str(p) for p in Path('setup/modules').glob('*.bat'))
BAT_TARGETS = [t for t in BAT_TARGETS if Path(t).exists()]

SH_TARGETS = sorted(set(
    [str(p) for p in Path('plugins').rglob('*.sh')] +
    [str(p) for p in Path('.claude/hooks').glob('*.sh')] +
    [str(p) for p in Path('.claude/scripts').rglob('*.sh')]
))

MD_TARGETS = sorted(set(
    [str(p) for p in Path('plugins').rglob('*.md')] +
    [str(p) for p in Path('.claude/commands').glob('*.md')] +
    [str(p) for p in Path('.claude/skills').glob('*.md')] +
    [str(p) for p in Path('.claude/agents').glob('*.md')] +
    [str(p) for p in Path('.claude/rules').glob('*.md')] +
    [str(p) for p in Path('docs').rglob('*.md')]
))

PY_TARGETS = sorted(set(
    [str(p) for p in Path('.claude/scripts').rglob('*.py')] +
    [str(p) for p in Path('plugins').rglob('*.py')]
))

JSON_TARGETS = sorted(set(
    [str(p) for p in Path('.claude').rglob('*.json')] +
    [str(p) for p in Path('plugins').rglob('*.json')] +
    [str(p) for p in Path('.claude-plugin').rglob('*.json')]
))

total = len(BAT_TARGETS) + len(SH_TARGETS) + len(MD_TARGETS) + len(PY_TARGETS) + len(JSON_TARGETS)
done = 0

def progress(label):
    global done
    done += 1
    print('[' + str(done) + '/' + str(total) + '] ' + label, flush=True)


# ===== 1. BAT - cmd parsing context mode =====
TMP = Path('C:/Users/ja205/AppData/Local/Temp/_audit_all.bat')
for t in BAT_TARGETS:
    progress(t + ' [bat parsing]')
    content = Path(t).read_text(encoding='utf-8', errors='replace')
    # encoding check
    raw = Path(t).read_bytes()
    if b'\r\n' not in raw and b'\n' in raw:
        add('bat_eol', t, 'LF only (cmd needs CRLF)')
    if REPLACEMENT_CHAR in content:
        add('encoding', t, 'U+FFFD found in source')
    # context run
    lines = ['@echo off', 'chcp 65001 >nul', 'setlocal enabledelayedexpansion']
    has_ko = False
    for ln in content.splitlines():
        s = ln.strip()
        if not (s.startswith('echo ') or s.startswith('echo.') or s.startswith('rem ')):
            continue
        if KOREAN_RE.search(s):
            has_ko = True
        lines.append(s)
    lines.append('exit /b 0')
    if has_ko:
        TMP.write_text('\r\n'.join(lines) + '\r\n', encoding='utf-8')
        try:
            r = subprocess.run(['cmd', '/c', str(TMP)], capture_output=True, text=True,
                               timeout=15, encoding='utf-8', errors='replace')
            out = (r.stdout or '') + (r.stderr or '')
            for m in re.finditer(r"'([^']+)'\s+is not recognized", out):
                add('bat_break', t, "NOT_RECOGNIZED: '" + m.group(1) + "'")
            if 'unexpected at this time' in out:
                add('bat_break', t, 'UNEXPECTED_AT_THIS_TIME')
        except Exception as e:
            add('bat_break', t, 'EXEC_ERR: ' + str(e))

TMP.unlink(missing_ok=True)


# ===== 2. SH - bash syntax + shellcheck =====
has_shellcheck = shutil.which('shellcheck') is not None
for t in SH_TARGETS:
    progress(t + ' [sh syntax]')
    r = subprocess.run(['bash', '-n', t], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode != 0:
        add('sh_syntax', t, (r.stderr or r.stdout).strip()[:200])
    if has_shellcheck:
        r2 = subprocess.run(['shellcheck', '-S', 'error', t], capture_output=True,
                            text=True, encoding='utf-8', errors='replace')
        if r2.returncode != 0:
            add('sh_shellcheck', t, (r2.stdout or r2.stderr).strip()[:200])


# ===== 3. MD - mojibake + frontmatter =====
for t in MD_TARGETS:
    progress(t + ' [md check]')
    try:
        content = Path(t).read_text(encoding='utf-8')
    except UnicodeDecodeError as e:
        add('md_mojibake', t, 'utf-8 decode err: ' + str(e))
        continue
    if REPLACEMENT_CHAR in content:
        add('md_mojibake', t, 'U+FFFD replacement char found')
    if content.startswith('---'):
        rest = content[3:]
        if '\n---' not in rest:
            add('md_frontmatter', t, 'frontmatter not closed')


# ===== 4. PY - ast.parse =====
for t in PY_TARGETS:
    progress(t + ' [py syntax]')
    try:
        src = Path(t).read_text(encoding='utf-8')
        ast.parse(src)
    except SyntaxError as e:
        add('py_syntax', t, str(e))
    except UnicodeDecodeError as e:
        add('py_encoding', t, 'utf-8 err: ' + str(e))


# ===== 5. JSON - valid =====
for t in JSON_TARGETS:
    progress(t + ' [json valid]')
    try:
        json.loads(Path(t).read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        add('json_invalid', t, str(e))
    except UnicodeDecodeError as e:
        add('json_encoding', t, 'utf-8 err: ' + str(e))


# ===== 6. Secret leak detection =====
SECRET_PATTERNS = [
    ('GitHub PAT', re.compile(r'ghp_[A-Za-z0-9]{30,}')),
    ('GitHub PAT (fine)', re.compile(r'github_pat_[A-Za-z0-9_]{60,}')),
    ('AWS Access Key', re.compile(r'AKIA[0-9A-Z]{16}')),
    ('Private Key', re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('Slack Webhook', re.compile(r'https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+')),
    ('OpenAI Key', re.compile(r'sk-[A-Za-z0-9]{40,}')),
]
SECRET_SCAN_PATHS = list(Path('.').glob('*.bat')) + list(Path('.').glob('*.md')) + \
                    list(Path('.').glob('*.json')) + \
                    list(Path('plugins').rglob('*.md')) + list(Path('plugins').rglob('*.json')) + \
                    list(Path('.claude').rglob('*.md')) + list(Path('.claude').rglob('*.json')) + \
                    list(Path('.claude').rglob('*.sh')) + list(Path('setup').rglob('*.bat'))
seen_secret_files = set()
for p in SECRET_SCAN_PATHS:
    if not p.is_file() or str(p) in seen_secret_files:
        continue
    seen_secret_files.add(str(p))
    progress(str(p) + ' [secret scan]')
    try:
        text = p.read_text(encoding='utf-8', errors='replace')
    except Exception:
        continue
    for label, pat in SECRET_PATTERNS:
        if pat.search(text):
            add('secret_leak', str(p), label + ' detected')


# ===== 7. Capture/OCR verification =====
CAPTURE_DIRS = ['docs/screens', '.claude/screens', 'docs/screenshots']
total_captures = 0
for d in CAPTURE_DIRS:
    if Path(d).exists():
        captures = list(Path(d).glob('*.png')) + list(Path(d).glob('*.jpg'))
        total_captures += len(captures)
        for c in captures:
            progress(str(c) + ' [capture]')
            if c.stat().st_size == 0:
                add('capture_empty', str(c), 'empty file')
            elif c.stat().st_size > 50_000_000:
                add('capture_huge', str(c), str(c.stat().st_size) + ' bytes (>50MB)')

# OCR hook readiness
ocr_hook = Path('.claude/hooks/hook-09-ocr-verify.sh')
if ocr_hook.exists():
    pass
else:
    add('ocr_missing', str(ocr_hook), 'OCR verify hook not found')


# ===== Output =====
print()
print('=' * 60)
print('AUDIT ALL - ' + str(len(issues)) + ' issue(s) across ' + str(done) + ' file(s)')
print('=' * 60)

# group by category
by_cat = {}
for c, t, info in issues:
    by_cat.setdefault(c, []).append((t, info))

for cat in sorted(by_cat.keys()):
    items = by_cat[cat]
    print()
    print('[' + cat + '] ' + str(len(items)) + ' issue(s)')
    for t, info in items:
        print('  ' + t + ': ' + str(info))

print()
print('Coverage: bat=' + str(len(BAT_TARGETS)) +
      ' sh=' + str(len(SH_TARGETS)) +
      ' md=' + str(len(MD_TARGETS)) +
      ' py=' + str(len(PY_TARGETS)) +
      ' json=' + str(len(JSON_TARGETS)) +
      ' captures=' + str(total_captures))
print('Shellcheck: ' + ('available' if has_shellcheck else 'not installed'))
print('OCR hook:   ' + ('present' if ocr_hook.exists() else 'missing'))

sys.exit(1 if issues else 0)
