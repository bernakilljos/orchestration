# exec_session_guard — 세션 가드 — 토큰 부족·강제 종료 대비 자동 스냅샷 저장

> **Prefix**: `exec_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0
> **Precedence**: 3 | **Token estimate**: ~1600

## 📖 개요

토큰 소진·세션 종료 대비 자동 스냅샷.

## 📋 커맨드

- `/exec_session_guard`
- `/guard-save` ⭐ 기본
- `/token-stats`

## 🧠 스킬

- `guard_snapshot` ⭐ 핵심
- `skill-token-tracker`

## 🪝 훅

- `cleanup-orphans.sh` (script)
- `hook-token-log.sh` (script)
- `stop-snapshot.sh` (script)

## 🔗 의존성

- **플러그인**: `exec_orch`

## 💡 사용 예시

### 예시 1: 즉시 스냅샷
```bash
/guard-save
```

### 예시 2: 토큰 통계
```bash
/token-stats --today
```

### 예시 3: 자동 동작
```bash
# Stop·PreCompact·SessionEnd 훅이 자동 저장
```

## 📝 참조

- 스펙: `plugin.json`
- 공유 규칙: `.claude/rules/`
- 아키텍처: `docs/architecture-patterns.md`
