"""Claude 플랜 사용률(세션·주간)이 90%+ 면 매 프롬프트 codex·gemini 위임 지시를 주입.

근거 2026-10-17 사용자 지시: «세션 90% 주간 90%면 codex도 시키고 95%이상이면 gemini도 시키자».
판정·임계·문구 정본: .claude/scripts/lib/usage_offload.py (여기선 불러 쓰기만).
level 0 (90% 미만·미측정) 이면 아무것도 안 넣는다.
"""
from __future__ import annotations

import sys

from _common import SCRIPTS_DIR


def run(ctx):
    lib = str(SCRIPTS_DIR / "lib")
    if lib not in sys.path:
        sys.path.insert(0, lib)
    from usage_offload import notice
    return notice() or None
