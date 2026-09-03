#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""audit-hardcoded — CLAUDE.md § 7-A1 (하드 경로·시크릿·Python 버전 금지) 자동 감사.
결과: .claude/state/hardcoded-audit.json
"""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / ".claude" / "state" / "hardcoded-audit.json"

PATTERNS = [
    ("users_path_win", re.compile(r"C:\\Users\\[a-z0-9_]+", re.IGNORECASE), "Windows 사용자 경로"),
    ("users_path_unix", re.compile(r"/home/[a-z0-9_]+"), "Linux 사용자 경로"),
    ("python_version", re.compile(r"Python3(10|11|12|13|14|15)\\python\.exe"), "Python 버전 박음"),
    ("desktop_hostname", re.compile(r"DESKTOP-[A-Z0-9]+"), "특정 호스트명"),
    ("ip_192", re.compile(r"192\.168\.\d+\.\d+"), "고정 사설 IP"),
    ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key"),
    ("openai_key", re.compile(r"sk-[a-zA-Z0-9]{40,}"), "OpenAI/Anthropic API key"),
    ("github_pat", re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub PAT"),
]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
             "archive", ".claude/state", ".claude/logs",
             ".claude/context-cache", "outputs", "local_data"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".docx", ".pptx",
            ".xlsx", ".zip", ".tar", ".gz", ".mp4", ".mp3", ".wav", ".sqlite",
            ".db", ".bak", ".pyc", ".pyo", ".ico"}


def scan():
    hits = {k: [] for k, _, _ in PATTERNS}
    scanned = 0
    for base, dirs, files in os.walk(ROOT):
        rel = Path(base).relative_to(ROOT).as_posix()
        # skip
        parts = rel.split("/")
        if any(p in SKIP_DIRS for p in parts):
            dirs[:] = []
            continue
        for name in files:
            ext = Path(name).suffix.lower()
            if ext in SKIP_EXT:
                continue
            fp = Path(base) / name
            try:
                if fp.stat().st_size > 500_000:
                    continue
                txt = fp.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            scanned += 1
            for key, pat, _ in PATTERNS:
                for m in pat.finditer(txt):
                    lineno = txt.count("\n", 0, m.start()) + 1
                    hits[key].append({
                        "file": fp.relative_to(ROOT).as_posix(),
                        "line": lineno,
                        "match": m.group(0)[:80],
                    })
                    if len(hits[key]) >= 100:
                        break
    return hits, scanned


def main():
    hits, scanned = scan()
    counts = {k: len(v) for k, v in hits.items()}
    total = sum(counts.values())
    critical = counts.get("aws_key", 0) + counts.get("openai_key", 0) + counts.get("github_pat", 0)
    status = "PASS" if total == 0 else ("CRITICAL" if critical else "WARN")
    result = {
        "ts": datetime.now().isoformat(),
        "scanned_files": scanned,
        "status": status,
        "total_hits": total,
        "counts": counts,
        "hits": {k: v[:20] for k, v in hits.items()},  # top 20 per pattern
        "patterns": {k: desc for k, _, desc in PATTERNS},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[audit-hardcoded] {status} - scanned {scanned} - total {total} - critical {critical}")
    print(f"  cache: {OUT.relative_to(ROOT)}")
    for k, n in counts.items():
        if n:
            print(f"  {k}: {n}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[audit-hardcoded] err: {e}", file=sys.stderr)
        sys.exit(1)
