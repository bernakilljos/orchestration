#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""memory-candidate.py — 08-learn 체인 memory 후보 생성 (2026-10-29).

사용자 아키텍처 (사용자 명시 2026-10-29):
  Workflow 실행 결과 → **Memory Candidate 생성** → 중복·품질·근거 검증 → **승인 정책에 따른 승격**
  **기존 ACTIVE Standing Requirements 자동 변경 금지**.

이 스크립트 역할:
  - 후보 **생성만** (파일 저장 · 자동 승격 X)
  - 저장 위치: `.claude/state/memory-candidates/<goal_id>-<ts>.md`
  - 실 memory (`~/.claude/projects/<proj>/memory/*.md`) 반영은 **별도 승인 명령 (promote)** 만

CLI:
  python memory-candidate.py --goal <goal_id> --outcome <success|partial|fail|halted>
  python memory-candidate.py list                 # 모든 후보 조회
  python memory-candidate.py show <candidate_id>  # 후보 상세
  python memory-candidate.py promote <candidate_id> --target <feedback|project|reference|user>
      # 사용자 명시 승인 후만 실제 memory/ 디렉토리로 이동

안전 장치:
  - 중복 (content_hash 동일) 후보 생성 X
  - Standing Requirements 자동 변경 X (별도 standing-requirements.py add 호출 필요)
  - promote 시 target type 명시 필수 (추측 금지)
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
CAND_DIR = ROOT / ".claude" / "state" / "memory-candidates"
CAND_DIR.mkdir(parents=True, exist_ok=True)
STATE_DB = ROOT / ".claude" / "state" / "orca.db"


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _goal_info(goal_id: str) -> dict:
    """orca.db.goals 에서 goal 메타 조회."""
    if not STATE_DB.exists():
        return {}
    try:
        conn = sqlite3.connect(STATE_DB)
        cur = conn.cursor()
        row = cur.execute(
            "SELECT description, status, failure_reason, workflow_type FROM goals WHERE goal_id=?",
            (goal_id,),
        ).fetchone()
        conn.close()
        if not row:
            return {}
        return {
            "description": row[0] or "",
            "status": row[1] or "",
            "failure_reason": row[2] or "",
            "workflow_type": row[3] or "",
        }
    except Exception as e:
        return {"error": str(e)}


def _classify(outcome: str, goal: dict) -> str:
    """outcome + goal 로부터 memory type 추천 (feedback/project/reference/user).

    자동 승격 금지 — 추천만. 사용자 명시 승인 후 promote 로 반영.
    """
    status = (goal.get("status") or "").upper()
    desc = (goal.get("description") or "").lower()
    if outcome in ("fail", "halted"):
        return "feedback"  # 실패 교훈 → feedback
    if "repair" in desc or "재발" in desc:
        return "feedback"
    if "research" in desc or "websearch" in desc:
        return "reference"
    if "pm" in desc or "project" in desc or "roadmap" in desc:
        return "project"
    return "feedback"  # default


def generate(goal_id: str, outcome: str) -> dict:
    """후보 생성 — 파일 저장 · 자동 승격 X."""
    goal = _goal_info(goal_id)
    if not goal:
        return {"ok": False, "reason": f"goal {goal_id} not found in orca.db"}
    if "error" in goal:
        return {"ok": False, "reason": goal["error"]}

    recommended_type = _classify(outcome, goal)
    content = (
        f"# Memory Candidate — goal {goal_id}\n\n"
        f"**Generated**: {datetime.now().isoformat(timespec='seconds')}\n"
        f"**Outcome**: {outcome}\n"
        f"**Recommended type**: {recommended_type}\n"
        f"**Status**: PENDING_APPROVAL (사용자 승인 후 promote 로 반영)\n\n"
        f"## Goal 메타\n"
        f"- description: {goal.get('description','')[:300]}\n"
        f"- status: {goal.get('status','')}\n"
        f"- workflow_type: {goal.get('workflow_type','')}\n"
        f"- failure_reason: {goal.get('failure_reason','')[:200]}\n\n"
        f"## 자동 승격 금지\n"
        f"이 후보는 사용자 명시 `promote` 명령 전까지 memory 디렉토리에 반영되지 않는다.\n"
        f"Standing Requirements 자동 변경 X · ACTIVE 상태 보존.\n"
    )

    chash = _hash(content)
    # 중복 체크
    for existing in CAND_DIR.glob("*.md"):
        try:
            if _hash(existing.read_text(encoding="utf-8")) == chash:
                return {"ok": True, "status": "duplicate", "path": str(existing), "hash": chash}
        except Exception:
            pass

    ts = int(time.time())
    out_path = CAND_DIR / f"g{goal_id}-{ts}.md"
    out_path.write_text(content, encoding="utf-8")
    return {
        "ok": True,
        "status": "generated",
        "path": str(out_path),
        "hash": chash,
        "recommended_type": recommended_type,
        "note": "promote 호출 전까지 memory/ 디렉토리 반영 X",
    }


def list_candidates() -> list:
    out = []
    for p in sorted(CAND_DIR.glob("*.md")):
        try:
            stat = p.stat()
            out.append({
                "id": p.stem,
                "path": str(p),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            })
        except Exception:
            pass
    return out


def show(cand_id: str) -> dict:
    p = CAND_DIR / f"{cand_id}.md"
    if not p.exists():
        return {"ok": False, "reason": f"candidate {cand_id} not found"}
    return {"ok": True, "id": cand_id, "content": p.read_text(encoding="utf-8")}


def promote(cand_id: str, target: str) -> dict:
    """사용자 명시 승인 후 memory/ 디렉토리로 이동.

    target: feedback | project | reference | user
    """
    if target not in ("feedback", "project", "reference", "user"):
        return {"ok": False, "reason": f"invalid target: {target} (feedback|project|reference|user)"}

    src = CAND_DIR / f"{cand_id}.md"
    if not src.exists():
        return {"ok": False, "reason": f"candidate {cand_id} not found"}

    # memory 디렉토리는 user 환경별 다름 — 기본 ~/.claude/projects/<proj>/memory/
    proj_name = ROOT.name  # 폴더명 (예: orchestration_v1)
    user_mem = Path.home() / ".claude" / "projects" / f"C--pjt-{proj_name}" / "memory"
    user_mem.mkdir(parents=True, exist_ok=True)

    # Candidate 이름을 {target}_{cand_id}.md 로 (안전)
    dst = user_mem / f"{target}_{cand_id}.md"
    if dst.exists():
        return {"ok": False, "reason": f"target already exists: {dst}"}

    # 이동 (복사 후 원본 삭제 — 다시 generate 안 되게)
    content = src.read_text(encoding="utf-8")
    # Standing Requirements 자동 추가 금지 안전 장치
    if "STANDING_REQUIREMENT" in content:
        return {"ok": False, "reason": "candidate contains STANDING_REQUIREMENT · 자동 승격 금지 (standing-requirements.py add 수동)"}
    dst.write_text(content, encoding="utf-8")
    src.unlink()
    return {"ok": True, "status": "promoted", "from": str(src), "to": str(dst), "target_type": target}


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")

    # default: generate (--goal --outcome)
    ap.add_argument("--goal", default=None)
    ap.add_argument("--outcome", default="success", choices=["success", "partial", "fail", "halted"])

    p_list = sub.add_parser("list")
    p_show = sub.add_parser("show"); p_show.add_argument("cand_id")
    p_prom = sub.add_parser("promote"); p_prom.add_argument("cand_id"); p_prom.add_argument("--target", required=True)

    args = ap.parse_args()

    if args.cmd == "list":
        print(json.dumps(list_candidates(), ensure_ascii=False, indent=2))
    elif args.cmd == "show":
        print(json.dumps(show(args.cand_id), ensure_ascii=False, indent=2))
    elif args.cmd == "promote":
        print(json.dumps(promote(args.cand_id, args.target), ensure_ascii=False, indent=2))
    else:
        # default: generate
        if not args.goal:
            print(json.dumps({"ok": False, "reason": "--goal required for generate"}, ensure_ascii=False))
            return 2
        print(json.dumps(generate(args.goal, args.outcome), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
