---
description: "영수증 스캔·회계 JSON·세금 분류 (mcp_docs·OCR)"
allowed-tools: Bash(bash:*), Write, Read
---

## Context
- 플러그인: `bundles_cowork` (spec-only)
- 출처: https://www.instagram.com/p/DW9GwvhFCu5/ (@aifornontechies 'Claude Cowork Essentials')

## Your task
```bash
source plugins/bundles_cowork/scripts/common.sh
load_env
is_dry_run "$@" && log_info "dry-run"
```

**목적**: 영수증 스캔·회계 JSON·세금 분류 (mcp_docs·OCR)

실구현은 플랫폼에서. 상세: `../SPEC.md`
