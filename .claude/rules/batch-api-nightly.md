# Batch API 야간 배치 룰 (Task 36)

> **근거**: 2026-09-02 · Anthropic Batch API 50% 할인 · 대량 비긴급 태스크 야간 처리.

## 절대 룰

**비긴급 대량 태스크 = 야간 03:00 Batch API 실행 · 50% 절감.**

## 배치 후보

| 태스크 유형 | 배치 적합 | 이유 |
|---|---|---|
| **대량 감사조서 생성** |  | 즉시 결과 필요 X · 야간 완료 |
| **문서 요약 (100+ 문서)** |  | 대량 · 시간 여유 |
| **RAG 재인덱싱** |  | 백그라운드 |
| **테스트 케이스 생성 (대량)** |  | test-gen 확장 |
| **주간 리포트** |  | 매주 일요일 |
| **실시간 응답** |  | Batch 부적합 |
| **디버깅·개발** |  | 즉시 필요 |

## 워크플로

```text
[야간 03:00 · Task Scheduler]
  1. .claude/state/pending-batch-tasks/ 폴더 스캔
  2. Anthropic Message Batches API 로 요청 (최대 100k requests · 24h)
  3. 완료 대기 · polling
  4. 결과 저장: .claude/state/batch-results/
  5. 아침 SessionStart 시 완료 알림
```

## 비용 매트릭스

| 모델 | 표준 | Batch (50% 할인) |
|---|---|---|
| Opus 5 | $5/$25 | **$2.5/$12.5** |
| Sonnet 5 | $2/$10 | **$1/$5** |
| Haiku 4.5 | $0.25/$1.25 | **$0.125/$0.625** |

**대량 배치일수록 절감 큼.**

## 사용 예

```python
from anthropic import Anthropic
client = Anthropic()

batch = client.messages.batches.create(
    requests=[
        {"custom_id": "audit-1", "params": {"model": "claude-opus-5", "max_tokens": 1024, "messages": [...]}},
        # ... 최대 100,000 requests
    ]
)
# batch.id 로 나중에 조회
```

## Task Scheduler 등록 (예정)

`setup/modules/17-batch-nightly.bat` (신설 예정):
```batch
schtasks /create /tn "Orca_BatchNightly" /tr "python C:\pjt\orchestration_v1\.claude\scripts\batch-nightly-run.py" /sc daily /st 03:00
```

## 관련

- `.claude/scripts/batch-nightly-run.py` (예정)
- `.claude/rules/auto-optimization.md` (야간 스케줄)
- Anthropic docs: docs.claude.com/en/api/batch-messages
