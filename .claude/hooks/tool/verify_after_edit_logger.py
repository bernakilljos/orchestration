"""verify-after-edit-logger.py 이식 — 성공한 Edit/Write 의 같은 파일 반복 수정 기록 (orca.db verify_after_edit_patterns · 비차단).

R375 Hook 경량화: 종전 settings 비동기 훅이 Edit 마다 python 프로세스 1개를 띄웠고, 인자로 '' 를 받아 stdin 을 읽지 않아
모든 기록이 빈 경로였다 (orca.db 2486건 · 보존). 5차 검토 반영:
- PostToolUse 에 등록 (성공한 Edit 만 · 실패·차단된 Edit 은 PostToolUse 가 오지 않는다 · 예전 PRE 는 차단된 것까지 기록)
- 응답 경로 시간 제한: 원본 정본 record_edit (연결 대기 0.25초 · 전체 0.5초 · finally close · 잠금·디스크 오류는 생략)
- 생략 사유는 로그에만 (작업을 막지 않음)
"""
from __future__ import annotations

from _common import load_script, tool_input


def run(ctx):
    fp = tool_input(ctx).get("file_path") or ""
    if not isinstance(fp, str) or not fp:
        return None
    mod = load_script("verify-after-edit-logger")
    if mod is None or not hasattr(mod, "record_edit"):
        return None
    try:
        r = mod.record_edit(fp)
        if r != "ok":
            mod.log(f"[SKIP] {mod.normalize_path(fp)} — {r}")
    except Exception:  # noqa: BLE001 — 로거 실패로 작업을 막지 않는다
        pass
    return None
