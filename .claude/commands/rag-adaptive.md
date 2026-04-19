---
description: "Adaptive RAG — Multi-step reasoning chain"
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

**목적**: Adaptive RAG — Multi-step reasoning chain

**실구현은 플랫폼에서**. 상세: `../SPEC.md`
