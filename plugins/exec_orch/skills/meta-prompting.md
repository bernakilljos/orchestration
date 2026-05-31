---
name: meta-prompting
description: LLM 이 자기 prompt 를 자가 개선·평가·재작성. prompt 자체가 모호하거나, 결과 품질 지속적으로 낮을 때 자동 활성. "meta prompting", "prompt 개선", "self-refine", "rewrite prompt" 키워드.
---

# Skill: Meta Prompting (Anthropic #7)

> **목적**: 약한 prompt → 강한 prompt 로 LLM 이 자가 변환.
> **트리거**: 결과 품질 지속 낮음 / prompt 모호 / 사용자 "다시 설명해줘".

## 1. 언제

| 상황 | Meta 적용? |
|---|---|
| Codex 가 같은 task 2회 hallucination | ✅ prompt 재작성 |
| 사용자 요청이 1줄 ("X 해줘") | ✅ 5단계 plan 으로 확장 |
| task-instruction.md 작성 후 hook-01 가 "4 기법 누락" warning | ✅ 보강 |
| 첫 시도 결과 불일치 | ✅ prompt 자체 점검 |
| 결과가 잘 나왔음 | ❌ 그대로 |

## 2. 표준 프로토콜 (3 단계)

```text
Step 1 — Critique
  Input: <원래 prompt>
  Question: "이 prompt 의 약점 3가지는?"
  Output: [모호함·negative 없음·예시 없음 등]

Step 2 — Rewrite
  Input: 약점 3가지
  Question: "각 약점을 보완해 prompt 다시 작성하라."
  Output: <개선 prompt v2>

Step 3 — Verify
  Input: prompt v2
  Question: "v2 가 12 기법 (Role/Negative/Context/Few-shot/CoT/...) 중 몇 개 적용?"
  Output: count + missing list
  IF count < 5 → Step 1 반복 (max 3회)
```

## 3. 자동 적용 (hook-01-pre-task 보강)

`hook-01-pre-task.sh` 가 task-instruction.md 의 12 기법 4개 누락 감지 시:

```bash
if [ -n "$MISSING_TECH" ]; then
  # 자동 meta-prompting 트리거
  python .claude/scripts/meta-rewrite.py "$TASK_INSTR" --rewrite >> "$TASK_INSTR.v2"
  diff "$TASK_INSTR" "$TASK_INSTR.v2" > "$TASK_INSTR.meta.diff"
  echo "[META] auto-rewrite 제안: $TASK_INSTR.v2 (diff: $TASK_INSTR.meta.diff)"
fi
```

## 4. 무한 재귀 방지

| 한계 | 값 |
|---|---|
| Step 1~3 반복 횟수 | max 3 |
| Step 2 rewrite 후 v3 가 v2 와 거의 동일 (sha diff ≤ 5%) | stop |
| 시간 limit | 60s |

## 5. 결과 평가 (eval_quality 와 연결)

meta-rewrite 후 v1 vs v2:
- `plugins/eval_quality/skills/llm-as-judge.md` 가 둘 다 채점
- 점수 차 ≥ 2점 → v2 채택
- 점수 차 < 2점 → v1 유지 (변경 비용 ↑)

## 6. 예시

### Before (약함)
```text
Codex, 이거 고쳐줘.
```

### After Critique
- ❌ Role 없음
- ❌ Files 없음
- ❌ Acceptance criteria 없음

### After Rewrite (강함)
```text
You are a senior Next.js engineer.

Context: orchestration_v1 — fix bug in plugins/exec_orch/hooks/hook-01-pre-task.sh
where MISSING_TECH detection fails for hyphen-encoded headings.

Files: hook-01-pre-task.sh (only)

Acceptance:
- INPUT:  task-instruction with "## 1) Role" → MATCH
- INPUT:  task-instruction with "## Role" (no num) → MATCH
- INPUT:  task-instruction without any role → MISSING

DO NOT: edit other hooks. DO NOT: add `?.` optional chaining.

Show CoT before code.
```

## 7. 금지

- 무한 재귀 (3회 한도)
- 원래 prompt 의 정보 손실 (rewrite 가 정보 줄이면 X)
- 사용자 명시 X 한 critique 외부 자동 수정
- 결과 검증 없이 v2 자동 채택

## 8. 참조

- `plugins/exec_orch/skills/prompt-techniques.md` § #7 Meta prompting
- `plugins/exec_orch/codex/task-instruction-template.md` § 1~10
- `plugins/eval_quality/skills/llm-as-judge.md`
- `plugins/exec_orch/skills/auto-planner.md` (5단계 plan 의 § 2 분석 단계와 연결)
- `.claude/scripts/meta-rewrite.py` (handler — 미구현 시 task 위임)
