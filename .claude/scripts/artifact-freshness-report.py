"""산출물 신선도 스캔 - SessionStart hook 용.

CLAUDE.md § 3.2 - `.claude/rules/artifact-freshness-check.md` 룰.

유통기한 매트릭스 (SoT = 룰 문서):
  pptx catalog (AI 기술)      60일
  md   catalog (AI 기술)      45일
  install README              30일
  강의 docx                   90일
  로드맵                      180일
  CLAUDE.md § 3.2 매트릭스     21일 (Claude Code 매트릭스는 CLAUDE.md 자체 mtime 로 판정)

Stdout:
  OVERDUE 만 line 출력 (첫 응답 전 사용자 알림용).
  STALE (한계 90% 이상) 은 stderr 로 로그.
  FRESH 는 silent.

Exit code: 0 (항상).
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Windows cp949 회피 — 한글-em-dash 안전 출력
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

# ── 유통기한 매트릭스 (SoT: .claude/rules/artifact-freshness-check.md) ──
DAY = 86400  # seconds

RULES = [
    # (label,                        glob pattern,                       limit_days)
    ("AI 기술 catalog pptx",         "docs/ssj/*.pptx",                   60),
    ("AI 기술 catalog pptx",         "docs/AI_*.pptx",                    60),
    ("AI 기술 catalog md",           "docs/ssj/ai-tech-*.md",             45),
    ("install README",               "docs/install/README.md",            30),
    ("강의 docx",                    "docs/lecture-*.docx",               90),
    ("로드맵",                       "docs/**/로드맵.md",                 180),
    ("CLAUDE.md § 3.2 매트릭스",     "CLAUDE.md",                         21),
]

# 프로젝트 루트 = 이 스크립트 상위 2단계 (.claude/scripts/ 위)
ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class Finding:
    path: Path
    label: str
    age_days: float
    limit_days: int

    @property
    def state(self) -> str:
        if self.age_days > self.limit_days:
            return "OVERDUE"
        if self.age_days >= self.limit_days * 0.9:
            return "STALE"
        return "FRESH"

    @property
    def delta(self) -> str:
        d = self.age_days - self.limit_days
        return f"{d:+.0f}일"


def scan() -> list[Finding]:
    now = time.time()
    findings: list[Finding] = []
    seen: set[Path] = set()

    for label, pattern, limit in RULES:
        # glob relative to ROOT — supports ** via Path.rglob when needed
        if "**" in pattern:
            base_pat = pattern.split("/**/", 1)[0]
            tail = pattern.split("/**/", 1)[1]
            base = ROOT / base_pat
            if base.exists():
                matches = list(base.rglob(tail))
            else:
                matches = []
        else:
            matches = list(ROOT.glob(pattern))

        for p in matches:
            if p in seen or not p.is_file():
                continue
            # skip backups
            if p.name.endswith((".bak", ".tmp", ".orig")):
                continue
            seen.add(p)
            age = (now - p.stat().st_mtime) / DAY
            findings.append(Finding(p, label, age, limit))

    return findings


def main() -> int:
    findings = scan()
    overdue = [f for f in findings if f.state == "OVERDUE"]
    stale = [f for f in findings if f.state == "STALE"]

    if overdue:
        print("[산출물 유통기한 초과 — 갱신 필요]")
        for f in sorted(overdue, key=lambda x: x.age_days - x.limit_days, reverse=True):
            rel = f.path.relative_to(ROOT).as_posix()
            print(f"  OVERDUE  {rel} — {f.age_days:.0f}일 - 한계 {f.limit_days}일 - {f.delta}  [{f.label}]")

    if stale:
        for f in sorted(stale, key=lambda x: x.age_days, reverse=True):
            rel = f.path.relative_to(ROOT).as_posix()
            print(f"  STALE    {rel} — {f.age_days:.0f}일 - 한계 {f.limit_days}일 - {f.delta}  [{f.label}]",
                  file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
