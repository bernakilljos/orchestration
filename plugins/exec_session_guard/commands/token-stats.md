---
description: "세션별 토큰 소비 통계 — 누적 비용·모델별 분포·상위 세션"
allowed-tools: Bash(cat:*), Bash(python:*), Read
---

## Context

- 로그 파일: `.claude/state/token-usage.jsonl`
- 인자: `$ARGUMENTS` (예: `--today`, `--top`, `--month`)

## Your task

`.claude/state/token-usage.jsonl` 읽어서 집계:

### 기본 (인자 없음)
- 이번 달 총 비용 (USD)
- 모델별 분포 (%)
- 평균 세션당 비용
- 누적 토큰 (input/output/cache)

### `--today`
오늘 진행된 모든 세션 + 총합

### `--top`
비용 상위 5개 세션

### `--month YYYY-MM`
특정 월 전체

데이터 없으면 "토큰 추적 로그 없음 — `skill-token-tracker` 참조" 출력.
