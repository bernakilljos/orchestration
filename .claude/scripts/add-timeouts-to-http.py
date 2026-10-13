#!/usr/bin/env python3
"""add-timeouts-to-http.py — Add timeout parameter to all HTTP requests

Scans Python files and adds timeout=10 to requests.get/post/put/delete/patch calls
that don't already have a timeout parameter.

Usage:
    python .claude/scripts/add-timeouts-to-http.py [--dry-run]
"""
import re
import sys
from pathlib import Path
from typing import Optional


def find_python_files(root: Path) -> list[Path]:
    """Find all Python files in .claude/scripts and plugins."""
    files = []
    for pattern in [".claude/scripts/**/*.py", "plugins/**/*.py"]:
        files.extend(root.glob(pattern))
    return [f for f in files if f.is_file()]


def has_timeout_param(match_text: str) -> bool:
    """Check if a requests call already has timeout parameter."""
    # Simple check: look for 'timeout=' in the match
    return "timeout=" in match_text


def add_timeout_to_call(line: str) -> tuple[str, bool]:
    """Add timeout=10 to a requests call if not already present.

    Args:
        line: Source code line

    Returns:
        Tuple of (modified_line, was_modified)
    """
    modified = False

    # Pattern for requests.get/post/put/delete/patch
    pattern = r'requests\.(get|post|put|delete|patch)\s*\('
    matches = list(re.finditer(pattern, line))

    if not matches:
        return line, modified

    # Process matches in reverse order to maintain indices
    for match in reversed(matches):
        paren_start = match.end() - 1  # Position of opening (

        # Find the matching closing parenthesis
        paren_count = 1
        pos = paren_start + 1
        call_content = ""

        while pos < len(line) and paren_count > 0:
            if line[pos] == "(":
                paren_count += 1
            elif line[pos] == ")":
                paren_count -= 1
            if paren_count > 0:
                call_content += line[pos]
            pos += 1

        # Check if timeout already exists
        if has_timeout_param(call_content):
            continue

        # Add timeout parameter before the closing paren
        # Find the position to insert (before closing paren)
        insert_pos = pos - 1  # Position of closing )

        # Check if we need to add a comma
        content_before_close = line[paren_start + 1 : insert_pos].rstrip()
        if content_before_close and not content_before_close.endswith(","):
            line = line[:insert_pos] + ", timeout=10" + line[insert_pos:]
        else:
            line = line[:insert_pos] + "timeout=10" + line[insert_pos:]

        modified = True

    return line, modified


def process_file(file_path: Path, dry_run: bool = False) -> tuple[int, list[str]]:
    """Process a single Python file.

    Args:
        file_path: Path to Python file
        dry_run: If True, don't write changes

    Returns:
        Tuple of (changes_count, modified_lines)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError) as e:
        print(f"[WARN] Cannot read {file_path}: {e}", file=sys.stderr)
        return 0, []

    lines = content.split("\n")
    modified_lines = []
    changes = 0

    for i, line in enumerate(lines):
        new_line, was_modified = add_timeout_to_call(line)
        if was_modified:
            modified_lines.append(i)
            changes += 1
            if not dry_run:
                lines[i] = new_line

    if changes > 0 and not dry_run:
        file_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  ✓ {file_path.relative_to(file_path.parent.parent.parent)} — {changes} timeout(s) added")

    return changes, modified_lines


def main() -> int:
    """Main entry point."""
    dry_run = "--dry-run" in sys.argv

    project_root = Path(__file__).resolve().parent.parent.parent
    python_files = find_python_files(project_root)

    print(f"Scanning {len(python_files)} Python files...")
    if dry_run:
        print("[DRY-RUN MODE] No changes will be written.\n")

    total_changes = 0
    files_modified = 0

    for python_file in sorted(python_files):
        changes, _ = process_file(python_file, dry_run=dry_run)
        if changes > 0:
            if dry_run:
                print(f"  [DRY] {python_file.relative_to(project_root)} — {changes} timeout(s) needed")
            files_modified += 1
            total_changes += changes

    print(f"\nTotal: {total_changes} timeout(s) added in {files_modified} file(s)")

    if dry_run:
        print("\nRun without --dry-run to apply changes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
