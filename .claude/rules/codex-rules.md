# Codex 위임 룰

> **근거**: CLAUDE.md § 7-1 (`task-instruction.md 없이 Codex 호출 금지`).
> **이유**: Codex 는 컨텍스트 추측 시 hallucination 발생률 ↑ (`.claude/rules/post-codex-verify.md` 의 2026-05-30 사례).

## 절대 룰

**Codex 호출 전 반드시 task-instruction.md 가 `.claude/tasks/` 에 존재.**

## task-instruction.md 필수 섹션 (12 기법 통합)

| 섹션 | 기법 (`prompt-techniques.md`) | 필수? |
|---|---|---|
| § 1 Role | #1 Role prompting | ✅ |
| § 2 Context | #3 Context priming | ✅ |
| § 3 Files (allow-list) | — | ✅ |
| § 4 Acceptance criteria | #4 Few-shot | ✅ |
| § 5 Reasoning (CoT) | #5 Chain of Thought | ✅ |
| § 6 Negative constraints | #2 Negative prompting | ✅ |
| § 7 ReAct loop | #10 ReAct | 도구 사용 시 |
| § 8 완료 검증 | post-codex-verify | ✅ |
| § 9 Confidence | failure-mode | ✅ |
| § 10 Self-consistency | #8 Self-consistency | 보안·DB·money 시만 |

표준: `plugins/exec_orch/codex/task-instruction-template.md`

## hook-01-pre-task 자동 검증

매 codex 호출 직전 `hook-01-pre-task.sh` 가:
1. `current-tasks.json` 에 등록
2. `locked_files` 충돌 검사
3. **12 기법 4개 (role·negative·context·few-shot) 누락 시 warning**

## 호출 흐름

```bash
# 1. task-instruction 작성 (template 복사)
cp plugins/exec_orch/codex/task-instruction-template.md \
   .claude/tasks/task-<slug>.md
$EDITOR .claude/tasks/task-<slug>.md

# 2. pre-snapshot (post-codex-verify)
bash plugins/exec_orch/hooks/post-codex-verify.sh pre <slug>

# 3. codex 호출
codex exec --task .claude/tasks/task-<slug>.md

# 4. post-verify (변경 0 = hallucination)
bash plugins/exec_orch/hooks/post-codex-verify.sh post <slug>
```

## 금지

1. **task-instruction.md 없이 직접 `codex exec "..."`** — 컨텍스트 부족 → 결과 엉망
2. **§ 3 files allow-list 없음** — codex 가 task 외 파일 마음대로 수정
3. **§ 6 negative constraints 없음** — `?.` / 하드 경로 / 주석에 owner 같은 흔한 위반 재발
4. **§ 8 완료 검증 없음** — git diff stat 안 보고 "완료" 보고
5. **`done/` 빈 task 이동** (§ 7-8 위장 완료) — empty commit 으로 hallucination 검출

## 라우팅 자동 위임 기준 (`route_dispatch.md`)

| 신호 | Codex 위임? |
|---|---|
| 코드 500줄+ | ✅ ×4 병렬 |
| 단순 구현 <200줄 | ❌ Sonnet 4.6 직접 |
| 설계·아키텍처·왜 | ❌ Opus 4.7 Extended Thinking |
| 검증·리뷰 | ❌ Haiku 4.5 ×2 |
| 1M+ 리서치 | ❌ Gemini Flash |

## 사후 검증 의무 (`post-codex-verify.md`)

- pre/post snapshot 자동
- 변경 0 라인 = `[HALLUCINATION]` 표시 + empty commit
- 같은 task 3회 hallucination → codex 임시 disable

## 참조

- `CLAUDE.md § 7-1` (금지)
- `plugins/exec_orch/codex/instructions.md` (codex 역할)
- `plugins/exec_orch/codex/task-instruction-template.md` (표준)
- `plugins/exec_orch/skills/prompt-techniques.md` (12 기법)
- `.claude/rules/post-codex-verify.md` (사후 검증)
- `.claude/rules/failure-mode.md` (거절·confidence)
