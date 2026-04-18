#!/bin/bash
# Hook: PreToolUse — Edit|Write 차단
# config.py, settings.json, main.py 등 핵심 파일 보호
# codex/gemini가 실수로 수정/삭제하는 것 방지

INPUT=$(cat)
TOOL=$(echo "$INPUT" | grep -o '"tool_name":"[^"]*"' | head -1 | cut -d'"' -f4)
FILE=$(echo "$INPUT" | grep -o '"file_path":"[^"]*"' | head -1 | cut -d'"' -f4)

# 보호 대상 파일 패턴
# 주: .claude/settings.json·settings.local.json 은 Claude 본인이 관리하므로 제외.
#     (codex/gemini 는 외부 프로세스이므로 이 훅을 거치지 않음 — 워커 보호엔 영향 없음)
PROTECTED_FILES=(
  "config.py"
  "settings.json"
  "main.py"
  ".env"
  ".env.local"
  "deploy-config.env"
)

# 루트 settings.json 만 매치하고, .claude/settings.json 은 통과시키기 위한 가드
# (아래 basename 매칭에서 둘 다 "settings.json"으로 잡히므로 경로로 구분)
# Windows JSON 경로는 \\ 이중 백슬래시로 올 수 있으므로 // 와 / 둘 다 흡수
if [ -n "$FILE" ]; then
  NORM=$(echo "$FILE" | sed -e 's|\\\\|/|g' -e 's|\\|/|g' -e 's|//|/|g')
  case "$NORM" in
    */.claude/settings.json|*/.claude/settings.local.json|.claude/settings.json|.claude/settings.local.json)
      exit 0
      ;;
  esac
fi

if [ -z "$FILE" ]; then
  exit 0
fi

BASENAME=$(basename "$FILE")
RELPATH=$(echo "$FILE" | sed 's|\\|/|g')

for PATTERN in "${PROTECTED_FILES[@]}"; do
  if [[ "$BASENAME" == "$PATTERN" ]] || [[ "$RELPATH" == *"$PATTERN"* ]]; then
    echo "BLOCKED: $BASENAME is a protected file. Do not modify."
    exit 2
  fi
done

exit 0
