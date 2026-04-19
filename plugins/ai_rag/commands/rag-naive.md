---
description: "Naive RAG — Query→Embed→VectorDB→Prompt→LLM (가장 단순·빠름)"
allowed-tools: Bash(bash:*), Write, Read
---

## Context
- 플러그인: `ai_rag` (spec-only)

## Your task
```bash
source plugins/ai_rag/scripts/common.sh
load_env
is_dry_run "$@" && log_info "dry-run"
```

**목적**: Naive RAG — Query→Embed→VectorDB→Prompt→LLM (가장 단순·빠름)

**실구현은 플랫폼에서**. 상세: `../SPEC.md`
