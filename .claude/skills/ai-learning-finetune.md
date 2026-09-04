---
name: ai-learning-finetune
description: MoE·SSM·DPO·RLHF·LoRA/QLoRA 학습 패러다임 통합. 자체 도메인 sLLM 저비용 학습, RLHF 대체로 DPO 적용, Mamba SSM 으로 긴 컨텍스트 효율. 사용자가 "MoE", "Mamba", "State Space Models", "DPO", "RLHF", "LoRA", "fine-tuning" 같은 키워드를 말할 때 활성화.
metadata:
  author: orchestration_v1
  version: 1.0.0
  category: learning
---

# Learning Paradigm Bundle

## 50 기술 매핑

| # | 기술 | 핵심 |
|---|---|---|
| 10 | Mixture of Experts (MoE) | DeepSeek V3·Llama 4·Mixtral |
| 11 | State Space Models | Mamba·Jamba·Striped Hyena |
| 12 | Test-Time Training | o1·o3·Claude Extended Thinking |
| 39 | DPO | Stanford·Anthropic·Meta |
| 40 | RLHF | OpenAI·Anthropic·DeepMind |
| 42 | LoRA / QLoRA | Microsoft·Hugging Face |

## 저비용 fine-tuning — LoRA

```bash
pip install peft transformers bitsandbytes
```

```python
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

# QLoRA — 4-bit quantization + LoRA = 메모리 1/4
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype='bfloat16')
base = AutoModelForCausalLM.from_pretrained('Llama-3-8B', quantization_config=bnb)
lora = LoraConfig(r=8, lora_alpha=16, target_modules=['q_proj', 'v_proj'])
model = get_peft_model(base, lora)

# 도메인 데이터 학습 (소액 GPU 로도 가능)
model.train(domain_data, epochs=3)
# 결과: 부서·산업 특화 sLLM (수십~수백만원 GPU 비용)
```

## DPO (RLHF 대체) — 학습 비용 1/10

```python
from trl import DPOTrainer

# 인간 피드백 대신 preference pair 만 필요
dpo_trainer = DPOTrainer(
    model=model,
    ref_model=base,
    train_dataset=preference_data,  # [{'prompt', 'chosen', 'rejected'}]
    beta=0.1
)
dpo_trainer.train()
```

→ 부서: 위험 판단 모델 정교화 — 전문가 선호 답 (chosen) vs 잘못된 답 (rejected) 쌍 모아 DPO.

## MoE — Mixtral 활용 (자체 학습 X, API)

```python
# Mistral API — Mixtral 8x7B
import requests

response = requests.post(
    'https://api.mistral.ai/v1/chat/completions',
    headers={'Authorization': f'Bearer {MISTRAL_KEY}'},
    json={
        'model': 'open-mixtral-8x7b',
        'messages': [{'role': 'user', 'content': prompt}]
    }
)
```

## SSM (Mamba) — 긴 컨텍스트

```bash
pip install mamba-ssm
```

```python
from mamba_ssm import Mamba

# Transformer 대체. 긴 행동 시퀀스 효율 처리
model = Mamba(d_model=256, d_state=16, d_conv=4, expand=2)
# 1년치 행동 로그 (1M+ 토큰) 효율적 학습
```

## ITCEN CORE 활용

| 시나리오 | 패러다임 |
|---|---|
| 내부회계 도메인 sLLM | LoRA fine-tune (Llama-3 base) |
| 카지노 도메인 LLM | QLoRA (저비용) |
| 위험 판단 모델 학습 | DPO (전문가 preference) |
| 긴 행동 로그 분석 | Mamba SSM |
| 고위험 사건 깊은 추론 | Test-Time Compute (Claude o3) |
| 다양한 산업 전문가 활성 | MoE (Mixtral API) |

## R&D 부서 여부

| 항목 | 자체 R&D | OEM 활용 |
|---|---|---|
| MoE | X (Mistral API) | O |
| SSM | M (Mamba 학습 어려움) | OSS |
| DPO | O (TRL OSS) | O |
| LoRA | O (PEFT OSS) | O |
| Test-Time | X (Claude·o3 API) | O |

→ **LoRA + DPO 만 자체 학습**. 나머지 OEM/API.

## Step-by-Step

| Phase | 작업 |
|---|---|
| 1 | LoRA + QLoRA 환경 구축 (GPU 1대) |
| 2 | 내부회계 도메인 sLLM PoC (3개월) |
| 3 | DPO 로 위험 판단 정교화 (1개월) |
| 4 | Mamba SSM 긴 로그 PoC (선택) |

## 트리거
- "MoE", "Mixtral"
- "Mamba", "State Space Models"
- "DPO", "RLHF"
- "LoRA", "QLoRA", "fine-tuning"

## 참조
- TRL (Hugging Face): https://huggingface.co/docs/trl
- PEFT: https://huggingface.co/docs/peft
- Mamba: https://github.com/state-spaces/mamba
- `solution-capability-audit.md` #10-12, #39-40, #42 ( → )
