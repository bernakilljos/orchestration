"""verify-teaching-doc-sections.py 이식 — Edit/Write 후 교재·강의 문서 8섹션 확인 (비차단 안내 · Claude 에 전달).

R375 Hook 경량화: 종전 settings 비동기 훅은 인자 없이 실행돼 사용법만 출력하고 exit 2 로 끝났다 (문서 미검사).
5차 검토 반영:
- 판정 정본 재사용: is_teaching_path · missing_sections (md 는 제목 줄·표 줄만) · SECTION_PATTERNS
- 응답 경로 예산: md·txt 만 · 크기 SYNC_MAX_BYTES 이하 · 링크·읽기 실패·큰 파일·docx/pdf = 미검사(UNKNOWN) 진단 (조용히 통과 X)
- 전달: exit 1 stderr 는 디스패처가 exit 0 로 내보내 Claude 에 안 간다 → PostToolUse additionalContext (비차단)
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from _common import Result, load_script, tool_input


def _ctx_msg(text: str) -> Result:
    return Result(0, json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text}},
                                ensure_ascii=False), "")


def run(ctx):
    fp = tool_input(ctx).get("file_path") or ""
    if not isinstance(fp, str) or not fp:
        return None
    mod = load_script("verify-teaching-doc-sections")
    if mod is None or not hasattr(mod, "missing_sections"):
        return None
    path = Path(fp)
    suf = path.suffix.lower()
    if suf not in (".md", ".txt", ".docx", ".pdf") or not mod.is_teaching_path(fp):
        return None
    shown = os.path.normpath(fp)
    if suf not in mod.SYNC_SUFFIXES:
        return _ctx_msg(f"[teaching-doc UNKNOWN] {shown} — {suf} 는 응답 경로에서 검사하지 않음 · "
                        f"확인: python .claude/scripts/verify-teaching-doc-sections.py \"{shown}\"")
    try:
        if path.is_symlink():
            return _ctx_msg(f"[teaching-doc UNKNOWN] {shown} — 링크 파일은 검사하지 않음")
        size = path.stat().st_size
        if size > mod.SYNC_MAX_BYTES:
            return _ctx_msg(f"[teaching-doc UNKNOWN] {shown} — {size // 1024}KB > 상한 {mod.SYNC_MAX_BYTES // 1024}KB · CLI 로 확인")
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return _ctx_msg(f"[teaching-doc UNKNOWN] {shown} — 읽기 실패 ({type(e).__name__})")
    missing = mod.missing_sections(text, suf)
    if not missing:
        return None
    return _ctx_msg(f"[teaching-doc] 8섹션 중 제목·표에서 못 찾은 것 {len(missing)}개: {missing} · {shown} "
                    f"(.claude/rules/teaching-doc.md § 각 챕터 필수 8 섹션 · 비차단 안내)")
