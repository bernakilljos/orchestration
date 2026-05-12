"""mHC 자동 인수인계 chain — Claude 결정 → 자동 AI dispatch.

흐름:
1. classify-task.py 로 사용자 메시지 분류
2. AI 결정 (codex/gemini/haiku/claude)
3. task-instruction.md 자동 작성
4. .claude/tasks/ 또는 ~/.claude/orca/ 에 enqueue → 워커 폴링
"""
import sys
import os
import json
import time
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TASKS_DIR = PROJECT_ROOT / ".claude" / "tasks"
GLOBAL_ORCA = Path.home() / ".claude" / "orca"

sys.path.insert(0, str(PROJECT_ROOT / ".claude" / "scripts"))
from importlib import import_module
_classify = import_module("classify-task")
classify = _classify.classify


def make_task_instruction(message: str, ai: str, task_type: str, reason: str, chunk_info: str = "") -> str:
    """task-instruction.md 자동 작성."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # AI 별 context 한계 (Codex 작아 chunk 필요)
    AI_CONTEXT = {"codex": "128k", "haiku": "200k", "gemini": "1M+", "claude": "1M"}
    ctx_limit = AI_CONTEXT.get(ai, "unknown")
    return f"""# Task — Auto-Dispatched

**Timestamp**: {ts}
**Assigned AI**: {ai} (context limit: {ctx_limit})
**Task Type**: {task_type}
**Reason**: {reason}
{chunk_info}

## Original Request

{message}

## Expected Output

- {ai} 가 위 요청 분석 + 실행
- 완료 시 결과 파일 또는 commit
- 검증: verify-* 도구 자동 발동

## Auto-Dispatch Metadata

```json
{json.dumps({"ai": ai, "task_type": task_type, "reason": reason, "context_limit": ctx_limit, "auto": True}, ensure_ascii=False)}
```
"""


def estimate_tokens(text: str) -> int:
    """대략적 토큰 추정 (한글·영어 혼합 평균)."""
    # 한글 1자 ≈ 1.5 token, 영어 4자 ≈ 1 token 추정
    return int(len(text) * 1.2)


def chunk_message(message: str, chunk_size_tokens: int = 50000) -> list:
    """큰 task 자동 chunk 분할 (Codex 용).

    파일·섹션 단위 우선 분할. 안 되면 줄 단위.
    """
    estimated = estimate_tokens(message)
    if estimated <= chunk_size_tokens:
        return [message]
    # 줄 단위 분할 (chunk_size_tokens 까지)
    lines = message.split("\n")
    chunks = []
    current = []
    current_tokens = 0
    for line in lines:
        line_tokens = estimate_tokens(line)
        if current_tokens + line_tokens > chunk_size_tokens and current:
            chunks.append("\n".join(current))
            current = [line]
            current_tokens = line_tokens
        else:
            current.append(line)
            current_tokens += line_tokens
    if current:
        chunks.append("\n".join(current))
    return chunks


def enqueue(message: str, target: str = "local") -> dict:
    """task 자동 분류 + dispatch + Codex chunk 분할."""
    result = classify(message)
    ai = result["ai"]
    if ai == "claude":
        return {**result, "dispatched": False, "reason": result["reason"] + " — Claude 직접 처리"}

    # AI 별 chunk_size — Codex 작아서 자동 분할
    CHUNK_SIZE = {"codex": 50000, "haiku": 150000, "gemini": 500000}
    chunk_limit = CHUNK_SIZE.get(ai, 100000)
    chunks = chunk_message(message, chunk_limit)
    queue_dir = GLOBAL_ORCA if target == "global" else TASKS_DIR
    queue_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_msg = re.sub(r"[^\w\-]", "_", message[:30])
    task_files = []
    for i, chunk in enumerate(chunks, 1):
        chunk_info = f"\n**Chunk**: {i}/{len(chunks)} (자동 분할 — {ai} context 한계 대응)" if len(chunks) > 1 else ""
        instruction = make_task_instruction(chunk, ai, result["task_type"], result["reason"], chunk_info)
        suffix = f"-chunk{i:02d}" if len(chunks) > 1 else ""
        task_file = queue_dir / f"task-{ts}-{ai}-{safe_msg}{suffix}.md"
        task_file.write_text(instruction, encoding="utf-8")
        task_files.append(str(task_file))

    return {
        **result,
        "dispatched": True,
        "task_files": task_files,
        "chunks": len(chunks),
        "target": target,
        "worker": f"{ai}-auto",
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        if not sys.stdin.isatty():
            msg = sys.stdin.read().strip()
        else:
            print("usage: auto-dispatch.py '<사용자 메시지>' [--global]")
            sys.exit(2)
    else:
        msg = sys.argv[1] if not sys.argv[1].startswith("--") else " ".join(sys.argv[2:])

    target = "global" if "--global" in sys.argv else "local"
    res = enqueue(msg, target)
    print(json.dumps(res, ensure_ascii=False, indent=2))
