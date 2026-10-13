#!/usr/bin/env python3
"""?꾩옱 ?몄뀡??而⑦뀓?ㅽ듃 ?ъ슜瑜?%)????以꾨줈 異쒕젰?쒕떎.

?뺣낯????怨녹뿉 ?붾떎. 媛숈? 怨꾩궛???낅쭏???⑹뼱吏硫??쒖そ留?怨좎퀜???쒕줈 ?ㅻⅨ ?먯젙???대┛??(2026-09-08: auto-compact-check ?????섎줈,
inject-compact-reminder ??% 濡??먯젙??29.5% ?먯꽌 媛뺤젣 ?뺤텞??嫄몃졇??.

?곹븳 ?뺣낯: .claude/state/context-limit.json (statusline_context.py 媛 湲곕줉).
jsonl ??message.model ?먮뒗 "[1m]" ???놁뼱 model 留?蹂대㈃ 1M ?몄뀡??200K 濡??ㅽ뙋?쒕떎.
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

    # 2026-09-19: ??stdin ??transcript_path(env CLAUDE_TRANSCRIPT_PATH) 媛 ?뺣낯. mtime 理쒖떊 ?뚯씪? ?숈떆 ?몄뀡?먯꽌 ?⑥쓽 寃껋씠怨?
    # 306MB 瑜?泥섏쓬遺???쎌쑝硫?3珥???꾩븘?껋뿉 嫄몃젮 auto-planner 媛 留ㅻ쾲 痍⑥냼?먮떎. 留덉?留?usage ??瑗щ━ 4MB ?덉뿉 ?덈떎.
    own = os.environ.get("CLAUDE_TRANSCRIPT_PATH", "")
    if own and Path(own).is_file():
        latest = Path(own)
    else:
        files = list(proj.glob("*.jsonl"))
        if not files:
            print("0")
            return
        latest = max(files, key=lambda f: f.stat().st_mtime)

    usage = None
    try:
        # 瑗щ━ 4MB ???놁쑝硫??ㅺ? attachment 肉먯씤 ?몄뀡) 64MB 濡???踰??? 洹몃옒???놁쑝硫?0.
        for TAIL in (4 * 1024 * 1024, 64 * 1024 * 1024):
            with latest.open("rb") as fb:
                fb.seek(0, 2)
                size = fb.tell()
                fb.seek(max(0, size - TAIL))
                chunk = fb.read().decode("utf-8", errors="replace")
            lines = chunk.split("\n")[1:] if size > TAIL else chunk.split("\n")
            for line in reversed(lines):
                if '"type":"assistant"' not in line:
                    continue
                try:
                    rec = json.loads(line)
                except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
                    continue
                u = (rec.get("message") or {}).get("usage")
                # ?꾨? 0 ??usage(?쒕룄 珥덇낵 ?덈궡 ?? ??嫄대꼫?곌퀬 吏곸쟾 ?ㅼ젣 ?묐떟???대떎
                if u and ((u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
                          + (u.get("cache_creation_input_tokens") or 0)) > 0:
                    usage = u
                    break
            if usage or size <= TAIL:
                break
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
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
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        pass
    if not limit:
        limit = 1_000_000 if tokens > 200_000 else 200_000

    print(f"{tokens / limit * 100:.1f}")


if __name__ == "__main__":
    main()

