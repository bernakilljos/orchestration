#!/usr/bin/env python
"""
auto-save-next-actions.py — Stop/SessionEnd hook: assistant 마지막 응답에서
"## Next Actions" / "다음 세션" / "이어서 할 일" 섹션 추출해 .claude/state/next-actions.md 저장.

왜:
- /clear 후 새 세션은 resume-last-24h.py 가 next-actions.md 를 systemMessage 로 주입.
- 하지만 이전 세션이 next-actions.md 를 안 적어두면 재개 X.
- 매 턴 끝에 자동 캡처 → 사용자가 /clear 해도 다음 세션이 바로 이어감.

대상 섹션 제목 (대소문 무관):
- "## Next Actions" / "### Next Actions"
- "## 다음 세션" / "## 다음에 할 일"
- "## 이어서 할 일" / "## 이어서"
- "## Phase <N>" 로 시작하는 미완료 리스트

규칙:
- 섹션 **없으면** next-actions.md 변경 X (기존 유지)
- 섹션 **있으면** overwrite (최신 응답 = 최신 계획)
- 빈 섹션 ("완료") 이면 next-actions.md 비우기
"""
from __future__ import annotations
import os
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
DB = ROOT / ".claude" / "state" / "orca.db"
OUT = ROOT / ".claude" / "state" / "next-actions.md"

PATTERN = re.compile(
    r"^(#{1,3})\s*(Next Actions?|다음\s*세션|다음에\s*할\s*일|이어서\s*할\s*일|이어서|Phase\s+\d+[^\n]*)[^\n]*\n(.+?)(?=\n#{1,3}\s|\Z)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)
EMPTY_MARKERS = re.compile(r"\b(완료|done|끝|empty|없음|비움|clear)\b", re.IGNORECASE)


def _latest_assistant_content() -> str | None:
    if not DB.exists():
        return None
    try:
        c = sqlite3.connect(DB)
        row = c.execute(
            "SELECT content FROM conversations WHERE role='assistant' "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()
    except Exception:
        return None
    return row[0] if row else None


def _extract_sections(text: str) -> str | None:
    """Return concatenated matching sections, or None if no match."""
    matches = []
    for m in PATTERN.finditer(text):
        heading_hashes = m.group(1)
        title = m.group(2).strip()
        body = m.group(3).strip()
        matches.append(f"{heading_hashes} {title}\n{body}")
    return "\n\n".join(matches) if matches else None


def main() -> int:
    content = _latest_assistant_content()
    if not content:
        return 0

    sections = _extract_sections(content)
    if sections is None:
        return 0  # no next-action section — keep existing file

    body = sections.strip()

    OUT.parent.mkdir(parents=True, exist_ok=True)

    if not body or EMPTY_MARKERS.search(body) and len(body) < 60:
        try:
            OUT.write_text("", encoding="utf-8")
        except Exception:
            pass
        return 0

    try:
        OUT.write_text(body + "\n", encoding="utf-8")
    except Exception as e:
        print(f"[auto-save-next-actions] write fail: {e}", file=sys.stderr)
        return 0

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[auto-save-next-actions] fatal: {e}", file=sys.stderr)
        sys.exit(0)
