#!/bin/bash
# orchestration_v1 -> orchestration_v1_team 동기화
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
# 2026-10-26 fix (사용자 명시 defect #1): --delete-after 제거 (대상 파일 삭제 금지)
#   additive-only: 소스에 없는 파일은 target 에 보존 (운영 target 안전)
#   오류는 전파 (|| true 사용 X · set -e 가 잡음)
if command -v rsync >/dev/null 2>&1; then
  RSYNC="rsync -av"
  EXCL='--exclude=.git/ --exclude=node_modules/ --exclude=*.pptx --exclude=*.png --exclude=docs/ini/ --exclude=.claude/state/ --exclude=.claude/tasks/locks/ --exclude=.claude/tasks/done/ --exclude=.claude/context-cache/ --exclude=.claude_backup_*/'
  if $RSYNC $EXCL "$SOURCE/" "$TARGET/"; then
    echo "[OK] rsync 동기화 완료 (additive · 대상 파일 삭제 X)"
    exit 0
  else
    echo "[ERROR] rsync 실패 (exit $?) — 성공 처리 X"
    exit 2
  fi
fi

# Fallback: robocopy (Windows)
if command -v robocopy >/dev/null 2>&1 || [ -f "/c/Windows/System32/Robocopy.exe" ]; then
  ROBO="/c/Windows/System32/Robocopy.exe"
  [ ! -f "$ROBO" ] && ROBO="robocopy"
  # 1) source 의 .bat CRLF 강제 정규화 (robocopy 가 main -> team 정확 복사)
  if command -v powershell.exe >/dev/null 2>&1 || [ -f "/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe" ]; then
    PS_SRC=$(cygpath -w "$SOURCE" 2>/dev/null || echo "$SOURCE")
    powershell.exe -NoProfile -Command "Get-ChildItem -Path '$PS_SRC' -Recurse -Include '*.bat' -ErrorAction SilentlyContinue | ForEach-Object { \$c = [IO.File]::ReadAllText(\$_.FullName); \$n = \$c -replace \"\`r\`n\",\"\`n\" -replace \"\`n\",\"\`r\`n\"; if (\$c -ne \$n) { [IO.File]::WriteAllText(\$_.FullName, \$n, (New-Object System.Text.UTF8Encoding \$false)) } }" >/dev/null 2>&1 || true
  fi

  # 2) robocopy — cmd 환경변수 전달 (backslash escape 안전)
  # 2026-10-26 fix (사용자 defect #1):
  #   /MIR → /E · 대상 파일 삭제 금지 (additive 복사만)
  #   || true 제거 · robocopy exit 8+ 는 실패 · 실패 시 성공 표시 X
  #   > /dev/null 2>&1 제거 · stderr 는 보존 (디버깅)
  SYNC_FAIL=0
  for sub in .claude .claude-plugin plugins outputs; do
    if [ -d "$SOURCE/$sub" ]; then
      SRC_WIN=$(cygpath -w "$SOURCE/$sub" 2>/dev/null || echo "$SOURCE/$sub")
      DST_WIN=$(cygpath -w "$TARGET/$sub" 2>/dev/null || echo "$TARGET/$sub")
      # 2026-10-26: robocopy exit 1~7 는 정상 · set -e 트립 방지용 || RC=$?
      RC=0
      RC_SRC="$SRC_WIN" RC_DST="$DST_WIN" cmd //c "robocopy %RC_SRC% %RC_DST% /E /IS /IT /XD .git node_modules state context-cache locks done /XF *.pptx *.png .is-kit-root /NFL /NDL /NJH /NJS /NP" > /dev/null || RC=$?
      # robocopy exit code: 0~7 = 성공·no change·copy OK · 8+ = 실패
      if [ "$RC" -ge 8 ]; then
        echo "[ERROR] robocopy $sub 실패 (exit $RC)"
        SYNC_FAIL=1
      fi
    fi
  done

  # 2-1) setup 폴더는 robocopy 가 timestamp 비교로 skip 하는 경우 발생 -> 개별 파일 강제 cp
  mkdir -p "$TARGET/setup/modules" 2>/dev/null
  for f in "$SOURCE"/setup/*.bat "$SOURCE"/setup/*.iss "$SOURCE"/setup/*.rtf; do
    [ -f "$f" ] && cp -f "$f" "$TARGET/setup/$(basename "$f")"
  done
  for f in "$SOURCE"/setup/modules/*.bat; do
    [ -f "$f" ] && cp -f "$f" "$TARGET/setup/modules/$(basename "$f")"
  done

  # 3) 루트 파일 강제 cp
  for f in AGENTS.md CLAUDE.md GEMINI.md guide.txt install.bat install_codex.bat install_codex.ps1 install_gemini.bat install_gemini.ps1; do
    [ -f "$SOURCE/$f" ] && cp -f "$SOURCE/$f" "$TARGET/$f"
  done

  # 4) setup.exe (GUI 마법사 — 다음다음 클릭 인스톨러)
  if [ -f "$SOURCE/setup/Output/OrchestrationKit-Setup.exe" ]; then
    mkdir -p "$TARGET/setup/Output"
    cp -f "$SOURCE/setup/Output/OrchestrationKit-Setup.exe" "$TARGET/setup/Output/OrchestrationKit-Setup.exe"
  fi

  # 2026-10-26 fix: 실패 1건이라도 있으면 성공 처리 X
  if [ "$SYNC_FAIL" -ne 0 ]; then
    echo "[ERROR] robocopy 일부 실패 — 성공 처리 X"
    exit 3
  fi
  echo "[OK] robocopy 동기화 완료 (additive · CRLF 정규화 + 강제 복사 · 대상 파일 삭제 X)"
  exit 0
fi

echo "[ERROR] rsync / robocopy 없음 — 수동 복사 필요"
exit 1
