---
name: ai-quantum-ml
description: IBM Quantum Network·Qiskit·PennyLane 무료 가입으로 Quantum ML 도입. 금융 부정거래·신용평가·공급망 최적화에 양자 우위 (Quantum Advantage) 적용. 사용자가 "Quantum ML", "QML", "IBM Quantum", "Qiskit", "양자모델" 같은 키워드를 말할 때 활성화.
metadata:
  author: orchestration_v1
  version: 1.0.0
  category: quantum-ai
  tags: [quantum-ml, qiskit, pennylane, ibm-quantum]
---

# Quantum ML Bundle — QML·Variational Quantum Circuits

## 50 기술 카탈로그 매핑

| # | 기술 | 핵심 |
|---|---|---|
| 20 | Quantum ML (QML) | IBM Quantum·Google·Azure Quantum |
| 21 | Variational Quantum Circuits | Qiskit·PennyLane |

## 무료 도입 (자체 R&D 거의 X)

```bash
# 1. IBM Quantum Network 가입 (무료)
# https://quantum-computing.ibm.com/

# 2. Qiskit 설치
pip install qiskit qiskit-machine-learning qiskit-aer

# 3. PennyLane (Xanadu)
pip install pennylane pennylane-qiskit

# 4. Azure Quantum (선택)
# https://azure.microsoft.com/en-us/products/quantum/
```

## Variational Quantum Classifier 예제 (금융 부정거래)

```python
from qiskit_machine_learning.algorithms import VQC
from qiskit_machine_learning.circuit.library import RawFeatureVector
from qiskit.circuit.library import RealAmplitudes
from qiskit.primitives import Sampler

# 1. 양자 feature map + ansatz
feature_map = RawFeatureVector(8)        # 8 features
ansatz = RealAmplitudes(8, reps=3)

# 2. VQC 학습 (고객 거래 데이터)
vqc = VQC(
    sampler=Sampler(),
    feature_map=feature_map,
    ansatz=ansatz,
    loss='cross_entropy'
)
vqc.fit(X_train, y_train)  # 부정/정상 라벨

# 3. 예측
score = vqc.predict_proba(X_test)
```

## ITCEN CORE 적용 (실제 사업화)

| 시나리오 | 양자 우위 | 객단가 |
|---|---|---|
| **금융 부정거래 양자 최적화** | 8-12 feature 동시 최적 | 5억+/年 |
| **신용평가 양자 가속** | 비선형 패턴 학습 | 3억+/年 |
| **공급망 위험 양자 시뮬** | NP-hard 라우팅 | 5억+/年 (건설 ERP base) |
| **카지노 게임 부정 (조작)** | 양자 RNG 검증 | 1억+/年 |

## ITCEN PNS 협업 (사이버보안 + 양자)

- 양자 우위 PQC (Post-Quantum Crypto) 마이그레이션
- KISA 2026 PQC 가이드 대응
- 금융권 양자 보안 컨설팅 → ITCEN PNS 가 보안 영역, ITCEN CORE 가 ML

## Step-by-Step

| Phase | 작업 | 기간 |
|---|---|---|
| 1 | IBM Quantum Network 가입 (10분) | 1일 |
| 2 | Qiskit 튜토리얼·샘플 학습 | 1주 |
| 3 | 금융 부정거래 PoC (8 features VQC) | 1개월 |
| 4 | ITCEN 고객사 데이터 적용 (익명화) | 2개월 |
| 5 | 양자 우위 측정·논문·표준 lobby | 3개월 |
| 6 | 사업화 (금융권 직판) | 6개월 |

## AI Risk Lighthouse 카테고리 #6 (Compliance 10%) 보강

PQC 마이그레이션 = NIST 2028-2030 의무화 대응.

## 트리거

- "Quantum ML", "QML", "양자모델"
- "IBM Quantum", "Qiskit", "PennyLane"
- "Variational Quantum Circuit"
- "양자 우위", "Quantum Advantage"

## 참조

- IBM Quantum Network: https://quantum-computing.ibm.com/
- Qiskit Tutorials: https://qiskit.org/learn/
- PennyLane: https://pennylane.ai/
- `solution-capability-audit.md` #20-21 ( →  가입 가이드 제공)
