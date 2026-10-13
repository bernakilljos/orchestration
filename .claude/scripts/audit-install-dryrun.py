"""
install.bat / setup.bat 吏꾩쭨 ?꾩닔議곗궗 (dry-run ?ㅽ뻾).

諛⑹떇:
  1. install.bat 蹂듭궗 -> ?꾩떆 ?뚯씪
  2. destructive 紐낅졊 (powershell, copy, mkdir, reg, setx, ...) ??echo 濡?wrap
  3. admin elevation (net session, Start-Process -Verb RunAs) ?고쉶
  4. cmd 濡??ㅽ뻾 -> 紐⑤뱺 echo/rem 異쒕젰 capture
  5. 'is not recognized' / 'unexpected at this time' 寃異?

?닿쾶 吏꾩쭨 ?꾩닔議곗궗. install.bat ?먯껜瑜??앷퉴吏 ?ㅽ뻾?섎뒗 寃껉낵 ?숈씪.
"""
import subprocess
import re
import sys
import io
import shutil
import tempfile
from pathlib import Path

_TMP_DIR = Path(tempfile.gettempdir())

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TARGETS = ['install.bat', 'install_codex.bat', 'install_gemini.bat']

# destructive 紐낅졊 ?⑦꽩 (echo 濡?wrap)
DESTRUCTIVE = [
    r'^(\s*)(call\s+winget\s)',
    r'^(\s*)(call\s+npm\s)',
    r'^(\s*)(call\s+refreshenv)',
    r'^(\s*)(powershell\s)',
    r'^(\s*)(pwsh\s)',
    r'^(\s*)(copy\s+)',
    r'^(\s*)(xcopy\s)',
    r'^(\s*)(robocopy\s)',
    r'^(\s*)(mkdir\s+)',
    r'^(\s*)(rmdir\s)',
    r'^(\s*)(del\s+)',
    r'^(\s*)(reg\s+add\s)',
    r'^(\s*)(reg\s+delete\s)',
    r'^(\s*)(setx\s)',
    r'^(\s*)(attrib\s)',
    r'^(\s*)(taskkill\s)',
    r'^(\s*)(schtasks\s)',
    r'^(\s*)(start\s+)',
    r'^(\s*)(net\s+session)',
    r'^(\s*)(net\s+stop)',
    r'^(\s*)(net\s+start)',
    r'^(\s*)(where\s+)',
    r'^(\s*)(git\s+)',
    r'^(\s*)(curl\s+)',
    r'^(\s*)(certutil\s)',
    r'^(\s*)(npm\s+)',
    r'^(\s*)(pip\s+)',
    r'^(\s*)(python\s+)',
    r'^(\s*)(node\s+)',
    r'^(\s*)(claude\s+)',
    r'^(\s*)(codex\s+)',
    r'^(\s*)(gemini\s+)',
    r'^(\s*)(install_codex\.bat)',
    r'^(\s*)(install_gemini\.bat)',
]

# admin elevation ?고쉶 (?꾩껜 ?쇱씤 skip)
SKIP_PATTERNS = [
    r'^\s*if\s+%errorlevel%\s+neq\s+0\s*\(',
    r'^\s*Start-Process\s+.*-Verb\s+RunAs',
    r'goto\s+ELEVATE',
]

def transform(content):
    out = []
    for line in content.splitlines():
        new_line = line
        # destructive 紐낅졊 -> echo 濡?wrap
        for pat in DESTRUCTIVE:
            m = re.match(pat, new_line, re.IGNORECASE)
            if m:
                indent = m.group(1)
                rest = new_line[len(indent):]
                new_line = f"{indent}echo [DRYRUN] {rest}"
                break
        out.append(new_line)
    return '\r\n'.join(out) + '\r\n'

def collect_errors(combined):
    errs = []
    for m in re.finditer(r"'([^']+)'\s+is not recognized", combined):
        errs.append(f"NOT_RECOGNIZED: '{m.group(1)}'")
    for m in re.finditer(r'unexpected at this time', combined):
        errs.append("UNEXPECTED_AT_THIS_TIME")
    return errs

results = []
for target in TARGETS:
    if not Path(target).exists():
        continue
    content = Path(target).read_text(encoding='utf-8', errors='replace')
    transformed = transform(content)
    tmp = _TMP_DIR / f'_dryrun_{Path(target).name}'
    tmp.write_text(transformed, encoding='utf-8')

    try:
        # admin ?고쉶瑜??꾪빐 ?섍꼍蹂??+ skip ?몄옄
        r = subprocess.run(
            ['cmd', '/c', str(tmp), '--dryrun-skip'],
            capture_output=True, text=True, timeout=60,
            encoding='utf-8', errors='replace',
            input='n\nn\nn\n\n\n\n\n\n\n'  # 紐⑤뱺 prompt ??N
        )
        combined = (r.stdout or '') + (r.stderr or '')
        errs = collect_errors(combined)
        if errs:
            results.append((target, errs, combined[:2000]))
        else:
            results.append((target, [], None))
    except subprocess.TimeoutExpired as e:
        results.append((target, ['TIMEOUT'], (e.stdout or b'').decode('utf-8', errors='replace')[:2000]))
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        results.append((target, [f'EXEC_ERR: {e}'], None))
    finally:
        tmp.unlink(missing_ok=True)

any_err = False
for target, errs, output in results:
    if errs:
        any_err = True
        print(f"=== {target}: {len(errs)} errors ===")
        for e in errs:
            print(f"  - {e}")
        if output:
            print("--- output snippet ---")
            print(output[-1500:])
            print("---")
    else:
        print(f"=== {target}: OK ===")

sys.exit(1 if any_err else 0)

