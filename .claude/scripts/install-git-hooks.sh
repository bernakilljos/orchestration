#!/usr/bin/env bash
# install-git-hooks.sh — .git/hooks/pre-commit 자동 설치
# setup 또는 SessionStart에서 호출
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/.git" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOK="$PROJECT_DIR/.git/hooks/pre-commit"

# 이미 있으면 skip
[ -f "$HOOK" ] && grep -q "guide.txt" "$HOOK" 2>/dev/null && exit 0

cat > "$HOOK" <<'HOOK_EOF'
#!/usr/bin/env bash
STAGED=$(git diff --cached --name-only 2>/dev/null)
INFRA=$(echo "$STAGED" | grep -cE '^(plugins/|\.claude/hooks/|\.claude/scripts/|setup/)' || echo "0")
if [ "$INFRA" -gt 0 ]; then
  GUIDE=$(echo "$STAGED" | grep -c "^guide.txt" || echo "0")
  if [ "$GUIDE" -eq 0 ]; then
    echo "❌ [git pre-commit] guide.txt 미포함! git add guide.txt"
    exit 1
  fi
fi
exit 0
HOOK_EOF

chmod +x "$HOOK" 2>/dev/null
echo "[install-git-hooks] pre-commit hook 설치 완료"
