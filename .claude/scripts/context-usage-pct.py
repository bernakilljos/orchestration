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

    # 2026-09-19: 훅 stdin 의 transcript_path(env CLAUDE_TRANSCRIPT_PATH) 가 정본. mtime 최신 파일은 동시 세션에서 남의 것이고,
    # 306MB 를 처음부터 읽으면 3초 타임아웃에 걸려 auto-planner 가 매번 취소됐다. 마지막 usage 는 꼬리 4MB 안에 있다.
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
        # 꼬리 4MB 에 없으면(뒤가 attachment 뿐인 세션) 64MB 로 한 번 더. 그래도 없으면 0.
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
                except Exception:
                    continue
                u = (rec.get("message") or {}).get("usage")
                # 전부 0 인 usage(한도 초과 안내 등) 는 건너뛰고 직전 실제 응답을 쓴다
                if u and ((u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
                          + (u.get("cache_creation_input_tokens") or 0)) > 0:
                    usage = u
                    break
            if usage or size <= TAIL:
                break
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
        pass  # noqa: BLE001
    if not limit:
        limit = 1_000_000 if tokens > 200_000 else 200_000

    print(f"{tokens / limit * 100:.1f}")


if __name__ == "__main__":
    main()
