---
description: Grok 호출 — 가벼운·빠른 응답·대량 처리 (Perplexity Computer 패턴)
allowed-tools: Bash(python:*), Bash(curl:*), Read, Write
---

# /grok-dispatch — Grok API 호출 wrapper

> **근거**: `docs/2026-06-16/tooling-comparison.md` §  Perplexity Computer 패턴.
> **사용**: 가벼운·빠른·대량 task (검증·summarize·번역). 비싼 Opus 4.8 절감.
> **요구**: `XAI_API_KEY` (.env)

## 사용

```bash
/grok-dispatch <task-instruction-path>
# 또는
/grok-dispatch "<inline prompt>"
```

## 동작

```bash
# 1. 게이트 확인 (quota + budget)
python .claude/scripts/route.py --check grok
# exit 0 = OK / exit 1 = 차단

# 2. 환경변수 확인
[ -z "$XAI_API_KEY" ] && echo "[FAIL] XAI_API_KEY 미설정" && exit 1

# 3. API 호출 (xAI 공식 endpoint)
curl -s https://api.x.ai/v1/chat/completions \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "grok-2-latest",
    "messages": [{"role": "user", "content": "<prompt>"}],
    "max_tokens": 4096
  }'

# 4. 결과 → .claude/tasks/done/<slug>-grok.md
# 5. post-codex-verify 패턴 적용 (pre/post snapshot, hallucination 검증)
```

## 라우팅 매트릭스 (CLAUDE.md § 3.2)

| 적합 | 부적합 |
|---|---|
| 단순 요약·번역 | 설계·아키텍처 (Opus) |
| 대량 검증 (>10 batch) | 보안·money·DB (Self-consistency Haiku ×2) |
| 비용 sensitive 작업 | 1M+ 컨텍스트 (Gemini Flash) |
| 빠른 응답 우선 | 멀티모달·vision (Fable 5 또는 Opus 4.8) |

## 비용 (2026-06 기준)

- Grok-2: $5/$15 per MTok (참고 — 변경 가능)
- Anthropic 대비 저렴, OpenAI 와 유사 가격대

## 폴링·재시도

- 60초 timeout
- 429/503 → 지수 backoff (10s/30s/60s/2m)
- 5xx 3회 연속 → quota_exceeded 표시 후 fallback (Sonnet 4.6)

## 참조

- [xAI API docs](https://docs.x.ai/) — model list, pricing, rate limits
- CLAUDE.md § 3.2 라우팅 표 — Grok 행
- `plugins/exec_orch/skills/route_dispatch.md`
- `.claude/scripts/route.py --check grok`
- `.env.example` § 확장 AI
