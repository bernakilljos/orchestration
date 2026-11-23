"""R365 (2026-11-23) — 최초 1회 UAC 후 허용 관리자 작업 실행 계층 격리 시험.

실제 예약 작업 등록·SYSTEM 실행은 관리자 권한이 필요해 여기서 하지 않는다 (사용자 1회 승인 뒤 실측).
여기서는 Install 이 만들 보호 폴더 구성을 임시 폴더에 그대로 재현하고, 실행기(elevated-runner.ps1)를 직접 실행해
허용·거부·해시 변조·형식 오류·TOCTOU 재검사를 확인한다. 실제 System32 파일 접촉 0.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
S = ROOT / ".claude" / "scripts"
PS = str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe")
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows 전용")


def _run(script, *args):
    r = subprocess.run([PS, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script), *args],
                       capture_output=True, timeout=120)
    return r.returncode, (r.stdout + r.stderr).decode("utf-8", "replace") + (r.stdout + r.stderr).decode("mbcs", "replace")


@pytest.fixture
def layer(tmp_path):
    """Install 과 같은 구성 (ACL 제외): root(실행기·작업 스크립트 사본·hashes·allow) + io(inbox·outbox) + 가짜 System32."""
    root, io, sysd = tmp_path / "root", tmp_path / "io", tmp_path / "sys32"
    for d in (root, io / "inbox", io / "outbox", sysd):
        d.mkdir(parents=True)
    lines = []
    for f in ("elevated-runner.ps1", "remove-shadow-command.ps1"):
        shutil.copy2(S / f, root / f)
        lines.append(hashlib.sha256((root / f).read_bytes()).hexdigest().upper() + " " + f)
    (root / "hashes.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    allow = {"remove-shadow-command": {"path_regex": "(?i)^" + re.escape(str(sysd)) + r"\\[a-z0-9_-]{1,64}$"}}
    (root / "allow.json").write_text(json.dumps(allow), encoding="utf-8")
    shutil.copy2(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "whoami.exe", sysd / "tool.exe")
    (sysd / "tool").write_bytes(b"")
    return root, io, sysd


def _request(layer, op, path):
    root, io, _ = layer
    rc, out = _run(S / "elevated-task.ps1", "-Action", "Request", "-Op", op, "-Path", str(path),
                   "-Root", str(root), "-Io", str(io), "-NoTrigger", "-TimeoutSec", "0")
    assert rc == 51, out                                   # 실행기를 안 불렀으니 결과 대기 시간 초과가 정상
    return re.search(r"id=(r\d{14}-[0-9a-f]{8})", out).group(1)


def _drain(layer):
    root, io, _ = layer
    rc, out = _run(root / "elevated-runner.ps1", "-Root", str(root), "-Io", str(io))
    assert rc == 0, out


def _result(layer, rid):
    return json.loads((layer[1] / "outbox" / (rid + ".json")).read_text(encoding="utf-8"))


def test_allowed_op_removes_isolated_shadow(layer):
    rid = _request(layer, "remove-shadow-command", layer[2] / "tool")
    assert (layer[1] / "inbox" / (rid + ".json")).exists()
    _drain(layer)
    res = _result(layer, rid)
    assert res["code"] == 0 and not (layer[2] / "tool").exists() and (layer[2] / "tool.exe").exists()
    assert "남아 있음=False" in res["message"]
    assert not any((layer[1] / "inbox").iterdir())         # 요청은 처리 후 제거 (재실행 X)
    assert "code=0" in (layer[0] / "audit.log").read_text(encoding="utf-8")


def test_rechecks_target_at_run_time(layer):
    rid = _request(layer, "remove-shadow-command", layer[2] / "tool")
    (layer[2] / "tool").write_bytes(b"x")                  # 요청 뒤 대상이 바뀜 (TOCTOU)
    _drain(layer)
    assert _result(layer, rid)["code"] == 10 and (layer[2] / "tool").exists()


@pytest.mark.parametrize("op,rel", [
    ("delete-anything", "tool"),                           # 허용 목록에 없는 작업
    ("remove-shadow-command", None),                       # 허용 폴더 밖 경로
    ("remove-shadow-command", "sub\\..\\tool"),            # 상위 경로 우회
    ("remove-shadow-command", "tool.txt"),                 # 확장자 있는 이름 = 정규식 밖
])
def test_disallowed_requests_rejected_40(layer, tmp_path, op, rel):
    target = (tmp_path / "elsewhere") if rel is None else Path(str(layer[2]) + "\\" + rel)
    rid = _request(layer, op, target)
    _drain(layer)
    assert _result(layer, rid)["code"] == 40
    assert (layer[2] / "tool").exists()


def test_tampered_task_script_rejected_42(layer):
    with open(layer[0] / "remove-shadow-command.ps1", "a", encoding="utf-8") as f:
        f.write("\n# tampered\n")
    rid = _request(layer, "remove-shadow-command", layer[2] / "tool")
    _drain(layer)
    assert _result(layer, rid)["code"] == 42 and (layer[2] / "tool").exists()


def test_malformed_request_41_and_no_execution(layer):
    (layer[1] / "inbox" / "bad.json").write_text('{"id":"../../x","op":"remove-shadow-command","path":"%s"}'
                                                 % str(layer[2] / "tool").replace("\\", "\\\\"), encoding="utf-8")
    _drain(layer)
    outs = list((layer[1] / "outbox").glob("*.json"))
    assert len(outs) == 1 and json.loads(outs[0].read_text(encoding="utf-8"))["code"] == 41
    assert outs[0].name.startswith("invalid-") and (layer[2] / "tool").exists()


def test_install_and_uninstall_require_admin_50(tmp_path):
    for act in ("Install", "Uninstall"):
        rc, out = _run(S / "elevated-task.ps1", "-Action", act, "-Root", str(tmp_path / "r"), "-Io", str(tmp_path / "i"))
        assert rc == 50, out
    assert not (tmp_path / "r").exists()                   # 권한 없으면 아무것도 만들지 않음


def test_request_without_install_50(tmp_path):
    rc, out = _run(S / "elevated-task.ps1", "-Action", "Request", "-Op", "remove-shadow-command", "-Path", "x",
                   "-Root", str(tmp_path / "r"), "-Io", str(tmp_path / "i"))
    assert rc == 50, out


def _json_line(out):
    return json.loads(next(l for l in out.splitlines() if l.strip().startswith("{")))


def test_status_reports_hash_tamper(layer):
    root, io, _ = layer
    rc, out = _run(S / "elevated-task.ps1", "-Action", "Status", "-Root", str(root), "-Io", str(io))
    st = _json_line(out)
    assert rc == 0 and st["hashes_ok"] is True
    (root / "elevated-runner.ps1").write_text("# x", encoding="utf-8")
    rc, out = _run(S / "elevated-task.ps1", "-Action", "Status", "-Root", str(root), "-Io", str(io))
    assert _json_line(out)["hashes_ok"] is False
