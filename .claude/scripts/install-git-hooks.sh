#!/usr/bin/env bash
# install-git-hooks.sh — .git/hooks/pre-commit 자동 설치
# setup 또는 SessionStart에서 호출
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/.git" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOK="$PROJECT_DIR/.git/hooks/pre-commit"

# 최신본이면 pre-commit 만 건너뛴다. 예전엔 "guide.txt" 만 보고 exit 0 해서
# 고친 판(|| true)이 기존 설치에 영영 안 들어갔고, 아래 post-merge·post-rewrite 도
# 설치되지 않았다 (2026-10-02 실측: pull 후에도 'integer expression expected' 재현).
# 2026-10-13: 인코딩 검사(precommit-encoding-check) 가 없는 옛 판도 다시 설치한다.
if [ -f "$HOOK" ] && grep -q "guide.txt" "$HOOK" 2>/dev/null && ! grep -q '|| echo "0"' "$HOOK" 2>/dev/null && grep -q "precommit-encoding-check" "$HOOK" 2>/dev/null; then
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
# 한글 깨짐·python 문법 오류 파일 커밋 차단 (2026-10-13 11c622f 사고)
ROOT="$(git rev-parse --show-toplevel)"
PY="$(command -v python || command -v python3)"
if [ -n "$PY" ] && [ -f "$ROOT/.claude/scripts/precommit-encoding-check.py" ]; then
  "$PY" -X utf8 "$ROOT/.claude/scripts/precommit-encoding-check.py" || exit 1
fi
exit 0
HOOK_EOF

chmod +x "$HOOK" 2>/dev/null
echo "[install-git-hooks] pre-commit hook 설치 완료"
fi

# post-merge: git pull 후 등록된 대상 프로젝트(.claude/state/merge-targets.txt)에 kit 자동 병합
# R389 (2026-11-24): pull 받으면 kit 자체 VS Code 설정 병합도 무조건 — 대상 목록이 없는 PC 는 종전 훅이 바로 끝나 아무것도 안 했다.
#   표식(deploy-vscode-settings)이 없는 옛 훅은 새 내용으로 다시 설치 (이미 설치된 PC 도 갱신되게)
PM="$PROJECT_DIR/.git/hooks/post-merge"
if ! grep -q "deploy-vscode-settings" "$PM" 2>/dev/null; then
  cat > "$PM" <<'PM_EOF'
#!/usr/bin/env bash
# kit git pull → ① kit VS Code 설정 병합(템플릿에만 있는 키만 · 그 PC 값 보존) ② 대상 프로젝트 자동 병합(덮어쓰기 X · 백업 · 대상별 VS Code 설정 병합 포함)
ROOT="$(git rev-parse --show-toplevel)"
[ -f "$ROOT/plugins/exec_orch/hooks/deploy-vscode-settings.sh" ] && bash "$ROOT/plugins/exec_orch/hooks/deploy-vscode-settings.sh" || true
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
