# exec_session_guard — 세션 가드 — 토큰 부족·강제 종료 대비 자동 스냅샷 저장

> **Prefix**: `exec_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0

## 📖 개요

토큰 소진·세션 강제 종료 대비 스냅샷 자동 저장.

- **Why**: 긴 세션이 갑자기 날아가는 사고 방지. Stop/PreCompact/SessionEnd 훅 자동 작동.
- **When**: 자동 (훅). 수동은 /guard-save.

## 📋 커맨드

- `/exec_session_guard`
- `/guard-save` ⭐ 기본

## 🧠 스킬

- `guard_snapshot` ⭐ 핵심

## 🪝 훅

- `cleanup-orphans.sh`
- `stop-snapshot.sh`

## 🔗 의존성

- **플러그인**: `exec_orch`
- **MCP**: 해당 없음
- **환경변수**: 해당 없음

## 💡 사용 예시

### 예시 1: 즉시 스냅샷
```
/guard-save  # 토큰 여유 있을 때 방어적 저장
```

### 예시 2: 자동 복구
```
# 다음 세션 시작 시 session-snapshot.md 복구 제안
```

## 📝 변경 이력

- 1.0 (2026-04-19) — 현재 버전
