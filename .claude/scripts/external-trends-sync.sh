#!/usr/bin/env bash
# external-trends-sync.sh
# 매시간 외부 트렌드 소스 (Claude doc · prompting guide · Reddit RSS · HackerNews) fetch
# → 변경 발견 시 task-instruction.md 생성 + git branch + PR.
#
# Trigger: Windows Task Scheduler 또는 CronCreate prompt
# 인스타그램 fetch 는 인증 게이트로 직접 불가 → 공개 소스로 대체:
#   - https://docs.anthropic.com/en/release-notes/claude-code
#   - https://www.promptingguide.ai/sitemap.xml
#   - https://www.reddit.com/r/PromptEngineering/.rss
#   - https://hnrss.org/newest?q=prompt+engineering

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$PROJECT_DIR" || exit 0

STATE_DIR=".claude/state/external-trends"
LOG_DIR=".claude/logs"
TASKS_DIR=".claude/tasks"
mkdir -p "$STATE_DIR" "$LOG_DIR" "$TASKS_DIR"

TS_FILE="$(date '+%Y-%m-%d_%H%M')"
TS_HUMAN="$(date '+%Y-%m-%d %H:%M:%S')"
LOG="$LOG_DIR/external-trends.log"

# 1) 소스 목록 (URL · 캐시 키)
declare -A SOURCES=(
  ["anthropic-release-notes"]="https://docs.anthropic.com/en/release-notes/claude-code"
  ["promptingguide-sitemap"]="https://www.promptingguide.ai/sitemap.xml"
  ["reddit-prompt-engineering"]="https://www.reddit.com/r/PromptEngineering/.rss"
  ["hn-prompt-engineering"]="https://hnrss.org/newest?q=prompt+engineering"
  ["anthropic-docs-prompting"]="https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview"
)

DETECTED_CHANGES=()
BASELINE_SET=()

for key in "${!SOURCES[@]}"; do
  url="${SOURCES[$key]}"
  cache_file="$STATE_DIR/${key}.sha"
  raw_cache="$STATE_DIR/${key}.raw"

  # fetch (timeout 15s)
  body=$(curl -sS --max-time 15 -L -A "Mozilla/5.0 (orchestration_v1 trends-sync)" "$url" 2>/dev/null || echo "")
  if [ -z "$body" ]; then
    echo "[$TS_HUMAN] [skip] $key — fetch failed" >> "$LOG"
    continue
  fi

  new_sha=$(echo "$body" | sha256sum | awk '{print $1}')
  old_sha=$(cat "$cache_file" 2>/dev/null || echo "")

  # 첫 실행 (cache 없음): baseline 만 저장하고 silent
  if [ -z "$old_sha" ]; then
    echo "$new_sha" > "$cache_file"
    echo "$body" > "$raw_cache"
    BASELINE_SET+=("$key")
    echo "[$TS_HUMAN] [baseline] $key (sha $new_sha)" >> "$LOG"
    continue
  fi

  if [ "$new_sha" != "$old_sha" ]; then
    # diff 추출 (기존 raw 있으면)
    diff_summary=""
    if [ -f "$raw_cache" ]; then
      diff_summary=$(diff <(echo "$body") "$raw_cache" 2>/dev/null | head -50 || echo "(diff failed)")
    fi
    # 캐시 갱신
    echo "$new_sha" > "$cache_file"
    echo "$body" > "$raw_cache"

    DETECTED_CHANGES+=("$key")
    echo "[$TS_HUMAN] [changed] $key (sha $new_sha)" >> "$LOG"

    # 변경 디테일 저장 (PR 본문용)
    {
      echo "## $key"
      echo "- URL: $url"
      echo "- SHA: $new_sha"
      echo "- diff (top 50 lines):"
      echo '```diff'
      echo "$diff_summary"
      echo '```'
    } > "$STATE_DIR/${key}.change-${TS_FILE}.md"
  else
    echo "[$TS_HUMAN] [unchanged] $key" >> "$LOG"
  fi
done

# 2) 변경 없으면 종료
if [ "${#DETECTED_CHANGES[@]}" -eq 0 ]; then
  echo "[$TS_HUMAN] no changes" >> "$LOG"
  exit 0
fi

# 3) task-instruction.md 생성
SLUG="external-trends-${TS_FILE}"
BRANCH="auto/${SLUG}"
TASK_FILE="$TASKS_DIR/task-${SLUG}.md"

{
  echo "# Task: $SLUG"
  echo
  echo "## 1) Role"
  echo "You are a senior prompt engineering researcher. Apply newly-discovered techniques to this kit's skills/rules."
  echo
  echo "## 2) Context"
  echo "- Project: orchestration_v1 (multi-AI orchestration kit)"
  echo "- Changed sources: ${DETECTED_CHANGES[*]}"
  echo "- Existing skill: plugins/exec_orch/skills/prompt-techniques.md (12 기법 매트릭스)"
  echo "- Read first: CLAUDE.md, .claude/rules/best-practices.md, prompt-techniques.md"
  echo
  echo "## 3) Files (수정 허용)"
  echo "- plugins/exec_orch/skills/prompt-techniques.md (새 기법 추가)"
  echo "- plugins/exec_orch/codex/task-instruction-template.md (template 보강)"
  echo "- .claude/rules/best-practices.md (관련 룰 보강)"
  echo
  echo "## 4) Acceptance criteria"
  echo "- 새 기법이 12 기법 매트릭스에 없으면 추가 (WHAT/WHEN/HOW 한 줄씩)"
  echo "- 라우팅 별 기본 적용 표에 매핑"
  echo "- task-instruction-template 의 § 1~10 어디에 적용할지 명시"
  echo
  echo "## 5) Reasoning (CoT)"
  echo "1. 변경 raw 본문 읽고 핵심 기법·뉴스 추출"
  echo "2. 12 기법 매트릭스와 비교 — 신규 / 중복 / 보강 분류"
  echo "3. 신규면 추가, 보강이면 example 갱신"
  echo
  echo "## 6) Negative constraints"
  echo "- 추측·헛소문 추가 X (소스 URL + 발견 일자 명시 필수)"
  echo "- 12 기법 → 30 기법 무한 확장 X (실제 사용 검증된 것만)"
  echo "- description 1024 byte 초과 X"
  echo
  echo "## 7) 변경 디테일"
  for key in "${DETECTED_CHANGES[@]}"; do
    cat "$STATE_DIR/${key}.change-${TS_FILE}.md"
    echo
  done
  echo
  echo "## 8) 완료 검증"
  echo "- python .claude/scripts/validate-plugin-schema.py"
  echo "- bash .claude/scripts/sync-plugins.sh --check"
} > "$TASK_FILE"

echo "[$TS_HUMAN] task created: $TASK_FILE" >> "$LOG"

# 4) git branch + commit + push + PR
if git rev-parse --git-dir >/dev/null 2>&1; then
  git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH" 2>/dev/null || true
  git add "$TASK_FILE" "$STATE_DIR/" 2>/dev/null
  git commit -m "chore(trends): external-trends-sync $TS_FILE — ${DETECTED_CHANGES[*]}" >/dev/null 2>&1 || true

  if command -v gh >/dev/null 2>&1; then
    GIT_TERMINAL_PROMPT=0 git push -u origin "$BRANCH" >/dev/null 2>&1 || true
    PR_BODY=".claude/state/external-trends/pr-body-${TS_FILE}.md"
    {
      echo "## 외부 트렌드 변경 감지 — $TS_HUMAN"
      echo
      echo "다음 소스에서 변경 감지:"
      for key in "${DETECTED_CHANGES[@]}"; do
        echo "- \`$key\`"
      done
      echo
      echo "Task: \`$TASK_FILE\`"
      echo
      echo "## 적용 가이드"
      echo "- 12 기법 매트릭스 (prompt-techniques.md) 와 비교"
      echo "- 신규 기법은 WHAT/WHEN/HOW 한 줄 씩 추가"
      echo "- 보강이면 example 갱신"
    } > "$PR_BODY"

    gh pr create --title "[trends] $TS_FILE — ${DETECTED_CHANGES[*]}" --body-file "$PR_BODY" --base main >/dev/null 2>&1 || \
      echo "[$TS_HUMAN] gh pr create failed (manual review: $TASK_FILE)" >> "$LOG"
  else
    echo "[$TS_HUMAN] gh CLI not found — skip PR, manual review: $TASK_FILE" >> "$LOG"
  fi

  git checkout main 2>/dev/null || git checkout master 2>/dev/null || true
fi

echo "[$TS_HUMAN] external-trends-sync done (changes: ${#DETECTED_CHANGES[@]})" >> "$LOG"
exit 0
