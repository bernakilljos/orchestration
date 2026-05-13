---
description: "결과 파일을 Haiku 가 0~10점 채점 — task-instruction + 결과물 경로 인자"
allowed-tools: Bash(python:*), Bash(jq:*), Read
---

# /score-task

Haiku 4.5 LLM-as-judge 로 결과물 품질을 0~10 점 평가.

## 사용

```
/score-task <task-file> <result-file>
```

예시:
```
/score-task .claude/tasks/done/task-042.md docs/implementation-report.md
```

## 동작

1. 두 파일을 읽어 평가 프롬프트 구성
2. `python plugins/eval_quality/scripts/score_task.py --task <task-file> --result <result-file>` 호출
3. Haiku 응답 → 4차원 점수 + verdict
4. `.claude/state/evaluations.jsonl` 에 한 줄 append
5. stdout 에 사람용 요약 출력

## 출력 예

```
Task: task-042 | File: docs/implementation-report.md
─────────────────────────────────────────
Correctness:   8/10
Completeness:  7/10
Style:         9/10
Safety:       10/10
─────────────────────────────────────────
VERDICT: PASS  (avg 8.5)
Reason: 요구사항 모두 충족, 일부 edge case 미커버
Saved: .claude/state/evaluations.jsonl (line +1)
```

## 자동화 옵션

`--auto` 플래그로 가장 최근 done/ 태스크 + 가장 최근 docs 결과 자동 매칭:
```bash
bash plugins/eval_quality/scripts/score_task.sh --auto
```

## 금지

- 결과 파일 수정 (읽기 전용)
- PASS 했다고 워커 자동 재시작 (Claude 가 결정)
- Safety < 10 인 결과를 PASS 로 통과시키지 말 것
