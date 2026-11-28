#!/usr/bin/env python3
"""verify-teaching-doc-sections.py — 교재/강의 doc 8섹션 검증

룰: .claude/rules/teaching-doc.md
8섹션: 핵심 한 줄-표-흐름-강점-약점-강추-우리 시스템 매핑-점검

호출:
  python verify-teaching-doc-sections.py <docx_or_md_path>

종료 코드:
  0 = 통과
  1 = 누락 섹션 있음
  2 = 파일 못 읽음
"""
import re
import sys
from pathlib import Path

# R375 (2026-11-28): 이모지가 지워진 흔적으로 빈 대안(«|핵심» = 모든 문서에 맞음)과 문자 묶음([STAT] = S·T·A 아무 글자)이
#   남아 8섹션 중 7개가 사실상 항상 통과였다 → 빈 대안 제거 · 라벨은 글자 그대로([STAT] 등) 맞춤
SECTION_PATTERNS = {
    "1.핵심": r"핵심.{0,4}한.?줄|핵심\s",
    "2.표":   r"\[STAT\]|^\s*\|.*\|.*\||<table>|<tr>",
    "3.흐름": r"흐름|flow|단계|->",
    "4.강점": r"강점|장점",
    "5.약점": r"\[WARN\]|약점|주의|함정|단점",
    "6.강추": r"강추|추천|언제\s.*사용",
    "7.매핑": r"\[TGT\]|우리\s?시스템|우리\s?매핑|orchestration_v1",
    "8.점검": r"점검|check|확인|체크",
}


TEACHING_KEYS = ("teaching", "교재", "강의", "guide", "가이드", "튜토리얼", "tutorial", "docs/", "docs\\")
SYNC_SUFFIXES = (".md", ".txt")                      # 훅 응답 경로에서 검사하는 형식 (docx·pdf 는 CLI 로)
SYNC_MAX_BYTES = 2 * 1024 * 1024                     # 훅 응답 경로 크기 상한 (넘으면 UNKNOWN)


def is_teaching_path(path) -> bool:
    """교재/강의/가이드 문서 판정 — 파일명·경로 휴리스틱 (CLI·훅 공통 정본)."""
    name = str(path).lower()
    return any(k in name for k in TEACHING_KEYS)


def section_scope(text: str, suffix: str) -> str:
    """섹션 판정 대상 — md 는 제목 줄(#)과 표 줄(|)만 (본문 아무 데나 «확인»·«단계» 가 있다고 섹션으로 치지 않음) ·
    그 밖 형식은 제목 구분이 없어 전체 텍스트."""
    if suffix.lower() == ".md":
        return "\n".join(l for l in text.splitlines() if l.lstrip().startswith(("#", "|")))
    return text


def missing_sections(text: str, suffix: str) -> list:
    scope = section_scope(text, suffix)
    return [k for k, pat in SECTION_PATTERNS.items() if not re.search(pat, scope, re.IGNORECASE | re.MULTILINE)]


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        try:
            from docx import Document
            doc = Document(str(path))
            parts = [p.text for p in doc.paragraphs]
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        parts.append(cell.text)
            return "\n".join(parts)
        except Exception as e:
            print(f"[ERROR] docx 읽기 실패: {e}", file=sys.stderr)
            return ""
    elif suffix in (".md", ".txt"):
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"[ERROR] {suffix} 읽기 실패: {e}", file=sys.stderr)
            return ""
    elif suffix == ".pdf":
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(path))
            return "\n".join(page.get_text() for page in doc)
        except Exception:
            return ""
    return ""


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"[ERROR] 파일 없음: {path}", file=sys.stderr)
        sys.exit(2)

    # 교재/강의/가이드 doc 만 검증 — 파일명-경로 휴리스틱 (정본 is_teaching_path)
    if not is_teaching_path(path):
        # 비-교재 doc 은 skip
        sys.exit(0)

    text = extract_text(path)
    if not text:
        sys.exit(2)

    missing = missing_sections(text, path.suffix)
    found = [k for k in SECTION_PATTERNS if k not in missing]

    if missing:
        # systemMessage 로 Claude 에게 알림 (PostToolUse 차단 X)
        print(f"[VIOLATION] teaching-doc 8섹션 누락 ({len(missing)}/8): {missing}",
              file=sys.stderr)
        print(f"[OK] 발견: {found}", file=sys.stderr)
        print(f"[FILE] {path}", file=sys.stderr)
        print("[RULE] .claude/rules/teaching-doc.md § 각 챕터 필수 8 섹션",
              file=sys.stderr)
        sys.exit(1)

    print(f"[PASS] {path}: 8섹션 모두 발견")
    sys.exit(0)


if __name__ == "__main__":
    main()
