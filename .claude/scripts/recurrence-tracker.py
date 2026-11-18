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
    CREATE TABLE IF NOT EXISTS recurrence_improvements (
      improvement_id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id TEXT NOT NULL, category TEXT,
      problem_summary TEXT, root_cause TEXT, improvement_plan TEXT, pre_metric REAL, post_metric REAL,
      pre_sample_size INTEGER, post_sample_size INTEGER, pre_measured_at TEXT, post_measured_at TEXT,
      verified INTEGER DEFAULT 0, status TEXT DEFAULT 'OBSERVING',
      ts_created TEXT DEFAULT (datetime('now')), ts_updated TEXT DEFAULT (datetime('now')),
      FOREIGN KEY (rule_id) REFERENCES recurrence_rules(rule_id)
    );
    """)
    # 기존 테이블에 archived 컬럼 없으면 추가 (idempotent)
    try:
        cols = [r[1] for r in c.execute("PRAGMA table_info(recurrence_rules)").fetchall()]
        if "archived" not in cols:
            c.execute("ALTER TABLE recurrence_rules ADD COLUMN archived INTEGER DEFAULT 0")
    except Exception:
        pass
    # recurrence_events 에 root_cause / auto_fix_status 컬럼 추가 (2026-10-26 · verify-improvement.py 연결용 스키마 선확장)
    try:
        ev_cols = [r[1] for r in c.execute("PRAGMA table_info(recurrence_events)").fetchall()]
        if "root_cause" not in ev_cols:
            c.execute("ALTER TABLE recurrence_events ADD COLUMN root_cause TEXT")
        if "auto_fix_status" not in ev_cols:
            c.execute("ALTER TABLE recurrence_events ADD COLUMN auto_fix_status TEXT")  # pending|dispatched|fixed|skipped
        if "improvement_id" not in ev_cols:
            c.execute("ALTER TABLE recurrence_events ADD COLUMN improvement_id INTEGER")
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


def _trigger_improvement_start(rule_id: str, category: str, total: int, desc: str) -> None:
    """2026-10-26 외부 AI 설계 수용: 통합 Supervisor Runtime 호출 (REPAIR workflow).
    + verify-improvement.py start 호출 유지 (관찰 레코드 · 지표 추적용 · 이중 등록).

    실패해도 추적 자체는 성공 (best-effort · 로그 .claude/logs/)."""
    log = ROOT / ".claude" / "logs" / "recurrence-trigger.log"
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # ① Supervisor REPAIR goal 등록 (실행 엔진 통합 — 외부 AI 설계)
    try:
        sys.path.insert(0, str(ROOT / ".claude" / "scripts" / "lib"))
        import supervisor  # noqa: WPS433
        gid = supervisor.create_repair_goal(rule_id, category, total, desc)
        with log.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {rule_id} REPAIR goal #{gid} created\n")
    except Exception as e:  # noqa: BLE001
        try:
            with log.open("a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {rule_id} supervisor ERR: {e}\n")
        except Exception:
            pass

    # ② verify-improvement.py start (관찰 레코드 · 지표 전후 비교용)
    try:
        import subprocess
        script = ROOT / ".claude" / "scripts" / "verify-improvement.py"
        if not script.exists():
            return
        env = os.environ.copy()
        env["ALLOW_VISIBLE_WINDOW"] = "1"
        r = subprocess.run([
            sys.executable, "-X", "utf8", str(script), "start", rule_id,
            "--metric", "재발률",
            "--direction", "descending",
            "--value", str(total),
            "--sample", str(total),
            "--cause", f"재발 {total}회 자동 승격 ({category})",
            "--plan", f"Supervisor REPAIR workflow 등록 · {(desc or '')[:100]}",
        ], check=False, timeout=10, capture_output=True, text=True, env=env)
        with log.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {rule_id} verify-improvement rc={r.returncode}\n")
            if r.stderr: f.write(f"  stderr: {r.stderr.strip()[:500]}\n")
    except Exception as e:  # noqa: BLE001
        try:
            with log.open("a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {rule_id} verify-improvement ERR: {e}\n")
        except Exception:
            pass


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
    old_lvl = lvl or 0
    new_lvl = old_lvl

    if total >= 5 and old_lvl < 3:
        new_lvl = 3
        _append_md(
            ENFORCE_MD,
            f"- [{category}] **{rule_id}** · {total}회 · PreToolUse hook 강제 차단 후보 · {desc}",
            "# Hook 강제 차단 후보 (재발 5회+ 자동 승격)\n\n수동 리뷰 후 `.claude/hooks/tool/<name>.py` 추가.",
        )
    elif total >= 3 and old_lvl < 2:
        new_lvl = 2
        _append_md(
            PROMO_MD,
            f"- [{category}] **{rule_id}** · {total}회 · CLAUDE.md § 7 승격 후보 · {desc}",
            "# CLAUDE.md 규칙 승격 후보 (재발 3회+ 자동 승격)\n\n수동 리뷰 후 CLAUDE.md § 7 또는 `.claude/rules/*.md` 추가.",
        )
    elif total >= 2 and old_lvl < 1:
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
        old_promoted = row[1] or 0
        c.execute(
            "UPDATE recurrence_rules SET total_occurrences=?, last_seen=? WHERE rule_id=?",
            (total, now, rule_id),
        )
    else:
        total = 1
        old_promoted = 0
        c.execute(
            "INSERT INTO recurrence_rules(rule_id, category, first_seen, last_seen, total_occurrences, description) "
            "VALUES (?,?,?,?,1,?)",
            (rule_id, category, now, now, snippet[:200] if snippet else rule_id),
        )

    event_id = c.execute(
        "INSERT INTO recurrence_events(rule_id, session_id, user_prompt_snippet) VALUES (?,?,?)",
        (rule_id, session_id, (snippet or "")[:300]),
    ).lastrowid

    new_lvl = _check_promotion(c, rule_id, total)
    if new_lvl:
        c.execute("UPDATE recurrence_rules SET promoted_level=? WHERE rule_id=?", (new_lvl, rule_id))

    c.commit()
    c.close()

    # 2026-10-26: 승격 전환 (level 2+) 시 verify-improvement.py start 자동 호출 (DB close 후 호출로 lock 회피)
    if new_lvl >= 2 and new_lvl > old_promoted:
        _trigger_improvement_start(rule_id, category or "misc", total, snippet or rule_id)

    return {"rule_id": rule_id, "total": total, "promoted_level": new_lvl, "event_id": event_id}


# 2026-11-18 R310 근본 원인 기록 — recurrence_events.root_cause 가 312건 중 0건 (채우는 흐름 없음).
#   증상(사용자 문장)과 원인을 분리 · 증거 없는 원인은 [추정] 으로만 · 같은 규칙의 확정 원인은 재사용 · 해결 실패 시 상태 갱신.
CAUSE_STATUS = ("confirmed", "suspected")


def _latest_event(c, rule_id):
    row = c.execute("SELECT id FROM recurrence_events WHERE rule_id=? ORDER BY id DESC LIMIT 1", (rule_id,)).fetchone()
    return row[0] if row else None


def set_root_cause(target: str, cause: str, evidence: str, status: str, fix: str = "") -> dict:
    """target = 이벤트 번호 또는 rule_id(그 규칙의 최신 이벤트). confirmed 는 증거 필수 (코드 파일:줄·로그·실행 출력)."""
    if status not in CAUSE_STATUS:
        raise ValueError(f"status 는 {CAUSE_STATUS} 중 하나")
    if not cause.strip():
        raise ValueError("cause 비어 있음")
    if status == "confirmed" and len(evidence.strip()) < 10:
        raise ValueError("confirmed 는 증거 필수 (파일:줄·로그·실행 출력 · 10자 이상) — 없으면 suspected 로 기록")
    ensure_schema()
    c = sqlite3.connect(DB)
    try:
        eid = int(target) if target.isdigit() else _latest_event(c, target)
        row = c.execute("SELECT rule_id FROM recurrence_events WHERE id=?", (eid,)).fetchone() if eid else None
        if not row:
            raise ValueError(f"이벤트 없음: {target}")
        rule_id = row[0]
        tag = "[확인]" if status == "confirmed" else "[추정]"
        text = f"{tag} {cause.strip()} · 근거: {evidence.strip() or '없음'}"
        # 같은 규칙에서 같은 원인으로 이미 확정된 기록이 있으면 그 개선 기록을 재사용 (새로 만들지 않음)
        reused = c.execute(
            "SELECT improvement_id FROM recurrence_improvements WHERE rule_id=? AND root_cause LIKE ? "
            "ORDER BY improvement_id DESC LIMIT 1", (rule_id, f"%{cause.strip()[:40]}%")).fetchone()
        imp_id = reused[0] if reused else None
        prior = None
        if reused:
            # R312: 같은 원인이 다시 발생 = 기존 해결책이 재발을 못 막았다 → 검증 표시를 풀고 재검증 대상으로 (원인 분석부터 다시)
            prior = c.execute("SELECT status, verified, improvement_plan FROM recurrence_improvements WHERE improvement_id=?",
                              (imp_id,)).fetchone()
            if prior and prior[0] == "VERIFIED":
                c.execute("UPDATE recurrence_improvements SET verified=0, status='REOPENED', ts_updated=datetime('now'), "
                          "improvement_plan=COALESCE(improvement_plan,'') || ? WHERE improvement_id=?",
                          (f" | reopened: event {eid} 같은 원인 재발", imp_id))
        if imp_id is None and status == "confirmed":
            imp_id = c.execute(
                "INSERT INTO recurrence_improvements(rule_id, problem_summary, root_cause, improvement_plan, status) "
                "VALUES (?,?,?,?, 'OBSERVING')", (rule_id, f"event {eid}", text, fix or "")).lastrowid
        c.execute("UPDATE recurrence_events SET root_cause=?, auto_fix_status=?, improvement_id=? WHERE id=?",
                  (text, "open" if status == "confirmed" else "suspected", imp_id, eid))
        c.commit()
        out = {"event_id": eid, "rule_id": rule_id, "root_cause": text, "improvement_id": imp_id, "reused": bool(reused)}
        if prior:
            out["prior_fix"] = {"status": prior[0], "plan": (prior[2] or "")[-300:],
                                "next": "기존 해결책을 그대로 쓰지 말고 이번 재현으로 다시 검증 — fix-result <id> passed --test 파일.py::시험"}
        return out
    finally:
        c.close()


def _run_regression_test(nodeid: str) -> tuple:
    """회귀 시험을 지금 실행 (회귀 게이트와 같은 실행기 independent_verifier._pytest_failures · 재구현 X) → (통과, 요약)."""
    import re as _re
    if not _re.fullmatch(r"[\w./\-]+\.py::[\w\[\]:.-]+", nodeid.strip()):
        raise ValueError("--test 는 pytest nodeid (파일.py::시험이름)")
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
    sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
    from independent_verifier import _pytest_failures
    fails, summary, rc = _pytest_failures(root, [nodeid.strip()], 600)
    return rc == 0 and not fails, f"rc={rc} {summary}"[:200]


def set_fix_result(target: str, result: str, evidence: str, test: str = "") -> dict:
    """해결책 검증 결과 — passed 는 증거 필수 · failed 는 연결된 개선 기록을 FIX_FAILED 로 되돌림 (검증 안 된 채 남지 않게).
    R312: passed 는 회귀 시험(--test) 필수 · 지금 실행해 실패하면 passed 가 아니라 failed 로 기록 (자기 보고 PASS 차단)."""
    if result not in ("passed", "failed"):
        raise ValueError("result 는 passed|failed")
    if result == "passed" and len(evidence.strip()) < 10:
        raise ValueError("passed 는 증거 필수 (회귀 시험 이름·실행 출력)")
    test_run = None
    if result == "passed":
        if not test.strip():
            raise ValueError("passed 는 --test 파일.py::시험 필수 — 지금 실행해 통과해야 VERIFIED")
        ok, summ = _run_regression_test(test)
        test_run = {"test": test.strip(), "ok": ok, "summary": summ}
        evidence = f"{evidence.strip()} · 시험 {test.strip()} {summ}"
        if not ok:
            result = "failed"
    c = sqlite3.connect(DB)
    try:
        eid = int(target) if target.isdigit() else _latest_event(c, target)
        row = c.execute("SELECT improvement_id FROM recurrence_events WHERE id=?", (eid,)).fetchone() if eid else None
        if not row:
            raise ValueError(f"이벤트 없음: {target}")
        c.execute("UPDATE recurrence_events SET auto_fix_status=? WHERE id=?",
                  ("verified" if result == "passed" else "fix_failed", eid))
        if row[0]:
            c.execute("UPDATE recurrence_improvements SET verified=?, status=?, ts_updated=datetime('now'), "
                      "improvement_plan=COALESCE(improvement_plan,'') || ? WHERE improvement_id=?",
                      (1 if result == "passed" else 0, "VERIFIED" if result == "passed" else "FIX_FAILED",
                       f" | {result}: {evidence.strip()}", row[0]))
        c.commit()
        return {"event_id": eid, "result": result, "improvement_id": row[0], "test_run": test_run}
    finally:
        c.close()


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


# 2026-11-18 R310 개발 품질 실측 — 추정치 대신 원장·대화 기록으로 분자/분모를 그대로 보인다 (과거 기록 수정 X).
#   재발 새 기준 시작 = R308 감지 범위 수정 커밋 3c316f16 (붙여 넣은 글·알림 제외) · 시각은 DB 와 같은 UTC.
NEW_BASIS_UTC = "2026-11-18 10:46:53"


MIN_SAMPLE = 30   # 헌장 B1 표본 하한 — 분모가 이보다 작으면 비율을 정상 수치처럼 보이지 않는다


def _ratio(num, den):
    state = "미측정" if not den else ("표본 부족" if den < MIN_SAMPLE else "측정")
    return {"num": num, "den": den, "pct": round(num / den * 100, 1) if den >= MIN_SAMPLE else None, "state": state}


def quality() -> dict:
    out = {"basis": {"recurrence_new_since_utc": NEW_BASIS_UTC,
                     "first_attempt": "실행 요청 다음의 같은 세션 요청이 redo(다시 지시)가 아닌 비율 "
                                      "(한계: redo 는 분류기 판정 · 다른 세션에서 다시 지시하면 못 셈 → 상한값)",
                     "reinstruct": "redo ÷ (execute + redo) · 오등록(invalid_registration) 제외",
                     "recurrence_per_100": "재발 이벤트 ÷ 사용자 프롬프트 × 100 (알림 제외)",
                     "same_cause": "확정([확인]) 원인 중 같은 원인이 2번+ 기록된 비율"}}
    led = ROOT / ".claude" / "state" / "request-ledger.json"
    try:
        reqs = [r for r in json.loads(led.read_text(encoding="utf-8")).get("requests", [])
                if r.get("status") != "invalid_registration" and r.get("classification") in ("execute", "redo")]
    except Exception:  # noqa: BLE001 — 원장 없음·손상 = 미측정 (0 아님)
        reqs = []
    redo = sum(1 for r in reqs if r["classification"] == "redo")
    out["reinstruct"] = _ratio(redo, len(reqs))
    by_sid = {}
    for r in reqs:
        by_sid.setdefault(r.get("session_id") or "?", []).append(r)
    ok = den = 0
    for lst in by_sid.values():
        for a, b in zip(lst, lst[1:]):
            if a["classification"] == "execute":
                den += 1
                ok += b["classification"] != "redo"
    out["first_attempt"] = _ratio(ok, den)
    c = sqlite3.connect(DB)
    try:
        def prompts(where, args=()):
            try:
                return c.execute("SELECT COUNT(*) FROM conversations WHERE role='user' AND content NOT LIKE '<task-notification>%' "
                                 + where, args).fetchone()[0]
            except sqlite3.Error:
                return 0
        ev_old = c.execute("SELECT COUNT(*) FROM recurrence_events WHERE detected_at < ?", (NEW_BASIS_UTC,)).fetchone()[0]
        ev_new = c.execute("SELECT COUNT(*) FROM recurrence_events WHERE detected_at >= ?", (NEW_BASIS_UTC,)).fetchone()[0]
        old = _ratio(ev_old, prompts("AND ts < ?", (NEW_BASIS_UTC,)))
        new = _ratio(ev_new, prompts("AND ts >= ?", (NEW_BASIS_UTC,)))
        old["label"] = "이전 기준 (붙여 넣은 글·상태줄 복사 포함 · 그대로 보존)"
        new["label"] = "새 기준 (직접 쓴 글만)"
        out["recurrence_per_100"] = {"old": old, "new": new}
        causes = [r[0] for r in c.execute("SELECT root_cause FROM recurrence_events WHERE root_cause LIKE '[확인]%'")]
        keys = [x.split(" · 근거:")[0] for x in causes]
        dup = sum(1 for k in set(keys) if keys.count(k) >= 2)
        out["same_cause"] = _ratio(dup, len(set(keys)))
    finally:
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
    if op == "quality":
        print(json.dumps(quality(), ensure_ascii=False, indent=2))
        return 0
    if op in ("root-cause", "fix-result"):
        import argparse
        ap = argparse.ArgumentParser(prog=f"recurrence-tracker.py {op}")
        ap.add_argument("target", help="이벤트 번호 또는 rule_id (최신 이벤트)")
        if op == "root-cause":
            ap.add_argument("--cause", required=True)
            ap.add_argument("--evidence", default="")
            ap.add_argument("--status", choices=CAUSE_STATUS, default="suspected")
            ap.add_argument("--fix", default="", help="확인된 해결책·회귀 시험")
        else:
            ap.add_argument("result", choices=("passed", "failed"))
            ap.add_argument("--evidence", default="")
            ap.add_argument("--test", default="", help="passed 필수 · pytest nodeid (지금 실행)")
        a = ap.parse_args(argv[2:])
        try:
            res = (set_root_cause(a.target, a.cause, a.evidence, a.status, a.fix) if op == "root-cause"
                   else set_fix_result(a.target, a.result, a.evidence, a.test))
        except ValueError as e:
            print(f"[recurrence-tracker] 거부: {e}", file=sys.stderr)
            return 2
        print(json.dumps(res, ensure_ascii=False))
        if op == "fix-result" and a.result == "passed" and res.get("result") != "passed":
            print("[recurrence-tracker] 시험 실패 — passed 대신 failed(FIX_FAILED) 로 기록함", file=sys.stderr)
            return 2
        return 0
    print(f"unknown op: {op}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print(f"[recurrence-tracker] fatal: {e}", file=sys.stderr)
        sys.exit(0)
