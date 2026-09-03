#!/usr/bin/env bash
# pre-compact-rules-reminder.sh — compact 직전 핵심 규칙 systemMessage 주입
# 목적: compact 후에도 Claude가 규칙을 잊지 않도록
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

cat <<'RULES'

[RED] [COMPACT 직전 규칙 리마인드 — 절대 잊지 마]

1. git commit 시 guide.txt + CLAUDE.md + settings.json + BUILD.md 같이 stage
2. 플러그인/hook/스크립트 변경 -> 관련 문서 전부 같이 갱신
3. 도메인별 레퍼런스 X -> 공통 도구 보강
4. 사용자가 카테고리만 말하면 -> 알아서 세부 조사+추가
5. 매번 sync-plugins.sh + auto-update-stats.sh 실행
6. 물어보지 말고 바로 실행 (Zero-touch)
7. pre-commit-full-check.sh 가 차단하므로 guide.txt 빠뜨리면 commit 실패

RULES

exit 0
