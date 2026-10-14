"""prevent-version-suffix.sh 이식 — "$FILE" 인자 방식 (위 prevent_emoji_in_code 와 동일한 사정)."""
from __future__ import annotations

import os

from _common import Spawn, ensure_dir, root_path


def run(ctx):
    ensure_dir(root_path(".claude", "logs"))
    f = os.environ.get("FILE", "")
    if not f:
        return None
    return Spawn(".claude/hooks/prevent-version-suffix.sh", (f,))
