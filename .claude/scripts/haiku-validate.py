#!/usr/bin/env python3
"""
haiku-validate.py <task_file> --worker-id <worker_id> --project-root <root>

Validate a task with Claude Haiku 4.5.
- Reads task from .claude/tasks/task-*.md
- Uses prompt caching for CLAUDE.md + system context
- Saves result to docs/YYYY-MM-DD/haiku-review-{task_name}.md
- Records metrics to SQLite (tokens, latency, cost)
- Exit codes: 0=success, 1=failure, 3=quota exceeded
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

# Add lib path for imports
script_dir = Path(__file__).parent
lib_dir = script_dir / "lib"
sys.path.insert(0, str(lib_dir))

try:
    from state_db import record_metric, set_quota_exceeded, init_schema
    from prompt_cache import build_cached_system, cache_control_block
    from pricing import estimate_cost
except ImportError as e:
    print(f"ERROR: Missing lib module: {e}", file=sys.stderr)
    sys.exit(1)


def read_file(path: Path) -> str:
    """Read file with UTF-8 encoding."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"ERROR reading {path}: {e}", file=sys.stderr)
        return ""


def build_validation_prompt(task_content: str, claude_md: str) -> tuple[list, list]:
    """
    Build system prompt with caching and messages array.

    Returns:
        (system_array, messages_array)
    """
    system = build_cached_system([
        {
            "text": "You are a rigorous code validator. Your role:\n"
                    "1. Review implementation against task requirements\n"
                    "2. Check for quality, correctness, security concerns\n"
                    "3. Provide concise verdict and actionable feedback\n"
                    "Be thorough but brief.",
            "cacheable": True
        },
        {
            "text": f"# Project Context (CLAUDE.md)\n\n{claude_md}",
            "cacheable": True
        },
    ])

    messages = [{
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": f"# Task to Validate\n\n{task_content}\n\n"
                       f"# Your Review\n\n"
                       f"Provide a structured review:\n\n"
                       f"## Verdict\n[PASS | NEEDS_FIX | FAIL]\n\n"
                       f"## Key Findings\n[Bullet list of issues or confirmations]\n\n"
                       f"## Recommendations\n[Suggestions for improvement, if any]\n\n"
                       f"Keep this concise (under 500 tokens). Focus on what matters most."
            }
        ]
    }]

    return system, messages


def call_haiku(system: list, messages: list, project_root: Path) -> dict:
    """
    Call Claude Haiku 4.5 API.

    Returns:
        {
            "success": bool,
            "content": str (response text or error),
            "usage": {
                "input_tokens": int,
                "output_tokens": int,
                "cache_creation_tokens": int,
                "cache_read_tokens": int
            },
            "latency_ms": int,
            "error_class": str or None
        }
    """
    try:
        import anthropic
    except ImportError:
        return {
            "success": False,
            "content": "anthropic SDK not installed. Run: pip install anthropic",
            "error_class": "import_error",
            "latency_ms": 0
        }

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "success": False,
            "content": "ANTHROPIC_API_KEY environment variable not set",
            "error_class": "auth",
            "latency_ms": 0
        }

    client = anthropic.Anthropic(api_key=api_key)
    t0 = time.time()

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=2048,
            system=system,
            messages=messages,
        )
    except anthropic.RateLimitError as e:
        latency = int((time.time() - t0) * 1000)
        return {
            "success": False,
            "content": f"Rate limited: {str(e)}",
            "error_class": "quota",
            "latency_ms": latency
        }
    except anthropic.APIError as e:
        latency = int((time.time() - t0) * 1000)
        error_str = str(e).lower()
        if "429" in error_str or "quota" in error_str or "rate" in error_str:
            return {
                "success": False,
                "content": str(e),
                "error_class": "quota",
                "latency_ms": latency
            }
        elif "timeout" in error_str:
            return {
                "success": False,
                "content": str(e),
                "error_class": "timeout",
                "latency_ms": latency
            }
        else:
            return {
                "success": False,
                "content": str(e),
                "error_class": "api_error",
                "latency_ms": latency
            }
    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        return {
            "success": False,
            "content": f"Unexpected error: {str(e)}",
            "error_class": "other",
            "latency_ms": latency
        }

    latency = int((time.time() - t0) * 1000)
    content_text = "\n".join([b.text for b in response.content if hasattr(b, "text")])

    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cache_creation_tokens": getattr(response.usage, "cache_creation_input_tokens", 0),
        "cache_read_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
    }

    return {
        "success": True,
        "content": content_text,
        "usage": usage,
        "latency_ms": latency,
        "error_class": None
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate task with Claude Haiku 4.5"
    )
    parser.add_argument("task_file", help="Path to task .md file")
    parser.add_argument("--worker-id", required=True, help="Worker identifier (e.g., haiku-1)")
    parser.add_argument("--project-root", default=None, help="Project root path")

    args = parser.parse_args()

    # Resolve paths
    task_file = Path(args.task_file).resolve()
    if not task_file.exists():
        print(f"ERROR: Task file not found: {task_file}", file=sys.stderr)
        sys.exit(1)

    if args.project_root:
        project_root = Path(args.project_root).resolve()
    else:
        project_root = Path(os.environ.get("PROJECT_ROOT", Path.cwd())).resolve()

    # Initialize DB schema
    try:
        init_schema()
    except Exception as e:
        print(f"WARN: Could not init DB: {e}", file=sys.stderr)

    # Read task content
    task_content = read_file(task_file)
    if not task_content:
        print(f"ERROR: Task file is empty: {task_file}", file=sys.stderr)
        sys.exit(1)

    # Read CLAUDE.md for context
    claude_md_path = project_root / "CLAUDE.md"
    claude_md = read_file(claude_md_path) if claude_md_path.exists() else ""

    # Build prompt with caching
    system, messages = build_validation_prompt(task_content, claude_md)

    # Call Haiku
    result = call_haiku(system, messages, project_root)

    # Handle errors
    if result["error_class"] == "quota":
        # Set quota exceeded with 1 hour recovery
        try:
            expires_at = int(time.time()) + 3600
            set_quota_exceeded("claude-haiku", expires_at, result["content"])
        except Exception as e:
            print(f"WARN: Could not record quota: {e}", file=sys.stderr)

        try:
            record_metric(
                ai="claude-haiku",
                model_id="claude-haiku-4-5",
                tokens_in=0,
                tokens_out=0,
                cost_usd=0.0,
                latency_ms=result["latency_ms"],
                success=False,
                task_id=task_file.stem,
                error_class="quota"
            )
        except Exception as e:
            print(f"WARN: Could not record metric: {e}", file=sys.stderr)

        print(f"[{args.worker_id}] Quota exceeded. Waiting before retry.", file=sys.stderr)
        sys.exit(3)

    if not result["success"]:
        try:
            record_metric(
                ai="claude-haiku",
                model_id="claude-haiku-4-5",
                tokens_in=0,
                tokens_out=0,
                cost_usd=0.0,
                latency_ms=result["latency_ms"],
                success=False,
                task_id=task_file.stem,
                error_class=result.get("error_class", "unknown")
            )
        except Exception as e:
            print(f"WARN: Could not record metric: {e}", file=sys.stderr)

        print(f"[{args.worker_id}] Validation failed: {result['content']}", file=sys.stderr)
        sys.exit(1)

    # Success: write result to docs
    today = datetime.now().strftime("%Y-%m-%d")
    out_dir = project_root / "docs" / today
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"ERROR: Could not create docs dir: {e}", file=sys.stderr)
        sys.exit(1)

    out_file = out_dir / f"haiku-review-{task_file.stem}.md"
    try:
        out_file.write_text(result["content"], encoding="utf-8")
    except Exception as e:
        print(f"ERROR: Could not write review: {e}", file=sys.stderr)
        sys.exit(1)

    # Calculate cost
    usage = result.get("usage", {})
    cost = estimate_cost(
        "claude-haiku-4-5",
        usage.get("input_tokens", 0),
        usage.get("output_tokens", 0),
        cache_hit_tokens=usage.get("cache_read_tokens", 0),
        cache_write_tokens=usage.get("cache_creation_tokens", 0),
    )

    # Record metrics
    try:
        record_metric(
            ai="claude-haiku",
            model_id="claude-haiku-4-5",
            tokens_in=usage.get("input_tokens", 0),
            tokens_out=usage.get("output_tokens", 0),
            cost_usd=cost,
            latency_ms=result["latency_ms"],
            success=True,
            task_id=task_file.stem,
            cache_hit=bool(usage.get("cache_read_tokens", 0) > 0)
        )
    except Exception as e:
        print(f"WARN: Could not record metric: {e}", file=sys.stderr)

    # Log success
    print(f"[{args.worker_id}] Review saved: {out_file}")
    print(f"  Tokens: {usage.get('input_tokens', 0)}in + {usage.get('output_tokens', 0)}out "
          f"| Cache: read={usage.get('cache_read_tokens', 0)}/write={usage.get('cache_creation_tokens', 0)} "
          f"| Cost: ${cost:.6f} | Latency: {result['latency_ms']}ms")

    sys.exit(0)


if __name__ == "__main__":
    main()
