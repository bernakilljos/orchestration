#!/usr/bin/env bash
# inject-user-style.sh — SessionStart hook · user_style_profile.md 핵심 축을 systemMessage 로 주입
# 매 세션 첫 응답 전에 Claude 가 사용자 스타일 즉시 인지
# Zero-touch · 사용자 액션 요구 X · 1회 세션당 1회 (throttle)
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
# 3-tier fallback: 프로젝트 state (install-to 자동 전파) → setup/templates (git-tracked SoT) → user memory
PROFILE="$PROJECT_DIR/.claude/state/user_style_profile.md"
[ -f "$PROFILE" ] || PROFILE="$PROJECT_DIR/setup/templates/user_style_profile.md"
# Claude Code 프로젝트 폴더명 = cwd 의 영숫자 외 문자를 '-' 로 (statusline cwd_to_proj_dir 와 동일 규칙)
WIN_DIR="$(cygpath -w "$PROJECT_DIR" 2>/dev/null || echo "$PROJECT_DIR")"
MEM_DIR="$HOME/.claude/projects/$(printf '%s' "$WIN_DIR" | python -X utf8 -c "import re,sys;print(re.sub(r'[^a-zA-Z0-9]','-',sys.stdin.read().strip()))" 2>/dev/null)/memory"
[ -f "$PROFILE" ] || PROFILE="$MEM_DIR/user_style_profile.md"
STATE="$PROJECT_DIR/.claude/state/inject-user-style.last"

# Throttle · 세션당 1회 (12시간 기준)
if [ -f "$STATE" ]; then
  AGE_HOURS=$(( ($(date +%s) - $(stat -c %Y "$STATE" 2>/dev/null || stat -f %m "$STATE" 2>/dev/null || echo 0)) / 3600 ))
  [ "$AGE_HOURS" -lt 12 ] 2>/dev/null && exit 0
fi

[ -f "$PROFILE" ] || exit 0

# Ultra-concise 10-axis header → stdout (SessionStart hook systemMessage)
cat <<'MSG'
[사용자 스타일 자동 로드 · user_style_profile.md]
① 응답: 짧고 명확 · breadth > depth · 직접 답(yes/no/숫자) → 부연 → 행동
② 톤: 한국어 default · 5살 톤 · 비유 환영 · 직진 (공손 과잉 X)
③ 디자인: 이모지 X · 여백=실패 · shadcn/AntD · SVG+화살표
④ ENFP-ADHD: spark 열어둠 · O/X 표 · 결정 강요 X · 고집 X (D8)
⑤ Zero-touch: 알림은 크리티컬 5만 · 반복 지시 받기 X · hook 로 흡수
⑥ 금기: 농땡이·거짓 PASS·회피·"확인해주세요"·v2 접미사·하드경로·중복함수
⑦ 자동 감정 대응: 답답→fast · 짜증→진단 · 반복→loop · design→command 수정
⑧ 검증: 수정 후 자동 PASS 확인 후 보고 · agent PASS 신뢰 X · raw 직접
⑨ 조사: 대상 확정 0순위 · 100% Read · 이력 먼저 · 30초 실측 > 30분 추론
⑩ 실전: 데모·목업 X (명시 시만) · install 순서 · 공통 kit · 신기능 자동 반영

전체: setup/templates/user_style_profile.md
MSG

mkdir -p "$(dirname "$STATE")"
touch "$STATE"
exit 0
