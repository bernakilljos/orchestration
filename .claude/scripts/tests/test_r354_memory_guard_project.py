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


def _run(script: Path, home: Path, project_env=None, extra=None):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_PROJECT_DIR", "MEMORY_GUARD_ALLOW_FOREIGN_PROJECT")}
    env.update(extra or {})
    env["HOME"] = str(home)
    env["TMPDIR"] = str(home)   # 프로젝트 못 찾음 SKIP 기록이 실제 %TEMP% 에 쌓이지 않게
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


def test_valid_env_same_as_script_project_is_used(tmp_path):
    # R354 25차: 종전 '다른 유효 프로젝트 env 가 이김' 계약은 fail-safe 로 바뀜 (아래 25차 절) — 같은 프로젝트면 그대로 사용
    other = _project(tmp_path / "home" / "other")
    _data(other)
    rc, out, _ = _run(_place(other, ".claude/hooks"), tmp_path / "home", str(other))
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


# ── R354 23차 검토 P1: 실재하지만 프로젝트 표식이 없는 CLAUDE_PROJECT_DIR · 건너뜀과 통과 구분 ──
# 신뢰 계약: 이 훅은 kit 이 설치된 프로젝트의 .claude/settings*.json 에 등록돼 실행된다 →
#   프로젝트 표식 = .claude/settings.json 또는 .claude/settings.local.json.
#   표식 없는 환경변수 경로는 쓰지 않고 경고 후 스크립트 위치 기준 탐색 (그쪽도 없으면 건너뜀).
SKIP_MARK = "[SKIP]"
DONE_MARK = "점검 완료"


def test_env_dir_without_marker_is_not_trusted(tmp_path):
    proj = _project(tmp_path / "home" / "proj")
    _data(proj)
    stray = tmp_path / "home" / "stray"   # 실재 폴더 · 표식 없음 · 데이터만 있음
    _data(stray)
    (stray / "data" / "strategy_memory.json").write_text("{bad json", encoding="utf-8")
    rc, out, err = _run(_place(proj, "plugins/exec_orch/hooks"), tmp_path / "home", str(stray))
    assert rc == 0, out + err    # stray 를 읽었으면 JSON 손상으로 rc=2
    assert "CLAUDE_PROJECT_DIR" in err and "표식" in err
    assert READ_MARK in out and DONE_MARK in out


def test_env_dir_with_settings_local_only_is_accepted(tmp_path):
    here = _project(tmp_path / "home" / "here")
    other = tmp_path / "home" / "other"
    (other / ".claude").mkdir(parents=True)
    (other / ".claude" / "settings.local.json").write_text("{}", encoding="utf-8")
    _data(other)
    rc, out, err = _run(_place(other, ".claude/hooks"), tmp_path / "home", str(other))
    assert rc == 0 and READ_MARK in out and "표식" not in err


def test_relative_env_dir_resolves_from_cwd(tmp_path):
    home = tmp_path / "home"
    here = _project(home / "here")
    other = _project(home / "other")
    _data(other)
    rc, out, _ = _run(_place(other, ".claude/hooks"), home, "other")   # cwd = home
    assert rc == 0 and READ_MARK in out


def test_skip_is_distinguishable_from_pass(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    rc, out, err = _run(_place(home / "kit", "plugins/exec_orch/hooks"), home)
    assert rc == 0
    assert SKIP_MARK in out and DONE_MARK not in out


def test_project_without_strategy_file_is_skip_and_logged(tmp_path):
    proj = _project(tmp_path / "home" / "proj")
    rc, out, _ = _run(_place(proj, ".claude/hooks"), tmp_path / "home")
    assert rc == 0
    assert SKIP_MARK in out and DONE_MARK not in out
    log = proj / ".claude" / "logs" / "memory-guard.log"
    assert log.is_file() and "SKIP" in log.read_text(encoding="utf-8")


# ── R354 24차 검토: 식별 계약의 한계(P1) · SKIP 가시성(P2) ──
# 계약: 표식(.claude/settings*.json)은 '프로젝트 폴더다' 만 증명하고 '호출자가 의도한 프로젝트' 는 증명하지 않는다.
#   유효한 CLAUDE_PROJECT_DIR 은 Claude Code 가 훅 실행 때 넣는 값이라 그대로 우선한다 (선택 동작 불변).
#   대신 고른 프로젝트와 근거를 출력하고, 스크립트 위치로 찾은 프로젝트와 다르면 경고해 오대상을 관찰 가능하게 한다.
# 호출자: SessionStart async 훅 4곳(kit·template·IFRS·ICMAI 설정)뿐 — 종료 코드를 PASS 로 집계하는 코드 없음 (전수 검색).
#   → 종료 코드는 0 유지 (호환) · 기록 실패를 stderr·stdout 에 남긴다.
SRC_LABEL = "대상 프로젝트:"
MISMATCH = "스크립트 위치 프로젝트와 다름"


def test_selected_project_and_source_are_printed(tmp_path):
    proj = _project(tmp_path / "home" / "proj")
    _data(proj)
    rc, out, _ = _run(_place(proj, ".claude/hooks"), tmp_path / "home")
    assert rc == 0 and SRC_LABEL in out and "근거: 스크립트 위치" in out


def test_env_other_valid_project_is_used_but_mismatch_warned(tmp_path):
    # R354 25차: 다른 프로젝트 점검은 명시적 허용(MEMORY_GUARD_ALLOW_FOREIGN_PROJECT=1)일 때만 · 경고는 그대로
    here = _project(tmp_path / "home" / "here")
    _data(here)
    other = _project(tmp_path / "home" / "other")
    (other / "data").mkdir()
    (other / "data" / "strategy_memory.json").write_text('[{"id":"o1"},{"id":"o2"}]', encoding="utf-8")
    rc, out, err = _run(_place(here, "plugins/exec_orch/hooks"), tmp_path / "home", str(other),
                        {"MEMORY_GUARD_ALLOW_FOREIGN_PROJECT": "1"})
    assert rc == 0
    assert "전략 수: 2개" in out          # 계약대로 env 프로젝트(other) 데이터를 읽음
    assert "근거: CLAUDE_PROJECT_DIR" in out
    assert MISMATCH in err               # 오대상 가능성을 숨기지 않음


def test_nested_install_env_outer_is_skipped(tmp_path):
    # R354 25차: 중첩 설치에서 env=outer · 스크립트=inner → 기본은 어느 쪽도 읽지 않고 SKIP (오대상 차단)
    outer = _project(tmp_path / "home" / "outer")
    _data(outer)
    inner = _project(outer / "inner")
    rc, out, err = _run(_place(inner, ".claude/hooks"), tmp_path / "home", str(outer))
    assert rc == 0 and READ_MARK not in out and SKIP_MARK in out and MISMATCH in err


def test_same_project_via_env_no_warning(tmp_path):
    proj = _project(tmp_path / "home" / "proj")
    _data(proj)
    rc, out, err = _run(_place(proj, "plugins/exec_orch/hooks"), tmp_path / "home", str(proj))
    assert rc == 0 and READ_MARK in out and MISMATCH not in err


def _dir_link(target: Path, link: Path) -> None:
    """디렉터리 링크 — symlink 권한이 없으면(Windows WinError 1314) 관리자 권한이 필요 없는 junction 으로 (R354 26차)."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except (OSError, NotImplementedError) as e:
        err = e
    if os.name == "nt":
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
        if r.returncode == 0:
            return
    pytest.skip(f"디렉터리 링크 생성 불가 (SKIP · 통과 아님): {err}")


def test_symlinked_env_same_project_no_warning(tmp_path):
    proj = _project(tmp_path / "home" / "proj")
    _data(proj)
    link = tmp_path / "home" / "link"
    _dir_link(proj, link)
    rc, out, err = _run(_place(proj, ".claude/hooks"), tmp_path / "home", str(link))
    assert rc == 0 and READ_MARK in out and MISMATCH not in err


def test_skip_log_write_failure_is_visible(tmp_path):
    proj = _project(tmp_path / "home" / "proj")
    (proj / ".claude" / "logs").write_text("not a dir", encoding="utf-8")   # 기록 폴더 생성 실패 유도
    rc, out, err = _run(_place(proj, ".claude/hooks"), tmp_path / "home")
    assert rc == 0                       # 호환: 종료 코드 불변
    assert SKIP_MARK in out and DONE_MARK not in out
    assert "기록 실패" in err and "기록 실패" in out


def test_drive_path_fallback_has_backreference():
    body = SRC.read_bytes()
    assert b"\x01" not in body           # sed 치환의 \1 이 제어문자로 깨지면 cygpath 없는 환경에서 경로가 망가짐
    assert rb"|\1:/|" in body


# ── R354 25차 검토 P1: 오대상 방지 계약 (경고 → 기본 차단 + 명시적 허용) ──
# provenance: 등록 명령은 4곳 모두 `bash "$CLAUDE_PROJECT_DIR/plugins/exec_orch/hooks/memory_guard.sh"` →
#   정상 실행에서 스크립트는 항상 CLAUDE_PROJECT_DIR 안에 있다 (= 실행 경로가 대상 증명).
#   공식 문서: CLAUDE_PROJECT_DIR = "the project root where the session started" (code.claude.com/docs/en/hooks).
#   그러므로 env 프로젝트와 스크립트 위치 프로젝트가 다르면(또는 스크립트 주변에 프로젝트가 없으면) 출처를 증명할 수 없어
#   기본은 SKIP · 다른 프로젝트를 일부러 점검할 때만 MEMORY_GUARD_ALLOW_FOREIGN_PROJECT=1.
ALLOW = {"MEMORY_GUARD_ALLOW_FOREIGN_PROJECT": "1"}


def test_foreign_env_project_is_skipped_by_default(tmp_path):
    here = _project(tmp_path / "home" / "here")
    other = _project(tmp_path / "home" / "other")
    _data(other)
    rc, out, err = _run(_place(here, ".claude/hooks"), tmp_path / "home", str(other))
    assert rc == 0
    assert READ_MARK not in out and SKIP_MARK in out and DONE_MARK not in out
    assert MISMATCH in err
    log = here / ".claude" / "logs" / "memory-guard.log"   # 기록은 스크립트 자신의 프로젝트에 (env 쪽에 쓰지 않음)
    assert log.is_file() and not (other / ".claude" / "logs").exists()


def test_script_outside_project_with_env_is_skipped(tmp_path):
    home = tmp_path / "home"
    other = _project(home / "other")
    _data(other)
    rc, out, err = _run(_place(home / "loose", "hooks"), home, str(other))
    assert rc == 0 and READ_MARK not in out and SKIP_MARK in out


def test_script_outside_project_with_env_allowed(tmp_path):
    home = tmp_path / "home"
    other = _project(home / "other")
    _data(other)
    rc, out, _ = _run(_place(home / "loose", "hooks"), home, str(other), ALLOW)
    assert rc == 0 and READ_MARK in out and "명시적 허용" in out


# ── R354 25차 검토 P2: 등록·소비자 증거 (저장소 안 2곳은 시험 · IFRS/ICMAI 는 보고서에 읽기 전용 실측) ──
REG_CMD = 'bash "$CLAUDE_PROJECT_DIR/plugins/exec_orch/hooks/memory_guard.sh"'


@pytest.mark.parametrize("rel", [".claude/settings.json", "setup/templates/settings.template.json"])
def test_registration_is_async_sessionstart_inside_project(rel):
    import json
    cfg = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    found = [(ev, h) for ev, groups in cfg.get("hooks", {}).items() for g in groups
             for h in g.get("hooks", []) if "memory_guard" in h.get("command", "")]
    assert len(found) == 1
    ev, h = found[0]
    assert ev == "SessionStart" and h.get("async") is True and h["command"] == REG_CMD


def test_no_consumer_aggregates_guard_output():
    # 출력·기록(memory-guard.log)을 읽어 PASS 로 집계하는 소비자가 생기면 이 시험이 먼저 알린다
    hits = []
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True,
                             encoding="utf-8", timeout=60).stdout.splitlines()
    for rel in tracked:
        f = ROOT / rel
        if f.suffix not in (".py", ".sh", ".ps1", ".bat", ".js") or not f.is_file():
            continue
        if rel.startswith((".git/", ".repair-sandbox/", ".ai-collab/", "node_modules/")) or "/logs/" in rel                 or rel.endswith("test_r354_memory_guard_project.py") or rel.endswith("memory_guard.sh"):
            continue
        try:
            t = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "memory-guard.log" in t or "MEMORY-GUARD" in t:
            hits.append(rel)
    assert hits == []


# ── R354 26차: 링크로 다른 프로젝트를 가리키는 env 도 실제 경로로 판정해 차단 ──
def test_linked_env_to_foreign_project_is_skipped(tmp_path):
    here = _project(tmp_path / "home" / "here")
    other = _project(tmp_path / "home" / "other")
    _data(other)
    link = tmp_path / "home" / "here-alias"   # 이름은 here 처럼 보이지만 실제는 other
    _dir_link(other, link)
    rc, out, err = _run(_place(here, ".claude/hooks"), tmp_path / "home", str(link))
    assert rc == 0 and READ_MARK not in out and SKIP_MARK in out and MISMATCH in err
