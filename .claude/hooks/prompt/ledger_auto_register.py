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
    # 명령형 동사 (사용자 지시 2026-10-28 자연어 확장)
    "해줘", "해 줘", "해라", "해봐", "해 봐", "해보자",
    "만들어", "수정", "고쳐", "구현", "추가", "작성", "개발",
    "보완", "채워", "완성", "완성해", "개선",
    "삭제", "제거", "변경", "배포", "install", "setup", "sync",
    "create", "add", "fix", "update", "delete", "deploy", "implement",
    "scaffold", "build", "test", "develop", "refactor",
    # 전부·모두 지시형
    "전부", "모두", "같이 해", "함께 해", "통째로", "다 처리", "전부 처리", "다 끝내",
    # 조사·분석 (실행 성격)
    "조사해", "분석해", "검증해", "실행해", "실측",
    # 자연 지시 패턴
    "~~ 좀", "좀 봐", "좀 해",
)
_QUESTION_SUFFIX = ("?", "？", "지?", "까?")
_STATUS_KEYWORDS = ("상태", "현황", "확인해", "보여줘", "show", "status", "list", "뭐야", "몇", "어디", "왜")
_CANCEL_KEYWORDS = ("취소", "그만", "안 할", "안할", "안 해", "안해", "하지 마", "cancel", "abort", "stop ")
_REDO_PREFIXES = ("재실행", "다시 실행", "REDO:", "다시해", "다시 해")
# 보고 재출력 요청 (2026-10-28 사용자 지시 — R24 재발 방지)
# "다시보고해줘 짤려서" 류를 execute 로 오분류 X · 보고 재출력로 분류
_REPORT_REQUEST_KEYWORDS = (
    "다시 보고", "다시보고", "재보고", "짤렸", "짤려서", "짤림",
    "재출력", "다시 출력", "다시출력", "다시 알려",
    "요약해줘", "정리해줘", "report again", "summary again",
    "이전 보고", "지난 보고", "방금 보고",
)


def _classify(text: str) -> str:
    """사용자 메시지 유형 분류 → report_request / execute / question / status / cancel / redo / unknown.

    2026-10-28 R24 재발 방지 (사용자 "다시보고해줘 짤려서" 오분류 fix):
    report_request 를 execute 보다 **먼저** 체크 (해줘 가 execute 매치하기 전).
    """
    low = (text or "").lower().strip()
    if not low:
        return "unknown"
    # 보고 재출력 요청 (R24 재발 방지 · execute 보다 우선 · "다시보고해줘" 에 "해줘" 포함되어도 report_request)
    for k in _REPORT_REQUEST_KEYWORDS:
        if k.lower() in low:
            return "report_request"
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


def _prompt_hash(prompt: str) -> str:
    """prompt 지문 (중복 감지용 보조 · 사용자 "텍스트만으로 중복 판단 X" 지시 반영 — 윈도우와 함께 사용)."""
    return hashlib.sha256((prompt or "").encode("utf-8", errors="replace")).hexdigest()[:12]


def _is_recent_duplicate(session_id: str, prompt: str, existing: list, window_s: int = 10) -> dict:
    """사용자 지시 2026-10-28: 분 bucket 설계 결함 fix.
    "같은 분 안 별개 메시지 2개 중 하나 사라짐" 문제 해결.
    새 설계: 윈도우 (default 10s) 안 같은 session+prompt_hash → 중복 (사용자 enter 두번 등)
    · 10초 이후 같은 문장 재지시 → 신규 등록 (오전/오후 재지시 완전 보존)."""
    phash = _prompt_hash(prompt)
    now = time.time()
    for r in existing:
        if r.get("session_id") != session_id:
            continue
        if r.get("prompt_hash") != phash:
            continue
        rts = r.get("ts_epoch") or 0
        if now - rts < window_s:
            return {"duplicate": True, "existing_id": r.get("id"), "event_id": r.get("event_id")}
    return {"duplicate": False}


def _new_event_id(session_id: str, prompt: str) -> str:
    """새 등록 시 발급 — ns 단위 timestamp 포함 (모든 호출마다 unique).
    사용자가 payload 에 message_id 를 넣어주면 그걸 우선 쓸 수 있도록 함수 분리."""
    ns = time.time_ns()
    phash = _prompt_hash(prompt)
    return hashlib.sha256(f"{session_id}|{phash}|{ns}".encode("utf-8")).hexdigest()[:16]


def _append_raw(prompt: str, session_id: str, classification: str, status: str) -> None:
    """사용자 지시 2026-10-28: 모든 UserPromptSubmit 원본 이벤트 append-only 보존.
    분류 결과·중복 여부 무관하게 전부 기록 · 삭제 X · 추적용."""
    try:
        raw_log = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."),
                               ".claude", "logs", "ledger-raw.jsonl")
        os.makedirs(os.path.dirname(raw_log), exist_ok=True)
        with open(raw_log, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.now().isoformat(timespec="seconds"),
                "ts_epoch": time.time(),
                "session_id": session_id,
                "classification": classification,
                "status": status,  # registered·duplicate_skipped·deferred·approval_required
                "prompt": (prompt or "")[:800],
                "prompt_hash": _prompt_hash(prompt),
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _append_deferred(prompt: str, session_id: str) -> None:
    """unknown 분류 — 원문 보존 (실행 보류 · 사용자 재해석 가능)."""
    try:
        deferred_log = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."),
                                     ".claude", "logs", "ledger-deferred.jsonl")
        os.makedirs(os.path.dirname(deferred_log), exist_ok=True)
        with open(deferred_log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                "session_id": session_id, "prompt": (prompt or "")[:400]},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass


# 승인 게이트 — 사용자 지시 2026-10-28 "삭제·배포·외부·권한·비용은 자동 실행 X"
_APPROVAL_PATTERNS = (
    # 데이터 손실
    "삭제해", "삭제해줘", "삭제해라", "지워", "remove ", "delete ", "drop table", "truncate",
    "rm -rf", "git reset --hard", "git clean -fd",
    # 배포·외부 push
    "배포", "deploy", "git push --force", "force push",
    "production", "운영", "실배포", "publish",
    # 권한 상승
    "sudo", "chmod 777", "권한 상승", "admin 권한",
    # 비용
    "결제", "구독", "유료", "paid plan", "subscription",
    # 외부 시스템
    "sap", "oracle", "실제 db", "운영 db",
    # 포괄 지시
    "전부 개발해", "모두 실행해", "다 해버려",
)


def _needs_approval(prompt: str) -> list:
    """위험 패턴 매치 반환 (사용자 지시 "포괄 '전부 개발해' 를 무제한 실행 권한으로 해석 X")."""
    low = (prompt or "").lower()
    matched = [p for p in _APPROVAL_PATTERNS if p in low]
    return matched


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

    # 2026-10-28 재설계 — 윈도우 기반 중복 감지 (분 bucket 폐기 · 사용자 지적 반영)
    existing = data.get("requests", [])
    dup = _is_recent_duplicate(session_id, prompt, existing, window_s=10)
    if dup.get("duplicate"):
        # 원본은 raw log 에 이미 보존 (삭제 X · 사용자 지시 반영)
        return {"status": "duplicate_within_window", "request_id": dup.get("existing_id"),
                "event_id": dup.get("event_id")}
    event_id = _new_event_id(session_id, prompt)
    rid = f"R{len(existing) + 1}"
    # 승인 요구 패턴 매치 시 status=approval_required (실행 보류)
    approval_matches = _needs_approval(prompt)
    initial_status = "approval_required" if approval_matches else "pending"
    entry = {
        "id": rid,
        "desc": (prompt or "")[:400],
        "classification": classification,
        "status": initial_status,
        "event_id": event_id,
        "session_id": session_id or "unknown",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "ts_epoch": time.time(),
        "prompt_hash": _prompt_hash(prompt),
    }
    if approval_matches:
        entry["approval_reasons"] = approval_matches[:5]
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
        # 기존 hook (save_user_prompt) 와 동일 key 패턴 — user_prompt | prompt
        prompt = payload.get("user_prompt") or payload.get("prompt") or payload.get("message") or ""
        session_id = payload.get("session_id") or payload.get("sessionId") or "unknown"
        if not prompt:
            return ""
        classification = _classify(prompt)
        # 모든 UserPromptSubmit → raw log 보존 (사용자 지시 "원본 이벤트 전부 append-only · 삭제 X")
        if classification == "unknown":
            # 분류 불확실 → raw + deferred (원문 2중 보존 · 실행 보류 · 사용자 재해석 가능)
            _append_raw(prompt, session_id, "unknown", "deferred")
            _append_deferred(prompt, session_id)
            return ""
        if classification not in ("execute", "redo"):
            # 질문·조회·취소 — 원본만 raw 로그에 보존 (ledger 등록 X)
            _append_raw(prompt, session_id, classification, "skipped_non_exec")
            return ""
        result = _append_ledger_entry(prompt, session_id, classification)
        if result.get("status") == "registered":
            # 승인 요구 여부 확인 (ledger 안 entry 의 status 가 approval_required 인지)
            ledger_path = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."),
                                       ".claude", "state", "request-ledger.json")
            with open(ledger_path, "r", encoding="utf-8") as f:
                d = json.load(f)
            latest = d.get("requests", [])[-1] if d.get("requests") else {}
            if latest.get("status") == "approval_required":
                _append_raw(prompt, session_id, classification, "approval_required")
                reasons = latest.get("approval_reasons", [])[:3]
                return f"[ledger] + {result['request_id']} (APPROVAL REQUIRED · reasons={reasons} · class={classification})"
            _append_raw(prompt, session_id, classification, "registered")
            return f"[ledger] + {result['request_id']} (event_id={result['event_id']} · class={classification})"
        if result.get("status") == "duplicate_within_window":
            # 중복 의심이지만 원본은 raw 로그에 보존됨 · 실행만 보류 (사용자 지시 "원본 삭제 X")
            _append_raw(prompt, session_id, classification, "duplicate_skipped_but_logged")
            return f"[ledger] = {result['request_id']} (duplicate 10s · raw 보존됨)"
        _append_raw(prompt, session_id, classification, "unknown_status")
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
