"""aggregate-rule-adherence.sh 이식 — 룰 위반 지수 집계 (statusline 이 읽는 rule-adherence.json).

원본은 매 프롬프트 python 을 백그라운드로 띄우고 스크립트 안에서 TTL(10분) 을 확인했다.
여기서는 TTL 을 먼저 in-process 로 확인 — 신선하면 아무것도 안 한다. 만료 시에만 집계를 in-process 실행.
"""
from __future__ import annotations

import os
import time

from _common import load_script

TTL = 600  # aggregate-rule-adherence.py 의 TTL 과 동일


def run(ctx):
    if not ctx.has_plugins():
        return None
    out = ctx.root / ".claude" / "state" / "rule-adherence.json"
    if out.exists() and time.time() - out.stat().st_mtime < TTL and os.environ.get("FORCE") != "1":
        return None
    mod = load_script("aggregate-rule-adherence")
    if mod is None:
        return None
    mod.main()
    return None
