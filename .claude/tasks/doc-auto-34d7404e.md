# doc_auto task — C:\\pjt\\orchestration_v1\\.claude\\scripts\\lib\\file_lock_poller.py

## Diff (HEAD)
```
diff --git a/.claude/scripts/lib/file_lock_poller.py b/.claude/scripts/lib/file_lock_poller.py
new file mode 100644
index 0000000..a2d99c3
--- /dev/null
+++ b/.claude/scripts/lib/file_lock_poller.py
@@ -0,0 +1,91 @@
+"""file_lock_poller.py — 파일 잠금 / 외부 의존 fail 시 자동 폴링 라이브러리
+
+룰: .claude/rules/best-practices.md § 멈춤 방지
+     feedback_no_user_stop.md
+
+사용:
+    from file_lock_poller import wait_unlock, exp_backoff, install_tool_if_missing
+    wait_unlock(path, max_sec=60, interval=2)
+    exp_backoff(max_retries=4, fn=lambda: my_call())
+"""
+from __future__ import annotations
+
+import os
+import shutil
+import subprocess
+import sys
+import time
+from pathlib import Path
+from typing import Callable, TypeVar
+
+T = TypeVar("T")
+
+
+def wait_unlock(path: Path | str, max_sec: int = 60, interval: int = 2) -> bool:
+    """파일 잠금 해제까지 폴링. 반환: True=풀림 / False=timeout."""
+    p = Path(path)
+    elapsed = 0
+    while elapsed < max_sec:
+        try:
+            # rename trick — Windows 파일 잠금 감지
+            test = p.with_suffix(p.suffix + ".lock-test")
+            p.rename(test)
+            test.rename(p)
+            return True
+        except (PermissionError, OSError):
+            if elapsed == 0:
+                print(f"[WAIT] {p.name} 잠김 — {max_sec}초 폴링", file=sys.stderr)
+            time.sleep(interval)
+            elapsed += interval
+    print(f"[FAIL] {p.name} 잠금 안 풀림 ({max_sec}초)", file=sys.stderr)
+    return False
+
+
+def exp_backoff(fn: Callable[[], T], max_retries: int = 4, base_delay: float = 2.0) -> T | None:
+    """지수 backoff retry. fn() 가 Exception 던지면 재시도. 반환: 마지막 결과 또는 None."""
+    delay = base_delay
+    last_exc = None
+    for i in range(max_retries):
+        try:
+            return fn()
+        except Exception as e:
+            last_exc = e
+            if i < max_retries - 1:
+                print(f"[RETRY {i+1}/{max_retries}] sleep {delay}s — {e}", file=sys.stderr)
+                time.sleep(delay)
+                delay *= 2
+    print(f"[FAIL] {max_retries} retries 후 실패: {last_exc}", file=sys.stderr)
+    return None
+
+
+def install_tool_if_missing(tool: str, install_cmd: list[str]) -> bool:
+    """도구 PATH에 없으면 자동 설치 후 재확인."""
+    if shutil.which(tool):
+        return True
+    print(f"[INSTALL] {tool} 자동 설치: {' '.join(install_cmd)}", file=sys.stderr)
+    try:
+        subprocess.run(install_cmd, check=True, capture_output=True, text=True)
+    except subprocess.CalledProcessError as e:
+        print(f"[FAIL] {tool} 설치 실패: {e.stderr}", file=sys.stderr)
+        return False
+    return shutil.which(tool) is not None
+
+
+def safe_write(path: Path | str, content: bytes | str, max_lock_wait: int = 60) -> bool:
+    """파일 잠금 폴링 후 쓰기. 실패 = False."""
+    p = Path(path)
+    if p.exists() and not wait_unlock(p, max_sec=max_lock_wait):
+        return False
+    try:
+        if isinstance(content, str):
+            p.write_text(content, encoding="utf-8")
+        else:
+            p.write_bytes(content)
+        return True
+    except (PermissionError, OSError) as e:
+        print(f"[FAIL] write {p}: {e}", file=sys.stderr)
+        return False
+
+
+if __name__ == "__main__":
+    print(__doc__)
```

## Action
1. 변경된 public API 추출 (함수·클래스·exports)
2. CHANGELOG.md `[Unreleased]` 섹션에 entry 추가:
   - Added/Changed/Fixed/Removed/Security 분류
3. README.md 의 API 섹션 갱신 (있을 시)
4. docs/api/<module>.md 갱신 (있을 시)

## Constraints
- 기존 entry 덮어쓰기 X (append)
- 자동 commit X (사용자 review 대기)
- 내부 helper 변경 skip (public API 만)
