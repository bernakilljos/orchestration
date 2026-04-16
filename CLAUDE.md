# CLAUDE.md — Multi-AI Orchestration Kit v3

## Role
Team Lead. Design, judge, approve, implement directly when needed.
→ Details: `guide.txt`

---

## Session Start (순서 고정)
1. **Orca Auto** — `.claude/skills/exec_orca-auto.md` 실행
2. **First-Run** — `docs/CLAUDE_SETUP_GUIDE.md` 존재 시 읽고 처리 후 삭제
3. **Resume** — `.claude/context-cache/session-snapshot.md` 존재 시 복구 제안

---

## Orca Auto 규칙
- 활성 조건: `.claude/orca-enabled` 있고 `.claude/orca-stopped` 없음
- 워커 수: `.claude/orca-workers-config.json` (codex=4, gemini=2, claude=3)
- 종료: `/orcauto-stop` 또는 Claude 종료 후 5분
- 상세: `.claude/skills/exec_orca-auto.md`

---

## AI 역할

| 태스크 | AI | 방법 |
|--------|-----|------|
| 설계·판단·승인 | Claude | 직접 |
| 코드 500줄+ | Codex | `task-instruction.md` → `codex-auto` |
| 코드 보완 | Claude | Codex 결과 위에 직접 |
| 검증·문서화 | Gemini | `gemini-auto` |
| PPT·디자인 | Claude | Gamma/Canva/Figma MCP |

라우팅 자동 결정: `.claude/skills/route_dispatch.md`

---

## 검색 규칙
라이브러리·에러·최신 정보 → **WebSearch 먼저** (내장, MCP 불필요)
npm·GitHub 문서 특화 → context7 MCP 병행

---

## 핵심 경로

| 경로 | 용도 |
|------|------|
| `.claude/skills/` | 38개 레거시 + exec_/state_/route_ 신규 |
| `.claude/agents/` | agent-01~06 |
| `.claude/commands/` | 슬래시 커맨드 (plug_*, check-*, vibe-loop 등) |
| `.claude/hooks/` | hook 명세 + 실행 스크립트 + hooks.json |
| `.claude/scripts/` | codex-auto, gemini-auto, deploy 등 |
| `.claude/tasks/` | task-instruction.md, locks/, done/ |
| `.claude/state/` | 상태 파일 (신규) |
| `.claude-plugin/` | plugin.json 메타 + migration-map.md |
| `plugins/` | 사용자 커스텀 플러그인 (→ guide.txt 참조) |
| `guide.txt` | 전체 사용 가이드 |

---

## 금지 사항
1. task-instruction.md 없이 Codex 호출
2. Gemini 리뷰 자동 채택 (Claude가 결정)
3. 같은 파일 동시 수정 (Writer=1)
4. 하드코딩 (API 키, 경로, 시크릿)
5. optional chaining (`?.`) 사용
6. 코드 주석에 "owner(주인)" 사용

---

## 태스크 파일 규칙
- 저장 위치: `.claude/tasks/task-*.md` 만 (다른 곳 저장 시 워커가 못 읽음)
- 경로: 반드시 상대경로 (절대경로 금지)

---

## 문서 저장 규칙
생성 문서 → `docs/YYYY-MM-DD/파일명.md`

---

## Loading Order
`.claude/hooks/hook-00-init.md` ~ `.claude/skills/skill-38-token-watchdog.md`
`.claude/skills/exec_orca-auto.md`
`.claude/skills/state_session.md`
`.claude/skills/route_dispatch.md`
`plugins/exec_voice/skills/` (음성 처리)
`plugins/exec_learning/skills/` (학습·메모리)
→ 전체 목록: `guide.txt` § Loading Order
