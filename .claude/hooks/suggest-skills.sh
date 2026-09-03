#!/usr/bin/env bash
# 사용자 프롬프트 -> 관련 skill-command-rule 자동 추천 (UserPromptSubmit)
# 근거: 2026-09-02 사용자 지시 — "내가 지시하면 뭐가 좋은지 확인한 다음에 skill 이든 뭐든 알려주는 알림으로 해"
set -eu

# guard
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
PROMPT="$(cat)"

# 소문자화 (매칭용)
LOWER=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]')

# 카테고리 -> skill/command 매핑
declare -A MATCH
matches=""

# PPT/슬라이드/발표
if echo "$LOWER" | grep -qE "ppt|슬라이드|프레젠테이션|발표자료|deck"; then
  matches="$matches\n  - /ppt-make - plugins/design_ppt/ (기업 PPT 자동)"
fi
# 문서/워드/docx
if echo "$LOWER" | grep -qE "docx|워드|word|보고서|리포트|report"; then
  matches="$matches\n  - plugins/design_web/ - docx 빌더 스킬"
fi
# Excel/xlsx
if echo "$LOWER" | grep -qE "엑셀|excel|xlsx|스프레드시트"; then
  matches="$matches\n  - plugins/data_excel/ - xlsx 스킬"
fi
# 감사/audit
if echo "$LOWER" | grep -qE "감사|audit|조서|증적|점검"; then
  matches="$matches\n  - plugins/audit_* - auto-planner skill"
fi
# 신사업/kpi
if echo "$LOWER" | grep -qE "신사업|kpi|사업기획|사업안|비즈니스"; then
  matches="$matches\n  - docs/kpi-*.docx 참조 - 8 track 산업 매트릭스"
fi
# 계산기/UI/화면
if echo "$LOWER" | grep -qE "계산기|화면|ui|디자인|만들어줘|앱"; then
  matches="$matches\n  - .claude/rules/app-ui-standard.md (shadcn/AntD/MUI 강제)"
fi
# 최신-신기능-changelog
if echo "$LOWER" | grep -qE "최신|신기능|changelog|릴리스|업데이트|가격|응시료"; then
  matches="$matches\n  - WebSearch 자동 (auto-websearch.md rule)"
fi
# 배포/install/setup
if echo "$LOWER" | grep -qE "배포|deploy|install|setup|배치"; then
  matches="$matches\n  - setup/setup.bat - install 순서 (kit->commit->sync->install->검증)"
fi
# commit/git
if echo "$LOWER" | grep -qE "커밋|commit|push|git"; then
  matches="$matches\n  - guide.txt + CLAUDE.md + settings.json 3-set 준수"
fi
# 감정: 답답/짜증/짱나
if echo "$LOWER" | grep -qE "답답|짜증|짱나|엉망|대충|장난"; then
  matches="$matches\n  - fast mode - 시스템 결함 진단 5단계 (user-emotion.md)"
fi
# 전수조사/전부/모든
if echo "$LOWER" | grep -qE "전수조사|모든|다|전부|100"; then
  matches="$matches\n  - Explore agent 병렬 dispatch (subagent-delegation.md)"
fi
# 검증/테스트/smoke
if echo "$LOWER" | grep -qE "검증|smoke|테스트|test|확인"; then
  matches="$matches\n  - smoke-test-screen.sh - verify-*.py (screen-verify.md)"
fi
# DB
if echo "$LOWER" | grep -qE "\bdb\b|데이터베이스|sqlite|테이블|orca"; then
  matches="$matches\n  - .claude/state/orca.db - kit-stats.py db"
fi
# 통계-시각-dashboard
if echo "$LOWER" | grep -qE "통계|시각|dashboard|현황|상태|보여"; then
  matches="$matches\n  - kit-stats.py all - kit-view.bat - dashboard.html"
fi
# 재사용/이력/기억
if echo "$LOWER" | grep -qE "재사용|이력|기억|이전|저장|어떻게 했"; then
  matches="$matches\n  - save_solution.py search - problem_solutions DB - lookup-rule.py"
fi
# 파일 관리
if echo "$LOWER" | grep -qE "파일 정리|이름|명명|중복|백업|삭제"; then
  matches="$matches\n  - production-file-management.md - file-naming.md - cleanup-pollution.sh"
fi
# 파인튜닝
if echo "$LOWER" | grep -qE "파인튜닝|fine-tune|lora|qlora|학습|train"; then
  matches="$matches\n  - .claude/skills/ai-finetune-pipeline.md"
fi

# 매치 있으면 systemMessage 주입 + 자동 실행 명령
# [2026-09-03] 이모지 ([TGT] - -) 제거 + python -X utf8 강제 -> CP949 surrogate 방지
if [ -n "$matches" ]; then
  MSG=$(printf "%b" "[SUGGEST] 관련 skill/tool 자동 활성 (즉시 실행):${matches}\n\n(위 skill/rule 은 지금 즉시 반영-실행. Skill tool 로 호출 가능한 것은 바로 Skill 호출.)")
  ESC=$(python -X utf8 -c "import json,sys; print(json.dumps(sys.stdin.read()))" <<< "$MSG")
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": ${ESC}
  }
}
EOF
fi

# log
mkdir -p "$ROOT/.claude/logs"
n_match=$(echo -e "$matches" | grep -c "-" || echo 0)
echo "[$(date -Iseconds)] matches=$n_match prompt=$(echo "$PROMPT" | head -c 80)" >> "$ROOT/.claude/logs/suggest-skills.log"

exit 0
