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
    return Spawn(REL)
