---
description: "슬라이드 빌드 (design_ppt 연계)"
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

**목적**: 슬라이드 빌드 (design_ppt 연계)

실구현은 플랫폼에서. 상세: `../SPEC.md`
