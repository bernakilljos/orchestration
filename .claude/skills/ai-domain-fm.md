---
name: ai-domain-fm
description: Domain Foundation Models·AI Search Engines·Ambient Intelligence 통합. 회계·법무·금융 특화 LLM, Perplexity·SearchGPT 사내 활용, IoT + Digital Twin Ambient Intelligence. 사용자가 "Domain FM", "특화 LLM", "AI Search", "Perplexity", "Ambient Intelligence" 같은 키워드를 말할 때 활성화.
metadata:
  author: orchestration_v1
  version: 1.0.0
  category: domain-ai
---

# Domain·Search·Ambient Bundle

## 50 기술 매핑

| # | 기술 | 핵심 |
|---|---|---|
| 48 | Domain Foundation Models | Med-PaLM·Harvey·BloombergGPT |
| 49 | AI Search Engines | Perplexity·SearchGPT·You.com |
| 50 | Ambient Invisible Intelligence | 통합 표준 형성 중 (Gartner 2027) |

## Domain FM — 회계 특화 LLM 자체 개발

```python
# LoRA fine-tuning 으로 ITCEN 내부회계 도메인 LLM
# (자체 학습 = M, 라이브러리 통합 = O)

from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM

base_model = AutoModelForCausalLM.from_pretrained('Llama-3-70B')
lora_config = LoraConfig(r=8, lora_alpha=16, target_modules=['q_proj', 'v_proj'])
model = get_peft_model(base_model, lora_config)

# ITCEN 내부회계 데이터 (익명화)
model.train(accounting_corpus, epochs=3)
# 결과: 한국 회계 특화 sLLM
```

→ 사업화: 한국 BloombergGPT, 한국 Harvey 후보. ITCEN CORE 내부회계 1위 데이터 자산 활용.

## AI Search Engines — 사내 활용

**Perplexity Enterprise** 라이선스:
- 사내 위험 정보 자율 검색
- 컴플라이언스 자동 조사 (규제 변경 추적)
- 경쟁사 분석·시장 정보

```python
# Perplexity API 사용
import requests

response = requests.post(
    'https://api.perplexity.ai/chat/completions',
    headers={'Authorization': f'Bearer {API_KEY}'},
    json={
        'model': 'sonar-pro',
        'messages': [{'role': 'user', 'content': '금감원 AI 거버넌스 2026 최신 가이드'}]
    }
)
# 실시간 웹 검색 + LLM 통합
```

## Ambient Invisible Intelligence (Gartner 2027)

**컨셉**: 저비용 IoT + 디지털 트윈 + 실시간 추적·센싱. **눈에 안 보이는 AI**.

**ITCEN CORE 자산 결합**:
- 디지털트윈 (이미 보유) + 저비용 IoT 센서 + ML
- 건설현장 안전·산업 모니터링·스마트 시티
- 통합 패키지 = K-Ambient Intelligence 표준 후보

## 적용 매트릭스

| 시나리오 | 활용 기술 |
|---|---|
| ITCEN 내부회계 LLM | Domain FM (LoRA fine-tune) |
| 카지노 도메인 LLM | Domain FM (게임 규칙·부정 패턴) |
| 사내 위험정보 자율 검색 | Perplexity Enterprise |
| 컴플라이언스 자율 조사 | AI Search (규제 변경 자동) |
| 산업 안전 IoT + 디지털트윈 | Ambient Intelligence |
| 스마트 빌딩 (ITCEN ENTEC 협업) | Ambient Intelligence |

## Step-by-Step

| Phase | 작업 |
|---|---|
| 1 | Perplexity Enterprise 라이선스 (즉시 사용) |
| 2 | 내부회계 도메인 LLM PoC (LoRA, Llama-3 base) |
| 3 | Ambient — 저비용 IoT 패키지 PoC |
| 4 | 한국 K-Domain 표준 등록 |

## 트리거
- "Domain Foundation Model", "특화 LLM"
- "Perplexity", "AI Search"
- "Ambient Intelligence"

## 참조
- Perplexity Enterprise
- BloombergGPT 논문
- Harvey AI (법무)
- `solution-capability-audit.md` #48-50 ( → )
