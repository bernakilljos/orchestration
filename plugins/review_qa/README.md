# review_qa — 코드 리뷰·보안 검사·품질 검증·테스트 자동화

> **Prefix**: `review_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0

## 📖 개요

코드 리뷰·보안·품질·테스트 검증 허브.

- **Why**: 배포 전 필수 게이트. CI 통합 가능.
- **When**: PR 리뷰, 배포 전, 주기 보안 감사.

## 📋 커맨드

- `/check` ⭐ 기본
- `/performance`
- `/review_qa`
- `/screenshot`
- `/security`
- `/validate`

## 🧠 스킬

- `skill-03-review` ⭐ 핵심
- `skill-06-test` ⭐ 핵심
- `skill-10-quality-verify` ⭐ 핵심
- `skill-17-debugging-canvas`
- `skill-23-owasp-security`
- `skill-27-mandatory-verify`
- `skill-35-performance-profiler`
- `skill-37-error-tracker`

## 🤖 에이전트

- `agent-03-reviewer`
- `agent-04-architect`

## 🪝 훅

- `hook-02-post-impl`
- `hook-03-post-review`
- `post-impl-verify.sh`

## 🔗 의존성

- **플러그인**: `exec_orch`
- **MCP**: 해당 없음
- **환경변수**: 해당 없음

## 💡 사용 예시

### 예시 1: 종합 체크
```
/check
```

### 예시 2: 보안 감사
```
/security
```

### 예시 3: 성능 검사
```
/performance
```

### 예시 4: 스크린샷 검증
```
/screenshot url
```

## 📝 변경 이력

- 1.0 (2026-04-19) — 현재 버전
