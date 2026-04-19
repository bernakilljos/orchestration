# design_excel — Excel·스프레드시트 자동화 — 데이터 분석·차트·리포트 생성

> **Prefix**: `design_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0

## 📖 개요

Excel·스프레드시트 자동 생성 — openpyxl + 차트 + Google Sheets.

- **Why**: 데이터 입력 → 차트·피벗 자동.
- **When**: 리포트 생성, 데이터 시각화, 예산 시트.

## 📋 커맨드

- `/design_excel`
- `/make`
- `/status`

## 🧠 스킬

- `skill-36-data-viz` ⭐ 핵심

## 🤖 에이전트

- `agent-02-implementer`
- `agent-06-designer`

## 🪝 훅

- `hook-02-post-impl`
- `hook-06-notify`

## 🔗 의존성

- **플러그인**: `exec_orch`
- **MCP**: 해당 없음
- **환경변수**: 해당 없음

## 💡 사용 예시

### 예시 1: 기본 생성
```
/excel-make "월간 매출" data.csv
```

### 예시 2: 상태 확인
```
/excel-status
```

## 📝 변경 이력

- 1.0 (2026-04-19) — 현재 버전
