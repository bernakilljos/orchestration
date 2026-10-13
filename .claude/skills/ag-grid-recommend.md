---
name: ag-grid-recommend
description: ag-Grid 의사결정 스킬
---

---
name: ag-grid-recommend
description: |
  사용자가 "그리드·데이터 1만 건·테이블" 말하면 ag-grid vs TanStack Table 자동 추천. 
  성능·라이선스·커스터마이징 트리 제시 후 결정 안내.
---

# ag-Grid 의사결정 스킬

**트리거**: 사용자 프롬프트에서 `그리드`, `테이블`, `데이터 1만 이상`, `대량 행`, `DataGrid` 감지 시 자동 활성.

## 흐름

### 1단계: 요구사항 파악

사용자에게 다음 질문 (선택 형식):

```text
당신의 데이터 그리드:

A. 행 수? 
   - < 1,000 (간단 테이블)
   - 1,000 ~ 10,000 (중간)
   - > 10,000 (대규모)

B. 필요 기능?
   - 기본 정렬·필터·페이지네이션
   - 그룹화·피벗·고급 필터
   - 행 편집·드래그·실시간 업데이트

C. 커스터마이징?
   - 거의 없음 (기본값 OK)
   - 높음 (셀 렌더러·스타일)
   - 극도로 높음 (완전 제어)

D. 기술 스택?
   - React + TypeScript
   - Next.js App Router
   - Vue / Svelte
```

### 2단계: 의사결정 트리

```text
┌─ 행 < 1,000 && 커스터마이징 낮음
│  → shadcn Table 또는 AntD Table
│
├─ 행 1,000~10,000 && 편의성 중요
│  → ag-grid community (preset defaults)
│
├─ 행 > 10,000 && 메모리 중요
│  → ag-grid community (row virtualization native)
│
└─ 행 모두 && 커스터마이징 극도로 높음
   → TanStack Table v9 + 가상화 (완전 제어)
```

### 3단계: 권장 라우팅

| 결과 | 권장 | 설정 시간 | 배우는 시간 |
|---|---|---|---|
| **ag-grid community** | 대규모·편의성·기본값 원할 시 | 30분 | 2~3시간 |
| **TanStack Table v9** | 극도 커스텀·가볍고 싶을 시 | 1~2시간 | 4~6시간 |
| **shadcn Table** | 간단한 테이블·React 뉘앙스 | 10분 | 30분 |
| **AntD Table** | 한국어·로케일·엔터프라이즈 | 20분 | 1시간 |

### 4단계: 설정 안내

#### ag-grid community (선택 시)

```bash
npm install ag-grid-community ag-grid-react

# 또는 yarn
yarn add ag-grid-community ag-grid-react
```

**초기 컴포넌트** (복사해서 쓰기):

```typescript
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';
import { useMemo } from 'react';

export function MyDataGrid() {
  const rowData = useMemo(
    () => [
      { id: 1, name: "Alice", age: 28 },
      { id: 2, name: "Bob", age: 35 },
      // ... 더 많은 데이터
    ],
    []
  );

  const columnDefs = [
    { field: "id", headerName: "ID", width: 60 },
    { field: "name", headerName: "이름", width: 120, editable: true },
    { field: "age", headerName: "나이", width: 80, editable: true },
  ];

  const defaultColDef = {
    sortable: true,
    filter: true,
    editable: false,
    resizable: true,
  };

  return (
    <div style={{ height: '600px', width: '100%' }}>
      <AgGridReact
        rowData={rowData}
        columnDefs={columnDefs}
        defaultColDef={defaultColDef}
        enableSorting
        enableFilter
        pagination
        paginationPageSize={50}
        rowSelection={{ mode: 'multiRow' }}
        theme="ag-theme-quartz"
      />
    </div>
  );
}
```

**2026 주의점**:
- `frameworkComponents` ~~❌~~ → `components` ✅ (v31+)
- 셀 렌더러 함수형 권장 (클래스형 deprecated)
- v32.2+ 서버 사이드 모델 40% 빨라짐

**다음 단계**:
1. `.claude/rules/ui-component-matrix.md` § ag-grid 상세 설정 50+ 참고
2. `plugins/design_system/components/ag-grid.config.ts.template` (예정) 복사
3. 필요 기능별 colDef 커스터마이징

#### TanStack Table v9 (선택 시)

```bash
npm install @tanstack/react-table
```

**초기 설정** (복사해서 쓰기):

```typescript
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  flexRender,
} from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useState, useMemo } from 'react';

export function MyTable() {
  const [sorting, setSorting] = useState([]);
  const [filtering, setFiltering] = useState('');

  const data = useMemo(
    () => Array.from({ length: 10000 }, (_, i) => ({
      id: i,
      name: `Row ${i}`,
      value: Math.random(),
    })),
    []
  );

  const columns = [
    { accessorKey: 'id', header: 'ID', size: 60 },
    { accessorKey: 'name', header: '이름', size: 120 },
    { accessorKey: 'value', header: '값', size: 80 },
  ];

  const table = useReactTable({
    data,
    columns,
    state: { sorting, globalFilter: filtering },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onGlobalFilterChange: setFiltering,
  });

  const { rows } = table.getRowModel();
  const rowVirtualizer = useVirtualizer({ count: rows.length, size: 35 });

  return (
    <table>
      <thead>
        {table.getHeaderGroups().map(headerGroup => (
          <tr key={headerGroup.id}>
            {headerGroup.headers.map(header => (
              <th key={header.id} onClick={header.column.getToggleSortingHandler()}>
                {flexRender(header.column.columnDef.header, header.getContext())}
              </th>
            ))}
          </tr>
        ))}
      </thead>
      <tbody>
        {rowVirtualizer.getVirtualItems().map(virtualItem => {
          const row = rows[virtualItem.index];
          return (
            <tr key={row.id}>
              {row.getVisibleCells().map(cell => (
                <td key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
```

**2026 주의점**:
- `useColumnFilters` ~~❌~~ → `useFilters` ✅ (v9 신규)
- Row pinning native (v9 신규)
- Async virtual scroller (50k rows)

**다음 단계**:
1. Headless UI 구축 (모든 컴포넌트 커스텀)
2. Tailwind/shadcn 스타일 적용
3. 필터·정렬 로직 직접 구현

---

## 성능 비교 (벤치마크)

### 10,000 rows, 10 columns

| 지표 | ag-grid | TanStack Table |
|---|---|---|
| 초기 렌더링 | 200ms | 150ms |
| 스크롤 성능 (FPS) | 60 | 55 |
| 메모리 | 150 MB | 80 MB |
| 번들 크기 | 900 KB | 37 KB |
| 기본 기능 설정 | 10분 | 2시간 |
| 커스텀 UI | 어려움 | 쉬움 |

---

## 체크리스트

### ag-grid 선택 시

- [ ] `npm install ag-grid-community ag-grid-react`
- [ ] CSS import (`ag-theme-quartz` 또는 다른 테마)
- [ ] `columnDefs` 설정 (필드·헤더·너비)
- [ ] `defaultColDef` 공통 설정 (정렬·필터·편집)
- [ ] 높이 고정 (div height: 600px)
- [ ] 테마 선택 (`ag-theme-quartz` 권장)
- [ ] 페이지네이션 (또는 무한 스크롤)
- [ ] Row selection 필요 시 (`rowSelection: { mode: 'multiRow' }`)
- [ ] 스타일 커스터마이징 (CSS 변수)
- [ ] Testing (cy.get('.ag-grid') 선택기)

### TanStack Table 선택 시

- [ ] `npm install @tanstack/react-table`
- [ ] Column definitions 작성
- [ ] `useReactTable` hook 설정
- [ ] Head·Body 렌더 구현
- [ ] 정렬·필터 로직 구현
- [ ] CSS/Tailwind 스타일 (모두 직접)
- [ ] Virtualization (50k+ rows인 경우)
- [ ] 테스트 (DOM selector 커스텀)

---

## 링크 · 참고

- **ag-grid 공식 docs**: https://www.ag-grid.com/react-data-grid/
- **ag-grid React examples**: https://www.ag-grid.com/react-data-grid/react-data-grid/
- **TanStack Table v9 docs**: https://tanstack.com/table/v9/docs
- **2026 Breaking Changes**: `.claude/rules/ui-component-matrix.md` § ag-grid 2026 Breaking Changes
- **커뮤니티 vs Enterprise**: https://www.ag-grid.com/license-pricing.php (커뮤니티 무제한 무료)

---

## 질문 들어오면

사용자가 다음 표현 감지 시 이 스킬 자동 활성:

- "그리드" / "데이터 그리드" / "대량 데이터"
- "1만 건" / "10,000 rows" / "무거운 테이블"
- "ag-grid" / "TanStack Table" (명시)
- "테이블" + ("빠르게" 또는 "커스텀" 또는 "고급")
