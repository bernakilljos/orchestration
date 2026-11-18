---
paths:
  - "**/*.sql"
  - "**/*.java"
  - "**/mapper/**"
  - "**/*.tsx"
  - "**/*.jsx"
  - "**/*.vue"
  - "**/*.html"
  - ".claude/scripts/smoke-test-screen.sh"
---
# 화면·기능 검증 룰 (Smoke Test 의무)

> **전문**: `.claude/rules-ref/screen-verify.md` — 이 규칙이 붙는 파일을 고치기 전에 반드시 Read (사례·매트릭스·이력·근거는 전문에만 있다).
> 2026-11-18 R310: 지시 파일 합계 250K자 > 권장 150K자 경고 해소 — 필수 조항만 여기 남기고 본문은 자동 로딩 밖으로 옮김 (내용 삭제 X).

## 절대 룰

**DB / API / 프론트 변경 후 사용자에게 "확인해 주세요" 금지.** 자동 smoke test → PASS 후 보고.

## 금지

1. **"확인해 주세요" 떠넘김** — AI 가 직접 curl·render·log 점검
2. **"다음부터는" 약속만** — 코드/룰/hook 으로 시스템화
3. **smoke test 결과 PASS 무시** — FAIL 이면 자동 재시도 (max 3회)
4. **null check 없는 코드 PASS** — NPE 패턴 grep 으로 사전 차단
5. **endpoint 영향 분석 skip** — DB 변경 시 모든 endpoint 추적
