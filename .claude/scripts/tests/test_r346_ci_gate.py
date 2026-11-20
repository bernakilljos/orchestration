"""R346 CI 가 실패를 숨기지 않는지 — 결함 주입: pytest 종료 코드 0·1·2·4·5 를 흉내 내 게이트 스크립트가 그대로 전파하는지.
워크플로우가 이 게이트를 쓰고 `|| echo`·`|| true` 로 pytest 결과를 덮지 않는지도 확인."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT / ".claude" / "scripts" / "ci-pytest-gate.sh"
BASH = shutil.which("bash")


@pytest.mark.skipif(not BASH, reason="bash 없음")
@pytest.mark.parametrize("code,word", [(0, "통과"), (1, "시험 실패"), (2, "실행 중단"), (4, "사용 오류"), (5, "0건")])
def test_exit_code_propagates(code, word, tmp_path):
    fake = tmp_path / "fake.py"
    fake.write_text(f"import sys\nsys.exit({code})\n", encoding="utf-8")
    py = Path(sys.executable).as_posix()
    env = {**os.environ, "PYTEST_CMD": f"{py} {fake.as_posix()}"}   # 공백 없는 경로 (따옴표를 넣으면 셸이 글자로 받음)
    r = subprocess.run([BASH, GATE.as_posix()], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    assert r.returncode == code and word in r.stdout, (r.returncode, r.stdout, r.stderr)


def test_workflow_uses_gate_and_does_not_mask_pytest():
    wf = (ROOT / ".github" / "workflows" / "test-matrix.yml").read_text(encoding="utf-8")
    assert "ci-pytest-gate.sh" in wf
    assert "No tests found" not in wf and "plugins/*/tests" not in wf
    for line in wf.splitlines():
        if "pytest" in line and "pip install" not in line and not line.lstrip().startswith("#"):   # 주석 속 옛 문구 인용 제외
            assert "|| true" not in line and "|| echo" not in line, line
    assert "validate-plugin-schema.py --strict || true" not in wf      # 스키마 검증은 필수


def test_init_schema_completes_db_that_only_has_schema_version(tmp_path, monkeypatch):
    """R346 후속: 새 clone 전체 시험에서 다른 모듈이 schema_version 만 먼저 만든 orca.db 를 init_schema 가 '초기화됨' 으로 보고
    tasks 를 만들지 않던 것 (Windows CI 필수 실패 4건 원인) — 임시 루트에서만 (운영 DB 미접촉)."""
    import importlib
    import sqlite3
    lib = ROOT / ".claude" / "scripts" / "lib"
    sys.path.insert(0, str(lib))
    (tmp_path / ".claude" / "scripts").mkdir(parents=True)
    monkeypatch.setenv("ORCHESTRATION_ROOT", str(tmp_path))
    import state_db
    importlib.reload(state_db)
    db = state_db.get_db_path()
    with sqlite3.connect(db) as c:
        c.execute("CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at INTEGER)")
        c.execute("INSERT INTO schema_version VALUES (1, 0)")
    state_db.init_schema()
    with sqlite3.connect(db) as c:
        have = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"tasks", "workers", "metrics", "quota", "budget", "session"} <= have, have
    assert str(db).startswith(str(tmp_path))
