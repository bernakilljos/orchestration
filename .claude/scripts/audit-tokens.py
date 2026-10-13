"""Token-cost audit — orchestration_v1 전용.

tokensave (epoko77-ai/tokensave) audit.py 의 9개 룰 중 우리 구조에 적합한 5개를
plugins/*/agents/ + plugins/*/skills/ + .claude/{agents,skills}/ 까지 전수 스캔.

5개 룰 (우리 컨텍스트):
  R1  Model Tier      — agent 의 model: 필드 opus 비율 >= 80% FAIL
  R2  HD-003          — 결정 키워드 + code-phase 키워드 0 = FAIL
  R4  CLAUDE.md/SKILL — 줄-문자 임계 (200줄+ / 8K자+)
  R5  Prompt Caching  — cache_control / prompt caching 명시 카운트
  R8  Writer Cap      — writer/drafter agent 에 per-call cap 명시

Usage:
  python .claude/scripts/audit-tokens.py
  python .claude/scripts/audit-tokens.py --json
  python .claude/scripts/audit-tokens.py --rules R1,R5

표준 라이브러리만 사용 (외부 의존 0). LLM 0회. 5초 안 완료.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # orchestration_v1 루트

DETERMINISTIC_KEYWORDS = [
    r"\bverbatim\b", r"\b1:1\s*매핑\b", r"\b1:1\s+mapping\b",
    r"\bBibTeX\b", r"\bformat\s+normalization\b", r"\bcross-?reference\b",
    r"\bdead[ -]?link\b", r"\bregex\s+transformation\b",
    r"\b결정적\b.*\b변환\b", r"\bJSON\s*정규화\b", r"\bsha256\b", r"\b해시\b",
]
CODE_SPLIT_KEYWORDS = [
    r"\bPython\b.*\b(스크립트|script|phase)\b",
    r"\bBash\b.*\b(스크립트|script)\b",
    r"code[- ]?phase", r"deterministic.*pass.*code",
    r"verify-.*\.py", r"validate-.*\.py",
]
WRITER_PATTERNS = [r"writer", r"drafter", r"집필", r"composer", r"section-writer"]
CAP_KEYWORDS = [
    r"per[- ]?call.*cap", r"output.*cap", r"\bmax\s*words\b",
    r"\bcap:\s*\d", r"분량\s*한도", r"자동\s*분할", r"섹션\s*>.*sub",
]
CACHE_KEYWORDS = [r"cache_control", r"prompt\s*caching", r"prompt_cache"]


@dataclass
class Agent:
    path: str
    name: str
    model: str
    size: int
    det_kw: int
    code_kw: int
    cache_kw: int
    cap_kw: int
    is_writer: bool


@dataclass
class Finding:
    rule_id: str
    title: str
    decision: str  # PASS / FAIL / WARN / N/A
    metric: str = ""
    evidence: list = field(default_factory=list)
    fix: str = ""


def normalize_model(raw: str) -> str:
    r = raw.strip().lower()
    for m in ("opus", "sonnet", "haiku"):
        if m in r:
            return m
    return r or "none"


def scan_agent(p: Path) -> Agent:
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        text = ""
    m = re.search(r"^model:\s*(\S+)", text, re.MULTILINE | re.IGNORECASE)
    model = normalize_model(m.group(1)) if m else "none"
    det = sum(1 for kw in DETERMINISTIC_KEYWORDS if re.search(kw, text, re.IGNORECASE))
    code = sum(1 for kw in CODE_SPLIT_KEYWORDS if re.search(kw, text, re.IGNORECASE))
    cache = sum(1 for kw in CACHE_KEYWORDS if re.search(kw, text, re.IGNORECASE))
    cap = sum(1 for kw in CAP_KEYWORDS if re.search(kw, text, re.IGNORECASE))
    name = p.name.lower()
    is_writer = any(re.search(pat, name) for pat in WRITER_PATTERNS) or \
                bool(re.search(r"(드래프트|draft|writer|집필|composer).*\b(agent|에이전트)\b", text, re.IGNORECASE))
    return Agent(
        path=str(p.relative_to(ROOT)),
        name=p.name,
        model=model,
        size=len(text),
        det_kw=det,
        code_kw=code,
        cache_kw=cache,
        cap_kw=cap,
        is_writer=is_writer,
    )


def discover_agents() -> list[Path]:
    """plugins/*/agents/*.md + .claude/agents/*.md 모두."""
    paths = []
    paths.extend(sorted((ROOT / ".claude" / "agents").glob("*.md")))
    for plug in sorted((ROOT / "plugins").iterdir()):
        if plug.is_dir():
            agents_dir = plug / "agents"
            if agents_dir.is_dir():
                paths.extend(sorted(agents_dir.glob("*.md")))
    return paths


def discover_skills() -> list[Path]:
    paths = []
    paths.extend(sorted((ROOT / ".claude" / "skills").glob("*.md")))
    for plug in sorted((ROOT / "plugins").iterdir()):
        if plug.is_dir():
            skills_dir = plug / "skills"
            if skills_dir.is_dir():
                paths.extend(sorted(skills_dir.glob("*.md")))
    return paths


def rule_R1(agents: list[Agent]) -> Finding:
    total = len(agents)
    if total == 0:
        return Finding("R1", "Model Tier (Opus 남용)", "N/A", "agent 0개")
    opus = sum(1 for a in agents if a.model == "opus")
    pct = opus / total * 100
    if pct >= 80:
        ev = [f"{a.path} (size {a.size})" for a in agents if a.model == "opus"][:5]
        return Finding("R1", "Model Tier (Opus 남용)", "FAIL",
                       f"Opus {pct:.1f}% ({opus}/{total})",
                       evidence=ev,
                       fix="크기 5K+ + 결정키워드 0 + writer 아닌 opus agent 를 Sonnet/Haiku 로 이동")
    return Finding("R1", "Model Tier (Opus 남용)", "PASS",
                   f"Opus {pct:.1f}% ({opus}/{total})")


def rule_R2(agents: list[Agent]) -> Finding:
    risky = [a for a in agents if a.det_kw > 0 and a.code_kw == 0]
    if not risky:
        return Finding("R2", "HD-003 (결정적 작업 LLM 위임)", "PASS",
                       "결정 키워드 있는 모든 agent 가 code-phase 키워드 포함")
    ev = [f"{a.path} (det_kw={a.det_kw}, code_kw={a.code_kw})" for a in risky[:5]]
    return Finding("R2", "HD-003 (결정적 작업 LLM 위임)", "FAIL",
                   f"RISKY {len(risky)}/{len(agents)}",
                   evidence=ev,
                   fix="해당 agent 의 결정 작업을 verify-*.py / validate-*.py 같은 Python phase 로 분리")


def rule_R4(skills: list[Path]) -> Finding:
    """CLAUDE.md + skill 파일들의 size 점검.

    임계: 300줄+ / 12K자+ (tokensave 영어권 200줄/8K자에서 한글 +50% 보정).
    근거: 동일 정보가 한글일 때 영어 대비 1.5~2배 길어짐 (한글 음절 = 영어 단어).
    우리 CLAUDE.md self-rule (500줄 미만) 과도 정합.
    """
    LINE_LIMIT = 300
    CHAR_LIMIT = 12000
    over = []
    files = [ROOT / "CLAUDE.md"] + skills
    for f in files:
        if not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        lines = text.count("\n") + 1
        chars = len(text)
        if lines >= LINE_LIMIT or chars >= CHAR_LIMIT:
            over.append((f, lines, chars))
    if not over:
        return Finding("R4", "비대 (CLAUDE.md/SKILL.md)", "PASS",
                       f"임계 미만 ({LINE_LIMIT}줄/{CHAR_LIMIT}자, 한글 보정): {len(files)} 파일")
    ev = [f"{f.relative_to(ROOT)} ({lines}줄, {chars}자)" for f, lines, chars in over[:10]]
    decision = "FAIL" if any(c >= CHAR_LIMIT for _, _, c in over) else "WARN"
    return Finding("R4", "비대 (CLAUDE.md/SKILL.md)", decision,
                   f"{len(over)} 파일 임계 초과 ({LINE_LIMIT}줄/{CHAR_LIMIT}자)",
                   evidence=ev,
                   fix=f"{LINE_LIMIT}줄+/{CHAR_LIMIT}자+ 파일을 references/ 로 분리하고 본문엔 트리거+actionable만")


def rule_R5(agents: list[Agent], skills: list[Path]) -> Finding:
    """cache_control / prompt caching 명시 카운트 (agent + skill + scripts)."""
    cache_in_agents = sum(1 for a in agents if a.cache_kw > 0)
    cache_in_skills = 0
    for sk in skills:
        try:
            text = sk.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if any(re.search(kw, text, re.IGNORECASE) for kw in CACHE_KEYWORDS):
            cache_in_skills += 1
    # scripts 안 실제 사용 카운트
    cache_in_scripts = 0
    scripts_dir = ROOT / ".claude" / "scripts"
    if scripts_dir.is_dir():
        for p in scripts_dir.rglob("*.py"):
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if any(re.search(kw, text, re.IGNORECASE) for kw in CACHE_KEYWORDS):
                cache_in_scripts += 1
    total = cache_in_agents + cache_in_skills + cache_in_scripts
    if total == 0:
        return Finding("R5", "Prompt Caching 부재", "FAIL",
                       "cache_control / prompt caching 언급 0회",
                       fix="docs/caching-strategy.md 의 3단계 TTL 적용 + cache_control 명시")
    if total < 3:
        return Finding("R5", "Prompt Caching", "WARN",
                       f"{total} 회만 명시 (agent {cache_in_agents} + skill {cache_in_skills} + scripts {cache_in_scripts})",
                       fix="agent 정의에 cache_control 명시 추가로 PASS 도달 가능")
    return Finding("R5", "Prompt Caching", "PASS",
                   f"{total} 회 명시 (agent {cache_in_agents} + skill {cache_in_skills} + scripts {cache_in_scripts})")


def rule_R8(agents: list[Agent]) -> Finding:
    writers = [a for a in agents if a.is_writer]
    if not writers:
        return Finding("R8", "Writer Cap (HD-011)", "N/A", "writer/drafter agent 0개")
    no_cap = [a for a in writers if a.cap_kw == 0]
    if not no_cap:
        return Finding("R8", "Writer Cap (HD-011)", "PASS",
                       f"writer {len(writers)} 모두 cap 명시")
    ev = [f"{a.path} (cap_kw=0)" for a in no_cap[:5]]
    decision = "FAIL" if len(no_cap) == len(writers) else "WARN"
    return Finding("R8", "Writer Cap (HD-011)", decision,
                   f"{len(no_cap)}/{len(writers)} writer 가 cap 없음",
                   evidence=ev,
                   fix="해당 writer 본문에 per-call cap (max words / 자동 분할) 명시")


def main():
    parser = argparse.ArgumentParser(description="orchestration_v1 token-cost audit")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--rules", default="R1,R2,R4,R5,R8")
    args = parser.parse_args()

    agents = [scan_agent(p) for p in discover_agents()]
    skills = discover_skills()

    rule_map = {
        "R1": lambda: rule_R1(agents),
        "R2": lambda: rule_R2(agents),
        "R4": lambda: rule_R4(skills),
        "R5": lambda: rule_R5(agents, skills),
        "R8": lambda: rule_R8(agents),
    }
    targets = [r.strip() for r in args.rules.split(",") if r.strip() in rule_map]
    findings = [rule_map[r]() for r in targets]

    stats = {
        "agents_total": len(agents),
        "skills_total": len(skills),
        "opus_count": sum(1 for a in agents if a.model == "opus"),
        "sonnet_count": sum(1 for a in agents if a.model == "sonnet"),
        "haiku_count": sum(1 for a in agents if a.model == "haiku"),
        "none_model": sum(1 for a in agents if a.model == "none"),
        "writer_count": sum(1 for a in agents if a.is_writer),
        "fail_count": sum(1 for f in findings if f.decision == "FAIL"),
        "warn_count": sum(1 for f in findings if f.decision == "WARN"),
        "pass_count": sum(1 for f in findings if f.decision == "PASS"),
        "na_count": sum(1 for f in findings if f.decision == "N/A"),
    }

    if args.json:
        print(json.dumps({
            "stats": stats,
            "findings": [asdict(f) for f in findings],
        }, ensure_ascii=False, indent=2))
        return 0

    print(f"=== orchestration_v1 token-cost audit ===")
    print(f"agents: {stats['agents_total']} (opus={stats['opus_count']}, sonnet={stats['sonnet_count']}, haiku={stats['haiku_count']}, none={stats['none_model']})")
    print(f"skills: {stats['skills_total']}, writers: {stats['writer_count']}")
    print(f"score:  PASS={stats['pass_count']} WARN={stats['warn_count']} FAIL={stats['fail_count']} N/A={stats['na_count']}")
    print()
    for f in findings:
        marker = {"PASS": "[OK]", "FAIL": "[!!]", "WARN": "[~~]", "N/A": "[--]"}[f.decision]
        print(f"  {marker} {f.rule_id} {f.title}")
        if f.metric:
            print(f"        metric: {f.metric}")
        if f.evidence:
            print(f"        evidence ({len(f.evidence)}):")
            for e in f.evidence[:5]:
                print(f"          - {e}")
        if f.fix and f.decision in ("FAIL", "WARN"):
            print(f"        fix: {f.fix}")
        print()
    return 0 if stats["fail_count"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
