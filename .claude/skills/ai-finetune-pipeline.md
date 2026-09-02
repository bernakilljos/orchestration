---
name: ai-finetune-pipeline
description: LLM 파인튜닝 실행 파이프라인 · unsloth (2~5x 빠른 QLoRA) + PEFT + Transformers 자동 · Ollama 로컬 병행. 사용자가 "파인튜닝", "fine-tune", "LoRA", "QLoRA", "PEFT", "unsloth", "sLLM 학습", "커스텀 모델" 같은 키워드 언급 시 활성화.
metadata:
  author: orchestration_v1
  version: 1.0.0
  category: ai/learning
  created: 2026-09-02
---

# AI Fine-tuning Pipeline (실행 가이드)

## 원리 커버 (참고)

원리·개념 = `plugins/exec_orch/skills/ai-learning-finetune.md` (MoE·SSM·DPO·RLHF·LoRA/QLoRA 매핑).

이 skill = **실행 파이프라인** 초점.

## 도구 스택 (2026 SOTA)

| 목적 | 도구 | 왜 |
|---|---|---|
| **초고속 QLoRA** | **unsloth** | 2~5x 빠름 · VRAM 60% 절감 · Llama·Mistral·Gemma·Qwen 대응 |
| **표준 PEFT** | **peft (Hugging Face)** | LoRA·QLoRA·Prefix·P-Tuning 통합 |
| **훈련 프레임워크** | **transformers** + **trl** | SFT·DPO·PPO·GRPO |
| **양자화** | **bitsandbytes** | 4-bit·8-bit 훈련 |
| **로컬 배포** | **Ollama** | 파인튜닝 후 gguf 변환 |
| **평가** | **lm-evaluation-harness** | MMLU·GSM8K·HumanEval |

## 자동 파이프라인 (3 단계)

### Step 1 · 환경 설정

```bash
# uv 로 빠른 설치 (권장)
uv pip install unsloth peft transformers trl bitsandbytes datasets accelerate

# 또는 pip
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
pip install --no-deps trl peft accelerate bitsandbytes
```

### Step 2 · QLoRA 파인튜닝 (unsloth · 초고속)

```python
from unsloth import FastLanguageModel
import torch
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset

# 1. 모델 로드 (4-bit)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-7B-Instruct-bnb-4bit",  # or Llama·Mistral·Gemma
    max_seq_length=2048,
    dtype=None,  # None = auto
    load_in_4bit=True,
)

# 2. LoRA adapter 부착
model = FastLanguageModel.get_peft_model(
    model,
    r=16,  # rank (8·16·32·64 · 클수록 정교·느림)
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",  # 30% VRAM 절감
    random_state=3407,
)

# 3. 데이터셋 준비
dataset = load_dataset("json", data_files="train.jsonl")["train"]
def format_chat(ex):
    return {"text": tokenizer.apply_chat_template(ex["messages"], tokenize=False)}
dataset = dataset.map(format_chat)

# 4. 훈련
trainer = SFTTrainer(
    model=model, tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=2048,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        num_train_epochs=1,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="outputs",
    ),
)
trainer.train()

# 5. 저장
model.save_pretrained("my-model-lora")
tokenizer.save_pretrained("my-model-lora")
```

### Step 3 · GGUF 변환 · Ollama 배포

```python
# GGUF 로 변환 (Ollama 호환)
model.save_pretrained_gguf("my-model-gguf", tokenizer, quantization_method="q4_k_m")
```

```bash
# Ollama 등록
cat > Modelfile <<EOF
FROM ./my-model-gguf/unsloth.Q4_K_M.gguf
TEMPLATE "{{ .Prompt }}"
PARAMETER temperature 0.7
EOF

ollama create my-model -f Modelfile
ollama run my-model
```

## DPO (Direct Preference Optimization · RLHF 대체)

```python
from trl import DPOTrainer

dpo_trainer = DPOTrainer(
    model=model,
    ref_model=None,  # unsloth 는 자동
    args=TrainingArguments(...),
    beta=0.1,
    train_dataset=dataset,  # {"prompt":..., "chosen":..., "rejected":...}
    tokenizer=tokenizer,
)
dpo_trainer.train()
```

## 데이터 형식

### SFT (chat)
```jsonl
{"messages":[{"role":"user","content":"질문"},{"role":"assistant","content":"답변"}]}
```

### DPO (선호도)
```jsonl
{"prompt":"...","chosen":"좋은 답","rejected":"나쁜 답"}
```

## 도메인 예시 (감사·규제 특화)

우리 kit 도메인 활용 시:
- 감사 로그 요약 (내부 감사팀 SFT)
- 규제 문서 QA (한국 개보법·자본시장법 DPO)
- 부정거래 탐지 분류 (RMS 데이터)
- ICM Agent Go 응답 스타일 커스터마이징

## 평가

```bash
# lm-evaluation-harness
git clone https://github.com/EleutherAI/lm-evaluation-harness
cd lm-evaluation-harness && pip install -e .

lm_eval --model hf \
    --model_args pretrained=./my-model-lora \
    --tasks mmlu,gsm8k,arc_challenge \
    --device cuda:0 \
    --batch_size 8
```

## 비용 매트릭스 (실측)

| GPU | 모델 | 배치·seq | 시간 (1 epoch·10k rows) | 메모리 |
|---|---|---|---|---|
| RTX 4090 (24GB) | Qwen2.5-7B QLoRA (unsloth) | 2 · 2048 | ~40분 | 15GB |
| A100 40GB | Llama-3.1-8B QLoRA (unsloth) | 4 · 4096 | ~25분 | 25GB |
| H100 80GB | Llama-3.1-70B QLoRA (unsloth) | 2 · 4096 | ~2h | 65GB |
| Colab T4 (16GB) | Qwen2.5-1.5B QLoRA | 1 · 1024 | ~1h | 12GB |

## 언제 파인튜닝? (판정)

| 요구 | 판정 |
|---|---|
| 답 정확도 향상 | RAG 우선 (더 저렴·빠름) |
| 응답 스타일·페르소나 | 파인튜닝 유리 |
| 도메인 용어·지식 | RAG + few-shot > 파인튜닝 |
| 특정 형식 강제 (JSON·XML) | 파인튜닝 유리 |
| 언어·번역 도메인 | 파인튜닝 유리 |
| 프라이버시·폐쇄망 | 파인튜닝 필수 (로컬 모델) |

## 금지

1. **평가 없이 배포 X** (lm-eval 필수)
2. **원본 데이터셋 유실 X** (버전 관리 필수)
3. **개인정보 포함 데이터셋 X** (마스킹 필수)
4. **GPU 없이 훈련 X** (CPU 는 예측만)
5. **작은 데이터 (100 rows) 로 fine-tune X** (오버피팅)

## 관련

- `plugins/exec_orch/skills/ai-learning-finetune.md` (원리·50 기술)
- `plugins/exec_offline/` (로컬 스택 · Ollama)
- `.claude/rules/language-standards.md` (Python 표준)
- unsloth GitHub: github.com/unslothai/unsloth
- PEFT docs: huggingface.co/docs/peft
