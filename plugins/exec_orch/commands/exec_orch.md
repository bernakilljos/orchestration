---
description: "멀티AI 오케스트레이션 진입점 (codex+gemini 루프)"
---

# /exec_orch — 오케스트레이션 허브

Claude + Codex + Gemini 멀티AI 파이프라인.

## 포함 커맨드
- `/check-agents` — 워커 가용성 + 실행 중 태스크 확인 (**기본 상태 조회**)
- `/godmode` — 공격적 실행 모드 (질문 최소화)
- `/gemini-verify` — Gemini로 단건 검증
- `/orcauto-stop` — 자동 시작 비활성화 + 워커 종료
- `/loop-stop` — 실행 중 루프 즉시 중단

## 기본 실행
세션 시작 시 `exec_orca-auto` 스킬이 자동으로 워커 띄움 (별도 커맨드 불필요).
추가 태스크 투입은 `orca-dispatch <task_file> [codex|gemini|claude]` (전역 큐) 또는 `.claude/tasks/task-*.md` 작성 (로컬).
