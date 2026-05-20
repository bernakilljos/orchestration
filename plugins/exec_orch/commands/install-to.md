---
description: "다른 프로젝트에 orchestration_v1 install — /install-to C:\\pjt\\target"
allowed-tools: Bash(cp:*), Bash(mkdir:*), Bash(python:*), Bash(bash:*), Read, Write, Glob, Grep
---

# /install-to — 다른 프로젝트에 orchestration_v1 설치

## 사용법
```text
/install-to <target_path>
```

예시:
```text
/install-to C:\pjt\calc
/install-to C:\lottoclaude
/install-to /home/user/myproject
```

## 동작
1. `<target_path>` 존재 확인 (없으면 생성)
2. plugins/ 전체 복사
3. .claude/ 인프라 복사 (hooks, scripts, rules, state, settings.json)
4. .claude-plugin/ 복사
5. CLAUDE.md + guide.txt 복사
6. .env.example → .env 자동 생성 (없으면)
7. sync-plugins.sh 실행 (plugins/ → .claude/commands,skills,agents)
8. init-state-db.py 실행 (orca.db 초기화)
9. orca-enabled + auto-dev-enabled 플래그 생성
10. 검증 (파일 카운트 확인)

## 규칙
- 기존 .claude/ 있으면 .claude.bak-YYYYMMDD_HHMMSS 백업
- 하드코딩 경로 금지 (동적 검색)
- setup.bat 의 Module 01~15 핵심 로직을 bash 로 재현
- Windows + Linux/Mac 둘 다 동작

## 실행 스크립트 (Claude가 직접 실행)
```bash
TARGET="$1"
SOURCE="$(pwd)"  # orchestration_v1

# 백업
[ -d "$TARGET/.claude" ] && cp -r "$TARGET/.claude" "$TARGET/.claude.bak-$(date +%Y%m%d_%H%M%S)"

# 복사
cp -r "$SOURCE/plugins" "$TARGET/"
for d in hooks scripts rules state context-cache; do
  mkdir -p "$TARGET/.claude/$d"
  cp -r "$SOURCE/.claude/$d/"* "$TARGET/.claude/$d/" 2>/dev/null
done
cp "$SOURCE/.claude/settings.json" "$TARGET/.claude/"
cp -r "$SOURCE/.claude-plugin" "$TARGET/"
cp "$SOURCE/CLAUDE.md" "$SOURCE/guide.txt" "$TARGET/"

# .env
[ ! -f "$TARGET/.env" ] && [ -f "$SOURCE/.env.example" ] && cp "$SOURCE/.env.example" "$TARGET/.env"

# sync + init
cd "$TARGET" && bash .claude/scripts/sync-plugins.sh
python .claude/scripts/init-state-db.py 2>/dev/null

# 플래그
echo "enabled" > "$TARGET/.claude/orca-enabled"
echo "enabled" > "$TARGET/.claude/auto-dev-enabled"

# git hook 설치 (guide.txt 누락 방지)
bash "$TARGET/.claude/scripts/install-git-hooks.sh" 2>/dev/null

# 검증
echo "=== Install 검증 ==="
echo "plugins: $(ls "$TARGET/plugins/" | wc -l)"
echo "commands: $(ls "$TARGET/.claude/commands/" 2>/dev/null | wc -l)"
echo "skills: $(ls "$TARGET/.claude/skills/" 2>/dev/null | wc -l)"
echo "hooks: $(ls "$TARGET/.claude/hooks/" 2>/dev/null | wc -l)"
echo "scripts: $(ls "$TARGET/.claude/scripts/" 2>/dev/null | wc -l)"
```
