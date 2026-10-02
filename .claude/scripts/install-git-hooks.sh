#!/usr/bin/env bash
# install-git-hooks.sh — .git/hooks/pre-commit 자동 설치
# setup 또는 SessionStart에서 호출
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/.git" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOK="$PROJECT_DIR/.git/hooks/pre-commit"

# 최신본이면 pre-commit 만 건너뛴다. 예전엔 "guide.txt" 만 보고 exit 0 해서
# 고친 판(|| true)이 기존 설치에 영영 안 들어갔고, 아래 post-merge·post-rewrite 도
# 설치되지 않았다 (2026-10-02 실측: pull 후에도 'integer expression expected' 재현).
if [ -f "$HOOK" ] && grep -q "guide.txt" "$HOOK" 2>/dev/null && ! grep -q '|| echo "0"' "$HOOK" 2>/dev/null; then
  : # 최신 pre-commit
else
cat > "$HOOK" <<'HOOK_EOF'
#!/usr/bin/env bash
STAGED=$(git diff --cached --name-only 2>/dev/null)
INFRA=$(echo "$STAGED" | grep -cE '^(plugins/|\.claude/hooks/|\.claude/scripts/|setup/)' || true)
if [ "$INFRA" -gt 0 ]; then
  GUIDE=$(echo "$STAGED" | grep -c "^guide.txt" || true)
  if [ "$GUIDE" -eq 0 ]; then
    echo "[X] [git pre-commit] guide.txt 미포함! git add guide.txt"
    exit 1
  fi
fi
exit 0
HOOK_EOF

chmod +x "$HOOK" 2>/dev/null
echo "[install-git-hooks] pre-commit hook 설치 완료"
fi

# post-merge: git pull 후 등록된 대상 프로젝트(.claude/state/merge-targets.txt)에 kit 자동 병합
PM="$PROJECT_DIR/.git/hooks/post-merge"
if ! grep -q "merge-to-target" "$PM" 2>/dev/null; then
  cat > "$PM" <<'PM_EOF'
#!/usr/bin/env bash
# kit git pull → 대상 프로젝트 자동 병합 (덮어쓰기 X · 대상 수정본 보존 · 백업)
ROOT="$(git rev-parse --show-toplevel)"
PY="$(command -v python || command -v python3)"
[ -n "$PY" ] && [ -f "$ROOT/.claude/state/merge-targets.txt" ] || exit 0
mkdir -p "$ROOT/.claude/logs"
"$PY" -X utf8 "$ROOT/.claude/scripts/merge-to-target.py" --all --apply >> "$ROOT/.claude/logs/merge-to-target.log" 2>&1 &
echo "[post-merge] 대상 프로젝트 자동 병합 시작 (로그: .claude/logs/merge-to-target.log)"
exit 0
PM_EOF
  chmod +x "$PM" 2>/dev/null
  echo "[install-git-hooks] post-merge hook 설치 완료"
fi

# post-rewrite: pull --rebase 는 post-merge 를 안 부른다 → 같은 동작을 rebase 후에도
PR="$PROJECT_DIR/.git/hooks/post-rewrite"
if ! grep -q "hooks/post-merge" "$PR" 2>/dev/null; then
  cat > "$PR" <<'PR_EOF'
#!/usr/bin/env bash
[ "$1" = "rebase" ] || exit 0
exec "$(git rev-parse --show-toplevel)/.git/hooks/post-merge"
PR_EOF
  chmod +x "$PR" 2>/dev/null
  echo "[install-git-hooks] post-rewrite hook 설치 완료"
fi
