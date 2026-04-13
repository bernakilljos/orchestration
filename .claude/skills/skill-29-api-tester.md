# Skill 29: API Tester

## 목적
API 엔드포인트를 자동으로 테스트한다. Postman/Insomnia 대체.
gemini 검증 시 실제 API를 호출해서 동작 확인.

## 트리거
- "API 테스트", "api test", "엔드포인트 확인"
- gemini-auto 검증 시 자동 호출
- 배포 후 health check

## 실행 흐름

### 1. API 목록 자동 수집
```
소스 코드에서 라우트 추출:
  Flask:   @app.route('/api/...')
  Express: router.get('/api/...')
  Spring:  @GetMapping("/api/...")
  FastAPI: @app.get("/api/...")
```

### 2. 테스트 실행
```
각 엔드포인트에 대해:
  1. GET → 200 OK 확인
  2. POST → 필수 파라미터 테스트
  3. 잘못된 입력 → 4xx 에러 확인
  4. 인증 필요 → 401 확인
  5. 응답 시간 측정 (3초 초과 경고)
```

### 3. 결과 리포트
```
API Test Results: 15/18 passed (83%)

✅ GET  /api/health         200  45ms
✅ GET  /api/users          200  120ms
✅ POST /api/auth/login     200  230ms
❌ POST /api/data/upload    500  timeout
⚠️ GET  /api/reports        200  3200ms (slow)
```

## 출력
- `docs/YYYY-MM-DD/api-test-result.md`
- 콘솔: 통과/실패 요약

## MCP 연동
- **playwright MCP**: 브라우저 기반 API 테스트
- **WebSearch / WebFetch**: API 프레임워크 문서 참조 (내장, MCP 불필요) / context7 MCP 설치 시 추가 활용
