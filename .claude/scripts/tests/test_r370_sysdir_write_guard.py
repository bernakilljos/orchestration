"""R370 (2026-11-23) — Windows 시스템 폴더에 잔여 파일을 만드는 쓰기·리디렉션 사전 차단.

계기: C:\\Windows\\System32\\powershell (확장자 없는 0바이트 · 2026-04-08 생성 · 생성 주체 UNKNOWN) 때문에
PowerShell 에서 `powershell` 이 '앱 선택' 창을 띄웠다. 같은 종류 재발(작업 폴더가 System32 인 상태의 `> 이름` 등)을 막는다.
판정 함수만 호출 — 실제 System32 접촉 0.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "prompt"))
sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "tool"))
import block_dangerous_bash as bdb  # noqa: E402

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows 전용")
SYS = os.environ.get("SystemRoot", r"C:\Windows")
S32 = SYS + r"\System32"
PROJ = str(ROOT)


@pytest.mark.parametrize("cmd,cwd", [
    ("echo x > powershell", S32),                                   # 이번 사고와 같은 모양 (작업 폴더 System32 + 상대 리디렉션)
    ("Get-Process 2> powershell", S32),
    ("cd C:\\Windows\\System32 && dir > out", PROJ),                # 명령 안에서 System32 로 이동 뒤 쓰기
    ("Set-Location $env:SystemRoot\\System32; 'a' | Out-File powershell", PROJ),
    ("echo x > C:\\Windows\\System32\\foo", PROJ),                  # 절대 경로 대상
    ("echo x > /c/Windows/System32/foo", PROJ),                     # Git Bash 경로 표기
    ("'x' | Set-Content -Path %SystemRoot%\\System32\\foo", PROJ),
])
def test_blocks_writes_into_windows_dir(cmd, cwd):
    assert bdb._system_dir_write(cmd, cwd), cmd


@pytest.mark.parametrize("cmd,cwd", [
    ("echo x > out.txt", PROJ),                                     # 프로젝트 안 상대 쓰기 = 정상
    ("dir C:\\Windows\\System32 > list.txt", PROJ),                 # 시스템 폴더 '읽기' 결과를 프로젝트에 저장
    ("whoami > nul", S32),                                          # 버림
    ("Get-Process 2>$null", S32),
    ("cmd /c ver 2>&1", S32),                                       # 스트림 합치기
    ("& $PSHOME\\powershell.exe -NoProfile -Command 'ok'", S32),     # 실행만
    ("Get-Content C:\\Windows\\System32\\drivers\\etc\\hosts", PROJ),
    ("python -c \"print(1 > 0)\"", S32),                            # 따옴표 안 비교 연산자
])
def test_allows_normal_commands(cmd, cwd):
    assert bdb._system_dir_write(cmd, cwd) is None, cmd


def test_run_denies_end_to_end(monkeypatch):
    payload = {"tool_name": "Bash", "tool_input": {"command": "echo x > powershell"}, "cwd": S32}
    monkeypatch.setattr(bdb, "py_stdin_text", lambda ctx: json.dumps(payload))
    r = bdb.run(object())
    out = json.loads(r.out if hasattr(r, "out") else r[1])
    hso = out["hookSpecificOutput"]
    assert hso["permissionDecision"] == "deny" and "R370" in hso["permissionDecisionReason"]
    payload["cwd"] = PROJ
    assert bdb.run(object()) is None                                # 같은 명령도 프로젝트 폴더면 통과


# R371 #6 (외부 검토): 정규식 우회 형태 — 수정 전 6건 모두 통과(누락) 재현 → 구간별 판정으로 수정
@pytest.mark.skipif(sys.platform != "win32", reason="Windows 전용 판정")
@pytest.mark.parametrize("cmd", [
    r"cd C:\Windows\System32; echo x > powershell; cd C:\pjt\proj",   # 이동 → 쓰기 → 되돌아오기
    r"Set-Content -Value x -Path C:\Windows\System32\foo",             # -Path 가 뒤에
    r"Out-File -InputObject x -FilePath C:\Windows\System32\foo",
    r'echo x > "C:\Windows\System32\foo"',                             # 따옴표로 감싼 대상
    r"echo x > ${env:SystemRoot}\System32\foo",                        # ${env:} 표기
    r"New-Item -ItemType File -Path $env:windir\foo",
])
def test_r371_bypass_forms_blocked(cmd):
    assert bdb._system_dir_write(cmd, PROJ)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows 전용 판정")
@pytest.mark.parametrize("cmd", [
    r"cd C:\Windows\System32; dir; cd C:\pjt\proj; echo x > out.txt",  # 되돌아온 뒤 쓰기 = 정상
    r"Set-Content -Path out.txt -Value C:\Windows\System32",            # 값에 시스템 경로 문자열
    r'echo "a > C:\Windows\x" > out.txt',                               # 따옴표 안 문자열
    "cat >> t.py <<'EOF'\n" + r"New-Item -Path $env:windir\foo" + "\nEOF",   # heredoc 본문 = 데이터
])
def test_r371_no_false_positive(cmd):
    assert bdb._system_dir_write(cmd, PROJ) is None
