#!/usr/bin/env python
"""
request-ledger.py — Request Ledger SoT (요청 원장).

근거: 외부 감사 2026-10-16 · execution-contract.md § 1 "n/n 완료 강제".

문제: 사용자 "A·B·C 다 해" → Claude 가 A만 하고 보고 → 사용자 재지시 반복.
해결: 사용자 메시지에서 N 개 request 추출 → ledger 저장 → N/N 완료 전 Stop 차단.

CLI:
  python request-ledger.py add <description> [--session <id>]  # 1개 request 등록
  python request-ledger.py add-batch <json>                     # 여러 개 등록
  python request-ledger.py complete <id>                        # 완료 체크
  python request-ledger.py status                               # 현재 ledger
  python request-ledger.py gate                                 # Stop hook 용 (exit 0=all done, exit 2=incomplete)
  python request-ledger.py clear                                # 전체 비우기 (사용자 명시 시)

저장:
  .claude/state/request-ledger.json
  {
    "session_id": "...",
    "created_at": "...",
    "requests": [
      {"id": "R1", "desc": "...", "status": "pending|completed", "ts": "..."},
      ...
    ]
  }
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
LEDGER = ROOT / ".claude" / "state" / "request-ledger.json"


def _load() -> dict:
    if not LEDGER.exists():
        return {}
    try:
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _next_id(requests: list) -> str:
    return f"R{len(requests) + 1}"


def _idempotency_key(desc: str, session: str = "") -> str:
    """멱등성 키 — 같은 desc 24h 안 재수신 중복 등록 방지 (사용자 지시 2026-10-28)."""
    import hashlib
    norm = (desc or "").strip().lower()[:300]
    base = f"{norm}|{session or 'unknown'}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


def cmd_add(desc: str, session: str = "", idempotency_window_h: int = 24) -> int:
    """사용자 지시 등록 — append-only + 멱등성 체크 (중복 skip)."""
    data = _load()
    if not data:
        data = {
            "session_id": session or "unknown",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "requests": [],
        }
    key = _idempotency_key(desc, session)
    import datetime as _dt
    cutoff = (datetime.now() - _dt.timedelta(hours=idempotency_window_h)).isoformat(timespec="seconds")
    for r in data["requests"]:
        if r.get("idempotency_key") == key and r.get("ts", "") > cutoff:
            print(f"[ledger] = {r.get('id')} (duplicate · idempotency_key · skipped)")
            return 0
    rid = _next_id(data["requests"])
    data["requests"].append({
        "id": rid,
        "desc": desc[:200],
        "status": "pending",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "idempotency_key": key,
    })
    _save(data)
    print(f"[ledger] + {rid}: {desc[:80]}")
    return 0


def cmd_add_batch(json_str: str) -> int:
    try:
        items = json.loads(json_str)
    except Exception as e:
        print(f"[ledger] JSON parse error: {e}", file=sys.stderr)
        return 2
    if not isinstance(items, list):
        print("[ledger] expected JSON array", file=sys.stderr)
        return 2
    data = _load() or {
        "session_id": "batch",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "requests": [],
    }
    for d in items:
        rid = _next_id(data["requests"])
        data["requests"].append({
            "id": rid,
            "desc": str(d)[:200],
            "status": "pending",
            "ts": datetime.now().isoformat(timespec="seconds"),
        })
    _save(data)
    print(f"[ledger] + {len(items)} requests · total {len(data['requests'])}")
    return 0


def cmd_complete(rid: str, evidence: str = "", verification: str = "") -> int:
    """4단계: pending → implemented → verified → completed · 증거 필수 (2026-10-16 외부 감사)."""
    data = _load()
    if not data:
        print("[ledger] empty", file=sys.stderr)
        return 2
    for r in data["requests"]:
        if r["id"] == rid or r["id"].lower() == rid.lower():
            # 증거 없으면 implemented 로만 (completed 불허)
            if not evidence:
                r["status"] = "implemented"
                r["note"] = "evidence 없음 · completed 대신 implemented (뻥 완료 방지)"
                _save(data)
                print(f"[ledger] ⚠ {rid}: implemented (evidence 미제공 — completed 보류)", file=sys.stderr)
                return 1
            if verification and verification.upper() != "PASS":
                r["status"] = "verified"
                r["evidence"] = evidence[:500]
                r["verification"] = verification
                _save(data)
                print(f"[ledger] ⚠ {rid}: verified (verification={verification} · PASS 아님)", file=sys.stderr)
                return 1
            r["status"] = "completed"
            r["completed_at"] = datetime.now().isoformat(timespec="seconds")
            r["evidence"] = evidence[:500]
            r["verification"] = verification or "PASS"
            _save(data)
            print(f"[ledger] ✓ {rid}: {r['desc'][:60]} · evidence 확보")
            return 0
    print(f"[ledger] {rid} not found", file=sys.stderr)
    return 2


def cmd_status() -> int:
    data = _load()
    if not data:
        print("[ledger] empty")
        return 0
    total = len(data["requests"])
    done = sum(1 for r in data["requests"] if r["status"] in ("completed", "deferred"))  # deferred = 사용자 명시 다음 세션 지연
    print(f"=== Request Ledger · {done}/{total} 완료 ===")
    for r in data["requests"]:
        mark = "✓" if r["status"] == "completed" else "☐"
        print(f"  {mark} {r['id']}: {r['desc'][:100]}")
    return 0


def cmd_gate() -> int:
    """Stop hook용. exit 0 = all done · exit 2 = incomplete (block Stop)."""
    data = _load()
    if not data or not data.get("requests"):
        return 0  # ledger 없음 = 통과
    # 2026-10-16: 시험이 남긴 ledger(session_id "test") 하나가 모든 세션의 Stop 을 막았다.
    #   시험 기록과 오래된 기록(지난 작업)은 이번 세션의 미완이 아니다 → 통과.
    # BASIS: agreed(2026-10-16, 한 세션의 요청 묶음은 몇 시간 안에 끝난다 — 6시간 넘게 안 바뀐 ledger 는 지난 작업.
    #   한계: 6시간 넘게 이어지는 긴 작업의 미완은 놓친다. 그때는 시각이 아니라 세션 id 대조로 바꾼다.)
    STALE_SEC = 6 * 3600
    import time as _t
    if data.get("session_id") == "test" or _t.time() - LEDGER.stat().st_mtime > STALE_SEC:
        print("[request-ledger] 시험·지난 작업 ledger — 이번 세션 기준 아님 · 통과", file=sys.stderr)
        return 0
    total = len(data["requests"])
    done = sum(1 for r in data["requests"] if r["status"] in ("completed", "deferred"))  # deferred = 사용자 명시 다음 세션 지연
    if done == total:
        return 0  # 모두 완료 = 통과
    # 미완료 있음 — Claude 에게 알림
    pending = [r for r in data["requests"] if r["status"] != "completed"]
    msg = f"[request-ledger] {done}/{total} 완료 · 미완료 {len(pending)}건:\n"
    for r in pending[:5]:
        msg += f"  ☐ {r['id']}: {r['desc'][:80]}\n"
    msg += "→ 미완료 request 계속 실행 후 보고 (execution-contract § 2 n/n 완료 전 보고 금지)"
    print(msg, file=sys.stderr)
    return 2


def cmd_clear() -> int:
    if LEDGER.exists():
        LEDGER.unlink()
    print("[ledger] cleared")
    return 0


def cmd_to_goals() -> int:
    """pending Ledger entries → Supervisor create_goal 자동 변환 (사용자 지시 2026-10-28).
    각 request 는 request_id 를 goal source_ref 에 저장 → 역추적 가능.
    기존 goal 보존 (덮어쓰기 X) · idempotency 는 ledger 에서 이미 처리됨."""
    data = _load()
    if not data:
        print("[ledger→goal] no ledger")
        return 1
    import sqlite3
    sup_db = ROOT / ".claude" / "state" / "orca.db"
    created = 0
    skipped = 0
    with sqlite3.connect(str(sup_db)) as c:
        for r in data.get("requests", []):
            if r.get("status") != "pending":
                continue
            rid = r.get("id")
            desc = r.get("desc") or ""
            source_ref = f"ledger:{rid}"
            # 기존 goal 중 같은 source_ref 있나 (idempotency)
            exist = c.execute("SELECT goal_id FROM goals WHERE source_ref=?",
                             (source_ref,)).fetchone()
            if exist:
                skipped += 1
                continue
            import time as _t
            now = int(_t.time())
            c.execute(
                "INSERT INTO goals (description, status, workflow_type, source_ref, "
                "max_retry, timeout_h, created_at, updated_at) "
                "VALUES (?, 'PENDING', 'GENERAL', ?, 3, 24, ?, ?)",
                (f"[{rid}] {desc}", source_ref, now, now)
            )
            created += 1
    print(f"[ledger→goal] created={created} skipped_existing={skipped}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="op")

    p_add = sub.add_parser("add")
    p_add.add_argument("desc")
    p_add.add_argument("--session", default="")

    p_batch = sub.add_parser("add-batch")
    p_batch.add_argument("json_str")

    p_comp = sub.add_parser("complete")
    p_comp.add_argument("rid")
    p_comp.add_argument("--evidence", default="", help="실제 수행 증거 (git diff·실행 결과·파일 경로)")
    p_comp.add_argument("--verification", default="", help="검증 결과 (PASS·FAIL)")

    sub.add_parser("status")
    sub.add_parser("gate")
    sub.add_parser("clear")
    sub.add_parser("to-goals")

    args = ap.parse_args()
    if args.op == "add":
        return cmd_add(args.desc, args.session)
    if args.op == "add-batch":
        return cmd_add_batch(args.json_str)
    if args.op == "complete":
        return cmd_complete(args.rid, args.evidence, args.verification)
    if args.op == "status":
        return cmd_status()
    if args.op == "gate":
        return cmd_gate()
    if args.op == "clear":
        return cmd_clear()
    if args.op == "to-goals":
        return cmd_to_goals()
    ap.print_help()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[request-ledger] fatal: {e}", file=sys.stderr)
        sys.exit(0)
