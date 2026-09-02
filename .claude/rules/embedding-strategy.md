# 임베딩 전략 룰 (Embedding Strategy)

> **근거**: 2026-09-02 · 축 9 임베딩 강화. chromadb + sentence-transformers 설치 완료. TF fallback 만으로 lookup 성능 약함.
> **이유**: rule·memory·conversations 벡터 검색 필요. 도메인·언어 특화 모델 선택.

## 절대 룰

**의미 검색 = chromadb 우선 · TF fallback 은 chromadb 미설치 시만. 임베딩 모델은 태스크·언어별 매트릭스 선택.**

## 모델 매트릭스

| 태스크 | 모델 | 차원 | 언어 | 라이선스 |
|---|---|---|---|---|
| **한국어 rule·memory 검색 (default)** | `intfloat/multilingual-e5-large` | 1024 | 100+ 다국어 (한국어 우수) | MIT |
| 영어 기술 문서 | `sentence-transformers/all-MiniLM-L6-v2` | 384 | 영어 | Apache 2.0 |
| 코드 임베딩 | `microsoft/codebert-base` | 768 | 코드 (Python·JS·Java 등) | MIT |
| 대용량 처리 (경량) | `sentence-transformers/all-MiniLM-L12-v2` | 384 | 영어 | Apache 2.0 |
| 최신 SOTA (2026) | `BAAI/bge-m3` | 1024 | 100+ · 8192 토큰 | MIT |
| 임베딩 API (외부) | `voyage-multilingual-2` | 1024 | 100+ | 유료 |

## 저장소

| 대상 | 위치 |
|---|---|
| Rule·memory 인덱스 | `.claude/state/rules-index/` (chromadb) |
| Conversations 검색 | `orca.db.conversations` (SQLite FTS) + `.claude/state/conv-index/` (chromadb 옵션) |
| Codebase 임베딩 | `.claude/state/code-index/` (chromadb) |
| claude-mem 자체 벡터 | `~/.claude-mem/chroma` (별도 관리) |

## `lookup-rule.py` 활용

- 기존 코드에 chromadb fallback 이미 있음 (`--rebuild` 로 재구성)
- 신규: `python .claude/scripts/lookup-rule.py --rebuild` 로 chromadb 활성
- 사용자 검색: `python .claude/scripts/lookup-rule.py "검증 후 보고"`
- 자동 rebuild: PostToolUse Edit/Write (rule·memory 변경 감지)

## FTS 병행 (SQLite Full-Text Search)

- `conversations` 테이블에 FTS 인덱스 추가 (예정)
- 벡터 검색 (의미) + FTS (키워드) 병행 = 정확도 상승

## 모델 선택 로직

```python
# lookup-rule.py 확장 (예정)
def pick_model(query: str, corpus_lang: str = "ko") -> str:
    if corpus_lang == "ko" or _has_korean(query):
        return "intfloat/multilingual-e5-large"
    elif _is_code(query):
        return "microsoft/codebert-base"
    else:
        return "sentence-transformers/all-MiniLM-L6-v2"
```

## Retention

- chromadb 인덱스 = rule·memory 변경 시 자동 갱신
- codebase 인덱스 = 주 1회 재구성 (일요일)
- conversations 인덱스 = 30일 초과 압축 시 재구성

## claude-mem 병행

- claude-mem = 자기 Chroma 관리 (`~/.claude-mem/chroma`)
- 우리 = `.claude/state/*-index/` 별개
- 저장소 분리 · 충돌 X

## 금지

1. 매 쿼리마다 embedding 재계산 X (캐시 활용)
2. 대용량 모델 (bge-m3 등) 실시간 로드 X (첫 로드 후 캐시)
3. 외부 API 임베딩 (voyage) 사용자 명시 없이 X (비용·개인정보)
4. chromadb 없이 벡터 검색 요구 X (TF fallback 는 rule·memory 만)

## 관련

- `.claude/scripts/lookup-rule.py` (구현)
- `.claude/rules/mcp-integration.md` (claude-mem)
- `.claude/rules/conversation-history.md` (conversations)
