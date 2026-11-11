"""ledger_auto_register — UserPromptSubmit 자동 Ledger 등록 (사용자 지시 2026-10-28).

사용자 메시지를 분류 (실행/질문/조회/수정/취소) 후 실행 요청만 Ledger 에 등록.
멱등성: event_id = sha256(session_id + prompt_hash + timestamp_minute)[:16]
         → 같은 메시지 재전달 (동일 분 안) 만 중복 간주 · 다른 날·다른 세션 재지시는 신규 등록.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
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


def _is_system_notification(text: str) -> bool:
    """harness 자동 이벤트 (사용자 입력 아님) — task-notification 태그로 시작."""
    t = (text or "").lstrip()
    # 2026-11-06: 대화 요약 뒤 harness 가 넣는 이어가기 메시지도 사용자 지시가 아니다
    return t.startswith("<task-notification>") or t.startswith("This session is being continued from a previous conversation")


# 2026-11-06 R167~R170: 붙여 넣은 평가 보고가 안의 '해줘'·'유료'·'배포' 단어로 실행·승인 요청에 등록됐다.
# 공식 hooks 문서: 붙여 넣은 글은 `<pasted_content id="…">` 줄과 `</pasted_content id="…">` 줄 사이로 온다.
_PASTE_RE = re.compile(r"<pasted_content\b[^>]*>.*?(?:</pasted_content\b[^>]*>|\Z)", re.S)
# 붙여 넣은 글만 온 메시지에서 '지금 하라는 지시' 표지 — 없으면 보고·인용으로 보고 등록하지 않는다.
_DIRECTIVE_LINE_RE = re.compile(r"^\s*대상\s*[:：]", re.M)
# 반말 명령형으로 끝나는 문장 ("다시 확인해.", "수정하지 마.") — 보고·평가 글은 "~습니다/~입니다" 로 끝난다
_IMPERATIVE_END_RE = re.compile(r"(?:해|하라|해라|해줘|해 줘|하지 마|하지마|할 것)"
                                r"(?:[.!](?=\s|$)|\s*$)", re.M)
# 2026-11-07 R184: 평가 보고 안의 권고 "…보존하세요." 한 줄로 보고 전체가 지시가 됐다.
# 존댓말 권고는 약한 표지 — 보고 문장("~습니다")보다 많을 때만 지시로 본다.
_POLITE_END_RE = re.compile(r"(?:하세요|해주세요|해 주세요|하십시오)(?:[.!](?=\s|$)|\s*$)", re.M)
_REPORT_END_RE = re.compile(r"니다[.!]?(?=\s|$)", re.M)
_DIRECTIVE_PHRASES = ("지시다", "지시한다", "승인한다", "전달할 승인 문구", "전달할 지시",
                      "claude code에 지시할", "claude code에 전달할")
# 금지·부정 문장 안의 위험 단어는 승인 요청이 아니다 ("유료 호출 금지", "배포는 승인하지 않는다").
_NEGATION_MARKERS = ("금지", "하지 마", "하지마", "않", "말고", "말 것")


def _split_pasted(text: str) -> tuple:
    """(사용자가 직접 쓴 글, 붙여 넣은 글)."""
    text = text or ""
    pasted = "\n".join(_PASTE_RE.findall(text))
    return _PASTE_RE.sub(" ", text).strip(), pasted


def _intent_text(prompt: str) -> tuple:
    """분류 대상 글과 종류 — own (직접 쓴 글) · pasted_directive · pasted_report.

    직접 쓴 글이 있으면 그것만 본다 (붙여 넣은 글은 참고 자료).
    붙여 넣은 글만 왔으면 그 글이 곧 사용자 메시지 — 지시 표지가 있을 때만 지시로 본다."""
    own, pasted = _split_pasted(prompt)
    if own or not pasted:
        return own, "own"
    low = pasted.lower()
    if (_DIRECTIVE_LINE_RE.search(pasted) or _IMPERATIVE_END_RE.search(pasted)
            or any(p in low for p in _DIRECTIVE_PHRASES)):
        return pasted, "pasted_directive"
    # 위험 단어가 든 존댓말 지시 ("운영 DB 를 수정하세요.") 는 보고 문장이 많아도 지시 — 등록돼야 승인 게이트가 본다
    polite = [ln.lower() for ln in pasted.splitlines() if _POLITE_END_RE.search(ln)]
    if polite and (any(_risk_hits(ln) for ln in polite)
                   or len(polite) >= len(_REPORT_END_RE.findall(pasted))):
        return pasted, "pasted_directive"
    return pasted, "pasted_report"


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
    # 명시적 취소 — 짧은 메시지만. 긴 지시 안의 "삭제하지 마" 같은 제약 문장을 취소로 읽지 않는다 (2026-11-06)
    if len(low) < 60:
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
                "prompt": _mask(prompt)[:800],   # 2026-11-07: 원문 발췌도 비밀정보 가림 (해시는 원문 기준)
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
                                "session_id": session_id, "prompt": _mask(prompt)[:400]},
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
    # 2026-11-07: 일반 push 도 승인 대상 (execution-contract § 3) — 명사 "Push" 가 아니라 하라는 말만
    "git push", "push해", "push 해", "푸시해", "푸시 해",
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


# 2026-11-07 R184~R186: 위험 단어가 '요청' 이 아닌 줄에 있어도 승인 대기가 됐다.
#   R184 표 칸 "유료 1회 승인 대기" · R185 "운영 게이트를 바꾸는 것이 아니라" · R186 "유료 호출 요청 → 승인 필요".
# 그래서 줄을 먼저 나눈다: 표 줄 · 제약 목록 · 상태/게이트 설명 · "A가 아니라 B" 의 A 는 위험 단어를 세지 않는다.
# 단, 줄 어디에든 요청·행동 표지가 있으면 ("…배포해줘 승인 전이라도", "배포   진행") 그대로 센다 —
# 구조만으로 실제 요청을 빼지 않는다 (독립 검토에서 줄 끝만 보던 첫 설계가 우회로 4건을 만들었다).
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$|\S(?:\t| {3,})\S.*\S(?:\t| {3,})\S")   # | 표 · 칸 3개 이상
_CONSTRAINT_HEAD_RE = re.compile(r"^\s*(?:제약|금지|금지 사항|하지 말 것)\s*(?:사항)?\s*[:：]\s*$")
_BULLET_RE = re.compile(r"^\s*(?:[-*·•]|\d+[.)])\s")
# 문장 중간 "A가 아니라 B" 만 (줄 끝 "아님" 은 범위를 자르지 않는다) — A 에 요청·행동 표지가 있으면 자르지 않는다
_NEGATED_SCOPE_RE = re.compile(r"(?:아니라(?!면)|아니고)\s*(?=\S)")
# 2026-11-07 R187: "유료 실행 없이 … 검증한다" 의 '유료' 가 승인 사유가 됐다.
# '없이' 는 근거가 드러날 때만 뺀다 — 위험 단어 바로 뒤에 실행·호출·사용·과금·진행 이 붙고 곧바로 '없이' 인 경우
# ("유료 실행 없이", "배포 진행 없이"). "push 경고 없이"·"배포 지연 없이"·"drop table 예외 없이" 처럼
# 다른 말이 끼면 위험 작업을 그대로 하라는 뜻일 수 있어 빼지 않는다 (독립 검토 3차 우회 사례).
_WITHOUT_RE = re.compile(r"\S+\s*(?:실행|호출|사용|과금|진행)\s+없이(?=\s*\S)")
# 2026-11-07 독립 검토 2·3차 교훈: "이 줄에 행동 표지가 없다" 를 근거로 줄을 빼는 규칙은 행동 표지 어휘가
# 끝이 없어서 (하자·가자·ㄱ·때려·run …) 계속 뚫린다. 그래서 예시 목록·인용 제외는 넣지 않았다 —
# 시험 설명 속 "- push origin main" 같은 줄은 승인 필요로 남는다 (안전한 쪽 과잉 판정).
# 표·상태·제약 제외(5814754)는 유지하되 행동 표지에 청유·명령 어미와 영어 명령어를 넣어 좁힌다.
# push 는 띄어쓰기·순서가 다양하다 ("git  push", "push origin main", "푸시 진행") — 문자열 대신 정규식
_RISK_REGEX = (
    ("git push", re.compile(r"git\s+push")),
    ("push origin", re.compile(r"(?<![a-z])push\s+(?:-{1,2}\S+\s+)*origin(?![a-z])")),
    ("push 진행", re.compile(r"(?<![a-z])push\s*(?:진행|실행)|푸시\s*(?:진행|실행)")),
)


def _risk_hits(text: str) -> list:
    """위험 패턴 — 문자열 목록 + 정규식 (소문자 입력)."""
    hits = [p for p in _APPROVAL_PATTERNS if p in text]
    return hits + [name for name, rx in _RISK_REGEX if name not in hits and rx.search(text)]
_STATUS_RE = re.compile(r"승인\s*(?:대기|필요|요청|전|여부)|대기\s*중|미확인|보류|blocked|approval_required")
_ACTION_RE = re.compile(r"해줘|해 줘|해라|하라|해(?=[\s.!,:：]|$)|한다|하세요|해주세요|하십시오|할 것|줘|주세요|주십시오"
                        r"|바랍니다|바람|부탁|진행|실행|시작|반영|수정|삭제|지워|제거|변경|교체|적용|올려"
                        r"|돌려|돌리|처리|수행|날려|때려|밀어|하자|합시다|하셈|해요|하죠|가자|고고|ㄱ"
                        r"|(?<![a-z])(?:run|do|go|execute|exec|apply|perform|start|please|just|let's)(?![a-z])")  # push 는 승인 패턴(동사형)만 — 표 칸 명사 오인 방지
# 판정 근거에 남기는 발췌의 비밀정보 가림 — 정본은 scripts/lib/redact.py (2026-11-10 · 대화·세션 DB·bash 로그와 공용)
try:  # sys.path 오염 없이 파일로 로드 (훅의 _common 등과 이름 충돌 방지)
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("redact_ledger", os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts", "lib", "redact.py"))
    _sm = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_sm)
    _SECRET_RE, _mask_impl = _sm.SECRET_RE, _sm.mask
except Exception:  # noqa: BLE001 — 가림 모듈이 없으면 원문을 남기지 않는다 (fail-closed)
    _SECRET_RE, _mask_impl = None, None


def _mask(text: str) -> str:
    """Ledger·raw·deferred 에 남기는 글의 비밀정보 가림 (원문 해시·판정은 가리기 전 원문으로)."""
    if _mask_impl is None:
        return "[MASKED]" if text else ""
    return _mask_impl(text or "")


# "…를 승인한다" — 기록만 한다. 이 문장으로 위험 작업 승인을 대신하지 않는다 (권한 판단은 사용자·실행 게이트).
_STATED_SCOPE_RE = re.compile(r"^[^\n]*승인한다[.]?[ \t]*$", re.M)


# 2026-11-07 R187: 시험 대상으로 나열한 "- git  push" · "- push origin main" 목록이 push 요청으로 읽혔다.
# 시도했다가 뺀 규칙 (독립 검토 2·3차에서 우회로 확인):
#   예시 목록 = 바로 앞 줄이 "아래/다음 표현·입력·사례…" 또는 바로 뒤 줄이 "위 입력·표현…" 인 글머리 묶음을 빼는 규칙.
#   가리키는 줄이 지시인지 ("다음 사례 처리해:", "위 입력 처리", "다음 케이스 순서대로 가자:") 글자로 다 가릴 수 없었다.
#   인용 = 따옴표·백틱 안에만 위험 문자열이 있으면 빼는 규칙 — "run `…`", "`git push` 하자" 가 빠졌다.
#   목록 줄 "- 푸시 진행" 은 실제 작업 목록과 글자로 구분할 수 없다 → 승인 필요로 남긴다.


def _drop_without(text: str) -> str:
    """'<위험 단어> 실행·호출·사용·과금·진행 없이' 만 지운 글 — 다른 말이 끼어 있으면 지우지 않는다."""
    return _WITHOUT_RE.sub(lambda m: " " * len(m.group(0)), text)


def _approval_basis(prompt: str) -> dict:
    """승인 판정과 근거 — matched(위험 패턴) · lines(판정에 쓴 줄 · 가림 · 200자) · excluded(제외 사유별 줄 수)."""
    matched, lines, excluded = [], [], {}
    in_constraints = False
    for no, raw in enumerate((prompt or "").splitlines(), 1):
        ln = raw.lower().strip()
        if not ln:
            in_constraints = False
            continue
        if _CONSTRAINT_HEAD_RE.match(ln):
            in_constraints = True
            continue
        if in_constraints and not _BULLET_RE.match(raw):
            in_constraints = False
        hits = _risk_hits(ln)
        if not hits:
            continue
        reason = None
        if any(n in ln for n in _NEGATION_MARKERS):
            reason = "negation"
        else:
            body = ln
            # "A 가 아니라 B" — A 에 요청·행동 표지가 없을 때만 A 를 빼고 B 를 본다
            m = _NEGATED_SCOPE_RE.search(ln)
            if m and not _ACTION_RE.search(ln[:m.start()]):
                body = ln[m.end():]
            # "X 없이" — X 안의 위험 단어만 뺀다
            body = _drop_without(body)
            hits = _risk_hits(body)
            if not hits:
                reason = "negated_scope"
            # (예시 목록·인용 제외는 두지 않는다 — 위 '시도했다가 뺀 규칙' 참고 · 인용된 '승인' 문장도 따옴표 안 위험 문자열도 그대로 센다)
            if reason is None and not _ACTION_RE.search(body):
                if in_constraints:
                    reason = "constraint"
                elif _TABLE_ROW_RE.search(raw):
                    reason = "table"
                elif _STATUS_RE.search(body):
                    reason = "status"
        if reason:
            excluded[reason] = excluded.get(reason, 0) + 1
            continue
        matched += [p for p in hits if p not in matched]
        lines.append({"line": no, "text": _mask(raw.strip())[:200]})
    scope = [_mask(s.strip())[:200] for s in _STATED_SCOPE_RE.findall(prompt or "")][:3]
    return {"matched": matched, "lines": lines[:5], "excluded": excluded, "stated_scope": scope}


def _needs_approval(prompt: str) -> list:
    """위험 패턴 매치 반환 (사용자 지시 "포괄 '전부 개발해' 를 무제한 실행 권한으로 해석 X")."""
    return _approval_basis(prompt)["matched"]


def _append_ledger_entry(prompt: str, session_id: str, classification: str, intent: str = None) -> dict:
    """append-only · event_id 기반 중복 방지 (desc hash 는 참고만).
    intent = 승인 판정 대상 글 (직접 쓴 글 · 또는 지시로 판정된 붙여 넣은 글). desc 는 원문 그대로."""
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
    basis = _approval_basis(prompt if intent is None else intent)
    approval_matches = basis["matched"]
    initial_status = "approval_required" if approval_matches else "pending"
    entry = {
        "id": rid,
        "desc": _mask(prompt)[:400],
        "classification": classification,
        "status": initial_status,
        "event_id": event_id,
        "session_id": session_id or "unknown",
        "ts": datetime.now().isoformat(timespec="seconds"),
        "ts_epoch": time.time(),
        "prompt_hash": _prompt_hash(prompt),
        # 2026-11-07: desc 는 400자에서 잘려 판정에 쓴 줄이 빠질 수 있었다 (R185).
        # 원문 전체는 저장하지 않는다 — 길이·전체 해시(앞 16자 = orca.db conversations.content_hash)와
        # 판정에 쓴 줄(가림 · 200자)만 남긴다.
        "prompt_len": len(prompt or ""),
        "prompt_sha256": hashlib.sha256((prompt or "").encode("utf-8", errors="replace")).hexdigest(),
        "approval_basis": {k: v for k, v in basis.items() if k != "matched" and v},
    }
    if approval_matches:
        entry["approval_reasons"] = approval_matches[:5]
    data.setdefault("requests", []).append(entry)
    try:
        with open(LEDGER, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return {"status": "write_error", "error": str(e)[:100]}
    try:  # §78 요청 접수 = 추적 시작 (추적번호 = event_id · R 번호는 별칭)
        from _common import trace_mod
        tm = trace_mod()
        if tm:
            tm.set_current(event_id, rid, prompt)
            tm.emit("request", step=rid, status="start", trace_id=event_id,
                    detail={"classification": classification, "approval_required": bool(approval_matches),
                            "session": (session_id or "unknown")[:8]})
    except Exception:  # noqa: BLE001 — 추적 실패가 등록을 막지 않음
        pass
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
        # 2026-10-30 R116: 백그라운드 작업 완료 알림은 harness 가 prompt 로 전달 · 사용자 요청 아님.
        # 요약문 안 "tests" 등이 execute 키워드에 매치돼 R112~R116 이 오등록됐다.
        if _is_system_notification(prompt):
            _append_raw(prompt, session_id, "system_notification", "skipped_non_user")
            return ""
        intent, kind = _intent_text(prompt)
        if kind == "pasted_report":
            # 붙여 넣은 보고·인용만 있고 지시 표지가 없다 — 원문은 raw 에 남기고 요청으로 등록하지 않는다
            _append_raw(prompt, session_id, "pasted_report", "skipped_non_exec")
            return ""
        classification = _classify(intent)
        if kind == "pasted_directive" and classification in ("unknown", "status", "question"):
            # 지시 표지가 확인된 붙여 넣은 지시 — 동사 목록에 없는 "확인해."·"유지해." 지시도 실행 요청이다
            classification = "execute"
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
        result = _append_ledger_entry(prompt, session_id, classification, intent)
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
