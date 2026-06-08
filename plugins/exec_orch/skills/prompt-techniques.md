---
name: prompt-techniques
description: |
  Codex·Gemini·Haiku 워커 호출 시 12 프롬프팅 기법 자동 적용으로 결과 품질 개선.
  사용자가 "프롬프트 강화", "엉망", "결과 품질", "role prompting", "CoT", "few-shot", "ReAct", "RAG", "self-consistency", "ToT" 등 키워드 언급 시 활성.
  task-instruction.md 생성 시 이 skill 의 template 자동 통합.
---

# Skill: 12 Prompting Techniques

> **목적**: 외부 워커 (Codex / Gemini / Haiku) 호출 결과가 엉망일 때 적용할 12 기법 매트릭스 + task-instruction template.
> **트리거**: task-instruction.md 작성 / route_dispatch 위임 / "결과 품질 부족" 신호.

## 1. 12 기법 매트릭스

| # | 기법 | WHAT | WHEN 쓰나 | HOW (한 줄 패턴) |
|---|---|---|---|---|
| 1 | **Role prompting** | LLM 에 페르소나 부여 | 도메인 전문성 필요 시 | "You are a senior Next.js architect with 10y experience." |
| 2 | **Negative prompting** | 하지 말아야 할 것 명시 | 흔한 실패 패턴 차단 | "DO NOT use `?.`, DO NOT add comments unless WHY is non-obvious." |
| 3 | **Context priming** | 작업 전 시스템 컨텍스트 주입 | 프로젝트 룰·구조 인지 필요 | "Project: orchestration_v1 (SoT=plugins/, sync=.claude/). Read CLAUDE.md before edit." |
| 4 | **Few-shot prompting** | 2~5개 입/출력 예시 | 출력 포맷 강제 | "Example1: ... → ...\nExample2: ... → ..." |
| 5 | **Chain of Thought (CoT)** | 단계별 추론 강요 | 다단계 논리·수학 | "Show your reasoning step by step before the final answer." |
| 6 | **Prompt chaining** | 단계별 prompt 직렬 연결 | 큰 task 분해 | step1 output → step2 input → step3 input |
| 7 | **Meta prompting** ([[meta-prompting]]) | LLM 이 자기 prompt 개선 | prompt 자체 모호할 때 / 결과 품질 지속 낮음 | Critique → Rewrite → Verify 3 단계 (max 3 반복). 자동 트리거: hook-01-pre-task 4 기법 누락 감지 시 |
| 8 | **Self-consistency** | N회 샘플 후 다수결 | 정답 검증 (factual·math) | "Generate 3 answers (temp=0.7), pick majority." |
| 9 | **Tree of Thoughts (ToT)** ([[tot-prompting]]) | 여러 경로 탐색 + backtrack | 탐색 공간 큰 문제 (아키텍처·알고리즘·디버깅 가설 분기) | Branch N=3~5 → Evaluate (Feasibility·Cost·Risk) → Prune top50% → Expand depth≤3. route_dispatch DESIGN/DECISION 자동 트리거. |
| 10 | **ReAct prompting** | Thought→Action→Observation 루프 | 도구 사용 task (search·exec) | "Thought: ...\nAction: search(\"X\")\nObservation: ...\nThought: ..." |
| 11 | **Zero-shot CoT** | 예시 없이 CoT 트리거 | 빠른 추론 (예시 비용 절감) | "Let's think step by step." 한 줄만 |
| 12 | **RAG prompting** | 외부 지식 검색 후 prompt 주입 | 최신·사실 기반 출력 필요 | "Retrieve top-5 docs → cite → answer with [source: ...]" |

## 2. 라우팅별 기본 기법 (이 kit 매핑)

| 워커 | 기본 적용 기법 | 비고 |
|---|---|---|
| **Claude Opus 4.8** | 1·3·5·9 (Role + Context + CoT + ToT) | 설계·복잡 추론. Extended Thinking 1M context + `/effort xhigh` + ultracode (Dynamic Workflows). |
| **Claude Sonnet 4.6** | 1·3·11 (Role + Context + Zero-shot CoT) | <200줄 단순 구현. 비용 효율. |
| **Codex (×4 병렬)** | 1·2·3·4·10 (Role + Negative + Context + Few-shot + ReAct) | 500줄+ 코드. task-instruction.md 의무. |
| **Haiku 4.5 (×2 검증)** | 1·3·4·11 (Role + Context + Few-shot + Zero-shot CoT) | 검증·점수화. Prompt caching 90% 절감. |
| **Gemini Flash** | 1·3·12 (Role + Context + RAG) | 초장문 (>500k 토큰) · 멀티모달. |

## 3. task-instruction.md 표준 template (Codex 위임)

```markdown
# Task: <slug>

## 1) Role (기법 #1)
You are a senior <stack> engineer. Your job: <one-line goal>.

## 2) Context (기법 #3)
- Project: <name> (root: <abs path>)
- SoT: plugins/<plug>/ — never edit .claude/ directly
- Read first: CLAUDE.md, .claude/rules/*.md, <relevant existing file>
- Existing pattern: <link to similar file>

## 3) Files (수정 허용 화이트리스트)
- <file1>
- <file2>

## 4) Acceptance criteria (기법 #4 few-shot)
- Input: <example1>  →  Output: <expected1>
- Input: <example2>  →  Output: <expected2>

## 5) Reasoning (기법 #5 CoT)
Before writing code, show:
1. 어떤 함수·모듈 영향 받는지
2. edge case 무엇
3. 어떤 룰 (CLAUDE.md § 7) 적용

## 6) Negative constraints (기법 #2)
DO NOT:
- 하드코딩 path / 사용자명 / Python 버전 (CLAUDE.md § 7-4)
- `?.` (optional chaining) 사용 (§ 7-5)
- 코드 주석에 "owner" (§ 7-6)
- task 외 파일 수정
- 빈 task `done/` 이동 (§ 7-8)

## 7) ReAct loop (기법 #10 — 도구 사용 시)
Format:
  Thought: <next step 추론>
  Action: <tool call>
  Observation: <tool result>
  ... (반복)
  Final: <결과 + 변경 summary>

## 8) 완료 검증 (post-codex-verify 호환)
끝나면:
1. `git status`
2. `git add -A`
3. `git diff --cached --stat`
4. 변경 0 라인 = "[HALLUCINATION SUSPECTED]" 표시
5. report.md 에 git diff stat 첨부
```

## 4. Negative prompting 표준 set (모든 위임 공통)

```text
DO NOT:
- Use `?.` optional chaining
- Add comments unless WHY is non-obvious
- Hardcode paths (C:\Users\X, /home/Y, Python3XX)
- Use word "owner" in code comments
- Fabricate file paths / function names not verified
- Report PASS without confidence ≥ 7 (.claude/rules/failure-mode.md)
- Edit .claude/ directly (it's sync target — plugins/ is SoT)
- Move empty tasks to done/ (fake completion)
```

## 5. Self-consistency 적용 (기법 #8) — eval_quality 와 연결

비싼 결정 (보안·아키텍처·DB 마이그레이션) 은 N=3 샘플 → 다수결:

```bash
# pseudo-code in route_dispatch
for i in 1..3:
  result_i = call_worker(prompt, temp=0.7)
final = majority_vote(result_1, result_2, result_3)
```

`plugins/eval_quality/skills/llm-as-judge.md` 와 결합.

## 6. ReAct loop (기법 #10) — 도구 사용 워커 표준

Codex / Claude 가 Bash·Read·WebFetch 같은 도구 쓸 때 format:

```text
Thought: 사용자가 X 를 원함. 먼저 파일 구조 봐야.
Action: ls plugins/exec_orch/
Observation: [skills/, commands/, hooks/, ...]
Thought: skills 에 prompt-techniques 있는지 확인.
Action: ls plugins/exec_orch/skills/
Observation: [auto-planner.md, ..., prompt-techniques.md]
Thought: 있음. 내용 본 후 결정.
Action: read prompt-techniques.md
Observation: ...
Final: 12 기법 모두 적용 가능. task-instruction template 사용 권장.
```

## 7. RAG prompting (기법 #12) — Claude doc / 인스타 트렌드 같은 외부 fetch

외부 fetch 후 prompt 주입:

```python
# pseudo
docs = WebFetch("https://docs.anthropic.com/en/release-notes")
prompt = f"""
You are a Claude Code expert.

Recent changes:
{docs}

User request: {user_input}

Answer based on the recent changes, cite source.
"""
```

이 패턴은 `plugins/exec_orch/skills/daily-claude-doc-sync.md` (이 skill 의 sibling) 에서 사용.

## 8. lottoclaude 같은 install target 에서 사용

1. `install-to-target.sh` 가 이 skill 자동 배포
2. task-instruction.md 작성 시 § 3 template 으로
3. codex / gemini 호출 전 hook-01-pre-task 가 template 검증
4. 결과 fail 율 ↓ + 코드 품질 ↑

## 9. 트리거

- 명시: "프롬프트", "role prompting", "CoT", "few-shot", "ReAct", "RAG", "self-consistency", "ToT", "엉망", "결과 품질"
- 자동: `task-instruction.md` 작성·수정 시 hook 발동
- 자동: route_dispatch 가 워커 위임 직전 (`hook-08-ai-handoff`)

## 10. 금지

- 기법 1·2·3 (Role + Negative + Context) 없이 외부 위임 — 결과 품질 보장 X
- few-shot 예시 없이 "포맷 따라" 명령 — fail 흔함
- self-consistency 없이 보안·DB·money 결정 위임 — 위험
- meta prompting 무한 재귀 — 1단계 limit

## 11. 참조

- `route_dispatch.md` — 워커 라우팅 매트릭스
- `post-codex-verify.md` — codex 결과 hallucination 검출
- `.claude/rules/failure-mode.md` § "9 Silent Killers" — fabrication 방지
- `plugins/eval_quality/skills/llm-as-judge.md` — Self-consistency 점수화
- `plugins/exec_orch/codex/instructions.md` — Codex 역할
- task-instruction template: `plugins/exec_orch/codex/task-instruction-template.md`
