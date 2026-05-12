"""Adaptive RAG — 질문 유형 분류 후 적절한 RAG 분기.

- factual (사실): Naive (빠름)
- complex (복잡): Corrective (자가 검증)
- vague (모호): HyDE (가상 답)
- multi-hop (다중 단계): Agentic 권장 (별도)
"""
import sys
import re
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / ".claude" / "scripts"))
import importlib.util


def classify_question(query: str) -> str:
    if re.search(r"무엇|뭐|어디|언제|누구|얼마|몇\s", query):
        return "factual"
    if re.search(r"어떻게|왜|이유|방법", query) and len(query) > 30:
        return "complex"
    if re.search(r"느낌|적당히|아마|혹시|대충", query) or len(query) < 8:
        return "vague"
    if re.search(r"그리고|또한|먼저.*다음|단계별", query):
        return "multi_hop"
    return "factual"


def adaptive_search(query: str, top_n: int = 5) -> dict:
    q_type = classify_question(query)

    if q_type == "complex":
        spec = importlib.util.spec_from_file_location("rc", PROJECT_ROOT / ".claude" / "scripts" / "rag-corrective.py")
    elif q_type == "vague":
        spec = importlib.util.spec_from_file_location("rh", PROJECT_ROOT / ".claude" / "scripts" / "rag-hyde.py")
    else:
        spec = importlib.util.spec_from_file_location("rg", PROJECT_ROOT / ".claude" / "scripts" / "rag-recall.py")

    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

    if q_type == "complex":
        results = mod.corrective_search(query, top_n)
        return {"type": q_type, "strategy": "Corrective", "results": results.get("combined", [])}
    elif q_type == "vague":
        results = mod.hyde_search(query, top_n)
        return {"type": q_type, "strategy": "HyDE", "results": results.get("results", [])}
    else:
        results = mod.search(query, top_n)
        return {"type": q_type, "strategy": "Naive", "results": results}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: rag-adaptive.py '<query>'"); sys.exit(2)
    print(json.dumps(adaptive_search(sys.argv[1]), ensure_ascii=False, indent=2))
