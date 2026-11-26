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
    for n in ("kit-merge-20261126-120000", "kit-merge-20261126-120000-2"):
        (root / n).mkdir()
        (root / n / m._PRUNABLE).write_text("x", encoding="utf-8")          # kit 소유 판만 든 백업 (정리 가능)
    m._prune_backups(tmp_path / "t", keep=1)
    assert (outside / "keep.txt").exists()                     # 정션 안으로 들어가 지우지 않음
    assert sorted(p.name for p in root.iterdir()) == ["kit-merge-20260101-000000", "kit-merge-20261126-120000-2"]


# ---- R375 7차 검토 P0 전파: 사용자 내용 백업 보존 · 쓰기 직전 재확인 · 대상 잠금 · 3.11 정션 ----
def _owned_target(m, tgt):
    """대상 파일을 «kit 가 마지막으로 써 넣은 판» 으로 기록 (stale-kit 경로 · 갱신 대상)."""
    import json
    mp = tgt / ".claude" / "state" / "kit-merge-manifest.json"
    mp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text(json.dumps({REL: m.md5(m.norm((tgt / REL).read_bytes()))}), encoding="utf-8")


def test_prune_keeps_backups_with_user_content(tmp_path):
    """이름이 맞아도 정리 가능 표시가 없는 백업(3-way 병합 전 대상본·settings 등)은 지우지 않는다."""
    m = _load()
    root = tmp_path / "t" / ".claude" / "backups"
    for n in ("kit-merge-20261101-000000", "kit-merge-20261102-000000", "kit-merge-20261103-000000"):
        (root / n).mkdir(parents=True)
        (root / n / "user.md").write_text("사용자 수정본", encoding="utf-8")
    for n in ("kit-merge-20261101-000000", "kit-merge-20261102-000000"):     # 표시 = kit 소유 판만 (정리 가능)
        (root / n / m._PRUNABLE).write_text("x", encoding="utf-8")
    m._prune_backups(tmp_path / "t", keep=1)
    left = sorted(p.name for p in root.iterdir())
    # 표시된 것 중 최신 1개(02)만 남기고 01 정리 · 표시 없는 사용자 내용 백업(03)은 가장 최신이어도 보존 대상 그대로
    assert left == ["kit-merge-20261102-000000", "kit-merge-20261103-000000"]


def test_mark_prunable_only_for_kit_owned_files(tmp_path):
    m = _load()
    b1, b2 = tmp_path / "b1", tmp_path / "b2"
    (b1 / ".claude/rules").mkdir(parents=True)
    (b1 / REL).write_text("kit 판", encoding="utf-8")
    m._mark_prunable(b1, {REL})
    assert (b1 / m._PRUNABLE).exists()
    (b2 / ".claude/rules").mkdir(parents=True)
    (b2 / REL).write_text("kit 판", encoding="utf-8")
    (b2 / ".claude/settings.json").write_text("{}", encoding="utf-8")        # 사용자 settings 원본
    m._mark_prunable(b2, {REL})
    assert not (b2 / m._PRUNABLE).exists()


def test_target_changed_between_check_and_write_is_held(env, monkeypatch):
    """확인(소유 판정·백업)한 뒤 쓰기 직전에 대상이 바뀌면 덮지 않고 보류 (rc=1 · 사용자 편집 보존)."""
    m, kit, tgt, run = env
    _owned_target(m, tgt)
    real = m.shutil.copy2

    def edit_after_backup(src, dst, *a, **k):
        r = real(src, dst, *a, **k)
        if "kit-merge-" in str(dst):
            (tgt / REL).write_text("방금 사용자가 고침\n", encoding="utf-8")   # 백업 직후 다른 세션 편집
        return r
    monkeypatch.setattr(m.shutil, "copy2", edit_after_backup)
    assert run("--apply") == 1
    assert (tgt / REL).read_text(encoding="utf-8") == "방금 사용자가 고침\n"


def test_owned_target_still_updates_atomically(env):
    m, kit, tgt, run = env
    _owned_target(m, tgt)
    assert run("--apply") == 0
    assert (tgt / REL).read_text(encoding="utf-8") == "kit 판\n"
    assert not list((tgt / ".claude" / "rules").glob(".*.tmp"))              # 임시 파일 잔여 없음


def test_concurrent_apply_on_same_target_is_skipped(env):
    """같은 대상에 다른 전파가 잠금을 쥐고 있으면 건너뜀 (rc=2 · 대상 변경 없음)."""
    import subprocess as sp
    m, kit, tgt, run = env
    _owned_target(m, tgt)
    lock = m._target_lock_path(tgt)                                          # 잠금은 kit 쪽 상태 폴더 (대상에 파일 X)
    lock.parent.mkdir(parents=True, exist_ok=True)
    holder = sp.Popen([sys.executable, "-c",
                       "import importlib.util as u,sys,time;"
                       "s=u.spec_from_file_location('p',sys.argv[1]);m=u.module_from_spec(s);s.loader.exec_module(m);"
                       "fd=m.try_lock(sys.argv[2]);print('L' if fd is not None else 'X',flush=True);time.sleep(30)",
                       str(_P.parent / "lib" / "proc_lock.py"), str(lock)], stdout=sp.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "L"
        assert run("--apply") == 2
        assert (tgt / REL).read_text(encoding="utf-8") == "대상 수정본 1\n"
    finally:
        holder.kill()
        holder.wait()
    assert run("--apply") == 0                                                 # 잠금이 풀리면 정상 진행


def test_isjunction_fallback_without_os_path_isjunction(tmp_path, monkeypatch):
    """3.11 처럼 os.path.isjunction 이 없으면 reparse point 속성으로 판정 · 판정 실패 = 정션으로 보고 지우지 않음."""
    m = _load()
    if os.name != "nt":
        pytest.skip("정션은 Windows 전용")
    import _winapi
    outside = tmp_path / "out"
    outside.mkdir()
    j = tmp_path / "j"
    _winapi.CreateJunction(str(outside), str(j))
    monkeypatch.delattr(os.path, "isjunction", raising=False)
    assert m._isjunction(j) is True
    assert m._isjunction(tmp_path / "없는-경로") is True                       # lstat 실패 = 지우지 않는 쪽
    plain = tmp_path / "plain"
    plain.mkdir()
    assert m._isjunction(plain) is False
