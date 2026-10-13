#!/usr/bin/env python3
"""
Shared utility library for orchestration_v1 scripts.

Consolidates: log(), get_infra(), ensure_table(), scan(), render(), search()
Eliminates duplication across 42+ scripts.

Usage:
    from lib.common import log, get_infra, ensure_table, scan, render, search
    log('INFO', 'Operation started')
    infra = get_infra()
    conn = ensure_table(conn, 'tasks', TASKS_SCHEMA)
"""

import sys
import os
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import re
import subprocess

# Import structured logging
from .structured_logger import get_logger as _get_structured_logger, log as structured_log

def log(level: str, msg: str, **kwargs):
    """
    Unified logging: write to console + file with structured fields.

    Args:
        level: 'DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'
        msg: Message
        **kwargs: Extra structured fields (logged as JSON)

    Note: This now uses structured_logger.py for JSON output.
          All kwargs are included as structured fields.
    """
    # Delegate to structured logger
    structured_log(level, msg, **kwargs)

def get_infra() -> Dict[str, Path]:
    """
    Get infrastructure paths (kit root, state, logs, tasks, etc.)

    Returns:
        dict with: root, state_dir, logs_dir, tasks_dir, done_dir, locks_dir, scripts_dir
        Raises if paths don't exist.
    """
    root = Path(__file__).parent.parent.parent.parent  # lib -> scripts -> .claude -> root

    infra = {
        'root': root,
        'state_dir': root / '.claude' / 'state',
        'logs_dir': root / '.claude' / 'logs',
        'tasks_dir': root / '.claude' / 'tasks',
        'done_dir': root / '.claude' / 'tasks' / 'done',
        'locks_dir': root / '.claude' / 'tasks' / 'locks',
        'scripts_dir': root / '.claude' / 'scripts',
        'lib_dir': root / '.claude' / 'scripts' / 'lib',
        'hooks_dir': root / '.claude' / 'hooks',
        'rules_dir': root / '.claude' / 'rules',
        'skills_dir': root / '.claude' / 'skills',
        'plugins_dir': root / 'plugins',
    }

    # Verify critical paths exist
    for key in ['root', 'state_dir', 'logs_dir', 'tasks_dir']:
        if not infra[key].exists():
            log('ERROR', f"Infrastructure path missing: {key} = {infra[key]}")
            raise FileNotFoundError(f"{key} not found at {infra[key]}")

    return infra

def ensure_table(conn: sqlite3.Connection, table_name: str, schema: Dict[str, str]) -> sqlite3.Connection:
    """
    Ensure table exists with given schema. Create if missing.

    Args:
        conn: SQLite connection
        table_name: Name of table
        schema: Dict mapping column_name -> type (e.g., {'id': 'INTEGER PRIMARY KEY', 'name': 'TEXT'})

    Returns:
        conn (unchanged)

    Raises:
        ValueError if schema is invalid
    """
    if not table_name or not schema:
        raise ValueError(f"Invalid table_name or schema: {table_name}, {schema}")

    cursor = conn.cursor()

    # Check if table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )

    if cursor.fetchone():
        log('DEBUG', f"Table {table_name} already exists")
        return conn

    # Build CREATE TABLE
    cols = ', '.join([f"{k} {v}" for k, v in schema.items()])
    sql = f"CREATE TABLE {table_name} ({cols})"

    try:
        cursor.execute(sql)
        conn.commit()
        log('INFO', f"Created table {table_name}")
    except sqlite3.Error as e:
        log('ERROR', f"Failed to create table {table_name}: {e}")
        raise

    return conn

def scan(path: str, pattern: str, recursive: bool = True) -> List[Path]:
    """
    Scan filesystem for files matching pattern.

    Args:
        path: Directory to scan
        pattern: Glob pattern (e.g., '*.py', '**/*.md')
        recursive: If True, search recursively (prepend ** if needed)

    Returns:
        List of Path objects
    """
    root = Path(path)
    if not root.exists():
        log('WARN', f"Scan path does not exist: {path}")
        return []

    if recursive and not pattern.startswith('**'):
        pattern = f"**/{pattern}"

    try:
        results = list(root.glob(pattern))
        log('DEBUG', f"Scanned {path} with pattern {pattern}: {len(results)} results")
        return sorted(results)
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        log('ERROR', f"Scan failed: {path} / {pattern}: {e}")
        return []

def render(template: str, context: Dict[str, Any]) -> str:
    """
    Simple template rendering: replace {{key}} with context[key].

    Args:
        template: Template string with {{key}} placeholders
        context: Dict with values

    Returns:
        Rendered string
    """
    result = template
    for key, value in context.items():
        placeholder = f"{{{{{key}}}}}"
        result = result.replace(placeholder, str(value))
    return result

def search(query: str, files: List[Path], case_sensitive: bool = False) -> List[tuple]:
    """
    Search for query string in files.

    Args:
        query: Search string (supports regex if starts with '/')
        files: List of file paths to search
        case_sensitive: Case sensitivity

    Returns:
        List of (file, line_num, line_text) tuples
    """
    results = []

    is_regex = query.startswith('/')
    if is_regex:
        query = query[1:]  # Strip leading '/'

    flags = 0 if case_sensitive else re.IGNORECASE

    try:
        pattern = re.compile(query, flags) if is_regex else None
    except re.error as e:
        log('ERROR', f"Invalid regex pattern: {query}: {e}")
        return []

    for filepath in files:
        if not filepath.exists():
            continue

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if pattern:
                        match = pattern.search(line)
                    else:
                        match = query.lower() in line.lower() if not case_sensitive else query in line

                    if match:
                        results.append((filepath, line_num, line.rstrip()))
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            log('WARN', f"Could not search {filepath}: {e}")

    log('DEBUG', f"Search for '{query}' in {len(files)} files: {len(results)} matches")
    return results

def silent_fail_audit() -> List[tuple]:
    r"""
    Audit codebase for silent fail patterns: except[^:]*:\s*pass

    Returns:
        List of (file, line_num, line_text) tuples
    """
    infra = get_infra()

    scripts = scan(str(infra['scripts_dir']), '*.py')
    scripts += scan(str(infra['plugins_dir']), '*.py', recursive=True)

    pattern = r'except[^:]*:\s*pass'
    results = search(f"/{pattern}", scripts)

    log('INFO', f"Silent fail audit: found {len(results)} instances")
    return results

def hash_content(content: str, length: int = 16) -> str:
    """
    SHA-256 hash of content, truncated.

    Args:
        content: String to hash
        length: Truncate to N chars

    Returns:
        Hex hash
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:length]

if __name__ == '__main__':
    # Test
    log('INFO', 'common.py loaded')
    infra = get_infra()
    log('INFO', f"Infrastructure root: {infra['root']}")

    # Audit silent fails
    silent_fails = silent_fail_audit()
    if silent_fails:
        print(f"\n=== Silent Fail Audit ({len(silent_fails)} instances) ===")
        for filepath, line_num, line_text in silent_fails[:10]:
            print(f"{filepath}:{line_num}: {line_text.strip()}")
        if len(silent_fails) > 10:
            print(f"... and {len(silent_fails) - 10} more")

