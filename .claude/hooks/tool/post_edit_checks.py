"""verify-teaching-doc-sections.py 이식 — Edit/Write 후 교재·강의 문서 8섹션 확인 (비차단 안내 · Claude 에 전달).

R375 Hook 경량화: 종전 settings 비동기 훅은 인자 없이 실행돼 사용법만 출력하고 exit 2 로 끝났다 (문서 미검사).
5차 검토 반영:
- 판정 정본 재사용: is_teaching_path · missing_sections (md 는 제목 줄·표 줄만) · SECTION_PATTERNS
- 응답 경로 예산: md·txt 만 · 실제 읽기량 SYNC_MAX_BYTES+1 상한 · 읽는 중 변경(크기·시각·inode) 감지 · 링크·정션·네트워크 경로·
  읽기 실패·큰 파일·docx/pdf = 미검사(UNKNOWN) 진단 (조용히 통과 X · 6차 검토)
- 전달: exit 1 stderr 는 디스패처가 exit 0 로 내보내 Claude 에 안 간다 → PostToolUse additionalContext (비차단)
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from _common import Result, load_script, tool_input


def _is_reparse(path: Path) -> bool:
    """Windows 정션·재분석 지점 (경로 상위 포함) — realpath 가 다를 때만 호출."""
    try:
        return any(bool(getattr(os.lstat(p), "st_file_attributes", 0) & 0x400) for p in [path, *path.parents])
    except OSError:
        return True


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
    if fp.startswith(("\\\\", "//")):
        return _ctx_msg(f"[teaching-doc UNKNOWN] {shown} — 네트워크 경로는 응답 경로에서 검사하지 않음")
    try:
        if path.is_symlink() or os.path.realpath(fp) != os.path.abspath(fp) and _is_reparse(path):
            return _ctx_msg(f"[teaching-doc UNKNOWN] {shown} — 링크·정션 경로는 검사하지 않음")
        st0 = path.stat()
        with open(path, "rb") as f:                       # 상한+1 바이트까지만 읽음 (stat 뒤 파일이 커져도 상한 보장)
            raw = f.read(mod.SYNC_MAX_BYTES + 1)
            st1 = os.fstat(f.fileno())
        if len(raw) > mod.SYNC_MAX_BYTES:
            return _ctx_msg(f"[teaching-doc UNKNOWN] {shown} — 상한 {mod.SYNC_MAX_BYTES // 1024}KB 초과 · CLI 로 확인")
        if (st0.st_size, st0.st_mtime_ns) != (st1.st_size, st1.st_mtime_ns) or \
                (getattr(st0, "st_ino", 0) and st0.st_ino != st1.st_ino):
            return _ctx_msg(f"[teaching-doc UNKNOWN] {shown} — 읽는 중 파일이 바뀜 · 다시 저장 후 확인")
        text = raw.decode("utf-8", errors="replace")
    except OSError as e:
        return _ctx_msg(f"[teaching-doc UNKNOWN] {shown} — 읽기 실패 ({type(e).__name__})")
    missing = mod.missing_sections(text, suf)
    if not missing:
        return None
    return _ctx_msg(f"[teaching-doc] 8섹션 중 제목·표에서 못 찾은 것 {len(missing)}개: {missing} · {shown} "
                    f"(.claude/rules/teaching-doc.md § 각 챕터 필수 8 섹션 · 비차단 안내)")
