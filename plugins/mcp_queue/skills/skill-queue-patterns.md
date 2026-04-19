# skill-queue-patterns

> **분류**: `mcp_` | **Status**: spec-only

## Purpose

큐 패턴 (fan-out·pub-sub·work-queue·DLQ)

## When to invoke

- 관련 커맨드 호출 시 자동 활성화
- 사용자가 관련 주제 언급 시

## Procedure (개요)

1. 컨텍스트 수집 (`common.sh` 헬퍼)
2. 도메인 로직 (플랫폼 구현)
3. 결과 검증 + 로깅

상세: `../SPEC.md`
