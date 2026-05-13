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

# === 전수조사 위반 방지 reminder (매 세션 강제 노출 — 5중 박기 중 1) ===
cat <<'REMINDER'

==============================
 ⚠ 전수조사 5단계 의무 (사용자 지시 처리)
==============================
1. 전수조사  — 인접 시스템·전역까지 모든 위치 훑기
2. 분석      — md5sum/diff/본문으로 내용 검증 (파일명만 보고 단정 X)
3. 실행      — 발견한 문제를 코드로 수정
4. 확인      — smoke test/dry-run/로그 점검
5. 보고      — 표·목록으로 결과 + 남은 결정사항

상세: .claude/rules/failure-mode.md § 전수조사 위반 안티패턴

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
 ⚠ Template Kit 원칙 (공통 폴더 적용)
==============================
- orchestration_v1 은 다른 폴더에 install 로 배포되는 공통 kit
- ~/.claude/ 직접 수정 X → setup/templates/ + setup/modules/03-settings.bat
- 다른 프로젝트 폴더 (ICM/IFRS/calc 등) 직접 수정 X → install 재배포
- 새 파일·기능마다 자문: "다른 머신·다른 사용자에서도 동작?"
                          "install 로 자동 배포?"
                          "사용자 액션 0개?"

상세: .claude/rules/best-practices.md § Template kit 원칙

==============================
 ⚠ 교재·강의 doc 작성 시 8섹션 + 다이어그램 품질 의무
==============================
- 각 챕터: 핵심 / 표 / 흐름 / 강점 / 약점 / 강추 / 우리시스템 매핑 / 점검
- 외국어 이미지 → 한글 다이어그램으로 "대체" (영어+한글 X, 한글만)
- 다이어그램 = SVG/HTML 기반 + 화살표 + 흐름 (단순 박스/표 = 위반)
- 도구 우선순위: HTML/CSS+SVG (Playwright) > Mermaid > matplotlib
- 5살 청자 톤. 비유·일상 예시

==============================
 ⚠ 산출물 버전 접미사 금지 (-v2, -v3)
==============================
- docx/pptx/pdf 빌드 시 잠금 폴백으로 -v2 만들기 X
- 백업 + 덮어쓰기: original.docx.bak 만들고 original.docx 덮어쓰기
- 원본 잠겨있으면 사용자에게 알림 ("원본 닫아주세요")
- 버전은 사용자 명시 요청 시만

상세: .claude/rules/teaching-doc.md § 산출물 명명

==============================
 ⚠ 수정·빌드 후 자동 검증 후 보고
==============================
- "수정했습니다" 만 보고 X
- 검증 도구 자동 실행 → PASS 확인 → 보고
- FAIL → 사용자 알리지 않고 자동 재수정 (max 3)
- 3회 후 FAIL → 솔직히 보고 + 사용자 결정
- 검증: PNG=verify-image-fit / docx=verify-docx-structure / pptx=verify-ppt-overflow

==============================
 ⚠ 회피·딴말 금지
==============================
- 사용자 질문 빙빙 돌리지 마 — 직접 답 (yes/no/숫자) → 부연 → 행동
- "그건 그렇지만"·"여러 옵션이 있는데" = 회피
- 결함 지적 → 시스템 자랑 = 위반

==============================
 ⚠ docx 구조 검증 (빈 페이지·중복 break)
==============================
- build-*-doc.py 후 verify-docx-structure.py 자동 발동 (hook-09)
- 빈 paragraph 5개+ 연속·중복 page_break 감지
- "빈 페이지 있네" 사용자 지적 후 fix = 전수조사 위반

==============================
 ⚠ Auto-Planner 자동 활성 (사용자 요청 받자마자)
==============================
- "해줘"·"고쳐줘"·결함 지적 받자마자 5단계 plan 생성
  1) 전수조사  2) 분석  3) 실행  4) 확인  5) 보고
- 작업 전 30+ rule 자가 점검
- 큰 작업·반복 패턴 = codex/gemini 위임
- 사용자가 매번 지시 기다림 X (Generative→Agentic 약점 보완)

skill: plugins/exec_orch/skills/auto-planner.md

==============================
 ⚠ 페이지 전체 콘텐츠 fit (H1+callout+이미지+표 합산)
==============================
- 이미지 비율만 X — 페이지의 모든 요소 height 합산
- 빈 여백·짤림·글씨 작음 = 같은 문제
- 빌더에 PageLayoutTracker (skill auto-layout-fit) 의무
- 사용자가 "여백 큰데"·"짤려" 한 후 fix = 전수조사 위반

상세: .claude/rules/teaching-doc.md § 페이지 콘텐츠 fit
       skill: plugins/exec_orch/skills/auto-layout-fit.md

==============================
 ⚠ 페이지 fit 검증 (docx · pptx · pdf 전체)
==============================
- 모든 산출물 (docx · pptx · pdf · html) 페이지 비율 측정 의무
- 산출물별 비율 (h/w):
    docx portrait 1.46 · landscape 0.69
    pptx 16:9 0.54 · 4:3 0.71
    pdf portrait 1.41 · landscape 0.71
- PNG viewport 비율 = 페이지 비율 (full_page=False + clip)
- 자동 검증: verify-image-fit.py + hook-09 (build/generate/render-* 트리거)

상세: .claude/rules/teaching-doc.md § 페이지 fit 검증

==============================
 ⚠ 하드 경로 금지 (cross-machine)
==============================
- 사용자명/Python버전/OS절대경로 박지 말 것
- 동적 검색: where python | tempfile.gettempdir() | %USERPROFILE%
- Task Scheduler 는 wrapper.bat 거쳐 동적 검색
- 검증 grep: C:\\Users\\[a-z]+ / /home/[a-z]+ / Python3[0-9]+

상세: .claude/rules/best-practices.md § 하드 경로 금지

==============================
 ⚠ 오염 파일 자동 정리 (SessionStart hook)
==============================
- nul / NUL (Windows redirect 잔재) — 즉시
- nested .claude/.claude/ — 즉시
- 3일+ *.bak / *.tmp / *.orig / *.swp / *~
- 14일+ .claude/logs/*.log
- 30일+ .claude/tasks/done/*
- 7일+ ~/.claude/projects/*/tool-results/*
- 빈 .claude/tasks/{done,locks} 디렉토리

스크립트: .claude/scripts/cleanup-pollution.sh (매 세션 자동 실행)
금기: bash 환경에 `2>nul` 사용 X → `2>/dev/null` 사용
PROJECT_ROOT 계산: 위치별 ../.. 깊이 주의

상세: .claude/rules/cleanup-policy.md
REMINDER

exit 0
