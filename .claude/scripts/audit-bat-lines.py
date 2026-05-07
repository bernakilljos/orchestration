"""
install.bat 와 모든 setup 모듈의 echo/rem 라인 전수 검사.
각 라인을 단독 .bat 에 넣고 cmd 로 실행해 'is not recognized' 발생 여부 확인.
"""
import subprocess
import re
import sys
import io
from pathlib import Path

# stdout 을 UTF-8 로 강제 (Windows cp949 회피)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

TARGETS = [
    'install.bat',
    'install_codex.bat',
    'install_gemini.bat',
    'setup/setup.bat',
    'setup/install-from-git.bat',
] + [str(p) for p in Path('setup/modules').glob('*.bat')]

TEST_BAT = Path('C:/Users/ja205/AppData/Local/Temp/_audit_test.bat')

errors = []
for target in TARGETS:
    if not Path(target).exists():
        continue
    content = Path(target).read_text(encoding='utf-8', errors='replace')
    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not (stripped.startswith('echo ') or stripped.startswith('echo.') or
                stripped.startswith('rem ') or stripped == 'echo.'):
            continue
        # 한글 포함 라인만 (ASCII only 는 cmd 가 잘 처리)
        if not re.search(r'[가-힯一-鿿]', stripped):
            continue
        # 단독 .bat
        test_content = f"@echo off\r\nchcp 65001 >nul\r\n{stripped}\r\n"
        TEST_BAT.write_text(test_content, encoding='utf-8')
        try:
            result = subprocess.run(
                ['cmd', '/c', str(TEST_BAT)],
                capture_output=True, text=True, timeout=5,
                encoding='utf-8', errors='replace'
            )
            combined = (result.stdout or '') + (result.stderr or '')
            if 'is not recognized' in combined or 'unexpected at this time' in combined:
                errors.append((target, i, stripped[:120]))
        except Exception as e:
            errors.append((target, i, f"[exec error: {e}] {stripped[:80]}"))

TEST_BAT.unlink(missing_ok=True)

if errors:
    print(f"=== {len(errors)} broken lines ===")
    for t, i, s in errors:
        print(f"{t}:{i}: {s}")
    sys.exit(1)
else:
    print("=== ALL OK — 전수 검사 통과 ===")
    sys.exit(0)
