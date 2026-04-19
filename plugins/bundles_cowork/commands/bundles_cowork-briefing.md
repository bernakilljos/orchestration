---
description: "아침 브리핑 드래프트 (Slack·이메일 요약)"
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

**목적**: 아침 브리핑 드래프트 (Slack·이메일 요약)

실구현은 플랫폼에서. 상세: `../SPEC.md`
