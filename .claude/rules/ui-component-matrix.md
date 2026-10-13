# UI 컴포넌트 라이브러리 매트릭스 (2026)

> **근거**: 2026-10-13 · ag-grid 커뮤니티·2026 신규 라이브러리·프레임워크별 최적 조합 통합.
> **이유**: 단순 "AntD vs shadcn" 이상으로 데이터 특성·성능·라이선스별 정밀 선택 필수. ag-grid 등 대규모 그리드·차트·폼 라이브러리 급격한 변화.

## 절대 룰

**UI 요청 = 이 매트릭스로 1순위·2순위·2026 신규 선택. 자체 구현 금지. 라이선스·성능·번들 사이즈 가중.**

## 15 카테고리 라이브러리 매트릭스 (2026-10-13)

### 1. DataGrid / 대규모 테이블 (10k+ rows)

| 기준 | 1순위 | 2순위 | 2026 신규 · 주의 |
|---|---|---|---|
| **ag-grid community** (Apache 2.0 · 무료 · 무제한) | ✅ 설정 50+ · sorting·filtering·grouping·pivot·editing·export·pinned | TanStack Table v9 + 가상화 (headless) | AG Grid v33 beta (2026 Q1 예정 · breaking) |
| **성능** | 100k rows O · 메모리 최적화 · row virtualization | 10k-50k 권장 | — |
| **커스터마이징** | 높음 (frameworkComponents) | 극도로 높음 | — |
| **초기 학습곡선** | 중간 (API 복잡) | 낮음 (headless) | — |
| **편의성** | 매우 높음 (preset defaults) | 낮음 (조립식) | — |
| **활용처** | 백오피스·대시보드·감시 시스템 | 커스텀 고성능 테이블 | — |
| **라이선스** | Apache 2.0 · 상용 OK | MIT | — |

**ag-grid 2026 Breaking Changes**:
- `frameworkComponents` → `components` (v31, 2025-11 완료)
- `colDef.cellRenderer` 함수형만 권장 (클래스형 deprecated)
- v33 예정: ICE (Island Cell Expansion) + async data source native
- v32.2 (2026-09): Server-side row model 성능 40% 향상

**TanStack Table v9** (2026-09):
- **핵심 변화**: `useColumnFilters` → `useFilters` API (v9 마이그레이션 필수)
- **신규**: Row pinning native (ag-grid 기능 커버)
- **신규**: Async virtual scroller (50k rows 실시간)
- **한계**: 편의성 떨어짐 · 기능 구현 100% 직접

### 2. 간단한 테이블 / CRUD 목록 (< 1k rows)

| 기준 | 1순위 | 2순위 |
|---|---|---|
| **shadcn Table** (React) | Radix + 스타일·선택·정렬 자동 | — |
| **AntD Table v5** | 한국어·locale 강력·폼 통합 | — |
| **TanStack Table v9 headless** | 가벼움·커스텀 UI | 복잡도 증가 |
| **편의성** | shadcn·AntD 1순위 | — |
| **번들 크기** | shadcn < AntD | — |

### 3. 폼 · 검증

| 기준 | 1순위 | 2순위 | 검증 라이브러리 |
|---|---|---|---|
| **react-hook-form v7** (2026-09 최신) | Zero dependency · 가볍고 빠름 | — | **zod** (TypeScript 우선) |
| **성능** | 매우 빠름 (재렌더 최소) | — | — |
| **DX** | 중간 (useForm hook) | — | — |
| **검증** | 외부 라이브러리 연동 | — | **valibot v1** (zod 경량 대체, 2026 성장 중) |
| **Advanced** | Server Actions (Next.js) | — | **Conform** (form mutation 자동) |
| **주의** | v7 마이그레이션 (nested field API) | — | — |

**2026 신규 선택지**:
- **Conform** (Remix/Next.js Server Actions 최적화, 2026-10 성숙도 높음)
- **Valibot v1** (zod 대비 80% 경량, 한국·아시아 커뮤니티 성장)

### 4. 차트 · 데이터 시각화

| 기준 | 1순위 | 2순위 | 3순위 | 2026 신규 |
|---|---|---|---|---|
| **라인·막대·산점도** | **Recharts** (React 전용·선언형·쉬움) | Apache ECharts (다양한 차트) | Victory | — |
| **고급 차트** | Apache ECharts | Nivo | Visx | — |
| **인터랙티브** | Plotly.js (대용량) | D3.js (완전 제어) | Vega-Lite | — |
| **AG Charts** (ag-grid 전용) | ag-grid 안에 **종속 license** (enterprise만 무료) | — | — | 2026-10 성숙도 높음 |
| **실시간** | Recharts + framer-motion | TradingView Lightweight Charts | — | — |
| **성능** (10k+ 데이터 포인트) | ECharts > D3 > Recharts | — | — | — |
| **권장** | 대부분 프로젝트 = Recharts | 감시·대시보드 = ECharts | — | — |

**2026 주의**:
- **AG Charts**: ag-grid enterprise-only (2026-10 정책 변화 없음). 무료는 Recharts/ECharts 유지.
- **Recharts 5.0** (2026-09 beta): Composition API 강화 · performance 개선
- **Apache ECharts v5.5** (2026-10): GL Renderer 기본 · 100k 포인트 O

### 5. 아이콘

| 기준 | 라이브러리 |
|---|---|
| **shadcn 기본** | **lucide-react** (MIT · 깔끔 · 한국 커뮤니티) |
| **다양성** | heroicons · Font Awesome |
| **커스텀** | SVG 직접 (최소한) |

### 6. UI 컴포넌트 라이브러리

| 프레임워크 | 1순위 | 2순위 | 한계 |
|---|---|---|---|
| **React** | **shadcn/ui v2** (MIT · headless + radix · 자동화) | Chakra UI | Enterprise 기능 제한 |
| **Next.js** | shadcn/ui + App Router | Refine (admin framework) | — |
| **Vue 3** | shadcn-vue (porting) | Naive UI | shadcn-vue 커뮤니티 작음 |
| **Svelte** | shadcn-svelte | daisyUI | 커뮤니티 작음 |
| **엔터프라이즈** | **Ant Design v5** (중국·아시아 강함·한국 지원) | Material-UI v6 | 번들 크기 큼 |

### 7. 상태 관리 (State)

| 기준 | 1순위 | 2순위 | 주의 |
|---|---|---|---|
| **경량 store** | **Zustand** (MIT · 가벼움 · TypeScript) | Jotai (atom 기반) | Redux 100% 대체 권장 X |
| **비동기 관리** | **TanStack Query v5** (React Query) | SWR (Vercel · 경량) | **필수** (API 캐싱) |
| **고급** | Recoil (Meta 후원 중단) | Valtio (proxy 기반) | Recoil 신규 X |
| **2026 신규** | **Relay** (GraphQL 최적화) | — | GraphQL only |

**2026 권장 조합**: Zustand + TanStack Query (대부분 프로젝트 족함)

### 8. 애니메이션

| 용도 | 라이브러리 |
|---|---|
| **페이지 전환** | Framer Motion 또는 React Spring |
| **마이크로 인터랙션** | Framer Motion (권장) |
| **CSS 애니메이션** | Tailwind (animate-* 기본) |
| **금지** | 자체 keyframes (Tailwind 우선) |

### 9. 국제화 (i18n)

| 프레임워크 | 1순위 |
|---|---|
| **Next.js** | **next-intl** (App Router 최적화) |
| **React** | **react-i18next** (표준) |
| **Vue** | vue-i18n |

### 10. 날짜 선택

| 요구 | 라이브러리 |
|---|---|
| **React** | date-fns + react-day-picker (shadcn) 또는 AntD DatePicker |
| **범위 선택** | react-date-range 또는 react-big-calendar |
| **시간** | time-picker (AntD) 또는 react-time-picker |

### 11. 명령어 팔레트 (Cmd+K)

| 용도 | 라이브러리 |
|---|---|
| **shadcn** | **cmdk** (MIT · 가벼움) |
| **대안** | kbar · command-palette-js |

### 12. 드래그&드롭

| 용도 | 라이브러리 |
|---|---|
| **dnd** | **react-beautiful-dnd** (Atlassian) 또는 **dnd-kit** (2026 권장) |
| **sortable** | SortableJS 또는 dnd-kit |
| **2026** | dnd-kit v8 (performance 개선 · Aria 강화) |

### 13. 입력 마스킹 · 포맷팅

| 용도 | 라이브러리 |
|---|---|
| **전화·카드** | **react-input-mask** 또는 **imask** |
| **통화** | **dinero.js** + 자체 포매터 |

### 14. 토스트 / 알림

| 요구 | 라이브러리 |
|---|---|
| **shadcn** | **sonner** (MIT · modern) |
| **AntD** | AntD notification 내장 |
| **고급** | react-toastify |

### 15. 색상 선택기

| 요구 | 라이브러리 |
|---|---|
| **간단** | input type="color" (native) |
| **고급** | react-color 또는 tinycolor2 |

---

## 성능 기준 (선택 판단)

### 번들 사이즈 (gzip)

| 라이브러리 | 크기 |
|---|---|
| Zustand | 2.2 KB |
| TanStack Query | 37 KB |
| react-hook-form | 8.5 KB |
| shadcn Button | 0.5 KB |
| Recharts | 65 KB |
| ag-grid-community | 900 KB |
| AntD | 500 KB |

**원칙**: 번들 < 200 KB 목표 (초기 로드). 대규모 앱 = code splitting 필수.

### 성능 체크리스트

- [ ] 메모리 누수 테스트 (DevTools)
- [ ] LCP < 2.5s (Lighthouse)
- [ ] FID < 100ms (상호작용)
- [ ] CLS < 0.1 (layout shift)

---

## 라이선스 정리

| 라이브러리 | 라이선스 | 상용 OK | 주의 |
|---|---|---|---|
| shadcn/ui | MIT |  | 상용 자유 |
| ag-grid-community | Apache 2.0 |  | 무료 무제한 |
| Recharts | Apache 2.0 |  | — |
| react-hook-form | MIT |  | — |
| Zustand | MIT |  | — |
| TanStack Query | MIT |  | — |
| AntD | MIT |  | 커뮤니티 강함 |
| MUI | MIT |  | Material Design 강제 |
| AG Charts | 특수 | ⚠️ 조건부 | ag-grid enterprise 연동 시만 무료 |

---

## 2026 신규 도입 기준

| 신기술 | 도입 시점 | 우리 kit |
|---|---|---|
| **Conform** (Server Actions) | Next.js App Router 필수 | 도입 권장 (2026-10 성숙) |
| **Valibot** | zod 경량 필요 시 | 옵션 (테스트 후) |
| **dnd-kit v8** | 드래그 성능 중요 | 도입 권장 |
| **Recharts 5.0** | 차트 성능 | 2026-11 대기 후 |
| **TanStack Table v9** | 대규모 그리드 | 마이그레이션 가이드 필요 |
| **AG Grid v33** | ag-grid 커뮤니티 | 2026-12 점검 |

---

## ag-grid 상세 설정 50+ (커뮤니티 free tier)

### 기본 설정

```typescript
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';

<AgGridReact
  // 데이터
  rowData={data}
  columnDefs={columns}
  
  // 행 높이·비비너 (v32+)
  rowHeight={35}
  headerHeight={40}
  
  // 정렬·필터
  enableSorting={true}
  enableFilter={true}
  
  // 행 선택
  rowSelection={{ mode: 'multiRow' }}
  
  // 라우팅·가상화
  rowBuffer={10}
  
  // 페이지네이션 (서버 사이드 권장)
  pagination={true}
  paginationPageSize={50}
/>
```

### 50+ 설정 카테고리

1. **행 데이터**: `rowData`, `rowKey`, `getRowId`
2. **컬럼 정의**: `columnDefs`, `defaultColDef`, `autoGroupColumnDef`
3. **정렬**: `enableSorting`, `sortingOrder`, `multiSortKey`
4. **필터**: `enableFilter`, `filterModel`, `advancedFilterModel` (v32)
5. **그룹화**: `groupDisplayType`, `rowGroupPanelShow`, `autoGroupColumnDef`
6. **피벗**: `pivotMode`, `pivotPanelShow`, `pivotRowTotals`
7. **핀 (고정)**: `pinnedTopRowData`, `pinnedBottomRowData`
8. **행 높이**: `rowHeight`, `getRowHeight`, `rowHeightState`
9. **가상화**: `rowBuffer`, `rowVirtualizationDisabled`
10. **선택**: `rowSelection`, `checkboxSelection`, `suppressRowClickSelection`
11. **편집**: `editType`, `stopEditingWhenCellLoseFocus`, `onCellValueChanged`
12. **셀 렌더**: `cellRenderer`, `cellRendererParams`, `cellEditor`
13. **애니메이션**: `animateRows`, `allowShowChangeAfterFilter`
14. **익스포트**: `excelStyles`, `columnTypes`
15. **테마**: `theme: { quartz, alpine, balham }`
... (35+ 추가)

**상세**: ag-grid docs · 설정별 스킬 작성 예정.

---

## 사용자 요청 시 자동 라우팅

| 요청 | 자동 선택 |
|---|---|
| "그리드"·"테이블"·"데이터 1만 건" | ag-grid community |
| "테이블" + "간단" | shadcn Table 또는 AntD Table |
| "대시보드" | shadcn + Recharts + KPI |
| "폼" | react-hook-form + zod |
| "관리자" | AntD 또는 ag-grid |
| "실시간 추적" | ECharts + TanStack Query |

---

## 금지

1. **ag-grid 커뮤니티 = 무제한 무료** (enterprise 혼동 X)
2. **자체 그리드 구현** (ag-grid·TanStack 있는데)
3. **번들 300 KB+** (code splitting 없이)
4. **오래된 버전** (v28 이하 · 2026-10 기준)
5. **라이선스 무시** (상용 목적 시 확인)

---

## 마이그레이션 체크리스트 (기존 프로젝트)

- [ ] ag-grid frameworkComponents → components 변환
- [ ] TanStack Table v9 API 마이그레이션 (useColumnFilters → useFilters)
- [ ] react-hook-form v7 nested field 업데이트
- [ ] Recharts 5.0 준비 (2026-11 예정)
- [ ] AG Grid v33 breaking changes 검토 (2026-12)

---

## 관련

- `.claude/rules/app-ui-standard.md` (기본 원칙)
- `plugins/design_system/` (컴포넌트 라이브러리)
- `.claude/skills/ag-grid-recommend.md` (신설 · ag-grid 의사결정)
- `plugins/design_web/` (웹 디자인 플러그인)
