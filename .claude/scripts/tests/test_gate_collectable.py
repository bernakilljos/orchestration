"""11-15: 회귀 게이트가 'git ls-files *_test.py' 로 pytest 가 모으지 않는 실행 스크립트(tools/playwright_sidebar_test.py —
가져오면 바로 브라우저 로그인 후 sys.exit)까지 pytest 에 넘겨 'caught unexpected SystemExit' rc=3 → 게이트 blocked."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import independent_verifier as v  # noqa: E402


def _repo(tmp_path):
    def w(rel, txt):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(txt, encoding="utf-8")
    w("pytest.ini", "[pytest]\ntestpaths = tests\npython_files = test_*.py\n")
    w("tests/test_ok.py", "def test_a():\n    assert True\n")
    w("tools/run_sidebar_test.py", "import sys\nsys.exit(0)\n")
    w("tools/test_helper.py", "x = 1\n")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    v._COLLECT_CACHE.clear()
    return tmp_path


def test_only_pytest_collectable_files_are_selected(tmp_path):
    r = _repo(tmp_path)
    assert v._collectable(r, "tests/test_ok.py")
    assert not v._collectable(r, "tools/run_sidebar_test.py")   # 이름이 python_files 와 다름 + testpaths 밖
    assert not v._collectable(r, "tools/test_helper.py")        # 이름은 맞지만 testpaths 밖
    assert v._collectable(r, "web/a.test.ts")                    # pytest 대상이 아닌 시험은 건드리지 않는다
    sel = v.impact_selection(r, ["tests/test_ok.py", "tools/run_sidebar_test.py"])
    assert "tools/run_sidebar_test.py" not in sel["tests"]
