# Task-instruction.md 표준 template (12 프롬프팅 기법 통합)

> **사용**: Codex / Gemini / Haiku 워커 위임 시 이 template 복사 → 빈 칸 채움 → `.claude/tasks/task-<slug>.md` 저장.
> **근거**: `plugins/exec_orch/skills/prompt-techniques.md` (Role + Negative + Context + Few-shot + CoT + ReAct).
> **자동화**: `hook-01-pre-task.sh` 가 task 생성 시 이 template 미사용 → 자동 wrap.

---

# Task: <slug>            ← kebab-case, 짧고 명확

## 1) Role (Anthropic Prompting #1)
You are a senior <stack: Next.js / Python / Bash / SQL> engineer.
Your single responsibility: <one-line goal>.

## 2) Context (#3 Context priming)
- Project root: `<abs path>` (e.g. C:\work\<name>)
- SoT 원칙: `plugins/<plug>/` 만 편집. `.claude/` 는 sync 결과 — 직접 편집 X.
- Read first:
  - `CLAUDE.md` (project rules)
  - `.claude/rules/<relevant>.md`
  - `<existing file similar to target>`
- Existing pattern reference: `<path/to/similar.py>`
- Today: `<YYYY-MM-DD>`

## 3) Files (allow-list — 수정 화이트리스트)
- `<file1>` — `<왜 수정 필요>`
- `<file2>` — `<왜 수정 필요>`
> 이 목록에 없는 파일 수정 = 위반.

## 4) Acceptance criteria (#4 Few-shot)

예시 1:
```text
INPUT:  <구체 input>
OUTPUT: <기대 output>
```

예시 2:
```text
INPUT:  <edge case input>
OUTPUT: <기대 output>
```

검증:
- `python .claude/scripts/<verify>.py` PASS
- 단위 테스트 `pytest <test_path>` PASS
- `git diff --stat` 라인 수 보고

## 5) Reasoning (#5 CoT — Chain of Thought)

코드 작성 전 다음을 보고하라:

1. **영향 범위**: 이 task 가 영향 주는 함수·모듈·DB 테이블
2. **Edge cases**: 빈 입력 / 큰 입력 / 잘못된 input / 경합 / 잠금 / OS 차이
3. **룰 매핑**: 이 task 가 적용해야 할 `CLAUDE.md § 7` 금지 사항 번호 (예: § 7-4 하드 경로)
4. **의존성**: 다른 plugin / skill / hook 영향
5. **Rollback**: 실패 시 되돌리기 전략 (`.bak` / git stash / git revert)

## 6) Negative constraints (#2 Negative prompting)

DO NOT:
- `?.` optional chaining 사용 (§ 7-5)
- 하드코딩 path · 사용자명 · Python 버전 (§ 7-4) — `os.environ['TEMP']` / `Path.home()` / `where python` 사용
- 코드 주석에 "owner" 단어 (§ 7-6)
- 코드 주석에 변경 이유·티켓 번호·작성자 (§ 본문 — well-named identifiers + commit message)
- `.claude/` 직접 편집 (§ 7-7) — sync 가 덮어씀
- 빈 task `done/` 이동 (§ 7-8 위장 완료)
- 검증 못 한 사실 단정 — `failure-mode.md` 따름
- `npm view` 검증 없이 npm 패키지 명령 작성 (§ 7-9)
- 전수조사 위반 (§ 7-10) — 샘플 1~2개로 단정 X
- "사용자가 X 해주세요" 노동 떠넘김 (§ 7-11) — 자동 우회

## 7) ReAct loop (#10 — 도구 사용 시)

이 task 가 Bash·Read·WebFetch 같은 도구 쓰면 format:

```text
Thought: <다음 단계 추론>
Action: <tool name>(<arg>)
Observation: <tool result>
... (반복)
Final: <결과 요약 + 변경 stat>
```

## 8) 완료 검증 (post-codex-verify 호환)

작업 끝나면 다음을 **반드시** 자동 실행:

1. `git status` 확인
2. `git add -A`
3. `git diff --cached --stat` 출력
4. **변경 0 라인이면** report 에 `[HALLUCINATION SUSPECTED]` 표시 (보고만 하고 commit 안 함)
5. 변경 있으면 commit 메시지:
   ```text
   <type>(<scope>): <slug> [auto-verify]

   Summary:
   <한 줄 요약>

   Actual changes:
   <git stat 출력>
   ```

6. `report.md` 에 git diff stat 첨부 + 적용한 룰 매핑

## 9) Confidence (failure-mode.md 호환)

```yaml
Evidence: <0~10>   # 직접 read 한 코드 근거
Coverage: <0~10>   # 관련 파일 다 본 상태
Recency:  <0~10>   # 같은 turn 에 확인
Total:    <min(E,C,R)>
```

- ≥ 7 = PASS
- ≤ 4 = FAIL → 부모 결정 위임 (INCONCLUSIVE)

## 10) Self-consistency (#8 — 비싼 결정만)

이 task 가 **보안 / DB 마이그레이션 / money / 비가역 작업** 이면:
- N=3 샘플 생성 (temp=0.7)
- 다수결로 final 결정
- 의견 갈리면 INCONCLUSIVE → Claude 부모로 에스컬레이션

---

## 빠른 wrapper (Bash)

```bash
SLUG="my-task"
cat > .claude/tasks/task-${SLUG}.md <<'EOF'
# Task: my-task
... (위 template 복사)
EOF
```

## 참조

- skill: `plugins/exec_orch/skills/prompt-techniques.md`
- 검증: `plugins/exec_orch/skills/post-codex-verify.md`
- 라우팅: `plugins/exec_orch/skills/route_dispatch.md`
- 거절 룰: `.claude/rules/failure-mode.md`
- 금지 23: `CLAUDE.md § 7`
