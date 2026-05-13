#!/usr/bin/env python3
"""score_task.py — Haiku LLM-as-judge for task results.

Usage:
    python score_task.py --task <task-file> --result <result-file>
    python score_task.py --auto    # latest done/ task + latest docs/ result
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EVAL_LOG = PROJECT_ROOT / ".claude" / "state" / "evaluations.jsonl"

SYSTEM_RUBRIC = """You are a strict code/output evaluator. Score 0-10 on 4 dimensions:

1. Correctness  - Does it meet the spec?
2. Completeness - Are all requirements covered? Any missing pieces?
3. Style        - Does it follow project conventions (CLAUDE.md, indentation, frontmatter)?
4. Safety       - Any hardcoded secrets, dangerous commands, injection risks?

Rules:
- Be honest. Round-numbers (5, 7, 10) are fine - don't pad.
- If you cannot evaluate (file empty, missing context), output score=null and explain.
- Output STRICT JSON only. No prose outside JSON."""

USER_TEMPLATE = """## Task spec
{task_md}

## Result to evaluate
{result_md}

Output JSON:
{{
  "correctness":  <0-10 or null>,
  "completeness": <0-10 or null>,
  "style":        <0-10 or null>,
  "safety":       <0-10 or null>,
  "reason":       "<one sentence each dimension>",
  "verdict":      "PASS" | "FAIL" | "INCONCLUSIVE"
}}
"""


def derive_verdict(scores: dict) -> str:
    vals = [scores.get(k) for k in ("correctness", "completeness", "style", "safety")]
    if any(v is None for v in vals):
        return "INCONCLUSIVE"
    if scores["safety"] <= 7:
        return "FAIL"
    if any(v <= 4 for v in vals):
        return "FAIL"
    if all(v >= 7 for v in vals) and scores["safety"] == 10:
        return "PASS"
    return "INCONCLUSIVE"


def call_haiku(task_md: str, result_md: str) -> dict:
    """Call Haiku via anthropic SDK; cache rubric for 90% savings."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY missing"}

    try:
        import anthropic
    except ImportError:
        return {"error": "anthropic SDK not installed (pip install anthropic)"}

    client = anthropic.Anthropic(api_key=api_key)
    user = USER_TEMPLATE.format(task_md=task_md[:8000], result_md=result_md[:12000])

    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=[{"type": "text", "text": SYSTEM_RUBRIC,
                     "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
    except Exception as e:
        return {"error": f"API call failed: {e}"}

    text = "".join(b.text for b in resp.content if hasattr(b, "text")).strip()
    if text.startswith("```"):
        text = text.strip("`").lstrip("json").strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        return {"error": f"non-JSON response: {e}", "raw": text[:300]}

    usage = resp.usage
    in_tok = usage.input_tokens
    out_tok = usage.output_tokens
    cache_hit = getattr(usage, "cache_read_input_tokens", 0) or 0
    cost = (in_tok * 0.0008 + out_tok * 0.004 + cache_hit * 0.00008) / 1000
    parsed["_meta"] = {
        "model": "claude-haiku-4-5-20251001",
        "tokens_in": in_tok, "tokens_out": out_tok,
        "cache_hit": cache_hit, "cost_usd": round(cost, 6),
    }
    return parsed


def find_latest(pattern_dir: Path, suffix: str) -> Path | None:
    if not pattern_dir.exists():
        return None
    files = sorted(pattern_dir.glob(f"*{suffix}"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def append_jsonl(record: dict) -> None:
    EVAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with EVAL_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", type=Path)
    ap.add_argument("--result", type=Path)
    ap.add_argument("--auto", action="store_true")
    args = ap.parse_args()

    if args.auto:
        args.task = find_latest(PROJECT_ROOT / ".claude" / "tasks" / "done", ".md")
        args.result = find_latest(PROJECT_ROOT / "docs", "-report.md")

    if not args.task or not args.task.exists():
        print(f"[score_task] task file missing: {args.task}", file=sys.stderr)
        return 2
    if not args.result or not args.result.exists():
        print(f"[score_task] result file missing: {args.result}", file=sys.stderr)
        return 2

    task_md = args.task.read_text(encoding="utf-8", errors="ignore")
    result_md = args.result.read_text(encoding="utf-8", errors="ignore")
    task_id = args.task.stem

    judged = call_haiku(task_md, result_md)
    if "error" in judged:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "verdict": "INCONCLUSIVE",
            "reason": judged["error"],
            "scores": None,
        }
        append_jsonl(record)
        print(json.dumps(record, ensure_ascii=False, indent=2))
        return 3

    scores = {k: judged.get(k) for k in ("correctness", "completeness", "style", "safety")}
    verdict = judged.get("verdict") or derive_verdict(scores)
    if verdict not in ("PASS", "FAIL", "INCONCLUSIVE"):
        verdict = derive_verdict(scores)

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "result_file": str(args.result.relative_to(PROJECT_ROOT)),
        "scores": scores,
        "verdict": verdict,
        "reason": judged.get("reason", ""),
        "model": judged["_meta"]["model"],
        "cost_usd": judged["_meta"]["cost_usd"],
        "tokens": {"in": judged["_meta"]["tokens_in"], "out": judged["_meta"]["tokens_out"]},
    }
    append_jsonl(record)

    valid_scores = [v for v in scores.values() if isinstance(v, (int, float))]
    avg = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else None
    print(f"Task: {task_id} | File: {record['result_file']}")
    print("-" * 41)
    for k, v in scores.items():
        print(f"{k.capitalize():13s} {v if v is not None else 'n/a'}/10")
    print("-" * 41)
    print(f"VERDICT: {verdict}  (avg {avg})")
    print(f"Reason:  {record['reason']}")
    print(f"Saved:   {EVAL_LOG.relative_to(PROJECT_ROOT)} (line +1)")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
