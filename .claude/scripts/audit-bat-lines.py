"""
.bat ?뚯씪??cmd parsing 源⑥쭚 ?꾩닔 議곗궗 (媛뺥솕??.

諛⑹떇 1 (?⑤룆 ?쇱씤): 媛?echo/rem ?쇱씤??蹂꾨룄 .bat ?먯꽌 ?ㅽ뻾
諛⑹떇 2 (而⑦뀓?ㅽ듃):  ??.bat ??紐⑤뱺 echo/rem ?쇱씤????.bat ??紐⑥븘 ?ㅽ뻾
                   -> install.bat ?먯껜??chcp 65001 + ?꾩쟻 而⑦뀓?ㅽ듃 ?ы쁽

諛⑹떇 1 留뚯쑝濡쒕뒗 ?ъ슜?먭? 蹂?install.bat:658 媛숈? ?꾩쟻 而⑦뀓?ㅽ듃 源⑥쭚??紐??≪쓬.
諛⑹떇 2 異붽?濡?吏꾩쭨 ?꾩닔 寃利?
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

# OS-agnostic ?꾩떆 ?붾젆?좊━ (Windows TEMP / Unix /tmp ?먮룞)
_TMP = Path(tempfile.gettempdir())
TMP_LINE = _TMP / '_audit_line.bat'

# 2026-10-06 ??Stop hook ?쇰줈 留???254珥??ㅼ륫) ?뚮ŉ CPU 瑜?癒뱀뼱 ?묐떟???먮젮議뚮떎.
#   ???.bat ??留덉?留?媛먯궗 ?댄썑 ??諛붾뚯뿀?쇰㈃ 嫄대꼫?대떎 (--force 濡?媛뺤젣).
_STAMP = Path('.claude/state/audit-bat-lines.stamp')
if '--force' not in sys.argv and _STAMP.exists():
    _last = _STAMP.stat().st_mtime
    if all(Path(t).stat().st_mtime <= _last for t in TARGETS if Path(t).exists()):
        sys.exit(0)
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

    # ---- 諛⑹떇 1: ?⑤룆 ?쇱씤 ----
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not (stripped.startswith('echo ') or stripped.startswith('echo.') or
                stripped.startswith('rem ') or stripped == 'echo.'):
            continue
        if not re.search(r'[媛-??', stripped):
            continue
        TMP_LINE.write_text(f"@echo off\r\nchcp 65001 >nul\r\n{stripped}\r\n", encoding='utf-8')
        try:
            r = run_cmd(TMP_LINE, timeout=5)
            errors.extend(collect_errors((r.stdout or '') + (r.stderr or ''), target, str(i)))
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            errors.append((target, str(i), f'EXEC_ERR: {e}'))

    # ---- 諛⑹떇 2: 而⑦뀓?ㅽ듃 (紐⑤뱺 echo/rem ??.bat) ----
    bat_lines = ['@echo off', 'chcp 65001 >nul', 'setlocal enabledelayedexpansion']
    has_korean = False
    for line in lines:
        stripped = line.strip()
        if not (stripped.startswith('echo ') or stripped.startswith('echo.') or
                stripped.startswith('rem ') or stripped == 'echo.'):
            continue
        if re.search(r'[媛-??', stripped):
            has_korean = True
        bat_lines.append(stripped)
    bat_lines.append('exit /b 0')

    if has_korean:
        TMP_CTX.write_text('\r\n'.join(bat_lines) + '\r\n', encoding='utf-8')
        try:
            r = run_cmd(TMP_CTX, timeout=15)
            errors.extend(collect_errors((r.stdout or '') + (r.stderr or ''),
                                          target, 'CONTEXT'))
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            errors.append((target, 'CONTEXT', f'EXEC_ERR: {e}'))


TMP_LINE.unlink(missing_ok=True)
TMP_CTX.unlink(missing_ok=True)

_STAMP.parent.mkdir(parents=True, exist_ok=True)
_STAMP.touch()
if errors:
    print(f"=== {len(errors)} broken pattern(s) ===")
    for t, loc, s in errors:
        print(f"  {t}@{loc}: {s}")
    sys.exit(1)
else:
    print("=== ALL OK ???⑤룆 + 而⑦뀓?ㅽ듃 ?꾩닔 寃???듦낵 ===")
    sys.exit(0)

