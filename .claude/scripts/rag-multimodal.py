"""Multimodal RAG — 이미지 + 텍스트 통합 검색.

최소 구현: 이미지 캡션 + filename 텍스트 indexing.
실제 사용 시 CLIP/BLIP 같은 이미지 embedding 모델 권장.
"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / ".claude" / "scripts"))

import importlib.util
spec = importlib.util.spec_from_file_location("rag", PROJECT_ROOT / ".claude" / "scripts" / "rag-recall.py")
rag = importlib.util.module_from_spec(spec); spec.loader.exec_module(rag)

# 이미지 디렉토리
IMG_DIRS = [
    PROJECT_ROOT / "docs" / "screens" / "arch-kor",
    PROJECT_ROOT / "docs" / "screens" / "arch",
]


def build_image_index():
    """이미지 파일명 + 디렉토리 = 텍스트 캡션으로 indexing."""
    import chromadb
    import hashlib
    INDEX_DIR = PROJECT_ROOT / ".claude" / "state" / "chromadb"
    client = chromadb.PersistentClient(path=str(INDEX_DIR))
    coll_name = "image_captions"
    try:
        client.delete_collection(coll_name)
    except Exception:
        pass

    emb_fn = rag._get_embedding_fn()
    coll = client.create_collection(coll_name, embedding_function=emb_fn) if emb_fn else client.create_collection(coll_name)

    ids, docs, metas = [], [], []
    for d in IMG_DIRS:
        if not d.exists(): continue
        for img in d.glob("*.png"):
            # 파일명 기반 캡션 (예: 08-8-models.png → "8 models 8 모델")
            cap = img.stem.replace("-", " ").replace("_", " ")
            # 디렉토리 컨텍스트
            cap_full = f"{cap} ({d.name})"
            cid = hashlib.md5(str(img).encode()).hexdigest()
            ids.append(cid); docs.append(cap_full); metas.append({"path": str(img), "type": "image"})
    if ids:
        coll.add(ids=ids, documents=docs, metadatas=metas)
    return {"indexed_images": len(ids)}


def multimodal_search(query: str, top_n: int = 5) -> dict:
    """이미지 + 텍스트 통합 검색."""
    import chromadb
    INDEX_DIR = PROJECT_ROOT / ".claude" / "state" / "chromadb"
    client = chromadb.PersistentClient(path=str(INDEX_DIR))

    # 텍스트 RAG (기존)
    text_results = rag.search(query, top_n=top_n)

    # 이미지 RAG
    image_results = []
    try:
        emb_fn = rag._get_embedding_fn()
        coll = client.get_collection("image_captions", embedding_function=emb_fn) if emb_fn else client.get_collection("image_captions")
        r = coll.query(query_texts=[query], n_results=top_n)
        for i in range(len(r["ids"][0])):
            image_results.append({
                "path": r["metadatas"][0][i]["path"],
                "caption": r["documents"][0][i],
                "distance": round(r["distances"][0][i], 3) if r["distances"] else None,
            })
    except Exception:
        image_results = [{"error": "image index not built. run: rag-multimodal.py --build"}]

    return {"text": text_results, "images": image_results}


if __name__ == "__main__":
    if "--build" in sys.argv:
        print(json.dumps(build_image_index(), ensure_ascii=False, indent=2))
        sys.exit(0)
    if len(sys.argv) < 2:
        print("usage: rag-multimodal.py '<query>' OR --build"); sys.exit(2)
    print(json.dumps(multimodal_search(sys.argv[1]), ensure_ascii=False, indent=2))
