# Skill 35: Performance Profiler

## 목적
런타임 성능을 분석하고 느린 API/쿼리/렌더링을 찾아낸다.

## 트리거
- "성능 분석", "profiler", "느린 API", "bottleneck"
- skill-10 quality-verify에서 성능 이슈 감지 시

## 실행 흐름

### 1. Backend 프로파일링
```
Python:
  - cProfile / py-spy → 함수별 실행 시간
  - Django Debug Toolbar → SQL 쿼리 분석
  - SQLAlchemy echo=True → 쿼리 로깅

Node.js:
  - clinic.js → 이벤트 루프/GC 분석
  - autocannon → HTTP 벤치마크

Java:
  - Spring Actuator → /metrics 엔드포인트
  - JFR (Java Flight Recorder) → 프로파일
```

### 2. Frontend 프로파일링
```
- Lighthouse CLI → Performance/Accessibility 점수
- Bundle Analyzer → 번들 크기 분석
- Core Web Vitals → LCP/FID/CLS 측정
```

### 3. DB 쿼리 분석
```
- EXPLAIN ANALYZE → 실행 계획
- 슬로우 쿼리 감지 (100ms+ 경고, 1s+ 에러)
- N+1 쿼리 패턴 탐지
- 인덱스 미사용 쿼리 감지
```

### 4. 리포트
```
Performance Report:

[API Response Time]
   GET  /api/users     45ms
   GET  /api/reports   1200ms  → 캐싱 권장
   POST /api/export    8500ms  → 비동기 처리 필요

[DB Queries]
   평균 쿼리 시간: 12ms
   N+1 감지: UserRepository.findAll() → 50 추가 쿼리
   인덱스 없음: orders.created_at

[Frontend]
  Lighthouse: 72/100
  LCP: 2.8s ( > 2.5s)
  Bundle: 1.2MB ( > 500KB)
```

## 출력
- `docs/YYYY-MM-DD/performance-report.md`
- 최적화 제안 코드 포함
