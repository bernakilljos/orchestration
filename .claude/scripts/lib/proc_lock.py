"""프로세스 생존·식별·OS 파일 잠금 공용 (정본 · 2026-11-26 R375 7차 검토).

같은 일을 하던 세 곳(ai-collab-report._pid_alive · auto-save-next-actions._pid_alive · own-cleanup._os_lock)을 하나로 모음.
- os_lock(fd): 비차단 배타 잠금 — 커널 잠금이라 주인이 죽으면 저절로 풀린다 (잠금 파일은 지우지 않는다).
- pid_alive(pid): Windows 는 OpenProcess 반환형을 HANDLE 로 명시 (기본 int 반환형은 64비트 핸들을 자를 수 있음 · 7차 검토).
- proc_start(pid): 프로세스 시작 시각 식별자 — 같은 pid 가 다른 프로세스로 재사용됐는지 가린다. 못 읽으면 "".
쓰는 쪽은 파일 경로로 불러 쓴다 (스크립트를 경로 지정으로 적재하는 시험·훅에서도 sys.path 와 무관하게 · sys.modules["_kit_proc_lock"] 공유).
"""
from __future__ import annotations

import os

_K: dict = {}


def _kernel32():
    if "k" not in _K:
        import ctypes
        import ctypes.wintypes as w
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.OpenProcess.restype = w.HANDLE
        k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        k.GetExitCodeProcess.restype = w.BOOL
        k.GetExitCodeProcess.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
        k.GetProcessTimes.restype = w.BOOL
        k.GetProcessTimes.argtypes = [w.HANDLE] + [ctypes.POINTER(w.FILETIME)] * 4
        k.CloseHandle.restype = w.BOOL
        k.CloseHandle.argtypes = [w.HANDLE]
        _K.update(k=k, ct=ctypes, w=w)
    return _K["k"], _K["ct"], _K["w"]


ALIVE, DEAD, UNKNOWN = "alive", "dead", "unknown"
_WIN_NO_PID = 87          # ERROR_INVALID_PARAMETER = 그런 pid 없음 (명확한 종료)
_WIN_DENIED = 5           # ERROR_ACCESS_DENIED = 존재함


def pid_state(pid) -> str:
    """이 PC 의 pid 상태 3분류 — ALIVE · DEAD(명확한 종료 증거) · UNKNOWN(확인 불가).
    R375 8차 검토 P0: 예전 pid_alive 는 OpenProcess 실패 중 접근 거부(5)만 생존으로, 그 밖의 모든 오류를 종료로 봐서
    «확인 못 함» 이 «죽었음» 으로 바뀌어 잠금 회수·중복 실행 쪽으로 기울 수 있었다. 종료는 «없는 pid(87)» · 종료 코드 · ESRCH 만."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return UNKNOWN
    if pid <= 0:
        return UNKNOWN
    if os.name == "nt":
        try:
            k, ct, w = _kernel32()
            h = k.OpenProcess(0x1000, False, pid)            # PROCESS_QUERY_LIMITED_INFORMATION
            if not h:
                err = ct.get_last_error()
                if err == _WIN_DENIED:
                    return ALIVE
                return DEAD if err == _WIN_NO_PID else UNKNOWN
            try:
                code = w.DWORD()
                if not k.GetExitCodeProcess(h, ct.byref(code)):
                    return UNKNOWN
                return ALIVE if code.value == 259 else DEAD  # STILL_ACTIVE (종료 코드 259 로 끝난 프로세스는 생존으로 = 보수적)
            finally:
                k.CloseHandle(h)
        except (OSError, AttributeError, ValueError):
            return UNKNOWN
    import errno
    try:
        os.kill(pid, 0)
        return ALIVE
    except PermissionError:
        return ALIVE
    except OSError as e:
        return DEAD if e.errno == errno.ESRCH else UNKNOWN


def pid_alive(pid: int, unknown: bool = True) -> bool:
    """이 PC 의 pid 가 살아 있나. 확인 자체가 안 되면 unknown 값 (기본 True = 살아 있다고 봄 → 회수·중복 실행 쪽으로 기울지 않음)."""
    s = pid_state(pid)
    return unknown if s == UNKNOWN else s == ALIVE


def proc_start(pid: int) -> str:
    """프로세스 시작 시각 식별자 (Windows = 생성 FILETIME · Linux = /proc 시작 틱 · 그 밖 psutil) · 못 읽으면 ""."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return ""
    if os.name == "nt":
        try:
            k, ct, w = _kernel32()
            h = k.OpenProcess(0x1000, False, pid)
            if not h:
                return ""
            try:
                t = [w.FILETIME() for _ in range(4)]
                if not k.GetProcessTimes(h, *[ct.byref(x) for x in t]):
                    return ""
                return str((t[0].dwHighDateTime << 32) | t[0].dwLowDateTime)
            finally:
                k.CloseHandle(h)
        except (OSError, AttributeError, ValueError):
            return ""
    try:
        with open(f"/proc/{pid}/stat", encoding="ascii", errors="replace") as f:
            return f.read().rsplit(")", 1)[1].split()[19]   # 22번째 필드 starttime
    except (OSError, IndexError):
        pass
    try:
        import psutil
        return str(psutil.Process(pid).create_time())
    except Exception:  # noqa: BLE001 — 없거나 못 읽음
        return ""


def os_lock(fd: int) -> bool:
    """비차단 배타 잠금 — 커널이 잡는 잠금이라 주인 프로세스가 죽으면 저절로 풀린다 (pid 판정·잠금 파일 삭제 불필요)."""
    try:
        if os.name == "nt":
            import msvcrt
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def try_lock(path) -> int | None:
    """잠금 파일을 열고(없으면 만듦 · 지우지 않음) 비차단 잠금 — 잡으면 fd, 다른 프로세스가 잡고 있으면 None."""
    try:
        os.makedirs(os.path.dirname(str(path)) or ".", exist_ok=True)
        fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o644)
    except OSError:
        return None
    if os_lock(fd):
        return fd
    os.close(fd)
    return None


def release(fd) -> None:
    """잠금 해제 + 닫기 (파일은 남긴다 · 닫기만 해도 OS 가 푼다)."""
    if fd is None:
        return
    try:
        if os.name == "nt":
            import msvcrt
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    except OSError:
        pass
    try:
        os.close(fd)
    except OSError:
        pass

