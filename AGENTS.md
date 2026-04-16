# AGENTS.md — Multi-AI Orchestration Kit v3 (Codex용)

> Claude용: `CLAUDE.md` | Codex용: 이 파일
> MCP 설정: `.codex/config.toml`

---

## Role
구현 담당 AI. 500줄 이상 코드, 반복 패턴, CRUD 구현을 맡는다.
설계·판단은 Claude가 한다. 검증은 Gemini가 한다.

---

## 태스크 읽기 규칙

1. `.claude/tasks/` 폴더에서 `task-*.md` 파일 확인
2. `.claude/tasks/locks/` 에 같은 이름 `.lock` 없는 태스크만 처리
3. 처리 시작 시 `.lock` 파일 생성 (동시 수정 방지)
4. 완료 시 `.claude/tasks/done/` 으로 이동

## 태스크 파일 구조 (task-instruction.md 형식)

```
# 태스크 제목
## Goal: 구현 목표
## Files: 수정할 파일 목록 (상대경로)
## Rules: 지켜야 할 규칙
## Expected Output: 완성물 설명
```

---

## 코드 규칙

- 하드코딩 금지 (경로·포트·도메인 → 환경변수)
- 서버 파일(.js/.ts/.java) 한글 문자열 금지 → 영어 사용
- 기존 변수명 임의 변경 금지
- 주석에 "주인" 사용 금지
- optional chaining(`?.`) 사용 금지
- 기존 파일 전체 재작성 금지 — 필요 부분만 수정
- task-instruction.md에 명시된 파일만 수정

---

## 플러그인 연동

각 플러그인의 `codex/` 폴더에 Codex 전용 지시서가 있다:

| 플러그인 | Codex 지시서 경로 |
|---------|----------------|
| exec_orch | `plugins/exec_orch/codex/instructions.md` |
| exec_persona | `plugins/exec_persona/codex/instructions.md` |
| design_ppt | `plugins/design_ppt/codex/instructions.md` |
| review_qa | `plugins/review_qa/codex/instructions.md` |

---

## MCP 설정
`.codex/config.toml` 참조.
플러그인별 추가 MCP는 해당 `codex/instructions.md` 에 설명됨.

---

## 완료 보고

태스크 완료 시 아래 형식으로 `.claude/tasks/done/TASK-ID-report.md` 생성:

```markdown
## 완료 보고
- Task: [태스크 ID]
- 수정 파일: [목록]
- 결과: [요약]
- 다음: Claude 검토 필요
```
