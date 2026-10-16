#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
drift-detect — orchestration 핵심 자산의 baseline 대비 drift 감지.

목표:
- core / rule / hook / agent 변경 수 각각 집계
- 중요 파일 (core SoT) 변경 여부 별도 추적
- FREEZE 상태 / FREEZE 위반 (허가 X 변경) 감지
- statusline 용 ANSI 색상 포함 JSON 반환

색상 (사용자 명시 2026-10-16):
- 0 변경         → 회색 (90)
- 1~2 변경       → 노랑 (33)
- 3+ 변경        → 주황 (1;33)
- 중요 파일 변경 → 주황 (1;33)
- FREEZE 위반    → 빨강 (1;31)
- 검증 완료      → 초록 (1;32)
- frozen ✅       → 초록 (1;32)
- frozen ⚠       → 노랑 (33)

사용:
  python drift-detect.py status   # statusline JSON (ANSI 포함)
  python drift-detect.py scan     # 상세 scan + 파일 목록
  python drift-detect.py baseline # 현재 상태를 release-manifest.json 에 baseline 저장
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
import glob

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
MANIFEST = os.path.join(ROOT, ".claude", "state", "release-manifest.json")

# 핵심 파일 (변경 시 orange+ 승격)
CORE_FILES = [
    "CLAUDE.md",
    ".claude/rules/operating-principles.md",
    ".claude/rules/execution-contract.md",
    ".claude/rules/operational-freeze.md",
    ".claude/rules/six-guards.md",
]

RULE_GLOB = ".claude/rules/*.md"
HOOK_GLOB = ".claude/hooks/*.sh"
AGENT_GLOB = ".claude/agents/*.md"


def _hash(path: str) -> str:
    try:
        with open(os.path.join(ROOT, path), "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except Exception:
        return ""


def _scan() -> dict:
    out = {"core": {}, "rule": {}, "hook": {}, "agent": {}}
    for p in CORE_FILES:
        out["core"][p] = _hash(p)
    for p in sorted(glob.glob(os.path.join(ROOT, RULE_GLOB))):
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        out["rule"][rel] = _hash(rel)
    for p in sorted(glob.glob(os.path.join(ROOT, HOOK_GLOB))):
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        out["hook"][rel] = _hash(rel)
    for p in sorted(glob.glob(os.path.join(ROOT, AGENT_GLOB))):
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        out["agent"][rel] = _hash(rel)
    return out


def _load_manifest() -> dict:
    try:
        with open(MANIFEST, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_manifest(data: dict) -> None:
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _is_frozen() -> bool:
    freeze_f = os.path.join(ROOT, ".claude", "rules", "operational-freeze.md")
    return os.path.exists(freeze_f)


def diff(current: dict, baseline: dict) -> dict:
    """카테고리별 (changed·added·removed·core_changed) 반환."""
    result = {}
    for cat in ("core", "rule", "hook", "agent"):
        cur = current.get(cat, {})
        base = baseline.get(cat, {})
        cur_keys = set(cur.keys())
        base_keys = set(base.keys())
        added = cur_keys - base_keys
        removed = base_keys - cur_keys
        changed = {k for k in cur_keys & base_keys if cur[k] != base[k]}
        result[cat] = {
            "added": sorted(added),
            "removed": sorted(removed),
            "changed": sorted(changed),
            "total": len(added) + len(removed) + len(changed),
        }
    # core 중요 변경 (별도 bit)
    result["core_important"] = result["core"]["total"] > 0
    return result


def _color(n: int, is_core: bool = False) -> str:
    """숫자 → ANSI 색 (사용자 명시 매트릭스)."""
    if n == 0:
        return "90"  # 회색
    if is_core:
        return "1;33"  # 주황 (bold yellow) · 중요 파일 변경
    if n <= 2:
        return "33"  # 노랑
    return "1;33"  # 주황


def status_line() -> str:
    """statusline 한 줄 (ANSI 포함)."""
    cur = _scan()
    base = _load_manifest()
    if not base:
        # baseline 없음 — 지금 상태를 저장하고 모두 0 으로 표시
        _save_manifest(cur)
        base = cur
    d = diff(cur, base)
    parts = []
    for cat_key, label in (("core", "core"), ("rule", "rule"),
                            ("hook", "hook"), ("agent", "agent")):
        n = d[cat_key]["total"]
        is_core = (cat_key == "core" and n > 0)
        c = _color(n, is_core)
        warn = " ⚠" if is_core else ""
        parts.append(f"{label} \033[{c}m{n}{warn}\033[0m")
    # FREEZE 상태
    if _is_frozen():
        # FREEZE 위반 = core 변경 (의도 X 가정)
        if d["core_important"]:
            parts.append("frozen \033[1;31m⚠ 위반\033[0m")
        else:
            parts.append("frozen \033[1;32m✅\033[0m")
    else:
        parts.append("frozen \033[33m—\033[0m")
    return " · ".join(parts)


def status_json() -> dict:
    cur = _scan()
    base = _load_manifest()
    if not base:
        _save_manifest(cur)
        base = cur
    d = diff(cur, base)
    return {
        "line": status_line(),
        "diff": d,
        "frozen": _is_frozen(),
        "manifest_exists": os.path.exists(MANIFEST),
    }


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        print(status_line())
    elif cmd == "scan":
        print(json.dumps(status_json(), indent=2, ensure_ascii=False))
    elif cmd == "baseline":
        cur = _scan()
        _save_manifest(cur)
        print(f"baseline saved: {sum(len(v) for v in cur.values())} entries")
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"core \033[90m?\033[0m · rule \033[90m?\033[0m · hook \033[90m?\033[0m · agent \033[90m?\033[0m · frozen \033[90m?\033[0m", file=sys.stderr)
        sys.exit(1)
