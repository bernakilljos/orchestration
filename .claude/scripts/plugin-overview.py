#!/usr/bin/env python3
"""
?뚮윭洹몄씤 媛쒖슂 ???곹깭蹂??됱긽 ?쒖떆 + 移댁슫??

?ъ슜踰?
  python .claude/scripts/plugin-overview.py              ?꾩껜 媛쒖슂
  python .claude/scripts/plugin-overview.py --no-color   ?됱긽 ?놁쓬
  python .claude/scripts/plugin-overview.py <plugin>     ?⑥씪 ?뚮윭洹몄씤 ?곸꽭

?곹깭 ?됱긽:
  ??stable       (?뱀깋)
  [FAST] experimental (?몃???
  [NOTE] spec-only   (?뚯깋)
  [WARN] deprecated  (鍮④컯)
"""
import json, sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
    pass

USE_COLOR = True
target = None

for arg in sys.argv[1:]:
    if arg == "--no-color":
        USE_COLOR = False
    elif not arg.startswith("-"):
        target = arg

# ANSI ?됱긽 (Windows Terminal / Git Bash 吏??
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
    "stable":       (C["green"], "??, "?꾩꽦"),
    "experimental": (C["yellow"], "[FAST]", "?ㅽ뿕"),
    "spec-only":    (C["gray"], "[NOTE]", "?ㅽ럺留?),
    "deprecated":   (C["red"], "[WARN]", "?먭린"),
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
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        continue

if target:
    # ?⑥씪 ?곸꽭
    hit = next((e for e in entries if e[0] == target), None)
    if not hit:
        print(f"?뚮윭洹몄씤 '{target}' ?놁쓬")
        sys.exit(1)
    name, d = hit
    status = d.get("status", "unknown")
    color, icon, label = STATUS_STYLE.get(status, (C["gray"], "?", "誘몃텇瑜?))
    print(f"{color}{C['bold']}{icon} {name}{C['reset']} v{d.get('version', '')}")
    print(f"  {d.get('display', '')}")
    print(f"  Status: {color}{status}{C['reset']} ({label}) | Phase: {d.get('phase', '-')}")
    deps = d.get("dependencies", {}).get("plugins", [])
    if deps:
        print(f"  ?섏〈: {', '.join(deps)}")
    ep = d.get("entry_points", {})
    if ep.get("default_command"):
        print(f"  湲곕낯: /{ep['default_command']}")
    if ep.get("core_skills"):
        print(f"  ?듭떖 ?ㅽ궗: {', '.join(ep['core_skills'])}")
    sys.exit(0)

# ?꾩껜 媛쒖슂
count = {s: 0 for s in STATUS_STYLE}
print(f"{C['bold']}=== ?뚮윭洹몄씤 媛쒖슂 ({len(entries)}媛? ==={C['reset']}\n")

by_phase = {}
for name, d in entries:
    phase = d.get("phase", 0)
    by_phase.setdefault(phase, []).append((name, d))
    st = d.get("status", "unknown")
    if st in count:
        count[st] += 1

for phase in sorted(by_phase):
    phase_label = {0: "Phase 0 ???꾩꽦", 1: "Phase 1 ???ㅽ럺", 2: "Phase 2 ???湲?, 3: "Phase 3 ??寃??}.get(phase, f"Phase {phase}")
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

