"""RAG ?섎? 寃????ChromaDB + sentence-transformers (濡쒖뺄, GPU 0).

vs recall-memory.py (?ㅼ썙??grep):
- ?섎? ?좎궗 寃??(synonym-paraphrase OK)
- index = CLAUDE.md + .claude/rules/ + memory/feedback + plugins/exec_orch/skills/

5 ?듭떖 遺??#2 Data layer (RAG) ???ъ슜??GPU 遺議????몃? LLM + 濡쒖뺄 vector DB.
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
    """chromadb ?먮룞 install (?놁쑝硫? ??Zero-touch ?먮룞??"""
    try:
        import chromadb  # noqa: F401
        return True
    except ImportError:
        import subprocess
        print("[rag-recall] chromadb 誘몄꽕移????먮룞 install", file=sys.stderr)
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet", "chromadb", "sentence-transformers"],
                check=True, timeout=300,
            )
            import chromadb  # noqa: F401
            return True
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            print(f"[rag-recall] auto-install failed: {e}", file=sys.stderr)
            return False


def _get_client():
    if not _ensure_chromadb():
        raise RuntimeError("chromadb unavailable")
    import chromadb
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(INDEX_DIR))


def _get_embedding_fn():
    """?쒓? 吏??embedding ?⑥닔 ??bge-m3 (????????媛뺥븿) ?ъ슜 媛????
    fallback: chromadb 湲곕낯 (all-MiniLM-L6-v2 ???곸뼱 ?꾩＜).
    """
    try:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        # BAAI/bge-m3 ???쒓? + ?곸뼱 紐⑤몢 理쒓컯. ??2.3GB
        # ?먮뒗 paraphrase-multilingual-MiniLM-L12-v2 ???묎퀬 鍮좊쫫 (?쒓? 吏??
        return SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return None  # chromadb 湲곕낯 ?ъ슜


def _docs_to_index() -> list:
    """index ????뚯씪 ?먮룞 ?섏쭛."""
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
    # 4. skills (紐⑤뱺 plugin)
    for p in (PROJECT_ROOT / "plugins").glob("*/skills/*.md"):
        docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
    # 5. references (49 toolkit ??12 RAG 湲곕쾿 #12 ???듭떖 RAG corpus)
    for p in (PROJECT_ROOT / "plugins").glob("*/references/*.md"):
        docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
    # 6. commands (slash command spec)
    for p in (PROJECT_ROOT / "plugins").glob("*/commands/*.md"):
        docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
    # 7. docs/ permanent (architecture-patterns-routing-policy-caching-strategy ??
    for p in (PROJECT_ROOT / "docs").glob("*.md"):
        docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
    return docs


def index_build():
    """ChromaDB 而щ젆??鍮뚮뱶 ??紐⑤뱺 臾몄꽌 ?먮룞 index."""
    client = _get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
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
    # 泥?겕 ?ш린 ???섍꼍蹂???먮뒗 default 800 (?쒓? 臾몄꽌???곹빀, ?곸뼱??500)
    chunk_size = int(os.environ.get("RAG_CHUNK_SIZE", "800"))
    chunk_overlap = int(os.environ.get("RAG_CHUNK_OVERLAP", "100"))
    for path, content in docs:
        for i in range(0, len(content), chunk_size - chunk_overlap):
            chunk = content[i:i + chunk_size]
            cid = hashlib.md5(f"{path}#{i}".encode()).hexdigest()
            ids.append(cid)
            contents.append(chunk)
            metas.append({"path": path, "chunk": i})

    # ChromaDB 湲곕낯 embedding (all-MiniLM-L6-v2 ??濡쒖뺄, GPU 0)
    coll.add(ids=ids, documents=contents, metadatas=metas)
    return {"indexed": len(ids), "docs": len(docs), "collection": COLLECTION_NAME}


def search(query: str, top_n: int = 5) -> list:
    """?섎? ?좎궗 寃??"""
    client = _get_client()
    emb_fn = _get_embedding_fn()
    try:
        if emb_fn:
            coll = client.get_collection(COLLECTION_NAME, embedding_function=emb_fn)
        else:
            coll = client.get_collection(COLLECTION_NAME)
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
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

