---
description: "2개 이상 아키텍처 비교표 (정확도·비용·레이턴시)"
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

**목적**: 2개 이상 아키텍처 비교표 (정확도·비용·레이턴시)

**실구현은 플랫폼에서**. 상세: `../SPEC.md`
