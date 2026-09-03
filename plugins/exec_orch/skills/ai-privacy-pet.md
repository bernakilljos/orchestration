---
name: ai-privacy-pet
description: Federated Learning·Confidential Computing·Synthetic Data·동형암호·차등프라이버시 등 PET (Privacy-Enhancing Technologies) 묶음 통합. 고객사 데이터 안 모으고 학습 + 메모리 사용 중 암호화 + 개인정보 0 합성. 사용자가 "Federated Learning", "Confidential Computing", "동형암호", "차등프라이버시", "PET", "Synthetic Data" 같은 키워드를 말할 때 활성화.
metadata:
  author: orchestration_v1
  version: 1.0.0
  category: privacy
  tags: [federated-learning, confidential-computing, synthetic-data, pet]
---

# PET Bundle — Privacy-Enhancing Technologies

## 50 기술 매핑

| # | 기술 | 핵심 |
|---|---|---|
| 27 | Federated Learning | NVIDIA FLARE·Flower·Owkin |
| 28 | Confidential Computing | NVIDIA H100 CC·Intel SGX·AMD SEV |
| 29 | Synthetic Data Generation | Gretel·Mostly AI·Tonic |

## 무료/저비용 도입

```bash
# 1. Federated Learning — Flower (오픈소스)
pip install flwr

# 2. Synthetic Data — Gretel (무료 tier)
pip install gretel-client
# https://gretel.ai/

# 3. Differential Privacy — Opacus (PyTorch)
pip install opacus

# 4. Homomorphic Encryption — TenSEAL·Pyfhel
pip install tenseal pyfhel

# 5. Confidential Computing — Intel SGX SDK
# https://software.intel.com/sgx (CPU 지원 필요)
```

## Flower 컨소시엄 학습 예제 (여러 고객사)

```python
import flwr as fl

# 각 고객사 (은행 A·B·C) 가 자기 서버에 학습
class BankClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        return [w.numpy() for w in model.weights]
    def fit(self, parameters, config):
        model.set_weights(parameters)
        # 자기 데이터로만 학습 — 외부로 안 보냄
        model.fit(local_data, epochs=5, batch_size=32)
        return self.get_parameters(config), len(local_data), {}
    def evaluate(self, parameters, config):
        model.set_weights(parameters)
        loss, acc = model.evaluate(local_test)
        return loss, len(local_test), {'accuracy': acc}

# Central Server (ITCEN CORE) — weight 만 받음
strategy = fl.server.strategy.FedAvg(min_fit_clients=3)
fl.server.start_server(strategy=strategy, num_rounds=20)
```

## Synthetic Data — Gretel 예제

```python
from gretel_client.helpers import poll

# 1. 실제 데이터 업로드 (익명화)
project = gretel.projects.create_project(name='dept-ueba-synthetic')
model = project.create_model_obj(
    model_config='synthetics/default',
    data_source='employee_behavior.csv'
)
model.submit_cloud()
poll(model)

# 2. 합성 데이터 생성 (개인정보 0)
record_handler = model.create_record_handler_obj(
    params={'num_records': 100000}
)
record_handler.submit_cloud()
poll(record_handler)

# 3. 다운로드 → 행동AI 학습 데이터
synthetic_df = record_handler.get_artifact_link('data_preview')
```

## Differential Privacy — Opacus

```python
from opacus import PrivacyEngine

privacy_engine = PrivacyEngine()
model, optimizer, train_loader = privacy_engine.make_private(
    module=model,
    optimizer=optimizer,
    data_loader=train_loader,
    noise_multiplier=1.1,   # epsilon 조절
    max_grad_norm=1.0,
)
# 학습 — 차등프라이버시 보장 (epsilon=ε 출력)
```

## ITCEN CORE 적용 매트릭스

| 시나리오 | 도입 PET |
|---|---|
| **금융권 컨소시엄 부정탐지** | Flower (여러 은행 데이터 안 모음) |
| **내부회계 합성 데이터** | Gretel (개인정보 없이 학습 데이터) |
| **AI 모델 도용 방어** | Confidential Computing (NVIDIA H100 CC) |
| **고객 데이터 분석 격리** | Intel SGX TEE |
| **차등프라이버시 학습** | Opacus (epsilon ≤ 3) |
| **암호화 상태 연산** | TenSEAL (CKKS 동형암호) |

## AI Risk Lighthouse 카테고리 #5 (Privacy PET 12%) 100% 충족

| 항목 | 검사 |
|---|---|
| Federated Learning 적용? | Flower 통합 = +5 |
| Confidential Computing? | TEE 적용 = +3 |
| 동형암호 사용? | TenSEAL = +2 |
| 차등프라이버시? | Opacus epsilon ≤ 3 = +2 |
| 합성 데이터? | Gretel = +2 |

→ 5 PET 다 통합 시 카테고리 100점.

## Step-by-Step

| Phase | 작업 | 기간 |
|---|---|---|
| 1 | Flower 무료 가입 + 튜토리얼 | 1일 |
| 2 | Gretel 무료 tier — 부서 합성 데이터 PoC | 1주 |
| 3 | Opacus 차등프라이버시 학습 PoC | 2주 |
| 4 | 금융 컨소시엄 Flower PoC (1社 + 1) | 1개월 |
| 5 | TenSEAL 동형암호 PoC | 1개월 |
| 6 | Intel SGX TEE — 필요 시 (CPU 의존) | 3개월 |

## 법규·표준 충족

- **EU GDPR** — 데이터 최소화·익명화
- **한국 개인정보보호법** — 가명정보·익명정보 (2026 확대)
- **금감원 AI 거버넌스** (2026) — 안전조치 의무
- **ISO 27701** — 개인정보 관리시스템

## 트리거

- "PET", "Privacy-Enhancing Technologies"
- "Federated Learning", "Flower", "NVIDIA FLARE"
- "Confidential Computing", "SGX", "TEE"
- "Synthetic Data", "Gretel"
- "동형암호", "Homomorphic", "TenSEAL"
- "차등프라이버시", "Differential Privacy", "Opacus"

## 참조

- Flower: https://flower.ai/
- Gretel: https://gretel.ai/
- Opacus: https://opacus.ai/
- `ai-risk-lighthouse.md` § Privacy (12%)
- `solution-capability-audit.md` #27-29 ( →  통합 가이드)
