#!/usr/bin/env python
"""
dedupe-rule.py — 룰 중복 섹션 자동 축약 (SoT 참조로 교체).

Operating Principles § 역할 분리 "1 규칙 = 1 SoT · 다른 파일은 [[참조]]" 적용.

사용:
  python dedupe-rule.py --dry           # 미리보기
  python dedupe-rule.py --apply         # 실제 적용 (.bak 백업)
  python dedupe-rule.py --pattern <k>   # 특정 패턴만

패턴 등록:
  verify_after_edit — "검증 후 보고" / "자동 검증" / "검증 의무" → verify-after-edit-mandatory
  common_component  — "공통 컴포넌트 먼저" / "기존 재사용" → operating-principles § 1·4

안전:
- 섹션 헤더 (## 또는 ###) 매치 → body 끝 (다음 ## 또는 EOF) 까지
- 50 chars 미만 body = skip (이미 참조로 축약된 것)
- SoT 자체 파일은 skip
- 각 파일 .bak 자동 백업
- 사용자 명시 "엔트로피 쫌 낮추자" 2026-10-16
"""
from __future__ import annotations
import argparse
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
RULES = ROOT / ".claude" / "rules"

PATTERNS = {
    "verify_after_edit": {
        "sot_file": "verify-after-edit-mandatory.md",
        "sot_slug": "verify-after-edit-mandatory",
        "section_regex": r"^(#{2,3})\s+(검증\s*후\s*보고|자동\s*검증\s*의무|수정\s*후\s*자동\s*검증|의무\s*흐름|완료\s*검증|사후\s*검증|검증\s*매트릭스|검증\s*의무|화면.*검증.*의무|검증\s*흐름)[^\n]*$",
        "sot_desc": "증명 체인 5단계 (pre→수정→post→작동 테스트→보고)",
        "principle_ref": "Operating Principles § 6 '완료는 증명' · § 10 '종료 조건'",
    },
    "common_component": {
        "sot_file": "operating-principles.md",
        "sot_slug": "operating-principles",
        "section_regex": r"^(#{2,3})\s+(공통\s*컴포넌트\s*(먼저|우선)|기존.*재사용|공통화\s*우선|함수.*중복|기존\s*자산\s*재사용|새\s*코드.*존재.*증명|재사용\s*우선|중복\s*금지)[^\n]*$",
        "sot_desc": "§ 1 조사→수정 · § 4 공통화 우선 ('이미 존재하는가?' 먼저 증명)",
        "principle_ref": "Operating Principles § 1·4",
    },
    "false_report": {
        "sot_file": "no-false-report.md",
        "sot_slug": "no-false-report",
        "section_regex": r"^(#{2,3})\s+(거짓\s*보고|False.?Report|이중\s*검증\s*의무|agent.*신뢰|PASS.*거짓)[^\n]*$",
        "sot_desc": "거짓 PASS 차단 · 이중 검증 (raw Read + mojibake grep + 백업 폴더)",
        "principle_ref": "Operating Principles § 6 '완료는 증명' · § 9 '미측정 ≠ 정상'",
    },
    "stop_prevention": {
        "sot_file": "best-practices.md",
        "sot_slug": "best-practices",
        "section_regex": r"^(#{2,3})\s+(멈춤\s*방지|사용자\s*액션\s*요구\s*금지|자동\s*우회\s*매트릭스)[^\n]*$",
        "sot_desc": "§ 멈춤 방지 — 외부 의존 fail 시 자동 우회 (폴링·backoff·대안 도구)",
        "principle_ref": "Operating Principles § 2 '범위 lock' · § 3 '최소 변경'",
    },
}

MIN_BODY_LEN = 80  # 이보다 짧으면 이미 축약된 것 — skip

# 각 파일 자체가 그 영역의 SoT · 축약 리스크 큼 (영역 특화 세부 있음)
SKIP_FILES = {
    "post-codex-verify.md",       # post-verify 특화 SoT
    "teaching-doc.md",            # 디자인 산출물 비율별 특화 (일반 verify 와 다름)
    "screen-verify.md",           # 화면/DB/API 특화 매트릭스
    "operating-principles.md",    # Operating Principles SoT 자체
    "verify-after-edit-mandatory.md",  # verify SoT 자체
    "no-false-report.md",         # false-report SoT 자체
    "best-practices.md",          # best-practices 자체 (이미 1건 수동 처리)
}


def _extract_section(text: str, section_regex: re.Pattern) -> list[tuple[int, int, str]]:
    """Return list of (start_line, end_line, section_title) tuples."""
    lines = text.split("\n")
    results = []
    i = 0
    while i < len(lines):
        m = section_regex.match(lines[i])
        if m:
            start = i
            level = len(m.group(1))  # ## = 2, ### = 3
            title = m.group(0)
            # find next ## or ### of same or higher level, or EOF
            j = i + 1
            while j < len(lines):
                lm = re.match(r"^(#{1,%d})\s" % level, lines[j])
                if lm and len(lm.group(1)) <= level:
                    break
                j += 1
            # body = lines[start+1:j]
            body_text = "\n".join(lines[start + 1:j]).strip()
            if len(body_text) >= MIN_BODY_LEN:
                results.append((start, j, title))
            i = j
        else:
            i += 1
    return results


def _build_replacement(title_line: str, pat_cfg: dict) -> str:
    """Build the replacement text for a section — reference + minimal note."""
    # title_line 유지 (헤더만), SoT 참조 추가
    return (
        f"{title_line.rstrip()} → [[{pat_cfg['sot_slug']}]]\n\n"
        f"SoT: `.claude/rules/{pat_cfg['sot_file']}` — {pat_cfg['sot_desc']}.\n"
        f"{pat_cfg['principle_ref']} 정합. 중복 본문 삭제 (2026-10-16 · 사용자 지시 '엔트로피 쫌 낮추자').\n"
    )


def process_file(path: Path, pat_key: str, pat_cfg: dict, apply: bool) -> tuple[int, list[str]]:
    """Return (num_sections_rewritten, log_lines)."""
    if path.name == pat_cfg["sot_file"]:
        return 0, []
    if path.name in SKIP_FILES:
        return 0, []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return 0, [f"[ERR] cannot read {path}"]

    section_re = re.compile(pat_cfg["section_regex"], re.MULTILINE | re.IGNORECASE)
    sections = _extract_section(text, section_re)
    if not sections:
        return 0, []

    log = [f"[{pat_key}] {path.name}: {len(sections)} 섹션 축약 후보"]
    lines = text.split("\n")
    # process in reverse order (indices stable)
    for start, end, title in reversed(sections):
        replacement = _build_replacement(lines[start], pat_cfg)
        log.append(f"    {start+1}~{end}: {title.strip()} → 축약 ({end-start-1}줄 삭제)")
        if apply:
            lines[start:end] = replacement.rstrip("\n").split("\n")

    if apply:
        bak = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, bak)
        path.write_text("\n".join(lines), encoding="utf-8")
        log.append(f"    → applied · .bak backup")
    else:
        log.append(f"    → DRY-RUN (--apply 로 적용)")

    return len(sections), log


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="실제 적용 (기본은 dry-run)")
    ap.add_argument("--pattern", choices=list(PATTERNS.keys()) + ["all"], default="all")
    args = ap.parse_args()

    patterns = PATTERNS if args.pattern == "all" else {args.pattern: PATTERNS[args.pattern]}
    total_files = 0
    total_sections = 0
    all_logs = []

    for pat_key, pat_cfg in patterns.items():
        print(f"\n=== 패턴: {pat_key} (SoT: {pat_cfg['sot_file']}) ===")
        for p in sorted(RULES.glob("*.md")):
            n, log = process_file(p, pat_key, pat_cfg, args.apply)
            if n > 0:
                total_files += 1
                total_sections += n
                for ln in log:
                    print(ln)

    print(f"\n=== 요약 ===")
    print(f"파일: {total_files} · 섹션: {total_sections} · 모드: {'APPLY' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[dedupe-rule] fatal: {e}", file=sys.stderr)
        sys.exit(0)
