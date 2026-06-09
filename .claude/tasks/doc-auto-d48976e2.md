# doc_auto task — C:\\work\\orchestration_v1\\.claude\\scripts\\rag-recall.py

## Diff (HEAD)
```
diff --git a/.claude/scripts/rag-recall.py b/.claude/scripts/rag-recall.py
index 0247cfd..5aeb77a 100644
--- a/.claude/scripts/rag-recall.py
+++ b/.claude/scripts/rag-recall.py
@@ -17,7 +17,29 @@ INDEX_DIR = PROJECT_ROOT / ".claude" / "state" / "chromadb"
 COLLECTION_NAME = "project_knowledge"
 
 
+def _ensure_chromadb():
+    """chromadb 자동 install (없으면) — Zero-touch 자동화."""
+    try:
+        import chromadb  # noqa: F401
+        return True
+    except ImportError:
+        import subprocess
+        print("[rag-recall] chromadb 미설치 — 자동 install", file=sys.stderr)
+        try:
+            subprocess.run(
+                [sys.executable, "-m", "pip", "install", "--quiet", "chromadb", "sentence-transformers"],
+                check=True, timeout=300,
+            )
+            import chromadb  # noqa: F401
+            return True
+        except Exception as e:
+            print(f"[rag-recall] auto-install failed: {e}", file=sys.stderr)
+            return False
+
+
 def _get_client():
+    if not _ensure_chromadb():
+        raise RuntimeError("chromadb unavailable")
     import chromadb
     INDEX_DIR.mkdir(parents=True, exist_ok=True)
     return chromadb.PersistentClient(path=str(INDEX_DIR))
@@ -56,8 +78,17 @@ def _docs_to_index() -> list:
             if proj_normalized in sub.name:
                 for p in (sub / "memory").glob("feedback_*.md") if (sub / "memory").exists() else []:
                     docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
-    # 4. skills
-    for p in (PROJECT_ROOT / "plugins" / "exec_orch" / "skills").glob("*.md"):
+    # 4. skills (모든 plugin)
+    for p in (PROJECT_ROOT / "plugins").glob("*/skills/*.md"):
+        docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
+    # 5. references (49 toolkit — 12 RAG 기법 #12 의 핵심 RAG corpus)
+    for p in (PROJECT_ROOT / "plugins").glob("*/references/*.md"):
+        docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
+    # 6. commands (slash command spec)
+    for p in (PROJECT_ROOT / "plugins").glob("*/commands/*.md"):
+        docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
+    # 7. docs/ permanent (architecture-patterns·routing-policy·caching-strategy 등)
+    for p in (PROJECT_ROOT / "docs").glob("*.md"):
         docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
     return docs
 
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
