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
    # R346 후속 4: pytest -r 은 기본값(fE)을 대체 — '-rs' 만 주면 FAILED·ERROR 요약 줄이 사라져 실패 시험 주석이 0건이 된다
    import re
    for line in wf.splitlines():
        if "ci-pytest-gate.sh" in line and not line.lstrip().startswith("#"):
            for m in re.findall(r"\s-r([A-Za-z]+)", line):
                assert "f" in m and "E" in m, line


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


@pytest.mark.skipif(not BASH, reason="bash 없음")
def test_failed_test_names_emitted_as_ci_annotations(tmp_path):
    """러너 전용 실패를 진단하려고 실패 시험 이름을 ::error:: 주석으로 낸다 (공개 API 로 보임) · 종료 코드는 그대로."""
    fake = tmp_path / "fake.py"
    # R346 후속 5: 러너 로그에 NUL 등 바이너리 바이트가 섞이면 grep 이 줄 대신 'Binary file … matches' 만 냄 (10331b98 Windows run 실측)
    fake.write_text("import sys\nsys.stdout.write('noise\\x00bin\\n')\nprint('FAILED tests/x.py::test_a - AssertionError')\n"
                    "print('ERROR tests/y.py')\nsys.exit(1)\n", encoding="utf-8")
    env = {**os.environ, "PYTEST_CMD": f"{Path(sys.executable).as_posix()} {fake.as_posix()}"}
    r = subprocess.run([BASH, GATE.as_posix()], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    assert r.returncode == 1
    assert "Binary file" not in r.stdout
    # R346 후속 6: 주석 10개 한도에 안 잘리게 실패 전체·러너 환경을 여러 줄 주석 1건으로 (한 줄 · %0A 줄바꿈)
    detail = [l for l in r.stdout.splitlines() if l.startswith("::notice title=pytest-detail 1::")]
    assert len(detail) == 1 and "[환경] bash=" in detail[0] and "%0AFAILED tests/x.py::test_a" in detail[0], r.stdout
    assert sum(l.startswith("::error title=pytest::") for l in r.stdout.splitlines()) <= 7
    assert "::error title=pytest::FAILED tests/x.py::test_a" in r.stdout and "::error title=pytest::ERROR tests/y.py" in r.stdout


@pytest.mark.skipif(not BASH, reason="bash 없음")
def test_detail_annotation_split_under_message_limit(tmp_path):
    """후속 7: 주석 메시지는 약 4KB 에서 잘림 → 3,500자 이하 조각 · 최대 8건 (실패가 많아도 앞부분은 남음)."""
    fake = tmp_path / "fake.py"
    fake.write_text("import sys\nfor i in range(300):\n    print(f'FAILED tests/t{i}.py::test_{i} - AssertionError ' + 'x' * 80)\n"
                    "    print('E   assert ' + 'y' * 120)\nsys.exit(1)\n", encoding="utf-8")
    env = {**os.environ, "PYTEST_CMD": f"{Path(sys.executable).as_posix()} {fake.as_posix()}"}
    r = subprocess.run([BASH, GATE.as_posix()], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    parts = [l for l in r.stdout.splitlines() if l.startswith("::notice title=pytest-detail ")]
    assert 2 <= len(parts) <= 8, len(parts)
    assert all(len(l.split("::", 2)[2]) <= 3700 for l in parts)
    assert "FAILED tests/t0.py::test_0" in parts[0] and r.returncode == 1
