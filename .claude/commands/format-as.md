---
description: "지정 형식 변환 — table·json·yaml·markdown·csv·xml·html 중 하나로"
allowed-tools: Read, Write, Edit, Bash(python:*)
---

## Context
- 대상 파일/텍스트: $ARGUMENTS

## Your task

사용자가 준 데이터·텍스트를 **지정 형식**으로 변환한다.

### 입력 받을 수 있는 인자
- `--as <table|json|yaml|markdown|csv|xml|html|sql|mermaid>` — 타겟 형식 (필수)
- `--pretty` — 들여쓰기·정렬 적용
- `--schema <path>` — JSON Schema 로 검증
- `--delimiter <,|;|\t>` — CSV 구분자

### 흐름

1. **원문 파싱** — 비정형 → 구조화 (헤더·행·필드 추출)
2. **형식 변환** — 타겟 syntax 적용
3. **검증** — JSON 은 `python -c "import json; json.loads(open('f').read())"` · CSV 는 pandas · YAML 은 PyYAML
4. **저장** — 사용자 명시 시 `.<format>` 확장자, 아니면 stdout

### 지원 형식 매트릭스

| 형식 | 용도 | 검증 |
|---|---|---|
| table | 가독성·대조 | 열 폭·정렬 |
| json | API 전송·설정 | `json.loads` |
| yaml | 설정·CI/CD | PyYAML load |
| markdown | 문서화 | 렌더 미리보기 |
| csv | 스프레드시트·분석 | pandas read_csv |
| xml | 레거시 통합 | ElementTree |
| html | 웹 표시 | BS4 파싱 |
| sql | DB insert | `CREATE TABLE` + `INSERT` |
| mermaid | 다이어그램 | `mmdc` 렌더 |

### 금지
- 데이터 왜곡·누락 (전부 변환)
- 샘플만 보이고 "...생략" X (전부 포함)
- 임의 열 추가 (원 데이터에 없는 것)
- 숫자 → 문자열 암묵 변환 (타입 보존)

### 자동 schema 추론
JSON·CSV·SQL 는 데이터 보고 타입 추론 (string·int·float·bool·date).

## 참조
- plugins/design_excel/ (대량 데이터 Excel 변환)
- plugins/design_ppt/ (표 → 슬라이드)
- plugins/exec_orch/skills/prompt-techniques.md
