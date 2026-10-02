#!/usr/bin/env python
"""학습 스크립트 — orca.db + memory/ 분석 → user_style_profile.md 재구성.

주 1회 (일요일 04:30 Task Scheduler) 또는 수동 (--now) 실행.
분석 축:
  1. feedback_* 변경 감지 (신규·수정)
  2. orca.db conversations top 반복 패턴
  3. orca.db decisions 최근 결정
  4. orca.db problem_solutions 재사용 top
  5. detect-user-emotion.sh 매핑 증가 여부
결과:
  - user_style_profile.md 의 "축" 섹션 재가중
  - 신규 feedback 감지 시 "## 신규 (주간)" append
  - .claude/logs/user-style-updates.log 기록
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path


# Dynamic paths (hardcoding X · feedback_no_hardcoded_paths 준수)
ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / ".claude" / "state" / "orca.db"
MEMORY_DIR = Path.home() / ".claude" / "projects" / "C--pjt-orchestration-v1" / "memory"
PROFILE = MEMORY_DIR / "user_style_profile.md"
LOG = ROOT / ".claude" / "logs" / "user-style-updates.log"
WINDOW_DAYS = 7


def _log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def analyze_memory() -> dict:
    if not MEMORY_DIR.exists():
        return {"feedback_count": 0, "recent": []}
    cutoff = datetime.now() - timedelta(days=WINDOW_DAYS)
    feedback_files = list(MEMORY_DIR.glob("feedback_*.md"))
    recent = [
        f.name for f in feedback_files
        if datetime.fromtimestamp(f.stat().st_mtime) > cutoff
    ]
    return {
        "feedback_count": len(feedback_files),
        "recent": sorted(recent),
    }


def analyze_db() -> dict:
    if not DB.exists():
        return {"conversations": 0, "decisions": [], "solutions": []}
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()
    try:
        conv_n = c.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    except sqlite3.OperationalError:
        conv_n = 0
    try:
        decisions = c.execute(
            "SELECT title FROM decisions ORDER BY ts DESC LIMIT 5"
        ).fetchall()
    except sqlite3.OperationalError:
        decisions = []
    try:
        solutions = c.execute(
            "SELECT problem, category, reusable_score FROM problem_solutions "
            "WHERE reusable_score >= 7 ORDER BY reusable_score DESC, ts DESC LIMIT 10"
        ).fetchall()
    except sqlite3.OperationalError:
        solutions = []
    conn.close()
    return {
        "conversations": conv_n,
        "decisions": [d[0] for d in decisions],
        "solutions": [(s[0][:60], s[1], s[2]) for s in solutions],
    }


def rewrite_profile(memory: dict, db: dict) -> None:
    if not PROFILE.exists():
        _log("[WARN] user_style_profile.md 없음 · skip")
        return
    content = PROFILE.read_text(encoding="utf-8")

    # Append (or replace) "## 신규 (주간)" section
    today = datetime.now().strftime("%Y-%m-%d")
    marker = "## 신규 (주간 · 자동 재구성)"
    new_section_lines = [
        f"{marker}",
        f"",
        f"**갱신**: {today} (learn-style.py 주간 분석)",
        f"",
        f"| 지표 | 값 |",
        f"|---|---|",
        f"| 총 feedback | {memory['feedback_count']} |",
        f"| 최근 {WINDOW_DAYS}일 신규·수정 | {len(memory['recent'])} |",
        f"| 총 conversations | {db['conversations']} |",
        f"| 최근 decisions (top 5) | {len(db['decisions'])} |",
        f"| 재사용 solutions (score≥7) | {len(db['solutions'])} |",
        f"",
    ]
    if memory["recent"]:
        new_section_lines.append("**최근 변경 feedback**:")
        for name in memory["recent"][:10]:
            new_section_lines.append(f"- `{name}`")
        new_section_lines.append("")
    if db["decisions"]:
        new_section_lines.append("**최근 decisions**:")
        for d in db["decisions"]:
            new_section_lines.append(f"- {d[:80]}")
        new_section_lines.append("")
    if db["solutions"]:
        new_section_lines.append("**검증된 재사용 solutions** (score≥7):")
        for prob, cat, score in db["solutions"]:
            new_section_lines.append(f"- [{cat} · {score}] {prob}")
        new_section_lines.append("")

    new_section = "\n".join(new_section_lines)

    # Replace existing marker block (if present) or append
    if marker in content:
        head, _, _ = content.partition(marker)
        # keep content before marker, replace rest
        content = head.rstrip() + "\n\n" + new_section + "\n"
    else:
        content = content.rstrip() + "\n\n---\n\n" + new_section + "\n"

    PROFILE.write_text(content, encoding="utf-8")
    _log(
        f"profile 재구성 · feedback={memory['feedback_count']} "
        f"(recent={len(memory['recent'])}) · conv={db['conversations']} "
        f"· dec={len(db['decisions'])} · sol={len(db['solutions'])}"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", action="store_true", help="즉시 실행 (스케줄러 외)")
    parser.add_argument("--dry", action="store_true", help="분석만 · 쓰기 X")
    args = parser.parse_args()

    memory = analyze_memory()
    db = analyze_db()

    print(f"[memory] feedback_count={memory['feedback_count']} · recent={len(memory['recent'])}")
    print(f"[db] conversations={db['conversations']} · decisions={len(db['decisions'])} · solutions={len(db['solutions'])}")

    if args.dry:
        print("[DRY] skip write")
        return 0

    rewrite_profile(memory, db)
    print(f"[OK] profile updated · log: {LOG}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
