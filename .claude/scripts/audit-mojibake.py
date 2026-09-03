#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""audit-mojibake — U+FFFD·CP949↔UTF-8 깨짐 패턴 감사 + 자동 복구.
결과: .claude/state/mojibake-audit.json
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
OUT = ROOT / ".claude" / "state" / "mojibake-audit.json"

# 6 카테고리 (no-false-report.md § Mojibake 패턴)
PATTERNS = [
    ("replacement_char", re.compile(r"�"), "U+FFFD replacement character"),
    ("known_broken_ko", re.compile(r"[꿇룷꿿괓]|점쇙올"), "한글 깨짐 (실제 사례)"),
    ("euc_kr_broken", re.compile(r"\?곸|\?쒕|\?대"), "EUC-KR → UTF-8 실패"),
    ("utf8_to_latin1", re.compile(r"Ã[¡-¿]|â€|ï¿½"), "UTF-8 → Latin-1 깨짐"),
    ("byte_sequence", re.compile(r"\\xc3\\x83|\\xc2"), "잘못된 byte sequence 표기"),
    ("emoji_leak", re.compile(r"[]"),
     "이모지 leak (kit 원칙: 이모지 금지)"),
]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
             "archive", ".claude/state", ".claude/logs",
             ".claude/context-cache", "outputs/insight-cards",
             "outputs/itcen", "local_data",
             "docs/screens/_brand-preview", "docs/screens"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".docx", ".pptx",
            ".xlsx", ".zip", ".tar", ".gz", ".mp4", ".mp3", ".wav", ".sqlite",
            ".db", ".bak", ".pyc", ".pyo", ".ico", ".woff", ".woff2", ".ttf"}
# 감사 대상 확장자 (kit 자체)
SCAN_EXT = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".txt",
            ".html", ".css", ".js", ".ts", ".bat", ".ps1"}


def scan(fix=False):
    hits = {k: [] for k, _, _ in PATTERNS}
    hits_flat = []
    scanned = 0
    fixed_files = []
    for base, dirs, files in os.walk(ROOT):
        rel = Path(base).relative_to(ROOT).as_posix()
        parts = rel.split("/")
        if any("/".join(parts[:i + 1]) in SKIP_DIRS or parts[i] in SKIP_DIRS
               for i in range(len(parts))):
            dirs[:] = []
            continue
        for name in files:
            ext = Path(name).suffix.lower()
            if ext in SKIP_EXT:
                continue
            if SCAN_EXT and ext not in SCAN_EXT:
                continue
            fp = Path(base) / name
            try:
                if fp.stat().st_size > 500_000:
                    continue
                txt = fp.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            scanned += 1
            file_had_hit = False
            new_txt = txt
            for key, pat, desc in PATTERNS:
                found = list(pat.finditer(txt))
                for m in found[:10]:
                    lineno = txt.count("\n", 0, m.start()) + 1
                    rec = {
                        "file": fp.relative_to(ROOT).as_posix(),
                        "line": lineno,
                        "pattern": key,
                        "match": m.group(0)[:40],
                    }
                    hits[key].append(rec)
                    hits_flat.append(rec)
                if found:
                    file_had_hit = True
                    if fix and key == "emoji_leak":
                        # 이모지 자동 제거 (kit 룰 - 이모지 leak 만)
                        new_txt = pat.sub("", new_txt)
            if fix and file_had_hit and new_txt != txt:
                try:
                    bak = fp.with_suffix(fp.suffix + ".bak")
                    if not bak.exists():
                        bak.write_text(txt, encoding="utf-8")
                    fp.write_text(new_txt, encoding="utf-8")
                    fixed_files.append(str(fp.relative_to(ROOT).as_posix()))
                except Exception:
                    pass
    return hits, hits_flat, scanned, fixed_files


def main():
    fix = "--fix" in sys.argv
    hits, hits_flat, scanned, fixed = scan(fix=fix)
    counts = {k: len(v) for k, v in hits.items()}
    total = sum(counts.values())
    status = "PASS" if total == 0 else "FAIL"
    result = {
        "ts": datetime.now().isoformat(),
        "scanned_files": scanned,
        "status": status,
        "total_hits": total,
        "counts": counts,
        "hits_flat": hits_flat[:100],
        "fixed_files": fixed if fix else [],
        "fix_mode": fix,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[audit-mojibake] {status} - scanned {scanned} - total {total}")
    if fix:
        print(f"  자동 복구: {len(fixed)} 파일 (이모지 leak · .bak 백업)")
    for k, n in counts.items():
        if n:
            print(f"  {k}: {n}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[audit-mojibake] err: {e}", file=sys.stderr)
        sys.exit(1)
