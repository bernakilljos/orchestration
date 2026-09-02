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
| DataTable·DataGrid·Pagination | AntD Table or TanStack Table + shadcn |
| Form·Validation | react-hook-form + zod |
| Chart | Recharts or Apache ECharts |
| Icon | lucide-react (shadcn 표준) or heroicons |
| Toast·Notification | sonner (shadcn) or AntD notification |
| Date Picker | date-fns + react-day-picker (shadcn) or AntD |
| Command Menu (Cmd+K) | cmdk (shadcn) |
| Color Palette | Tailwind default (slate·zinc·blue 등) or 사용자 지정 |

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

1. **자체 CSS 대량 작성 X** (10줄 이상 = 재검토)
2. **인라인 style 남발 X** (Tailwind class 우선)
3. **버전 오래된 라이브러리 X** (AntD v4·MUI v4 등 · v5+ 만)
4. **KRDS·행안부 코드 직접 배포 X** (라이선스 조건 확인 · 참고만)
5. **다크모드 미지원 X** (`dark:` prefix 필수)
6. **모바일 미대응 X** (반응형 필수)
7. **접근성 무시 X** (aria-label·역할·키보드)

## 사용자 요청 시 자동 적용

- "계산기 만들어" → shadcn + Tailwind + 필수 요소
- "관리자 화면" → AntD + DataTable + Form
- "대시보드" → shadcn + Recharts + KPI 카드
- "랜딩" → shadcn + Tailwind + 반응형

## 관련

- `plugins/design_web/` (랜딩·포트폴리오·블로그·SEO)
- CLAUDE.md § 7 E (UI/UX 표준 기존)
- `.claude/rules/teaching-doc.md` (문서 디자인 시스템)
