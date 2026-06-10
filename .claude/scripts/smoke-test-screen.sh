#!/usr/bin/env bash
# smoke-test-screen.sh — 화면·기능 자동 smoke test
# 근거: CLAUDE.md § 7-24 + .claude/rules/screen-verify.md
#
# 호출:
#   bash smoke-test-screen.sh <changed_file>           # 자동 분류
#   bash smoke-test-screen.sh --db <sql_file>          # SQL schema 영향
#   bash smoke-test-screen.sh --api <controller_file>  # API endpoint
#   bash smoke-test-screen.sh --ui <html_file_or_url>  # 프론트 렌더
#
# 출력: .claude/logs/smoke-test.log + stdout PASS/FAIL
set -uo pipefail

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
LOG_DIR="${PROJECT_ROOT}/.claude/logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/smoke-test.log"
TS=$(date +%F_%T)

# 서브 프로젝트 가드
[ -d "${PROJECT_ROOT}/plugins" ] || [ -d "${PROJECT_ROOT}/src" ] || exit 0

MODE=""
TARGET=""

case "${1:-}" in
  --db)  MODE="db"; TARGET="${2:-}" ;;
  --api) MODE="api"; TARGET="${2:-}" ;;
  --ui)  MODE="ui"; TARGET="${2:-}" ;;
  "")    echo "usage: smoke-test-screen.sh [--db|--api|--ui] <file>"; exit 2 ;;
  *)
    # 자동 분류 (확장자 기반)
    TARGET="$1"
    case "$TARGET" in
      *.sql)                MODE="db" ;;
      *.java|*Controller.*|*controller.*|*Service.*|*service.*) MODE="api" ;;
      *.py)                 MODE="api" ;;  # Python controller 가능성
      *.html|*.jsx|*.tsx|*.vue) MODE="ui" ;;
      *) echo "[skip] $TARGET (지원 안 함)" >> "$LOG"; exit 0 ;;
    esac
    ;;
esac

[ -z "$TARGET" ] && { echo "[smoke] target 없음"; exit 2; }

echo "[$TS] ===== smoke test 시작 (mode=$MODE, target=$TARGET) =====" >> "$LOG"

PASS=1
ISSUES=()

# =========================================================
# MODE: db — SQL schema 변경 → NULL 컬럼 + null-unsafe 검출
# =========================================================
run_db_check() {
  local sql="$1"
  echo "[$TS] DB 모드 — $sql" >> "$LOG"

  # NULL 가능 컬럼 추출 (ADD COLUMN ... NULL 또는 DEFAULT NULL)
  local null_cols
  null_cols=$(grep -ihE "ADD COLUMN [a-zA-Z_]+|NULL DEFAULT NULL|DEFAULT NULL" "$sql" 2>/dev/null | grep -ihoE "[a-zA-Z_]+[[:space:]]+[A-Z]+.*NULL" || true)
  if [ -z "$null_cols" ]; then
    echo "[$TS]   NULL 가능 컬럼 없음" >> "$LOG"
    return 0
  fi

  echo "[$TS]   NULL 가능 컬럼 검출:" >> "$LOG"
  echo "$null_cols" | head -10 >> "$LOG"

  # 컬럼명 추출 (첫 단어)
  local cols
  cols=$(echo "$null_cols" | awk '{print $1}' | sort -u)

  for col in $cols; do
    # 해당 컬럼 참조하는 Java/Python/JS 코드 grep
    local refs
    refs=$(grep -rlE "(getString|getColumn|columns\[|\.${col}|\"${col}\")" "$PROJECT_ROOT/src" "$PROJECT_ROOT/app" 2>/dev/null | head -5 || true)
    if [ -z "$refs" ]; then continue; fi

    # null check 있는지
    local has_null_check
    has_null_check=$(grep -lE "!= *null|is None|Optional\.ofNullable|\?\." $refs 2>/dev/null | head -1 || true)
    if [ -z "$has_null_check" ]; then
      ISSUES+=("NULL 가능 컬럼 '$col' 참조 코드에 null check 없음 → NPE 위험")
      PASS=0
    fi
  done
}

# =========================================================
# MODE: api — controller 수정 → endpoint curl
# =========================================================
run_api_check() {
  local file="$1"
  echo "[$TS] API 모드 — $file" >> "$LOG"

  # endpoint 추출 (Spring/Flask/FastAPI 패턴)
  local endpoints
  endpoints=$(grep -hE "@(Get|Post|Put|Delete|Request)Mapping|@app\.(get|post|put|delete)|@router\.(get|post)" "$file" 2>/dev/null | grep -oE '"[^"]+"' | head -10 || true)

  if [ -z "$endpoints" ]; then
    echo "[$TS]   endpoint 없음 (또는 패턴 매치 X)" >> "$LOG"
    return 0
  fi

  # 환경변수 또는 기본
  local base_url="${SMOKE_API_BASE:-http://localhost:8080}"

  for ep in $endpoints; do
    ep="${ep//\"/}"
    local url="${base_url}${ep}"
    echo "[$TS]   curl $url" >> "$LOG"

    # curl + status + body
    local status body
    status=$(curl -s -o /tmp/smoke-body.txt -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    body=$(cat /tmp/smoke-body.txt 2>/dev/null || echo "")

    if [ "$status" = "000" ]; then
      ISSUES+=("$url — 서버 응답 없음 (서버 안 떠 있을 수도)")
      continue
    fi

    if [ "$status" -ge 500 ]; then
      ISSUES+=("$url — HTTP $status (서버 오류, NPE 가능성)")
      PASS=0
      echo "$body" | head -10 >> "$LOG"
    elif [ "$status" -ge 400 ]; then
      ISSUES+=("$url — HTTP $status (클라이언트 오류)")
    fi
  done
}

# =========================================================
# MODE: ui — 프론트 Playwright render
# =========================================================
run_ui_check() {
  local target="$1"
  echo "[$TS] UI 모드 — $target" >> "$LOG"

  if ! command -v python >/dev/null 2>&1; then
    echo "[$TS]   python 없음 → skip" >> "$LOG"
    return 0
  fi

  # Playwright 가용성 체크
  if ! python -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
    echo "[$TS]   playwright 없음 → skip" >> "$LOG"
    return 0
  fi

  # URL or HTML 파일
  local url="$target"
  case "$target" in
    http*) ;;
    *.html) url="file://$target" ;;
    *) echo "[$TS]   render 대상 모호 → skip" >> "$LOG"; return 0 ;;
  esac

  python <<EOF >> "$LOG" 2>&1
from playwright.sync_api import sync_playwright
import sys
errors = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on("console", lambda msg: errors.append((msg.type, msg.text)) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(("pageerror", str(exc))))
    try:
        page.goto("$url", timeout=15000, wait_until="load")
    except Exception as e:
        errors.append(("nav", str(e)))
    browser.close()
if errors:
    print("[FAIL] console/page errors:")
    for t, msg in errors:
        print(f"  [{t}] {msg}")
    sys.exit(1)
print("[PASS] render OK, console clean")
EOF
  if [ $? -ne 0 ]; then
    ISSUES+=("$url — render 또는 console error")
    PASS=0
  fi
}

# =========================================================
# 실행
# =========================================================
case "$MODE" in
  db)  run_db_check "$TARGET" ;;
  api) run_api_check "$TARGET" ;;
  ui)  run_ui_check "$TARGET" ;;
esac

# 결과
if [ "$PASS" = "1" ]; then
  echo "[$TS] ===== smoke test PASS =====" >> "$LOG"
  echo "[smoke-test] PASS ($MODE: $TARGET)"
  exit 0
else
  echo "[$TS] ===== smoke test FAIL =====" >> "$LOG"
  echo "[smoke-test] FAIL ($MODE: $TARGET)"
  for issue in "${ISSUES[@]}"; do
    echo "  - $issue"
    echo "  - $issue" >> "$LOG"
  done
  exit 1
fi
