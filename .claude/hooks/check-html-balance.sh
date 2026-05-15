#!/usr/bin/env bash
# PostToolUse Edit|Write hook — HTML tag balance + <script> 안 brace 짝 검사
# Quick lint (grep 기반, 외부 의존 0)
set +e

INPUT="$(cat)"

if command -v jq >/dev/null 2>&1; then
  FILE_PATH="$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')"
else
  FILE_PATH="$(echo "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+' | head -1 | sed 's/.*"\([^"]*\)$/\1/')"
fi

[ -f "$FILE_PATH" ] || exit 0

case "$FILE_PATH" in
  *.html|*.htm) ;;
  *) exit 0 ;;
esac

# <script> 블록 추출 후 brace/paren balance
SCRIPT_CONTENT="$(awk '/<script[^>]*>/,/<\/script>/' "$FILE_PATH" | grep -v '<script\|</script>')"

# 단순 count — opening vs closing
OPEN_BRACE=$(echo "$SCRIPT_CONTENT" | tr -cd '{' | wc -c)
CLOSE_BRACE=$(echo "$SCRIPT_CONTENT" | tr -cd '}' | wc -c)
OPEN_PAREN=$(echo "$SCRIPT_CONTENT" | tr -cd '(' | wc -c)
CLOSE_PAREN=$(echo "$SCRIPT_CONTENT" | tr -cd ')' | wc -c)

WARN=""
if [ "$OPEN_BRACE" -ne "$CLOSE_BRACE" ]; then
  WARN="$WARN\n  - <script> brace 불균형: { $OPEN_BRACE / } $CLOSE_BRACE"
fi
if [ "$OPEN_PAREN" -ne "$CLOSE_PAREN" ]; then
  WARN="$WARN\n  - <script> paren 불균형: ( $OPEN_PAREN / ) $CLOSE_PAREN"
fi

# HTML tag balance — 단순 매칭 (script/style 제외 후)
HTML_BODY="$(grep -v '<script\|</script>\|<style\|</style>' "$FILE_PATH" 2>/dev/null)"
# self-closing tags (br, hr, img, input, meta, link) 제외
for tag in div span p ul ol li table tr td th tbody thead nav header footer section article main aside form; do
  OPEN=$(echo "$HTML_BODY" | grep -oE "<${tag}[ >/]" | wc -l)
  CLOSE=$(echo "$HTML_BODY" | grep -oE "</${tag}>" | wc -l)
  DIFF=$((OPEN - CLOSE))
  if [ "$DIFF" -gt 2 ] || [ "$DIFF" -lt -2 ]; then
    # 2 이상 차이만 보고 (template literal 등 false positive 완화)
    WARN="$WARN\n  - <$tag> 불균형: 열린 $OPEN / 닫은 $CLOSE"
  fi
done

if [ -n "$WARN" ]; then
  BASE="$(basename "$FILE_PATH")"
  cat <<EOF
{"systemMessage": "[html-balance] $BASE — tag/brace 불균형 의심:$WARN\n수동 검토 권장."}
EOF
fi
exit 0
