# Skill 18: Web Artifacts

## 목적
HTML/CSS/JS 코드를 즉시 실행 가능한 웹 아티팩트로 생성한다.
미리보기 가능한 단일 HTML 파일 또는 컴포넌트 데모를 만든다.

## 트리거
- "미리보기 만들어", "web artifact", "HTML 데모", "컴포넌트 시연"
- UI 컴포넌트 구현 후 확인 필요할 때

## 실행 흐름

### 1. 아티팩트 유형 감지
```
- 단일 컴포넌트 데모 → standalone HTML
- 전체 페이지 프리뷰 → full page HTML
- 인터랙티브 위젯 → HTML + JS
- 데이터 시각화 → Chart.js / D3 내장
- 애니메이션 → CSS animation + JS
```

### 2. 생성 규칙
```
- 단일 HTML 파일 (외부 의존성 CDN으로 로드)
- Tailwind CSS CDN 기본 포함
- 반응형 (모바일/데스크탑)
- 다크모드 지원
- 브랜드 가이드라인 있으면 자동 반영 (context/brand-guidelines.md)
```

### 3. 출력 구조
```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{artifact name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>/* 커스텀 스타일 */</style>
</head>
<body>
  <!-- 아티팩트 콘텐츠 -->
  <script>/* 인터랙션 */</script>
</body>
</html>
```

### 4. 미리보기
```
- playwright MCP로 자동 스크린샷
- 또는 로컬 브라우저에서 직접 열기
- docs/YYYY-MM-DD/artifact-{name}.html 저장
```

## 출력 파일
- `docs/YYYY-MM-DD/artifact-{name}.html` — 실행 가능한 HTML
- `docs/YYYY-MM-DD/artifact-{name}.png` — 스크린샷 (playwright)

## MCP 연동
- **playwright MCP**: 렌더링 + 스크린샷
- **Figma MCP**: 디자인 → HTML 변환 시 참조
