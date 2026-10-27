#!/usr/bin/env python
"""
snapshot.py · verify-after-edit-mandatory.md 증명 체인 (pre·수정·post) stub

근거:
- workflow 06-verify.yaml step `pre_post_snapshot` 요구
- verify-after-edit-mandatory.md 룰

CLI:
  python snapshot.py pre --files <path1,path2>
  python snapshot.py post --files <path1,path2>
  python snapshot.py diff --files <path1,path2>   # pre vs post md5 비교
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / ".claude" / "state" / "snapshots"
STATE_DIR.mkdir(parents=True, exist_ok=True)


def _md5_file(p: Path) -> str:
    try:
        return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else "MISSING"
    except Exception as e:
        return f"ERR:{e}"


def _snapshot(label: str, files: list[str]) -> dict:
    result = {"label": label, "files": {}}
    for f in files:
        p = (ROOT / f) if not Path(f).is_absolute() else Path(f)
        result["files"][str(f)] = {
            "md5": _md5_file(p),
            "size": p.stat().st_size if p.exists() else 0,
        }
    out = STATE_DIR / f"{label}.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def _diff(files: list[str]) -> dict:
    pre_p = STATE_DIR / "pre.json"
    post_p = STATE_DIR / "post.json"
    if not pre_p.exists() or not post_p.exists():
        return {"error": "pre.json or post.json missing · run pre/post first"}
    pre = json.loads(pre_p.read_text(encoding="utf-8"))
    post = json.loads(post_p.read_text(encoding="utf-8"))
    changes = []
    for f in files:
        a = pre.get("files", {}).get(f, {})
        b = post.get("files", {}).get(f, {})
        if a.get("md5") != b.get("md5"):
            changes.append({"file": f, "pre": a.get("md5"), "post": b.get("md5"), "size_delta": b.get("size", 0) - a.get("size", 0)})
    return {"changed": len(changes), "files": changes}


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for mode in ("pre", "post", "diff"):
        p = sub.add_parser(mode)
        p.add_argument("--files", default="", help="comma-separated paths")
    args = ap.parse_args()
    files = [x for x in (args.files or "").split(",") if x.strip()]
    if args.cmd == "diff":
        print(json.dumps(_diff(files), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(_snapshot(args.cmd, files), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
