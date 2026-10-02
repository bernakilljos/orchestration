#!/usr/bin/env python3
"""merge-to-target — kit 인프라를 기존 프로젝트에 **병합** (덮어쓰기 X · 중복 제외).

install-to-target.sh 는 rules/·plugins/ 를 rm -rf 후 통째 복사 → 대상 고유 파일이 사라지고,
commands·skills·agents·settings hook 은 아예 안 갔다. 이 스크립트가 그 병합판이다.

같은 경로 파일 판정 (내용 기준 · 추측 X):
  identical      → skip (중복)
  stale-kit      → 대상 내용이 kit git 이력의 과거 버전과 바이트 동일 = 옛 kit 사본 → 최신으로 교체
  target-custom  → 어느 kit 버전과도 다름 = 대상에서 고친 것 → 보존 (보고만)
  kit-only       → 추가
  target-only    → 보존

settings.json : hook 은 command 문자열 기준 합집합 · permissions.allow 합집합 ·
                없는 최상위 키만 추가 · statusLine 은 없거나 전역(~/.claude) 옛 스크립트일 때만 kit 포인터로.
.mcp.json     : 없는 서버만 추가.
메모리        : setup/templates/user_style_profile.md → 대상 프로젝트 memory + .claude/state (없을 때).
CLAUDE.md     : 건드리지 않음 (프로젝트 헌장).

사용: python merge-to-target.py <TARGET> [--apply]   (기본 = 미리보기)
      python merge-to-target.py --all --apply           (.claude/state/merge-targets.txt 전부 · git post-merge 가 호출)
백업: <TARGET>/.claude/backups/kit-merge-<ts>/ (교체되는 파일만)
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

KIT = Path(__file__).resolve().parents[2]
TREES = [
    ".claude/rules", ".claude/hooks", ".claude/scripts", ".claude/commands",
    ".claude/skills", ".claude/agents", "plugins", ".claude-plugin",
]
SKIP_PARTS = {"__pycache__", "backups", "state", "logs", "tasks", "context-cache", "learning"}
SKIP_SUFFIX = {".pyc", ".bak", ".orig", ".log"}


def md5(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def git_history_hashes(rel: str) -> set[str]:
    """kit git 이력에 있었던 이 경로의 모든 내용 hash (CRLF/LF 둘 다)."""
    out: set[str] = set()
    try:
        revs = subprocess.run(
            ["git", "-C", str(KIT), "log", "--all", "--format=%H", "--", rel],
            capture_output=True, text=True, timeout=60,
        ).stdout.split()
        for r in revs[:200]:
            blob = subprocess.run(
                ["git", "-C", str(KIT), "show", f"{r}:{rel}"], capture_output=True, timeout=30,
            ).stdout
            if blob:
                out.add(md5(blob))
                out.add(md5(blob.replace(b"\r\n", b"\n")))
                out.add(md5(blob.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")))
    except Exception:
        pass
    return out


def norm(b: bytes) -> bytes:
    # 줄끝 통일 + CLAUDE.md 의 AUTO-STATS 한 줄(스크립트 수 등, hook 이 수시로 고침)은 비교에서 제외
    b = b.replace(b"\r\n", b"\n")
    return re.sub(rb"(?m)^> \*\*" + "현재 상태".encode("utf-8") + rb"\*\*.*$", b"", b)


def walk(root: Path, rel_tree: str):
    base = root / rel_tree
    if not base.exists():
        return
    for p in base.rglob("*"):
        if p.is_file() and not (set(p.relative_to(root).parts) & SKIP_PARTS) and p.suffix not in SKIP_SUFFIX:
            yield p.relative_to(root).as_posix()


def proj_memory_dir(target: Path) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9]", "-", str(target))
    return Path.home() / ".claude" / "projects" / safe / "memory"


def load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8-sig") or "{}")


def hook_key(cmd: str) -> str:
    """중복 판정 키 = 실행 스크립트 파일명 + 인자 (경로가 달라도 같은 hook 이면 중복).
    예: .claude/hooks/cleanup-orphans.sh SessionEnd == plugins/x/hooks/cleanup-orphans.sh SessionEnd"""
    m = re.search(r"([\w.-]+\.(?:sh|py))[\"']?(.*)$", cmd)
    return (m.group(1) + m.group(2).strip()) if m else cmd.strip()


def merge_settings(kit: dict, tgt: dict, report: list) -> dict:
    out = json.loads(json.dumps(tgt))
    # hooks: event 별 command 합집합 (대상 순서 유지, kit 것은 뒤에 append)
    kh, th = kit.get("hooks") or {}, out.setdefault("hooks", {})
    added = 0
    for ev, kmatchers in kh.items():
        have = {hook_key(h.get("command", "")) for m in th.get(ev, []) or [] for h in m.get("hooks", [])}
        for km in kmatchers or []:
            new_hooks = [h for h in km.get("hooks", []) if hook_key(h.get("command", "")) not in have]
            if not new_hooks:
                continue
            th.setdefault(ev, []).append({**{k: v for k, v in km.items() if k != "hooks"}, "hooks": new_hooks})
            have |= {hook_key(h.get("command", "")) for h in new_hooks}
            added += len(new_hooks)
    report.append(f"settings.hooks +{added}")
    # permissions.allow 합집합
    ka = (kit.get("permissions") or {}).get("allow") or []
    perm = out.setdefault("permissions", {})
    ta = perm.setdefault("allow", [])
    add_allow = [a for a in ka if a not in ta]
    ta.extend(add_allow)
    report.append(f"settings.permissions.allow +{len(add_allow)}")
    # statusLine: 없거나 전역 옛 스크립트를 가리키면 kit 포인터로
    sl = (out.get("statusLine") or {}).get("command", "")
    if not sl or ".claude/statusline_context.py" in sl.replace("\\", "/") and "$CLAUDE_PROJECT_DIR" not in sl:
        out["statusLine"] = kit.get("statusLine")
        report.append("settings.statusLine → kit 포인터")
    # 없는 최상위 키만
    for k, v in kit.items():
        if k not in out:
            out[k] = v
            report.append(f"settings.{k} 추가")
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    if sys.argv[1] == "--all":
        reg = KIT / ".claude" / "state" / "merge-targets.txt"
        rc = 0
        for line in (reg.read_text(encoding="utf-8").splitlines() if reg.exists() else []):
            if line.strip() and Path(line.strip()).is_dir():
                sys.argv = [sys.argv[0], line.strip()] + [a for a in sys.argv[2:]]
                rc |= main()
        return rc
    target = Path(sys.argv[1]).resolve()
    apply = "--apply" in sys.argv
    if not target.is_dir():
        print(f"대상 없음: {target}")
        return 2
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = target / ".claude" / "backups" / f"kit-merge-{ts}"
    stats = {k: [] for k in ("identical", "stale-kit", "target-custom", "kit-only")}
    # 이 도구가 마지막으로 써 넣은 내용 지문 — 그대로면 kit 소유 (커밋 전 버전을 복사했어도 갱신 가능)
    man_p = target / ".claude" / "state" / "kit-merge-manifest.json"
    try:
        manifest = json.loads(man_p.read_text(encoding="utf-8")) if man_p.exists() else {}
    except Exception:
        manifest = {}

    def owned(rel: str, db: bytes) -> bool:
        return manifest.get(rel) == md5(norm(db)) or md5(db) in git_history_hashes(rel)

    def put(rel: str, src: Path, dst: Path) -> None:
        shutil.copy2(src, dst)
        manifest[rel] = md5(norm(src.read_bytes()))

    for tree in TREES:
        for rel in walk(KIT, tree):
            src, dst = KIT / rel, target / rel
            sb = src.read_bytes()
            if not dst.exists():
                stats["kit-only"].append(rel)
                if apply:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    put(rel, src, dst)
                continue
            db = dst.read_bytes()
            if norm(sb) == norm(db):
                stats["identical"].append(rel)
                manifest[rel] = md5(norm(db))
                continue
            if owned(rel, db):
                stats["stale-kit"].append(rel)
                if apply:
                    (backup / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dst, backup / rel)
                    put(rel, src, dst)
            else:
                stats["target-custom"].append(rel)

    for rel in ("CLAUDE.md", "guide.txt"):
        src, dst = KIT / rel, target / rel
        if not src.exists():
            continue
        if not dst.exists():
            stats["kit-only"].append(rel)
            if apply:
                put(rel, src, dst)
        elif norm(src.read_bytes()) == norm(dst.read_bytes()):
            stats["identical"].append(rel)
        elif owned(rel, dst.read_bytes()):
            stats["stale-kit"].append(rel)
            if apply:
                backup.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, backup / rel)
                put(rel, src, dst)
        else:
            stats["target-custom"].append(rel)

    report: list[str] = []
    # settings.json
    sp = target / ".claude" / "settings.json"
    kit_s = load_json(KIT / ".claude" / "settings.json")
    tgt_s = load_json(sp)
    merged = merge_settings(kit_s, tgt_s, report)
    if apply and merged != tgt_s:
        if sp.exists():
            (backup / ".claude").mkdir(parents=True, exist_ok=True)
            shutil.copy2(sp, backup / ".claude" / "settings.json")
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # .mcp.json
    km, tm_p = load_json(KIT / ".mcp.json"), target / ".mcp.json"
    tm = load_json(tm_p)
    if km.get("mcpServers"):
        # 실행 파일이 이 PC 에 없는 서버는 넣지 않는다 (연결 실패를 퍼뜨리지 않음)
        add = {k: v for k, v in km["mcpServers"].items()
               if k not in (tm.get("mcpServers") or {}) and (v.get("url") or shutil.which(v.get("command", "")))}
        skipped = [k for k, v in km["mcpServers"].items()
                   if k not in (tm.get("mcpServers") or {}) and k not in add]
        if skipped:
            report.append(f".mcp.json 제외(실행파일 없음) {skipped}")
        report.append(f".mcp.json 서버 +{len(add)} {sorted(add)}")
        if apply and add:
            if tm_p.exists():
                shutil.copy2(tm_p, backup / ".mcp.json") if backup.exists() else None
            tm.setdefault("mcpServers", {}).update(add)
            tm_p.write_text(json.dumps(tm, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # 메모리 (스타일 프로필)
    prof = KIT / "setup" / "templates" / "user_style_profile.md"
    if prof.exists():
        mem = proj_memory_dir(target)
        for dst in (mem / "user_style_profile.md", target / ".claude" / "state" / "user_style_profile.md"):
            if not dst.exists() or norm(dst.read_bytes()) != norm(prof.read_bytes()):
                report.append(f"memory → {dst}")
                if apply:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(prof, dst)
        idx = mem / "MEMORY.md"
        line = "- [사용자 스타일 10축](user_style_profile.md) — ENFP-ADHD · 짧고 명확 · Zero-touch · 이력 먼저 (kit setup/templates 정본)\n"
        if not idx.exists() or "user_style_profile.md" not in idx.read_text(encoding="utf-8", errors="replace"):
            report.append(f"memory index → {idx}")
            if apply:
                idx.parent.mkdir(parents=True, exist_ok=True)
                with open(idx, "a", encoding="utf-8") as f:
                    f.write(line)

    if apply:
        man_p.parent.mkdir(parents=True, exist_ok=True)
        man_p.write_text(json.dumps(manifest, ensure_ascii=False, indent=0), encoding="utf-8")
    # 병합한 대상은 이 PC 의 목록에 자동 등록 → git pull (post-merge) 때 자동 재병합
    #   목록은 .claude/state/ (gitignore · PC 별) — 경로를 git 에 박지 않는다
    if apply:
        reg = KIT / ".claude" / "state" / "merge-targets.txt"
        reg.parent.mkdir(parents=True, exist_ok=True)
        cur = reg.read_text(encoding="utf-8").splitlines() if reg.exists() else []
        if str(target) not in cur:
            with open(reg, "a", encoding="utf-8") as f:
                f.write(str(target) + chr(10))
            report.append(f"자동 병합 목록 등록 → {reg}")

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"=== merge-to-target [{mode}] {target}")
    for k, v in stats.items():
        print(f"  {k:14} {len(v)}")
    for rel in stats["target-custom"]:
        print(f"    보존(대상 수정본) {rel}")
    for r in report:
        print(f"  {r}")
    if apply:
        print(f"  백업: {backup if backup.exists() else '(교체 없음)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
