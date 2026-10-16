#!/usr/bin/env python
"""
recurrence-tracker.py — 사용자 지시 재발 추적 + 자동 승격.

정의 (2026-10-16 사용자):
  재발률 = 이전에 이미 지시한 rule_id 중 다시 user 프롬프트에 등장한 비율
         = (total_occurrences >= 2 인 rule) / (전체 등록 rule)

쓰임:
  python recurrence-tracker.py record <rule_id> <category> [snippet]
  python recurrence-tracker.py stats
  python recurrence-tracker.py ensure

자동 승격 (사용자 지시):
  1회 → log 만 (recurrence_events)
  2회 → warn (promoted_level=1)
  3회 → CLAUDE.md 규칙 승격 후보 (.claude/state/rule-promotion-candidates.md)
  5회 → Hook 강제 차단 후보 (.claude/state/hook-enforcement-candidates.md)

OUT:
  orca.db.recurrence_rules + recurrence_events (SoT)
  .claude/state/rule-promotion-candidates.md
  .claude/state/hook-enforcement-candidates.md
"""
from __future__ import annotations
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
DB = ROOT / ".claude" / "state" / "orca.db"
PROMO_MD = ROOT / ".claude" / "state" / "rule-promotion-candidates.md"
ENFORCE_MD = ROOT / ".claude" / "state" / "hook-enforcement-candidates.md"

# 임계치 통일 (2026-10-16 사용자 지시)
CAUTION_PCT = 20   # 20% 미만 정상 · 20~40% 주의
DANGER_PCT = 40    # 40% 이상 위험
STALE_DAYS = 60    # 60일 비활동 rule 자동 archive (지표 수명 관리)


def _classify_status(pct: float) -> str:
    if pct < CAUTION_PCT:
        return "normal"
    if pct < DANGER_PCT:
        return "caution"
    return "danger"


def _trend_arrow(current: float, previous: float, deadband: float = 2.0) -> str:
    """현재 vs 과거 비교: ↓ (개선) · → (평탄) · ↑ (악화). deadband 안쪽은 → ."""
    if current < previous - deadband:
        return "↓"
    if current > previous + deadband:
        return "↑"
    return "→"


def ensure_schema() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS recurrence_rules (
      rule_id TEXT PRIMARY KEY,
      category TEXT,
      first_seen TIMESTAMP,
      last_seen TIMESTAMP,
      total_occurrences INTEGER DEFAULT 1,
      promoted_level INTEGER DEFAULT 0,
      description TEXT,
      archived INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS recurrence_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      rule_id TEXT NOT NULL,
      session_id TEXT,
      user_prompt_snippet TEXT,
      detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_rec_rule_time
      ON recurrence_events(rule_id, detected_at);
    CREATE INDEX IF NOT EXISTS idx_rec_rule_cat
      ON recurrence_rules(category, total_occurrences DESC);
    """)
    # 기존 테이블에 archived 컬럼 없으면 추가 (idempotent)
    try:
        cols = [r[1] for r in c.execute("PRAGMA table_info(recurrence_rules)").fetchall()]
        if "archived" not in cols:
            c.execute("ALTER TABLE recurrence_rules ADD COLUMN archived INTEGER DEFAULT 0")
    except Exception:
        pass
    c.commit()
    c.close()


def archive_stale() -> int:
    """last_seen 이 STALE_DAYS 일 이전인 rule 을 archived=1 로 표시 (집계 제외)."""
    ensure_schema()
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=STALE_DAYS)).isoformat()
    c = sqlite3.connect(DB)
    cur = c.execute(
        "UPDATE recurrence_rules SET archived=1 WHERE archived=0 AND last_seen < ?",
        (cutoff,),
    )
    n = cur.rowcount
    c.commit()
    c.close()
    return n


def _append_md(path: Path, line: str, header: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
    except Exception:
        existing = ""
    if line in existing:
        return
    if not existing:
        existing = header + "\n\n"
    path.write_text(existing + line + "\n", encoding="utf-8")


def _check_promotion(c: sqlite3.Connection, rule_id: str, total: int) -> int:
    """return new promoted_level"""
    row = c.execute(
        "SELECT category, promoted_level, description FROM recurrence_rules WHERE rule_id=?",
        (rule_id,),
    ).fetchone()
    if not row:
        return 0
    category, lvl, desc = row
    desc = desc or rule_id
    new_lvl = lvl or 0

    if total >= 5 and (lvl or 0) < 3:
        new_lvl = 3
        _append_md(
            ENFORCE_MD,
            f"- [{category}] **{rule_id}** · {total}회 · PreToolUse hook 강제 차단 후보 · {desc}",
            "# Hook 강제 차단 후보 (재발 5회+ 자동 승격)\n\n수동 리뷰 후 `.claude/hooks/tool/<name>.py` 추가.",
        )
    elif total >= 3 and (lvl or 0) < 2:
        new_lvl = 2
        _append_md(
            PROMO_MD,
            f"- [{category}] **{rule_id}** · {total}회 · CLAUDE.md § 7 승격 후보 · {desc}",
            "# CLAUDE.md 규칙 승격 후보 (재발 3회+ 자동 승격)\n\n수동 리뷰 후 CLAUDE.md § 7 또는 `.claude/rules/*.md` 추가.",
        )
    elif total >= 2 and (lvl or 0) < 1:
        new_lvl = 1

    return new_lvl


def record(rule_id: str, category: str = "misc", snippet: str = "", session_id: str = "") -> dict:
    ensure_schema()
    c = sqlite3.connect(DB)
    now = datetime.now().isoformat(timespec="seconds")

    row = c.execute(
        "SELECT total_occurrences, promoted_level FROM recurrence_rules WHERE rule_id=?",
        (rule_id,),
    ).fetchone()
    if row:
        total = (row[0] or 0) + 1
        c.execute(
            "UPDATE recurrence_rules SET total_occurrences=?, last_seen=? WHERE rule_id=?",
            (total, now, rule_id),
        )
    else:
        total = 1
        c.execute(
            "INSERT INTO recurrence_rules(rule_id, category, first_seen, last_seen, total_occurrences, description) "
            "VALUES (?,?,?,?,1,?)",
            (rule_id, category, now, now, snippet[:200] if snippet else rule_id),
        )

    c.execute(
        "INSERT INTO recurrence_events(rule_id, session_id, user_prompt_snippet) VALUES (?,?,?)",
        (rule_id, session_id, (snippet or "")[:300]),
    )

    new_lvl = _check_promotion(c, rule_id, total)
    if new_lvl:
        c.execute("UPDATE recurrence_rules SET promoted_level=? WHERE rule_id=?", (new_lvl, rule_id))

    c.commit()
    c.close()

    return {"rule_id": rule_id, "total": total, "promoted_level": new_lvl}


def _avg_hours_between(c, rule_id: str) -> float:
    evs = c.execute(
        "SELECT detected_at FROM recurrence_events WHERE rule_id=? ORDER BY detected_at ASC",
        (rule_id,),
    ).fetchall()
    if len(evs) < 2:
        return 0.0
    diffs = []
    for i in range(1, len(evs)):
        try:
            dt1 = datetime.fromisoformat(evs[i - 1][0])
            dt2 = datetime.fromisoformat(evs[i][0])
            diffs.append((dt2 - dt1).total_seconds() / 3600)
        except Exception:
            pass
    return round(sum(diffs) / len(diffs), 1) if diffs else 0.0


def _recur_rate_in_window(c, cat: str, days: int) -> float:
    """categorized recur rate in a window: rules with >=2 events whose last event is within window."""
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    rows = c.execute(
        "SELECT r.rule_id, r.total_occurrences FROM recurrence_rules r "
        "WHERE r.archived=0 AND r.category=? AND r.last_seen >= ?",
        (cat, cutoff),
    ).fetchall()
    if not rows:
        return 0.0
    n = len(rows)
    recurring = sum(1 for _, tot in rows if (tot or 0) >= 2)
    return round(recurring / n * 100, 1) if n else 0.0


def stats() -> dict:
    ensure_schema()
    # 지표 수명 관리: 매 stats 호출 시 stale 자동 archive
    archive_stale()
    c = sqlite3.connect(DB)
    rules = c.execute(
        "SELECT rule_id, category, total_occurrences, promoted_level, first_seen, last_seen, description "
        "FROM recurrence_rules WHERE archived=0 "
        "ORDER BY total_occurrences DESC, last_seen DESC"
    ).fetchall()

    out: dict = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_rules": len(rules),
        "thresholds": {"caution_pct": CAUTION_PCT, "danger_pct": DANGER_PCT, "stale_days": STALE_DAYS},
        "by_category": {},
        "top_recurring": [],
    }
    for rid, cat, tot, lvl, fs, ls, desc in rules:
        cat_key = cat or "misc"
        slot = out["by_category"].setdefault(
            cat_key, {"n": 0, "recurring_n": 0, "total_events": 0, "top_rule": None, "top_count": 0}
        )
        slot["n"] += 1
        slot["total_events"] += tot or 0
        if (tot or 0) >= 2:
            slot["recurring_n"] += 1
        if (tot or 0) > slot["top_count"]:
            slot["top_count"] = tot or 0
            slot["top_rule"] = rid
        if len(out["top_recurring"]) < 10 and (tot or 0) >= 2:
            out["top_recurring"].append({
                "rule_id": rid,
                "category": cat,
                "count": tot,
                "avg_h_between_recur": _avg_hours_between(c, rid),
                "promoted_level": lvl or 0,
                "last_seen": ls,
            })

    for cat, v in out["by_category"].items():
        pct = round(v["recurring_n"] / v["n"] * 100, 1) if v["n"] else 0.0
        v["recur_rate_pct"] = pct
        v["status"] = _classify_status(pct)
        # trend: 7d vs 30d
        pct7 = _recur_rate_in_window(c, cat, 7)
        pct30 = _recur_rate_in_window(c, cat, 30)
        v["recur_rate_7d"] = pct7
        v["recur_rate_30d"] = pct30
        v["trend"] = _trend_arrow(pct7, pct30)

    # archived count 포함
    archived = c.execute(
        "SELECT COUNT(*) FROM recurrence_rules WHERE archived=1"
    ).fetchone()[0]
    out["archived_rules"] = archived

    c.close()
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(json.dumps(stats(), ensure_ascii=False, indent=2))
        return 0
    op = argv[1]
    if op == "ensure":
        ensure_schema()
        print("[recurrence-tracker] schema ensured")
        return 0
    if op == "archive":
        n = archive_stale()
        print(f"[recurrence-tracker] archived {n} stale rules (last_seen > {STALE_DAYS}d)")
        return 0
    if op == "record":
        if len(argv) < 3:
            print("usage: record <rule_id> [category] [snippet]", file=sys.stderr)
            return 2
        rule_id = argv[2]
        category = argv[3] if len(argv) > 3 else "misc"
        snippet = argv[4] if len(argv) > 4 else ""
        res = record(rule_id, category, snippet)
        print(json.dumps(res, ensure_ascii=False))
        return 0
    if op == "stats":
        print(json.dumps(stats(), ensure_ascii=False, indent=2))
        return 0
    print(f"unknown op: {op}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print(f"[recurrence-tracker] fatal: {e}", file=sys.stderr)
        sys.exit(0)
