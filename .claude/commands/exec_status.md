---
description: "오케스트레이션 통합 상태 — 워커·큐·heartbeat·sync 한 번에"
allowed-tools: Bash(bash:*)
---

## Context

- Orca 상태: !`bash .claude/scripts/orca-status.sh`

## Your task

`/check-agents` 가 워커 리스트 중심이라면, `/status` 는 **통합 대시보드**:
- 로컬 + 전역 태스크 큐
- 워커 heartbeat (활성/지연/휴면 구분)
- 워커 상한 설정
- 마지막 sync 시각 + 파일 카운트

이상 징후 (heartbeat 5분 초과, 큐 적체, sync 오래됨) 자동 하이라이트.
