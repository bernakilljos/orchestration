# Anthropic API 신기능 활용 룰

> **근거**: 2026-09-02 · Anthropic 2026-07~09 신기능 · 우리 kit 통합.

## 신기능 매트릭스

| 기능 | 적용 | 우리 활용 |
|---|---|---|
| **Prompt cache 1시간 TTL** | `cache_control: {type: "ephemeral", ttl: "1h"}` | 장기 세션 · 큰 시스템 프롬프트 |
| **Advisor tool** | `{"type":"advisor"}` in multiagent roster | mid-turn 다른 모델 상담 (Claude → GPT 상담) |
| **Session budgets** | `budget_reached` stop_reason | route.py budget 정합 |
| **Inference geo pinning** | `model.inference_geo` | 개보법·GDPR 대응 |
| **GitHub-hosted skills** | repo `.claude/skills` 자동 discovery | install 워크플로우 |
| **Inference hooks** (Enterprise beta) | 조직 AI security server 로 hold | approval-gate 정면 |
| **Managed Agents webhooks** | `environment.*`·`memory_store.*` | 이벤트 자동 |
| **Files API** | 파일 업로드·재사용 | 대량 문서 감사 |
| **Citations** | 응답 근거 자동 인용 | 감사 신뢰도 |
| **Extended Thinking** (`beta`) | 사고 체인 저장 | Opus 5 default |

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
