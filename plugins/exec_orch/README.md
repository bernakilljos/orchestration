# exec_orch — 오케스트레이션 — 워커·파이프라인·라우팅·AI 역할 분배

> **Prefix**: `exec_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0
> **Precedence**: 1 | **Token estimate**: ~3600

## 📖 개요

Claude + Codex + Gemini 멀티AI 파이프라인 코어 엔진.

## 📋 커맨드

- `/check-agents` ⭐ 기본
- `/exec_orch`
- `/gemini-verify`
- `/godmode`
- `/help`
- `/loop-stop`
- `/orcauto-stop`
- `/status`

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

- `hook-00-init` (spec)
- `hook-01-pre-task` (spec)
- `hook-04-pre-deploy` (spec)
- `hook-05-post-deploy` (spec)
- `hook-06-notify` (spec)
- `hook-08-ai-handoff` (spec)
- `memory_guard.sh` (script)
- `protect-critical-files.sh` (script)

## 🔗 의존성

- **플러그인**: 없음 (코어)

## 💡 사용 예시

### 예시 1: 현재 워커 상태
```bash
/check-agents
```

### 예시 2: 통합 대시보드
```bash
/status  # 워커·큐·heartbeat·sync
```

### 예시 3: 공격적 실행
```bash
/godmode  # 질문 최소화·최대 워커
```

### 예시 4: 한도 복구
```bash
bash plugins/exec_orch/scripts/codex-quota-check.sh --clear
```

## 📝 참조

- 스펙: `plugin.json`
- 공유 규칙: `.claude/rules/`
- 아키텍처: `docs/architecture-patterns.md`
