"""Multimodal RAG ???대?吏 + ?띿뒪???듯빀 寃??

理쒖냼 援ы쁽: ?대?吏 罹≪뀡 + filename ?띿뒪??indexing.
?ㅼ젣 ?ъ슜 ??CLIP/BLIP 媛숈? ?대?吏 embedding 紐⑤뜽 沅뚯옣.
"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / ".claude" / "scripts"))

import importlib.util
spec = importlib.util.spec_from_file_location("rag", PROJECT_ROOT / ".claude" / "scripts" / "rag-recall.py")
rag = importlib.util.module_from_spec(spec); spec.loader.exec_module(rag)

# ?대?吏 ?붾젆?좊━
IMG_DIRS = [
    PROJECT_ROOT / "docs" / "screens" / "arch-kor",
    PROJECT_ROOT / "docs" / "screens" / "arch",
]


def build_image_index():
    """?대?吏 ?뚯씪紐?+ ?붾젆?좊━ = ?띿뒪??罹≪뀡?쇰줈 indexing."""
    import chromadb
    import hashlib
    INDEX_DIR = PROJECT_ROOT / ".claude" / "state" / "chromadb"
    client = chromadb.PersistentClient(path=str(INDEX_DIR))
    coll_name = "image_captions"
    try:
        client.delete_collection(coll_name)
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        pass

    emb_fn = rag._get_embedding_fn()
    coll = client.create_collection(coll_name, embedding_function=emb_fn) if emb_fn else client.create_collection(coll_name)

    ids, docs, metas = [], [], []
    for d in IMG_DIRS:
        if not d.exists(): continue
        for img in d.glob("*.png"):
            # ?뚯씪紐?湲곕컲 罹≪뀡 (?? 08-8-models.png -> "8 models 8 紐⑤뜽")
            cap = img.stem.replace("-", " ").replace("_", " ")
            # ?붾젆?좊━ 而⑦뀓?ㅽ듃
            cap_full = f"{cap} ({d.name})"
            cid = hashlib.md5(str(img).encode()).hexdigest()
            ids.append(cid); docs.append(cap_full); metas.append({"path": str(img), "type": "image"})
    if ids:
        coll.add(ids=ids, documents=docs, metadatas=metas)
    return {"indexed_images": len(ids)}


def multimodal_search(query: str, top_n: int = 5) -> dict:
    """?대?吏 + ?띿뒪???듯빀 寃??"""
    import chromadb
    INDEX_DIR = PROJECT_ROOT / ".claude" / "state" / "chromadb"
    client = chromadb.PersistentClient(path=str(INDEX_DIR))

    # ?띿뒪??RAG (湲곗〈)
    text_results = rag.search(query, top_n=top_n)

    # ?대?吏 RAG
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
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        image_results = [{"error": "image index not built. run: rag-multimodal.py --build"}]

    return {"text": text_results, "images": image_results}


if __name__ == "__main__":
    if "--build" in sys.argv:
        print(json.dumps(build_image_index(), ensure_ascii=False, indent=2))
        sys.exit(0)
    if len(sys.argv) < 2:
        print("usage: rag-multimodal.py '<query>' OR --build"); sys.exit(2)
    print(json.dumps(multimodal_search(sys.argv[1]), ensure_ascii=False, indent=2))

