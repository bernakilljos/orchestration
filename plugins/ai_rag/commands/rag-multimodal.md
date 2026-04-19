---
description: "Multimodal RAG — 이미지·텍스트 동시 검색"
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

**목적**: Multimodal RAG — 이미지·텍스트 동시 검색

**실구현은 플랫폼에서**. 상세: `../SPEC.md`
