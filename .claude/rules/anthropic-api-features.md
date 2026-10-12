# Anthropic API 신기능 활용 룰

> **DEPRECATION 2026-10-12**: 이 파일 안 **Headroom** / **claude-mem** / **mcp-autostart** / **mcp-integration** 참조는 모두 무시. 완전 삭제됨 (설치만 되고 실제 동작 X · RAM 2.5GB 낭비). Anthropic 네이티브 prompt caching 만 사용.


> **근거**: 2026-10-12 갱신 · Anthropic 2026-07~10 신기능 · 우리 kit 통합.

## 신기능 매트릭스

| 기능 | 적용 | 우리 활용 |
|---|---|---|
| **Haiku 5.5 출시** [NEW 10/7] | `claude-haiku-5-5` · 1M context · 128k 출력 · adaptive thinking (effort) | 검증 라우팅 Haiku 4.5 승격 후보 · Breaking: budget_tokens·temp·top_p·top_k·prefill·computer_20250124 모두 400 error |
| **Sonnet 5.5 cache read 50% 인하** [10/7] | $0.20 → **$0.10** per MTok (base input 0.05x) | Sonnet 5.5 cache 적중 극대화 · Dreams 지원 |
| **Managed Agents Dynamic Workflows** (beta) [10/9] | `multiagent: {type:"multiagent_20261001", workflows:{type:"enabled"}}` + `managed-agents-2026-04-01` header | 수백 문서 리뷰 등 대규모 작업 · workflow_run.* 이벤트 |
| **Browser/Computer use SDK classes** (beta) [10/7] | Python·TS SDK subclass + method per tool | Playwright 보완 · URL/파일 policy·approval callback |
| **web_fetch URL 제한** [10/7 보안] | Managed Agents 가 user.message 에 등장한 URL 만 fetch 허용 | data exfil 방지 · agent 자체 output URL 은 fetch 불가 |
| **limited networking allowed_hosts** [10/7] | web_search·web_fetch 도 `allowed_hosts` 따름 | 엔터프라이즈 geo-fencing 정합 |
| **Models API capabilities.server_tools** [10/6] | `GET /v1/models` 응답에 web_search·code_execution 지원 여부 | 라우팅 전 동적 체크 |
| **Models API thinking.disabled 보고** [10/5] | `capabilities.thinking.types.disabled` | Opus 5.5 는 false (always-on) 재확인 |
| **Max/Team plans API credits** [10/7] | monthly API credits 포함 | 사용자 플랜 비용 재산정 |
| **Opus 5.5 adaptive thinking (always-on)** | `claude-opus-5-5` default effort medium | 설계·복잡추론 default — thinking disable 불가 |
| **On-demand conversation compaction** (9/22) | `/v1/messages/compaction` → signed `compaction` block 재사용 | 긴 세션 자동 압축 · state_session 룰과 정합 |
| **`thinking_mismatch_allowed`** (9/22) | preserved thinking 블록이 history edit 전에 감지 | multi-session·orchestration 안전 |
| **Agent Skills (GA)** (9/22) | GitHub repo `.claude/skills` 자동 discovery + 조직 공유 | 우리 skill-design.md 와 정합 · install 워크플로우 |
| **Commerce agents blueprint** (9/22) | retail·travel·telecom·ticketing reference impl · Messages API·Agent SDK·Managed Agents | Guardrail 패턴 참고 (가격 catalog 제한·upsell 차단) |
| **Mid-conversation inline tools in system messages** (beta, 9/22) | Opus 5.5 only | dynamic tool addition 가능 |
| **Prompt cache 1시간 TTL** | `cache_control: {type: "ephemeral", ttl: "1h"}` | 장기 세션 · 큰 시스템 프롬프트 · Fable 5.1 **cache reads 75% 저렴** |
| **Advisor tool** | `{"type":"advisor"}` in multiagent roster | mid-turn 다른 모델 상담 (Claude → GPT 상담) |
| **Session budgets** | `budget_reached` stop_reason | route.py budget 정합 |
| **Inference geo pinning** | `model.inference_geo` | 개보법·GDPR 대응 |
| **GitHub-hosted skills** | repo `.claude/skills` 자동 discovery | install 워크플로우 |
| **Inference hooks** (Enterprise beta) | 조직 AI security server 로 hold | approval-gate 정면 |
| **Managed Agents webhooks** | `environment.*`·`memory_store.*` | 이벤트 자동 |
| **Files API** | 파일 업로드·재사용 | 대량 문서 감사 |
| **Citations** | 응답 근거 자동 인용 | 감사 신뢰도 |
| **Extended Thinking** (`beta`) | 사고 체인 저장 | Opus 5.5 default (always-on) |

## 실제 사용 예

### Prompt Cache 1h TTL
```python
messages = [
    {"role": "user", "content": [
        {"type": "text", "text": SYSTEM_PROMPT,
         "cache_control": {"type": "ephemeral", "ttl": "1h"}},
        {"type": "text", "text": query}
    ]}
]
```

### Advisor tool (Managed Agents)
```python
tools = [{
    "type": "advisor",
    "name": "gpt5_advisor",
    "description": "복잡 리서치 시 GPT-5 상담",
    "model": "gpt-5"
}]
```

### Files API
```python
file = client.files.create(file=open("big-doc.pdf", "rb"))
messages = [{"role": "user", "content": [
    {"type": "file", "file_id": file.id},
    {"type": "text", "text": "이 문서 요약"}
]}]
```

### Citations
```python
messages = [{"role": "user", "content": [
    {"type": "document", "source": {...}, "citations": {"enabled": True}},
    {"type": "text", "text": "질문"}
]}]
```

## 우리 kit 통합 우선

1. **Prompt cache 1h TTL** — CLAUDE.md 시스템 프롬프트 · 90% 절감 극대화
2. **Files API** — 대량 감사 문서 · 재사용
3. **Citations** — 감사 응답 신뢰도

## 관련

- `.claude/rules/mcp-integration.md`
- `.claude/rules/embedding-strategy.md`
- Anthropic changelog 2026-07~09
- CLAUDE.md § 3.2 (API 신규)
