"""Token-cost audit ??orchestration_v1 ?꾩슜.

tokensave (epoko77-ai/tokensave) audit.py ??9媛?猷?以??곕━ 援ъ“???곹빀??5媛쒕?
plugins/*/agents/ + plugins/*/skills/ + .claude/{agents,skills}/ 源뚯? ?꾩닔 ?ㅼ틪.

5媛?猷?(?곕━ 而⑦뀓?ㅽ듃):
  R1  Model Tier      ??agent ??model: ?꾨뱶 opus 鍮꾩쑉 >= 80% FAIL
  R2  HD-003          ??寃곗젙 ?ㅼ썙??+ code-phase ?ㅼ썙??0 = FAIL
  R4  CLAUDE.md/SKILL ??以?臾몄옄 ?꾧퀎 (200以? / 8K??)
  R5  Prompt Caching  ??cache_control / prompt caching 紐낆떆 移댁슫??
  R8  Writer Cap      ??writer/drafter agent ??per-call cap 紐낆떆

Usage:
  python .claude/scripts/audit-tokens.py
  python .claude/scripts/audit-tokens.py --json
  python .claude/scripts/audit-tokens.py --rules R1,R5

?쒖? ?쇱씠釉뚮윭由щ쭔 ?ъ슜 (?몃? ?섏〈 0). LLM 0?? 5珥????꾨즺.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # orchestration_v1 猷⑦듃

DETERMINISTIC_KEYWORDS = [
    r"\bverbatim\b", r"\b1:1\s*留ㅽ븨\b", r"\b1:1\s+mapping\b",
    r"\bBibTeX\b", r"\bformat\s+normalization\b", r"\bcross-?reference\b",
    r"\bdead[ -]?link\b", r"\bregex\s+transformation\b",
    r"\b寃곗젙??b.*\b蹂??b", r"\bJSON\s*?뺢퇋??b", r"\bsha256\b", r"\b?댁떆\b",
]
CODE_SPLIT_KEYWORDS = [
    r"\bPython\b.*\b(?ㅽ겕由쏀듃|script|phase)\b",
    r"\bBash\b.*\b(?ㅽ겕由쏀듃|script)\b",
    r"code[- ]?phase", r"deterministic.*pass.*code",
    r"verify-.*\.py", r"validate-.*\.py",
]
WRITER_PATTERNS = [r"writer", r"drafter", r"吏묓븘", r"composer", r"section-writer"]
CAP_KEYWORDS = [
    r"per[- ]?call.*cap", r"output.*cap", r"\bmax\s*words\b",
    r"\bcap:\s*\d", r"遺꾨웾\s*?쒕룄", r"?먮룞\s*遺꾪븷", r"?뱀뀡\s*>.*sub",
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
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        text = ""
    m = re.search(r"^model:\s*(\S+)", text, re.MULTILINE | re.IGNORECASE)
    model = normalize_model(m.group(1)) if m else "none"
    det = sum(1 for kw in DETERMINISTIC_KEYWORDS if re.search(kw, text, re.IGNORECASE))
    code = sum(1 for kw in CODE_SPLIT_KEYWORDS if re.search(kw, text, re.IGNORECASE))
    cache = sum(1 for kw in CACHE_KEYWORDS if re.search(kw, text, re.IGNORECASE))
    cap = sum(1 for kw in CAP_KEYWORDS if re.search(kw, text, re.IGNORECASE))
    name = p.name.lower()
    is_writer = any(re.search(pat, name) for pat in WRITER_PATTERNS) or \
                bool(re.search(r"(?쒕옒?꾪듃|draft|writer|吏묓븘|composer).*\b(agent|?먯씠?꾪듃)\b", text, re.IGNORECASE))
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
    """plugins/*/agents/*.md + .claude/agents/*.md 紐⑤몢."""
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
        return Finding("R1", "Model Tier (Opus ?⑥슜)", "N/A", "agent 0媛?)
    opus = sum(1 for a in agents if a.model == "opus")
    pct = opus / total * 100
    if pct >= 80:
        ev = [f"{a.path} (size {a.size})" for a in agents if a.model == "opus"][:5]
        return Finding("R1", "Model Tier (Opus ?⑥슜)", "FAIL",
                       f"Opus {pct:.1f}% ({opus}/{total})",
                       evidence=ev,
                       fix="?ш린 5K+ + 寃곗젙?ㅼ썙??0 + writer ?꾨땶 opus agent 瑜?Sonnet/Haiku 濡??대룞")
    return Finding("R1", "Model Tier (Opus ?⑥슜)", "PASS",
                   f"Opus {pct:.1f}% ({opus}/{total})")


def rule_R2(agents: list[Agent]) -> Finding:
    risky = [a for a in agents if a.det_kw > 0 and a.code_kw == 0]
    if not risky:
        return Finding("R2", "HD-003 (寃곗젙???묒뾽 LLM ?꾩엫)", "PASS",
                       "寃곗젙 ?ㅼ썙???덈뒗 紐⑤뱺 agent 媛 code-phase ?ㅼ썙???ы븿")
    ev = [f"{a.path} (det_kw={a.det_kw}, code_kw={a.code_kw})" for a in risky[:5]]
    return Finding("R2", "HD-003 (寃곗젙???묒뾽 LLM ?꾩엫)", "FAIL",
                   f"RISKY {len(risky)}/{len(agents)}",
                   evidence=ev,
                   fix="?대떦 agent ??寃곗젙 ?묒뾽??verify-*.py / validate-*.py 媛숈? Python phase 濡?遺꾨━")


def rule_R4(skills: list[Path]) -> Finding:
    """CLAUDE.md + skill ?뚯씪?ㅼ쓽 size ?먭?.

    ?꾧퀎: 300以? / 12K?? (tokensave ?곸뼱沅?200以?8K?먯뿉???쒓? +50% 蹂댁젙).
    洹쇨굅: ?숈씪 ?뺣낫媛 ?쒓??????곸뼱 ?鍮?1.5~2諛?湲몄뼱吏?(?쒓? ?뚯젅 = ?곸뼱 ?⑥뼱).
    ?곕━ CLAUDE.md self-rule (500以?誘몃쭔) 怨쇰룄 ?뺥빀.
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
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            continue
        lines = text.count("\n") + 1
        chars = len(text)
        if lines >= LINE_LIMIT or chars >= CHAR_LIMIT:
            over.append((f, lines, chars))
    if not over:
        return Finding("R4", "鍮꾨? (CLAUDE.md/SKILL.md)", "PASS",
                       f"?꾧퀎 誘몃쭔 ({LINE_LIMIT}以?{CHAR_LIMIT}?? ?쒓? 蹂댁젙): {len(files)} ?뚯씪")
    ev = [f"{f.relative_to(ROOT)} ({lines}以? {chars}??" for f, lines, chars in over[:10]]
    decision = "FAIL" if any(c >= CHAR_LIMIT for _, _, c in over) else "WARN"
    return Finding("R4", "鍮꾨? (CLAUDE.md/SKILL.md)", decision,
                   f"{len(over)} ?뚯씪 ?꾧퀎 珥덇낵 ({LINE_LIMIT}以?{CHAR_LIMIT}??",
                   evidence=ev,
                   fix=f"{LINE_LIMIT}以?/{CHAR_LIMIT}?? ?뚯씪??references/ 濡?遺꾨━?섍퀬 蹂몃Ц???몃━嫄?actionable留?)


def rule_R5(agents: list[Agent], skills: list[Path]) -> Finding:
    """cache_control / prompt caching 紐낆떆 移댁슫??(agent + skill + scripts)."""
    cache_in_agents = sum(1 for a in agents if a.cache_kw > 0)
    cache_in_skills = 0
    for sk in skills:
        try:
            text = sk.read_text(encoding="utf-8", errors="replace")
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            continue
        if any(re.search(kw, text, re.IGNORECASE) for kw in CACHE_KEYWORDS):
            cache_in_skills += 1
    # scripts ???ㅼ젣 ?ъ슜 移댁슫??
    cache_in_scripts = 0
    scripts_dir = ROOT / ".claude" / "scripts"
    if scripts_dir.is_dir():
        for p in scripts_dir.rglob("*.py"):
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
                continue
            if any(re.search(kw, text, re.IGNORECASE) for kw in CACHE_KEYWORDS):
                cache_in_scripts += 1
    total = cache_in_agents + cache_in_skills + cache_in_scripts
    if total == 0:
        return Finding("R5", "Prompt Caching 遺??, "FAIL",
                       "cache_control / prompt caching ?멸툒 0??,
                       fix="docs/caching-strategy.md ??3?④퀎 TTL ?곸슜 + cache_control 紐낆떆")
    if total < 3:
        return Finding("R5", "Prompt Caching", "WARN",
                       f"{total} ?뚮쭔 紐낆떆 (agent {cache_in_agents} + skill {cache_in_skills} + scripts {cache_in_scripts})",
                       fix="agent ?뺤쓽??cache_control 紐낆떆 異붽?濡?PASS ?꾨떖 媛??)
    return Finding("R5", "Prompt Caching", "PASS",
                   f"{total} ??紐낆떆 (agent {cache_in_agents} + skill {cache_in_skills} + scripts {cache_in_scripts})")


def rule_R8(agents: list[Agent]) -> Finding:
    writers = [a for a in agents if a.is_writer]
    if not writers:
        return Finding("R8", "Writer Cap (HD-011)", "N/A", "writer/drafter agent 0媛?)
    no_cap = [a for a in writers if a.cap_kw == 0]
    if not no_cap:
        return Finding("R8", "Writer Cap (HD-011)", "PASS",
                       f"writer {len(writers)} 紐⑤몢 cap 紐낆떆")
    ev = [f"{a.path} (cap_kw=0)" for a in no_cap[:5]]
    decision = "FAIL" if len(no_cap) == len(writers) else "WARN"
    return Finding("R8", "Writer Cap (HD-011)", decision,
                   f"{len(no_cap)}/{len(writers)} writer 媛 cap ?놁쓬",
                   evidence=ev,
                   fix="?대떦 writer 蹂몃Ц??per-call cap (max words / ?먮룞 遺꾪븷) 紐낆떆")


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

