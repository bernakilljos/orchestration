#!/usr/bin/env python3
"""
플러그인 개요 — 상태별 색상 표시 + 카운트.

사용법:
  python .claude/scripts/plugin-overview.py              전체 개요
  python .claude/scripts/plugin-overview.py --no-color   색상 없음
  python .claude/scripts/plugin-overview.py <plugin>     단일 플러그인 상세

상태 색상:
  ✓ stable       (녹색)
  [FAST] experimental (노란색)
  [NOTE] spec-only   (회색)
  [WARN] deprecated  (빨강)
"""
import json, sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

USE_COLOR = True
target = None

for arg in sys.argv[1:]:
    if arg == "--no-color":
        USE_COLOR = False
    elif not arg.startswith("-"):
        target = arg

# ANSI 색상 (Windows Terminal / Git Bash 지원)
C = {
    "green":  "\033[32m",
    "yellow": "\033[33m",
    "gray":   "\033[90m",
    "red":    "\033[31m",
    "bold":   "\033[1m",
    "reset":  "\033[0m",
}
if not USE_COLOR:
    C = {k: "" for k in C}

STATUS_STYLE = {
    "stable":       (C["green"], "✓", "완성"),
    "experimental": (C["yellow"], "[FAST]", "실험"),
    "spec-only":    (C["gray"], "[NOTE]", "스펙만"),
    "deprecated":   (C["red"], "[WARN]", "폐기"),
}

plugins_dir = Path("plugins")
entries = []
for p in sorted(plugins_dir.iterdir()):
    if not p.is_dir() or p.name.startswith("_"):
        continue
    pj = p / "plugin.json"
    if not pj.exists():
        continue
    try:
        data = json.loads(pj.read_text(encoding="utf-8"))
        entries.append((p.name, data))
    except Exception:
        continue

if target:
    # 단일 상세
    hit = next((e for e in entries if e[0] == target), None)
    if not hit:
        print(f"플러그인 '{target}' 없음")
        sys.exit(1)
    name, d = hit
    status = d.get("status", "unknown")
    color, icon, label = STATUS_STYLE.get(status, (C["gray"], "?", "미분류"))
    print(f"{color}{C['bold']}{icon} {name}{C['reset']} v{d.get('version', '')}")
    print(f"  {d.get('display', '')}")
    print(f"  Status: {color}{status}{C['reset']} ({label}) | Phase: {d.get('phase', '-')}")
    deps = d.get("dependencies", {}).get("plugins", [])
    if deps:
        print(f"  의존: {', '.join(deps)}")
    ep = d.get("entry_points", {})
    if ep.get("default_command"):
        print(f"  기본: /{ep['default_command']}")
    if ep.get("core_skills"):
        print(f"  핵심 스킬: {', '.join(ep['core_skills'])}")
    sys.exit(0)

# 전체 개요
count = {s: 0 for s in STATUS_STYLE}
print(f"{C['bold']}=== 플러그인 개요 ({len(entries)}개) ==={C['reset']}\n")

by_phase = {}
for name, d in entries:
    phase = d.get("phase", 0)
    by_phase.setdefault(phase, []).append((name, d))
    st = d.get("status", "unknown")
    if st in count:
        count[st] += 1

for phase in sorted(by_phase):
    phase_label = {0: "Phase 0 — 완성", 1: "Phase 1 — 스펙", 2: "Phase 2 — 대기", 3: "Phase 3 — 검토"}.get(phase, f"Phase {phase}")
    print(f"{C['bold']}[{phase_label}]{C['reset']}")
    for name, d in sorted(by_phase[phase]):
        status = d.get("status", "unknown")
        color, icon, _ = STATUS_STYLE.get(status, (C["gray"], "?", ""))
        display = d.get("display", "")[:60]
        print(f"  {color}{icon} {name:22s}{C['reset']} {display}")
    print()

print(f"{C['bold']}Summary:{C['reset']}")
for st, n in count.items():
    color, icon, label = STATUS_STYLE[st]
    print(f"  {color}{icon} {st:14s}{C['reset']} {n:3d}")
