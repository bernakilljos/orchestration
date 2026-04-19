---
description: "로컬 모델 다운로드·실행 (Llama·Gemma·Mistral)"
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

**목적**: 로컬 모델 다운로드·실행 (Llama·Gemma·Mistral)

실구현은 플랫폼에서. 상세: `../SPEC.md`
