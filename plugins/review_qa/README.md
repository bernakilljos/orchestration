# review_qa — 코드 리뷰·보안 검사·품질 검증·테스트 자동화

> **Prefix**: `review_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0
> **Precedence**: 5 | **Token estimate**: ~5200

## 📖 개요

코드 리뷰·보안·품질·테스트 검증 허브.

## 📋 커맨드

- `/check`  기본
- `/performance`
- `/review_qa`
- `/screenshot`
- `/security`
- `/validate`

## 🧠 스킬

- `skill-03-review`  핵심
- `skill-06-test`  핵심
- `skill-10-quality-verify`  핵심
- `skill-17-debugging-canvas`
- `skill-23-owasp-security`
- `skill-27-mandatory-verify`
- `skill-35-performance-profiler`
- `skill-37-error-tracker`

## 🤖 에이전트

- `agent-03-reviewer`
- `agent-04-architect`

## 🪝 훅

- `hook-02-post-impl` (spec)
- `hook-03-post-review` (spec)
- `post-impl-verify.sh` (script)

## 🔗 의존성

- **플러그인**: `exec_orch`

## 💡 사용 예시

### 예시 1: 종합 체크
```bash
/check
```

### 예시 2: 보안 감사
```bash
/security
```

### 예시 3: 성능 검사
```bash
/performance
```

### 예시 4: UI 스크린샷
```bash
/screenshot https://example.com
```

### 예시 5: 요구사항 검증
```bash
/validate
```

## 📝 참조

- 스펙: `plugin.json`
- 공유 규칙: `.claude/rules/`
- 아키텍처: `docs/architecture-patterns.md`
