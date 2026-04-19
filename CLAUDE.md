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
- 로컬 워커 수: `.claude/orca-workers-config.json` (codex=4, gemini=2, claude=2)
- **전역 워커 상한**: `~/.claude/orca/workers-config.json` (`max_workers`) — 여러 프로젝트에서 동시에 `/exec_orch` 써도 총량 상한 적용
- 종료: `/orcauto-stop` 또는 Claude 종료 후 5분
- 상세: `.claude/skills/exec_orca-auto.md`

---

## 전역 오케스트레이션 (멀티 프로젝트)
- 진입점: `orca-dispatch <task_file> [codex|gemini|claude]` → `~/.claude/orca/tasks/` 로 태스크 투입
- 워커: `codex-auto-global`, `gemini-auto-global` — 전역 큐 폴링, 태스크 frontmatter의 `project_root` 로 cd 후 실행
- 상한: `~/.claude/orca/workers-config.json` 의 `max_workers.codex`(=4) 등 — 프로젝트 수와 무관하게 전역 N개
- 중단: `touch ~/.claude/orca/stop`
- 상세: `plugins/exec_orch/skills/route_dispatch.md` § Step 4

---

## AI 역할

| 태스크 | AI | 방법 |
|--------|-----|------|
| 설계·판단·승인 | Claude | 직접 |
| 코드 500줄+ | Codex | `task-instruction.md` → `codex-auto` |
| 코드 보완 | Claude | Codex 결과 위에 직접 |
| 검증·문서화 | Gemini | `gemini-auto` |
| PPT·디자인 | Claude | Gamma/Canva/Figma MCP |

라우팅 자동 결정: `plugins/exec_orch/skills/route_dispatch.md` (원본) → sync 후 `.claude/skills/route_dispatch.md` 로드됨

---

## 검색 규칙
라이브러리·에러·최신 정보 → **WebSearch 먼저** (내장, MCP 불필요)
npm·GitHub 문서 특화 → context7 MCP 병행

---

## 핵심 경로

**소스 오브 트루스 규칙**: `plugins/` 가 원본, `.claude/` 는 sync 결과물.
커맨드·스킬 편집은 `plugins/<name>/` 에서만. `.claude/` 직접 수정 금지 (sync시 덮어씀).
동기화: `bash .claude/scripts/sync-plugins.sh` (dry run: `--dry`)

| 경로 | 용도 | 편집 |
|------|------|------|
| `plugins/` | **원본** — 사용자 커스텀 플러그인 (14개) | ✅ 여기만 |
| `.claude/commands/` | sync 결과물 — 슬래시 커맨드 | ❌ 자동 생성 |
| `.claude/skills/` | sync 결과물 — 38개 레거시 + 플러그인 skill | ❌ 자동 생성 |
| `.claude/agents/` | agent-01~06 | ✅ |
| `.claude/hooks/` | hook 명세 + 실행 스크립트 + hooks.json | ✅ |
| `.claude/scripts/` | codex-auto, gemini-auto, sync-plugins, orca-dispatch | ✅ |
| `.claude/tasks/` | task-instruction.md, locks/, done/ | 자동 |
| `.claude/state/` | 상태 파일 | 자동 |
| `~/.claude/orca/` | **전역 큐** (멀티 프로젝트 공유) | 자동 |
| `.claude-plugin/` | plugin.json 메타 + migration-map.md | ✅ |
| `guide.txt` | 전체 사용 가이드 | ✅ |

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
`.claude/skills/exec_orca-auto.md` (원본: `plugins/exec_orch/`)
`.claude/skills/state_session.md` (원본: `plugins/exec_orch/`)
`.claude/skills/route_dispatch.md` (원본: `plugins/exec_orch/`)
→ 전체 목록: `guide.txt` § Loading Order

## 플러그인 편집 → 배포 플로우
```bash
# 1. plugins/ 에서 편집
vim plugins/exec_orch/commands/godmode.md

# 2. dry-run으로 변경 미리보기
bash .claude/scripts/sync-plugins.sh --dry

# 3. 실제 sync
bash .claude/scripts/sync-plugins.sh

# 4. 커밋 (plugins/ + .claude/ 둘 다 포함)
git add plugins/ .claude/
git commit -m "..."
```
