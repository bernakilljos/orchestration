# doc_auto task — C:\\work\\orchestration_v1\\.claude\\scripts\\fix_bom.py

## Diff (HEAD)
```
diff --git a/.claude/scripts/fix_bom.py b/.claude/scripts/fix_bom.py
new file mode 100644
index 0000000..4751442
--- /dev/null
+++ b/.claude/scripts/fix_bom.py
@@ -0,0 +1,76 @@
+"""
+UTF-8 BOM 제거 — 범용 wrapper.
+사용:
+  python .claude/scripts/fix_bom.py <file1> [file2 ...]
+  python .claude/scripts/fix_bom.py --from-audit <audit.json>   # audit json 의 'UTF-8 BOM' detail 항목 자동 처리
+  python .claude/scripts/fix_bom.py --glob "**/*.py"            # glob 으로 후보 스캔
+"""
+from __future__ import annotations
+
+import argparse
+import json
+from pathlib import Path
+
+BOM = b'\xef\xbb\xbf'
+
+
+def strip_bom(path: Path) -> str:
+    raw = path.read_bytes()
+    if raw.startswith(BOM):
+        path.write_bytes(raw[len(BOM):])
+        return "fixed"
+    return "skipped"
+
+
+def iter_audit_targets(audit_path: Path):
+    obj = json.loads(audit_path.read_text(encoding="utf-8", errors="replace"))
+    results = obj.get("results", {}) if isinstance(obj, dict) else {}
+    if not isinstance(results, dict):
+        return
+    for section_items in results.values():
+        if not isinstance(section_items, list):
+            continue
+        for item in section_items:
+            if not isinstance(item, dict):
+                continue
+            detail = str(item.get("detail", ""))
+            path = str(item.get("item", "")).strip()
+            if "UTF-8 BOM" in detail and path:
+                yield path
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser()
+    parser.add_argument("files", nargs="*", help="파일 경로 (직접 지정)")
+    parser.add_argument("--from-audit", type=Path, help="audit json 파일에서 BOM 항목 자동 추출")
+    parser.add_argument("--glob", help="glob 패턴 (예: '**/*.py')")
+    args = parser.parse_args()
+
+    targets: list[str] = list(args.files)
+    if args.from_audit and args.from_audit.exists():
+        targets.extend(iter_audit_targets(args.from_audit))
+    if args.glob:
+        targets.extend(str(p) for p in Path(".").glob(args.glob))
+
+    if not targets:
+        print("no targets")
+        return 1
+
+    fixed = skipped = missing = 0
+    for rel in sorted(set(targets)):
+        p = Path(rel)
+        if not p.exists():
+            missing += 1
+            continue
+        status = strip_bom(p)
+        if status == "fixed":
+            fixed += 1
+        else:
+            skipped += 1
+
+    print(f"total={fixed+skipped+missing} fixed={fixed} skipped={skipped} missing={missing}")
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
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
