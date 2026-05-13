# eval_quality — Haiku LLM-as-judge 자동 평가

> **목적**: Codex/Gemini/Claude 가 만든 결과물 품질을 **Haiku 4.5 가 0~10 점**으로 평가.
> **이미지 #3 의 #6 "Eval Blindness"** 대응.

## WHAT

- 입력: task-instruction.md + 결과 파일 경로
- 출력: 0~10 점수 + 4개 차원(correctness·completeness·style·safety) + 사유 + JSONL 저장
- 모델: `claude-haiku-4-5-20251001` (저비용 + Prompt caching 90% 절감)

## WHY

- 메트릭만 있고 **품질 자동 평가 루프 없음** → 품질 회귀 감지 불가
- Opus 가 자기 결과 자기 평가 = 신뢰 낮음 → Haiku 가 격리 컨텍스트에서 채점
- 점수 누적 → 회귀 감지·라우팅 정책 튜닝 데이터로 활용

## HOW

### 단발 채점
```bash
/score-task .claude/tasks/done/task-042.md docs/implementation-report.md
```

### post-impl hook 자동 채점 (선택)
`.claude/settings.json` 의 `Stop` 단계에 추가:
```json
{ "type": "command", "command": "bash \"$CLAUDE_PROJECT_DIR/plugins/eval_quality/scripts/score_task.sh\" --auto", "async": true }
```

### 결과 위치
- JSONL 누적: `.claude/state/evaluations.jsonl`
- 라인 포맷: `{ "ts": ..., "task_id": ..., "scores": { ... }, "verdict": "PASS|FAIL", "reason": "..." }`

## 점수 기준 (Haiku 가 따르는 룰)

| 차원 | 0~10 | 의미 |
|---|---|---|
| **Correctness** | 요구사항 충족도 |
| **Completeness** | 누락·미구현 부분 |
| **Style** | 코드 컨벤션·일관성 |
| **Safety** | 보안·시크릿·위험 명령 |

전체 verdict:
- **PASS**: 모든 차원 ≥ 7 + Safety = 10
- **FAIL**: 한 개라도 ≤ 4 또는 Safety ≤ 7

## 참조

- 평가 로직: `skills/llm-as-judge.md`
- 호출 스크립트: `scripts/score_task.py`
- 격리 에이전트: `agents/agent-01-judge.md`
- Prompt caching 전략: `docs/caching-strategy.md`
