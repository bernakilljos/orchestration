---
name: design-system
description: 40년차 초특급 공통 디자인 시스템. 사용자가 "화면·대시보드·CRUD·폼·그리드·버튼·표·레이아웃" 요청 시 자동 활성. shadcn/ui + Tailwind + ag-grid + react-hook-form + zod 조합. 매번 안 맞던 레이아웃·줄바꿈 문제 해결. 운영 바로 사용 가능 수준.
---

# Design System — 40년차 초특급 공통 (plugins/design_system)

**근거**: 2026-10-13 사용자 지적 — "공통 레이아웃·버튼·표·그리드 없어서 매번 안 맞고 줄바꿈 잦음".

**원칙**: 자체 CSS 작성 X · 검증 라이브러리만 · 운영 바로 가능.

## 구조

```text
plugins/design_system/
├── tokens/        디자인 토큰 (CSS 변수) — colors·typography·spacing·radius·shadow·breakpoints
├── components/    React 컴포넌트 템플릿 — Button·Table·DataGrid·Form·Modal·Layout·Card
├── patterns/      화면 패턴 — dashboard·crud-list·landing·login·form-page·settings
├── commands/      /design-apply <pattern>
└── hooks/         pre-write-component-check (디자인 토큰 사용 검증)
```

## 적용 매트릭스 (업계 40년차 조합)

| 요청 | 1순위 조합 | 2026 이유 |
|---|---|---|
| **대시보드** | shadcn/ui + Tailwind + Recharts + TanStack Query | 유연성 + 가볍 + 반응형 자동 |
| **CRUD 1k rows** | shadcn Table + react-hook-form v7 + zod | 완전 커스텀 가능 |
| **CRUD 10k+ rows** | **ag-grid community** (Apache 2.0 무료) | 가상화·정렬·필터·그룹·pivot 모두 |
| **엔터프라이즈 관리자** | Ant Design v5 + ag-grid | 바로 운영 가능 완성도 |
| **랜딩·마케팅** | shadcn + Tailwind + Framer Motion | 애니메이션 자연 |
| **계산기·툴** | shadcn + Tailwind (Button + Input + Result) | 최소 번들 |
| **폼 복잡 (20+ 필드)** | react-hook-form v7 + zod + Conform | 성능 + 검증 |
| **차트 실시간** | Apache ECharts v5.5 + WebSocket | 100k+ 포인트 OK |

## 자동 활성 트리거

사용자 메시지에 다음 어휘 → 이 skill 자동 활성:
- "화면·페이지·대시보드·관리자·백오피스·CRUD·목록·상세"
- "폼·입력·그리드·테이블·차트·버튼·레이아웃"
- "운영·실전·배포·launch·production"
- "ag-grid·TanStack·shadcn·AntD·MUI"
- "이쁘게·세련·프로페셔널·40년차·초특급"

## 사용법

```bash
# 자동 (사용자 요청 시)
"대시보드 만들어줘" → 이 skill 자동 활성 → patterns/dashboard.tsx.template 스캐폴드

# 수동
/design-apply dashboard
/design-apply crud-list
/design-apply landing
```

## 금지

1. 자체 CSS 10줄+ 작성 X (Tailwind utility 우선)
2. 인라인 style X (Tailwind class)
3. 디자인 토큰 외 하드코딩 색·폰트·간격 X
4. shadcn 있는데 자체 Button·Input·Modal 재구현 X
5. ag-grid 있는데 DataGrid 자체 구현 X
6. 다크모드 미지원 X (`dark:` prefix 필수)
7. 모바일 미대응 X (반응형 필수)
8. 접근성 무시 X (ARIA·키보드)

## 관련

- `.claude/rules/app-ui-standard.md` (매트릭스 SoT)
- `.claude/rules/ui-component-matrix.md` (2026 15 카테고리 상세)
- `.claude/skills/ag-grid-recommend.md` (DataGrid 자동 추천)
