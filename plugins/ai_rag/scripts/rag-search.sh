#!/usr/bin/env bash
# ai_rag plugin — RAG 의미 검색 (ChromaDB query)
set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
exec PYTHONIOENCODING=utf-8 python "$PROJECT_ROOT/.claude/scripts/rag-recall.py" "$@"
