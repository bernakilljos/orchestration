---
name: ai-affective-emotion
description: Affective Computing / Emotion AI 통합 — Affectiva·Hume·Realeyes OEM 으로 감정·스트레스 인식. 카지노 딜러·금융직원 부정 사전 예방, 카지노 플레이어 도박중독 조기경보. 사용자가 "Affective Computing", "Emotion AI", "감정 인식", "스트레스 탐지", "Hume", "Affectiva" 같은 키워드를 말할 때 활성화.
metadata:
  author: orchestration_v1
  version: 1.0.0
  category: affective-ai
---

# Affective Computing — 감정·스트레스 AI

## 50 기술 #30

**시장**: $42.9B by 2027 (CAGR 12.8%) — 한국 진입자 거의 없음.

## 신호 채널

| 채널 | 측정 |
|---|---|
| **얼굴** | 미세표정·시선·동공·표정 변화 |
| **음성** | tone·pitch·jitter·shimmer·pause |
| **텍스트** | sentiment·urgency·강도 |
| **생체** | 심박변동(HRV)·피부 전도(GSR)·호흡 |
| **행동** | 타이핑·마우스 패턴 (Behavioral Biometric 연동) |

## OEM 추천

| 회사 | 특징 | 한국 |
|---|---|---|
| **Hume AI** | 음성+얼굴+텍스트 통합 (최강) | 없음 ⭐⭐⭐ |
| **Affectiva** (SmartEye 인수) | 얼굴 표정 표준 | 없음 |
| **Realeyes** | 마케팅·UX 측정 | 없음 |
| **Beyond Verbal** | 음성 감정 | 학계 |

## ITCEN CORE 적용 시나리오

| 시나리오 | OEM | 매출 잠재 |
|---|---|---|
| **카지노 딜러 스트레스 사전 감지** | Affectiva (CCTV 통합) | 카지노 9社 × 5억 |
| **금융 직원 부정 사전 예방** | Hume (음성+행동) | 1社 3-7억 × 30개 은행 |
| **카지노 플레이어 도박중독 조기경보** | Realeyes (얼굴 분석) | 사회적 책임·정부 보조금 |
| **콜센터 감정 분석** | Hume | 금융·보험·텔레콤 |
| **회의·면담 위험 감지** | 음성+얼굴 | HR·임원 의사결정 |

## 도입 코드 예제 (Hume API)

```python
import requests

# Hume 음성 분석
response = requests.post(
    'https://api.hume.ai/v0/batch/jobs',
    headers={'X-Hume-Api-Key': API_KEY},
    json={
        'models': {'prosody': {}, 'language': {}, 'face': {}},
        'transcription': {'language': 'ko'},
        'urls': ['s3://dept/dealer-shift-001.mp4']
    }
)
job_id = response.json()['job_id']

# 결과 — 감정 점수 + 시간대별
result = requests.get(f'https://api.hume.ai/v0/batch/jobs/{job_id}/predictions')
# 출력: angry·anxious·focused·tired ... 시간대별
```

## 행동위험분석 + Emotion AI 융합 (부서 차원 확장)

```text
기존 UEBA: 행동 패턴 → 위험 점수
        ↓
   + Emotion AI
        ↓
새 차원: 행동 + 감정 = 더 정확한 위험 예측

예) 직원 행동이 정상 + 감정이 극도 스트레스 → 부정 가능성 ↑
    딜러 행동 정상 + 미세표정 긴장 → 공모 의심
```

## AI Risk Lighthouse #3 (Coverage 15%) 강화

행동 + 감정 통합 시 카테고리 점수 +15.

## Step-by-Step

| Phase | 작업 | 기간 |
|---|---|---|
| 1 | Hume 무료 tier 가입 + 음성 PoC | 1주 |
| 2 | 카지노 1社 베타 (CCTV 음성 분석) | 1개월 |
| 3 | UEBA + Emotion 융합 모델 | 2개월 |
| 4 | 본격 도입 (9社) | 6개월 |
| 5 | 글로벌 확장 (동남아 카지노) | 12개월 |

## 트리거
- "Affective Computing", "Emotion AI"
- "감정 인식", "스트레스 탐지"
- "Hume", "Affectiva", "Realeyes"

## 참조
- Hume AI: https://hume.ai/
- Affectiva (SmartEye)
- `ai-risk-lighthouse.md` § Behavioral Coverage
- `solution-capability-audit.md` #30 (❌ → 🟡)
