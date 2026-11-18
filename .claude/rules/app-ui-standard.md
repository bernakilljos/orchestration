---
paths:
  - "**/*.tsx"
  - "**/*.jsx"
  - "**/*.vue"
  - "**/*.svelte"
  - "**/*.html"
  - "**/*.css"
  - "**/*.scss"
  - "plugins/design_*/**"
---
# 앱 UI 표준 룰 (App UI Standard)

> **전문**: `.claude/rules-ref/app-ui-standard.md` — 이 규칙이 붙는 파일을 고치기 전에 반드시 Read (사례·매트릭스·이력·근거는 전문에만 있다).
> 2026-11-18 R310: 지시 파일 합계 250K자 > 권장 150K자 경고 해소 — 필수 조항만 여기 남기고 본문은 자동 로딩 밖으로 옮김 (내용 삭제 X).

## 절대 룰

**앱 UI (계산기·백오피스·CRUD·대시보드·랜딩·폼·차트) 요청 시 자체 CSS 짜지 X · 검증된 디자인 시스템 사용.**

## 금지

1. **자체 CSS 대량 작성 X** (10줄 이상 = 재검토) · Tailwind 우선
2. **인라인 style 남발 X** (Tailwind class 우선)
3. **버전 오래된 라이브러리 X** (AntD v4·MUI v4·react-hook-form v6 등 · v5+ 또는 v7+ 만)
4. **KRDS·행안부 코드 직접 배포 X** (라이선스 조건 확인 · 참고만)
5. **다크모드 미지원 X** (`dark:` prefix 필수)
6. **모바일 미대응 X** (반응형 필수)
7. **접근성 무시 X** (aria-label·역할·키보드 필수)
8. **ag-grid 커뮤니티 = 무제한 무료** (enterprise 기능 혼동 X · 라이선스 확인)
9. **자체 그리드 구현** (ag-grid·TanStack Table 있는데 처음부터 만들기 X)
10. **번들 사이즈 300 KB+** (code splitting 없이 증가 X)
