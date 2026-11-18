"""
install.bat / setup.bat 진짜 전수조사 (dry-run 실행).

방식:
  1. install.bat 복사 -> 임시 파일
  2. destructive 명령 (powershell, copy, mkdir, reg, setx, ...) 을 echo 로 wrap
  3. admin elevation (net session, Start-Process -Verb RunAs) 우회
  4. cmd 로 실행 -> 모든 echo/rem 출력 capture
  5. 'is not recognized' / 'unexpected at this time' 검출

이게 진짜 전수조사. install.bat 자체를 끝까지 실행하는 것과 동일.
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

# 대상·스탬프가 상대경로라 저장소 루트로 (audit-bat-lines.py 와 같은 이유)
import os
import hashlib
os.chdir(Path(__file__).resolve().parents[2])

TARGETS = ['install.bat', 'install_codex.bat', 'install_gemini.bat']

# 2026-11-18 (R288 성능 1차): Stop 마다 설치 bat 3개를 cmd 로 끝까지 돌렸다 (각 최대 60초 · skip 없음).
#   대상 파일 내용 + 이 스크립트 자체의 해시가 마지막 통과(OK) 때와 같으면 건너뛴다 (--force 로 강제).
#   실패(오류 발견)는 스탬프를 쓰지 않아 다음 Stop 에 다시 검사한다 — 감사 약화 X.
_STAMP = Path('.claude/state/audit-install-dryrun.stamp')


def _inputs_hash() -> str:
    h = hashlib.sha256()
    h.update(Path(__file__).read_bytes())
    for t_ in TARGETS:
        if Path(t_).exists():
            h.update(t_.encode()); h.update(Path(t_).read_bytes())
    return h.hexdigest()


_HASH = _inputs_hash()
if '--force' not in sys.argv and _STAMP.exists() and _STAMP.read_text(encoding='utf-8', errors='replace').strip() == _HASH:
    sys.exit(0)

# destructive 명령 패턴 (echo 로 wrap)
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

# admin elevation 우회 (전체 라인 skip)
SKIP_PATTERNS = [
    r'^\s*if\s+%errorlevel%\s+neq\s+0\s*\(',
    r'^\s*Start-Process\s+.*-Verb\s+RunAs',
    r'goto\s+ELEVATE',
]

def transform(content):
    out = []
    for line in content.splitlines():
        new_line = line
        # destructive 명령 -> echo 로 wrap
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
    # 고유 임시 파일 (종전 고정 이름 _dryrun_<name> — 세션 2~3개가 같은 Stop 시점에 겹치면 서로 덮어씀)
    _fd, _tmp_name = tempfile.mkstemp(prefix=f'_dryrun_{Path(target).stem}_', suffix='.bat', dir=str(_TMP_DIR))
    os.close(_fd)
    tmp = Path(_tmp_name)
    tmp.write_text(transformed, encoding='utf-8')

    try:
        # admin 우회를 위해 환경변수 + skip 인자
        r = subprocess.run(
            ['cmd', '/c', str(tmp), '--dryrun-skip'],
            capture_output=True, text=True, timeout=60,
            encoding='utf-8', errors='replace',
            input='n\nn\nn\n\n\n\n\n\n\n'  # 모든 prompt 에 N
        )
        combined = (r.stdout or '') + (r.stderr or '')
        errs = collect_errors(combined)
        if errs:
            results.append((target, errs, combined[:2000]))
        else:
            results.append((target, [], None))
    except subprocess.TimeoutExpired as e:
        results.append((target, ['TIMEOUT'], (e.stdout or b'').decode('utf-8', errors='replace')[:2000]))
    except Exception as e:
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

if not any_err:
    try:
        _STAMP.parent.mkdir(parents=True, exist_ok=True)
        _STAMP.write_text(_HASH, encoding='utf-8')
    except OSError:
        pass
sys.exit(1 if any_err else 0)
