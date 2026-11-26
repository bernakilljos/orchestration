"""R375 7차 검토 (2026-11-25 · 전파 안전성) — merge-to-target 강제 교체의 복구 증거 보호.

격리: kit·대상 모두 tmp_path (운영 대상 IFRS·ICMAI 사용 X) · KIT·TREES 를 임시 kit 로 바꿔 --only 경로로 실행.
"""
import datetime as _dt
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

_P = Path(__file__).resolve().parents[1] / "merge-to-target.py"


def _load():
    spec = importlib.util.spec_from_file_location("merge_to_target_r375g", _P)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


REL = ".claude/rules/a.md"


def _git(cwd, *a):
    subprocess.run(["git", "-C", str(cwd), *a], check=True, capture_output=True)


@pytest.fixture
def env(tmp_path, monkeypatch):
    m = _load()
    kit, tgt = tmp_path / "kit", tmp_path / "tgt"
    (kit / ".claude" / "rules").mkdir(parents=True)
    (kit / REL).write_text("kit 판\n", encoding="utf-8")
    (tgt / ".claude" / "rules").mkdir(parents=True)
    (tgt / REL).write_text("대상 수정본 1\n", encoding="utf-8")
    _git(tgt, "init", "-q")
    _git(tgt, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    _git(tgt, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    monkeypatch.setattr(m, "KIT", kit)
    monkeypatch.setattr(m, "TREES", [".claude/rules"])
    monkeypatch.setattr(m, "three_way", lambda rel, db: None)
    monkeypatch.setattr(m, "_record_apply", lambda *a, **k: None)
    monkeypatch.setattr(m, "_retired_names", lambda: set(), raising=False)

    class _Fixed(_dt.datetime):                      # 같은 초에 두 번 전파
        @classmethod
        def now(cls, tz=None):
            return _dt.datetime(2026, 11, 26, 12, 0, 0)
    monkeypatch.setattr(m.datetime, "datetime", _Fixed)

    def run(*extra):
        monkeypatch.setattr(sys, "argv", ["merge-to-target.py", str(tgt), "--only", REL, *extra])
        return m.main()
    return m, kit, tgt, run


def _commit_target(tgt, text):
    (tgt / REL).write_text(text, encoding="utf-8")
    _git(tgt, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "edit")


def test_same_second_force_runs_keep_both_originals(env):
    m, kit, tgt, run = env
    assert run("--apply", "--force") == 0
    _commit_target(tgt, "대상 수정본 2\n")             # 사용자가 다시 고침 → 같은 초에 다시 강제 전파
    (kit / REL).write_text("kit 판 2\n", encoding="utf-8")
    assert run("--apply", "--force") == 0
    bk = sorted(p.name for p in (tgt / ".claude" / "backups").iterdir() if p.name.startswith("kit-force-"))
    assert bk == ["kit-force-20261126-120000", "kit-force-20261126-120000-2"]
    got = {(tgt / ".claude" / "backups" / b / REL).read_text(encoding="utf-8") for b in bk}
    assert got == {"대상 수정본 1\n", "대상 수정본 2\n"}       # 이전 원본(유일한 복구 증거)이 덮이지 않음


def test_bad_backup_copy_holds_force(env, monkeypatch):
    m, kit, tgt, run = env
    real = m.shutil.copy2

    def broken(src, dst, *a, **k):
        r = real(src, dst, *a, **k)
        if "kit-force-" in str(dst):
            Path(dst).write_bytes(b"partial")         # 부분 복사 모의
        return r
    monkeypatch.setattr(m.shutil, "copy2", broken)
    assert run("--apply", "--force") == 1             # 강제 보류 = 성공으로 숨기지 않음
    assert (tgt / REL).read_text(encoding="utf-8") == "대상 수정본 1\n"


def test_dirty_target_file_is_held_and_reported(env):
    m, kit, tgt, run = env
    (tgt / REL).write_text("미커밋 수정\n", encoding="utf-8")
    assert run("--apply", "--force") == 1
    assert (tgt / REL).read_text(encoding="utf-8") == "미커밋 수정\n"


def test_dry_run_creates_no_backup_dirs(env, capsys):
    m, kit, tgt, run = env
    assert run("--force") == 0
    assert not (tgt / ".claude" / "backups").exists()
    assert "강제 교체 원본 보존" not in capsys.readouterr().out
    assert (tgt / REL).read_text(encoding="utf-8") == "대상 수정본 1\n"


def test_all_ignores_cli_force(env, monkeypatch, tmp_path):
    m, kit, tgt, run = env
    st = kit / ".claude" / "state"
    st.mkdir(parents=True)
    (st / "merge-targets.txt").write_text(str(tgt) + "\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["merge-to-target.py", "--all", "--only", REL, "--apply", "--force"])
    m.main()
    assert (tgt / REL).read_text(encoding="utf-8") == "대상 수정본 1\n"   # --all 은 대상별 목록 없이는 강제 안 함


def test_prune_skips_junction_backup(tmp_path):
    m = _load()
    if not hasattr(os.path, "isjunction") or os.name != "nt":
        pytest.skip("정션은 Windows 전용")
    import _winapi
    root = tmp_path / "t" / ".claude" / "backups"
    root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("바깥", encoding="utf-8")
    _winapi.CreateJunction(str(outside), str(root / "kit-merge-20260101-000000"))
    (root / "kit-merge-20261126-120000").mkdir()
    (root / "kit-merge-20261126-120000-2").mkdir()
    m._prune_backups(tmp_path / "t", keep=1)
    assert (outside / "keep.txt").exists()                     # 정션 안으로 들어가 지우지 않음
    assert sorted(p.name for p in root.iterdir()) == ["kit-merge-20260101-000000", "kit-merge-20261126-120000-2"]
