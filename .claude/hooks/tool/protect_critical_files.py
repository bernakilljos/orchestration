"""protect-critical-files.sh 이식 — config.py · .env 등 핵심 파일 편집 차단 (exit 2)."""
from __future__ import annotations

from _common import Result, bash_field, bash_read


def run(ctx):
    inp = bash_read(ctx.raw)
    if '"file_path"' not in inp:
        return None
    f = bash_field(inp, "file_path")
    if not f:
        return None
    # JSON 의 \ 와 OS 의 \ 를 모두 / 로, 연속 / 압축
    norm = f.replace("\\\\", "/").replace("\\", "/")
    while "//" in norm:
        norm = norm.replace("//", "/")
    # 예외: .claude/settings*.json 은 Claude 본인이 관리
    if (norm.endswith("/.claude/settings.json") or norm.endswith("/.claude/settings.local.json")
            or norm in (".claude/settings.json", ".claude/settings.local.json")):
        return None
    base = norm[norm.rfind("/") + 1:]
    # 2026-11-08: 승인 상태 DB·Ledger 를 Write/Edit 로 직접 고치는 경로 (스크립트 경유만)
    if base in ("config.py", "settings.json", "main.py", ".env", ".env.local", "deploy-config.env",
                "orca.db", "sessions.db", "request-ledger.json"):
        return Result(2, "", "BLOCKED: %s is a protected file. Do not modify.\n" % base)
    return None
