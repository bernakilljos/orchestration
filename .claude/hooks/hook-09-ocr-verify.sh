#!/usr/bin/env bash
# HOOK-09 — OCR Overflow Verify
#
# PostToolUse hook — Bash 명령에 'generate-*-ppt.py' 패턴이 포함되면 자동 검증.
# stdin 으로 hook input JSON 받음 (tool_input.command).

set -e

# stdin 의 JSON 에서 command 추출
INPUT="$(cat)"

# jq 가 있으면 정확 추출, 없으면 grep fallback
if command -v jq >/dev/null 2>&1; then
  CMD="$(echo "$INPUT" | jq -r '.tool_input.command // ""')"
else
  CMD="$(echo "$INPUT" | grep -oE '"command"\s*:\s*"[^"]*"' | head -1 | sed 's/.*:"\(.*\)"/\1/')"
fi

# 산출물 빌드 패턴 매칭 (확장: build-*-doc / build-*-diagrams / generate-*-ppt / render-* / pdf)
if ! echo "$CMD" | grep -qE '(build|generate|render)-[a-z-]+-(ppt|doc|diagrams|pdf|html)\.py|build-[a-z-]+-doc\.py'; then
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# PPT 검증
VERIFY_PPT="$PROJECT_ROOT/.claude/scripts/verify-ppt-overflow.py"
# 일반 이미지 fit 검증 (PNG 비율 vs 페이지 비율)
VERIFY_FIT="$PROJECT_ROOT/.claude/scripts/verify-image-fit.py"

if [ -f "$VERIFY_FIT" ] && echo "$CMD" | grep -qE '(build|generate|render)-[a-z-]+-(diagrams|doc|html)\.py'; then
  FIT_RESULT="$(python "$VERIFY_FIT" 2>&1 || true)"
  if echo "$FIT_RESULT" | grep -q 'FAIL'; then
    cat <<EOF
{"systemMessage": "[hook-09 fit] 이미지 fit 검증 실패:\n$FIT_RESULT"}
EOF
  fi
fi

# PNG 흰 여백 자동 검출 — build-*-diagrams 또는 build-*-doc 호출 시
VERIFY_WS="$PROJECT_ROOT/.claude/scripts/verify-image-whitespace.py"
if [ -f "$VERIFY_WS" ] && echo "$CMD" | grep -qE '(build|generate|render)-[a-z-]+-(diagrams|doc|html)\.py'; then
  WS_RESULT="$(python "$VERIFY_WS" "$PROJECT_ROOT/docs/screens/arch-kor" 2>&1 || true)"
  if echo "$WS_RESULT" | grep -q 'WARN'; then
    cat <<EOF
{"systemMessage": "[hook-09 whitespace] PNG 흰 여백 감지 (≥5%) — 사용자 'docx 안 이미지 여백' 호소 방지:\n$WS_RESULT"}
EOF
  fi
fi

# docx 구조 검증 (paragraph 기반 — 빠른 1차) — build-*-doc.py 호출 시
VERIFY_DOCX="$PROJECT_ROOT/.claude/scripts/verify-docx-structure.py"
if [ -f "$VERIFY_DOCX" ] && echo "$CMD" | grep -qE 'build-[a-z-]+-doc\.py'; then
  DOCX_RESULT="$(python "$VERIFY_DOCX" 2>&1 || true)"
  if echo "$DOCX_RESULT" | grep -q 'FAIL'; then
    cat <<EOF
{"systemMessage": "[hook-09 docx-structure] paragraph 구조 검증 실패:\n$DOCX_RESULT"}
EOF
  fi
fi

# docx 실제 페이지 검증 (Word COM — 진짜 빈 페이지·자투리 검출) — build-*-doc.py 호출 시
VERIFY_DOCX_PAGES="$PROJECT_ROOT/.claude/scripts/verify-docx-pages.py"
VERIFY_DOCX_VISUAL="$PROJECT_ROOT/.claude/scripts/verify-docx-visual.py"
if echo "$CMD" | grep -qE 'build-[a-z-]+-doc\.py'; then
  for docx in "$PROJECT_ROOT"/docs/*.docx "$PROJECT_ROOT"/docs/lecture/*.docx; do
    [ -f "$docx" ] || continue
    DOCX_BASE="$(basename "$docx")"
    # 1차: paragraph 페이지 검증
    if [ -f "$VERIFY_DOCX_PAGES" ]; then
      PAGES_RESULT="$(python "$VERIFY_DOCX_PAGES" "$docx" 2>&1 || true)"
      if echo "$PAGES_RESULT" | grep -q 'FAIL'; then
        cat <<EOF
{"systemMessage": "[hook-09 docx-pages] 빈 페이지 검출:\n$PAGES_RESULT"}
EOF
      fi
    fi
    # 2차: docx → PDF → PNG visual export — Claude 가 Read tool 로 시각 확인 의무
    if [ -f "$VERIFY_DOCX_VISUAL" ]; then
      python "$VERIFY_DOCX_VISUAL" "$docx" "1,4,6,10,15,20" >/dev/null 2>&1 || true
      VISUAL_DIR="$(dirname "$docx")/_visual"
      if [ -d "$VISUAL_DIR" ]; then
        VISUAL_PNGS="$(ls "$VISUAL_DIR"/page-*.png 2>/dev/null | head -6 | sed 's|.*|  - &|')"
        cat <<EOF
{"systemMessage": "[hook-09 docx-visual] docx 빌드 완료. 산출물 실제 출력 확인 의무 — Read tool 로 다음 PNG 시각 확인:\n$VISUAL_PNGS\n\n검증 항목: 이미지 잘림 / 글씨 가독성 (>=11pt) / 빈 공간 / 페이지 fit. PNG OCR 만 보지 말고 docx 안 실제 출력 봐야 함."}
EOF
      fi
    fi
  done
fi

# pptx visual 검증 — build-*-ppt.py / build-*-pptx.py
VERIFY_PPT_VISUAL="$PROJECT_ROOT/.claude/scripts/verify-ppt-overflow.py"
if echo "$CMD" | grep -qE 'build-[a-z-]+-(ppt|pptx)\.py|generate-[a-z-]+-ppt\.py'; then
  cat <<EOF
{"systemMessage": "[hook-09 pptx] pptx 빌드 감지. 산출물 실제 출력 확인 의무 — verify-ppt-overflow.py 결과 + 슬라이드 PNG export → Read tool 로 시각 확인. PNG OCR ≠ pptx 안 실제 출력."}
EOF
fi

if [ ! -f "$VERIFY_PPT" ]; then
  exit 0
fi
VERIFY_SCRIPT="$VERIFY_PPT"

# 검증 실행
RESULT="$(python "$VERIFY_SCRIPT" 2>&1 || true)"
EXIT_CODE=$?

# suspects 발견 시 Claude 에게 알림 (systemMessage)
if echo "$RESULT" | grep -q '\[!\]'; then
  SUSPECTS="$(echo "$RESULT" | grep -E '^\s*-\s+slide-' | sed 's/^\s*//' | head -10)"
  cat <<EOF
{
  "systemMessage": "[hook-09 OCR Verify] PPT 렌더 후 잘림 의심 슬라이드 발견 — Read tool 로 직접 OCR 검증 권장:\n${SUSPECTS}\n\noverflow-report.md 참조"
}
EOF
fi

# ★1 RAG index 자동 재빌드 — feedback/rule/skill md 변경 시
if echo "$CMD" | grep -qE '(Write|Edit).*(memory/feedback_|\.claude/rules/|plugins/.*/skills/|CLAUDE\.md)'; then
  RAG_SCRIPT="$PROJECT_ROOT/.claude/scripts/rag-recall.py"
  if [ -f "$RAG_SCRIPT" ]; then
    (PYTHONIOENCODING=utf-8 python "$RAG_SCRIPT" --build >/dev/null 2>&1) &
  fi
fi

# ★2 Decision pattern alarm — 같은 키워드 1h 내 3회+ → systemMessage
ALARM_DB="$PROJECT_ROOT/.claude/state/orca.db"
if [ -f "$ALARM_DB" ]; then
  ALARMS="$(PYTHONIOENCODING=utf-8 python -c "
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
db = Path(r'$ALARM_DB')
conn = sqlite3.connect(str(db))
try:
    cutoff = (datetime.utcnow() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
    cur = conn.execute(\"SELECT keywords, COUNT(*) FROM decisions WHERE ts >= ? AND keywords != '' GROUP BY keywords HAVING COUNT(*) >= 3 LIMIT 3\", (cutoff,))
    for row in cur.fetchall():
        print(f'{row[0]}={row[1]}회')
except Exception:
    pass
conn.close()
" 2>/dev/null)"
  if [ -n "$ALARMS" ]; then
    ALARMS_FMT="$(echo "$ALARMS" | tr '\n' ' ')"
    cat <<EOF
{"systemMessage": "⚠ [Decision Alarm] 같은 패턴 1시간 내 3회+: ${ALARMS_FMT}— 근본 원인 점검 필요"}
EOF
  fi
fi

exit 0
