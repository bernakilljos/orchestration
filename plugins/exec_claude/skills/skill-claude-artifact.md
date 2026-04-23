---
name: skill-claude-artifact
description: |
  단일 HTML 파일로 인터랙티브 결과물(대시보드·계산기·차트·폼·게임)을 생성하는 패턴.
  사용자가 "인터랙티브", "대시보드", "HTML 결과물", "아티팩트", "한 파일로", "클릭 가능한" 같은 표현을 쓸 때 활성화.
  정적 PDF/PPT 가 부적합한 (사용자가 탐색·입력해야 하는) 결과물 요청 시 자동 선택.
---

# Skill: Claude Artifact (Interactive HTML)

## 목적
정적 출력(PDF·PPT·이미지)으로 표현 불가능한 **인터랙티브 결과물**을 단일 HTML 로 생성. 백엔드 없음 → 어디서나 더블클릭 실행.

## 트리거
- 한국어: "인터랙티브", "대시보드", "HTML 결과물", "아티팩트", "클릭 가능한", "한 파일로"
- 영어: "artifact", "interactive", "dashboard", "calculator", "single-file html"
- **자동 신호**: 결과물에 입력 필드·차트 호버·클릭 분기·실시간 계산 등이 필요

## 5대 타입

| 타입 | 핵심 라이브러리 | 예시 |
|------|----------------|------|
| dashboard | Chart.js | 매출·트래픽 카드 그리드 |
| calculator | 순수 JS | 모기지·세금·환율 |
| chart | Chart.js / Plotly | 시계열·분포·비교 |
| form | HTML + localStorage | 설문·신청서 |
| game | Canvas / DOM | 타이핑·퀴즈·미니게임 |

## 단일 파일 원칙

```html
<!DOCTYPE html>
<html><head>
  <meta charset="UTF-8">
  <title>...</title>
  <!-- CDN 만 OK, 로컬 .css/.js 금지 -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>/* 모두 인라인 */</style>
</head><body>
  <!-- UI -->
  <script>/* 모두 인라인 */</script>
</body></html>
```

## 디자인 규칙
- **단일 파일** (CDN 외부 의존만 허용)
- **모바일 반응형** (flex/grid + vh/vw)
- **다크/라이트 자동** (`@media (prefers-color-scheme: dark)`)
- **100KB 이하** (첫 페인트)
- **콘솔 에러 0**
- **한국어 UI** (사용자 요청이 한국어면)

## 색상 팔레트 (기본)
```
Primary:   #6366F1 (인디고)
Accent:    #EC4899 (핑크)
Success:   #10B981 (그린)
Warning:   #F59E0B (앰버)
Danger:    #EF4444 (레드)
배경(라이트): #FFFFFF
배경(다크):  #0F172A
글자(라이트): #1E293B
글자(다크):  #F1F5F9
```

## 안티패턴
- ❌ 외부 .css/.js 파일 분리
- ❌ 백엔드 호출 (서버 의존)
- ❌ 1MB 이상
- ❌ 영문 UI (한국어 요청에 영어 응답)
- ❌ 다크모드 무시
