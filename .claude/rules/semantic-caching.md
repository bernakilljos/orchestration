# Semantic Caching 룰 (Task 37)

> **근거**: 2026-09-02 · 유사 프롬프트 재사용 · 원가 절감.

## 절대 룰

**유사 프롬프트 (임베딩 유사도 ≥ 0.92) = 캐시 응답 재사용. 원가 0.**

## 아키텍처

```text
[사용자 프롬프트] → 임베딩 (sentence-transformers)
     ↓
[Chroma vector DB] 최근 30일 프롬프트·응답 저장
     ↓
[유사도 검색] top-1 · cosine ≥ 0.92 → 캐시 hit
     │                          → 미만 → LLM 호출
     ↓
[캐시 hit 시] 즉시 응답 + 로그 (원가 $0)
```

## 저장소

- Vector DB: `.claude/state/semantic-cache/` (Chroma)
- 모델: `intfloat/multilingual-e5-large` (한국어 · 이미 설치)
- Retention: 30일

## 유사도 threshold

| 유사도 | 처리 |
|---|---|
| ≥ 0.98 | 완전 동일 · 캐시 즉시 응답 |
| 0.92~0.97 | 유사 · 캐시 참고 + LLM 재확인 (선택) |
| 0.80~0.91 | 부분 유사 · 참고만 (systemMessage 힌트) |
| < 0.80 | 새 프롬프트 · LLM 호출 |

## 활성 시나리오

| 시나리오 | 활성? |
|---|---|
| 사용자가 같은 질문 반복 | ✅ 즉시 캐시 |
| 프롬프트 재작성 (유사) | ✅ 힌트 |
| 새 문제 | ❌ LLM 호출 |
| 시크릿·개인정보 포함 | ❌ 캐시 skip (안전) |

## Anthropic Prompt Caching 병행

- Anthropic native prompt caching = 반복 컨텍스트 (system·history) 90% 절감
- Semantic caching = 반복 프롬프트 (user query) 재사용
- **둘 다 활용 시 극한 절감**

## 사용 예

```python
from .claude.scripts.lib import semantic_cache

response = semantic_cache.get_or_generate(
    prompt="개인정보 처리방침 자동 생성",
    threshold=0.92,
    llm_call=lambda: anthropic.messages.create(...)
)
# hit 시 즉시 캐시 · miss 시 LLM 호출 + 저장
```

## 금지

1. 개인정보·시크릿 포함 프롬프트 캐시 X
2. 최신 정보 (오늘 뉴스·주가) 캐시 X (stale)
3. 실시간 시스템 상태 조회 캐시 X
4. threshold < 0.80 자동 재사용 X (품질 저하)

## 관련

- `.claude/rules/embedding-strategy.md` (Chroma·모델)
- `.claude/rules/auto-optimization.md` (캐시 축)
- `.claude/scripts/lib/semantic_cache.py` (예정)
