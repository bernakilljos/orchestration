#!/usr/bin/env python
"""
dedupe-skill.py — 중복 skill 자동 REMOVE (plugins SoT 지정).

전제:
- `.claude/skills/` 는 sync 결과물 (plugins/ 가 SoT)
- 같은 skill name 이 여러 plugins/ 에 있으면 → **ownership plugin** 1개만 유지 · 나머지 REMOVE
- MD5 해시 동일 → 명백 중복 (안전 REMOVE)

ownership plugin 지정 (어느 plugin 이 소유):
- `ai-*` skills → `plugins/exec_orch/skills/`
- `skill-01~45` → `plugins/exec_orch/skills/` or 역할 별 (claude-* 는 exec_claude)
- 그 외 → 가장 많이 쓰는 plugin (혹은 명시 매핑)

사용:
  python dedupe-skill.py --scan              # 중복 리포트만
  python dedupe-skill.py --apply             # 실제 REMOVE (.bak 폴더로 이동)
  python dedupe-skill.py --apply --unsafe    # 해시 다름도 REMOVE (경고 — 사용자 명시)

안전:
- MD5 동일만 REMOVE (기본). unsafe = 다른 해시도.
- 삭제 전 `.claude/state/skill-removed/<timestamp>/` 로 이동 (롤백 가능)
- `.claude/skills/` 전역 복사본은 유지 (sync 결과물)
- 사용자 명시 "다 · 계속" 2026-10-16
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
GLOBAL_SKILLS = ROOT / ".claude" / "skills"
TRASH = ROOT / ".claude" / "state" / "skill-removed"

# ownership plugin — 어느 plugin 이 소유 (SoT) 인지 매핑
# 매핑 안 된 경우 = 알파벳순 첫 plugin 유지
OWNERSHIP = {
    # ai-* 시리즈는 exec_orch
    "ai-affective-emotion": "exec_orch",
    "ai-biometric-auth": "exec_orch",
    "ai-domain-fm": "exec_orch",
    "ai-governance-iso42001": "exec_orch",
    "ai-learning-finetune": "exec_orch",
    "ai-physical-world-models": "exec_orch",
    "ai-privacy-pet": "exec_orch",
    "ai-quantum-ml": "exec_orch",
    "ai-rag-bundle": "exec_orch",
    "ai-risk-lighthouse": "exec_orch",
    "ai-security-bundle": "exec_orch",
    # auto-* / 자동화
    "auto-compact": "exec_orch",
    "auto-layout-fit": "exec_orch",
    "auto-planner": "exec_orch",
    "asset-creation-workflow": "exec_orch",
    "external-trends-sync": "exec_orch",
    "feature-discovery": "exec_orch",
    # prompt·meta
    "causal-ai": "exec_orch",
    "claude-ultracode": "exec_orch",
    "constitutional-ai": "exec_orch",
    "cloud-provider-select": "exec_orch",
    "graphrag-behavior": "exec_orch",
    "meta-prompting": "exec_orch",
    "prompt-techniques": "exec_orch",
    "route_dispatch": "exec_orch",
    "self-critique-loop": "exec_orch",
    "tot-prompting": "exec_orch",
    # review·judge
    "skill-03-review": "review_qa",
    # media/doc
    "skill-22-remotion": "design_ppt",
    "skill-25-media-enhance": "mcp_media",
    "skill-34-code-docs": "mcp_docs",
}


def _md5(path: Path) -> str:
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def _collect() -> dict[str, list[Path]]:
    """Collect all skill files by basename (stem)."""
    groups = defaultdict(list)
    for p in PLUGINS.glob("*/skills/*.md"):
        stem = p.stem
        groups[stem].append(p)
    return groups


def _owner(stem: str, paths: list[Path]) -> Path:
    """Pick the SoT path for a skill."""
    desired_plugin = OWNERSHIP.get(stem)
    if desired_plugin:
        for p in paths:
            if f"plugins/{desired_plugin}/" in str(p).replace("\\", "/") or f"plugins\\{desired_plugin}\\" in str(p):
                return p
    # fallback — alphabetical first (deterministic)
    return sorted(paths, key=lambda p: str(p))[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="실제 REMOVE (.state/skill-removed/ 로 이동)")
    ap.add_argument("--unsafe", action="store_true", help="해시 다름도 REMOVE (사용자 명시)")
    args = ap.parse_args()

    groups = _collect()
    dup_groups = {k: v for k, v in groups.items() if len(v) > 1}

    total_dup_files = sum(len(v) - 1 for v in dup_groups.values())
    print(f"=== Skills 중복 분석 ===")
    print(f"총 그룹: {len(groups)} · 중복 그룹: {len(dup_groups)} · 삭제 후보 파일: {total_dup_files}")
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
        print(f"[{stem}] ownership: {owner.relative_to(ROOT)}")

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
                    # move to trash
                    rel = p.relative_to(ROOT)
                    target = trash_dir / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.move(str(p), str(target))
                        removed += 1
                    except Exception as e:
                        print(f"        [ERR] move fail: {e}")
                else:
                    unsafe_skipped += 1

    print()
    print(f"=== 요약 ===")
    print(f"유지 (SoT): {kept}")
    print(f"REMOVE: {removed} · 다른 해시 (--unsafe 필요): {unsafe_skipped}")
    print(f"모드: {'APPLY' if args.apply else 'SCAN'}")
    if args.apply and removed:
        print(f"백업: {trash_dir}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[dedupe-skill] fatal: {e}", file=sys.stderr)
        sys.exit(0)
