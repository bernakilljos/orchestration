---
description: "작업 설명 입력 → 최적 AI 아키텍처 추천 (LLM/VLM/SLM/MoE 등)"
allowed-tools: Bash(bash:*), Write, Read
---

## Context
- 플러그인: `ai_arch` (spec-only)

## Your task
```bash
source plugins/ai_arch/scripts/common.sh
load_env
is_dry_run "$@" && log_info "dry-run"
```

**목적**: 작업 설명 입력 → 최적 AI 아키텍처 추천 (LLM/VLM/SLM/MoE 등)

**실구현은 플랫폼에서**. 상세: `../SPEC.md`
