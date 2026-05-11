#!/bin/bash
# HOOK-00 — Init: 프로젝트 첫 셋업
# .claude/scripts/init.bat 가 있으면 호출, 없으면 기본 폴더만 생성
set -e

PROJECT="${1:-$(pwd)}"
INIT_BAT="$PROJECT/.claude/scripts/init.bat"

# 기본 폴더 (idempotent)
mkdir -p "$PROJECT/docs/adr" \
         "$PROJECT/docs/deploy-history" \
         "$PROJECT/docs/screens" \
         "$PROJECT/.claude/context-cache" \
         "$PROJECT/.claude/tasks" \
         "$PROJECT/.claude/learning"

if [ -f "$INIT_BAT" ]; then
  if command -v cmd.exe >/dev/null 2>&1; then
    cmd.exe //c "$INIT_BAT" "$PROJECT" 2>&1 || echo "[HOOK-00] init.bat 실행 실패 (계속 진행)"
  else
    echo "[HOOK-00] cmd.exe 없음 - init.bat 건너뜀"
  fi
else
  echo "[HOOK-00] init.bat 없음 - 기본 폴더만 생성"
fi

# Stack 자동 감지 (정보 출력만)
if [ -f "$PROJECT/package.json" ]; then
  if grep -q '"vue".*"\^3' "$PROJECT/package.json" 2>/dev/null; then
    echo "[HOOK-00] Detected: Vue 3"
  elif grep -q '"vue".*"\^2' "$PROJECT/package.json" 2>/dev/null; then
    echo "[HOOK-00] Detected: Vue 2"
  fi
fi
[ -f "$PROJECT/pom.xml" ] && echo "[HOOK-00] Detected: Spring Boot"

# === 농땡이 방지 reminder (매 세션 강제 노출 — 5중 박기 중 1) ===
cat <<'REMINDER'

==============================
 ⚠ 농땡이 방지 5단계 (사용자 지시 처리)
==============================
1. 전수조사  — 인접 시스템·전역까지 모든 위치 훑기
2. 분석      — md5sum/diff/본문으로 내용 검증 (파일명만 보고 단정 X)
3. 실행      — 발견한 문제를 코드로 수정
4. 확인      — smoke test/dry-run/로그 점검
5. 보고      — 표·목록으로 결과 + 남은 결정사항

상세: .claude/rules/failure-mode.md § 농땡이 안티패턴

==============================
 ⚠ Zero-touch 자동화 원칙
==============================
- 사용자 액션 요구 금지 — 모든 셋업은 SessionStart hook 으로 자동
- 알림은 크리티컬 5가지만:
    1) 시크릿 노출  2) 데이터 손실  3) 보안 위협
    4) 비용 폭증    5) 시스템 손상
- 그 외 진행 상황은 침묵 + 로그 (.claude/logs/, .claude/state/)

상세: .claude/rules/best-practices.md § Zero-touch 자동화

==============================
 ⚠ 하드 경로 금지 (cross-machine)
==============================
- 사용자명/Python버전/OS절대경로 박지 말 것
- 동적 검색: where python | tempfile.gettempdir() | %USERPROFILE%
- Task Scheduler 는 wrapper.bat 거쳐 동적 검색
- 검증 grep: C:\\Users\\[a-z]+ / /home/[a-z]+ / Python3[0-9]+

상세: .claude/rules/best-practices.md § 하드 경로 금지
REMINDER

exit 0
