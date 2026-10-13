---
description: "40년차 공통 디자인 시스템 적용 — 토큰·컴포넌트·패턴 즉시 scaffold"
allowed-tools: Read, Write, Bash
---

사용자가 지정한 패턴 (dashboard / crud-list / landing / login / form-page / settings) 또는 컴포넌트 (Button / Input / Table / DataGrid / Form / Modal / Layout) 를 target 프로젝트에 즉시 scaffold.

## 사용

```bash
/design-apply dashboard        # 전체 대시보드 스캐폴드
/design-apply crud-list        # CRUD 목록 + Modal + Form
/design-apply landing          # 랜딩 페이지
/design-apply tokens           # 디자인 토큰 CSS 복사
/design-apply ag-grid          # DataGrid 템플릿만
/design-apply --list           # 사용 가능 패턴·컴포넌트 전체 리스트
```

## 흐름

1. target 프로젝트 React·Next.js·Vite 감지 (package.json)
2. 필요 npm 패키지 확인 (shadcn·tailwind·ag-grid·react-hook-form·zod·recharts)
3. 없는 패키지 안내 (실제 install 은 사용자 명시 승인)
4. 템플릿 → `src/components/`·`src/patterns/` 복사
5. 토큰 CSS → `src/styles/tokens.css` 복사 + `main.css` import 추가
6. Dark mode 지원 확인 (Tailwind config `darkMode: "class"`)

## 금지

- 사용자 코드 덮어쓰기 X (`.bak` 백업 후만)
- 자체 CSS 추가 X (Tailwind utility 활용)
- 하드코딩 색·폰트·간격 X (토큰 사용)
