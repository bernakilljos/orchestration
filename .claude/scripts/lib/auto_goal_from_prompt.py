"""auto_goal_from_prompt.py — UserPromptSubmit → Goal 자동 등재 helper (Phase 3 · 2026-10-30).

사용자 지시 (3307fcd 후속 · "자동 Agent 개발 종단 완성"):
  - UserPromptSubmit → Goal 자동 등재 · investigate 자동 실행 · systemMessage 로 Claude turn Task tool 유도
  - 임의 개수 요청 보존 · 세션 재시작 복구
  - 중복 실행 방지
  - 승인 대기 작업과 독립 작업 구분
  - 실패 때문에 다른 요청이 중단 X

안전 default:
  - 명시 개발 트리거만 (좁은 패턴) · 질문·메타 명령 skip
  - 중복 방지 (prompt hash · 최근 1h)
  - opt-out: 환경변수 AUTO_GOAL_REGISTER=0 또는 .claude/state/no-auto-goal 파일 있으면 skip
  - test marker (PHASE3-TEST·debug·sandbox) 자동 skip
  - 등재만 자동 · 실제 cmd 생성·실행은 승인 후만 (SAFE_PATTERNS 추가 X)
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
DB = ROOT / ".claude" / "state" / "orca.db"
LIB = ROOT / ".claude" / "scripts" / "lib"

# 명시 개발 트리거 — 좁은 패턴 (질문·메타 명령·단순 조회 제외)
# 과거 R58~R61 OUT_OF_SCOPE 반복 피해 "구체 개발·구현·자동화·종단" 어휘만
_DEV_TRIGGER = re.compile(
    r"("
    r"구현해줘|구현해주|구현하자|구현해라|구현 완성|"
    r"만들어줘|만들어주|만들어서|자동으로 만들"
    r"|자동화해줘|자동화 완성|자동 종단|end[- ]to[- ]end|end2end"
    r"|실행 연결|자동 연결"
    r"|Phase ?[1-9][A-Z]?[- ]?.*(완성|실 연결|실 통합)"
    r"|개발 완성|개발 종단|개발 자동화"
    r")",
    re.IGNORECASE,
)
# skip 트리거 — 질문·요약·메타·테스트
_SKIP_TRIGGER = re.compile(
    r"("
    r"뭐야\?|어때\?|어떻게.*있어\?|가능해\?|돼\?|되나\?"
    r"|요약해줘|보고해줘|확인해줘"
    r"|^/[a-z\-]+"  # /loop·/brief 등 slash command
    r"|debug test|PHASE3-TEST|sandbox-only|test request"
    r")",
    re.IGNORECASE,
)


def _is_disabled() -> bool:
    """Opt-out 체크."""
    if os.environ.get("AUTO_GOAL_REGISTER") == "0":
        return True
    if (ROOT / ".claude" / "state" / "no-auto-goal").exists():
        return True
    return False


def _prompt_hash(prompt: str) -> str:
    norm = re.sub(r"\s+", " ", prompt.strip()).lower()[:500]
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def _is_dup_recent(prompt_hash: str, window_sec: int = 3600) -> Optional[int]:
    """최근 window 안 같은 hash 의 goal_id 반환 (중복)."""
    if not DB.exists():
        return None
    try:
        with sqlite3.connect(str(DB)) as c:
            # goals.source_ref 에 'auto:ph=<hash>' 로 저장했으면 재사용
            cutoff = int(time.time()) - window_sec
            row = c.execute(
                "SELECT goal_id FROM goals "
                "WHERE source_ref LIKE ? AND created_at > ? "
                "ORDER BY created_at DESC LIMIT 1",
                (f"auto:ph={prompt_hash}%", cutoff),
            ).fetchone()
            return row[0] if row else None
    except Exception:
        return None


def should_register(prompt: str) -> Dict[str, Any]:
    """등재 여부 판정 · 자세한 사유 반환."""
    if _is_disabled():
        return {"register": False, "reason": "disabled (AUTO_GOAL_REGISTER=0 or no-auto-goal file)"}
    if not prompt or len(prompt.strip()) < 10:
        return {"register": False, "reason": "too short (<10 chars)"}
    if _SKIP_TRIGGER.search(prompt):
        return {"register": False, "reason": "skip trigger matched (question/meta/test)"}
    if not _DEV_TRIGGER.search(prompt):
        return {"register": False, "reason": "no dev trigger matched"}
    ph = _prompt_hash(prompt)
    dup_gid = _is_dup_recent(ph)
    if dup_gid:
        return {"register": False, "reason": f"duplicate within 1h (goal #{dup_gid})",
                "existing_goal_id": dup_gid, "prompt_hash": ph}
    return {"register": True, "prompt_hash": ph}


def register(prompt: str, source: str = "auto-planner") -> Dict[str, Any]:
    """Goal 등재 + investigate 자동 실행.

    반환: {"ok", "goal_id", "investigate_result", "systemMessage"} 또는 {"ok": False, "reason"}
    """
    verdict = should_register(prompt)
    if not verdict.get("register"):
        return {"ok": False, **verdict}

    ph = verdict["prompt_hash"]
    # supervisor + planner import
    sys.path.insert(0, str(LIB))
    try:
        import supervisor  # noqa: F401
        import planner  # noqa: F401
    except Exception as e:
        return {"ok": False, "reason": f"import failed: {e}"}

    # Goal 생성 (원문 보존 · source_ref 로 hash + source 기록)
    try:
        desc = prompt.strip()
        gid = supervisor.create_goal(desc, max_retry=1, timeout_h=24)
        # source_ref 업데이트 (중복 방지 + 추적성)
        with sqlite3.connect(str(DB)) as c:
            c.execute(
                "UPDATE goals SET source_ref=? WHERE goal_id=?",
                (f"auto:ph={ph}:src={source}", gid),
            )
    except Exception as e:
        return {"ok": False, "reason": f"create_goal failed: {e}"}

    # investigate (Grep/Glob · LLM X · 조사 보고서)
    investigate_result = None
    try:
        investigate_result = planner.investigate(gid, max_keywords=6)
    except Exception as e:
        investigate_result = {"error": f"investigate failed: {e}"}

    kw = investigate_result.get("keywords", []) if investigate_result else []
    files = investigate_result.get("related_files", []) if investigate_result else []
    system_msg = (
        f"[AUTO-GOAL #{gid}] 개발 요청 자동 등재 · investigate 완료\n"
        f"  prompt_hash={ph} · keywords={len(kw)} · related_files={len(files)}\n"
        f"  다음 단계 (사용자 액션 X · 메인 Claude turn 안에서 자동):\n"
        f"  1) Task tool 로 general-purpose/explorer subagent 호출 → investigate 결과 분석 + Task 계약 JSON 생성\n"
        f"  2) Subagent 결과를 `python .claude/scripts/lib/planner.py bridge {gid}` 로 pipe (stdin JSON array)\n"
        f"  3) 사용자 승인 후 `python .claude/scripts/lib/planner.py promote {gid}` → tasks 등재\n"
        f"  4) supervisor advance-all 가 safe_mode sandbox 로 실행 → apply/discard chain\n"
        f"  5) `python .claude/scripts/lib/independent_verifier.py {gid} --sandbox <path>` 로 독립 검증\n"
        f"  * SAFE_PATTERNS 자동 생성 X · 승인 통과 cmd 만 실행 · worktree 격리 강제"
    )
    return {
        "ok": True,
        "goal_id": gid,
        "prompt_hash": ph,
        "investigate_keywords": kw[:8],
        "investigate_files_count": len(files),
        "systemMessage": system_msg,
    }


def _cli_main(argv):
    """CLI: stdin 으로 prompt 받음 또는 argv[1] 로 받음."""
    if len(argv) >= 2 and argv[1] in ("should", "register", "status"):
        action = argv[1]
    else:
        action = "status"
    if action == "status":
        print(json.dumps({
            "disabled": _is_disabled(),
            "trigger_regex": _DEV_TRIGGER.pattern[:200],
            "skip_regex": _SKIP_TRIGGER.pattern[:200],
        }, ensure_ascii=False, indent=2))
        return 0
    # should / register — prompt 는 stdin 또는 argv[2]
    if len(argv) >= 3:
        prompt = argv[2]
    else:
        prompt = sys.stdin.read()
    if action == "should":
        print(json.dumps(should_register(prompt), ensure_ascii=False, indent=2))
        return 0
    r = register(prompt)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(_cli_main(sys.argv))
