"""suggest-command-from-context.sh 이식 — 최근 10 turn 패턴·임계 초과·재사용 해결책·외부 신호 기반 command 추천.

로직은 .claude/scripts/suggest-command-from-context.py (5분 TTL 캐시) 를 in-process 로 호출한다.
그 스크립트가 print 하던 JSON 만 가로채 additionalContext 를 꺼낸다 (모듈 전역 print 교체 — 전역 stdout 은 건드리지 않음).
캐시 만료 시 스크립트 내부에서 git status 를 1회 부른다 (5분에 최대 1회 · 원본 동일).
"""
from __future__ import annotations

import json

from _common import load_script


def run(ctx):
    if not ctx.has_plugins():
        return None
    mod = load_script("suggest-command-from-context")
    if mod is None:
        return None
    buf: list[str] = []
    mod.print = lambda *a, **k: buf.append(" ".join(str(x) for x in a))
    try:
        mod.main()
    finally:
        del mod.print
    if not buf:
        return None
    text = "\n".join(buf)
    try:
        return json.loads(text)["hookSpecificOutput"]["additionalContext"]
    except Exception:
        return text + "\n"
