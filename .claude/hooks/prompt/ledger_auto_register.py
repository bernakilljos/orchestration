"""ledger_auto_register — UserPromptSubmit 자동 Ledger 등록 (사용자 지시 2026-10-28).

사용자 메시지를 분류 (실행/질문/조회/수정/취소) 후 실행 요청만 Ledger 에 등록.
멱등성: event_id = sha256(session_id + prompt_hash + timestamp_minute)[:16]
         → 같은 메시지 재전달 (동일 분 안) 만 중복 간주 · 다른 날·다른 세션 재지시는 신규 등록.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime

try:
    from _common import Ctx  # type: ignore
except Exception:
    Ctx = None  # type: ignore


# 분류 룰 — 간단한 키워드 기반 scaffold
_EXEC_KEYWORDS = (
    "해줘", "해 줘", "만들어", "수정", "고쳐", "구현", "추가", "작성",
    "삭제", "제거", "변경", "배포", "install", "setup", "sync",
    "create", "add", "fix", "update", "delete", "deploy",
    "개선", "완성", "scaffold", "build", "test",
)
_QUESTION_SUFFIX = ("?", "？", "지?", "까?")
_STATUS_KEYWORDS = ("상태", "현황", "확인해", "보여줘", "show", "status", "list", "뭐야", "몇", "어디", "왜")
_CANCEL_KEYWORDS = ("취소", "그만", "안 할", "안할", "안 해", "안해", "하지 마", "cancel", "abort", "stop ")
_REDO_PREFIXES = ("재실행", "다시 실행", "REDO:", "다시해", "다시 해")


def _classify(text: str) -> str:
    """사용자 메시지 유형 분류 → execute / question / status / cancel / redo / unknown."""
    low = (text or "").lower().strip()
    if not low:
        return "unknown"
    # 명시적 재실행
    for p in _REDO_PREFIXES:
        if p.lower() in low:
            return "redo"
    # 명시적 취소
    for k in _CANCEL_KEYWORDS:
        if k in low:
            return "cancel"
    # 상태 조회 (짧은 메시지 + 조회 키워드)
    if len(low) < 60:
        for k in _STATUS_KEYWORDS:
            if k in low:
                return "status"
        # 질문 접미사
        if low.endswith(_QUESTION_SUFFIX):
            return "question"
    # 실행 요청 (한글/영어 명령형)
    for k in _EXEC_KEYWORDS:
        if k in low:
            return "execute"
    # 긴 메시지 + 결함 지적 패턴
    if len(low) > 200 and ("문제" in low or "결함" in low or "오류" in low or "안 됐" in low or "안됐" in low):
        return "execute"
    return "unknown"


def _event_id(session_id: str, prompt: str) -> str:
    """멱등성 키 — session + prompt_hash + 분 단위 timestamp.
    같은 분 안 같은 메시지 = 중복 (재전달 간주) · 다른 날·다른 분 = 신규."""
    minute_bucket = int(time.time() // 60)
    prompt_hash = hashlib.sha256((prompt or "").encode("utf-8", errors="replace")).hexdigest()[:12]
    base = f"{session_id}|{prompt_hash}|{minute_bucket}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


def _append_ledger_entry(prompt: str, session_id: str, classification: str) -> dict:
    """append-only · event_id 기반 중복 방지 (desc hash 는 참고만)."""
    LEDGER = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."), ".claude", "state", "request-ledger.json")
    try:
        if os.path.exists(LEDGER):
            with open(LEDGER, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        else:
            data = {"session_id": session_id or "unknown",
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                    "requests": []}
    except Exception:
        data = {"session_id": session_id or "unknown",
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "requests": []}

    event_id = _event_id(session_id, prompt)
    # 같은 event_id 재전달 skip
    for r in data.get("requests", []):
        if r.get("event_id") == event_id:
            return {"status": "duplicate_event", "request_id": r.get("id"), "event_id": event_id}

    rid = f"R{len(data.get('requests', [])) + 1}"
    entry = {
        "id": rid,
        "desc": (prompt or "")[:400],
        "classification": classification,
        "status": "pending",
        "event_id": event_id,
        "session_id": session_id or "unknown",
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
    data.setdefault("requests", []).append(entry)
    try:
        with open(LEDGER, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return {"status": "write_error", "error": str(e)[:100]}
    return {"status": "registered", "request_id": rid, "event_id": event_id,
            "classification": classification}


def run(ctx) -> str:
    """UserPromptSubmit 시점 호출 · 사용자 메시지 → 분류 → 실행 요청만 Ledger 등록."""
    try:
        payload = getattr(ctx, "payload", {}) or {}
        prompt = payload.get("prompt") or payload.get("message") or ""
        session_id = payload.get("session_id") or payload.get("sessionId") or "unknown"
        if not prompt:
            return ""
        classification = _classify(prompt)
        # 실행 요청만 등록 (사용자 지시 "불명확한 요청 임의 실행 X")
        if classification not in ("execute", "redo"):
            return ""  # 질문·조회·취소·unknown 은 등록 X
        result = _append_ledger_entry(prompt, session_id, classification)
        if result.get("status") == "registered":
            return f"[ledger] + {result['request_id']} (event_id={result['event_id']} · class={classification})"
        if result.get("status") == "duplicate_event":
            return f"[ledger] = {result['request_id']} (duplicate event · same minute)"
        return ""
    except Exception as e:
        # Hook 실패해도 다른 hook 영향 X · log 만
        try:
            logf = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."), ".claude", "logs", "ledger-auto-register.log")
            os.makedirs(os.path.dirname(logf), exist_ok=True)
            with open(logf, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().isoformat()}] ERROR: {str(e)[:200]}\n")
        except Exception:
            pass
        return ""


if __name__ == "__main__":
    # CLI 테스트
    raw = sys.stdin.read()
    class _MockCtx:
        payload = json.loads(raw or "{}")
    print(run(_MockCtx()))
