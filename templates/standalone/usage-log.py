#!/usr/bin/env python3
"""
usage-log.py — Standalone 환경의 토큰 사용량 기록

Codex / Gemini standalone 환경에서 각 호출의 사용량을 .codex/usage.jsonl 또는
.gemini/usage.jsonl 에 기록합니다.

사용법:
  python usage-log.py --mode codex --in 150 --out 420 --cost 0.015
  python usage-log.py --mode gemini --in 1500 --out 800 --cost 0.001

결과:
  .codex/usage.jsonl (또는 .gemini/usage.jsonl)
  {"ts": "2026-04-24T10:30:00Z", "model": "gpt-4", "in": 150, "out": 420, "cost_usd": 0.015}
"""

import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path


def log_usage(mode: str, model: str, tokens_in: int, tokens_out: int, cost_usd: float) -> None:
    """토큰 사용량을 JSONL 파일에 기록."""

    # 파일 경로 결정
    if mode.lower() == "codex":
        log_file = Path.cwd() / ".codex" / "usage.jsonl"
    elif mode.lower() == "gemini":
        log_file = Path.cwd() / ".gemini" / "usage.jsonl"
    else:
        print(f"[ERROR] 알 수 없는 모드: {mode}")
        sys.exit(1)

    # 디렉토리 생성
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 기록 생성
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec='seconds'),
        "model": model,
        "in": tokens_in,
        "out": tokens_out,
        "cost_usd": cost_usd
    }

    # JSONL에 추가
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[OK] {log_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Standalone 환경의 토큰 사용량 기록"
    )
    parser.add_argument("--mode", required=True, choices=["codex", "gemini"],
                        help="모드 (codex 또는 gemini)")
    parser.add_argument("--model", required=False, help="모델명 (기본: gpt-4 또는 gemini-2.0-flash)")
    parser.add_argument("--in", type=int, required=True, dest="tokens_in",
                        help="입력 토큰 수")
    parser.add_argument("--out", type=int, required=True, dest="tokens_out",
                        help="출력 토큰 수")
    parser.add_argument("--cost", type=float, required=True,
                        help="비용 (USD)")

    args = parser.parse_args()

    # 기본 모델명
    if not args.model:
        args.model = "gpt-4" if args.mode == "codex" else "gemini-2.0-flash"

    log_usage(args.mode, args.model, args.tokens_in, args.tokens_out, args.cost)


if __name__ == "__main__":
    main()
