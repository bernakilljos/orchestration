#!/usr/bin/env python
"""
standing-requirements.py — Persistent Requirement Registry (SoT).

근거: 2026-10-16 사용자 지적 "저장 ≠ 재주입" — conversation 저장만으로는 다음 세션 반영 X.

구조:
- 지속 요구사항 (STANDING_REQUIREMENT): 앞으로 매 세션 자동 적용 (statusline 라인·디자인 규칙 등)
- 일회성 (CURRENT_TASK): 이번 요청만 (Request Ledger 로 관리)

CLI:
  python standing-requirements.py add <id> <type> <rule>   # 등록
  python standing-requirements.py list [--active]           # 조회
  python standing-requirements.py replay                    # SessionStart 용 systemMessage (JSON)
  python standing-requirements.py gate                      # Stop hook — ACTIVE 반영 여부 체크
  python standing-requirements.py resolve <id>              # ACTIVE → RESOLVED
  python standing-requirements.py disable <id>              # 임시 비활성

저장:
  .claude/state/standing-requirements.json
  {
    "UX-STATUS-007": {
      "type": "STANDING_REQUIREMENT",
      "status": "ACTIVE",
      "source": "USER_EXPLICIT",
      "rule": "품질추세 라인을 statusline 에 유지",
      "verify_pattern": "품질추세",
      "verify_target": ".claude/scripts/statusline_context.py",
      "created_at": "...",
      "last_verified_at": "..."
    }
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
STORE = ROOT / ".claude" / "state" / "standing-requirements.json"


def _load() -> dict:
    if not STORE.exists():
        return {}
    try:
        return json.loads(STORE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_add(rid: str, rtype: str, rule: str, verify_pattern: str = "", verify_target: str = "") -> int:
    data = _load()
    data[rid] = {
        "type": rtype,
        "status": "ACTIVE",
        "source": "USER_EXPLICIT",
        "rule": rule,
        "verify_pattern": verify_pattern,
        "verify_target": verify_target,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "last_verified_at": None,
    }
    _save(data)
    print(f"[req] + {rid} [{rtype}] ACTIVE: {rule[:80]}")
    return 0


def cmd_list(active_only: bool = False) -> int:
    data = _load()
    if not data:
        print("[req] empty")
        return 0
    for rid, r in data.items():
        if active_only and r.get("status") != "ACTIVE":
            continue
        print(f"  [{r['status']}] {rid} ({r['type']}): {r['rule'][:100]}")
    return 0


def _verify(r: dict) -> "str":
    """verify_pattern 이 verify_target 안에 존재하는지.

    P0a-C: 2026-10-28 CRITICAL #3 fix.
    기존 verify_pattern 없으면 True 자동 반환 — gate 무력화 결함.
    이제 3-state 반환: 'PASS' / 'FAIL' / 'UNKNOWN'.
    UNKNOWN 은 gate 에서 PASS 로 간주 X · 수동 검증 요구 flag 로 처리.
    """
    tgt = r.get("verify_target", "")
    pat = r.get("verify_pattern", "")
    if not tgt or not pat:
        return "UNKNOWN"  # 검증 패턴 미제공 — 자동 True X · gate 가 수동 확인 요구
    p = ROOT / tgt
    if not p.exists():
        return "FAIL"
    try:
        return "PASS" if pat in p.read_text(encoding="utf-8", errors="ignore") else "FAIL"
    except Exception:
        return "FAIL"


def cmd_replay() -> int:
    """SessionStart hook 용. ACTIVE requirements 를 systemMessage JSON 으로 출력."""
    data = _load()
    active = [(rid, r) for rid, r in data.items() if r.get("status") == "ACTIVE"]
    if not active:
        return 0
    lines = ["# ACTIVE Standing Requirements (매 세션 재주입 · 작업 전 대조)"]
    lines.append("")
    for rid, r in active:
        lines.append(f"- **{rid}** ({r['type']}): {r['rule']}")
    lines.append("")
    lines.append("**금지**: 이 중 하나라도 생략한 채 작업 완료 보고 X. Stop gate 가 재검사.")
    msg = "\n".join(lines)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": msg,
        }
    }, ensure_ascii=False))
    return 0


def cmd_gate() -> int:
    """Stop hook 용. ACTIVE requirements 중 verify FAIL 있으면 exit 2."""
    data = _load()
    active = [(rid, r) for rid, r in data.items() if r.get("status") == "ACTIVE"]
    if not active:
        return 0
    failed = []
    unknown = []
    for rid, r in active:
        result = _verify(r)
        if result == "PASS":
            r["last_verified_at"] = datetime.now().isoformat(timespec="seconds")
        elif result == "FAIL":
            failed.append((rid, r))
        else:  # UNKNOWN — verify_pattern 미제공 (P0a-C fix: 자동 True X)
            unknown.append((rid, r))
    _save(data)
    if not failed and not unknown:
        return 0
    msg = f"[standing-req] {len(active)-len(failed)-len(unknown)}/{len(active)} 유지"
    if failed:
        msg += f" · 누락 {len(failed)}건"
    if unknown:
        msg += f" · 미검증 {len(unknown)}건 (verify_pattern 미제공 · 수동 확인 요구)"
    msg += ":\n"
    for rid, r in failed[:5]:
        msg += f"  ✗ {rid}: {r['rule'][:80]}\n"
    for rid, r in unknown[:3]:
        msg += f"  ⏳ {rid} (UNKNOWN · verify_pattern 추가 필요): {r['rule'][:70]}\n"
    msg += "→ ACTIVE standing requirement 복원 후 완료 (Stop 차단)"
    print(msg, file=sys.stderr)
    # FAIL 이 있거나 UNKNOWN 이 있어도 exit 2 (fail-closed)
    return 2


def cmd_resolve(rid: str) -> int:
    data = _load()
    if rid not in data:
        print(f"[req] {rid} not found", file=sys.stderr)
        return 2
    data[rid]["status"] = "RESOLVED"
    data[rid]["resolved_at"] = datetime.now().isoformat(timespec="seconds")
    _save(data)
    print(f"[req] ✓ {rid} RESOLVED")
    return 0


def cmd_disable(rid: str) -> int:
    data = _load()
    if rid not in data:
        print(f"[req] {rid} not found", file=sys.stderr)
        return 2
    data[rid]["status"] = "DISABLED"
    _save(data)
    print(f"[req] - {rid} DISABLED")
    return 0


def cmd_stats() -> dict:
    data = _load()
    total = len(data)
    active = sum(1 for r in data.values() if r.get("status") == "ACTIVE")
    failed = sum(1 for r in data.values() if r.get("status") == "ACTIVE" and not _verify(r))
    return {"total": total, "active": active, "failed": failed, "ok": active - failed}


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="op")
    p_add = sub.add_parser("add")
    p_add.add_argument("rid")
    p_add.add_argument("rtype", choices=["STANDING_REQUIREMENT", "CURRENT_TASK", "PREFERENCE"])
    p_add.add_argument("rule")
    p_add.add_argument("--verify-pattern", default="")
    p_add.add_argument("--verify-target", default="")
    p_list = sub.add_parser("list")
    p_list.add_argument("--active", action="store_true")
    sub.add_parser("replay")
    sub.add_parser("gate")
    sub.add_parser("stats")
    p_res = sub.add_parser("resolve")
    p_res.add_argument("rid")
    p_dis = sub.add_parser("disable")
    p_dis.add_argument("rid")
    args = ap.parse_args()
    if args.op == "add":
        return cmd_add(args.rid, args.rtype, args.rule, args.verify_pattern, args.verify_target)
    if args.op == "list":
        return cmd_list(args.active)
    if args.op == "replay":
        return cmd_replay()
    if args.op == "gate":
        return cmd_gate()
    if args.op == "stats":
        print(json.dumps(cmd_stats(), ensure_ascii=False))
        return 0
    if args.op == "resolve":
        return cmd_resolve(args.rid)
    if args.op == "disable":
        return cmd_disable(args.rid)
    ap.print_help()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[standing-req] fatal: {e}", file=sys.stderr)
        sys.exit(0)
