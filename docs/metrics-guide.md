# Metrics Guide — Multi-AI Orchestration v1

> **목적**: metrics.db 기반 비용·성능·신뢰성 관측 및 튜닝
> **대상**: 운영자 (비용 모니터링, 워커 튜닝)
> **Phase**: 1 (메트릭 기록 + 대시보드), Phase 2 (router-agent 가 메트릭 기반 라우팅), Phase 3 (watchdog 가 budget breaker 감시)

---

## 1. 메트릭 시스템 개요

### 테이블 스키마

```
metrics (id, task_id, ai, model_id, tokens_in, tokens_out, cost_usd, 
         latency_ms, success, cache_hit, retry, recorded_at, error_class)
```

- **ai**: `claude-opus`, `claude-haiku`, `codex`, `gemini`
- **model_id**: 정확한 모델 이름 (`claude-opus-4-7`, `gemini-2-0-flash` 등)
- **tokens_in/out**: 입출력 토큰 수 (캐시 토큰 별도)
- **cost_usd**: 이 호출의 USD 비용
- **latency_ms**: 응답 시간 (밀리초)
- **success**: 1=성공, 0=실패
- **cache_hit**: 캐시 히트 여부
- **error_class**: 오류 분류 (`timeout`, `quota`, `validation` 등)

---

## 2. 메트릭 기록

### 2.1 워커에서 기록 (Codex/Gemini)

각 워커가 작업 완료 후 자동 기록:

```bash
# codex-auto.bat 내부
python record_call.py --ai codex --model codex \
    --tokens-in 1000 --tokens-out 0 \
    --latency-ms 2500 --success 1 \
    --task-id task-42
```

### 2.2 Python 에서 직접 기록

```python
from record_call import record_api_call

cost = record_api_call(
    ai="claude-opus",
    model="claude-opus-4-7",
    tokens_in=1500,
    tokens_out=750,
    latency_ms=2340,
    success=True,
    task_id="task-001"
)
# cost = $0.02345 (반환)
```

### 2.3 캐시 토큰 포함

```python
# Prompt cache hit 토큰 추적
record_api_call(
    ai="claude-opus",
    model="claude-opus-4-7",
    tokens_in=5000,
    tokens_out=200,
    cache_hit_tokens=4000,  # 캐시에서 로드
    cache_write_tokens=0,
    ...
)
```

### 2.4 오류 분류

```python
record_api_call(
    ...,
    success=False,
    error_class="timeout"  # quota, validation, network, etc.
)
```

---

## 3. 메트릭 조회

### 3.1 CLI 리포트

```bash
# 지난 24시간
python .claude/scripts/metrics-report.py

# 지난 72시간
python .claude/scripts/metrics-report.py --hours 72

# Claude만
python .claude/scripts/metrics-report.py --ai claude-opus
```

**출력 예시:**

```
─────────────────────────────────────────────────────────────
AI             calls  success%   tokens (in/out)   cost      avg_latency
─────────────────────────────────────────────────────────────
claude-opus    42     95.2%      120k / 45k        $8.12     2340ms
claude-haiku   89     98.9%      50k / 18k         $0.89     340ms
codex          12     83.3%      30k / 12k         $1.45     4200ms
gemini          8     100.0%     80k / 5k          $0.04     890ms
─────────────────────────────────────────────────────────────
Cache hit rate: 87.2%
Errors last 24h:
  timeout       3
  quota         1
```

### 3.2 대시보드 웹 인터페이스

```
http://localhost:8787
```

메인 페이지 상단에 메트릭 요약 표시:
- 시간대별 AI 호출 통계
- 누적 비용
- 캐시 히트율
- 오류 분포

자동 갱신: 30초마다

### 3.3 API 엔드포인트

```bash
# JSON 형식
curl http://localhost:8787/api/metrics?hours=24

# 응답:
{
  "claude-opus": {
    "count": 42,
    "success_rate": 0.952,
    "tokens_in": 120000,
    "tokens_out": 45000,
    "total_cost_usd": 8.12,
    "avg_latency_ms": 2340,
    "cache_hits": 36
  },
  ...
}
```

### 3.4 SQLite 직접 쿼리

```bash
# AI별 비용 합계
sqlite3 .claude/state/orca.db \
  "SELECT ai, COUNT(*) as calls, SUM(cost_usd) as total_cost, AVG(latency_ms) as avg_latency 
   FROM metrics WHERE recorded_at >= datetime('now','-24 hours') 
   GROUP BY ai ORDER BY total_cost DESC"

# 오류 분류
sqlite3 .claude/state/orca.db \
  "SELECT error_class, COUNT(*) as count FROM metrics 
   WHERE success = 0 AND recorded_at >= datetime('now','-24 hours') 
   GROUP BY error_class ORDER BY count DESC"

# 최근 10개 실패
sqlite3 .claude/state/orca.db \
  "SELECT recorded_at, ai, model_id, error_class 
   FROM metrics WHERE success = 0 
   ORDER BY recorded_at DESC LIMIT 10"
```

---

## 4. 비용 관측

### 4.1 예산 설정 (Phase 2)

```python
# .claude/state/orca.db 의 budget 테이블
# UPDATE budget SET daily_limit_usd = 100 WHERE id = 1;
```

- **daily_limit_usd**: 하루 지출 한계
- **today_spent_usd**: 오늘 누적 지출 (자동 갱신)
- **breaker_tripped**: 한계 초과 시 1 (모든 워커 중단)

### 4.2 비용 드라이버

| AI | 1M 토큰당 비용 | 샘플 크기 |
|---|---|---|
| Claude Opus | $15 / $75 | 큼 (종합 판단) |
| Claude Haiku | $0.80 / $4 | 작음 (검증) |
| Codex | ~$1/출력 | 중간 (구현) |
| Gemini | ~$0.08 / $0.32 | 중간 (보조 검증) |

### 4.3 최적화 포인트

| 포인트 | 액션 | 예상 절감 |
|---|---|---|
| **캐시 재사용** | Prompt cache hit > 80% | 90% 토큰 비용 |
| **모델 선택** | Haiku 검증 → Opus 설계만 | 80% 비용 |
| **배치 실행** | 배치 API (Phase 2+) | 50% 비용 |
| **조기 종료** | 실패 패턴 감지 시 중단 | 30% 비용 |

---

## 5. 성능 관측

### 5.1 응답 시간 분포

```bash
# 워커별 평균 지연
sqlite3 .claude/state/orca.db \
  "SELECT ai, COUNT(*) as calls, 
           AVG(latency_ms) as avg_latency, 
           MAX(latency_ms) as max_latency
   FROM metrics WHERE recorded_at >= datetime('now','-24 hours')
   GROUP BY ai ORDER BY avg_latency"
```

**해석:**
- Claude: 2000-3000ms (설계·판단)
- Codex: 3000-5000ms (구현, 더 김)
- Gemini: 500-1500ms (경량 검증)

### 5.2 지연 이상 감지

```python
# metrics-report.py 에서 자동 경고
# latency_ms > 10000 → 느린 호출
# latency_ms < 100 → 캐시 히트 (정상)
```

---

## 6. 신뢰성 관측

### 6.1 성공률 임계치

| AI | 목표 | 경고 | 심각 |
|---|---|---|---|
| Claude | 95%+ | <95% | <85% |
| Codex | 90%+ | <90% | <80% |
| Gemini | 95%+ | <95% | <85% |

### 6.2 오류 패턴

```bash
# 시간대별 오류 분포
sqlite3 .claude/state/orca.db \
  "SELECT strftime('%H', datetime(recorded_at, 'unixepoch')) as hour, 
           error_class, COUNT(*) as count
   FROM metrics WHERE success = 0
   GROUP BY hour, error_class
   ORDER BY hour, count DESC"
```

**흔한 오류:**
- `quota`: API 한도 초과 (30분 재시도)
- `timeout`: 응답 지연 (retry_count 증가)
- `validation`: 입력/출력 검증 실패 (로직 수정)
- `network`: 네트워크 오류 (재시도)

---

## 7. 메트릭 아카이브 및 정리

### 7.1 장기 보관 정책

```bash
# 30일 이상 된 메트릭 내보내기 (선택사항)
sqlite3 .claude/state/orca.db \
  "SELECT * FROM metrics 
   WHERE recorded_at < datetime('now','-30 days')" \
  | tee docs/metrics-archive-$(date +%Y-%m-%d).csv

# 테이블 크기 제한 (선택사항: 1년분만 유지)
DELETE FROM metrics 
WHERE recorded_at < datetime('now','-365 days');
```

### 7.2 자동 정리 (Phase 2)

```python
# .claude/hooks/cleanup-old-metrics.sh
# 일주일마다 자동 실행
# 1년 초과 메트릭 삭제
```

---

## 8. 트러블슈팅

### Q: metrics-report.py 실행 실패
- **A**: `.claude/state/orca.db` 초기화
  ```bash
  python .claude/scripts/lib/state_db.py  # init_schema() 호출
  ```

### Q: 메트릭이 기록되지 않음
- **A**: record_call.py 반환값 확인
  ```bash
  python record_call.py --ai claude --model claude-opus --tokens-in 100 --tokens-out 50 --latency-ms 1000 --success 1
  # "Recorded: claude/claude-opus in=100 out=50 cost=$0.000015" 출력되어야 함
  ```

### Q: 대시보드 메트릭 표시 안 됨
- **A**: 브라우저 콘솔 열기 (F12)
  - `/api/metrics` 응답 확인
  - 네트워크 탭에서 status 200 확인

### Q: 비용이 너무 높음
- **A**:
  1. 모델별 토큰 비용 확인 (`record_call.py` pricing_map)
  2. 캐시 히트율 확인 (목표: >80%)
  3. 모델 선택 재검토 (Haiku vs Opus)

---

## 9. Phase 2~3 연결 포인트

### Phase 2: Router Agent

Router가 메트릭 기반 의사결정:

```python
# Phase 2 router-agent (미래)
if metrics["codex"]["success_rate"] < 0.8:
    # Codex 신뢰도 낮음 → Claude로 폴백
    dispatch_to("claude-opus")
elif metrics["gemini"]["avg_latency_ms"] < 1000:
    # Gemini 빠름 → 경량 검증용으로 우선
    dispatch_to("gemini")
```

### Phase 3: Watchdog

Watchdog이 budget breaker 감시:

```bash
# Phase 3 watchdog (미래)
# budget.breaker_tripped = 1 감지 시
# - 모든 워커 신호 (SIGTERM)
# - 대시보드에 ⚠ 빨간 배너 표시
# - escalation task 생성
```

---

## 10. 참조

- `record_call.py` — API 호출 기록 헬퍼
- `metrics-report.py` — CLI 리포트 도구
- `test-metrics.py` — 메트릭 시스템 테스트
- `state_db.py` — SQLite 상태 관리
- CLAUDE.md § Budget management — 예산 정책
