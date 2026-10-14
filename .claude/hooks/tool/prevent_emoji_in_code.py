"""prevent-emoji-in-code.sh 이식 — settings 가 "$FILE" 인자로 호출한다. $FILE 은 Claude Code 가 설정하지 않아
대부분 빈 문자열이므로 원본도 (로그 디렉터리 생성 외) 아무것도 안 한다. FILE 이 있으면 원본에 위임."""
from __future__ import annotations

import os

from _common import Spawn, ensure_dir, root_path


def run(ctx):
    ensure_dir(root_path(".claude", "logs"))
    f = os.environ.get("FILE", "")
    if not f:
        return None
    return Spawn(".claude/hooks/prevent-emoji-in-code.sh", (f,))
