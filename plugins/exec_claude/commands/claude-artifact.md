---
description: "인터랙티브 HTML 결과물 생성 — 대시보드·계산기·차트·폼·게임"
allowed-tools: Write, Bash(where:*)
---

## Context
- 인자: `$ARGUMENTS` (형식: `<type> <subject>`)
- 지원 타입: dashboard | calculator | chart | form | game | other
- 출력 디렉토리: `outputs/artifacts/`

## Your task

`skill-claude-artifact` 활성화. 정적 PDF/PPT 가 아닌 **단일 HTML 파일** 로 인터랙티브 결과물 생성.

### 왜 이게 필요한가
- `design_pdf` / `design_ppt` = 인쇄용 정적
- 인터랙티브 = 사용자가 클릭·입력하며 탐색
- 단일 HTML = 백엔드 없이 어디서나 실행 (이메일·Slack 첨부 가능)

### Step 1 — 타입 파싱

`$ARGUMENTS` 에서 첫 단어 = type, 나머지 = subject.

| 타입 | 예시 | 권장 라이브러리 |
|------|------|-----------------|
| dashboard | "주간 매출 대시보드" | Chart.js + 카드 레이아웃 |
| calculator | "모기지 계산기" | 순수 JS + 입력 필드 |
| chart | "방문자 통계" | Chart.js / Plotly |
| form | "고객 설문" | 순수 HTML + localStorage |
| game | "타이핑 연습" | Canvas / DOM 이벤트 |
| other | (자유) | 가장 적합한 것 추론 |

### Step 2 — 단일 HTML 생성 규칙

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>{subject}</title>
  <!-- 외부 의존: CDN 만 (백엔드 없음) -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>/* 인라인 스타일 */</style>
</head>
<body>
  <!-- 인터랙티브 UI -->
  <script>
    // 모든 로직 인라인
  </script>
</body>
</html>
```

### 디자인 규칙 (artifact 통일)
- 단일 파일 (외부 .css/.js 금지, CDN 만 OK)
- 모바일 반응형 (vh/vw 또는 flex/grid)
- 다크/라이트 자동 감지 (`@media (prefers-color-scheme)`)
- 첫 렌더 100KB 이하
- 콘솔 에러 0

### Step 3 — 저장 + 검증

```
저장: outputs/artifacts/<type>-<slug>-<YYYY-MM-DD>.html

검증 체크리스트:
- [ ] 단일 파일 (외부 의존 CDN 만)
- [ ] 모바일 반응형
- [ ] 다크/라이트 자동
- [ ] 100KB 이하
- [ ] 핵심 인터랙션 동작 설명 포함 (주석)
```

### Step 4 — 결과 보고

```
 인터랙티브 아티팩트 생성
- 파일: outputs/artifacts/<file>.html
- 타입: <type>
- 크기: <bytes>
- 열기: 브라우저로 더블클릭

핵심 기능:
- <feature1>
- <feature2>

수정하려면: 해당 .html 파일 직접 편집 (단일 파일)
```

## 안티패턴
-  외부 .css·.js 파일 분리 (단일 파일 원칙)
-  백엔드 호출 (서버 필요해짐)
-  1MB 이상 (느림)
-  로컬스토리지 외 영속 저장 (정적 파일 한계)
