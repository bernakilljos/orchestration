#!/usr/bin/env bash
# detect-asset-creation.sh — PreToolUse Write hook
# 목적: 새 자산 (rule/hook/skill/command/agent) 생성 시 자동 감지 -> 유사 파일 grep -> 자매 파일 유형 검사
# 근거: .claude/rules/consistency.md § 함수-훅-룰 중복 금지 - feedback_no_duplicate_function
set -e

INPUT="$(cat)"
if command -v jq >/dev/null 2>&1; then
  TOOL="$(echo "$INPUT" | jq -r '.tool_name // ""' 2>/dev/null)"
  PATH_ARG="$(echo "$INPUT" | jq -r '.tool_input.file_path // ""' 2>/dev/null)"
else
  TOOL="$(echo "$INPUT" | grep -oE '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*: *"\(.*\)"$/\1/')"
  PATH_ARG="$(echo "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*: *"\(.*\)"$/\1/')"
fi

# Write tool 만 대상 (Edit 는 기존 파일 수정)
[ "$TOOL" = "Write" ] || exit 0
[ -z "$PATH_ARG" ] && exit 0

# 이미 존재하는 파일 = 덮어쓰기, skip
[ -f "$PATH_ARG" ] && exit 0

PROJECT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
BASENAME="$(basename "$PATH_ARG")"
STEM="${BASENAME%.*}"
EXT="${BASENAME##*.}"

# 자산 유형 판정
kind=""
case "$PATH_ARG" in
  */.claude/rules/*.md|*/rules/*.md)                 kind="rule" ;;
  */.claude/hooks/*.sh|*/hooks/*.sh)                  kind="hook_bash" ;;
  */.claude/hooks/*.ps1|*/hooks/*.ps1)                kind="hook_ps" ;;
  */.claude/hooks/*.py|*/hooks/*.py)                  kind="hook_python" ;;
  */.claude/hooks/*.md|*/hooks/*.md)                  kind="hook_spec" ;;
  */.claude/skills/*.md|*/skills/*.md)                kind="skill" ;;
  */.claude/commands/*.md|*/commands/*.md)            kind="command" ;;
  */.claude/agents/*.md|*/agents/*.md)                kind="agent" ;;
  *memory/feedback_*.md)                              kind="memory_feedback" ;;
  *memory/reference_*.md)                             kind="memory_reference" ;;
  *) exit 0 ;;
esac

# 유사 파일 grep
dup_files=""
similar_files=""
case "$kind" in
  rule)
    similar_files="$(find "$PROJECT/.claude/rules" -name "*${STEM}*" -o -name "*${STEM%-*}*" 2>/dev/null | grep -v "$PATH_ARG" | head -3)"
    ;;
  hook_bash|hook_ps|hook_python|hook_spec)
    similar_files="$(find "$PROJECT/.claude/hooks" "$PROJECT/plugins" -name "*${STEM}*" 2>/dev/null | grep -v "$PATH_ARG" | head -5)"
    ;;
  skill|command|agent)
    similar_files="$(find "$PROJECT/.claude" "$PROJECT/plugins" -type d \( -name skills -o -name commands -o -name agents \) -prune -o \
                     -name "*${STEM}*" -print 2>/dev/null | grep -v "$PATH_ARG" | head -5)"
    ;;
  memory_feedback|memory_reference)
    MEM_DIR="$HOME/.claude/projects/$(basename "$PROJECT" | tr '_' '-')/memory"
    similar_files="$(find "$MEM_DIR" -name "*${STEM#feedback_}*" -o -name "*${STEM#reference_}*" 2>/dev/null | grep -v "$PATH_ARG" | head -3)"
    ;;
esac

# 자매 파일 검사 (bash ↔ PowerShell)
sibling_warn=""
if [ "$kind" = "hook_bash" ]; then
  ps1_path="${PATH_ARG%.sh}.ps1"
  [ ! -f "$ps1_path" ] && sibling_warn="PowerShell 자매 미존재: $ps1_path (Windows 사용자 대비)"
elif [ "$kind" = "hook_ps" ]; then
  sh_path="${PATH_ARG%.ps1}.sh"
  [ ! -f "$sh_path" ] && sibling_warn="bash 자매 미존재: $sh_path (Linux/Mac 사용자 대비)"
fi

# systemMessage warn (block X — 경고만)
msg="[자산 감지] 유형: $kind - 신규: $BASENAME"
[ -n "$similar_files" ] && msg="$msg\\n\\n[WARN] 유사 자산 존재:\\n$(echo "$similar_files" | sed 's/^/  - /' | tr '\\n' '_' | sed 's/_/\\\\n/g')\\n\\n-> 기존 확장 검토 (consistency.md § 함수-훅-룰 중복 금지)"
[ -n "$sibling_warn" ] && msg="$msg\\n\\n[WARN] $sibling_warn"
msg="$msg\\n\\n워크플로우: plugins/exec_orch/skills/asset-creation-workflow.md"

cat <<EOF
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"$msg"}}
EOF
exit 0
