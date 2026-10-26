#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
verify-improvement — pre/post gate (A2).

사용:
  python verify-improvement.py start RULE_ID --metric 재발률 --value 40.0 --sample 10
  python verify-improvement.py finish IMP_ID --value 15.0 --sample 10
  python verify-improvement.py list

- start: pre_metric 측정 · recurrence_improvements INSERT (status=OBSERVING)
- finish: post_metric 측정 · 효과 계산 · verified=1 if 개선 (post < pre)
- list: 모든 improvement 상태
"""
from __future__ import annotations
import json, os, sqlite3, sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
DB = os.path.join(ROOT, ".claude", "state", "orca.db")


def cmd_start(args):
    rule_id = args[0]
    metric = _flag(args, "--metric", "unknown")
    direction = _flag(args, "--direction", "descending")  # defect #5 fix 2026-10-26
    if direction not in ("ascending", "descending"):
        print(f"[ERR] --direction 는 ascending|descending (지표가 올라야 좋은지 내려야 좋은지)", file=sys.stderr)
        sys.exit(2)
    value = float(_flag(args, "--value", "0") or 0)
    sample = int(_flag(args, "--sample", "0") or 0)
    plan = _flag(args, "--plan", "")
    cause = _flag(args, "--cause", "")
    now = datetime.now().isoformat(timespec="seconds")
    # metric + direction 을 problem_summary 에 함께 저장 (스키마 변경 없이 식별)
    summary = f"metric={metric}|direction={direction}|측정 전"
    with sqlite3.connect(DB) as c:
        cur = c.execute(
            "INSERT INTO recurrence_improvements "
            "(rule_id, problem_summary, root_cause, improvement_plan, "
            " pre_metric, pre_sample_size, pre_measured_at, status, ts_created, ts_updated) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'OBSERVING', ?, ?)",
            (rule_id, summary, cause, plan, value, sample, now, now, now)
        )
        imp_id = cur.lastrowid
    print(f"[OK] improvement #{imp_id} started · {rule_id} · {metric}={value} (n={sample}) · dir={direction} · OBSERVING")


def cmd_finish(args):
    imp_id = int(args[0])
    value = float(_flag(args, "--value", "0") or 0)
    sample = int(_flag(args, "--sample", "0") or 0)
    finish_metric = _flag(args, "--metric", "")  # defect #5: metric 일치 확인
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB) as c:
        row = c.execute(
            "SELECT pre_metric, rule_id, pre_sample_size, problem_summary FROM recurrence_improvements WHERE improvement_id=?",
            (imp_id,)
        ).fetchone()
        if not row:
            print(f"[ERR] improvement #{imp_id} 없음", file=sys.stderr)
            sys.exit(1)
        pre, rule_id, pre_sample, summary = row
        pre = pre or 0
        pre_sample = pre_sample or 0
        # defect #5 fix: metric name + direction 파싱
        start_metric = "unknown"
        direction = "descending"
        if summary and "|" in summary:
            for part in summary.split("|"):
                if part.startswith("metric="):
                    start_metric = part[7:]
                elif part.startswith("direction="):
                    direction = part[10:]
        # metric 일치 확인
        if finish_metric and finish_metric != start_metric:
            print(f"[ERR] metric 불일치 · start='{start_metric}' finish='{finish_metric}' — 동일 metric 로 측정해야 비교 유효", file=sys.stderr)
            sys.exit(2)
        # 지표 방향 반영
        if direction == "ascending":
            improved = value > pre  # 높을수록 좋음 (coverage·pass rate·throughput)
            delta = value - pre
        else:
            improved = value < pre  # 낮을수록 좋음 (재발률·오류·latency)
            delta = pre - value
        pct_change = (abs(delta) / pre * 100) if pre else 0
        sufficient_sample = sample >= 5 and pre_sample >= 5
        # defect #5 fix: pre 값 0 이면 비교 무의미 · VERIFIED 금지
        if pre <= 0:
            status = "OBSERVING"  # 기준값 없음 · 비교 불가
        elif improved and pct_change >= 10 and sufficient_sample:
            status = "VERIFIED"
        elif not improved:
            status = "REJECTED"
        else:
            status = "OBSERVING"  # 개선됐으나 표본·크기 부족
        verified = 1 if status == "VERIFIED" else 0
        c.execute(
            "UPDATE recurrence_improvements "
            "SET post_metric=?, post_sample_size=?, post_measured_at=?, "
            "    verified=?, status=?, ts_updated=? WHERE improvement_id=?",
            (value, sample, now, verified, status, now, imp_id)
        )
    icon = "✅" if verified else ("❌" if status == "REJECTED" else "⏳")
    print(f"[OK] improvement #{imp_id} finished · {rule_id} · pre={pre}→post={value} (Δ{delta:+.1f} / {pct_change:+.1f}%) · {icon} {status}")


def cmd_list(args):
    with sqlite3.connect(DB) as c:
        rows = c.execute(
            "SELECT improvement_id, rule_id, status, pre_metric, post_metric, verified, ts_updated "
            "FROM recurrence_improvements ORDER BY ts_updated DESC"
        ).fetchall()
    if not rows:
        print("improvements 0건")
        return
    print(f"improvements {len(rows)}건:")
    print(f"{'ID':>4} {'rule':<20} {'status':<10} {'pre':>8} {'post':>8} {'verified':<9} {'updated':<20}")
    for r in rows:
        pre = f"{r[3]:.1f}" if r[3] is not None else "?"
        post = f"{r[4]:.1f}" if r[4] is not None else "?"
        v = "✅" if r[5] else "⏳"
        print(f"{r[0]:>4} {r[1]:<20} {r[2]:<10} {pre:>8} {post:>8} {v:<9} {r[6]:<20}")


def _flag(args, flag, default=""):
    try:
        i = args.index(flag)
        return args[i + 1]
    except (ValueError, IndexError):
        return default


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    args = sys.argv[2:]
    if cmd == "start":
        cmd_start(args)
    elif cmd == "finish":
        cmd_finish(args)
    elif cmd == "list":
        cmd_list(args)
    else:
        print(f"unknown: {cmd}", file=sys.stderr)
        print("usage: verify-improvement.py {start|finish|list} ...", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
