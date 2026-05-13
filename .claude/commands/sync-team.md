---
description: "orchestration_v1 → orchestration_v1_team 인프라 동기화 (commands/skills/agents/hooks/plugins/setup)"
allowed-tools: Bash(bash:*)
---

# /sync-team — Team 폴더 동기화

orchestration_v1 (인프라 본체) 의 변경을 orchestration_v1_team (팀 사용자용) 으로 복사.

## 실행
```bash
bash .claude/scripts/sync-to-team.sh
# 또는 다른 폴더 지정:
bash .claude/scripts/sync-to-team.sh C:/pjt/some_team_copy
```

## 복사 대상
- `.claude/` (commands, skills, agents, hooks, scripts, rules, settings.json)
- `plugins/` (모든 플러그인)
- `.claude-plugin/` (manifest)
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `guide.txt`
- `install.bat`, `install_codex.bat/.ps1`, `install_gemini.bat/.ps1`
- `setup/` (setup 모듈 + setup.iss)

## 제외
- `.git/`, `node_modules/`
- `*.pptx`, `*.png` (대용량)
- `docs/ini/` (PAT 등 시크릿)
- `.claude/state/`, `.claude/tasks/locks|done/`, `.claude/context-cache/`
- `.claude_backup_*/`

## 사용 시점
- 인프라 (commands/hooks/plugins) 변경 후 팀 폴더 반영
- install.bat / setup 흐름 fix 후
- guide.txt 현행화 후

## 자동화 (선택)
`.claude/settings.json` Stop hook 에 등록 가능 (매 응답 끝마다 sync) — 단 부하 고려.
