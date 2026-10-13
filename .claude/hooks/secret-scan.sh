#!/usr/bin/env bash
# PreToolUse hook — Bash git commit / push 직전 secret 스캔
# .env / API key / PAT 검출 시 차단
#
# 성능 (2026-09-02): 매 Bash 호출마다 돈다. Windows + Privacy-i(DLP) 에서 프로세스
#   생성이 300~400ms 라, git commit/push 가 아닌 명령은 서브프로세스 0개로 즉시 빠진다.
#
# 정확성 (2026-09-02 수정): 이전 fallback sed 는
#   sed 's/.*:"\(.*\)"/\1/' 가 '"command": "git commit ..."' 에서 키 이름을 남겨
#   결과가 'command": "git commit -m test' 가 됐다. 그래서 ^git commit 매치가
#   never true — jq 없는 환경(이 PC)에서 스캔이 한 번도 돌지 않았다.

read -r -d '' INPUT

# 1차 필터: bash 내장만. git commit/push 아니면 서브프로세스 0개로 종료.
case "$INPUT" in
  *'git commit'*|*'git push'*) ;;
  *) exit 0 ;;
esac

# command 값 추출 — 콜론 뒤 공백 유무 무관, bash 내장 치환만 사용
CMD="${INPUT#*\"command\":}"
CMD="${CMD#\"}"          # 공백 없는 경우
CMD="${CMD# \"}"         # 공백 있는 경우
CMD="${CMD%%\"*}"

# 실제로 git commit / push 로 시작하는지 정밀 확인
case "$CMD" in
  'git commit'*|'git push'*) ;;
  *) exit 0 ;;
esac

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"

SECRET_PATTERNS=(
  'sk-[A-Za-z0-9]{40,}'                          # OpenAI API key
  'sk-ant-[A-Za-z0-9_-]{40,}'                    # Anthropic key
  'ghp_[A-Za-z0-9]{36,}'                          # GitHub PAT
  'AKIA[0-9A-Z]{16}'                              # AWS access key
  'AIza[0-9A-Za-z_-]{35}'                         # Google API key
  'xox[baprs]-[0-9]+-[0-9]+-[A-Za-z0-9]+'         # Slack token
  'glpat-[A-Za-z0-9_-]{20,}'                      # GitLab PAT
)

STAGED="$(cd "$PROJECT_ROOT" && git diff --cached --name-only 2>/dev/null || true)"
[ -n "$STAGED" ] || exit 0

# 패턴을 한 번의 grep -E 로 합쳐 파일당 프로세스 1개만 쓴다 (이전: 파일당 7개)
ALL_PAT="$(IFS='|'; echo "${SECRET_PATTERNS[*]}")"

FOUND=""
while IFS= read -r f; do
  [ -n "$f" ] || continue
  [ -f "$PROJECT_ROOT/$f" ] || continue
  case "$f" in
    docs/ini/*) continue ;;  # 내부 ini 허용 (사용자 명시 화이트리스트)
  esac
  case "$f" in
    *.env|*.env.local|.env*|*secret*|*credentials*)
      FOUND="${FOUND} / $f (위험 파일명)"; continue ;;
  esac
  if grep -qE "$ALL_PAT" "$PROJECT_ROOT/$f" 2>/dev/null; then
    FOUND="${FOUND} / $f (secret 패턴 감지)"
  fi
done <<< "$STAGED"

if [ -n "$FOUND" ]; then
  # 개행 없이 한 줄 — permissionDecisionReason 안에 실제 개행이 들어가면 JSON 이 깨진다
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Secret 감지 — commit 차단:%s | .env / API key 제거 후 .gitignore 에 추가하고 재시도."}}\n' "$FOUND"
fi
exit 0
