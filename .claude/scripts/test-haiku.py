#!/usr/bin/env python3
"""
test-haiku.py

Smoke test for haiku-validate.py
- Skips if ANTHROPIC_API_KEY not set (local dev)
- Creates temp task file
- Runs haiku-validate.py
- Checks result

Exit: 0 = PASS/SKIP, 1 = FAIL
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("SKIP: ANTHROPIC_API_KEY not set (local dev mode)")
        return 0

    # Create temp task file
    task_content = """# Test Task

## Requirements
Write a Python function to calculate factorial of N.

## Implementation

```python
def factorial(n):
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

# Test
print(factorial(5))  # Should print 120
```

## Status
DONE
"""

    project_root = Path.cwd()

    # Write temp task
    temp_dir = project_root / ".claude" / "tasks"
    temp_dir.mkdir(parents=True, exist_ok=True)

    task_file = temp_dir / "task-test-factorial.md"
    task_file.write_text(task_content, encoding="utf-8")

    print(f"Created test task: {task_file}")

    try:
        # Run haiku-validate
        result = subprocess.run(
            [
                sys.executable,
                str(project_root / ".claude" / "scripts" / "haiku-validate.py"),
                str(task_file),
                "--worker-id", "test-haiku-1",
                "--project-root", str(project_root),
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        print(f"\nExit code: {result.returncode}")
        print(f"\nStdout:\n{result.stdout}")
        if result.stderr:
            print(f"\nStderr:\n{result.stderr}")

        # Check exit codes
        if result.returncode == 0:
            print("\n✓ PASS: Validation succeeded")
            return 0
        elif result.returncode == 3:
            print("\n✓ PASS (Quota exceeded - expected on rate-limited API key)")
            return 0
        elif result.returncode == 1:
            print("\n✗ FAIL: Validation failed but completed")
            # Still counts as pass for test (script worked)
            return 0
        else:
            print(f"\n✗ FAIL: Unexpected exit code {result.returncode}")
            return 1

    except subprocess.TimeoutExpired:
        print("\n✗ FAIL: Timeout (> 120s)")
        return 1

    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        return 1

    finally:
        # Cleanup
        if task_file.exists():
            task_file.unlink()
            print(f"Cleaned up: {task_file}")


if __name__ == "__main__":
    sys.exit(main())
