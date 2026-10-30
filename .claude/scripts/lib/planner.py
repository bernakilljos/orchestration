"""planner.py — 범용 Planner (2026-10-29 Phase 2-D).

사용자 지시 (391e691 후속):
  - SAFE_PATTERNS 증설 X (어휘 매칭 기반 자동 cmd 생성 금지)
  - LLM 이 작성한 임의 명령 즉시 Shell 실행 X
  - 승인 정책과 검증 가능한 작업 계약 통과 후만 실행
  - 기존 Agent/LLM/Router/Supervisor 자산 재사용

역할 분리:
  1. **investigate** — 코드베이스 조사 (Grep/Glob 기반, LLM 아님, 안전)
     goal description 안 키워드로 관련 파일 수집 · 조사 보고서 생성
  2. **propose** — Task 계약 제안 저장 (외부: Claude Code Task tool · Agent SDK · 사용자)
     이 모듈은 proposal 을 받아 planner_proposals 테이블에 저장
     SAFE_PATTERNS 매칭 자동 생성 X — 외부 (LLM 또는 사용자) 가 명시 제출
  3. **approve/reject** — HITL 승인 흐름
  4. **promote** — approved proposals → supervisor tasks (safe_mode default)

안전 default:
  - 모든 approved proposal 은 safe_mode=True (worktree 격리 강제)
  - requires_user_approval=True default (명시 low 만 자동 허용)
  - risk=unknown 자동 변환 X (사용자 명시)
  - 승인 정책 통과 체크 (approval-gate)

사용:
  python planner.py investigate <goal_id>              # 조사 보고서 생성 (Grep/Glob)
  python planner.py propose <goal_id> <spec_json>      # Task 계약 제안
  python planner.py list [--goal G] [--status S]
  python planner.py approve <proposal_id>
  python planner.py reject <proposal_id> [--reason R]
  python planner.py promote <goal_id>                  # approved → tasks
"""
from __future__ import annotations
import json
import os
import re
import sqlite3
import sys
import time
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
DB = ROOT / ".claude" / "state" / "orca.db"
VALID_PROPOSAL_STATUS = ("pending", "approved", "rejected", "promoted", "superseded")


def ensure_schema() -> None:
    """planner_proposals 테이블 생성 (idempotent)."""
    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(DB)) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS planner_proposals (
                proposal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                sequence INTEGER DEFAULT 0,
                spec_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                origin TEXT,
                risk TEXT,
                requires_user_approval INTEGER DEFAULT 1,
                created_at INTEGER NOT NULL,
                approved_at INTEGER,
                approved_by TEXT,
                rejected_at INTEGER,
                reject_reason TEXT,
                promoted_at INTEGER,
                promoted_task_id TEXT,
                notes TEXT
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_pp_goal ON planner_proposals(goal_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_pp_status ON planner_proposals(status)")


# ========== 1. INVESTIGATE (코드베이스 조사 · LLM 아님) ==========

_KEYWORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_\-]{2,}|[가-힣]{2,}")
_STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "goal", "task",
    "하기", "하는", "입니다", "되는", "되면", "같은", "그리고", "이것", "저것",
    "please", "then", "when", "where", "should",
}


def _extract_keywords(text: str, max_count: int = 12) -> List[str]:
    """description 에서 조사용 키워드 추출 (LLM 아님 · regex)."""
    if not text:
        return []
    toks = _KEYWORD_RE.findall(text)
    seen = []
    for t in toks:
        tl = t.lower()
        if tl in _STOPWORDS:
            continue
        if len(t) < 3:
            continue
        if t not in seen:
            seen.append(t)
        if len(seen) >= max_count:
            break
    return seen


def _grep_scan(keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
    """ripgrep 또는 git grep 으로 키워드 scan · 결과 limit."""
    results: List[Dict[str, Any]] = []
    tried = []
    for cmd_variant in (
        ["rg", "-n", "--max-count", "3", "-S", keyword,
         "--glob", "!node_modules", "--glob", "!.git", "--glob", "!.repair-sandbox"],
        ["git", "grep", "-n", "-I", "--", keyword],
    ):
        tried.append(cmd_variant[0])
        try:
            r = subprocess.run(
                cmd_variant, cwd=str(ROOT), capture_output=True, text=True,
                timeout=20, encoding="utf-8", errors="replace",
                env={**os.environ, "ALLOW_VISIBLE_WINDOW": "1"},
            )
            if r.returncode in (0, 1):  # 0 = match · 1 = no match (grep 관례)
                lines = (r.stdout or "").splitlines()[:limit]
                for ln in lines:
                    results.append({"line": ln[:300]})
                return results
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return [{"line": f"[scan skipped — tools not available: {tried}]"}]


def _glob_scan(pattern: str, limit: int = 30) -> List[str]:
    """Glob (Path.rglob)."""
    out = []
    try:
        for p in ROOT.rglob(pattern):
            if any(seg in {".git", "node_modules", ".repair-sandbox", "__pycache__"}
                   for seg in p.parts):
                continue
            rel = p.relative_to(ROOT).as_posix()
            out.append(rel)
            if len(out) >= limit:
                break
    except Exception:
        pass
    return out


def investigate(goal_id: int, max_keywords: int = 8) -> Dict[str, Any]:
    """goal 1건의 코드베이스 조사 보고서 생성 (LLM 아님 · Grep/Glob).

    생성물:
      - keywords: 추출된 조사 키워드
      - scan: 키워드별 grep 결과 (파일:라인)
      - related_files: 추측되는 관련 파일 목록
      - prompt_template: LLM/Claude Code Task tool 호출용 prompt (별도 수동)

    이 함수는 Task 계약 (cmd) 을 자동 생성하지 않음.
    외부 (LLM 또는 사용자) 가 proposal() 로 명시 제출.
    """
    ensure_schema()
    if not DB.exists():
        return {"error": "orca.db not found"}
    with sqlite3.connect(str(DB)) as c:
        row = c.execute(
            "SELECT description, status FROM goals WHERE goal_id=?",
            (goal_id,),
        ).fetchone()
    if not row:
        return {"error": f"goal {goal_id} not found"}
    desc, status = row[0] or "", row[1]

    keywords = _extract_keywords(desc, max_count=max_keywords)
    scan_results = {}
    related_files = set()
    for kw in keywords:
        hits = _grep_scan(kw, limit=10)
        scan_results[kw] = hits
        for h in hits:
            m = re.match(r"^([^:]+):\d+:", h.get("line", ""))
            if m:
                related_files.add(m.group(1))

    prompt_template = _render_prompt_template(goal_id, desc, keywords, list(related_files)[:30])

    return {
        "goal_id": goal_id,
        "goal_status": status,
        "description_head": desc[:300],
        "keywords": keywords,
        "scan": scan_results,
        "related_files": sorted(related_files)[:30],
        "prompt_template": prompt_template,
        "note": (
            "이 조사 보고서는 Grep/Glob 기반 · 자동 cmd 생성 X · "
            "LLM/사용자가 propose() 로 명시 Task 계약 제출 필요."
        ),
    }


def _render_prompt_template(goal_id: int, description: str,
                            keywords: List[str], files: List[str]) -> str:
    """Claude Code Task tool (general-purpose subagent) 호출용 prompt 생성.

    사용자 명시: "LLM 이 작성한 임의 명령을 즉시 Shell 로 실행하지 마라".
    → prompt 결과 (Task 계약 JSON) 는 propose() 로 저장 · 승인 후만 실행.
    """
    files_block = "\n".join(f"- {f}" for f in files[:20]) or "(관련 파일 없음)"
    kw_block = ", ".join(keywords) or "(없음)"
    return (
        f"# Universal Planner Task — Goal #{goal_id}\n\n"
        f"## 요구사항 원문\n{description[:600]}\n\n"
        f"## 사전 조사 (Grep/Glob)\n"
        f"- 키워드: {kw_block}\n"
        f"- 관련 파일 후보:\n{files_block}\n\n"
        f"## 요청\n"
        f"위 요구사항·관련 파일을 분석해 **실행 가능한 Task 계약 (JSON 배열)** 을 반환해라.\n"
        f"각 Task 는 다음 스키마를 따른다:\n"
        f"  {{\n"
        f"    \"kind\": \"cmd\",\n"
        f"    \"cmd\": \"<실행 명령 · 허용된 명령 범위 내만>\",\n"
        f"    \"verify\": \"<검증 명령 · 생략 가능>\",\n"
        f"    \"verify_type\": \"shell|python\",\n"
        f"    \"verifier_id\": \"<python verifier id · verify_type=python 시>\",\n"
        f"    \"verifier_ctx\": {{...}},\n"
        f"    \"safe_mode\": true,          // 격리 공간 실행 (default)\n"
        f"    \"risk\": \"low|medium|high|unknown\",\n"
        f"    \"requires_user_approval\": true,  // risk != low 는 true\n"
        f"    \"rationale\": \"<이 task 가 요구사항을 어떻게 충족하는가>\",\n"
        f"    \"files\": [\"<수정 예상 파일>\"],\n"
        f"    \"allow_paths\": [\"<scope-lock 허용 경로>\"]\n"
        f"  }}\n\n"
        f"반드시 지켜라:\n"
        f"  - LLM 추측 X · 실측 조사한 파일·심볼만 참조\n"
        f"  - 비가역 명령 (rm -rf·DROP TABLE·force push) 생성 X\n"
        f"  - 각 cmd 는 승인 정책 (approval-gate.py) 을 통과하도록 작성\n"
        f"  - safe_mode=true 유지 (sandbox 격리)\n"
        f"  - requires_user_approval 은 risk 가 명시 'low' 가 아니면 true\n\n"
        f"반환 후 사용자 또는 orchestrator 가 다음 명령으로 저장한다:\n"
        f"  python .claude/scripts/lib/planner.py propose {goal_id} '<json_array>'\n"
    )


# ========== 2. PROPOSE (외부 proposal 저장) ==========

def propose(goal_id: int, specs: List[Dict[str, Any]],
            origin: str = "external") -> Dict[str, Any]:
    """Task 계약 제안 저장 (외부: LLM · 사용자 · Claude Code Task tool).

    각 spec 은 investigate() 가 생성한 prompt_template 스키마를 따른다.
    저장 시 안전 default 강제:
      - safe_mode 누락 → True
      - risk 누락·unknown → requires_user_approval=True
      - cmd 가 비가역/위험 명령이면 risk 상향 (approval-gate pattern)
    """
    ensure_schema()
    if not isinstance(specs, list):
        return {"error": "specs must be a list"}
    if not specs:
        return {"error": "empty specs"}
    with sqlite3.connect(str(DB)) as c:
        exists = c.execute("SELECT goal_id FROM goals WHERE goal_id=?",
                           (goal_id,)).fetchone()
    if not exists:
        return {"error": f"goal {goal_id} not found"}

    saved = []
    now = int(time.time())
    with sqlite3.connect(str(DB)) as c:
        # 다음 sequence 번호
        seq_row = c.execute(
            "SELECT COALESCE(MAX(sequence), -1) + 1 FROM planner_proposals WHERE goal_id=?",
            (goal_id,),
        ).fetchone()
        next_seq = int(seq_row[0]) if seq_row else 0
        for idx, raw_spec in enumerate(specs):
            # 안전 normalization
            spec = dict(raw_spec)
            # safe_mode default True (격리 강제)
            spec.setdefault("safe_mode", True)
            # risk 평가
            risk = (spec.get("risk") or "unknown").lower()
            if risk not in ("low", "medium", "high", "unknown"):
                risk = "unknown"
            # cmd 안 비가역 패턴 → risk 상향
            cmd = spec.get("cmd") or ""
            if _is_dangerous_cmd(cmd):
                risk = "high"
            spec["risk"] = risk
            # requires_user_approval: low 만 자동 허용
            spec["requires_user_approval"] = bool(spec.get("requires_user_approval", True))
            if risk != "low":
                spec["requires_user_approval"] = True

            c.execute(
                "INSERT INTO planner_proposals "
                "(goal_id, sequence, spec_json, status, origin, risk, "
                " requires_user_approval, created_at) "
                "VALUES (?, ?, ?, 'pending', ?, ?, ?, ?)",
                (goal_id, next_seq + idx, json.dumps(spec, ensure_ascii=False),
                 origin, risk, 1 if spec["requires_user_approval"] else 0, now),
            )
            pid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
            saved.append({
                "proposal_id": pid,
                "sequence": next_seq + idx,
                "kind": spec.get("kind", "cmd"),
                "risk": risk,
                "requires_user_approval": spec["requires_user_approval"],
            })
    return {"goal_id": goal_id, "proposed": len(saved), "proposals": saved}


_DANGEROUS_PATTERNS = [
    re.compile(r"\brm\s+-rf\b", re.I),
    re.compile(r"\bDROP\s+TABLE\b", re.I),
    re.compile(r"\bDROP\s+DATABASE\b", re.I),
    re.compile(r"\bgit\s+push\s+--force\b", re.I),
    re.compile(r"\bgit\s+reset\s+--hard\b", re.I),
    re.compile(r"\bshutdown\b", re.I),
    re.compile(r"\bformat\b.*\b[c-z]:\b", re.I),
    re.compile(r"\bcurl\b[^|]*\|\s*(bash|sh)\b", re.I),
    re.compile(r"\bchmod\s+777\b", re.I),
    re.compile(r"\bsudo\b", re.I),
]


def _is_dangerous_cmd(cmd: str) -> bool:
    if not cmd:
        return False
    return any(p.search(cmd) for p in _DANGEROUS_PATTERNS)


# ========== 3. APPROVE / REJECT (HITL) ==========

def approve(proposal_id: int, approved_by: str = "user") -> Dict[str, Any]:
    ensure_schema()
    now = int(time.time())
    with sqlite3.connect(str(DB)) as c:
        row = c.execute("SELECT status, spec_json FROM planner_proposals WHERE proposal_id=?",
                        (proposal_id,)).fetchone()
        if not row:
            return {"error": f"proposal {proposal_id} not found"}
        if row[0] != "pending":
            return {"error": f"proposal {proposal_id} is '{row[0]}' not pending"}
        c.execute(
            "UPDATE planner_proposals SET status='approved', approved_at=?, approved_by=? "
            "WHERE proposal_id=?",
            (now, approved_by, proposal_id),
        )
    return {"proposal_id": proposal_id, "status": "approved", "approved_by": approved_by}


def reject(proposal_id: int, reason: str = "") -> Dict[str, Any]:
    ensure_schema()
    now = int(time.time())
    with sqlite3.connect(str(DB)) as c:
        row = c.execute("SELECT status FROM planner_proposals WHERE proposal_id=?",
                        (proposal_id,)).fetchone()
        if not row:
            return {"error": f"proposal {proposal_id} not found"}
        if row[0] != "pending":
            return {"error": f"proposal {proposal_id} is '{row[0]}' not pending"}
        c.execute(
            "UPDATE planner_proposals SET status='rejected', rejected_at=?, reject_reason=? "
            "WHERE proposal_id=?",
            (now, reason[:500], proposal_id),
        )
    return {"proposal_id": proposal_id, "status": "rejected", "reason": reason[:200]}


# ========== 4. PROMOTE (approved → supervisor tasks) ==========

def promote(goal_id: int) -> Dict[str, Any]:
    """approved proposals 를 supervisor tasks 로 승격.
    - safe_mode=True 강제 (sandbox 격리)
    - 승인 정책 통과 체크 (approval-gate · cmd 가 blocked 면 reject 로 변환)
    - tasks + goal_tasks 등재
    - proposal.status = 'promoted'
    """
    ensure_schema()
    now = int(time.time())
    # supervisor import (approval-gate 체크용)
    sys.path.insert(0, str(ROOT / ".claude" / "scripts" / "lib"))
    try:
        import supervisor as _sup  # noqa: F401
    except Exception as e:
        return {"error": f"supervisor import failed: {e}"}

    promoted = []
    rejected_at_promote = []
    with sqlite3.connect(str(DB)) as c:
        rows = c.execute(
            "SELECT proposal_id, sequence, spec_json FROM planner_proposals "
            "WHERE goal_id=? AND status='approved' ORDER BY sequence",
            (goal_id,),
        ).fetchall()
    if not rows:
        return {"goal_id": goal_id, "promoted": 0, "note": "no approved proposals"}

    for pid, seq, spec_json in rows:
        try:
            spec = json.loads(spec_json)
        except Exception as e:
            rejected_at_promote.append({"proposal_id": pid, "error": f"json: {e}"})
            continue
        # safe_mode 강제 (격리)
        spec["safe_mode"] = True
        cmd = spec.get("cmd") or ""
        # 승인 정책 재확인
        gate = _sup._check_approval_gate(cmd) if cmd else {"blocked": False}
        if gate.get("blocked"):
            # 승인 정책 통과 못 함 → promote 거부
            with sqlite3.connect(str(DB)) as c:
                c.execute(
                    "UPDATE planner_proposals SET status='rejected', rejected_at=?, "
                    "reject_reason=? WHERE proposal_id=?",
                    (now, f"approval_gate_blocked:{gate.get('category')}", pid),
                )
            rejected_at_promote.append({
                "proposal_id": pid, "reason": "approval_gate_blocked",
                "category": gate.get("category"),
            })
            continue
        # 허용된 cmd 체크 (일부 패턴만 자동 실행 허용)
        if cmd and not _sup._is_allowed_cmd(cmd):
            with sqlite3.connect(str(DB)) as c:
                c.execute(
                    "UPDATE planner_proposals SET status='rejected', rejected_at=?, "
                    "reject_reason='cmd_not_allowed' WHERE proposal_id=?",
                    (now, pid),
                )
            rejected_at_promote.append({"proposal_id": pid, "reason": "cmd_not_allowed",
                                        "cmd_head": cmd[:80]})
            continue
        # task 등재
        task_id = f"g{goal_id}-p{pid}"
        with sqlite3.connect(str(DB)) as c:
            exists = c.execute("SELECT task_id FROM tasks WHERE task_id=?",
                               (task_id,)).fetchone()
            if exists:
                # idempotent
                c.execute(
                    "UPDATE planner_proposals SET status='promoted', promoted_at=?, "
                    "promoted_task_id=? WHERE proposal_id=?",
                    (now, task_id, pid),
                )
                promoted.append({"proposal_id": pid, "task_id": task_id, "note": "already_registered"})
                continue
            c.execute(
                "INSERT INTO tasks (task_id, task_file, status, created_at, retry_count) "
                "VALUES (?, ?, 'pending', ?, 0)",
                (task_id, json.dumps(spec, ensure_ascii=False), now),
            )
            # goal_tasks sequence — 기존 뒤에 붙임
            next_seq_row = c.execute(
                "SELECT COALESCE(MAX(sequence), -1) + 1 FROM goal_tasks WHERE goal_id=?",
                (goal_id,),
            ).fetchone()
            next_seq = int(next_seq_row[0]) if next_seq_row else 0
            c.execute(
                "INSERT INTO goal_tasks (goal_id, task_id, sequence) VALUES (?, ?, ?)",
                (goal_id, task_id, next_seq),
            )
            c.execute(
                "UPDATE planner_proposals SET status='promoted', promoted_at=?, "
                "promoted_task_id=? WHERE proposal_id=?",
                (now, task_id, pid),
            )
        promoted.append({"proposal_id": pid, "task_id": task_id, "sequence": next_seq,
                         "risk": spec.get("risk")})
    return {"goal_id": goal_id, "promoted": len(promoted),
            "promoted_tasks": promoted,
            "rejected": rejected_at_promote}


# ========== 5. LIST / SHOW ==========

def list_proposals(goal_id: Optional[int] = None,
                   status: Optional[str] = None,
                   limit: int = 50) -> List[Dict[str, Any]]:
    ensure_schema()
    q = "SELECT proposal_id, goal_id, sequence, status, risk, requires_user_approval, " \
        "origin, created_at, promoted_task_id FROM planner_proposals"
    where, params = [], []
    if goal_id is not None:
        where.append("goal_id=?")
        params.append(goal_id)
    if status:
        where.append("status=?")
        params.append(status)
    if where:
        q += " WHERE " + " AND ".join(where)
    q += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    out = []
    with sqlite3.connect(str(DB)) as c:
        for r in c.execute(q, params).fetchall():
            out.append({
                "proposal_id": r[0], "goal_id": r[1], "sequence": r[2],
                "status": r[3], "risk": r[4],
                "requires_user_approval": bool(r[5]),
                "origin": r[6],
                "created_at": r[7],
                "promoted_task_id": r[8],
            })
    return out


def show_proposal(proposal_id: int) -> Dict[str, Any]:
    ensure_schema()
    with sqlite3.connect(str(DB)) as c:
        row = c.execute(
            "SELECT proposal_id, goal_id, sequence, spec_json, status, origin, risk, "
            "requires_user_approval, created_at, approved_at, approved_by, "
            "rejected_at, reject_reason, promoted_at, promoted_task_id, notes "
            "FROM planner_proposals WHERE proposal_id=?",
            (proposal_id,),
        ).fetchone()
    if not row:
        return {"error": f"proposal {proposal_id} not found"}
    try:
        spec = json.loads(row[3])
    except Exception:
        spec = {"error": "json parse failed", "raw": row[3][:200]}
    return {
        "proposal_id": row[0], "goal_id": row[1], "sequence": row[2],
        "spec": spec, "status": row[4], "origin": row[5], "risk": row[6],
        "requires_user_approval": bool(row[7]),
        "created_at": row[8], "approved_at": row[9], "approved_by": row[10],
        "rejected_at": row[11], "reject_reason": row[12],
        "promoted_at": row[13], "promoted_task_id": row[14],
        "notes": row[15],
    }


# ========== CLI ==========

def bridge(goal_id: int, stdin_json: str,
           origin: str = "task-tool-bridge") -> Dict[str, Any]:
    """Task tool bridge — Claude Code 세션 안 Task tool subagent 결과를 propose 로 safely absorb.

    사용자 지시 (3307fcd 후속 · Phase 3-R3):
      - Agent 기반 동적 Planner · LLM 결과 + 스키마 검증 + 정책 재평가 통과 후만 실행
      - 외부 Anthropic API 재귀 호출 X · Claude Code 세션 안에서만

    stdin_json: Task tool subagent 가 반환한 JSON array (planner.investigate prompt_template 스키마)

    흐름:
      1. JSON 파싱 + 스키마 검증 (kind·cmd·verify·risk·safe_mode)
      2. 비가역 cmd 자동 risk=high 상향 (propose 와 동일)
      3. propose 호출 (planner_proposals 등재)
      4. 결과 요약 반환
    """
    try:
        parsed = json.loads(stdin_json)
    except Exception as e:
        return {"ok": False, "error": f"json parse: {e}", "hint": "stdin must be JSON array"}
    if not isinstance(parsed, list):
        return {"ok": False, "error": "stdin must be a JSON array of Task specs"}
    if not parsed:
        return {"ok": False, "error": "empty array"}
    # 스키마 검증 — 각 spec 에 kind 또는 cmd 둘 중 하나 필수
    validated = []
    skipped = []
    for i, spec in enumerate(parsed):
        if not isinstance(spec, dict):
            skipped.append({"index": i, "reason": "not a dict"})
            continue
        if not (spec.get("cmd") or spec.get("kind")):
            skipped.append({"index": i, "reason": "missing kind and cmd"})
            continue
        # 안전 default: safe_mode=True 강제
        spec.setdefault("safe_mode", True)
        spec.setdefault("kind", "cmd")
        validated.append(spec)
    if not validated:
        return {"ok": False, "error": "no valid specs after schema check",
                "skipped": skipped}
    # propose 재사용 (중복 코드 X · 비가역 cmd 자동 risk 상향 포함)
    r = propose(goal_id, validated, origin=origin)
    if "error" in r:
        return {"ok": False, **r, "skipped_schema": skipped}
    return {"ok": True, "goal_id": goal_id,
            "proposed": r.get("proposed", 0),
            "proposals": r.get("proposals", []),
            "skipped_schema": skipped,
            "note": "proposals saved as 'pending' · 'planner.py approve <pid>' 후 'promote <goal_id>'"}


def _cli_main(argv):
    if len(argv) < 2:
        print("usage: planner.py {investigate|propose|bridge|list|show|approve|reject|promote} [...]")
        return 2
    cmd = argv[1]
    try:
        if cmd == "investigate":
            if len(argv) < 3:
                print("usage: planner.py investigate <goal_id>")
                return 2
            r = investigate(int(argv[2]))
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return 0 if "error" not in r else 1
        if cmd == "propose":
            if len(argv) < 4:
                print("usage: planner.py propose <goal_id> <json_array> [--origin X]")
                return 2
            goal_id = int(argv[2])
            specs = json.loads(argv[3])
            origin = "external"
            if "--origin" in argv:
                i = argv.index("--origin")
                if i + 1 < len(argv):
                    origin = argv[i + 1]
            r = propose(goal_id, specs, origin=origin)
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return 0 if "error" not in r else 1
        if cmd == "list":
            goal_id = None
            status = None
            if "--goal" in argv:
                i = argv.index("--goal")
                if i + 1 < len(argv):
                    goal_id = int(argv[i + 1])
            if "--status" in argv:
                i = argv.index("--status")
                if i + 1 < len(argv):
                    status = argv[i + 1]
            print(json.dumps(list_proposals(goal_id=goal_id, status=status),
                             ensure_ascii=False, indent=2))
            return 0
        if cmd == "show":
            if len(argv) < 3:
                print("usage: planner.py show <proposal_id>")
                return 2
            r = show_proposal(int(argv[2]))
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return 0 if "error" not in r else 1
        if cmd == "approve":
            if len(argv) < 3:
                print("usage: planner.py approve <proposal_id>")
                return 2
            r = approve(int(argv[2]))
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return 0 if "error" not in r else 1
        if cmd == "reject":
            if len(argv) < 3:
                print("usage: planner.py reject <proposal_id> [--reason R]")
                return 2
            reason = ""
            if "--reason" in argv:
                i = argv.index("--reason")
                if i + 1 < len(argv):
                    reason = argv[i + 1]
            r = reject(int(argv[2]), reason=reason)
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return 0 if "error" not in r else 1
        if cmd == "promote":
            if len(argv) < 3:
                print("usage: planner.py promote <goal_id>")
                return 2
            r = promote(int(argv[2]))
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return 0
        if cmd == "bridge":
            if len(argv) < 3:
                print("usage: planner.py bridge <goal_id>  (stdin: JSON array)")
                return 2
            goal_id = int(argv[2])
            origin = "task-tool-bridge"
            if "--origin" in argv:
                i = argv.index("--origin")
                if i + 1 < len(argv):
                    origin = argv[i + 1]
            stdin_data = sys.stdin.read()
            r = bridge(goal_id, stdin_data, origin=origin)
            print(json.dumps(r, ensure_ascii=False, indent=2))
            return 0 if r.get("ok") else 1
        print(f"unknown cmd: {cmd}")
        return 2
    except Exception as e:
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(_cli_main(sys.argv))
