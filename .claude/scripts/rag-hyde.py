"""HyDE RAG — Hypothetical Document Embeddings.

가상 답 생성 -> 그 답으로 검색 (질문 자체보다 더 정확).
LLM 없이 query 확장 기반 (Claude API 호출은 별도 통합).
"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / ".claude" / "scripts"))
import importlib.util
spec = importlib.util.spec_from_file_location("rag", PROJECT_ROOT / ".claude" / "scripts" / "rag-recall.py")
rag = importlib.util.module_from_spec(spec); spec.loader.exec_module(rag)


def expand_query(query: str) -> list:
    """질문 -> 가상 답 패턴 (Claude 없이 룰 기반 expand)."""
    hyp = [query]  # 원본 포함
    # 질문 -> 답 형태 변환
    hyp.append(query.replace("?", "").replace("어떻게", "방법은").replace("뭐야", "이것은"))
    hyp.append(f"{query} 답변: 다음과 같은 방법으로 해결")
    hyp.append(f"이 문제는 {query.replace('?', '')} — 해결 방안")
    return list(set(hyp))


def hyde_search(query: str, top_n: int = 5) -> dict:
    hyps = expand_query(query)
    all_results = []
    seen = set()
    for hyp in hyps:
        results = rag.search(hyp, top_n=2)
        for r in results:
            key = (r.get("path"), r.get("chunk"))
            if key not in seen:
                seen.add(key)
                all_results.append({**r, "via_hyp": hyp[:50]})
    # distance 작은 순
    all_results.sort(key=lambda x: x.get("distance", 999) if isinstance(x.get("distance"), (int, float)) else 999)
    return {"hypotheses_used": len(hyps), "results": all_results[:top_n]}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: rag-hyde.py '<query>'"); sys.exit(2)
    print(json.dumps(hyde_search(sys.argv[1]), ensure_ascii=False, indent=2))
