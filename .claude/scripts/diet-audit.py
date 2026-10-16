#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
diet-audit — 중복·orphan·dead 자산 KEEP/MERGE/REMOVE/MOVE 분류 (사용자 명시 2026-10-16).

원칙 (사용자):
  - 자동 수정 X · CHANGE CANDIDATE 보고만
  - 핵심 뼈대 (Request Ledger · Standing Requirement · Stop Gate · Codex routing · 전파 · FREEZE) 건드리지 X
  - 축소 우선: SessionStart Hook · Stop Hook · 동일 목적 validation Hook · 중복 Skill · Agent 역할 중복

분류:
  KEEP   = 실제 사용 중 + 중복 X + 효과 있음
  MERGE  = 비슷한 기능 2~5개를 하나로 통합
  REMOVE = obsolete / orphan / 중복 / dead
  MOVE   = 잘못된 계층

출력: docs/ORCHESTRATION_DIET_YYYY-MM-DD.md
"""
from __future__ import annotations
import json, os, sys, re, glob, hashlib
from collections import Counter, defaultdict
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)

# 핵심 뼈대 (건드리지 X · 사용자 명시)
PROTECTED = {
    "request-ledger", "standing-requirements", "stop-request-ledger-gate",
    "stop-six-guards", "classify-task", "drift-detect", "health-check",
    "golden-test", "scope-lock", "recurrence-tracker", "operational-freeze",
    "operating-principles", "execution-contract", "six-guards",
    "sync-plugins", "sync-to-team", "install-to-target", "merge-to-target",
}


def _hash_content(path: str, max_bytes: int = 10000) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read(max_bytes)).hexdigest()[:16]
    except Exception:
        return ""


def _is_protected(path: str) -> bool:
    base = os.path.basename(path).rsplit(".", 1)[0]
    return any(p in base for p in PROTECTED)


def audit_hooks() -> dict:
    """.claude/hooks/*.sh 감사."""
    hook_dir = os.path.join(ROOT, ".claude", "hooks")
    settings = os.path.join(ROOT, ".claude", "settings.json")
    registered = set()
    try:
        with open(settings, "r", encoding="utf-8") as f:
            s = json.load(f)
        text = json.dumps(s)
        for m in re.finditer(r"\.claude[/\\]+hooks[/\\]+([\w\-.]+\.sh)", text):
            registered.add(m.group(1))
    except Exception:
        pass

    hooks = sorted(glob.glob(os.path.join(hook_dir, "*.sh")))
    hook_names = [os.path.basename(h) for h in hooks]

    # prefix 그룹화
    prefix_groups = defaultdict(list)
    for h in hook_names:
        parts = h.rsplit(".", 1)[0].split("-")
        if len(parts) >= 2:
            # 2-part prefix: pre-commit, stop-six 등
            prefix = "-".join(parts[:2])
            prefix_groups[prefix].append(h)

    result = {"KEEP": [], "MERGE": [], "REMOVE": [], "MOVE": [],
              "total": len(hooks), "registered": len(registered)}

    # ORPHAN: 등록 안 됨 (단 PreToolUse·PostToolUse 는 dispatch.py 통해 호출될 수 있음)
    orphan = []
    for h in hook_names:
        if h in registered:
            continue
        full = os.path.join(hook_dir, h)
        # tool-dispatch.py 는 전부 자동 호출 → orphan 아님 가정
        if "pre-" in h or "post-" in h or "stop-" in h or "session-" in h:
            continue  # dispatch 통한 호출
        if _is_protected(full):
            continue
        orphan.append(h)
    result["REMOVE"].extend(orphan)

    # MERGE: 3+ 같은 prefix (pre-commit-*, stop-*, session-start-*)
    for prefix, group in prefix_groups.items():
        if len(group) >= 3:
            if any(_is_protected(os.path.join(hook_dir, g)) for g in group):
                continue
            result["MERGE"].append({"prefix": prefix, "count": len(group), "files": group})

    # KEEP: 나머지
    merge_files = set()
    for m in result["MERGE"]:
        merge_files.update(m["files"])
    result["KEEP"] = [h for h in hook_names if h not in orphan and h not in merge_files]

    return result


def audit_rules() -> dict:
    """.claude/rules/*.md 감사."""
    rule_dir = os.path.join(ROOT, ".claude", "rules")
    rules = sorted(glob.glob(os.path.join(rule_dir, "*.md")))
    result = {"KEEP": [], "MERGE": [], "REMOVE": [], "MOVE": [], "total": len(rules)}

    # 참조 횟수 (grep)
    rule_names = [os.path.basename(r).rsplit(".", 1)[0] for r in rules]
    ref_count = Counter()
    try:
        import subprocess
        for name in rule_names:
            r = subprocess.run(
                ["grep", "-r", "-l", f"[[{name}]]", ROOT, "--include=*.md"],
                capture_output=True, text=True, timeout=5
            )
            ref_count[name] = len(r.stdout.splitlines())
    except Exception:
        pass

    # REMOVE: 0 참조 + 비 핵심
    for rule in rules:
        name = os.path.basename(rule).rsplit(".", 1)[0]
        if _is_protected(rule):
            continue
        if ref_count.get(name, 0) == 0:
            result["REMOVE"].append({"file": os.path.basename(rule), "refs": 0})

    # MERGE: 같은 접두 2+ 룰 (feedback-*, verify-*, no-* 등)
    prefix_groups = defaultdict(list)
    for name in rule_names:
        parts = name.split("-")
        if len(parts) >= 2:
            prefix_groups[parts[0]].append(name)
    for prefix, group in prefix_groups.items():
        if len(group) >= 3:
            if any(_is_protected(f"{p}.md") for p in group):
                continue
            result["MERGE"].append({"prefix": prefix, "count": len(group), "files": group})

    # KEEP: 나머지
    removed = {r["file"].rsplit(".", 1)[0] for r in result["REMOVE"]}
    merged = set()
    for m in result["MERGE"]:
        if isinstance(m, dict):
            merged.update(m.get("files", []))
    result["KEEP"] = [n for n in rule_names if n not in removed and n not in merged]

    return result


def audit_agents() -> dict:
    """.claude/agents/*.md 감사 — 역할 중복 검출."""
    agent_dir = os.path.join(ROOT, ".claude", "agents")
    agents = sorted(glob.glob(os.path.join(agent_dir, "*.md")))
    result = {"KEEP": [], "MERGE": [], "REMOVE": [], "total": len(agents)}

    # 역할 태그 (description 1줄 유사)
    descriptions = {}
    for a in agents:
        try:
            with open(a, "r", encoding="utf-8") as f:
                content = f.read(2000)
            m = re.search(r"description:\s*(.+?)[\n$]", content)
            if m:
                descriptions[os.path.basename(a)] = m.group(1)[:80]
        except Exception:
            pass

    # 유사 역할 (키워드 기반)
    role_groups = defaultdict(list)
    for name, desc in descriptions.items():
        keywords = {"review", "verif", "test", "code", "research", "explor", "plan", "debug", "secur"}
        for kw in keywords:
            if kw in desc.lower():
                role_groups[kw].append(name)
                break

    for kw, group in role_groups.items():
        if len(group) >= 2:
            result["MERGE"].append({"role": kw, "count": len(group), "files": group})

    merged = set()
    for m in result["MERGE"]:
        merged.update(m["files"])
    result["KEEP"] = [os.path.basename(a) for a in agents if os.path.basename(a) not in merged]

    return result


def audit_skills() -> dict:
    """plugins/*/skills/*.md — 중복 skill 검출."""
    skills = sorted(glob.glob(os.path.join(ROOT, "plugins", "*", "skills", "*.md")))
    result = {"total": len(skills), "duplicates": []}

    # 동일 slug 다중 plugin 등장
    skill_names = defaultdict(list)
    for s in skills:
        name = os.path.basename(s).rsplit(".", 1)[0]
        plugin = os.path.basename(os.path.dirname(os.path.dirname(s)))
        skill_names[name].append(plugin)

    for name, plugins in skill_names.items():
        if len(plugins) > 1:
            result["duplicates"].append({"skill": name, "plugins": plugins})

    return result


def gen_report() -> str:
    date = datetime.now().strftime("%Y-%m-%d")
    report_path = os.path.join(ROOT, "docs", f"ORCHESTRATION_DIET_{date}.md")

    hooks = audit_hooks()
    rules = audit_rules()
    agents = audit_agents()
    skills = audit_skills()

    lines = [
        f"# Orchestration Diet — {date}",
        "",
        "**원칙** (사용자 명시 2026-10-16):",
        "- 자동 수정 X · CHANGE CANDIDATE 보고만 · 사용자 승인 후만 축약",
        "- 핵심 뼈대 (Request Ledger·Standing Req·Stop Gate·Codex·전파·FREEZE) 건드리지 X",
        "- 축약 후 반드시 회귀: golden test → request → Codex → Stop Gate → 전파 → statusline → PASS면 FREEZE",
        "",
        "## 요약",
        "",
        f"| 자산 | 전체 | KEEP | MERGE 후보 | REMOVE 후보 |",
        f"|---|---|---|---|---|",
        f"| Hooks  | {hooks['total']}  | {len(hooks['KEEP'])}  | {len(hooks['MERGE'])} 그룹 | {len(hooks['REMOVE'])} |",
        f"| Rules  | {rules['total']}  | {len(rules['KEEP'])}  | {len(rules['MERGE'])} 그룹 | {len(rules['REMOVE'])} |",
        f"| Agents | {agents['total']} | {len(agents['KEEP'])} | {len(agents['MERGE'])} 그룹 | - |",
        f"| Skills | {skills['total']} | - | - | {len(skills['duplicates'])} 중복 |",
        "",
    ]

    # Hooks
    lines.extend(["## 1. Hooks", ""])
    if hooks["REMOVE"]:
        lines.extend(["### REMOVE 후보 (orphan 또는 등록 X)", ""])
        for h in hooks["REMOVE"][:20]:
            lines.append(f"- `{h}`")
        if len(hooks["REMOVE"]) > 20:
            lines.append(f"- ... + {len(hooks['REMOVE']) - 20} more")
        lines.append("")
    if hooks["MERGE"]:
        lines.extend(["### MERGE 후보 (같은 prefix 3+)", ""])
        for g in hooks["MERGE"][:10]:
            lines.append(f"- `{g['prefix']}-*` ({g['count']}개): {', '.join(g['files'][:5])}" +
                         (f" ..." if len(g["files"]) > 5 else ""))
        lines.append("")

    # Rules
    lines.extend(["## 2. Rules", ""])
    if rules["REMOVE"]:
        lines.extend(["### REMOVE 후보 (0 참조)", ""])
        for r in rules["REMOVE"][:15]:
            lines.append(f"- `{r['file']}` (refs: {r['refs']})")
        lines.append("")
    if rules["MERGE"]:
        lines.extend(["### MERGE 후보 (같은 접두 3+)", ""])
        for g in rules["MERGE"][:10]:
            if isinstance(g, dict):
                lines.append(f"- `{g['prefix']}-*` ({g['count']}개): {', '.join(g['files'][:5])}")
        lines.append("")

    # Agents
    lines.extend(["## 3. Agents", ""])
    if agents["MERGE"]:
        lines.extend(["### MERGE 후보 (역할 중복)", ""])
        for g in agents["MERGE"]:
            lines.append(f"- role `{g['role']}` ({g['count']}개): {', '.join(g['files'])}")
        lines.append("")

    # Skills
    lines.extend(["## 4. Skills (중복)", ""])
    if skills["duplicates"]:
        for d in skills["duplicates"][:15]:
            lines.append(f"- `{d['skill']}` in plugins: {', '.join(d['plugins'])}")
        lines.append("")

    lines.extend([
        "## 다음 단계",
        "",
        "1. 사용자가 CHANGE CANDIDATE 리스트 승인",
        "2. 영향 범위 분석 (각 후보 참조 그래프)",
        "3. 축약 (REMOVE → MERGE → MOVE 순)",
        "4. **회귀 테스트**:",
        "   - `python .claude/scripts/golden-test.py` → 13/13 PASS",
        "   - `python .claude/scripts/request-ledger.py gate` → exit 0",
        "   - `python .claude/scripts/standing-requirements.py gate` → exit 0",
        "   - Codex 라우팅 명시 테스트",
        "   - 전파: `bash .claude/scripts/sync-to-team.sh`",
        "5. PASS 시 **FREEZE**",
        "",
    ])

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return report_path


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "report":
        p = gen_report()
        print(f"[OK] report: {p}")
    elif cmd == "scan":
        result = {
            "hooks": audit_hooks(),
            "rules": audit_rules(),
            "agents": audit_agents(),
            "skills": audit_skills(),
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"unknown: {cmd}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERR] {e}", file=sys.stderr)
        sys.exit(1)
