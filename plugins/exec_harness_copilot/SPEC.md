# exec_harness_copilot (spec-only)

> **목적**: orchestration_v1 task 를 GitHub Copilot CLI 에 위임 — multi-harness 확장.
> **근거**: `docs/2026-06-16/tooling-comparison.md` §  wshobson/agents 패턴.
> **상태**: spec-only — 사용자 진행 결정 후 stable.

## 활용 시점

- 사용자가 GitHub Copilot 구독 중 (개인 또는 enterprise)
- GitHub-native workflow (issue → PR → review) 자동화 필요
- Codex CLI 와 별도 비용 회피

## 명령 (예정)

| 명령 | 동작 |
|---|---|
| `/copilot-dispatch <task>` | task-instruction.md → `gh copilot` 호출 |
| `/copilot-suggest <file>` | inline 자동 보완 |
| `/copilot-pr-review <pr>` | GitHub Copilot PR review 트리거 |

## 의존성

- `gh` CLI 설치 + `gh extension install github/gh-copilot`
- `GITHUB_TOKEN` (Copilot 권한 포함)
- `exec_orch` (task-instruction 표준)

## 다음 단계

- 사용자 활성화 결정 시:
  1. `gh copilot` 명령 출력 형식 검증
  2. status → `experimental`
  3. commands/ 구현
  4. CLAUDE.md § 3.2 라우팅 표 행 추가 (저비용 검증/리뷰용)
