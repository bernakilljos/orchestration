---
description: "API vs 로컬 라우팅 결정 (비용·품질)"
allowed-tools: Bash(bash:*), Write, Read
---

## Context
- 플러그인: `exec_offline` (spec-only)
- 출처: docs/upgrade § 이미지 3 ($0 AI Stack 2026, Brij Kishore Pandey)

## Your task
```bash
source plugins/exec_offline/scripts/common.sh
load_env
is_dry_run "$@" && log_info "dry-run"
```

**목적**: API vs 로컬 라우팅 결정 (비용·품질)

실구현은 플랫폼에서. 상세: `../SPEC.md`
