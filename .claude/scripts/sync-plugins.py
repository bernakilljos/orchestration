#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
sync-plugins.py — plugins/ -> .claude/ 단방향 동기화 (bash → Python 재작성, 2026-10-13)

왜 Python: bash sync-plugins.sh 는 cmp -s per-file 로 300+ 파일 process spawn → 71~138초.
Python 은 hashlib.md5 in-process batch 로 수초 완료.

사용법 (bash 와 동일):
  python .claude/scripts/sync-plugins.py              실제 동기화
  python .claude/scripts/sync-plugins.py --dry        미리보기
  python .claude/scripts/sync-plugins.py --check      드리프트-orphan 점검
  python .claude/scripts/sync-plugins.py --verbose    상세
  python .claude/scripts/sync-plugins.py --prune      orphan 삭제

종료 코드: drift 또는 orphan 있으면 2, 정상 0.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass  # noqa: BLE001

REPO_ROOT = Path(__file__).resolve().parents[2]
SUBDIRS = ("commands", "skills", "agents")

# 충돌 룰 — 여러 플러그인에 동명 파일 있을 때만 사용
RENAME_MAP = {
    "mcp_collab/commands/install.md": "mcp_collab-install.md",
    "mcp_collab/commands/status.md": "mcp_collab-status.md",
    "mcp_data/commands/install.md": "mcp_data-install.md",
    "mcp_data/commands/status.md": "mcp_data-status.md",
    "mcp_dev/commands/install.md": "mcp_dev-install.md",
    "mcp_dev/commands/status.md": "mcp_dev-status.md",
    "mcp_docs/commands/install.md": "mcp_docs-install.md",
    "mcp_docs/commands/status.md": "mcp_docs-status.md",
    "mcp_media/commands/install.md": "mcp_media-install.md",
    "mcp_media/commands/status.md": "mcp_media-status.md",
    "mcp_web/commands/install.md": "mcp_web-install.md",
    "mcp_web/commands/status.md": "mcp_web-status.md",
    "mcp_social/commands/install.md": "mcp_social-install.md",
    "mcp_social/commands/status.md": "mcp_social-status.md",
    "mcp_social/commands/auth.md": "mcp_social-auth.md",
    "mcp_queue/commands/install.md": "mcp_queue-install.md",
    "sec_guidance/commands/install.md": "sec_guidance-install.md",
    "exec_remote/commands/setup.md": "exec_remote-setup.md",
    "exec_remote/commands/ssh.md": "exec_remote-ssh.md",
    "exec_remote/commands/deploy.md": "exec_remote-deploy.md",
    "exec_remote/commands/mobile.md": "exec_remote-mobile.md",
    "exec_remote/commands/tmux.md": "exec_remote-tmux.md",
    "exec_remote/commands/status.md": "exec_remote-status.md",
}

LEGACY_SKILL_PATTERNS = ("skill-0", "skill-1", "skill-2", "skill-3", "skill-4")


def md5(path: Path) -> str:
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except Exception:
        return ""
    return h.hexdigest()


def resolve_plugin_order() -> list[str]:
    script = REPO_ROOT / ".claude/scripts/resolve-plugin-order.py"
    if script.exists():
        try:
            r = subprocess.run([sys.executable, str(script)],
                               capture_output=True, text=True, timeout=20,
                               cwd=str(REPO_ROOT))
            if r.returncode == 0:
                order = [l.strip() for l in r.stdout.replace("\r", "").split("\n") if l.strip()]
                if order:
                    return order
        except Exception:
            pass
    # fallback: plugins/ 디렉토리 알파벳 순서
    plugins_dir = REPO_ROOT / "plugins"
    return sorted(p.name for p in plugins_dir.iterdir()
                  if p.is_dir() and p.name != "_template")


def load_orphan_allow() -> set[str]:
    allow_file = REPO_ROOT / ".claude/orphan-allow.txt"
    allow: set[str] = set()
    if not allow_file.exists():
        return allow
    try:
        for line in allow_file.read_text(encoding="utf-8").split("\n"):
            s = line.split("#", 1)[0].strip()
            if s:
                allow.add(s)
    except Exception:
        pass
    return allow


def is_legacy_skill(name: str) -> bool:
    if not name.startswith("skill-"):
        return False
    rest = name[6:]
    if not rest or not rest[0].isdigit():
        return False
    return any(name.startswith(p) for p in LEGACY_SKILL_PATTERNS)


def main() -> int:
    ap = argparse.ArgumentParser(description="plugins/ → .claude/ 동기화 (Python 2026-10-13)")
    ap.add_argument("--dry", "--dry-run", action="store_true", help="미리보기")
    ap.add_argument("--check", action="store_true", help="드리프트-orphan 점검만")
    ap.add_argument("--prune", action="store_true", help="orphan 자동 삭제")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    mode = "check" if args.check else ("dry" if args.dry else "sync")
    print(f"=== sync-plugins.py (mode={mode}) ===")

    copied = skipped = renamed = drift = orphan = 0
    reverse_map: dict[str, Path] = {}  # ".claude/<sub>/<name>" -> plugins src

    order = resolve_plugin_order()

    for plugin in order:
        plugin_dir = REPO_ROOT / "plugins" / plugin
        if not plugin_dir.is_dir():
            continue
        for sub in SUBDIRS:
            sub_dir = plugin_dir / sub
            if not sub_dir.is_dir():
                continue
            for src in sorted(sub_dir.glob("*.md")):
                name = src.name
                if name.lower() in {"readme.md"}:
                    continue
                key = f"{plugin}/{sub}/{name}"
                target_name = RENAME_MAP.get(key, name)
                dst = REPO_ROOT / ".claude" / sub / target_name
                dst_key = f"{sub}/{target_name}"
                reverse_map[dst_key] = src
                if target_name != name:
                    renamed += 1

                if dst.exists():
                    # md5 비교 (in-process · process spawn 없음 → 빠름)
                    if md5(src) == md5(dst):
                        skipped += 1
                        continue
                    # 역방향 drift 감지 (dst 가 src 보다 신규)
                    if mode == "check" or args.verbose:
                        try:
                            if dst.stat().st_mtime > src.stat().st_mtime:
                                rel_dst = dst.relative_to(REPO_ROOT)
                                rel_src = src.relative_to(REPO_ROOT)
                                print(f"[WARN]  DRIFT: {rel_dst} 가 {rel_src} 보다 새로움 (.claude/ 직접 수정 의심)")
                                drift += 1
                        except Exception:
                            pass

                rel_src = src.relative_to(REPO_ROOT)
                rel_dst = dst.relative_to(REPO_ROOT)
                if mode == "dry":
                    print(f"[DRY] {rel_src} -> {rel_dst}")
                    copied += 1
                elif mode == "sync":
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    if args.verbose:
                        print(f"[SYNC] {rel_src} -> {rel_dst}")
                    copied += 1
                else:  # check
                    print(f"[DIFF] {rel_src} ↔ {rel_dst}")
                    copied += 1

    # Orphan 점검
    print("\n=== Orphan 점검 ===")
    orphan_allow = load_orphan_allow()
    orphan_list: list[Path] = []
    for sub in SUBDIRS:
        sub_dir = REPO_ROOT / ".claude" / sub
        if not sub_dir.is_dir():
            continue
        for f in sorted(sub_dir.glob("*.md")):
            dst_key = f"{sub}/{f.name}"
            if dst_key in reverse_map:
                continue
            if is_legacy_skill(f.name):
                continue
            if f.name in orphan_allow:
                continue
            orphan_list.append(f)

    orphan = len(orphan_list)
    if orphan > 0:
        print(f"[WARN]  Orphan {orphan} 개 발견 (plugins/ 에 원본 없음):")
        for f in orphan_list:
            print(f"   - {f.relative_to(REPO_ROOT)}")
        if args.prune:
            print("   [--prune] 삭제 진행...")
            for f in orphan_list:
                try:
                    f.unlink()
                    print(f"      ✂ {f.relative_to(REPO_ROOT)} 삭제됨")
                except Exception as e:
                    print(f"      [WARN] {f.relative_to(REPO_ROOT)} 삭제 실패: {e}")
            orphan = 0
        else:
            print("   해결: plugins/<name>/commands/<name>.md 로 이동 또는 --prune 으로 일괄 삭제")
    else:
        print("✓ Orphan 없음")

    print("\n=== Summary ===")
    print(f"  copied/changed: {copied}")
    print(f"  skipped (identical): {skipped}")
    print(f"  renamed (conflict): {renamed}")
    print(f"  drift (.claude manual edit suspected): {drift}")
    print(f"  orphan: {orphan}")

    tail = {"dry": "(dry run — 실제 파일 변경 없음)",
            "check": "(check mode — 드리프트-orphan 점검만)",
            "sync": "✓ sync complete"}
    print(f"  {tail[mode]}")

    return 2 if (drift > 0 or orphan > 0) else 0


if __name__ == "__main__":
    sys.exit(main())
