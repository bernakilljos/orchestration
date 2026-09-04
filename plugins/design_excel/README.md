# design_excel — Excel·스프레드시트 자동화 — 데이터 분석·차트·리포트 생성

> **Prefix**: `design_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0
> **Precedence**: 10 | **Token estimate**: ~1100

## 📖 개요

Excel·스프레드시트 자동 생성 — openpyxl + 차트 + Google Sheets.

## 📋 커맨드

- `/design_excel`
- `/excel-make`  기본
- `/excel-status`

## 🧠 스킬

- `skill-36-data-viz`  핵심

## 🤖 에이전트

- `agent-02-implementer`
- `agent-06-designer`

## 🪝 훅

- `hook-02-post-impl` (spec)
- `hook-06-notify` (spec)

## 🔗 의존성

- **플러그인**: `exec_orch`

## 💡 사용 예시

### 예시 1: Excel 생성
```bash
/excel-make "월간 매출" data.csv
```

### 예시 2: 상태 확인
```bash
/excel-status
```

## 📝 참조

- 스펙: `plugin.json`
- 공유 규칙: `.claude/rules/`
- 아키텍처: `docs/architecture-patterns.md`
