#!/bin/bash
# orchestration_v1 → orchestration_v1_team 동기화
# 사용: bash .claude/scripts/sync-to-team.sh
#
# 복사 대상 (인프라):
#   .claude/ (commands, skills, agents, hooks, scripts, rules, settings.json)
#   plugins/
#   .claude-plugin/
#   AGENTS.md, CLAUDE.md, GEMINI.md
#   guide.txt
#   install*.bat, install*.ps1
#   setup/
#
# 제외:
#   .git/, node_modules/, *.pptx, *.png (대용량)
#   docs/ini/ (PAT 등 시크릿)
#   .claude/state/, .claude/tasks/, .claude/context-cache/

set -e

SOURCE="$(cd "$(dirname "$0")/../.." && pwd)"
TARGET="${1:-${SOURCE%/*}/orchestration_v1_team}"

if [ ! -d "$TARGET" ]; then
  echo "[ERROR] team 폴더 없음: $TARGET"
  echo "        먼저 폴더 생성: mkdir -p '$TARGET'"
  exit 1
fi

echo "=== sync $SOURCE -> $TARGET ==="

# rsync 있으면 우선
if command -v rsync >/dev/null 2>&1; then
  RSYNC="rsync -av --delete-after"
  EXCL='--exclude=.git/ --exclude=node_modules/ --exclude=*.pptx --exclude=*.png --exclude=docs/ini/ --exclude=.claude/state/ --exclude=.claude/tasks/locks/ --exclude=.claude/tasks/done/ --exclude=.claude/context-cache/ --exclude=.claude_backup_*/'
  $RSYNC $EXCL "$SOURCE/" "$TARGET/"
  echo "[OK] rsync 동기화 완료"
  exit 0
fi

# Fallback: robocopy (Windows)
if command -v robocopy >/dev/null 2>&1 || [ -f "/c/Windows/System32/Robocopy.exe" ]; then
  ROBO="/c/Windows/System32/Robocopy.exe"
  [ ! -f "$ROBO" ] && ROBO="robocopy"
  for sub in .claude .claude-plugin plugins setup; do
    [ -d "$SOURCE/$sub" ] && \
      "$ROBO" "$SOURCE/$sub" "$TARGET/$sub" /MIR /XD .git node_modules state tasks/locks tasks/done context-cache /XF "*.pptx" "*.png" /NFL /NDL /NJH /NJS /NP > /dev/null 2>&1 || true
  done
  for f in AGENTS.md CLAUDE.md GEMINI.md guide.txt install.bat install_codex.bat install_codex.ps1 install_gemini.bat install_gemini.ps1; do
    [ -f "$SOURCE/$f" ] && cp -f "$SOURCE/$f" "$TARGET/$f"
  done

  # CRLF 정규화 — robocopy 는 EOL 변환 안 함, .bat 가 LF 면 cmd 깨짐
  if command -v powershell.exe >/dev/null 2>&1 || [ -f "/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe" ]; then
    PS_TARGET=$(cygpath -w "$TARGET" 2>/dev/null || echo "$TARGET")
    powershell.exe -NoProfile -Command "Get-ChildItem -Path '$PS_TARGET' -Recurse -Include '*.bat' | ForEach-Object { \$c = [IO.File]::ReadAllText(\$_.FullName); \$c = \$c -replace \"\`r\`n\",\"\`n\" -replace \"\`n\",\"\`r\`n\"; [IO.File]::WriteAllText(\$_.FullName, \$c, (New-Object System.Text.UTF8Encoding \$false)) }" >/dev/null 2>&1 || true
  fi

  echo "[OK] robocopy 동기화 완료 (+ CRLF 정규화)"
  exit 0
fi

echo "[ERROR] rsync / robocopy 없음 — 수동 복사 필요"
exit 1
