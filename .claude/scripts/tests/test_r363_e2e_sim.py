"""R363 (2026-11-23) — 승인 교착·가짜 명령 파일 정리 12종 격리 E2E 시뮬레이션.

실제 PreToolUse 훅(approval_gate_detect.run)과 프롬프트 승인(user_approval.run)을 그대로 거친다.
승인 DB = ORCHESTRATION_ROOT 임시 폴더 · 삭제·권한 시험 = tmp_path 안 가짜 파일만 (실제 System32 파일 접촉 0).
시나리오 이름 a~l 은 .ai-collab/requests/R363.md 의 12종 목록과 같다.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "prompt"))
sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "tool"))
import approval_gate_detect as agd  # noqa: E402

_spec = importlib.util.spec_from_file_location("_gate_r363", ROOT / ".claude" / "scripts" / "approval-gate.py")
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

SCRIPT = ROOT / ".claude" / "scripts" / "remove-shadow-command.ps1"
PS = str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe")
win = pytest.mark.skipif(os.name != "nt", reason="Windows 전용")


@pytest.fixture
def tmp_root(tmp_path, monkeypatch):
    monkeypatch.setenv("ORCHESTRATION_ROOT", str(tmp_path))
    (tmp_path / ".claude" / "state").mkdir(parents=True)
    (tmp_path / "plugins").mkdir()
    with sqlite3.connect(tmp_path / ".claude" / "state" / "orca.db") as c:
        c.execute("CREATE TABLE tasks (task_id TEXT PRIMARY KEY, task_file TEXT NOT NULL, status TEXT NOT NULL, "
                  "created_at INTEGER NOT NULL, completed_at INTEGER, approval_state TEXT DEFAULT 'not_required', "
                  "risk_category TEXT, risk_detail TEXT, approved_at INTEGER, approved_by TEXT)")
    assert str(gate.get_db_path()).startswith(str(tmp_path))
    return tmp_path


def _hook(cmd, cwd, resp=None):
    import _common
    payload = {"tool_name": "PowerShell", "tool_input": {"command": cmd}, "cwd": cwd}
    if resp is not None:
        payload["tool_response"] = resp
    ctx = _common.Ctx(json.dumps(payload, ensure_ascii=False))
    ctx.project_dir = str(ROOT)
    return ctx


def _prompt(text):
    import _common
    import user_approval
    ctx = _common.Ctx(json.dumps({"prompt": text}))
    ctx.project_dir = str(ROOT)
    return user_approval.run(ctx)


def _tid(r):
    return re.search(r"appr-[0-9a-f]{12}", r.err).group(0)


def _rows(state=None):
    q = "SELECT task_id, approval_state, status FROM tasks WHERE task_file='<approval-gate>'"
    with sqlite3.connect(gate.get_db_path()) as c:
        rows = c.execute(q).fetchall()
    return [r for r in rows if state is None or r[1] == state]


def _runas(script, extra=""):
    return f"Start-Process powershell -Verb RunAs -Wait -ArgumentList '-File','{script}'{extra}"


def _fixture_script(tmp_root, body="Write-Host 'x'\n"):
    s = tmp_root / "fix.ps1"
    s.write_text(body, encoding="utf-8")
    return s


def _ps(*args, pre=""):
    cmd = [PS, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command",
           pre + "& '" + str(SCRIPT) + "' " + " ".join(args) + "; exit $LASTEXITCODE"]
    r = subprocess.run(cmd, capture_output=True, timeout=120)
    raw = r.stdout + r.stderr   # 콘솔 코드페이지가 실행 환경마다 다름 (회귀 게이트 = UTF-8 · 일반 = ANSI) → 둘 다 해석해 이어 붙임
    return r.returncode, raw.decode("utf-8", "replace") + " | " + raw.decode("mbcs", "replace")


def _shadow_dir(tmp_path):
    """가짜 명령 파일 fixture: d/tool (0바이트·확장자 없음) + d/tool.exe (진짜 실행 파일 사본)."""
    d = tmp_path / "sys"
    d.mkdir()
    shutil.copy2(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "whoami.exe", d / "tool.exe")
    (d / "tool").write_bytes(b"")
    return d


# (a) 유효 승인 없는 RunAs 차단 — 대기 요청 1건
def test_a_runas_without_approval_blocked(tmp_root):
    r = agd.run(_hook(_runas(_fixture_script(tmp_root)), str(tmp_root)))
    assert r is not None and r.rc == 2 and "security" in r.err
    assert len(_rows("waiting")) == 1


# (b) 승인된 정확한 명령 한 번만 실행
def test_b_exact_approved_command_once(tmp_root):
    cmd = _runas(_fixture_script(tmp_root))
    t = _tid(agd.run(_hook(cmd, str(tmp_root))))
    assert "승인 기록됨" in _prompt(f"/approve {t}")
    assert agd.run(_hook(cmd, str(tmp_root))) is None
    r = agd.run(_hook(cmd, str(tmp_root)))
    assert r.rc == 2 and _tid(r) != t


# (c) 승인 뒤 스크립트 변경 = 안전 차단 · 옛 승인 행 그대로
def test_c_script_changed_after_approval_blocked(tmp_root):
    s = _fixture_script(tmp_root)
    cmd = _runas(s)
    t = _tid(agd.run(_hook(cmd, str(tmp_root))))
    gate.approve(t, gate.USER_APPROVER)
    s.write_text("Write-Host 'changed'\n", encoding="utf-8")
    r = agd.run(_hook(cmd, str(tmp_root)))
    assert r.rc == 2 and _tid(r) != t and "바뀌어" in r.err


# (d) 명령 글자 변경 → 새 번호 + 옛 대기 번호·해결 경로 안내 (R363 수정 대상 · 수정 전 FAIL)
def test_d_changed_command_notice_prevents_deadlock(tmp_root):
    s = _fixture_script(tmp_root)
    t1 = _tid(agd.run(_hook(_runas(s), str(tmp_root))))
    r2 = agd.run(_hook(f"Start-Process -FilePath powershell -Verb RunAs -ArgumentList '-NoProfile','-File','{s}'",
                       str(tmp_root)))
    t2 = _tid(r2)
    assert t2 != t1
    assert "승인 교착" in r2.err and t1 in r2.err, "옛 대기 번호를 알리지 않아 승인 교착이 생김"
    assert r2.err.index(t2) < r2.err.index(t1)          # 맨 앞 번호 = 지금 명령의 번호


# (e) 같은 명령 재시도 2회·5회 → 같은 번호·새 행 없음 · 일상어 재촉은 승인이 아님
@pytest.mark.parametrize("n", [2, 5])
def test_e_repeat_same_command_same_id(tmp_root, n):
    cmd = _runas(_fixture_script(tmp_root))
    ids = {_tid(agd.run(_hook(cmd, str(tmp_root)))) for _ in range(n)}
    assert len(ids) == 1 and len(_rows()) == 1
    for text in ("지우라고", "그러면 바로해", "내가 지시했자나 하라고"):
        assert _prompt(text) is None
    assert _rows("waiting")[0][0] in ids


# (f) 거절·만료·실행 실패(UAC 취소에 해당) → 실행 안 됨·성공 기록 안 됨
def test_f_reject_expire_and_failed_run(tmp_root):
    cmd = _runas(_fixture_script(tmp_root))
    t = _tid(agd.run(_hook(cmd, str(tmp_root))))
    assert "거부 기록됨" in _prompt(f"/reject {t} 시험")
    r = agd.run(_hook(cmd, str(tmp_root)))
    assert r.rc == 2 and _tid(r) != t
    t2 = _tid(r)
    with sqlite3.connect(gate.get_db_path()) as c:
        c.execute("UPDATE tasks SET created_at=created_at-? WHERE task_id=?", (gate.REQUEST_TTL_SEC + 10, t2))
    t3 = _tid(agd.run(_hook(cmd, str(tmp_root))))
    assert t3 not in (t, t2)                            # 만료된 대기 번호는 다시 안내하지 않음
    gate.approve(t3, gate.USER_APPROVER)
    assert agd.run(_hook(cmd, str(tmp_root))) is None
    agd.run_action(_hook(cmd, str(tmp_root), {"stdout": "", "stderr": "The operation was canceled by the user.",
                                              "interrupted": True}), "post")
    assert gate.status(t3)["status"] == "failed"        # UAC 취소·중단 = 실패 기록 (성공 아님)


# (g) 일반 권한 부족 → rc 20 · 파일 그대로 (실제 System32 와 같은 «삭제 시 UnauthorizedAccess» 를 주입 · 읽기는 허용)
#     참고: 읽기까지 막힌 파일이면 서명 조회 예외로 rc 1 이 된다 (발견 · 대기 승인 appr-713617e80d83 의 스크립트 해시를
#     바꾸지 않으려고 미적용 — 실제 대상은 읽기 가능해 해당 없음)
@win
def test_g_permission_denied_rc20(tmp_path):
    d = _shadow_dir(tmp_path)
    rc, out = _ps("-Path", f"'{d / 'tool'}'",
                  pre="function global:Remove-Item { param($LiteralPath, [switch]$Force) "
                      "throw [System.UnauthorizedAccessException]::new('Access to the path is denied.') }; ")
    assert rc == 20 and "권한 부족" in out, out
    assert (d / "tool").exists()


# (h) 권한 있는 격리 파일 = 삭제 + Test-Path 없음 + 진짜 exe 가 이름을 받음
@win
def test_h_isolated_shadow_removed(tmp_path):
    d = _shadow_dir(tmp_path)
    rc, out = _ps("-Path", f"'{d / 'tool'}'")
    assert rc == 0 and "삭제·검증 완료" in out, out
    assert not (d / "tool").exists() and (d / "tool.exe").exists()
    rc, out = _ps("-Path", f"'{d / 'tool'}'")
    assert rc == 3                                      # 다시 실행 = 이미 없음 (거짓 재삭제 없음)


# (i) 크기·확장자·짝 없는 파일·폴더·링크는 보존
@win
def test_i_non_target_files_kept(tmp_path):
    d = _shadow_dir(tmp_path)
    (d / "tool").write_bytes(b"x")                      # 1바이트
    rc, _ = _ps("-Path", f"'{d / 'tool'}'")
    assert rc == 10 and (d / "tool").exists()
    (d / "lonely").write_bytes(b"")                     # 같은 이름 진짜 exe 없음
    rc, _ = _ps("-Path", f"'{d / 'lonely'}'")
    assert rc == 10 and (d / "lonely").exists()
    (d / "dirx").mkdir()
    rc, _ = _ps("-Path", f"'{d / 'dirx'}'")
    assert rc == 10 and (d / "dirx").exists()
    (d / "tool.txt").write_bytes(b"")
    rc, _ = _ps("-Path", f"'{d / 'tool.txt'}'")
    assert rc == 10 and (d / "tool.txt").exists()


@win
def test_i_reparse_point_kept(tmp_path):
    d = _shadow_dir(tmp_path)
    (d / "target").write_bytes(b"")
    (d / "tool").unlink()
    try:
        os.symlink(d / "target", d / "tool")
    except OSError as e:
        pytest.skip("심볼릭 링크 생성 권한 없음 (개발자 모드 꺼짐) — NOT_VERIFIED: %s" % e)
    rc, _ = _ps("-Path", f"'{d / 'tool'}'")
    assert rc == 10 and os.path.lexists(d / "tool")


# (j) 삭제 명령이 조용히 성공(rc 0)해도 파일이 남으면 실패 30 — 거짓 완료 금지
@win
def test_j_silent_noop_delete_reports_30(tmp_path):
    d = _shadow_dir(tmp_path)
    rc, out = _ps("-Path", f"'{d / 'tool'}'", pre="function global:Remove-Item { param($LiteralPath, [switch]$Force) }; ")
    assert rc == 30 and "남아 있음" in out, out
    assert (d / "tool").exists()


# (k) 명령 검색 차이: 실제 구조(가짜 파일이 진짜 exe 보다 앞 PATH 폴더 = System32 vs WindowsPowerShell\v1.0)
#     PowerShell 은 앞 폴더의 확장자 없는 가짜를 먼저 잡고, cmd·Python 은 PATHEXT 로 .exe 만 찾는다
@win
def test_k_command_resolution_differs(tmp_path):
    a, b = tmp_path / "first", tmp_path / "second"
    a.mkdir(); b.mkdir()
    (a / "tool").write_bytes(b"")
    shutil.copy2(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "whoami.exe", b / "tool.exe")
    env = dict(os.environ, PATH=str(a) + os.pathsep + str(b) + os.pathsep + os.environ.get("PATH", ""))
    first = [PS, "-NoProfile", "-NonInteractive", "-Command", "(Get-Command tool -All | Select-Object -First 1).Source"]
    r = subprocess.run(first, capture_output=True, env=env, timeout=60)
    assert r.stdout.decode("mbcs", "replace").strip().lower() == str(a / "tool").lower()   # 앱 선택 창 원인 재현
    assert shutil.which("tool", path=env["PATH"]).lower() == str(b / "tool.exe").lower()
    r = subprocess.run(["cmd", "/c", "tool"], capture_output=True, env=env, timeout=60)   # where 는 가짜도 목록에 보이지만 실행은 PATHEXT
    assert r.returncode == 0 and os.environ.get("USERNAME", "").lower() in r.stdout.decode("mbcs", "replace").lower()
    r = subprocess.run([PS, "-NoProfile", "-NonInteractive", "-Command", f"& '{b / 'tool.exe'}'; exit $LASTEXITCODE"],
                       capture_output=True, env=env, timeout=60)
    assert r.returncode == 0                            # 전체 경로 = 가짜 파일 영향 없음 (비파괴 대안)
    rc, out = _ps("-Path", f"'{a / 'tool'}'", pre="$env:PATH = '%s;' + $env:PATH; " % b)
    assert rc == 0 and not (a / "tool").exists(), out   # 다른 폴더의 진짜 exe 로도 가짜 판정 → 정리
    r = subprocess.run(first, capture_output=True, env=env, timeout=60)
    assert r.stdout.decode("mbcs", "replace").strip().lower() == str(b / "tool.exe").lower()   # 이름이 진짜 exe 로 복구


# (l) 실행·결과 기록 뒤 같은 범위 대기 요청이 다시 생기지 않음
def test_l_no_duplicate_waiting_after_done(tmp_root):
    cmd = _runas(_fixture_script(tmp_root))
    t = _tid(agd.run(_hook(cmd, str(tmp_root))))
    gate.approve(t, gate.USER_APPROVER)
    assert agd.run(_hook(cmd, str(tmp_root))) is None
    agd.run_action(_hook(cmd, str(tmp_root), {"stdout": "[0] ok", "interrupted": False}), "post")
    assert gate.status(t)["status"] == "done"
    assert _rows("waiting") == []                       # 결과 보고 뒤 자동 재요청 없음


# (m) R364: git 의 줄바꿈 변환(LF↔CRLF)만으로 승인이 무효가 되지 않음 · 실제 내용 변경은 계속 차단
def test_m_line_ending_change_keeps_approval_content_change_blocks(tmp_root):
    s = tmp_root / "eol.ps1"
    s.write_bytes(b"Write-Host 'a'\nWrite-Host 'b'\n")
    cmd = _runas(s)
    t = _tid(agd.run(_hook(cmd, str(tmp_root))))
    gate.approve(t, gate.USER_APPROVER)
    s.write_bytes(b"Write-Host 'a'\r\nWrite-Host 'b'\r\n")      # git checkout 이 CRLF 로 바꾼 상황
    assert agd.run(_hook(cmd, str(tmp_root))) is None           # 같은 내용 → 승인 1회 소비
    t2 = _tid(agd.run(_hook(cmd, str(tmp_root))))
    gate.approve(t2, gate.USER_APPROVER)
    s.write_bytes(b"Write-Host 'a'\r\nWrite-Host 'CHANGED'\r\n")
    r = agd.run(_hook(cmd, str(tmp_root)))
    assert r is not None and r.rc == 2 and "바뀌어" in r.err     # 내용 변경 → 차단
