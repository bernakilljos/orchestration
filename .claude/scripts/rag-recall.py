"""RAG 의미 검색 — ChromaDB + sentence-transformers (로컬, GPU 0).

vs recall-memory.py (키워드 grep):
- 의미 유사 검색 (synonym-paraphrase OK)
- index = CLAUDE.md + .claude/rules/ + memory/feedback + plugins/exec_orch/skills/

5 핵심 부품 #2 Data layer (RAG) — 사용자 GPU 부족 시 외부 LLM + 로컬 vector DB.
"""
import sys
import os
import json
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INDEX_DIR = PROJECT_ROOT / ".claude" / "state" / "chromadb"
COLLECTION_NAME = "project_knowledge"


def _ensure_chromadb():
    """chromadb 자동 install (없으면) — Zero-touch 자동화."""
    try:
        import chromadb  # noqa: F401
        return True
    except ImportError:
        import subprocess
        print("[rag-recall] chromadb 미설치 — 자동 install", file=sys.stderr)
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet", "chromadb", "sentence-transformers"],
                check=True, timeout=300,
            )
            import chromadb  # noqa: F401
            return True
        except Exception as e:
            print(f"[rag-recall] auto-install failed: {e}", file=sys.stderr)
            return False


def _get_client():
    if not _ensure_chromadb():
        raise RuntimeError("chromadb unavailable")
    import chromadb
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(INDEX_DIR))


def _get_embedding_fn():
    """한글 지원 embedding 함수 — bge-m3 (한-영 둘 다 강함) 사용 가능 시.
    fallback: chromadb 기본 (all-MiniLM-L6-v2 — 영어 위주).
    """
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        # BAAI/bge-m3 — 한글 + 영어 모두 최강. 약 2.3GB
        # 또는 paraphrase-multilingual-MiniLM-L12-v2 — 작고 빠름 (한글 지원)
        return SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
    except Exception:
        return None  # chromadb 기본 사용


def _docs_to_index() -> list:
    """index 대상 파일 자동 수집."""
    docs = []
    # 1. CLAUDE.md (project + global)
    for p in [PROJECT_ROOT / "CLAUDE.md", Path.home() / ".claude" / "CLAUDE.md"]:
        if p.exists():
            docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
    # 2. .claude/rules/
    for p in (PROJECT_ROOT / ".claude" / "rules").glob("*.md"):
        docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
    # 3. feedback memory
    proj_normalized = PROJECT_ROOT.name.replace("_", "-")
    mem_base = Path.home() / ".claude" / "projects"
    if mem_base.exists():
        for sub in mem_base.iterdir():
            if proj_normalized in sub.name:
                for p in (sub / "memory").glob("feedback_*.md") if (sub / "memory").exists() else []:
                    docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
    # 4. skills (모든 plugin)
    for p in (PROJECT_ROOT / "plugins").glob("*/skills/*.md"):
        docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
    # 5. references (49 toolkit — 12 RAG 기법 #12 의 핵심 RAG corpus)
    for p in (PROJECT_ROOT / "plugins").glob("*/references/*.md"):
        docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
    # 6. commands (slash command spec)
    for p in (PROJECT_ROOT / "plugins").glob("*/commands/*.md"):
        docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
    # 7. docs/ permanent (architecture-patterns-routing-policy-caching-strategy 등)
    for p in (PROJECT_ROOT / "docs").glob("*.md"):
        docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
    return docs


def index_build():
    """ChromaDB 컬렉션 빌드 — 모든 문서 자동 index."""
    client = _get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    emb_fn = _get_embedding_fn()
    if emb_fn:
        coll = client.create_collection(COLLECTION_NAME, embedding_function=emb_fn)
    else:
        coll = client.create_collection(COLLECTION_NAME)

    docs = _docs_to_index()
    if not docs:
        return {"indexed": 0, "error": "no docs"}

    ids = []
    contents = []
    metas = []
    # 청크 크기 — 환경변수 또는 default 800 (한글 문서에 적합, 영어는 500)
    chunk_size = int(os.environ.get("RAG_CHUNK_SIZE", "800"))
    chunk_overlap = int(os.environ.get("RAG_CHUNK_OVERLAP", "100"))
    for path, content in docs:
        for i in range(0, len(content), chunk_size - chunk_overlap):
            chunk = content[i:i + chunk_size]
            cid = hashlib.md5(f"{path}#{i}".encode()).hexdigest()
            ids.append(cid)
            contents.append(chunk)
            metas.append({"path": path, "chunk": i})

    # ChromaDB 기본 embedding (all-MiniLM-L6-v2 — 로컬, GPU 0)
    coll.add(ids=ids, documents=contents, metadatas=metas)
    return {"indexed": len(ids), "docs": len(docs), "collection": COLLECTION_NAME}


def search(query: str, top_n: int = 5) -> list:
    """의미 유사 검색."""
    client = _get_client()
    emb_fn = _get_embedding_fn()
    try:
        if emb_fn:
            coll = client.get_collection(COLLECTION_NAME, embedding_function=emb_fn)
        else:
            coll = client.get_collection(COLLECTION_NAME)
    except Exception:
        return [{"error": "index not built. run: rag-recall.py --build"}]

    results = coll.query(query_texts=[query], n_results=top_n)
    out = []
    for i in range(len(results["ids"][0])):
        out.append({
            "path": results["metadatas"][0][i].get("path", ""),
            "chunk": results["metadatas"][0][i].get("chunk", 0),
            "distance": round(results["distances"][0][i], 3) if results["distances"] else None,
            "preview": results["documents"][0][i][:200],
        })
    return out


if __name__ == "__main__":
    if "--build" in sys.argv:
        result = index_build()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)
    if len(sys.argv) < 2:
        if not sys.stdin.isatty():
            query = sys.stdin.read().strip()
        else:
            print("usage: rag-recall.py '<query>' [--build] [--top N]")
            sys.exit(2)
    else:
        query = sys.argv[1]
    top = 5
    if "--top" in sys.argv:
        i = sys.argv.index("--top")
        if i + 1 < len(sys.argv):
            top = int(sys.argv[i + 1])
    results = search(query, top)
    print(json.dumps(results, ensure_ascii=False, indent=2))
