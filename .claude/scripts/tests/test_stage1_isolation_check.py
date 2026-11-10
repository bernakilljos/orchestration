"""Stage 1 Agent 계정 격리 검사 스크립트 회귀 (2026-11-09).

원래 사용자로 실행 = 자가 점검 모드 (자격 증명 조회 안 함 · 판정 아님). 실제 판정은 orca-agent 로그인 후 실행해야 한다.
여기서는 스크립트가 PowerShell 5.1 에서 돌고, §53-3·§55 항목을 모두 담고, 값을 출력하지 않는지만 확인한다.
"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude" / "scripts" / "stage1-agent-isolation-check.ps1"
PS = shutil.which("powershell.exe") or shutil.which("powershell")

pytestmark = pytest.mark.skipif(os.name != "nt" or not PS, reason="Windows PowerShell 필요")


def test_script_has_bom_and_parses():
    assert SCRIPT.read_bytes()[:3] == b"\xef\xbb\xbf"          # 한글 .ps1 = UTF-8 BOM (D22)
    r = subprocess.run([PS, "-NoProfile", "-Command",
                        "$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('%s',[ref]$null,[ref]$e); $e.Count"
                        % str(SCRIPT)], capture_output=True, text=True, timeout=60)
    assert r.stdout.strip().endswith("0"), r.stdout + r.stderr


def test_self_test_runs_covers_all_items_and_prints_no_values(tmp_path):
    env = {k: v for k, v in os.environ.items()}
    r = subprocess.run([PS, "-NoProfile", "-File", str(SCRIPT), "-OutDir", str(tmp_path)],
                       capture_output=True, timeout=120, env=env)
    out = r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
    files = list(tmp_path.glob("stage1-isolation-*.json"))
    assert files, out
    d = json.loads(files[0].read_text(encoding="utf-8-sig"))
    ids = {x["id"] for x in d["results"]}
    assert {"C1a", "C1b", "1", "2", "3", "4", "5", "5s", "5r", "5w", "5g", "5h", "6", "7", "8", "10b", "12", "13", "14",
            "C4"} <= ids
    assert d["self_test"] is True and d["verdict"].startswith("SELF-TEST")       # 원래 사용자 = 판정 아님
    assert next(x for x in d["results"] if x["id"] == "8")["status"] == "BLOCKED"  # 자격 증명 조회 안 함
    assert next(x for x in d["results"] if x["id"] == "C4")["status"] == "BLOCKED"
    blob = out + json.dumps(d, ensure_ascii=False)
    assert not re.search(r"(ghp_|github_pat_|gho_|sk-ant-|password=|token=)[A-Za-z0-9_]{6,}", blob)
    for name in ("GITHUB_PERSONAL_ACCESS_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        v = os.environ.get(name)
        if v and len(v) >= 8:
            assert v not in blob                                                  # 값은 어디에도 없어야 한다
    for f in (ROOT / ".claude" / "state" / "stage1").glob(files[0].name):        # 시험이 만든 kit 사본 정리
        f.unlink()


def _run(tmp_path, extra_env=None, kit=None, extra=None):
    env = dict(os.environ, **(extra_env or {}))
    args = [PS, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT), "-OutDir", str(tmp_path)]
    if kit:
        args += ["-Kit", str(kit)]
    args += extra or []
    subprocess.run(args, capture_output=True, timeout=120, env=env)
    f = sorted(tmp_path.glob("stage1-isolation-*.json"))[-1]
    d = json.loads(f.read_text(encoding="utf-8-sig"))
    for c in (ROOT / ".claude" / "state" / "stage1").glob(f.name):
        c.unlink()
    return {x["id"]: x for x in d["results"]}


def test_other_owner_repo_still_read_not_false_pass(tmp_path):
    # orca-agent 실행 = kit 소유자 다름 → git dubious ownership (exit 128). 오류를 버리면 원격 0줄 = 거짓 PASS 였다 (2026-11-09).
    r = _run(tmp_path, {"GIT_TEST_ASSUME_DIFFERENT_OWNER": "1"})
    assert r["14"]["status"] == "PASS" and "원격 0줄" not in r["14"]["evidence"], r["14"]
    assert re.search(r"원격 [1-9]\d*줄", r["14"]["evidence"]), r["14"]


def test_broker_absent_is_blocked_and_token_bytes_counted(tmp_path):
    """S4 이후 기준 (§69): Broker 폴더가 없으면 5r·5w·5g·5h = BLOCKED (NA 로 통과 X) · kit DB 토큰 원시 바이트 검사."""
    kit = tmp_path / "kit"
    (kit / ".claude" / "state").mkdir(parents=True)
    (kit / ".claude" / "state" / "orca.db").write_bytes(b"x" * 100 + ("ghp_" + "A1b" * 12).encode() + b"y")
    (kit / ".claude" / "state" / "sessions.db").write_bytes(b"clean")
    out = tmp_path / "out"
    out.mkdir()
    r = _run(out, {"GIT_CEILING_DIRECTORIES": str(tmp_path)}, kit=kit, extra=["-Broker", str(tmp_path / "no-broker")])
    assert r["5"]["status"] == "FAIL" and r["5s"]["status"] == "PASS"
    assert all(r[i]["status"] == "BLOCKED" for i in ("5r", "5w", "5g", "5h")), [r[i] for i in ("5r", "5w", "5g", "5h")]


def test_unreadable_repo_is_blocked_not_pass(tmp_path):
    kit = tmp_path / "not-a-repo"
    kit.mkdir()
    out = tmp_path / "out"
    out.mkdir()
    r = _run(out, {"GIT_CEILING_DIRECTORIES": str(tmp_path)}, kit=kit)
    assert r["13"]["status"] == "BLOCKED" and r["14"]["status"] == "BLOCKED", (r["13"], r["14"])
