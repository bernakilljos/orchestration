# doc_auto task — C:\\pjt\\orchestration_v1\\.claude\\scripts\\approval-gate.py

## Diff (HEAD)
```
diff --git a/.claude/scripts/approval-gate.py b/.claude/scripts/approval-gate.py
index 4a192b3..8c2b353 100644
--- a/.claude/scripts/approval-gate.py
+++ b/.claude/scripts/approval-gate.py
@@ -211,6 +211,11 @@ def status(task_id: str) -> dict:
 
 
 def main():
+    # Windows cp949 회피 — stdout UTF-8 강제
+    try:
+        sys.stdout.reconfigure(encoding='utf-8')
+    except (AttributeError, Exception):
+        pass
     if len(sys.argv) < 2:
         print(__doc__)
         sys.exit(2)
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
