---
name: web-cli-dialogue-workflow
description: CLI (kit·개발 실행 담당) ↔ claude.ai Web (실운영 판정·감사 담당) 왕복 대화 워크플로우. 애매·감사 판정 필요 시 CLI 가 질문 문안 만듬 → 사용자 web 에 붙임 → web 답 → 사용자 CLI 에 붙임 → 진행. 사용자 = 클립보드 릴레이만. 완전 자동은 Chrome Extension 필요.
---

# Web ↔ CLI 왕복 대화 워크플로우

두 세션이 각자 역할 담당 · 애매한 것은 서로 물어봐서 답 받음. 사용자는 클립보드 릴레이만.

## 역할 분담

| 세션 | 담당 | 예 |
|---|---|---|
| **CLI (여기, orchestration_v1)** | kit 편집·개발 실행·자산 등재·commit·install·subagent 실행 | 룰 추가·hook 등재·sync·target 배포 |
| **claude.ai Web develop** | 실운영 판정·감사·리스크·비즈니스 결정·설계 승인 | 닷넷 7-4 캡·dashboard 리팩터 순서·감사 관점 |

## 왕복 대화 트리거 (CLI → Web 질문)

CLI 가 다음 상황에 develop 질문 문안 자동 생성:
- 감사 관점 판정 필요 (예: 캡 초과 · 미흡 등급)
- 실운영 리스크 결정 (예: 프로덕션 배포 · 데이터 마이그레이션)
- 비즈니스 우선순위 판단 (예: 리팩터 순서 · 스코프 축소)
- 사용자 개인 도메인 지식 필요 (ISMS-P · RMS · ITCEN ESG 조직 컨텍스트)
- kit 자체와 무관한 실운영 프로젝트 결정

## 질문 문안 표준 형식

CLI 가 이 형식으로 만들어서 사용자에게 제공:

```markdown
### develop 에 붙일 질문 (v_YYYY-MM-DD_HH:MM)

**Context**: [상황 1~2줄]
**Options**: [옵션 A / B / C · 각 1줄]
**Trade-off**: [옵션별 장단점 표]
**Blocker**: [지금 왜 CLI 가 판정 못 하는지 1줄]
**Ask**: [원하는 답 형식 — yes/no · 옵션 번호 · 순서 등]
```

## 답 수신 (Web → CLI)

사용자가 develop 답 붙이면 CLI:
1. 답 파일 저장 (`.claude/state/dialogue/<timestamp>.md` — 대화 이력)
2. 답 반영해서 실행 (kit 편집·commit·배포 등)
3. 완료 보고

## 대화 이력 저장

`.claude/state/dialogue/`:
- `<timestamp>-q.md` — CLI 가 만든 질문
- `<timestamp>-a.md` — Web 이 준 답
- 다음 세션에서 [[dialogue-history]] recall 가능

## 완전 자동은 언제

| 방식 | 자동성 | 개발 필요 |
|---|---|---|
| **수동 클립보드** (지금 유일) | 사용자 릴레이 | X |
| **파일 브릿지** (`~/.claude/orca/`) | 사용자 저장 | X (kit 이미 있음) |
| **Managed Agents API** | 자체 UI · web claude.ai 아님 | Python·Node SDK 코드 |
| **Chrome Extension** | web 브라우저 자동 | 확장 프로그램 개발 |
| **Playwright 로 claude.ai 조작** | ⚠️ ToS 위반 소지 | 권장 X |

지금 = 수동 릴레이가 유일 . Chrome Extension 이 미래 진짜 자동화.

## 금지

1. CLI 가 자체 판단 가능한데 develop 에 물어봄 (사용자 개입 유발)
2. develop 판정 대신 CLI 가 실운영 결정 (역할 침범)
3. 대화 이력 저장 skip (recall 손실)
4. 질문 문안 없이 그냥 "물어봐 주세요"

## 관련

- `outputs/install/web-cli-bridge.md` (4 방식 상세)
- `outputs/install/session-bootstrap-prompt.md` (develop project 세팅)
- `.claude/rules/direction-first.md` (대상 4갈래 · CLI vs Web)
- `feedback_confirm_target_first` · [[reference_claude_web_projects_setup]]
