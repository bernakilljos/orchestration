"""prevent-whitespace-png.sh 이식 — "$FILE" 인자 방식 (위와 동일). FILE 이 있으면 원본에 위임."""
from __future__ import annotations

import os

from _common import Spawn, ensure_dir, root_path


def run(ctx):
    ensure_dir(root_path(".claude", "logs"))
    f = os.environ.get("FILE", "")
    if not f:
        return None
    return Spawn(".claude/hooks/prevent-whitespace-png.sh", (f,))
