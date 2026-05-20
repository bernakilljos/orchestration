# doc_auto task — C:\\pjt\\orchestration_v1\\.claude\\scripts\\verify-teaching-doc-sections.py

## Diff (HEAD)
```
diff --git a/.claude/scripts/verify-teaching-doc-sections.py b/.claude/scripts/verify-teaching-doc-sections.py
new file mode 100644
index 0000000..e8805e9
--- /dev/null
+++ b/.claude/scripts/verify-teaching-doc-sections.py
@@ -0,0 +1,109 @@
+#!/usr/bin/env python3
+"""verify-teaching-doc-sections.py — 교재/강의 doc 8섹션 검증
+
+룰: .claude/rules/teaching-doc.md
+8섹션: 핵심 한 줄·표·흐름·강점·약점·강추·우리 시스템 매핑·점검
+
+호출:
+  python verify-teaching-doc-sections.py <docx_or_md_path>
+
+종료 코드:
+  0 = 통과
+  1 = 누락 섹션 있음
+  2 = 파일 못 읽음
+"""
+import re
+import sys
+from pathlib import Path
+
+SECTION_PATTERNS = {
+    "1.핵심": r"📚|핵심.{0,4}한.?줄|핵심\s",
+    "2.표":   r"📊|^\s*\|.*\|.*\||\<table\>|<tr>",
+    "3.흐름": r"🌊|흐름|flow|단계|→",
+    "4.강점": r"💪|강점|장점",
+    "5.약점": r"⚠️|약점|주의|함정|단점",
+    "6.강추": r"⭐|강추|추천|언제\s.*사용",
+    "7.매핑": r"🎯|우리\s?시스템|우리\s?매핑|orchestration_v1",
+    "8.점검": r"🧪|점검|check|확인|체크",
+}
+
+
+def extract_text(path: Path) -> str:
+    suffix = path.suffix.lower()
+    if suffix == ".docx":
+        try:
+            from docx import Document
+            doc = Document(str(path))
+            parts = [p.text for p in doc.paragraphs]
+            for table in doc.tables:
+                for row in table.rows:
+                    for cell in row.cells:
+                        parts.append(cell.text)
+            return "\n".join(parts)
+        except Exception as e:
+            print(f"[ERROR] docx 읽기 실패: {e}", file=sys.stderr)
+            return ""
+    elif suffix in (".md", ".txt"):
+        try:
+            return path.read_text(encoding="utf-8", errors="replace")
+        except Exception as e:
+            print(f"[ERROR] {suffix} 읽기 실패: {e}", file=sys.stderr)
+            return ""
+    elif suffix == ".pdf":
+        try:
+            import fitz  # PyMuPDF
+            doc = fitz.open(str(path))
+            return "\n".join(page.get_text() for page in doc)
+        except Exception:
+            return ""
+    return ""
+
+
+def main():
+    if len(sys.argv) < 2:
+        print(__doc__)
+        sys.exit(2)
+
+    path = Path(sys.argv[1])
+    if not path.exists():
+        print(f"[ERROR] 파일 없음: {path}", file=sys.stderr)
+        sys.exit(2)
+
+    # 교재/강의/가이드 doc 만 검증 — 파일명·경로 휴리스틱
+    name_lower = str(path).lower()
+    is_teaching = any(k in name_lower for k in [
+        "teaching", "교재", "강의", "guide", "가이드", "튜토리얼", "tutorial",
+        "docs/", "docs\\",
+    ])
+    if not is_teaching:
+        # 비-교재 doc 은 skip
+        sys.exit(0)
+
+    text = extract_text(path)
+    if not text:
+        sys.exit(2)
+
+    missing = []
+    found = []
+    for label, pattern in SECTION_PATTERNS.items():
+        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
+            found.append(label)
+        else:
+            missing.append(label)
+
+    if missing:
+        # systemMessage 로 Claude 에게 알림 (PostToolUse 차단 X)
+        print(f"[VIOLATION] teaching-doc 8섹션 누락 ({len(missing)}/8): {missing}",
+              file=sys.stderr)
+        print(f"[OK] 발견: {found}", file=sys.stderr)
+        print(f"[FILE] {path}", file=sys.stderr)
+        print("[RULE] .claude/rules/teaching-doc.md § 각 챕터 필수 8 섹션",
+              file=sys.stderr)
+        sys.exit(1)
+
+    print(f"[PASS] {path}: 8섹션 모두 발견")
+    sys.exit(0)
+
+
+if __name__ == "__main__":
+    main()
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
