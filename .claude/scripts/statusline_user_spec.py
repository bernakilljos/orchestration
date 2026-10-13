#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
statusline_context ??Claude Code 而⑦뀓?ㅽ듃 ?붾웾 ?쒖떆
?쒖? ?쇱씠釉뚮윭由щ쭔 ?ъ슜 - Windows ?⑥젙 4媛??뚰뵾.

寃쎈줈 ?? ~/.claude/statusline_context.py
"""
from __future__ import annotations
import json
import os
import re
import sys

# [?⑥젙 1] CP949 stdout ?뚰뵾
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
    pass

FILLED = "??  # ??
EMPTY = "??   # ??
WIDTH = 10

# ?곹븳 留ㅽ븨 - 湲?寃껊???
LIMIT_PREFIXES = [
    # [1m] ?묐? - 湲?寃?癒쇱?
    ("claude-opus-5[1m]", 1_000_000),
    ("claude-sonnet-5[1m]", 1_000_000),
    ("claude-opus-4-8[1m]", 1_000_000),
    ("claude-opus-4-7[1m]", 1_000_000),
    ("claude-sonnet-4-6[1m]", 1_000_000),
    # ?쒖? 200K
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
    """(?곹븳, ?뺥솗?) 諛섑솚."""
    if not model_id:
        return DEFAULT_LIMIT, False
    for pref, lim in LIMIT_PREFIXES:
        if model_id.startswith(pref):
            return lim, True
    return DEFAULT_LIMIT, False


def cwd_to_proj_dir(cwd: str) -> str:
    """cwd -> ~/.claude/projects/<safe>/ ?대뜑紐?"""
    safe = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
    home = os.path.expanduser("~")
    return os.path.join(home, ".claude", "projects", safe)


def last_assistant_usage(jsonl_path: str) -> dict | None:
    """jsonl 留덉?留?assistant ?덉퐫?쒖쓽 message.usage."""
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
                except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
                    continue
                if rec.get("type") == "assistant":
                    usage = ((rec.get("message") or {}).get("usage")) or None
                    if usage:
                        last = usage
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
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
        return f"{EMPTY * WIDTH} 痢≪젙 ??
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
        line += "  compact ?꾨컯"
    elif pct >= 80:
        line += "  [WARN]"
    return line


def main() -> None:
    # [?⑥젙 4] ?덉쇅 ?섎룄 rc=0 + 鍮?寃뚯씠吏
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        data = {}

    model_id = ""
    try:
        model_id = (data.get("model") or {}).get("id") or ""
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
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
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            pass

    print(render(tokens, limit, exact_model, no_usage))


if __name__ == "__main__":
    try:
        main()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        # 理쒗썑 fallback
        try:
            print(EMPTY * WIDTH + " 痢≪젙 ??)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            print("痢≪젙 ??)
    sys.exit(0)

