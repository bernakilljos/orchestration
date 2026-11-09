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
    assert {"C1a", "C1b", "1", "2", "3", "4", "5", "5w", "6", "7", "8", "10b", "12", "13", "14", "C4"} <= ids
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
