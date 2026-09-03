#!/usr/bin/env bash
# WebSearch 자동 발동 트리거 감지 (UserPromptSubmit)
# 근거: .claude/rules/auto-websearch.md
set -eu

# guard: kit 프로젝트에서만
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

# stdin 에서 사용자 프롬프트 받기
PROMPT="$(cat)"

# 트리거 어휘 (한/영 - 정규식)
TRIGGERS='최신|신기능|신기술|changelog|릴리스|릴리즈|업데이트|얼마|응시료|가격|출시|발표|공개|요즘|트렌드|동향|화제|Opus 5|Sonnet 5|GPT-5|Gemini 3|Llama 4|Claude Code v2|어떤 게 좋|비교|vs'

if echo "$PROMPT" | grep -qE "$TRIGGERS"; then
  # additionalContext 로 systemMessage 주입
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "[SIG] WebSearch 자동 발동 권장 - auto-websearch.md 룰 트리거 감지 (최신 정보-모델-가격-비교 등). WebSearch tool 로 확인 후 답변하세요. 출처 명시 필수."
  }
}
EOF
fi

exit 0
