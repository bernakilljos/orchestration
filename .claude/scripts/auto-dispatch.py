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


def make_task_instruction(message: str, ai: str, task_type: str, reason: str) -> str:
    """task-instruction.md 자동 작성."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""# Task — Auto-Dispatched

**Timestamp**: {ts}
**Assigned AI**: {ai}
**Task Type**: {task_type}
**Reason**: {reason}

## Original Request

{message}

## Expected Output

- {ai} 가 위 요청 분석 + 실행
- 완료 시 결과 파일 또는 commit
- 검증: verify-* 도구 자동 발동

## Auto-Dispatch Metadata

```json
{json.dumps({"ai": ai, "task_type": task_type, "reason": reason, "auto": True}, ensure_ascii=False)}
```
"""


def enqueue(message: str, target: str = "local") -> dict:
    """task 자동 분류 + dispatch."""
    result = classify(message)
    ai = result["ai"]
    if ai == "claude":
        return {**result, "dispatched": False, "reason": result["reason"] + " — Claude 직접 처리"}

    # task-instruction.md 작성
    instruction = make_task_instruction(message, ai, result["task_type"], result["reason"])
    queue_dir = GLOBAL_ORCA if target == "global" else TASKS_DIR
    queue_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_msg = re.sub(r"[^\w\-]", "_", message[:30])
    task_file = queue_dir / f"task-{ts}-{ai}-{safe_msg}.md"
    task_file.write_text(instruction, encoding="utf-8")

    return {
        **result,
        "dispatched": True,
        "task_file": str(task_file),
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
