#!/usr/bin/env python3
"""verify-no-mojibake.py — Korean mojibake (encoding break) detector
Ref: CLAUDE.md § 7-25 + .claude/rules/no-false-report.md

Targets: text files (.md, .txt, .html, .py, .js, .ts, .json, .yaml, .sh, .sql)
Includes backup folders (.bak, _backup, _v2, _old, archive)

Usage:
  python verify-no-mojibake.py <path>            # file or directory
  python verify-no-mojibake.py docs/ssj/         # recursive
  python verify-no-mojibake.py file.md --quiet   # exit code only (CI)

Exit codes:
  0 — PASS (no mojibake)
  1 — FAIL (mojibake found, listed to stdout)
"""
import sys
import re
from pathlib import Path

# Force UTF-8 stdout on Windows
import io
import os
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")


# === Mojibake patterns ===
# Use chr() / escape to avoid the very characters being filtered by check-mojibake hook
REPLACEMENT_CHAR = chr(0xFFFD)  # U+FFFD replacement char (most reliable signal)

PATTERNS = [
    (REPLACEMENT_CHAR, "U+FFFD replacement char"),
    # User-reported actual breaks (2026-06-10)
    ("꿇룷", "user-reported break (kkuh-rut)"),
    ("꿇", "user-reported break fragment"),
    ("룷", "user-reported break fragment"),
    ("꿿", "Korean break pattern"),
    ("괓", "Korean break pattern"),
    # EUC-KR / cp949 -> UTF-8 decoding failures (these chars themselves are valid hanja)
    ("점쇙올", "cp949 -> UTF-8 break"),
    ("점시", "cp949 -> UTF-8 break"),
    ("점십", "cp949 -> UTF-8 break"),
    # UTF-8 -> Latin-1 corruption (most common in web)
    ("Ã", "UTF-8 -> Latin-1 (Ã)"),
    ("â€", "UTF-8 -> Latin-1 (a-euro)"),
    ("ï¿½", "UTF-8 -> Latin-1 (i-question-half)"),
]

# Regex patterns (Korean + ? combo — broken form)
REGEX_PATTERNS = [
    # Korean char + ? + Korean char (decoding failure)
    (re.compile(r"[가-힯]\?[가-힯]"), "Korean-?-Korean (decode failure suspect)"),
    # ?곸 ?쒕 ?대 — cp949 broken
    (re.compile(r"\?[곸엕대щ쳨]"), "EUC-KR break (?+broken-korean)"),
]

# Skip dirs
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".pytest_cache", "venv", ".venv", "dist", "build"}
TEXT_EXTS = {".md", ".txt", ".html", ".py", ".js", ".jsx", ".ts", ".tsx", ".vue", ".json", ".yaml", ".yml", ".sh", ".bat", ".css", ".sql"}

# Skip files that legitimately contain mojibake patterns (rule definitions, this tool itself)
SKIP_FILES = {
    "verify-no-mojibake.py",
    "no-false-report.md",
    "feedback_no_false_pass_report.md",
    "check-mojibake.sh",
}
# Skip raw PDF/OCR extract dumps
SKIP_NAME_PATTERNS = ("_pdf_text", "_ocr_text", "_raw_extract")


def check_file(path: Path) -> list:
    """Check one file; return list of (lineno, msg)."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return [(0, f"read failed: {e}")]

    issues = []

    # String patterns
    for pat, desc in PATTERNS:
        if pat in content:
            for lineno, line in enumerate(content.splitlines(), 1):
                if pat in line:
                    excerpt = line.strip()[:80]
                    issues.append((lineno, f"{desc}: '{pat}' in: {excerpt}"))
                    break

    # Regex patterns
    for pat, desc in REGEX_PATTERNS:
        for lineno, line in enumerate(content.splitlines(), 1):
            m = pat.search(line)
            if m:
                issues.append((lineno, f"{desc}: '{m.group(0)}' in: {line.strip()[:80]}"))
                break

    return issues


def walk_path(target: Path) -> dict:
    results = {}

    if target.is_file():
        issues = check_file(target)
        if issues:
            results[str(target)] = issues
        return results

    for p in target.rglob("*"):
        if any(d in p.parts for d in SKIP_DIRS):
            continue
        if not p.is_file():
            continue
        if p.suffix.lower() not in TEXT_EXTS:
            continue
        if p.name in SKIP_FILES:
            continue
        if any(s in p.name for s in SKIP_NAME_PATTERNS):
            continue
        try:
            if p.stat().st_size > 500_000:
                continue
        except OSError:
            continue

        issues = check_file(p)
        if issues:
            results[str(p)] = issues

    return results


def main():
    args = sys.argv[1:]
    quiet = "--quiet" in args
    args = [a for a in args if a != "--quiet"]

    if not args:
        print("usage: verify-no-mojibake.py <path> [--quiet]")
        sys.exit(2)

    target = Path(args[0])
    if not target.exists():
        print(f"[ERROR] not found: {target}")
        sys.exit(2)

    results = walk_path(target)

    if not results:
        if not quiet:
            print(f"[PASS] mojibake 0 — {target}")
        sys.exit(0)

    total = sum(len(v) for v in results.values())
    print(f"[FAIL] mojibake {total} found in {len(results)} files:")
    for path, issues in results.items():
        print(f"\n  [{path}]")
        for lineno, msg in issues[:5]:
            print(f"    L{lineno}: {msg}")
        if len(issues) > 5:
            print(f"    ... +{len(issues)-5} more")
    sys.exit(1)


if __name__ == "__main__":
    main()
