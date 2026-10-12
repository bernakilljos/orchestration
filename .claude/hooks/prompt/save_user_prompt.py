"""save-user-prompt.sh 이식 — 사용자 프롬프트를 orca.db.conversations 에 저장 (출력 없음).

원본의 에러 출력(stderr)은 .claude/logs/conversation-save.log 로 갔다 — 그대로 유지.
"""
from __future__ import annotations

import os

from _common import append_text, load_script


def run(ctx):
    root = ctx.root
    log = root / ".claude" / "logs" / "conversation-save.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    if not log.exists():  # 원본의 `>>"$LOG"` 는 출력이 없어도 파일을 만든다
        log.touch()

    if ctx.parse_error:
        append_text(log, "[parse error] %s\n" % ctx.parse_error)
        return None
    # 2026-09-19: 세션 id 는 훅 stdin 의 session_id 가 정본 — 단, 같은 프로세스의 다른 훅에 새지 않게 저장 동안만 설정
    sid = ctx.payload.get("session_id")
    prev = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if sid:
        os.environ["CLAUDE_CODE_SESSION_ID"] = sid
    try:
        p = ctx.field("user_prompt", "prompt")
        if not p:
            return None
        CL = load_script("lib/conversation_logger")
        CL.save_turn("user", p)
    except Exception as e:
        append_text(log, "[save error] %s\n" % e)
    finally:
        if sid:
            if prev is None:
                os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
            else:
                os.environ["CLAUDE_CODE_SESSION_ID"] = prev
    return None
