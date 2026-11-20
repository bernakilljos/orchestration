"""R350 커밋 직전 누락 발견 → 회귀 게이트 반복 실행 근절 (격리 저장소 · 운영 저장소 변경 없음).

세션 실측(2026-11-20): plugin.json 의 core_skill 참조만 고쳤는데 커밋 훅이 marketplace.json 을 요구 → 버전을 억지로 올림 →
JSON(코드 확장자) 이 바뀌어 게이트 stale → 재실행(메모리 보류 포함 3회). 두 원인:
  ① 동반 파일 검사가 커밋 순간에만 돌아 비싼 게이트 '뒤' 에 발견됨 → 게이트가 시험 전에 같은 훅을 미리보기로 불러 한 번에 알림
  ② manifest 가 조금만 바뀌어도 marketplace 요구 → 스테이징된 manifest·marketplace 를 대조해 실제로 어긋날 때만 요구
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / ".claude" / "hooks" / "pre-commit-full-check.sh"
sys.path.insert(0, str(ROOT / ".claude" / "scripts" / "lib"))
import independent_verifier as iv  # noqa: E402

BASH = shutil.which("bash")
pytestmark = pytest.mark.skipif(not BASH, reason="bash 없음 (훅 실행 불가)")


def _git(cwd, *a):
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=str(cwd), check=True, capture_output=True)


def _write_json(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _repo(tmp_path):
    r = tmp_path / "repo"
    (r / ".claude" / "hooks").mkdir(parents=True)
    shutil.copy(HOOK, r / ".claude" / "hooks" / HOOK.name)
    (r / ".claude" / "scripts" / "lib").mkdir(parents=True)
    (r / ".claude" / "scripts" / "lib" / "independent_verifier.py").write_text("# placeholder\n", encoding="utf-8")
    _write_json(r / "plugins" / "alpha" / "plugin.json", {"name": "alpha", "version": "1.0", "skills": ["s1", "s2"]})
    _write_json(r / ".claude-plugin" / "marketplace.json", {"plugins": [{"name": "alpha", "version": "1.0"}]})
    (r / "guide.txt").write_text("guide\n", encoding="utf-8")
    _git(r, "init", "-q")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "init")
    return r


def _missing(r):
    return iv.staging_preflight(r)


def test_manifest_edit_without_version_change_needs_no_marketplace(tmp_path):
    r = _repo(tmp_path)
    _write_json(r / "plugins" / "alpha" / "plugin.json", {"name": "alpha", "version": "1.0", "skills": ["s2"]})
    (r / "guide.txt").write_text("guide\nfix\n", encoding="utf-8")
    _git(r, "add", "-A")
    assert _missing(r) == []                      # 종전: 무조건 marketplace 요구 → 억지 버전 올림


def test_version_mismatch_and_unregistered_listed_at_once(tmp_path):
    r = _repo(tmp_path)
    _write_json(r / "plugins" / "alpha" / "plugin.json", {"name": "alpha", "version": "1.1", "skills": ["s1"]})
    _write_json(r / "plugins" / "beta" / "plugin.json", {"name": "beta", "version": "0.1"})
    _git(r, "add", "-A")                          # guide.txt 도 안 바꿈 → 누락 2종을 한 번에
    got = _missing(r)
    assert any(m.startswith("guide.txt") for m in got), got
    mp = [m for m in got if "marketplace.json" in m]
    assert len(mp) == 1 and "alpha" in mp[0] and "1.1" in mp[0] and "beta" in mp[0] and "미등록" in mp[0], got


def test_synced_marketplace_passes(tmp_path):
    r = _repo(tmp_path)
    _write_json(r / "plugins" / "alpha" / "plugin.json", {"name": "alpha", "version": "1.1"})
    _write_json(r / ".claude-plugin" / "marketplace.json", {"plugins": [{"name": "alpha", "version": "1.1"}]})
    (r / "guide.txt").write_text("guide\nbump\n", encoding="utf-8")
    _git(r, "add", "-A")
    assert _missing(r) == []


def test_unstaged_marketplace_fix_still_flagged(tmp_path):
    """작업 폴더에서만 고치고 stage 안 하면 여전히 누락 (스테이징 내용으로 비교)."""
    r = _repo(tmp_path)
    _write_json(r / "plugins" / "alpha" / "plugin.json", {"name": "alpha", "version": "2.0"})
    (r / "guide.txt").write_text("guide\nx\n", encoding="utf-8")
    _git(r, "add", "-A")
    _write_json(r / ".claude-plugin" / "marketplace.json", {"plugins": [{"name": "alpha", "version": "2.0"}]})
    assert any("marketplace.json" in m for m in _missing(r))


def test_gate_stops_before_tests_and_lists_all(tmp_path):
    r = _repo(tmp_path)
    (r / "engine").mkdir()
    (r / "engine" / "a.py").write_text("x = 2\n", encoding="utf-8")
    _write_json(r / "plugins" / "alpha" / "plugin.json", {"name": "alpha", "version": "1.1"})
    _git(r, "add", "-A")
    res = iv.regression_gate(r, timeout=60)
    assert res["status"] == "incomplete_staging", res
    assert res["tests"] == [] and len(res["missing"]) >= 2      # 시험 0건 실행 · guide + marketplace 한 번에
    stamp = json.loads((r / iv.REGRESSION_STAMP).read_text(encoding="utf-8"))
    assert stamp["status"] == "incomplete_staging"              # 커밋 훅은 이 기록을 통과로 보지 않는다



def test_cli_exit_code_incomplete_is_not_success(monkeypatch, capsys):
    """CLI 는 kit ROOT 에서 게이트를 돌리므로 하위 프로세스로 부르면 실제 저장소 전체 회귀가 뜬다 → 게이트만 대체해 종료 코드 확인."""
    monkeypatch.setattr(iv, "regression_gate", lambda *a, **k: {"status": "incomplete_staging", "missing": ["guide.txt"]})
    assert iv._cli_main(["x", "regression-gate"]) == 1           # 동반 파일 누락 = 미실행 (성공 0 아님)


def test_commit_hook_still_blocks_and_gate_check_unchanged(tmp_path):
    """미리보기 모드가 아닌 실제 커밋 훅은 그대로 차단 · 게이트 기록 검사(6번)도 그대로."""
    r = _repo(tmp_path)
    (r / "engine").mkdir()
    (r / "engine" / "a.py").write_text("x = 3\n", encoding="utf-8")
    (r / "guide.txt").write_text("guide\ny\n", encoding="utf-8")
    _git(r, "add", "-A")
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(r)}
    env.pop("PRECOMMIT_PREFLIGHT", None)
    p = subprocess.run([BASH, str(r / ".claude" / "hooks" / HOOK.name)], input=json.dumps({"tool_input": {"command": "git commit -m x"}}),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd=str(r))
    assert p.returncode == 2 and "회귀 방지 게이트" in p.stderr, p.stderr
    assert iv.staging_preflight(r) == []                         # 미리보기는 게이트 자신을 요구하지 않음
