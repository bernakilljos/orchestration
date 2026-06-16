---
description: GPT-5.2 호출 — 초장기 컨텍스트 recall (2M+) (Perplexity Computer 패턴)
allowed-tools: Bash(python:*), Bash(curl:*), Read, Write
---

# /gpt-dispatch — GPT-5.2 API 호출 wrapper

> **근거**: `docs/2026-06-16/tooling-comparison.md` § ⭐⭐ Perplexity Computer 패턴.
> **사용**: **2M+ 토큰** 초장기 문서 recall·전체 codebase 분석 (Gemini Flash 의 1M 부족 시).
> **요구**: `OPENAI_API_KEY` (.env)

## 사용

```bash
/gpt-dispatch <task-instruction-path>
/gpt-dispatch --context <file1> <file2> <file3> "<prompt>"
```

## 동작

```bash
# 1. 게이트 확인
python .claude/scripts/route.py --check gpt-5.2

# 2. 환경변수 확인
[ -z "$OPENAI_API_KEY" ] && echo "[FAIL] OPENAI_API_KEY 미설정" && exit 1

# 3. token estimate (2M 제한 사전 검증)
python .claude/scripts/lib/token_count.py <files> --max 2000000

# 4. API 호출 (OpenAI 공식 endpoint)
curl -s https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.2",
    "messages": [...],
    "max_tokens": 16384
  }'

# 5. 결과 → .claude/tasks/done/<slug>-gpt52.md
```

## 라우팅 매트릭스 (CLAUDE.md § 3.2)

| 적합 | 부적합 |
|---|---|
| **2M+ 토큰** 초장기 recall | <500k (Sonnet/Haiku) |
| 전체 codebase 통합 분석 | 단순 implementation (Codex) |
| 멀티 파일 cross-reference | 설계·결정 (Opus 4.8) |
| Gemini 1M 부족 case | 멀티모달 (Gemini Flash 가 vision 강함) |

## 비용 (2026-06 기준)

- GPT-5.2: $10/$30 per MTok (참고 — 2M context 사용 시 입력 비용 큼)
- 2M token 입력 = $20 단발 — **cost critical 알림 임계 ($5+) 초과 — 사용자 사전 승인 필수**

## 폴링·재시도

- 120초 timeout (2M 처리)
- 429/503 → 지수 backoff
- context 초과 → 자동 분할 + sequential 호출 + merge

## 참조

- [OpenAI Platform — GPT-5.2](https://platform.openai.com/docs/models/gpt-5-2)
- CLAUDE.md § 3.2 라우팅 표 — GPT-5.2 행
- CLAUDE.md § 7-11 cost critical 알림
- `.claude/scripts/route.py --check gpt-5.2`
