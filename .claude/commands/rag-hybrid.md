---
description: "Hybrid RAG — Vector + Graph DB 동시"
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

**목적**: Hybrid RAG — Vector + Graph DB 동시

**실구현은 플랫폼에서**. 상세: `../SPEC.md`
