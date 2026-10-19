"""UserPromptSubmit 훅 모듈 — 관련 검증 경험 top 3 자동 주입 (A1 · 2026-10-19).

이 모듈은 .claude/scripts/inject-experience.py 와 같은 로직 (성능 위해 직접 수행).
결과: dict {"systemMessage": "..."} · prompt-dispatch 가 수집·병합.
"""
from __future__ import annotations
import re
import sqlite3
from datetime import datetime

from _common import Ctx, ROOT


DB = ROOT / ".claude" / "state" / "orca.db"


def _extract_keywords(text, top_n=5):
    words = re.findall(r"[가-힣]{2,}|[A-Za-z]{3,}", text or "")
    stop = {"있는", "없는", "이것", "저것", "그것", "되는", "하는", "해줘", "주세요",
            "입니다", "the", "and", "for", "with", "from", "that", "this"}
    words = [w.lower() for w in words if w not in stop]
    seen = {}
    for w in words:
        seen[w] = seen.get(w, 0) + 1
    sorted_w = sorted(seen.items(), key=lambda x: -x[1])
    return [w for w, _ in sorted_w[:top_n]]


def _find_experiences(keywords, top=3):
    if not keywords or not DB.exists():
        return []
    try:
        with sqlite3.connect(str(DB)) as c:
            rows = c.execute(
                "SELECT id, problem, solution, category, reusable_score, verified, hit_count "
                "FROM problem_solutions "
                "WHERE (verified=1 OR reusable_score >= 8) "
                "AND (experience_type IS NULL OR experience_type NOT IN ('ARCHIVED','STALE'))"
            ).fetchall()
    except Exception:
        return []
    scored = []
    for r in rows:
        text = ((r[1] or "") + " " + (r[2] or "") + " " + (r[3] or "")).lower()
        s = sum(1 for kw in keywords if kw in text)
        if s > 0:
            scored.append((s, r))
    scored.sort(key=lambda x: (-x[0], -(x[1][4] or 0), -(x[1][6] or 0)))
    return [r for _, r in scored[:top]]


def _update_hits(ids):
    if not ids:
        return
    now = datetime.now().isoformat(timespec="seconds")
    try:
        with sqlite3.connect(str(DB)) as c:
            for i in ids:
                c.execute(
                    "UPDATE problem_solutions SET hit_count = COALESCE(hit_count, 0) + 1, "
                    "last_hit_ts = ? WHERE id = ?", (now, i)
                )
    except Exception:
        pass


def run(ctx: Ctx):
    prompt = ctx.payload.get("prompt", "") or ctx.payload.get("user_prompt", "")
    if not prompt or len(prompt) < 10:
        return None
    kws = _extract_keywords(prompt)
    exps = _find_experiences(kws, top=3)
    if not exps:
        return None
    _update_hits([e[0] for e in exps])
    L = ["## 📚 관련 검증 경험 (A1 자동 주입 · verified/score≥8 중 top 3 · hit_count 자동 증가)"]
    for i, (eid, problem, solution, category, score, verified, hits) in enumerate(exps, 1):
        vcheck = "✅" if verified else "⭐"
        p_short = (problem or "")[:80].replace("\n", " ")
        s_short = (solution or "")[:120].replace("\n", " ")
        L.append(f"{i}. {vcheck} [{category or '?'}] score={score} hits={hits}: {p_short}")
        if s_short.strip():
            L.append(f"   → {s_short}")
    L.append("")
    L.append("*적용 가능 시 재사용 · 부적합 시 무시 · hit_count 가 자동 추적*")
    return "\n".join(L)
