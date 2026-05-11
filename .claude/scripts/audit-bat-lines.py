"""
.bat 파일의 cmd parsing 깨짐 전수 조사 (강화판).

방식 1 (단독 라인): 각 echo/rem 라인을 별도 .bat 에서 실행
방식 2 (컨텍스트):  한 .bat 의 모든 echo/rem 라인을 한 .bat 에 모아 실행
                   → install.bat 자체의 chcp 65001 + 누적 컨텍스트 재현

방식 1 만으로는 사용자가 본 install.bat:658 같은 누적 컨텍스트 깨짐을 못 잡음.
방식 2 추가로 진짜 전수 검증.
"""
import subprocess
import re
import sys
import io
import tempfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TARGETS = [
    'install.bat',
    'install_codex.bat',
    'install_gemini.bat',
    'setup/setup.bat',
    'setup/install-from-git.bat',
] + sorted(str(p) for p in Path('setup/modules').glob('*.bat'))

# OS-agnostic 임시 디렉토리 (Windows TEMP / Unix /tmp 자동)
_TMP = Path(tempfile.gettempdir())
TMP_LINE = _TMP / '_audit_line.bat'
TMP_CTX = _TMP / '_audit_ctx.bat'

errors = []


def run_cmd(bat_path, timeout=10):
    return subprocess.run(
        ['cmd', '/c', str(bat_path)],
        capture_output=True, text=True, timeout=timeout,
        encoding='utf-8', errors='replace'
    )


def collect_errors(combined, target, line_no_or_ctx):
    out = []
    for m in re.finditer(r"'([^']+)'\s+is not recognized", combined):
        out.append((target, line_no_or_ctx, f"NOT_RECOGNIZED: '{m.group(1)}'"))
    if 'unexpected at this time' in combined:
        out.append((target, line_no_or_ctx, "UNEXPECTED_AT_THIS_TIME"))
    return out


for target in TARGETS:
    if not Path(target).exists():
        continue
    content = Path(target).read_text(encoding='utf-8', errors='replace')
    lines = content.splitlines()

    # ---- 방식 1: 단독 라인 ----
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not (stripped.startswith('echo ') or stripped.startswith('echo.') or
                stripped.startswith('rem ') or stripped == 'echo.'):
            continue
        if not re.search(r'[가-힯]', stripped):
            continue
        TMP_LINE.write_text(f"@echo off\r\nchcp 65001 >nul\r\n{stripped}\r\n", encoding='utf-8')
        try:
            r = run_cmd(TMP_LINE, timeout=5)
            errors.extend(collect_errors((r.stdout or '') + (r.stderr or ''), target, str(i)))
        except Exception as e:
            errors.append((target, str(i), f'EXEC_ERR: {e}'))

    # ---- 방식 2: 컨텍스트 (모든 echo/rem 한 .bat) ----
    bat_lines = ['@echo off', 'chcp 65001 >nul', 'setlocal enabledelayedexpansion']
    has_korean = False
    for line in lines:
        stripped = line.strip()
        if not (stripped.startswith('echo ') or stripped.startswith('echo.') or
                stripped.startswith('rem ') or stripped == 'echo.'):
            continue
        if re.search(r'[가-힯]', stripped):
            has_korean = True
        bat_lines.append(stripped)
    bat_lines.append('exit /b 0')

    if has_korean:
        TMP_CTX.write_text('\r\n'.join(bat_lines) + '\r\n', encoding='utf-8')
        try:
            r = run_cmd(TMP_CTX, timeout=15)
            errors.extend(collect_errors((r.stdout or '') + (r.stderr or ''),
                                          target, 'CONTEXT'))
        except Exception as e:
            errors.append((target, 'CONTEXT', f'EXEC_ERR: {e}'))


TMP_LINE.unlink(missing_ok=True)
TMP_CTX.unlink(missing_ok=True)

if errors:
    print(f"=== {len(errors)} broken pattern(s) ===")
    for t, loc, s in errors:
        print(f"  {t}@{loc}: {s}")
    sys.exit(1)
else:
    print("=== ALL OK — 단독 + 컨텍스트 전수 검사 통과 ===")
    sys.exit(0)
