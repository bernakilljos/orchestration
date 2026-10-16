#!/usr/bin/env python
"""
dedupe-agent.py — 중복 agent 자동 REMOVE (SoT 지정).

전수조사 결과 (2026-10-16):
- agent-02-implementer × 11 플러그인
- agent-05-monitor × 3
- agent-03-reviewer × 2 (exec_orch + mcp_web)
- agent-07-code-reviewer × 2
- agent-example × 2

전략:
- MD5 동일 → SoT 1개 유지 · 나머지 REMOVE
- MD5 다름 → --unsafe 플래그 필요 (경고)
- SoT 순서: `.claude/agents/` > `plugins/exec_orch/agents/` > 기타 알파벳

사용:
  python dedupe-agent.py           # scan
  python dedupe-agent.py --apply   # 실제 REMOVE
"""
from __future__ import annotations
import argparse
import hashlib
import os
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
PLUGINS = ROOT / "plugins"
GLOBAL_AGENTS = ROOT / ".claude" / "agents"
TRASH = ROOT / ".claude" / "state" / "agent-removed"


def _md5(path: Path) -> str:
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def _collect() -> dict[str, list[Path]]:
    groups = defaultdict(list)
    # .claude/agents/
    if GLOBAL_AGENTS.exists():
        for p in GLOBAL_AGENTS.glob("*.md"):
            groups[p.stem].append(p)
    # plugins/*/agents/
    for p in PLUGINS.glob("*/agents/*.md"):
        groups[p.stem].append(p)
    return groups


def _owner(stem: str, paths: list[Path]) -> Path:
    """SoT 우선순위: .claude/agents > plugins/exec_orch > 알파벳 첫 파일"""
    # .claude/agents 우선
    for p in paths:
        if ".claude/agents" in str(p).replace("\\", "/") or ".claude\\agents" in str(p):
            return p
    # plugins/exec_orch 우선
    for p in paths:
        if "plugins/exec_orch" in str(p).replace("\\", "/") or "plugins\\exec_orch" in str(p):
            return p
    return sorted(paths, key=lambda p: str(p))[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--unsafe", action="store_true", help="해시 다름도 REMOVE")
    args = ap.parse_args()

    groups = _collect()
    dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
    total_dup = sum(len(v) - 1 for v in dup_groups.values())

    print(f"=== Agents 중복 분석 ===")
    print(f"총 그룹: {len(groups)} · 중복 그룹: {len(dup_groups)} · 삭제 후보: {total_dup}")
    print()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    trash_dir = TRASH / ts
    removed = 0
    kept = 0
    unsafe_skipped = 0

    for stem in sorted(dup_groups.keys()):
        paths = dup_groups[stem]
        owner = _owner(stem, paths)
        owner_md5 = _md5(owner)
        print(f"[{stem}] × {len(paths)} · ownership: {owner.relative_to(ROOT)}")

        for p in paths:
            if p == owner:
                kept += 1
                continue
            p_md5 = _md5(p)
            same = p_md5 == owner_md5
            marker = "✓same" if same else "⚠diff"
            print(f"    {marker} {p.relative_to(ROOT)}")
            if args.apply:
                if same or args.unsafe:
                    rel = p.relative_to(ROOT)
                    target = trash_dir / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.move(str(p), str(target))
                        removed += 1
                    except Exception as e:
                        print(f"        [ERR] {e}")
                else:
                    unsafe_skipped += 1

    print()
    print(f"=== 요약 ===")
    print(f"유지 (SoT): {kept} · REMOVE: {removed} · 다른 해시: {unsafe_skipped}")
    print(f"모드: {'APPLY' if args.apply else 'SCAN'}")
    if args.apply and removed:
        print(f"백업: {trash_dir}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[dedupe-agent] fatal: {e}", file=sys.stderr)
        sys.exit(0)
