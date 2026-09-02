"""
nightly-optimize — 매일 03:00 실행 (Task Scheduler 등록)
1. orca.db 백업
2. conversations 30일 초과 압축
3. VACUUM + ANALYZE
4. 로그 14일 초과 삭제
5. image-cache 7일 초과 삭제
6. hook profile 리포트 (예정)
근거: .claude/rules/auto-optimization.md
"""
from __future__ import annotations
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / ".claude" / "state" / "orca.db"
LOG = ROOT / ".claude" / "logs" / "nightly-optimize.log"
LOG.parent.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")


def backup_db() -> None:
    if not DB.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d")
    bak = DB.with_suffix(f".db.bak.{stamp}")
    if bak.exists():
        return
    shutil.copy2(DB, bak)
    log(f"backup: {bak.name}")

    # 30일 rolling
    cutoff = datetime.now() - timedelta(days=30)
    for p in DB.parent.glob("orca.db.bak.*"):
        try:
            if p.stat().st_mtime < cutoff.timestamp():
                p.unlink()
                log(f"rolling delete: {p.name}")
        except Exception:
            pass


def compress_conversations() -> None:
    if not DB.exists():
        return
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(str(DB)) as c:
        n = c.execute(
            "UPDATE conversations SET content='(compressed)', tokens=0 WHERE ts < ? AND content != '(compressed)'",
            (cutoff,),
        ).rowcount
        c.commit()
    if n:
        log(f"compressed conversations: {n} rows (>30 days)")


def vacuum_db() -> None:
    if not DB.exists():
        return
    with sqlite3.connect(str(DB)) as c:
        c.execute("VACUUM")
        c.execute("ANALYZE")
    log("VACUUM + ANALYZE ok")


def cleanup_logs() -> None:
    logs_dir = ROOT / ".claude" / "logs"
    cutoff = datetime.now() - timedelta(days=14)
    n = 0
    for p in logs_dir.glob("*.log"):
        try:
            if p.stat().st_mtime < cutoff.timestamp():
                p.unlink()
                n += 1
        except Exception:
            pass
    if n:
        log(f"deleted old logs: {n}")


def cleanup_image_cache() -> None:
    cache = ROOT / "image-cache"
    if not cache.exists():
        return
    cutoff = datetime.now() - timedelta(days=7)
    n = 0
    for p in cache.rglob("*"):
        try:
            if p.is_file() and p.stat().st_mtime < cutoff.timestamp():
                p.unlink()
                n += 1
        except Exception:
            pass
    if n:
        log(f"cleaned image-cache: {n} files")


def main() -> int:
    log("=== nightly-optimize start ===")
    for fn in (backup_db, compress_conversations, vacuum_db, cleanup_logs, cleanup_image_cache):
        try:
            fn()
        except Exception as e:
            log(f"[warn] {fn.__name__}: {e}")
    log("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
