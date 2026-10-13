#!/usr/bin/env python3
"""merge-to-target ??kit ?명봽?쇰? 湲곗〈 ?꾨줈?앺듃??**蹂묓빀** (??뼱?곌린 X 쨌 以묐났 ?쒖쇅).

install-to-target.sh ??rules/쨌plugins/ 瑜?rm -rf ???듭㎏ 蹂듭궗 ?????怨좎쑀 ?뚯씪???щ씪吏怨?
commands쨌skills쨌agents쨌settings hook ? ?꾩삁 ??媛붾떎. ???ㅽ겕由쏀듃媛 洹?蹂묓빀?먯씠??

媛숈? 寃쎈줈 ?뚯씪 ?먯젙 (?댁슜 湲곗? 쨌 異붿륫 X):
  identical      ??skip (以묐났)
  stale-kit      ??????댁슜??kit git ?대젰??怨쇨굅 踰꾩쟾怨?諛붿씠???숈씪 = ??kit ?щ낯 ??理쒖떊?쇰줈 援먯껜
  target-custom  ???대뒓 kit 踰꾩쟾怨쇰룄 ?ㅻ쫫 = ??곸뿉??怨좎튇 寃???蹂댁〈 (蹂닿퀬留?
  kit-only       ??異붽?
  target-only    ??蹂댁〈

settings.json : hook ? command 臾몄옄??湲곗? ?⑹쭛??쨌 permissions.allow ?⑹쭛??쨌
                ?녿뒗 理쒖긽???ㅻ쭔 異붽? 쨌 statusLine ? ?녾굅???꾩뿭(~/.claude) ???ㅽ겕由쏀듃???뚮쭔 kit ?ъ씤?곕줈.
.mcp.json     : ?녿뒗 ?쒕쾭留?異붽?.
硫붾え由?       : setup/templates/user_style_profile.md ??????꾨줈?앺듃 memory + .claude/state (?놁쓣 ??.
CLAUDE.md     : 嫄대뱶由ъ? ?딆쓬 (?꾨줈?앺듃 ?뚯옣).

?ъ슜: python merge-to-target.py <TARGET> [--apply]   (湲곕낯 = 誘몃━蹂닿린)
      python merge-to-target.py --all --apply           (.claude/state/merge-targets.txt ?꾨? 쨌 git post-merge 媛 ?몄텧)
諛깆뾽: <TARGET>/.claude/backups/kit-merge-<ts>/ (援먯껜?섎뒗 ?뚯씪留?
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
except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
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
    """kit git ?대젰???덉뿀????寃쎈줈??紐⑤뱺 ?댁슜 hash (CRLF/LF ????."""
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
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        pass
    return out


def norm(b: bytes) -> bytes:
    # 以꾨걹 ?듭씪 + CLAUDE.md ??AUTO-STATS ??以??ㅽ겕由쏀듃 ???? hook ???섏떆濡?怨좎묠)? 鍮꾧탳?먯꽌 ?쒖쇅
    b = b.replace(b"\r\n", b"\n")
    return re.sub(rb"(?m)^> \*\*" + "?꾩옱 ?곹깭".encode("utf-8") + rb"\*\*.*$", b"", b)


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
    """以묐났 ?먯젙 ??= ?ㅽ뻾 ?ㅽ겕由쏀듃 ?뚯씪紐?+ ?몄옄 (寃쎈줈媛 ?щ씪??媛숈? hook ?대㈃ 以묐났).
    ?? .claude/hooks/cleanup-orphans.sh SessionEnd == plugins/x/hooks/cleanup-orphans.sh SessionEnd"""
    m = re.search(r"([\w.-]+\.(?:sh|py))[\"']?(.*)$", cmd)
    return (m.group(1) + m.group(2).strip()) if m else cmd.strip()


def merge_settings(kit: dict, tgt: dict, report: list) -> dict:
    out = json.loads(json.dumps(tgt))
    # hooks: event 蹂?command ?⑹쭛??(????쒖꽌 ?좎?, kit 寃껋? ?ㅼ뿉 append)
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
    # 2026-10-12 ??kit ?먯꽌 ?ㅻⅨ hook ?쇰줈 ?泥대맂 hook ? ??곸뿉?쒕룄 類??(??鍮쇰㈃ ??13媛?+ ??1媛쒓? 媛숈씠 ?덈떎).
    #   ?泥?hook ????곸뿉 ?ㅼ뼱媛?寃쎌슦?먮쭔 類??쨌 ??곸씠 吏곸젒 怨좎튇 hook ??媛숈? ?대쫫?대㈃ ?泥대맂 寃껋쑝濡?蹂몃떎.
    retired_n = 0
    try:
        ret = json.loads((KIT / ".claude" / "scripts" / "retired-hooks.json").read_text(encoding="utf-8"))
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        ret = {}
    for ev, spec in ret.items():
        if ev.startswith("_") or not isinstance(spec, dict):
            continue
        gone = set(spec.get("hooks") or [])
        tm_list = th.get(ev) or []
        have_new = any(hook_key(h.get("command", "")) == spec.get("replaced_by")
                       for m in tm_list for h in m.get("hooks", []))
        if not have_new or not gone:
            continue
        kept = []
        for m in tm_list:
            hs = [h for h in m.get("hooks", []) if hook_key(h.get("command", "")) not in gone]
            retired_n += len(m.get("hooks", [])) - len(hs)
            if hs:
                kept.append({**m, "hooks": hs})
        th[ev] = kept
    report.append(f"settings.hooks ?泥대줈 ?쒓굅 {retired_n}")
    # ?대? ?덈뒗 kit hook ???ㅽ뻾 ?띿꽦(timeout쨌async)? kit 媛믪쓣 ?곕Ⅸ??    #   2026-10-06: kit ?먯꽌 detect-* timeout 3??0 ?쇰줈 ?щ젮????곸? 3 ??癒몃Ъ??寃?    kit_attr = {}
    for ev, kmatchers in kh.items():
        for km in kmatchers or []:
            for h in km.get("hooks", []):
                kit_attr[(ev, hook_key(h.get("command", "")))] = {k: h[k] for k in ("timeout", "async") if k in h}
    synced = 0
    for ev, tmatchers in th.items():
        for tm in tmatchers or []:
            for h in tm.get("hooks", []):
                want = kit_attr.get((ev, hook_key(h.get("command", ""))))
                if want is None:
                    continue
                for k, v in want.items():
                    if h.get(k) != v:
                        h[k] = v
                        synced += 1
    report.append(f"settings.hooks ?띿꽦 ?숆린??{synced}")
    # permissions.allow ?⑹쭛??    ka = (kit.get("permissions") or {}).get("allow") or []
    perm = out.setdefault("permissions", {})
    ta = perm.setdefault("allow", [])
    add_allow = [a for a in ka if a not in ta]
    ta.extend(add_allow)
    report.append(f"settings.permissions.allow +{len(add_allow)}")
    # statusLine: ?녾굅???꾩뿭 ???ㅽ겕由쏀듃瑜?媛由ы궎硫?kit ?ъ씤?곕줈
    sl = (out.get("statusLine") or {}).get("command", "")
    if not sl or ".claude/statusline_context.py" in sl.replace("\\", "/") and "$CLAUDE_PROJECT_DIR" not in sl:
        out["statusLine"] = kit.get("statusLine")
        report.append("settings.statusLine ??kit ?ъ씤??)
    # ?녿뒗 理쒖긽???ㅻ쭔
    for k, v in kit.items():
        if k not in out:
            out[k] = v
            report.append(f"settings.{k} 異붽?")
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
        print(f"????놁쓬: {target}")
        return 2
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = target / ".claude" / "backups" / f"kit-merge-{ts}"
    stats = {k: [] for k in ("identical", "stale-kit", "target-custom", "kit-only")}
    # ???꾧뎄媛 留덉?留됱쑝濡????ｌ? ?댁슜 吏臾???洹몃?濡쒕㈃ kit ?뚯쑀 (而ㅻ컠 ??踰꾩쟾??蹂듭궗?덉뼱??媛깆떊 媛??
    man_p = target / ".claude" / "state" / "kit-merge-manifest.json"
    try:
        manifest = json.loads(man_p.read_text(encoding="utf-8")) if man_p.exists() else {}
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
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
        # ?ㅽ뻾 ?뚯씪????PC ???녿뒗 ?쒕쾭???ｌ? ?딅뒗??(?곌껐 ?ㅽ뙣瑜??쇰쑉由ъ? ?딆쓬)
        add = {k: v for k, v in km["mcpServers"].items()
               if k not in (tm.get("mcpServers") or {}) and (v.get("url") or shutil.which(v.get("command", "")))}
        skipped = [k for k, v in km["mcpServers"].items()
                   if k not in (tm.get("mcpServers") or {}) and k not in add]
        if skipped:
            report.append(f".mcp.json ?쒖쇅(?ㅽ뻾?뚯씪 ?놁쓬) {skipped}")
        report.append(f".mcp.json ?쒕쾭 +{len(add)} {sorted(add)}")
        if apply and add:
            if tm_p.exists():
                shutil.copy2(tm_p, backup / ".mcp.json") if backup.exists() else None
            tm.setdefault("mcpServers", {}).update(add)
            tm_p.write_text(json.dumps(tm, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # 硫붾え由?(?ㅽ????꾨줈??
    prof = KIT / "setup" / "templates" / "user_style_profile.md"
    if prof.exists():
        mem = proj_memory_dir(target)
        for dst in (mem / "user_style_profile.md", target / ".claude" / "state" / "user_style_profile.md"):
            if not dst.exists() or norm(dst.read_bytes()) != norm(prof.read_bytes()):
                report.append(f"memory ??{dst}")
                if apply:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(prof, dst)
        idx = mem / "MEMORY.md"
        line = "- [?ъ슜???ㅽ???10異?(user_style_profile.md) ??ENFP-ADHD 쨌 吏㏐퀬 紐낇솗 쨌 Zero-touch 쨌 ?대젰 癒쇱? (kit setup/templates ?뺣낯)\n"
        if not idx.exists() or "user_style_profile.md" not in idx.read_text(encoding="utf-8", errors="replace"):
            report.append(f"memory index ??{idx}")
            if apply:
                idx.parent.mkdir(parents=True, exist_ok=True)
                with open(idx, "a", encoding="utf-8") as f:
                    f.write(line)

    if apply:
        man_p.parent.mkdir(parents=True, exist_ok=True)
        man_p.write_text(json.dumps(manifest, ensure_ascii=False, indent=0), encoding="utf-8")
    # 蹂묓빀????곸? ??PC ??紐⑸줉???먮룞 ?깅줉 ??git pull (post-merge) ???먮룞 ?щ퀝??    #   紐⑸줉? .claude/state/ (gitignore 쨌 PC 蹂? ??寃쎈줈瑜?git ??諛뺤? ?딅뒗??    if apply:
        reg = KIT / ".claude" / "state" / "merge-targets.txt"
        reg.parent.mkdir(parents=True, exist_ok=True)
        cur = reg.read_text(encoding="utf-8").splitlines() if reg.exists() else []
        if str(target) not in cur:
            with open(reg, "a", encoding="utf-8") as f:
                f.write(str(target) + chr(10))
            report.append(f"?먮룞 蹂묓빀 紐⑸줉 ?깅줉 ??{reg}")

    mode = "APPLY" if apply else "DRY-RUN"
    print(f"=== merge-to-target [{mode}] {target}")
    for k, v in stats.items():
        print(f"  {k:14} {len(v)}")
    for rel in stats["target-custom"]:
        print(f"    蹂댁〈(????섏젙蹂? {rel}")
    for r in report:
        print(f"  {r}")
    if apply:
        print(f"  諛깆뾽: {backup if backup.exists() else '(援먯껜 ?놁쓬)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

