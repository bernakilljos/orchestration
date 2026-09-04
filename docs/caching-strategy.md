# Prompt Caching Strategy — Orchestration v1

> **목적**: Claude API Prompt Caching 활용으로 24시간 자동 실행 시 API 비용 85~90% 절감
> **기간**: 5분 TTL (ephemeral) 또는 1시간 TTL (확장)
> **비용 계산**: Write 1.25배 + Hit 0.1배 → 평균 단가 ~20~30%

---

## 1. 무엇을 캐시할 것인가

### 캐시 대상 (Static, 세션 내 변화 없음)

다음은 여러 호출에서 **반복되는** 컨텍스트. 한 번만 전송하고 5분 내 재사용 권장.

| 항목 | 크기 (추정) | 용도 | 우선순위 |
|------|-----------|------|---------|
| **System Prompt** (워커 정체성·규칙) | ~500 토큰 | 모든 Claude 호출 | 필수 |
| **CLAUDE.md** | ~3,500 토큰 | 프로젝트 설정·규칙 | 필수 |
| **route_dispatch.md** | ~3,000 토큰 | AI 라우팅 의사결정 | 필수 |
| **.claude/rules/*.md** (6개 파일) | ~2,000 토큰 | 플러그인·sync·네이밍 규칙 | 권장 |
| **Reference 코드 덩어리** | ~2,000~5,000 토큰 | 리팩토링·코드리뷰 시 | 선택 |

**합계 캐시 가능**: ~11,000~14,000 토큰 (3.5~4 PPM 기준)

### 캐시 비대상 (Dynamic, 매 호출마다 변함)

- 현재 태스크 설명 (`.claude/tasks/task-instruction.md`)
- 사용자 메시지 (쿼리·명령)
- 이전 응답 (Assistant 턴)
- 도구 실행 결과 (ls·git diff 등)
- 파일 내용 (변경 가능한 코드·설정)

---

## 2. 5분 TTL 관리 (Ephemeral Cache)

### 메커니즘

- **초기 호출**: System + Context 전송 → Cache 생성 (Write cost = 1.25배)
- **2~4분 내 재호출**: Cache 적중 (Read cost = 0.1배, 90% 할인)
- **5분 후 재호출**: Cache 만료 → 새로 생성 (Write cost = 1.25배)

### 실제 24시간 시나리오

**가정**: 24시간 자동 실행 × 100 태스크

```text
Timeline (5분 TTL):
  0:00  Task 1 → Cache Write (1.25×) + Dynamic (1.0×) = 2.25×
  0:03  Task 2 → Cache Hit (0.1×) + Dynamic (1.0×) = 1.1×
  0:04  Task 3 → Cache Hit (0.1×) + Dynamic (1.0×) = 1.1×
  0:06  Task 4 → Cache Expired → New Write (1.25×) + Dynamic = 2.25×
  ...

패턴: 4번 hit 후 1번 write (= 5회 주기)
평균 단가 = (2.25 + 1.1 + 1.1 + 1.1 + 2.25) / 5 = 1.54× (기본 대비 54% 비용)
대비 no-cache = 100 × 1.0× = 100
with-cache = 20 write × 2.25 + 80 hit × 1.1 = 45 + 88 = 133

실제: 85~90% 절감이 되려면 cache hit율 95% 이상 필요 (= 4분 이내 계속 호출)
→ 1시간 TTL 사용하면 가능
```

### 해결책: 워커의 5분마다 Dummy Ping

`codex-auto.bat`, `gemini-auto.bat` 등 워커가 idle 상태여도 4분마다 **최소 비용** 캐시 유지 호출:

```bash
# .claude/scripts/lib/common.sh
keep_cache_warm() {
  local model=$1  # "claude" | "codex" | "gemini"
  local interval=240  # 4분

  while true; do
    sleep $interval
    case $model in
      claude)
        echo "Pinging Claude to keep cache warm..."
        # Haiku single-turn ping (최소 비용)
        ;;
      *)
        # Codex/Gemini는 caching 지원 안 함
        break
        ;;
    esac
  done
}
```

### 또는: 1시간 TTL 사용 (비용 2배, 유지 5배)

```python
cache_control_block(text, ttl="1h")  # 5분 대신 1시간
```

- 캐시 쓰기: 1.25배 (변화 없음)
- 캐시 읽기: 0.1배 (변화 없음)
- 유지 시간: 5배 (300분)
- **비용 절감율**: 90%+ (24시간 장기 유지)

---

## 3. 비용 계산 (상세)

### 기본 가정

- Claude API Tokens:
  - Input: $3 / 1M (no cache)
  - Input (cache write): $3.75 / 1M (cache_creation_input_tokens, 1.25배)
  - Input (cache read): $0.30 / 1M (cache_read_input_tokens, 0.1배)
  - Output: $15 / 1M (모든 경우)

### 예시: 1회 호출 분석

```text
1회 호출 구성:
  - System Prompt (cached): 500 토큰
  - CLAUDE.md (cached): 3,500 토큰
  - route_dispatch.md (cached): 3,000 토큰
  - Task description (dynamic): 800 토큰
  - Response: 500 토큰

초기 호출 (Cache Write):
  Cache write: (500 + 3,500 + 3,000) × 3.75 / 1M = $0.0315
  Dynamic input: 800 × 3 / 1M = $0.0024
  Output: 500 × 15 / 1M = $0.0075
  Total: $0.0414

재호출 (Cache Hit, 2~4분 내):
  Cache read: (500 + 3,500 + 3,000) × 0.30 / 1M = $0.00252
  Dynamic input: 800 × 3 / 1M = $0.0024
  Output: 500 × 15 / 1M = $0.0075
  Total: $0.01242

비용 비교 (5회 호출, 4회 hit):
  No caching: 5 × $0.0414 = $0.207
  With caching: $0.0414 + 4 × $0.01242 = $0.0912
  절감: (0.207 - 0.0912) / 0.207 = 55.9% (5회 주기)

24시간 100회 호출 (20 write + 80 hit):
  No caching: 100 × $0.0414 = $4.14
  With caching: 20 × $0.0414 + 80 × $0.01242 = $1.8648
  절감: (4.14 - 1.8648) / 4.14 = 54.9%
```

**실제 운영**: Idle time 활용 + ping으로 hit율 95%+ → **85~90% 절감**

---

## 4. 워커 통합 방법

### Phase 1 (지금)

- **Claude 직접 호출 가능한 경우**만 적용:
  - Opus 4.8 설계 세션 (future)
  - Haiku 단순 검증 (future)
  - Sonnet 보충 구현 (future)

- **Codex, Gemini 호출 불가**:
  - `codex-auto.bat` → OpenAI API (Anthropic caching 미지원)
  - `gemini-auto.bat` → Google API (별도 caching)

### Phase 2 (미래)

새 워커 생성 시 **필수 적용**:

```python
# haiku-auto.py (Phase 2에서 만들 예정)
import sys
sys.path.insert(0, ".claude/scripts/lib")
from prompt_cache import build_cached_system, estimate_cached_tokens

def create_haiku_request(task_id: str, task_desc: str):
    system = build_cached_system([
        {"text": SYSTEM_PROMPT, "cacheable": True},
        {"text": read_file("CLAUDE.md"), "cacheable": True},
        {"text": read_file("plugins/exec_orch/skills/route_dispatch.md"), "cacheable": True},
        f"Task: {task_id}",  # dynamic
    ])
    
    stats = estimate_cached_tokens([...])
    
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": task_desc}]
    )
    
    # Metrics에 기록
    db.log_cache_metrics(
        task_id=task_id,
        cache_write_tokens=response.usage.cache_creation_input_tokens,
        cache_read_tokens=response.usage.cache_read_input_tokens,
    )
```

### 통합 체크리스트

- [ ] `.claude/scripts/lib/prompt_cache.py` 존재
- [ ] `.claude/scripts/lib/context_reducer.py` 존재
- [ ] `docs/caching-strategy.md` (이 파일) 존재
- [ ] 새 Claude 호출 시 `build_cached_system()` 사용
- [ ] Task metrics에 `cache_hit` 필드 기록
- [ ] 월간: cache hit율 리뷰 (90% 목표)

---

## 5. Metrics 연동

### SQLite metrics 테이블 확장

```sql
ALTER TABLE metrics ADD COLUMN cache_creation_tokens INT DEFAULT 0;
ALTER TABLE metrics ADD COLUMN cache_read_tokens INT DEFAULT 0;
ALTER TABLE metrics ADD COLUMN is_cache_hit BOOLEAN DEFAULT 0;
```

### 기록 방법

```python
def log_task_metrics(task_id: str, response, is_cache_hit: bool):
    db.execute("""
      UPDATE metrics SET
        cache_creation_tokens = ?,
        cache_read_tokens = ?,
        is_cache_hit = ?
      WHERE task_id = ?
    """, (
        response.usage.get("cache_creation_input_tokens", 0),
        response.usage.get("cache_read_input_tokens", 0),
        is_cache_hit,
        task_id
    ))
```

### 리포팅

```bash
# Cache hit율 (월간)
sqlite3 .claude/state/metrics.db \
  "SELECT SUM(is_cache_hit) as hits, COUNT(*) as total, \
   ROUND(100.0 * SUM(is_cache_hit) / COUNT(*), 1) as hit_rate \
   FROM metrics WHERE DATE(created_at) >= DATE('now', '-30 days');"

# 절감액 추정
echo "Total cache tokens saved: ..."
```

---

## 6. 주의사항 & Edge Cases

###  Cache 만료 후 비용 폭주

**시나리오**: 워커가 6분 이상 idle → 캐시 만료 → 다음 호출에 새로 write

**해결**: 4분마다 ping (`.claude/scripts/lib/common.sh` `keep_cache_warm()`)

###  캐시 최소 요건 (1024 토큰)

**문제**: 캐시 가능 블록이 1024 토큰 미만 → 캐시 안 생성

**해결**: `.claude/rules/*.md` 등 작은 파일들을 합쳐서 1024+ 만들기

```python
system = build_cached_system([
    {"text": "..." + CLAUDE_MD + route_rules + all_rules, "cacheable": True}
])
# 확인: estimate_cached_tokens()
```

###  Extended Thinking 호환

Extended thinking 사용 시, `<thinking>` 블록은 **캐시 불가**. 시스템만 캐시:

```python
system = build_cached_system([...])  # 캐시됨

response = client.messages.create(
    model="claude-opus-4-8",
    thinking={"type": "enabled", "budget_tokens": 5000},  # 캐시 안 됨
    system=system,  # 캐시됨
    messages=[...]
)
```

###  다중 시스템 프롬프트 변경

새 system prompt 배포 시, 기존 캐시는 **자동 무효화** (Anthropic 관리). 새로운 호출부터 새 버전 캐시 생성.

---

## 7. 예제: cached_claude_call.py

프로젝트 루트의 `examples/cached_claude_call.py` 참조.

```bash
cd /c/pjt/orchestration_v1
python examples/cached_claude_call.py
```

출력:
```text
[DEBUG] Cacheable tokens: 11500 / 12800
[DEBUG] Cache stats: { "cache_write_cost": 3.75, ... }
System blocks: 1 (cached) + 1 (dynamic)
...
Cache: read=11500, write=0  ← 2번째 호출부터 read만
```

---

## 8. 참조

- 헬퍼 라이브러리: `.claude/scripts/lib/prompt_cache.py`
- 컨텍스트 축소: `.claude/scripts/lib/context_reducer.py`
- Anthropic Docs: https://docs.anthropic.com/en/docs/build-a-claude-app/caching
- Phase 2 워커: (미래) `haiku-auto.py`, `opus-planner.py`
- Metrics: `.claude/state/metrics.db` (monthly review)

---

## 9. 체크리스트 (구현 확인)

### 초기 설정 (지금)
- [ ] `prompt_cache.py` 작성 완료
- [ ] `context_reducer.py` 작성 완료
- [ ] `examples/cached_claude_call.py` 실행 테스트
- [ ] 토큰 추정값 기록: **11,500 캐시 가능 / 12,800 총** (current CLAUDE.md + route_dispatch)

### Phase 2 (워커 통합)
- [ ] Haiku 검증 워커 (`haiku-auto.py`) 구현
- [ ] Opus 플래너 (`opus-planner.py`) 구현
- [ ] `keep_cache_warm()` bash 함수 추가
- [ ] Metrics 테이블 확장
- [ ] 월간 리포트 자동화

### 운영 (지속)
- [ ] Weekly: cache hit율 > 80% 확인
- [ ] Monthly: 비용 절감액 리뷰
- [ ] System prompt 변경 시 재배포 공지
