"""plugins/exec_session_guard/hooks/periodic-snapshot.sh 이식 - 5분 간격 세션 스냅샷.

5분 게이트(대부분의 호출은 여기서 끝난다) 를 in-process 로 판정하고, 게이트를 통과했을 때만 (5분에 1번)
원본 스크립트에 위임해 스냅샷 재생성(session-snapshot-save.py) · Last Hook Record 기록을 그대로 수행한다.
"""
from __future__ import annotations

import os
import re
import time

from _common import Spawn, ensure_dir, project_guard, root_path

REL = "plugins/exec_session_guard/hooks/periodic-snapshot.sh"
INTERVAL = 300


def run(ctx):
    if not project_guard(ctx):
        return None
    cache_dir = root_path(".claude", "context-cache")
    try:
        os.makedirs(cache_dir, exist_ok=True)
    except OSError:
        return None
    last_file = os.path.join(cache_dir, ".last-periodic-snapshot")
    if os.path.isfile(last_file):
        try:
            with open(last_file, "rb") as f:
                last = re.sub(rb"\s+", b"", f.read()).decode("utf-8", "replace")
        except OSError:
            last = ""
        if last == "" or re.fullmatch(r"-?[0-9]+", last):
            elapsed = int(time.time()) - int(last or 0)
            if elapsed < INTERVAL:
                return None
        # 숫자가 아닌 값은 bash 산술 규칙이 복잡하므로 원본에 맡긴다
    # 2026-11-12 (R245): 원본을 기다리지 않고 분리 실행한다. 동기 Spawn 은 5초 상한에 걸리면 디스패처가
    #   하위 트리를 강제 종료해 스냅샷이 저장되지 않았다 (IFRS 77회 중 7회 5초 초과 · 최대 15.3초).
    #   결과는 파일(session-snapshot.md) 로만 남고 도구 실행을 막을 이유가 없다.
    if os.environ.get("PERIODIC_SNAPSHOT_SYNC") == "1":   # 시험·진단용: 예전 동기 방식
        return Spawn(REL)
    # 중복 실행 방지: 5분 시각은 분리된 원본이 나중에 쓰므로 그 사이 연속 호출이 여러 번 띄울 수 있다 →
    #   실행 표시 파일을 원자적으로 잡은 1회만 띄운다 (RUNNING_STALE_SEC 지나면 죽은 실행으로 보고 다시 잡음).
    running = os.path.join(cache_dir, ".periodic-snapshot.running")
    if not _claim(running):
        return None
    return _detach(root_path(*REL.split("/")), running, root_path(".claude", "logs", "periodic-snapshot.log"))


RUNNING_STALE_SEC = 120


def _claim(path) -> bool:
    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(int(time.time())).encode())
            os.close(fd)
            return True
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(path) <= RUNNING_STALE_SEC:
                    return False
                os.remove(path)
            except OSError:
                return False
        except OSError:
            return False
    return False


def _detach(path, running, log) -> None:
    """원본을 분리 실행하고, 끝나면 종료 코드·스냅샷 갱신 여부를 log 에 1줄 · 실행 표시 파일 해제."""
    import subprocess

    kw = {}
    if os.name == "nt":
        kw["creationflags"] = 0x08000000 | 0x00000008  # CREATE_NO_WINDOW | DETACHED_PROCESS
    else:
        kw["start_new_session"] = True
    snap = os.path.join(os.path.dirname(running), "session-snapshot.md")
    script = ('s="$1"; r="$2"; l="$3"; n="$4"; b=$(stat -c %Y "$n" 2>/dev/null || echo 0); bash "$s"; c=$?; '
              'a=$(stat -c %Y "$n" 2>/dev/null || echo 0); [ "$a" -gt "$b" ] && w=saved || w=unchanged; '
              'rm -f "$r"; mkdir -p "$(dirname "$l")"; echo "$(date "+%Y-%m-%dT%H:%M:%S") rc=$c snapshot=$w" >> "$l"')
    try:
        ensure_dir(os.path.dirname(log))
        subprocess.Popen(["bash", "-c", script, "periodic-snapshot", str(path), running, log, snap],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         close_fds=True, **kw)
    except Exception:  # noqa: BLE001
        try:
            os.remove(running)
        except OSError:
            pass
        return Spawn(REL)   # 분리 실행 실패 시 예전 방식으로 (스냅샷 누락보다 대기가 낫다)
    return None
