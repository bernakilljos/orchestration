"""Agentic RAG — 추론 에이전트 + 다중 소스 + 자가 검증.

흐름:
1. Adaptive 분류 + Corrective 검색
2. 결과 score 평가 (distance + 매칭 chunks 수)
3. score 낮으면 → HyDE 추가 검색 (다중 소스)
4. 최종 결과 + confidence 점수
"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / ".claude" / "scripts"))
import importlib.util


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def agentic_search(query: str, top_n: int = 5) -> dict:
    rc = load_module("rc", PROJECT_ROOT / ".claude" / "scripts" / "rag-corrective.py")
    rh = load_module("rh", PROJECT_ROOT / ".claude" / "scripts" / "rag-hyde.py")

    # 1단계: Corrective
    primary = rc.corrective_search(query, top_n)
    avg_distance = 999
    if primary.get("combined"):
        ds = [r.get("distance") for r in primary["combined"] if isinstance(r.get("distance"), (int, float))]
        if ds:
            avg_distance = sum(ds) / len(ds)

    confidence = max(0, 1 - avg_distance)  # 0~1

    # 2단계: 자가 평가 — confidence 낮으면 HyDE 추가
    fallback_used = False
    extra_results = []
    if confidence < 0.5:
        fallback_used = True
        hyde = rh.hyde_search(query, top_n=3)
        extra_results = hyde.get("results", [])

    return {
        "strategy": "Agentic (Corrective + 자가 평가 + HyDE fallback)",
        "primary_count": len(primary.get("combined", [])),
        "avg_distance": round(avg_distance, 3),
        "confidence": round(confidence, 3),
        "fallback_used": fallback_used,
        "primary": primary.get("combined", [])[:top_n],
        "extra": extra_results,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: rag-agentic.py '<query>'"); sys.exit(2)
    print(json.dumps(agentic_search(sys.argv[1]), ensure_ascii=False, indent=2))
