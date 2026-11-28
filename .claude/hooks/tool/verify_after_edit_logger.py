"""verify-after-edit-logger.py 이식 — Edit/Write 직전 같은 파일 반복 수정 기록 (orca.db verify_after_edit_patterns · 비차단).

R375 (2026-11-28 · Hook 경량화 기준선): 종전 settings 비동기 훅이 Edit 마다 python 프로세스 1개를 띄웠고,
인자로 '' 를 받아 stdin 을 읽지 않아 모든 기록이 빈 경로였다 (orca.db 2486건 전부 file_path='') —
여기서는 tool_input.file_path 를 실제로 넘긴다. 기록 로직은 원본 함수(on_edit_tool) 그대로 재사용 (이식 없음).
"""
from __future__ import annotations

from _common import load_script, tool_input


def run(ctx):
    fp = tool_input(ctx).get("file_path") or ""
    if not isinstance(fp, str) or not fp:
        return None
    mod = load_script("verify-after-edit-logger")
    if mod is None:
        return None
    try:
        mod.on_edit_tool(fp)
    except Exception:  # noqa: BLE001 — 원본도 로거 실패로 작업을 막지 않았다
        pass
    return None
