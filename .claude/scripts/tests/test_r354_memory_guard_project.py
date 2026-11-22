"""memory_guard.sh 프로젝트 폴더 판정 경계 (R354 22차 검토 P2 · 134351c2 후속).

검토 지적: 가장 가까운 상위 .claude/settings.json 을 고르는 방식은
  - 설정 파일을 못 찾으면 `../..` fallback 이 plugins/exec_orch/hooks 위치에서 plugins/ 를 가리키고
  - CLAUDE_PROJECT_DIR 가 없는 폴더를 가리키면 cd 실패 뒤에도 계속 진행한다 → 무언의 오대상 실행.
추가로 확인한 것: 위로 올라가다 사용자 홈의 ~/.claude/settings.json(전역 설정)을 프로젝트로 오인한다.
실제 스크립트를 임시 폴더 사본으로 실행한다 (운영 파일·운영 홈 불변).
판정 근거 = 어느 폴더의 data/strategy_memory.json 을 읽었는지 (그 폴더에만 파일을 둔다).
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks" / "prompt"))
from _common import bash_exe  # noqa: E402

BASH = bash_exe()
SRC = ROOT / "plugins" / "exec_orch" / "hooks" / "memory_guard.sh"
READ_MARK = "[INFO] 파일 크기"


def _project(base: Path) -> Path:
    (base / ".claude").mkdir(parents=True, exist_ok=True)
    (base / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
    return base


def _data(base: Path) -> None:
    (base / "data").mkdir(parents=True, exist_ok=True)
    (base / "data" / "strategy_memory.json").write_text("[]", encoding="utf-8")


def _place(base: Path, rel: str) -> Path:
    dst = base / rel / "memory_guard.sh"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC, dst)
    return dst


def _run(script: Path, home: Path, project_env=None):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    env["HOME"] = str(home)
    if project_env is not None:
        env["CLAUDE_PROJECT_DIR"] = project_env
    p = subprocess.run([BASH, str(script)], capture_output=True, timeout=60, env=env,
                       cwd=str(home))
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


@pytest.mark.parametrize("rel", [".claude/hooks", "plugins/exec_orch/hooks"])
def test_both_locations_find_same_project(tmp_path, rel):
    proj = _project(tmp_path / "home" / "proj")
    _data(proj)
    rc, out, _ = _run(_place(proj, rel), tmp_path / "home")
    assert rc == 0 and READ_MARK in out


def test_nested_project_picks_nearest(tmp_path):
    outer = _project(tmp_path / "home" / "outer")
    inner = _project(outer / "inner")
    _data(inner)   # outer 에는 파일 없음 → outer 를 고르면 '파일 없음'
    rc, out, _ = _run(_place(inner, "plugins/exec_orch/hooks"), tmp_path / "home")
    assert rc == 0 and READ_MARK in out


def test_valid_env_wins_over_script_location(tmp_path):
    here = _project(tmp_path / "home" / "here")
    other = _project(tmp_path / "home" / "other")
    _data(other)
    rc, out, _ = _run(_place(here, ".claude/hooks"), tmp_path / "home", str(other))
    assert rc == 0 and READ_MARK in out


def test_missing_env_dir_falls_back_with_warning(tmp_path):
    proj = _project(tmp_path / "home" / "proj")
    _data(proj)
    rc, out, err = _run(_place(proj, "plugins/exec_orch/hooks"), tmp_path / "home",
                        str(tmp_path / "home" / "no-such-dir"))
    assert rc == 0
    assert "CLAUDE_PROJECT_DIR" in err and "없음" in err
    assert READ_MARK in out   # 종전: cd 실패 뒤 없는 경로 기준으로 '파일 없음'


def test_no_settings_skips_instead_of_plugins_fallback(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    kit = home / "kit"   # .claude/settings.json 없음
    _data(kit / "plugins")   # 종전 ../.. fallback 이 가리키던 오대상
    rc, out, err = _run(_place(kit, "plugins/exec_orch/hooks"), home)
    assert rc == 0
    assert READ_MARK not in out
    assert "프로젝트 폴더를 찾지 못함" in err


def test_home_global_settings_is_not_a_project(tmp_path):
    home = _project(tmp_path / "home")   # ~/.claude/settings.json = 전역 설정
    _data(home)
    kit = home / "kit"
    rc, out, err = _run(_place(kit, ".claude/hooks"), home)
    assert rc == 0
    assert READ_MARK not in out   # 종전: 홈을 프로젝트로 오인해 홈의 파일을 읽음
    assert "프로젝트 폴더를 찾지 못함" in err
