# design_system — 40년차 초특급 공통 디자인

> **근거**: 2026-10-13 사용자 지적 — "공통 레이아웃·버튼·표·그리드 없어 매번 안 맞고 줄바꿈 잦음".

## 구조

```text
plugins/design_system/
├── SKILL.md               자동 활성 skill (화면·대시보드·CRUD 요청 감지)
├── plugin.json
├── README.md
├── tokens/
│   └── all.css            CSS 변수 통합 (color·typo·spacing·radius·shadow·motion·z-index · dark mode)
├── components/
│   ├── core.tsx.template          Button·Input·Table·Card·Modal
│   ├── DataGrid.tsx.template      ag-grid community (1k~1M rows)
│   ├── Form.tsx.template          react-hook-form v7 + zod
│   └── Layout.tsx.template        AppShell·Container·Grid·PageHeader
├── patterns/
│   ├── dashboard.tsx.template     Sidebar + KPI 4 + Chart 2 + Table
│   └── crud-list.tsx.template     Search + DataGrid + Modal + Form
├── commands/
│   └── design-apply.md            /design-apply <pattern|component>
└── hooks/                         (예정) pre-write component check
```

## 선택 조합

| 요청 | 1순위 조합 |
|---|---|
| 대시보드 | shadcn + Tailwind + Recharts + TanStack Query |
| CRUD 10k+ rows | **ag-grid community** (Apache 2.0 무료) |
| CRUD 1k rows | shadcn Table + react-hook-form + zod |
| 랜딩 | shadcn + Tailwind + Framer Motion |
| 폼 복잡 | react-hook-form v7 + zod |
| 차트 실시간 | Apache ECharts v5.5 + WebSocket |

## 설치 (target 프로젝트)

```bash
npm install -D tailwindcss@latest postcss autoprefixer
npm install class-variance-authority clsx tailwind-merge lucide-react
npm install @radix-ui/react-dialog
npm install react-hook-form zod @hookform/resolvers
npm install ag-grid-community ag-grid-react
npm install recharts
# dark mode
# tailwind.config: darkMode: "class"
```

## 사용 (사용자가 kit install 후)

```bash
# 자동 (사용자 요청 어휘 감지)
"대시보드 화면 만들어줘" → SKILL.md 활성 → design-apply dashboard

# 수동
/design-apply dashboard
/design-apply crud-list
/design-apply tokens
```

## 40년차 수준 증명

| 축 | 보장 |
|---|---|
| 접근성 | WCAG 2.2 AA · ARIA · 키보드 네비 · focus-visible 처리 |
| 반응형 | Mobile-first · sm·md·lg·xl·2xl 자동 |
| 다크모드 | `.dark` class · 모든 토큰 light/dark 쌍 |
| 성능 | ag-grid 가상화 1M rows · react-hook-form uncontrolled |
| 타입 안전 | TypeScript strict · zod runtime validation |
| 국제화 | 한글 default + aria-label 한글 |
| 다운그레이드 | prefers-reduced-motion 존중 |
| 일관성 | 모든 간격·색·radius·shadow = 디자인 토큰 |

## 관련 룰·스킬

- `.claude/rules/app-ui-standard.md` (매트릭스 SoT)
- `.claude/rules/ui-component-matrix.md` (2026 15 카테고리)
- `.claude/skills/ag-grid-recommend.md` (DataGrid 자동 추천)
