# exec_learning — 학습·메모리·요약 — 세션 학습·실패 패턴·최적화 규칙 관리

> **Prefix**: `exec_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0

## 📖 개요

세션 실패·성공 패턴을 JSON으로 축적. 다음 세션이 과거 실수 반복하지 않도록.

- **Why**: AI는 세션 간 기억이 없음. 이 플러그인이 영구 학습 역할.
- **When**: 세션 끝날 때 /summarize. 새 작업 시작 시 /recall.

## 📋 커맨드

- `/exec_learning`
- `/learn` ⭐ 기본
- `/recall`
- `/summarize`

## 🧠 스킬

- `skill-09-memory-reset` ⭐ 핵심

## 🤖 에이전트

- `agent-01-team-lead`

## 🪝 훅

- `hook-03-post-review`
- `hook-06-notify`

## 🔗 의존성

- **플러그인**: `exec_orch`
- **MCP**: 해당 없음
- **환경변수**: 해당 없음

## 💡 사용 예시

### 예시 1: 학습 저장
```
/learn  # 현 세션 패턴 추출
```

### 예시 2: 과거 조회
```
/recall "authentication bug"
```

### 예시 3: 세션 요약
```
/summarize
```

## 📝 변경 이력

- 1.0 (2026-04-19) — 현재 버전
