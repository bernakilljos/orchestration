#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
adaptive-measure — 현재 orca.db 안 "학습 바닥선" 측정 (사용자 명시 2026-10-19).

원칙 (사용자):
  - "저장된 대화 1,000건보다 교훈 3개 정확히 불러오는 게 더 유용"
  - 신규 시스템 X · 측정만 · 결과 보고 → 사용자 Phase 1 결정
  - 변경 금지: Rule·Hook·Subagent·Routing·FREEZE·전파

측정 축 (8):
  1. 저장량 (conversations · session_summary · solutions · decisions · recurrence)
  2. 재사용률 (problem_solutions.hit_count · last_hit_ts)
  3. 검증률 (verified=1 비율 · reusable_score 분포)
  4. 재발 원인 저장률 (recurrence_rules.description 길이 vs count 만)
  5. 검색 적중률 (lookup-history 로그 분석)
  6. Standing Requirement 활용 (ACTIVE vs completed · age)
  7. Golden Test 커버리지 (test-cache.json)
  8. Experience 분류 체계 (TASK/STANDING/EXPERIENCE/CORRECTION) 유무

출력:
  python adaptive-measure.py        # 콘솔 요약 + docs/ADAPTIVE_BASELINE_YYYY-MM-DD.md
  python adaptive-measure.py json   # JSON
"""
from __future__ import annotations
import json, os, sqlite3, sys, glob, time
from datetime import datetime, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
DB = os.path.join(ROOT, ".claude", "state", "orca.db")


def _measure():
    r = {"ts": datetime.now().isoformat(timespec="seconds"), "root": ROOT}
    if not os.path.exists(DB):
        r["error"] = "orca.db 없음"
        return r

    with sqlite3.connect(DB) as c:
        # 1) 저장량
        storage = {}
        for t in ("conversations", "session_summary", "problem_solutions",
                  "decisions", "recurrence_rules", "recurrence_events", "file_audit"):
            try:
                storage[t] = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            except Exception:
                storage[t] = -1
        r["storage"] = storage

        # 2) 재사용률 (problem_solutions)
        try:
            total = storage["problem_solutions"]
            hit = c.execute("SELECT COUNT(*) FROM problem_solutions WHERE hit_count > 0").fetchone()[0]
            avg_hits = c.execute("SELECT AVG(hit_count) FROM problem_solutions").fetchone()[0] or 0
            max_hits = c.execute("SELECT MAX(hit_count) FROM problem_solutions").fetchone()[0] or 0
            # 최근 30일 안 last_hit_ts 가 찍힌 solution 수
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            recent_hit = c.execute(
                "SELECT COUNT(*) FROM problem_solutions WHERE last_hit_ts >= ?",
                (thirty_days_ago,)
            ).fetchone()[0]
            r["reuse"] = {
                "total_solutions": total,
                "ever_hit": hit,
                "ever_hit_rate_pct": round(hit / total * 100, 1) if total else 0,
                "avg_hits": round(avg_hits, 2),
                "max_hits": max_hits,
                "recent_30d_hit": recent_hit,
                "recent_30d_rate_pct": round(recent_hit / total * 100, 1) if total else 0,
            }
        except Exception as e:
            r["reuse"] = {"error": str(e)}

        # 3) 검증률
        try:
            verified = c.execute("SELECT COUNT(*) FROM problem_solutions WHERE verified = 1").fetchone()[0]
            total = storage["problem_solutions"]
            score_dist = {}
            for row in c.execute(
                "SELECT reusable_score, COUNT(*) FROM problem_solutions GROUP BY reusable_score"
            ).fetchall():
                score_dist[str(row[0])] = row[1]
            r["verification"] = {
                "verified": verified,
                "verified_rate_pct": round(verified / total * 100, 1) if total else 0,
                "reusable_score_dist": score_dist,
            }
        except Exception as e:
            r["verification"] = {"error": str(e)}

        # 4) 재발 원인 저장률
        try:
            # recurrence_rules 안 description 길이 > 20 자 비율 (실제 원인 적혔는지 heuristic)
            rules_total = storage["recurrence_rules"]
            rich_desc = c.execute(
                "SELECT COUNT(*) FROM recurrence_rules WHERE LENGTH(description) > 20"
            ).fetchone()[0]
            # events 쪽 상세 사유 (description 유무)
            events_cols = [col[1] for col in c.execute("PRAGMA table_info(recurrence_events)").fetchall()]
            events_total = storage["recurrence_events"]
            events_detail = 0
            if "detail" in events_cols or "description" in events_cols or "root_cause" in events_cols:
                col_name = next(x for x in ("root_cause", "detail", "description") if x in events_cols)
                events_detail = c.execute(f"SELECT COUNT(*) FROM recurrence_events WHERE {col_name} IS NOT NULL AND LENGTH({col_name}) > 20").fetchone()[0]
            r["root_cause"] = {
                "rules_total": rules_total,
                "rules_rich_description": rich_desc,
                "rules_rich_rate_pct": round(rich_desc / rules_total * 100, 1) if rules_total else 0,
                "events_total": events_total,
                "events_with_detail": events_detail,
                "events_detail_rate_pct": round(events_detail / events_total * 100, 1) if events_total else 0,
                "root_cause_column_exists": any(c_ in events_cols for c_ in ("root_cause", "root-cause")),
            }
        except Exception as e:
            r["root_cause"] = {"error": str(e)}

    # 5) 검색 적중률 (lookup-history.log · lookup-rule 호출 횟수)
    try:
        log = os.path.join(ROOT, ".claude", "logs", "lookup-history.log")
        if os.path.exists(log):
            with open(log, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            # 최근 1000 줄 분석
            recent = lines[-1000:]
            search_cnt = sum(1 for ln in recent if "search" in ln.lower() or "query" in ln.lower())
            hit_cnt = sum(1 for ln in recent if "hit" in ln.lower() or "found" in ln.lower() or "매치" in ln)
            r["search"] = {
                "log_exists": True,
                "recent_lines": len(recent),
                "searches": search_cnt,
                "hits": hit_cnt,
                "hit_rate_pct": round(hit_cnt / search_cnt * 100, 1) if search_cnt else 0,
            }
        else:
            r["search"] = {"log_exists": False, "note": "lookup-history.log 없음 - 검색 추적 X"}
    except Exception as e:
        r["search"] = {"error": str(e)}

    # 6) Standing Requirements 활용
    try:
        sr_file = os.path.join(ROOT, ".claude", "state", "standing-requirements.json")
        if os.path.exists(sr_file):
            with open(sr_file, "r", encoding="utf-8") as f:
                sr = json.load(f)
            reqs = sr.get("requirements", []) if isinstance(sr, dict) else sr
            active = sum(1 for q in reqs if q.get("status") == "ACTIVE")
            r["standing"] = {
                "total": len(reqs),
                "active": active,
                "verify_pattern_set": sum(1 for q in reqs if q.get("verify_pattern")),
            }
        else:
            r["standing"] = {"error": "state 파일 없음"}
    except Exception as e:
        r["standing"] = {"error": str(e)}

    # 7) Golden Test 커버리지
    try:
        test_cache = os.path.join(ROOT, ".claude", "state", "test-cache.json")
        if os.path.exists(test_cache):
            with open(test_cache, "r", encoding="utf-8") as f:
                tc = json.load(f)
            r["golden"] = {
                "passed": tc.get("passed", 0),
                "total": tc.get("total", 0),
                "last_run": tc.get("ts", "?"),
            }
        else:
            r["golden"] = {"error": "test-cache 없음"}
    except Exception as e:
        r["golden"] = {"error": str(e)}

    # 8) Experience 분류 체계 (현재 problem_solutions.category 분포)
    try:
        with sqlite3.connect(DB) as c:
            cats = {}
            for row in c.execute("SELECT category, COUNT(*) FROM problem_solutions GROUP BY category").fetchall():
                cats[str(row[0])] = row[1]
            r["classification"] = {
                "categories": cats,
                "distinct": len(cats),
                "note": "현재 problem_solutions.category 만 · TASK/STANDING/EXPERIENCE/CORRECTION/FAILURE 분류 없음",
            }
    except Exception as e:
        r["classification"] = {"error": str(e)}

    return r


def _summary(data):
    lines = [f"# Adaptive Learning Baseline — {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    lines.append("**원칙**: 신규 시스템 X · 측정만 · 사용자 Phase 1 결정 전 바닥선 확정")
    lines.append("")
    lines.append("## 1. 저장량")
    s = data.get("storage", {})
    lines.append(f"| 테이블 | 레코드 수 |")
    lines.append(f"|---|---|")
    for k, v in s.items():
        lines.append(f"| `{k}` | {v} |")
    lines.append("")

    lines.append("## 2. 재사용률 (problem_solutions)")
    r = data.get("reuse", {})
    lines.append(f"- 총 solution: **{r.get('total_solutions', 0)}건**")
    lines.append(f"- 한 번이라도 재사용 (hit_count > 0): **{r.get('ever_hit', 0)}건 ({r.get('ever_hit_rate_pct', 0)}%)**")
    lines.append(f"- 평균 hit 수: {r.get('avg_hits', 0)} · 최대: {r.get('max_hits', 0)}")
    lines.append(f"- 최근 30일 안 hit: **{r.get('recent_30d_hit', 0)}건 ({r.get('recent_30d_rate_pct', 0)}%)**")
    lines.append("")

    lines.append("## 3. 검증률")
    v = data.get("verification", {})
    lines.append(f"- 검증된 (verified=1): **{v.get('verified', 0)}건 ({v.get('verified_rate_pct', 0)}%)**")
    lines.append(f"- reusable_score 분포: {v.get('reusable_score_dist', {})}")
    lines.append("")

    lines.append("## 4. 재발 원인 저장률")
    rc = data.get("root_cause", {})
    lines.append(f"- recurrence_rules: {rc.get('rules_total', 0)}건 · 상세 description (20자+): **{rc.get('rules_rich_rate_pct', 0)}%**")
    lines.append(f"- recurrence_events: {rc.get('events_total', 0)}건 · 상세 detail: **{rc.get('events_detail_rate_pct', 0)}%**")
    lines.append(f"- `root_cause` 컬럼 존재: {rc.get('root_cause_column_exists', False)}")
    lines.append("")

    lines.append("## 5. 검색 적중률")
    sr = data.get("search", {})
    if sr.get("log_exists"):
        lines.append(f"- 최근 로그 1000줄 중 검색: {sr.get('searches', 0)}건 · hit: {sr.get('hits', 0)}건 · 적중률 **{sr.get('hit_rate_pct', 0)}%**")
    else:
        lines.append(f"- {sr.get('note', sr.get('error', '측정 X'))}")
    lines.append("")

    lines.append("## 6. Standing Requirements")
    sg = data.get("standing", {})
    lines.append(f"- 총 {sg.get('total', 0)}건 · ACTIVE {sg.get('active', 0)}건 · verify_pattern 설정 {sg.get('verify_pattern_set', 0)}건")
    lines.append("")

    lines.append("## 7. Golden Test")
    g = data.get("golden", {})
    lines.append(f"- 최근: {g.get('passed', 0)}/{g.get('total', 0)} · {g.get('last_run', '?')}")
    lines.append("")

    lines.append("## 8. Experience 분류 체계")
    cl = data.get("classification", {})
    lines.append(f"- 현재 category 분포: {cl.get('categories', {})}")
    lines.append(f"- 사용자 제안 분류 (TASK/STANDING/EXPERIENCE/CORRECTION/FAILURE/IMPROVEMENT_CANDIDATE): **없음**")
    lines.append("")

    # 평가 (바닥선 판정)
    lines.append("## 바닥선 판정 (Phase 1 결정 참고)")
    ever_hit = data.get("reuse", {}).get("ever_hit_rate_pct", 0)
    verified = data.get("verification", {}).get("verified_rate_pct", 0)
    rich = data.get("root_cause", {}).get("rules_rich_rate_pct", 0)
    hit_rate = data.get("search", {}).get("hit_rate_pct", 0) if data.get("search", {}).get("log_exists") else None
    judgments = []
    if ever_hit < 30:
        judgments.append(f"❌ **재사용률 {ever_hit}%** (<30% · 저장만 되고 안 쓰임)")
    elif ever_hit < 70:
        judgments.append(f"⚠ 재사용률 {ever_hit}% (70% 미만 · 검색·활용 체계 약함)")
    else:
        judgments.append(f"✅ 재사용률 {ever_hit}% (양호)")
    if verified < 20:
        judgments.append(f"❌ 검증률 {verified}% (<20% · 미검증 저장 다수)")
    else:
        judgments.append(f"✅ 검증률 {verified}%")
    if rich == 0:
        judgments.append(f"❌ root_cause 저장률 {rich}% (**원인 분석 체계 없음** · 사용자 제안 핵심)")
    elif rich < 50:
        judgments.append(f"⚠ root_cause 저장률 {rich}%")
    else:
        judgments.append(f"✅ root_cause 저장률 {rich}%")
    if hit_rate is None:
        judgments.append(f"❌ 검색 적중률 **측정 불가** (lookup 로그 없음)")
    elif hit_rate < 50:
        judgments.append(f"❌ 검색 적중률 {hit_rate}% (<50%)")
    else:
        judgments.append(f"✅ 검색 적중률 {hit_rate}%")
    for j in judgments:
        lines.append(f"- {j}")
    lines.append("")
    lines.append("## Phase 1 후보 (사용자 승인 후만)")
    lines.append("1. `recurrence_events` 테이블 `root_cause` 컬럼 ALTER (스키마 1 변경)")
    lines.append("2. `problem_solutions` 에 `experience_type` 컬럼 ALTER (TASK/STANDING/EXPERIENCE/CORRECTION/FAILURE 분류)")
    lines.append("3. `recurrence_improvements` 신규 테이블 (pre/post metric · verified flag)")
    lines.append("4. `/learning-report` 커맨드 (상세 지표)")
    lines.append("5. 신규 Hook ❌ · 신규 Subagent ❌ · 기존 Stop hook 에만 '학습 후보 검출' 로직 추가")
    return "\n".join(lines)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "md"
    data = _measure()
    if cmd == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        md = _summary(data)
        date = datetime.now().strftime("%Y-%m-%d")
        path = os.path.join(ROOT, "docs", f"ADAPTIVE_BASELINE_{date}.md")
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
