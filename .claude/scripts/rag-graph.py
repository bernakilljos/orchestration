"""Graph RAG — 엔티티 추출 + 관계 그래프 + 다중 hop 검색.

최소 구현: 정규식 entity extract (Claude/Hash) + co-occurrence 관계.
실제 사용 시 networkx + LLM entity extraction 권장.
"""
import sys
import re
import json
import sqlite3
from pathlib import Path
from collections import defaultdict, Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / ".claude" / "state" / "orca.db"


# 도메인 entity 패턴 (orchestration_v1 컨텍스트)
ENTITY_PATTERNS = [
    r"Claude(?:\s*(?:Opus|Sonnet|Haiku|Code))?(?:\s*\d\.\d)?",
    r"Codex(?:\s*CLI)?",
    r"Gemini(?:\s*Flash)?",
    r"Haiku(?:\s*\d\.\d)?",
    r"MCP",
    r"RAG",
    r"ChromaDB",
    r"orca\.db",
    r"hook[s]?",
    r"plugin[s]?",
    r"skill[s]?",
    r"subagent[s]?",
    r"CLAUDE\.md",
]


def ensure_graph_table(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS graph_edges (
        entity_a TEXT, entity_b TEXT, doc_path TEXT, weight INTEGER DEFAULT 1,
        PRIMARY KEY (entity_a, entity_b, doc_path)
    );
    CREATE INDEX IF NOT EXISTS idx_graph_a ON graph_edges(entity_a);
    CREATE INDEX IF NOT EXISTS idx_graph_b ON graph_edges(entity_b);
    """)


def extract_entities(text: str) -> list:
    entities = set()
    for pat in ENTITY_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            entities.add(m.group().strip())
    return list(entities)


def build_graph():
    """문서들 -> 엔티티 + 관계 (co-occurrence) -> orca.db."""
    conn = sqlite3.connect(str(DB_PATH))
    ensure_graph_table(conn)
    conn.execute("DELETE FROM graph_edges")

    # 모든 .md 문서 스캔
    docs = []
    for d in [PROJECT_ROOT / "CLAUDE.md"]:
        if d.exists(): docs.append((str(d), d.read_text(encoding="utf-8", errors="ignore")))
    for p in (PROJECT_ROOT / ".claude" / "rules").glob("*.md"):
        docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))
    proj_normalized = PROJECT_ROOT.name.replace("_", "-")
    mem_base = Path.home() / ".claude" / "projects"
    if mem_base.exists():
        for sub in mem_base.iterdir():
            if proj_normalized in sub.name and (sub / "memory").exists():
                for p in (sub / "memory").glob("feedback_*.md"):
                    docs.append((str(p), p.read_text(encoding="utf-8", errors="ignore")))

    edges = 0
    for path, content in docs:
        entities = extract_entities(content)
        # 같은 문서 안 co-occurrence
        for i, a in enumerate(entities):
            for b in entities[i + 1:]:
                if a != b:
                    pair = tuple(sorted([a, b]))
                    conn.execute(
                        "INSERT OR IGNORE INTO graph_edges (entity_a, entity_b, doc_path) VALUES (?, ?, ?)",
                        (pair[0], pair[1], path),
                    )
                    edges += 1
    conn.commit()
    conn.close()
    return {"docs": len(docs), "edges": edges}


def graph_search(query: str, top_n: int = 5) -> dict:
    """질문 -> 엔티티 추출 -> 관련 엔티티 hop -> 문서 반환."""
    query_entities = extract_entities(query)
    if not query_entities:
        return {"error": "no entities in query", "supported": [p[:20] for p in ENTITY_PATTERNS]}

    conn = sqlite3.connect(str(DB_PATH))
    related = Counter()
    docs = Counter()
    for ent in query_entities:
        cur = conn.execute(
            "SELECT entity_a, entity_b, doc_path FROM graph_edges WHERE entity_a = ? OR entity_b = ?",
            (ent, ent),
        )
        for a, b, doc in cur.fetchall():
            other = b if a == ent else a
            related[other] += 1
            docs[doc] += 1
    conn.close()

    return {
        "query_entities": query_entities,
        "related_entities": related.most_common(top_n),
        "top_docs": [{"path": d, "weight": w} for d, w in docs.most_common(top_n)],
    }


if __name__ == "__main__":
    if "--build" in sys.argv:
        print(json.dumps(build_graph(), ensure_ascii=False, indent=2))
        sys.exit(0)
    if len(sys.argv) < 2:
        print("usage: rag-graph.py '<query>' OR --build"); sys.exit(2)
    print(json.dumps(graph_search(sys.argv[1]), ensure_ascii=False, indent=2))
