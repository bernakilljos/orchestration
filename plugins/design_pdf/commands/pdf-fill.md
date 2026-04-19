---
description: "양식(form) 자동 채우기"
allowed-tools: Bash(bash:*), Write, Read
---

## Context

- 플러그인: `design_pdf` (status=spec-only)
- 출력: `data/design_pdf/$(date +%Y-%m-%d)/`
- DRY_RUN 환경변수: `${DRY_RUN:-false}`

## Your task

### 기본 공통 (모든 커맨드 공유)

```bash
source plugins/design_pdf/scripts/common.sh
load_env

if is_dry_run "$@"; then
  log_info "dry-run 모드"
fi
```

### 커맨드별 로직

**목적**: 양식(form) 자동 채우기

**단계**:
1. 입력 검증 (필수 인자·환경변수)
2. 드라이런 분기 (미리보기)
3. 실제 작업 (플랫폼 구현)
4. 결과 JSON 로깅

**실구현은 플랫폼에서** — 상세: `../SPEC.md`
