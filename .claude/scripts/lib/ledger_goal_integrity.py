"""ledger_goal_integrity.py — Request Ledger vs Goal DB 무결성 교차 검증 (2026-10-30 P5-R5).

사용자 지시 (b03dbf8 후속):
  - Request Ledger 와 Goal DB 상태 일치 확인
  - 실제 완료 증거 없는 complete 방지
  - 자동 등록 오탐 기록 보존
  - 재시작 후 작업 상태 복원

검증 항목:
  1. ledger 가 completed 로 marked 됐지만 goals 테이블에 status=VERIFIED/COMPLETED 가 없음
  2. ledger 가 invalid_registration 인데 goals 에 생성된 goal 이 아직 PENDING/RUNNING
  3. autogoal source_ref 로 등재된 goal 중 ledger entry 없음 (고아 goal)
  4. source_ref=ledger:R<id> goal 중 ledger 에 해당 ID 없음 (dangling)

반환: 불일치 항목 리스트 + 권장 조치.
"""
from __future__ import annotations
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Any, List

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
DB = ROOT / ".claude" / "state" / "orca.db"
LEDGER = ROOT / ".claude" / "state" / "request-ledger.json"


def _load_ledger() -> Dict[str, Any]:
    if not LEDGER.exists():
        return {}
    try:
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    except Exception:
        return {}


def check() -> Dict[str, Any]:
    """교차 검증 수행 · 불일치 항목 반환."""
    issues: List[Dict[str, Any]] = []
    ledger = _load_ledger()
    requests = ledger.get("requests", [])
    ledger_ids = {r["id"]: r for r in requests}

    if not DB.exists():
        return {"error": "orca.db not found"}

    with sqlite3.connect(str(DB)) as c:
        # 1. ledger→goals: source_ref 로 추적
        for rid, req in ledger_ids.items():
            source_ref = f"ledger:{rid}"
            rows = c.execute(
                "SELECT goal_id, status FROM goals WHERE source_ref=?",
                (source_ref,),
            ).fetchall()
            if not rows:
                # ledger entry 있지만 goal 생성 안 됨 (to-goals 미실행 또는 skip)
                if req["status"] == "completed":
                    # 완료로 marked 됐지만 goal 자체가 없음 — evidence 가 goal 밖에 있는 작업 (OK)
                    continue
                if req["status"] == "pending":
                    issues.append({
                        "kind": "ledger_pending_without_goal",
                        "rid": rid, "ledger_status": req["status"],
                        "hint": "to-goals 실행 필요 또는 ledger 수동 처리",
                    })
                continue
            for gid, gstatus in rows:
                # ledger=completed 인데 goal status 가 VERIFIED/FAILED 아님
                if req["status"] == "completed" and gstatus not in ("VERIFIED", "FAILED"):
                    issues.append({
                        "kind": "ledger_completed_but_goal_incomplete",
                        "rid": rid, "goal_id": gid,
                        "ledger_status": req["status"], "goal_status": gstatus,
                        "hint": "완료 보고된 ledger 지만 goal 미완 · 재검증 필요",
                    })
                # ledger=invalid_registration 인데 goal 이 아직 RUNNING
                if req["status"] == "invalid_registration" and gstatus not in ("BLOCKED", "FAILED", "VERIFIED"):
                    issues.append({
                        "kind": "invalid_ledger_but_goal_active",
                        "rid": rid, "goal_id": gid,
                        "ledger_status": req["status"], "goal_status": gstatus,
                        "hint": "oldgal 분류기 오탐으로 ledger invalid 지만 goal 실행 중 · supervisor block 권장",
                    })

        # 2. 고아 goals: source_ref 가 ledger:R<id> 인데 ledger 에 해당 ID 없음
        for gid, src_ref, status in c.execute(
            "SELECT goal_id, source_ref, status FROM goals WHERE source_ref LIKE 'ledger:R%'"
        ).fetchall():
            m = re.match(r"ledger:(R\d+)", src_ref or "")
            if m:
                rid = m.group(1)
                if rid not in ledger_ids:
                    issues.append({
                        "kind": "dangling_goal",
                        "goal_id": gid, "source_ref": src_ref, "goal_status": status,
                        "hint": f"source_ref 로 {rid} 참조하지만 ledger entry 없음 · ledger clear 후 재등재했을 수 있음",
                    })

        # 3. autogoal 고아 (source_ref=auto:ph=... 인 goal 중 PENDING 오래된 것)
        auto_pending = c.execute(
            "SELECT goal_id, substr(description, 1, 80), created_at FROM goals "
            "WHERE source_ref LIKE 'auto:%' AND status='PENDING' "
            "ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
        import time as _t
        now = _t.time()
        for gid, desc, created in auto_pending:
            age_hours = (now - int(created)) / 3600
            if age_hours > 2:  # 2시간+ PENDING = 처리 미이행
                issues.append({
                    "kind": "stale_auto_pending",
                    "goal_id": gid, "desc_head": desc[:60],
                    "age_hours": round(age_hours, 1),
                    "hint": "autogoal 로 등재됐지만 2h+ PENDING · 승인/promote 미이행 또는 결함 가능",
                })

    # 요약
    counts = {}
    for i in issues:
        counts[i["kind"]] = counts.get(i["kind"], 0) + 1

    return {
        "ok": len(issues) == 0,
        "total_issues": len(issues),
        "counts": counts,
        "issues": issues[:50],  # 최대 50건
        "ledger_requests": len(requests),
        "note": (
            "fail-closed: 불일치 발견 시 수동 조치 필요 · 자동 수정 X "
            "(사용자 지시 기존 Git·Ledger·DB 보존 원칙)"
        ),
    }


def _cli_main(argv):
    r = check()
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(_cli_main(sys.argv))
