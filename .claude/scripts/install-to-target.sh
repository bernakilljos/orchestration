#!/bin/bash
# install-to-target.sh — 이 킷을 다른 프로젝트에 안전 적용 (업그레이드)
#
# 사용법:
#   bash .claude/scripts/install-to-target.sh <TARGET_DIR>
#
# 복사 대상 (덮어쓰기 + 백업):
#   - plugins/               (킷 플러그인 전체)
#   - .claude-plugin/        (메타·스키마·마켓플레이스)
#   - .claude/rules/         (공유 규칙)
#   - .claude/scripts/       (sync·validate·install 등 인프라)
#   - .claude/hooks/*.sh     (신규 훅만 추가 — 기존 유지)
#   - guide.txt
#   - .gitattributes
#   - .env.example           (없으면)
#   - docs/architecture-patterns.md
#   - docs/2026-04-19/        (로드맵 등)
#
# 보호 (절대 건드리지 않음):
#   - CLAUDE.md              (프로젝트 고유 — 병합은 수동)
#   - .claude/tasks/         (진행 중 태스크)
#   - .claude/state/         (워커 heartbeat·플래그)
#   - .claude/context-cache/ (세션 스냅샷)
#   - .claude/learning/      (학습 JSON)
#   - .claude/settings.json  (프로젝트별 권한 — 병합은 수동)

set -uo pipefail

TARGET="${1:-}"
if [ -z "$TARGET" ] || [ ! -d "$TARGET" ]; then
  echo "사용법: $0 <TARGET_DIR>"
  echo "오류: '$TARGET' 디렉토리 없음"
  exit 1
fi

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP="$TARGET/.claude/backups/kit-upgrade-$(date +%Y%m%d-%H%M%S)"

echo "=== Orchestration Kit 업그레이드 ==="
echo "  SRC:    $SRC"
echo "  TARGET: $TARGET"
echo "  BACKUP: $BACKUP"
echo ""

mkdir -p "$BACKUP"

# ─────────────────────────────────────────────
# 1. plugins/ 전체 교체 (기존 백업)
# ─────────────────────────────────────────────
echo "[1/7] plugins/ 업그레이드..."
if [ -d "$TARGET/plugins" ]; then
  cp -r "$TARGET/plugins" "$BACKUP/plugins" 2>/dev/null || true
  rm -rf "$TARGET/plugins"
fi
cp -r "$SRC/plugins" "$TARGET/plugins"
echo "  ✓ plugins/ 24개 복사"

# ─────────────────────────────────────────────
# 2. .claude-plugin/ 전체 교체
# ─────────────────────────────────────────────
echo "[2/7] .claude-plugin/ 업그레이드..."
if [ -d "$TARGET/.claude-plugin" ]; then
  cp -r "$TARGET/.claude-plugin" "$BACKUP/.claude-plugin" 2>/dev/null || true
  rm -rf "$TARGET/.claude-plugin"
fi
cp -r "$SRC/.claude-plugin" "$TARGET/.claude-plugin"
echo "  ✓ plugin.json + schema + marketplace.json"

# ─────────────────────────────────────────────
# 3. .claude/rules/ 전체 교체
# ─────────────────────────────────────────────
echo "[3/7] .claude/rules/ 업그레이드..."
mkdir -p "$TARGET/.claude"
if [ -d "$TARGET/.claude/rules" ]; then
  cp -r "$TARGET/.claude/rules" "$BACKUP/rules" 2>/dev/null || true
  rm -rf "$TARGET/.claude/rules"
fi
cp -r "$SRC/.claude/rules" "$TARGET/.claude/rules"
echo "  ✓ 6 규칙 파일"

# ─────────────────────────────────────────────
# 4. .claude/scripts/ 업그레이드 (기존 백업 후 교체)
# ─────────────────────────────────────────────
echo "[4/7] .claude/scripts/ 업그레이드..."
if [ -d "$TARGET/.claude/scripts" ]; then
  cp -r "$TARGET/.claude/scripts" "$BACKUP/scripts" 2>/dev/null || true
fi
mkdir -p "$TARGET/.claude/scripts"
cp -f "$SRC/.claude/scripts/"*.sh "$TARGET/.claude/scripts/" 2>/dev/null || true
cp -f "$SRC/.claude/scripts/"*.py "$TARGET/.claude/scripts/" 2>/dev/null || true
cp -f "$SRC/.claude/scripts/"*.bat "$TARGET/.claude/scripts/" 2>/dev/null || true
cp -f "$SRC/.claude/scripts/"*.ps1 "$TARGET/.claude/scripts/" 2>/dev/null || true
# scripts/lib/ 도 동기화 (state_db·router·pricing·prompt_cache 등)
if [ -d "$SRC/.claude/scripts/lib" ]; then
  mkdir -p "$TARGET/.claude/scripts/lib"
  cp -f "$SRC/.claude/scripts/lib/"*.py "$TARGET/.claude/scripts/lib/" 2>/dev/null || true
fi
echo "  ✓ sync·validate·install·worker-health·rag·trends·cleanup 등 (.sh/.py/.bat/.ps1 + lib/)"

# ─────────────────────────────────────────────
# 5. .claude/hooks/ 신규 훅만 추가 (기존 .sh 건드리지 않음)
# ─────────────────────────────────────────────
echo "[5/7] .claude/hooks/ (신규만)..."
mkdir -p "$TARGET/.claude/hooks"
for hook in check-mojibake.sh; do
  if [ ! -f "$TARGET/.claude/hooks/$hook" ] && [ -f "$SRC/.claude/hooks/$hook" ]; then
    cp "$SRC/.claude/hooks/$hook" "$TARGET/.claude/hooks/"
    echo "  + $hook"
  fi
done

# ─────────────────────────────────────────────
# 6. 루트 파일들
# ─────────────────────────────────────────────
echo "[6/7] 루트 파일..."
for f in guide.txt .gitattributes; do
  if [ -f "$SRC/$f" ]; then
    [ -f "$TARGET/$f" ] && cp "$TARGET/$f" "$BACKUP/$f" 2>/dev/null || true
    cp "$SRC/$f" "$TARGET/$f"
  fi
done
if [ ! -f "$TARGET/.env.example" ] && [ -f "$SRC/.env.example" ]; then
  cp "$SRC/.env.example" "$TARGET/.env.example"
  echo "  + .env.example (신규)"
fi
echo "  ✓ guide.txt + .gitattributes"

# ─────────────────────────────────────────────
# 7. docs/ 참조 문서 (프로젝트 docs 보호)
# ─────────────────────────────────────────────
echo "[7/7] docs/ 참조 문서..."
mkdir -p "$TARGET/docs"
for f in architecture-patterns.md; do
  if [ -f "$SRC/docs/$f" ]; then
    cp "$SRC/docs/$f" "$TARGET/docs/$f"
  fi
done
if [ -d "$SRC/docs/2026-04-19" ]; then
  mkdir -p "$TARGET/docs/2026-04-19"
  cp -f "$SRC/docs/2026-04-19/"* "$TARGET/docs/2026-04-19/" 2>/dev/null || true
fi
echo "  ✓ architecture-patterns.md + 2026-04-19/"

echo ""
echo "=== 업그레이드 완료 ==="
echo "  백업: $BACKUP"
echo ""
echo "다음 단계 (대상 프로젝트에서):"
echo "  cd $TARGET"
echo "  bash .claude/scripts/sync-plugins.sh"
echo "  python .claude/scripts/validate-plugin-schema.py"
echo ""
echo "보호됨 (수동 병합 필요):"
echo "  - CLAUDE.md"
echo "  - .claude/settings.json"
echo "  - .claude/tasks/·state/·context-cache/·learning/"
