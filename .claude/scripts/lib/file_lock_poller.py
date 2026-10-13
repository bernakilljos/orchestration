"""file_lock_poller.py ???뚯씪 ?좉툑 / ?몃? ?섏〈 fail ???먮룞 ?대쭅 ?쇱씠釉뚮윭由?
猷? .claude/rules/best-practices.md 짠 硫덉땄 諛⑹?
     feedback_no_user_stop.md

?ъ슜:
    from file_lock_poller import wait_unlock, exp_backoff, install_tool_if_missing
    wait_unlock(path, max_sec=60, interval=2)
    exp_backoff(max_retries=4, fn=lambda: my_call())
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, TypeVar

T = TypeVar("T")


def wait_unlock(path: Path | str, max_sec: int = 60, interval: int = 2) -> bool:
    """?뚯씪 ?좉툑 ?댁젣源뚯? ?대쭅. 諛섑솚: True=?由?/ False=timeout."""
    p = Path(path)
    elapsed = 0
    while elapsed < max_sec:
        try:
            # rename trick ??Windows ?뚯씪 ?좉툑 媛먯?
            test = p.with_suffix(p.suffix + ".lock-test")
            p.rename(test)
            test.rename(p)
            return True
        except (PermissionError, OSError):
            if elapsed == 0:
                print(f"[WAIT] {p.name} ?좉? ??{max_sec}珥??대쭅", file=sys.stderr)
            time.sleep(interval)
            elapsed += interval
    print(f"[FAIL] {p.name} ?좉툑 ???由?({max_sec}珥?", file=sys.stderr)
    return False


def exp_backoff(fn: Callable[[], T], max_retries: int = 4, base_delay: float = 2.0) -> T | None:
    """吏??backoff retry. fn() 媛 Exception ?섏?硫??ъ떆?? 諛섑솚: 留덉?留?寃곌낵 ?먮뒗 None."""
    delay = base_delay
    last_exc = None
    for i in range(max_retries):
        try:
            return fn()
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            last_exc = e
            if i < max_retries - 1:
                print(f"[RETRY {i+1}/{max_retries}] sleep {delay}s ??{e}", file=sys.stderr)
                time.sleep(delay)
                delay *= 2
    print(f"[FAIL] {max_retries} retries ???ㅽ뙣: {last_exc}", file=sys.stderr)
    return None


def install_tool_if_missing(tool: str, install_cmd: list[str]) -> bool:
    """?꾧뎄 PATH???놁쑝硫??먮룞 ?ㅼ튂 ???ы솗??"""
    if shutil.which(tool):
        return True
    print(f"[INSTALL] {tool} ?먮룞 ?ㅼ튂: {' '.join(install_cmd)}", file=sys.stderr)
    try:
        subprocess.run(install_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] {tool} ?ㅼ튂 ?ㅽ뙣: {e.stderr}", file=sys.stderr)
        return False
    return shutil.which(tool) is not None


def safe_write(path: Path | str, content: bytes | str, max_lock_wait: int = 60) -> bool:
    """?뚯씪 ?좉툑 ?대쭅 ???곌린. ?ㅽ뙣 = False."""
    p = Path(path)
    if p.exists() and not wait_unlock(p, max_sec=max_lock_wait):
        return False
    try:
        if isinstance(content, str):
            p.write_text(content, encoding="utf-8")
        else:
            p.write_bytes(content)
        return True
    except (PermissionError, OSError) as e:
        print(f"[FAIL] write {p}: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    print(__doc__)

