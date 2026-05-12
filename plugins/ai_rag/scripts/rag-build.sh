#!/usr/bin/env bash
# ai_rag plugin — RAG index 빌드 (ChromaDB 기반)
# core 도구: .claude/scripts/rag-recall.py 호출
set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
exec PYTHONIOENCODING=utf-8 python "$PROJECT_ROOT/.claude/scripts/rag-recall.py" --build "$@"
