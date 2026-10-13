#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
statusline_context — Claude Code 컨텍스트 잔량 표시
표준 라이브러리만 사용 - Windows 함정 4개 회피.

경로 예: ~/.claude/statusline_context.py
"""
from __future__ import annotations
import json
import os
import re
import sys

# [함정 1] CP949 stdout 회피
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FILLED = "█"  # █
EMPTY = "▒"   # ▒
WIDTH = 10

# 상한 매핑 - 긴 것부터
LIMIT_PREFIXES = [
    # [1m] 접미 - 긴 것 먼저
    ("claude-opus-5[1m]", 1_000_000),
    ("claude-sonnet-5[1m]", 1_000_000),
    ("claude-opus-4-8[1m]", 1_000_000),
    ("claude-opus-4-7[1m]", 1_000_000),
    ("claude-sonnet-4-6[1m]", 1_000_000),
    # 표준 200K
    ("claude-opus-5", 200_000),
    ("claude-sonnet-5", 200_000),
    ("claude-opus-4-8", 200_000),
    ("claude-opus-4-7", 200_000),
    ("claude-sonnet-4-6", 200_000),
    ("claude-fable-5", 200_000),
    ("claude-haiku-4-5", 200_000),
]
DEFAULT_LIMIT = 200_000


def pick_limit(model_id: str) -> tuple[int, bool]:
    """(상한, 정확?) 반환."""
    if not model_id:
        return DEFAULT_LIMIT, False
    for pref, lim in LIMIT_PREFIXES:
        if model_id.startswith(pref):
            return lim, True
    return DEFAULT_LIMIT, False


def cwd_to_proj_dir(cwd: str) -> str:
    """cwd -> ~/.claude/projects/<safe>/ 폴더명."""
    safe = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
    home = os.path.expanduser("~")
    return os.path.join(home, ".claude", "projects", safe)


def last_assistant_usage(jsonl_path: str) -> dict | None:
    """jsonl 마지막 assistant 레코드의 message.usage."""
    if not os.path.exists(jsonl_path):
        return None
    last = None
    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("type") == "assistant":
                    usage = ((rec.get("message") or {}).get("usage")) or None
                    if usage:
                        last = usage
    except Exception:
        return None
    return last


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)


def render(tokens: int, limit: int, exact_model: bool, no_usage: bool) -> str:
    if no_usage:
        return f"{EMPTY * WIDTH} 측정 전"
    ratio = 0.0 if limit <= 0 else min(tokens / limit, 1.0)
    filled = int(round(ratio * WIDTH))
    filled = min(WIDTH, max(0, filled))
    bar = FILLED * filled + EMPTY * (WIDTH - filled)
    pct = ratio * 100
    tok_s = fmt_tokens(tokens)
    lim_s = fmt_tokens(limit)
    q = "" if exact_model else "?"
    line = f"{bar} {pct:.1f}%{q} ({tok_s}/{lim_s}{q})"
    if pct >= 95:
        line += "  compact 임박"
    elif pct >= 80:
        line += "  [WARN]"
    return line


def main() -> None:
    # [함정 4] 예외 나도 rc=0 + 빈 게이지
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    model_id = ""
    try:
        model_id = (data.get("model") or {}).get("id") or ""
    except Exception:
        pass

    session_id = data.get("session_id") or ""
    cwd = data.get("cwd") or ""

    limit, exact_model = pick_limit(model_id)

    tokens = 0
    no_usage = True

    if session_id and cwd:
        try:
            proj_dir = cwd_to_proj_dir(cwd)
            jsonl = os.path.join(proj_dir, f"{session_id}.jsonl")
            usage = last_assistant_usage(jsonl)
            if usage:
                tokens = int(
                    (usage.get("input_tokens") or 0)
                    + (usage.get("cache_read_input_tokens") or 0)
                    + (usage.get("cache_creation_input_tokens") or 0)
                )
                no_usage = False
        except Exception:
            pass

    print(render(tokens, limit, exact_model, no_usage))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # 최후 fallback
        try:
            print(EMPTY * WIDTH + " 측정 전")
        except Exception:
            print("측정 전")
    sys.exit(0)
