# exec_learning — 학습·메모리·요약 — 세션 학습·실패 패턴·최적화 규칙 관리

> **Prefix**: `exec_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0
> **Precedence**: 5 | **Token estimate**: ~1300

## 📖 개요

세션 실패·성공 패턴을 JSON 에 축적.

## 📋 커맨드

- `/exec_learning`
- `/learn`  기본
- `/recall`
- `/summarize`

## 🧠 스킬

- `skill-09-memory-reset`  핵심

## 🤖 에이전트

- `agent-01-team-lead`

## 🪝 훅

- `hook-03-post-review` (spec)
- `hook-06-notify` (spec)
- `hook-worker-failure.sh` (script)

## 🔗 의존성

- **플러그인**: `exec_orch`

## 💡 사용 예시

### 예시 1: 현 세션 학습 저장
```bash
/learn
```

### 예시 2: 과거 패턴 검색
```bash
/recall authentication
```

### 예시 3: 세션 요약 생성
```bash
/summarize
```

## 📝 참조

- 스펙: `plugin.json`
- 공유 규칙: `.claude/rules/`
- 아키텍처: `docs/architecture-patterns.md`
