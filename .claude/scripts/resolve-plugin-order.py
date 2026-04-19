#!/usr/bin/env python3
"""plugin.json dependencies 기반 위상정렬. stdout 한 줄당 플러그인 이름."""
import json, sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

plugins_dir = Path("plugins")
names = [p.name for p in plugins_dir.iterdir() if p.is_dir() and not p.name.startswith("_")]

plugins = {}
for n in names:
    pj_path = plugins_dir / n / "plugin.json"
    deps = []
    if pj_path.exists():
        try:
            pj = json.loads(pj_path.read_text(encoding="utf-8"))
            deps = [d for d in pj.get("dependencies", {}).get("plugins", []) if d in names]
        except Exception:
            pass
    plugins[n] = deps

ordered = []
visited = set()

def visit(n):
    if n in visited:
        return
    visited.add(n)
    for d in plugins.get(n, []):
        visit(d)
    ordered.append(n)

for n in sorted(plugins):
    visit(n)

for n in ordered:
    print(n)
