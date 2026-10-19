#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
learning-report — Adaptive Orchestration 학습 효과 상세 보고 (Phase 1-3).

adaptive-measure 바닥선 + root_cause/experience_type/improvements 통합.

사용:
  python learning-report.py        # 상세 markdown
  python learning-report.py json   # JSON
  python learning-report.py short  # 한 줄 (statusline 용)

보고 축:
  A. 학습 저장 (storage · classification)
  B. 재사용 효과 (retrieval hit · hit_count distribution)
  C. 원인 분석 (recurrence_events.root_cause 저장률)
  D. 개선 검증 (recurrence_improvements · pre/post · VERIFIED)
  E. 재발률 추세 (현재 vs 개선 후)
  F. 지시 분류 (TASK/EXPERIENCE/CORRECTION/FAILURE)
"""
from __future__ import annotations
import json, os, sqlite3, sys
from datetime import datetime, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
DB = os.path.join(ROOT, ".claude", "state", "orca.db")


def _collect():
    r = {"ts": datetime.now().isoformat(timespec="seconds")}
    if not os.path.exists(DB):
        r["error"] = "orca.db 없음"
        return r

    with sqlite3.connect(DB) as c:
        # A. 저장
        storage = {}
        for t in ("conversations", "session_summary", "problem_solutions",
                  "decisions", "recurrence_rules", "recurrence_events",
                  "recurrence_improvements"):
            try:
                storage[t] = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except Exception:
                storage[t] = -1
        r["A_storage"] = storage

        # B. 재사용 효과
        try:
            total = storage.get("problem_solutions", 0)
            hit = c.execute("SELECT COUNT(*) FROM problem_solutions WHERE hit_count > 0").fetchone()[0]
            avg_hits = c.execute("SELECT AVG(hit_count) FROM problem_solutions WHERE hit_count > 0").fetchone()[0] or 0
            top5 = c.execute(
                "SELECT problem, hit_count, reusable_score, verified FROM problem_solutions "
                "WHERE hit_count > 0 ORDER BY hit_count DESC LIMIT 5"
            ).fetchall()
            r["B_reuse"] = {
                "total": total,
                "ever_hit": hit,
                "hit_rate_pct": round(hit / total * 100, 1) if total else 0,
                "avg_hits_when_hit": round(avg_hits, 2),
                "top_reused": [
                    {"problem": row[0][:60], "hits": row[1], "score": row[2], "verified": bool(row[3])}
                    for row in top5
                ],
            }
        except Exception as e:
            r["B_reuse"] = {"error": str(e)}

        # C. 원인 분석
        try:
            evt_total = storage.get("recurrence_events", 0)
            evt_with_cause = c.execute(
                "SELECT COUNT(*) FROM recurrence_events WHERE root_cause IS NOT NULL AND LENGTH(root_cause) > 10"
            ).fetchone()[0]
            rules = c.execute(
                "SELECT rule_id, category, total_occurrences, promoted_level, archived "
                "FROM recurrence_rules ORDER BY total_occurrences DESC"
            ).fetchall()
            r["C_root_cause"] = {
                "events_total": evt_total,
                "events_with_root_cause": evt_with_cause,
                "root_cause_rate_pct": round(evt_with_cause / evt_total * 100, 1) if evt_total else 0,
                "rules": [
                    {"id": row[0], "cat": row[1], "occur": row[2], "promo": row[3], "archived": bool(row[4])}
                    for row in rules
                ],
            }
        except Exception as e:
            r["C_root_cause"] = {"error": str(e)}

        # D. 개선 검증
        try:
            imp_total = storage.get("recurrence_improvements", 0)
            by_status = {}
            for row in c.execute(
                "SELECT status, COUNT(*) FROM recurrence_improvements GROUP BY status"
            ).fetchall():
                by_status[row[0]] = row[1]
            verified = c.execute(
                "SELECT COUNT(*) FROM recurrence_improvements WHERE verified = 1"
            ).fetchone()[0]
            samples = c.execute(
                "SELECT improvement_id, rule_id, status, pre_metric, post_metric, verified "
                "FROM recurrence_improvements ORDER BY ts_updated DESC LIMIT 5"
            ).fetchall()
            r["D_improvement"] = {
                "total": imp_total,
                "verified": verified,
                "by_status": by_status,
                "recent": [
                    {"id": row[0], "rule": row[1], "status": row[2],
                     "pre": row[3], "post": row[4], "verified": bool(row[5])}
                    for row in samples
                ],
            }
        except Exception as e:
            r["D_improvement"] = {"error": str(e)}

        # F. Experience 분류
        try:
            by_exp = {}
            for row in c.execute(
                "SELECT COALESCE(experience_type, '(unclassified)'), COUNT(*) "
                "FROM problem_solutions GROUP BY experience_type"
            ).fetchall():
                by_exp[row[0]] = row[1]
            r["F_classification"] = by_exp
        except Exception as e:
            r["F_classification"] = {"error": str(e)}

    # E. 재발률 (rule-adherence.json)
    try:
        ra_f = os.path.join(ROOT, ".claude", "state", "rule-adherence.json")
        if os.path.exists(ra_f):
            with open(ra_f, "r", encoding="utf-8") as f:
                ra = json.load(f)
            rec = ra.get("recurrence", {}).get("by_category", {})
            r["E_recurrence_trend"] = {
                cat: {"rate_pct": v.get("recur_rate_pct", 0), "trend": v.get("trend", "→"),
                      "status": v.get("status", "normal")}
                for cat, v in rec.items()
            }
        else:
            r["E_recurrence_trend"] = {"error": "rule-adherence.json 없음"}
    except Exception as e:
        r["E_recurrence_trend"] = {"error": str(e)}

    # 검색 적중률 (lookup-rule.log 분석 · 신 포맷)
    try:
        log = os.path.join(ROOT, ".claude", "logs", "lookup-rule.log")
        if os.path.exists(log):
            with open(log, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()[-500:]
            search_cnt = sum(1 for ln in lines if "[search]" in ln)
            hit_cnt = sum(1 for ln in lines if "[hit]" in ln)
            miss_cnt = sum(1 for ln in lines if "[miss]" in ln)
            r["search_metrics"] = {
                "searches": search_cnt,
                "hits": hit_cnt,
                "misses": miss_cnt,
                "hit_rate_pct": round(hit_cnt / search_cnt * 100, 1) if search_cnt else 0,
            }
        else:
            r["search_metrics"] = {"note": "lookup-rule.log 없음 (아직 호출 X)"}
    except Exception as e:
        r["search_metrics"] = {"error": str(e)}

    return r


def _md(data):
    L = [f"# Learning Effectiveness Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]

    L.append("## A. 저장")
    for k, v in data.get("A_storage", {}).items():
        L.append(f"- `{k}`: {v}")
    L.append("")

    L.append("## B. 재사용 효과")
    b = data.get("B_reuse", {})
    L.append(f"- 총 solution: **{b.get('total', 0)}** · 재사용 (hit > 0): **{b.get('ever_hit', 0)} ({b.get('hit_rate_pct', 0)}%)**")
    L.append(f"- 평균 hits (hit 있을 때): {b.get('avg_hits_when_hit', 0)}")
    L.append("- Top 5 재사용:")
    for t in b.get("top_reused", []):
        vcheck = "✅" if t.get("verified") else "⚠"
        L.append(f"  - {vcheck} `{t.get('problem', '?')}` (hits={t.get('hits')}, score={t.get('score')})")
    L.append("")

    L.append("## C. 원인 분석 (root_cause)")
    c = data.get("C_root_cause", {})
    rate = c.get("root_cause_rate_pct", 0)
    status = "✅" if rate >= 70 else ("⚠" if rate >= 30 else "❌")
    L.append(f"- events {c.get('events_total', 0)}건 · root_cause 저장: **{c.get('events_with_root_cause', 0)} ({rate}%)** {status}")
    L.append("- 등록된 rules:")
    for rule in c.get("rules", []):
        L.append(f"  - `{rule.get('id', '?')}` [{rule.get('cat', '?')}] occur={rule.get('occur')} promoted={rule.get('promo')}")
    L.append("")

    L.append("## D. 개선 검증 (recurrence_improvements)")
    d = data.get("D_improvement", {})
    L.append(f"- 총 {d.get('total', 0)}건 · verified **{d.get('verified', 0)}건**")
    L.append(f"- status 분포: {d.get('by_status', {})}")
    L.append("- 최근 5건:")
    for imp in d.get("recent", []):
        vc = "✅" if imp.get("verified") else "⏳"
        pre = imp.get("pre") if imp.get("pre") is not None else "?"
        post = imp.get("post") if imp.get("post") is not None else "?"
        L.append(f"  - {vc} #{imp.get('id')} rule={imp.get('rule')} status={imp.get('status')} pre={pre} post={post}")
    L.append("")

    L.append("## E. 재발률 추세")
    e = data.get("E_recurrence_trend", {})
    if "error" in e:
        L.append(f"- {e['error']}")
    else:
        for cat, v in e.items():
            L.append(f"- {cat}: {v.get('rate_pct', 0)}% {v.get('trend', '→')} ({v.get('status', '?')})")
    L.append("")

    L.append("## F. Experience 분류 (TASK/EXPERIENCE/CORRECTION/FAILURE)")
    f = data.get("F_classification", {})
    if "error" in f:
        L.append(f"- {f['error']}")
    else:
        for k, v in f.items():
            L.append(f"- {k}: {v}건")
    L.append("")

    L.append("## 검색 적중률 (lookup-rule.log 신 포맷)")
    s = data.get("search_metrics", {})
    if "note" in s:
        L.append(f"- {s['note']}")
    elif "error" in s:
        L.append(f"- {s['error']}")
    else:
        L.append(f"- 검색 {s.get('searches', 0)} · hit {s.get('hits', 0)} · miss {s.get('misses', 0)} · 적중률 **{s.get('hit_rate_pct', 0)}%**")

    return "\n".join(L)


def _short(data):
    """statusline 용 한 줄."""
    b = data.get("B_reuse", {})
    c = data.get("C_root_cause", {})
    d = data.get("D_improvement", {})
    s = data.get("search_metrics", {})
    reuse = f"{b.get('hit_rate_pct', 0):.0f}%"
    rc = f"{c.get('root_cause_rate_pct', 0):.0f}%"
    imp_v = d.get("verified", 0)
    hr = s.get("hit_rate_pct", 0) if "hit_rate_pct" in s else "⏳"
    return f"재사용 {reuse} · root_cause {rc} · 검증개선 {imp_v} · 검색적중 {hr}"


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "md"
    data = _collect()
    if cmd == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    elif cmd == "short":
        print(_short(data))
    else:
        md = _md(data)
        date = datetime.now().strftime("%Y-%m-%d")
        path = os.path.join(ROOT, "docs", f"LEARNING_REPORT_{date}.md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        print(md)
        print(f"\n[OK] report: {path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERR] {e}", file=sys.stderr)
        sys.exit(1)
