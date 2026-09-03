"""Corrective RAG — 검색 결과 자가 검증 + 부족 시 재검색.

흐름:
1. Naive RAG 검색
2. 결과 distance 평가 (0.7 이상 = 약함)
3. 약하면 query 재작성 -> 재검색
4. 약함 결과 + 강함 결과 합쳐 반환
"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / ".claude" / "scripts"))

import importlib.util
spec = importlib.util.spec_from_file_location("rag", PROJECT_ROOT / ".claude" / "scripts" / "rag-recall.py")
rag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rag)


def corrective_search(query: str, top_n: int = 5, threshold: float = 0.7) -> dict:
    """1차 검색 -> 약하면 query 변형 후 2차 검색."""
    primary = rag.search(query, top_n)
    weak_count = sum(1 for r in primary if isinstance(r.get("distance"), (int, float)) and r["distance"] > threshold)

    fallback_used = False
    fallback = []
    if weak_count >= top_n // 2:  # 절반 이상 약함
        # query 변형 (간단 — 키워드 확장)
        variants = [
            query.replace("어떻게", "방법"),
            query.replace("?", "").strip() + " 예시",
            " ".join(query.split()[:3]),  # 짧게
        ]
        for v in variants:
            if v == query:
                continue
            r = rag.search(v, top_n=2)
            fallback.extend(r)
            if r:
                fallback_used = True
                break

    return {
        "primary": primary,
        "weak_count": weak_count,
        "fallback_used": fallback_used,
        "fallback": fallback,
        "combined": primary + fallback,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: rag-corrective.py '<query>'")
        sys.exit(2)
    result = corrective_search(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
