"""R375 8차 검토 P0 — 공통 생존 계약 (lib/proc_lock.pid_state) · 정본을 못 불러올 때 호출부 fail closed.

- 예전 pid_alive: OpenProcess 실패 중 접근 거부(5)만 생존, 그 밖 모든 오류를 «종료» 로 봄 → 확인 불가가 회수·중복 실행 쪽으로 기울었다.
- 예전 merge-to-target: lib/proc_lock.py 가 없으면 대상 잠금 없이 --apply 진행 · own-cleanup·next-actions 는 예외가 그대로 올라감.
"""
import errno
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / ".claude" / "scripts"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def pl():
    m = _load(SCRIPTS / "lib" / "proc_lock.py", "proc_lock_r375i")
    yield m
    m._K.clear()


class _Fake:
    """kernel32 흉내 — OpenProcess 실패 코드·종료 코드를 지정."""

    def __init__(self, open_err=0, exit_code=259, exit_ok=True):
        self.open_err, self.exit_code, self.exit_ok = open_err, exit_code, exit_ok
        self.closed = 0

    def OpenProcess(self, *_a):
        return 0 if self.open_err else 1234

    def GetExitCodeProcess(self, _h, ref):
        ref._obj.value = self.exit_code
        return self.exit_ok

    def CloseHandle(self, _h):
        self.closed += 1
        return True


def _install_fake(pl, fake):
    import ctypes

    class _CT:
        @staticmethod
        def get_last_error():
            return fake.open_err

        byref = staticmethod(ctypes.byref)

    import ctypes.wintypes as w
    pl._K.update(k=fake, ct=_CT, w=w)


@pytest.mark.skipif(os.name != "nt", reason="Windows OpenProcess 분기")
def test_r375i_windows_open_errors_three_way(pl):
    """없는 pid(87) = DEAD · 접근 거부(5) = ALIVE · 그 밖 오류 = UNKNOWN (예전: 종료로 처리)."""
    for err, want in ((87, pl.DEAD), (5, pl.ALIVE), (6, pl.UNKNOWN), (1450, pl.UNKNOWN)):
        _install_fake(pl, _Fake(open_err=err))
        assert pl.pid_state(4321) == want, err
    _install_fake(pl, _Fake(open_err=6))
    assert pl.pid_alive(4321) is True                    # 확인 불가 = 기본은 살아 있다고 봄 (회수 X)
    assert pl.pid_alive(4321, unknown=False) is False    # 생존 증거가 필요한 쪽(heartbeat)은 False
    _install_fake(pl, _Fake(exit_ok=False))
    assert pl.pid_state(4321) == pl.UNKNOWN              # 종료 코드 못 읽음 = 모름
    f = _Fake(exit_code=0)
    _install_fake(pl, f)
    assert pl.pid_state(4321) == pl.DEAD and f.closed == 1   # 종료 코드 있음 = 종료 · 핸들 닫음
    _install_fake(pl, _Fake(exit_code=259))
    assert pl.pid_state(4321) == pl.ALIVE


@pytest.mark.skipif(os.name == "nt", reason="POSIX kill 분기")
def test_r375i_posix_kill_errors_three_way(pl, monkeypatch):
    def kill(code):
        def f(_p, _s):
            raise OSError(code, os.strerror(code))
        return f
    monkeypatch.setattr(os, "kill", kill(errno.ESRCH))
    assert pl.pid_state(4321) == pl.DEAD
    monkeypatch.setattr(os, "kill", kill(errno.EINVAL))
    assert pl.pid_state(4321) == pl.UNKNOWN and pl.pid_alive(4321) is True
    monkeypatch.setattr(os, "kill", lambda _p, _s: (_ for _ in ()).throw(PermissionError()))
    assert pl.pid_state(4321) == pl.ALIVE


def test_r375i_real_processes(pl):
    """실제 프로세스: 나 = ALIVE · 끝난 자식 = DEAD(또는 pid 재사용 시 ALIVE — DEAD 를 잘못 ALIVE 로 볼 순 있어도 반대는 X) · 잘못된 값 = UNKNOWN."""
    assert pl.pid_state(os.getpid()) == pl.ALIVE
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    assert pl.pid_state(p.pid) in (pl.DEAD, pl.ALIVE)
    assert pl.pid_state("x") == pl.UNKNOWN and pl.pid_state(0) == pl.UNKNOWN and pl.pid_state(-5) == pl.UNKNOWN


def _copy_without_lib(tmp_path: Path, name: str) -> Path:
    d = tmp_path / "kit" / ".claude" / "scripts"
    d.mkdir(parents=True)
    shutil.copy2(SCRIPTS / name, d / name)
    return d / name


def test_r375i_next_actions_missing_lib_never_reclaims(tmp_path):
    """next-actions: 정본을 못 불러오면 «살아 있다» (잠금 회수 X) — 예전엔 FileNotFoundError 가 올라와 훅이 죽었다."""
    sys.modules.pop("_kit_proc_lock", None)
    saved = sys.modules.pop("_kit_proc_lock", None)
    try:
        m = _load(_copy_without_lib(tmp_path, "auto-save-next-actions.py"), "asna_r375i")
        assert m._pid_alive(999999) is True
        lp = tmp_path / "x.lock"
        lp.write_text("999999 0", encoding="ascii")
        assert m._holder_dead(lp) is False
    finally:
        sys.modules.pop("_kit_proc_lock", None)
        if saved is not None:
            sys.modules["_kit_proc_lock"] = saved


def test_r375i_own_cleanup_missing_lib_takes_no_lock(tmp_path):
    """own-cleanup: 정본을 못 불러오면 잠금 실패 = 이번엔 아무것도 바꾸지 않음."""
    saved = sys.modules.pop("_kit_proc_lock", None)
    try:
        m = _load(_copy_without_lib(tmp_path, "own-cleanup.py"), "oc_r375i")
        fd = os.open(str(tmp_path / "l.lock"), os.O_RDWR | os.O_CREAT)
        try:
            assert m._os_lock(fd) is False
        finally:
            os.close(fd)
    finally:
        sys.modules.pop("_kit_proc_lock", None)
        if saved is not None:
            sys.modules["_kit_proc_lock"] = saved


def test_r375i_collab_missing_lib_no_liveness_no_refresh(tmp_path, monkeypatch):
    """ai-collab-report: 정본을 못 불러오면 생존 증거 없음(False) · 갱신을 띄우지도 쓰지도 않음."""
    saved = sys.modules.pop("_kit_proc_lock", None)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    try:
        m = _load(_copy_without_lib(tmp_path, "ai-collab-report.py"), "acr_r375i")
        assert m._pl() is None
        assert m._pid_alive(os.getpid()) is False
        assert m._pstart(os.getpid()) == ""
        spawned = []
        assert m._spawn_refresh(spawn=spawned.append) is False and spawned == []
        monkeypatch.setattr(m, "pending_lines", lambda *a, **k: pytest.fail("잠금 없이 갱신 실행"))
        assert m.cmd_refresh() == 0
    finally:
        sys.modules.pop("_kit_proc_lock", None)
        if saved is not None:
            sys.modules["_kit_proc_lock"] = saved


def test_r375i_merge_apply_refused_without_lock_module(tmp_path):
    """merge-to-target --apply: 잠금 정본이 없으면 대상 변경 0 · rc=2 (예전: 경고 후 잠금 없이 진행) · dry-run 은 그대로."""
    kit, tgt = tmp_path / "kit", tmp_path / "tgt"
    (kit / ".claude" / "hooks").mkdir(parents=True)
    script = _copy_without_lib(tmp_path, "merge-to-target.py")
    (kit / ".claude" / "hooks" / "x.sh").write_text("echo v1\n", encoding="utf-8")
    g = lambda *a: subprocess.run(["git", "-C", str(kit), *a], capture_output=True, text=True, timeout=60)
    g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
    g("add", "-A"); g("commit", "-q", "-m", "v1")
    (tgt / ".claude").mkdir(parents=True)
    run = lambda *a: subprocess.run([sys.executable, "-X", "utf8", str(script), str(tgt), *a],
                                    capture_output=True, text=True, encoding="utf-8", timeout=120)
    before = sorted(str(p.relative_to(tgt)) for p in tgt.rglob("*"))
    r = run("--apply")
    assert r.returncode == 2 and "proc_lock" in r.stdout, r.stdout + r.stderr
    assert sorted(str(p.relative_to(tgt)) for p in tgt.rglob("*")) == before        # 대상 변경 0
    assert run().returncode == 0                                                      # 미리보기는 가능
