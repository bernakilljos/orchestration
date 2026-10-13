# 앱 UI 표준 룰 (App UI Standard)

> **근거**: 2026-09-02 사용자 지적 — "계산기 이쁘게 해달라 하면 디자인 형편없이 나옴".
> **이유**: 자체 CSS 작성 X · 검증된 디자인 시스템 (shadcn/AntD/MUI) 강제 채택.

## 절대 룰

**앱 UI (계산기·백오피스·CRUD·대시보드·랜딩·폼·차트) 요청 시 자체 CSS 짜지 X · 검증된 디자인 시스템 사용.**

## 디자인 시스템 선택 매트릭스

| 요청 유형 | 1순위 | 2순위 |
|---|---|---|
| **모던 앱·계산기·툴** | **shadcn/ui + Tailwind CSS** (MIT · 커스터마이징 최상) | Chakra UI |
| **엔터프라이즈 백오피스·CRUD·대시보드** | **Ant Design v5** (MIT · 데이터 그리드·폼 강함) | Refine (백오피스 프레임워크) |
| **Material Design** | **MUI v6** (MIT) | — |
| **Headless (자체 스타일)** | **Radix UI** (MIT) | Headless UI |
| **경량·Tailwind 기반 컴포넌트** | **daisyUI** (MIT) | — |
| **접근성 최우선** | **Chakra UI** (MIT) | Radix UI |

## 프레임워크 매트릭스

| 프레임워크 | 라이브러리 조합 |
|---|---|
| **React (default)** | shadcn/ui + Tailwind + Radix + lucide-react (icon) + zod (validation) |
| **Next.js** | 위 + App Router + Server Components |
| **Vue 3** | shadcn-vue + Tailwind or Naive UI |
| **Svelte/SvelteKit** | shadcn-svelte + Tailwind |
| **Vanilla HTML** | Tailwind CDN + daisyUI (프레임워크 없이 즉시) |

## 필수 요소 (자체 CSS 대신)

| 요소 | 라이브러리 |
|---|---|
| Button·Input·Select·Checkbox·Radio | shadcn/AntD/MUI 컴포넌트 |
| Modal·Drawer·Tooltip·Popover | Radix UI (shadcn 기본) |
| DataGrid 대규모 (10k+ rows) | **ag-grid-community** (Apache 2.0 · 무제한 무료) |
| DataTable·Table 간단 (< 1k rows) | AntD Table or shadcn Table |
| DataTable 커스톰 (1k-10k rows) | **TanStack Table v9** + 가상화 |
| Pagination | AntD 또는 Recharts / shadcn custom |
| Form·Validation | react-hook-form v7 + zod |
| Chart (라인·막대·산점도) | **Recharts** (권장) or Apache ECharts |
| Chart (실시간·대용량) | Apache ECharts v5.5 |
| Icon | lucide-react (shadcn 표준) or heroicons |
| Toast·Notification | sonner (shadcn) or AntD notification |
| Date Picker | date-fns + react-day-picker (shadcn) or AntD |
| Command Menu (Cmd+K) | cmdk (shadcn) |
| Color Palette | Tailwind default (slate·zinc·blue 등) or 사용자 지정 |
| State · 비동기 | **Zustand + TanStack Query v5** (권장) |
| Drag & Drop | **dnd-kit v8** (2026 권장) |
| 드래그 정렬 | SortableJS 또는 react-beautiful-dnd |

## 접근성 (A11y) 자동

- WCAG 2.2 AA 이상 준수
- Radix UI·shadcn = ARIA 자동
- 키보드 네비게이션 필수
- 명도 대비 4.5:1 이상

## 반응형 (Responsive) 자동

- Mobile-first (Tailwind 기본)
- Breakpoints: sm(640)·md(768)·lg(1024)·xl(1280)·2xl(1536)
- Flexbox·Grid 자동

## 아이덴티티·브랜드

| 요소 | 표준 |
|---|---|
| 폰트 | **Pretendard** (한국어) + Inter (영어) fallback |
| 색 | Tailwind default palette or 사용자 지정 (CSS 변수) |
| Radius | `rounded-md` (medium) default · Card `rounded-lg` |
| Shadow | `shadow-sm` default · Modal `shadow-lg` |
| Spacing | Tailwind scale (4·8·12·16·24 px) |

## 화면 유형별 템플릿

| 유형 | 필수 요소 |
|---|---|
| **랜딩 페이지** | Header + Hero + Features(3 카드) + CTA + Footer |
| **로그인·회원가입** | Form + Validation + Error 표시 + Loading |
| **대시보드** | Sidebar + Topbar + KPI 카드(4개) + Chart(2~4개) + Table |
| **CRUD 목록** | Search + Filter + Sort + Table + Pagination + Detail Modal |
| **폼** | 그룹핑 + 실시간 Validation + Save/Cancel + Auto-save |
| **계산기·툴** | Input + 결과 + Copy 버튼 + 리셋 |
| **설정** | Sidebar 탭 + 섹션별 그룹핑 + Save |

## 국제화 (i18n)

- **next-intl** (Next.js) or **react-i18next**
- 한국어 default + 영어 fallback
- 리소스: `locales/ko.json`·`locales/en.json`

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

## 사용자 요청 시 자동 라우팅 (ag-grid-recommend 스킬 활성 + 매트릭스)

| 요청 | 자동 선택 | 추가 의존 |
|---|---|---|
| "계산기" | shadcn + Tailwind | Input + Button + Result 표시 |
| "관리자 화면" | AntD + Form + DataGrid | ag-grid (1k+ rows) 또는 AntD Table |
| "대시보드" | shadcn + Recharts + KPI 카드 | TanStack Query (비동기) |
| "랜딩" | shadcn + Tailwind + 반응형 | 애니메이션 = Framer Motion |
| "테이블 1만 건" | **ag-grid-recommend 스킬 → ag-grid community** | 페이지네이션 · 필터 · 정렬 |
| "커스텀 그리드" | **ag-grid-recommend 스킬 → TanStack Table v9** | 완전 제어 · 가상화 |
| "폼 (복잡)" | react-hook-form v7 + zod | Server Actions (Next.js) 또는 Conform |
| "차트 (실시간)" | Apache ECharts v5.5 + TanStack Query | WebSocket 연동 |
| "다크모드" | Tailwind `dark:` class 필수 | shadcn dark mode 기본 지원 |

## 2026 신규 추가

- **ag-grid-recommend 스킬** (`.claude/skills/ag-grid-recommend.md`) — 자동 활성 (그리드·대량 데이터)
- **ui-component-matrix.md** (신규) — 15 카테고리 매트릭스 · 2026 버전 · breaking changes
- **ag-grid 상세 설정 50+** (matrix에 포함) — 성능·라이선스·번들 비교

## 마이그레이션 체크리스트 (2026-10 기준)

| 라이브러리 | 이전 버전 | 신규 버전 | 주의사항 |
|---|---|---|---|
| react-hook-form | v6 | v7 | nested field API 변경 |
| TanStack Table | v8 | v9 | useColumnFilters → useFilters |
| ag-grid | v28-v30 | v32+ | frameworkComponents → components |
| Recharts | v2.x | v5.0 beta | 2026-11 준비 |
| ECharts | v5.4 | v5.5 | GL Renderer 기본 (100k 포인트) |

## 관련

- `plugins/design_web/` (랜딩·포트폴리오·블로그·SEO)
- `plugins/design_system/` (컴포넌트 라이브러리 · ag-grid template 예정)
- CLAUDE.md § 7 E (UI/UX 표준 기존)
- `.claude/rules/teaching-doc.md` (문서 디자인 시스템)
- `.claude/rules/ui-component-matrix.md` (2026 신규 · 15 카테고리 · 성능 비교)
- `.claude/skills/ag-grid-recommend.md` (의사결정 자동화)
- 공식 문서:
  - https://www.ag-grid.com/react-data-grid/
  - https://tanstack.com/table/v9/docs
  - https://recharts.org/
  - https://echarts.apache.org/
