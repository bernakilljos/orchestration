---
name: haiku-validator
description: Claude Haiku 4.5 격리 검증 워커. Gemini 대비 2x 빠름·11x 저렴, prompt caching 90% 절감. task-review-*.md 우선, 범용 task-*.md 가능.
---

# Haiku 4.5 Validator Worker

## 개요

Claude Haiku 4.5 를 기본 검증 워커로 사용. 작은 태스크(< 200k tokens), 빠른 응답이 필요할 때 최적.

### 주요 특징

- **속도**: Gemini Flash 대비 ~2배 빠름
- **비용**: Gemini 대비 ~11배 저렴 ($0.0008 vs $0.075 per 1M input tokens)
- **Caching**: 5분 TTL ephemeral prompt caching 지원
  - CLAUDE.md + task context 를 캐시 → 반복 호출 시 입력 비용 90% 절감
- **정확도**: Claude 계열 최고 품질 (Opus/Sonnet 다음)

### 언제 사용

| 상황 | Haiku | Gemini |
|------|:-----:|:------:|
| 일반 코드 검증 |  **기본** | fallback |
| task 크기 < 100k 토큰 |  | X |
| 빠른 응답 필요 |  | X |
| 장문 검증 (500k+) | X |  |
| 이미지/비디오 | X |  |
| 예산 제약 있음 |  | X |

## 사용법

### 1. 워커 시작

```bash
# 설정된 워커 수로 시작 (기본 2개, .claude/orca-workers-config.json 에서 "haiku" 항목)
haiku-auto

# 4개 병렬로 시작
haiku-auto 4

# 단일 모드 (직렬, 테스트용)
haiku-auto 1

# 내부용: 단일 워커 #1 (haiku-auto.bat 에서 호출)
haiku-auto --child 1
```

### 2. 검증 대상 파일

워커가 자동으로 선택하는 순서:

1. **task-review-*.md** — 검증 전용 태스크 (최우선)
2. **task-*.md** — 일반 태스크 (그 다음)

### 3. 결과

검증 완료 후 다음 위치에 저장:

```text
docs/YYYY-MM-DD/
  └─ haiku-review-{task_name}.md
```

예시:

```markdown
# Validation Review

## Verdict
PASS

## Key Findings
- Function implements requirements correctly
- Error handling present for edge cases
- No security concerns detected

## Recommendations
- Consider adding docstring to public functions
- Performance is adequate for use case
```

## 내부 동작

### 1. Task Lock & Selection

- 각 워커는 `.claude/tasks/locks/{task_name}.lock` 파일로 atomic lock 수행
- 30분 이상 stale lock 자동 정리 (워커 crash 대비)
- SQLite 기반 task 상태 추적

### 2. Prompt Caching

```python
system = build_cached_system([
    {"text": "You are a rigorous validator...", "cacheable": True},
    {"text": "# CLAUDE.md\n...", "cacheable": True},
])
```

- CLAUDE.md + 시스템 프롬프트 → 5분 ephemeral cache
- 반복 호출 시 cache hit → 입력 토큰 비용 90% 절감
- 미니 배치 모드 시 누적 절감 > $100/day

### 3. 메트릭 기록

SQLite `.claude/state/orca.db` 에 자동 기록:

```sql
metrics (
  task_id, ai="claude-haiku", model_id="claude-haiku-4-5",
  tokens_in, tokens_out,
  cost_usd, latency_ms, success, cache_hit, error_class
)
```

### 4. Quota 관리

Rate limit (429) 감지 시:

- 1시간 backoff 설정 (`.claude/state/orca.db` quota table)
- 해당 워커 자동 sleep (600초 주기 체크)
- 1시간 경과 후 자동 복구

## 제약

### 모델 한계

- **Context window**: 200k tokens
  - 초과 시: Gemini (1M tokens) 로 fallback
- **Vision**: Haiku는 이미지 분석 불가
  - 이미지 첨부 task 는 Gemini 전용

### 성능

- **Throughput**: 초당 최대 ~30 validators (Haiku quota)
  - 기본 2개면 충분한 대부분의 프로젝트
  - 대규모 배치 시 "codex-auto + haiku-auto" 조합
- **Latency**: 평균 500~1000ms (인터넷 지연 포함)
- **비용**: $0.0008 per 1M input tokens (Gemini 대비 1/100)

## 설정 튜닝

### Workers 개수 조정

`.claude/orca-workers-config.json`:

```json
{
  "workers": {
    "codex": 4,
    "gemini": 2,
    "haiku": 4,        // ← 증가하면 병렬도 증가 (quota 주의)
    "claude": 2,
    "local_llm": 1
  }
}
```

### Quota 복구

수동으로 quota 초과 해제:

```bash
python .claude/scripts/lib/state_db.py -c "clear_quota('claude-haiku')"
```

## 디버깅

### Worker가 뜨지 않음

```bash
# 1. Python 확인
python --version      # 3.8+ 필요

# 2. .claude 폴더 확인
ls -la .claude/       # scripts/, tasks/, state/ 있나?

# 3. anthropic SDK 확인
pip install anthropic

# 4. API 키 확인
echo $ANTHROPIC_API_KEY  # 값이 설정되어 있나?
```

### Task stuck in lock

30분 이상 진행 없으면 자동 정리됨. 수동:

```bash
rm .claude/tasks/locks/task-*.lock
```

### 비용 너무 높음

- Cache hit 확인: `SELECT cache_hit FROM metrics WHERE ai='claude-haiku'`
  - hit rate < 20% → caching 문제. CLAUDE.md 크기 확인 (1024토큰 이상?)
- Haiku 대신 사용: token-heavy 테스크는 처음부터 Gemini 사용

## 참고

- 모델 가격 (최신): `pricing.py` § claude-haiku-4-5
- Prompt caching: `prompt_cache.py`
- Task locking: `state_db.py` § try_lock_task
- Route logic: `route_dispatch.md` (Phase 3에서 Haiku → Gemini 순서 정의)
