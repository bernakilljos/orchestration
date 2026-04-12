# Skill 37: Error Tracker

## 목적
프로젝트의 에러를 수집, 분류, 분석한다. Sentry/Bugsnag 대체.
반복 에러 패턴을 감지하고 자동 수정 제안.

## 트리거
- "에러 추적", "error tracker", "버그 분석", "에러 패턴"
- 서버 로그에서 에러 감지 시
- codex/gemini 실행 중 에러 발생 시

## 실행 흐름

### 1. 에러 수집
```
소스:
  - 서버 로그 (stdout/stderr)
  - git log (실패한 커밋)
  - 테스트 결과 (pytest/jest 실패)
  - API 응답 (4xx/5xx)
  - codex-auto/gemini-auto 실행 로그
```

### 2. 에러 분류
```
[문법 에러]     SyntaxError, IndentationError
[타입 에러]     TypeError, AttributeError
[임포트 에러]   ImportError, ModuleNotFoundError
[런타임 에러]   ValueError, KeyError, IndexError
[네트워크]      ConnectionError, TimeoutError
[DB]            OperationalError, IntegrityError
[인코딩]        UnicodeDecodeError, UTF-16 감지
[보호 파일]     config.py/settings.json 변경 감지
```

### 3. 패턴 분석
```
[반복 에러 감지]
  - 같은 파일에서 3회+ 에러 → 근본 원인 분석 필요
  - 같은 타입 에러 반복 → 코딩 패턴 문제

[시간대 분석]
  - codex 실행 후 에러 급증 → codex 결과물 문제
  - 배포 후 에러 급증 → 롤백 권장

[연관 분석]
  - 파일 A 수정 → 파일 B에서 에러 → 의존성 문제
```

### 4. 자동 수정 제안
```
각 에러에 대해:
  1. 원인 분석 (스택 트레이스 파싱)
  2. 수정 코드 제안 (diff 형식)
  3. 유사 에러 해결 사례 참조 (.claude/learning/)
  4. 재발 방지 테스트 코드 제안
```

### 5. 에러 대시보드
```
Error Summary (Last 24h):
  Total: 12 errors
  Fixed: 8 (67%)
  Open:  4

  [CRITICAL] api.py:552 SyntaxError — codex가 인코딩 깨뜨림
  [HIGH]     config.py deleted — codex가 삭제
  [MEDIUM]   timeout on /api/reports — 슬로우 쿼리
  [LOW]      deprecation warning — numpy 버전
```

## .claude/learning 연동
```
에러 패턴 + 해결법을 learning에 저장:
  failure-patterns.json: 에러 타입별 빈도
  optimization-rules.json: 해결법 + 예방법
→ 같은 에러 재발 시 자동으로 해결법 제안
```

## 출력
- `docs/YYYY-MM-DD/error-report.md`
- `.claude/learning/failure-patterns.json` 업데이트
- 수정 코드 제안 (diff)
