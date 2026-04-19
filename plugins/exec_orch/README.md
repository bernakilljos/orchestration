# exec_orch — 오케스트레이션 — 워커·파이프라인·라우팅·AI 역할 분배

> **Prefix**: `exec_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0

## 📖 개요

Claude + Codex + Gemini 멀티AI 파이프라인 코어 엔진. 설계→구현→검증 루프 자동화.

- **Why**: 단일 AI 한계 극복. 설계는 Claude, 코드는 Codex 4대, 검증은 Gemini 2대 병렬.
- **When**: 세션 시작 시 자동 (exec_orca-auto). 수동 진입은 /exec_orch.

## 📋 커맨드

- `/check-agents` ⭐ 기본
- `/exec_orch`
- `/gemini-verify`
- `/godmode`
- `/loop-stop`
- `/orcauto-stop`

## 🧠 스킬

- `exec_orca-auto` ⭐ 핵심
- `route_dispatch` ⭐ 핵심
- `skill-03-review`
- `state_session` ⭐ 핵심

## 🤖 에이전트

- `agent-01-team-lead`
- `agent-02-implementer`
- `agent-03-reviewer`
- `agent-04-architect`
- `agent-05-monitor`
- `agent-06-designer`

## 🪝 훅

- `hook-00-init`
- `hook-01-pre-task`
- `hook-04-pre-deploy`
- `hook-05-post-deploy`
- `hook-06-notify`
- `hook-08-ai-handoff`
- `memory_guard.sh`
- `protect-critical-files.sh`

## 🔗 의존성

- **플러그인**: 없음 (코어)
- **MCP**: 해당 없음
- **환경변수**: 해당 없음

## 💡 사용 예시

### 예시 1: 기본 상태 조회
```
/check-agents  # 워커 + 실행 중 태스크
```

### 예시 2: 공격적 실행
```
/godmode  # 질문 최소화 · 최대 워커
```

### 예시 3: Gemini 검증
```
/gemini-verify target.md
```

## 📝 변경 이력

- 1.0 (2026-04-19) — 현재 버전
