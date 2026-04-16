# Skill 36: Data Visualization

## 목적
데이터를 차트, 그래프, 대시보드로 자동 시각화한다.

## 트리거
- "차트 만들어", "data viz", "시각화", "그래프", "대시보드"
- 데이터 분석 결과 표시 시

## 실행 흐름

### 1. 데이터 소스 감지
```
CSV/Excel:  pandas로 읽기
JSON:       직접 파싱
DB:         SQLAlchemy 쿼리
API:        HTTP 호출 → JSON
```

### 2. 차트 유형 자동 선택
```
시계열 데이터     → Line Chart
카테고리 비교     → Bar Chart
비율/구성         → Pie / Donut
분포              → Histogram
상관관계          → Scatter Plot
지리 데이터       → Map (folium)
다차원            → Heatmap
계층 구조         → Treemap
```

### 3. 출력 형식
```
[정적 이미지]
  matplotlib / seaborn → PNG/SVG

[인터랙티브 HTML]
  plotly → HTML 파일 (브라우저에서 열기)
  
[대시보드]
  streamlit → 웹 대시보드
  
[프레젠테이션용]
  Gamma MCP → 슬라이드에 삽입
```

### 4. 자동 인사이트
```
데이터 분석 후 자동 코멘트:
  "매출이 전월 대비 23% 증가"
  "이탈률이 3월에 급등 (원인: 서버 장애)"
  "상위 5개 제품이 전체 매출의 72% 차지"
```

## 출력
- `docs/YYYY-MM-DD/chart-{name}.html` (인터랙티브)
- `docs/YYYY-MM-DD/chart-{name}.png` (정적)
- `docs/YYYY-MM-DD/data-insights.md` (인사이트)

## MCP 연동
- **excel MCP**: Excel 데이터 읽기
- **Gamma MCP**: 프레젠테이션에 차트 삽입
