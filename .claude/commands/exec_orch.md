---
description: "exec_orch — 멀티AI 오케스트레이션 진입점 (codex+gemini 루프)"
---

# /exec_orch — 오케스트레이션 허브

Claude + Codex + Gemini 멀티AI 파이프라인.

## 포함 커맨드
- `/vibe-loop` — codex-auto + gemini-auto 멀티 루프 시작 (**기본 액션**)
- `/check-agents` — 워커 가용성 + 실행 중 태스크 확인
- `/godmode` — 공격적 실행 모드 (질문 최소화)
- `/gemini-verify` — Gemini로 단건 검증
- `/orcauto-stop` — 자동 시작 비활성화 + 워커 종료
- `/loop-stop` — 실행 중 루프 즉시 중단

## 기본 실행
`/vibe-loop` 을 실행해 파이프라인 시작. 옵션을 보려면 위 목록 중 골라서 직접 호출.
