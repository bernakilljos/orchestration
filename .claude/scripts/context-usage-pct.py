#!/usr/bin/env python3
"""현재 세션의 컨텍스트 사용률(%)을 한 줄로 출력한다.

정본을 한 곳에 둔다. 같은 계산이 훅마다 흩어지면 한쪽만 고쳐져
서로 다른 판정을 내린다 (2026-09-08: auto-compact-check 는 턴 수로,
inject-compact-reminder 는 % 로 판정해 29.5% 에서 강제 압축이 걸렸다).

상한 정본: .claude/state/context-limit.json (statusline_context.py 가 기록).
jsonl 의 message.model 에는 "[1m]" 이 없어 model 만 보면 1M 세션을 200K 로 오판한다.
"""
import json
import os
import re
import sys
from pathlib import Path


def main() -> None:
    cwd = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    safe = re.sub(r"[^a-zA-Z0-9]", "-", str(cwd))
    proj = Path.home() / ".claude" / "projects" / safe
    if not proj.is_dir():
        print("0")
        return

    files = list(proj.glob("*.jsonl"))
    if not files:
        print("0")
        return
    latest = max(files, key=lambda f: f.stat().st_mtime)

    usage = None
    try:
        with latest.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("type") == "assistant":
                    u = (rec.get("message") or {}).get("usage")
                    if u:
                        usage = u
    except Exception:
        print("0")
        return

    if not usage:
        print("0")
        return

    tokens = (
        (usage.get("input_tokens") or 0)
        + (usage.get("cache_read_input_tokens") or 0)
        + (usage.get("cache_creation_input_tokens") or 0)
    )

    limit = 0
    try:
        with (cwd / ".claude" / "state" / "context-limit.json").open(encoding="utf-8") as f:
            limit = int(json.load(f).get("limit") or 0)
    except Exception:
        pass
    if not limit:
        limit = 1_000_000 if tokens > 200_000 else 200_000

    print(f"{tokens / limit * 100:.1f}")


if __name__ == "__main__":
    main()
