# Skill 20: Claude SEO

## 목적
웹 페이지/프로젝트의 SEO를 분석하고 최적화한다.
메타 태그, 구조화 데이터, 성능, 접근성을 종합 점검.

## 트리거
- "SEO 분석", "SEO 최적화", "claude seo", "검색 엔진 최적화"
- 웹 프로젝트 배포 전 자동 제안

## 실행 흐름

### 1. SEO 감사 (Audit)
```
[메타 태그 체크]
  - title (50-60자)
  - meta description (150-160자)
  - canonical URL
  - og:title, og:description, og:image
  - twitter:card
  - viewport

[구조화 데이터]
  - JSON-LD (Schema.org)
  - breadcrumb
  - FAQ, HowTo, Article 스키마

[기술 SEO]
  - robots.txt
  - sitemap.xml
  - 페이지 로딩 속도 (Core Web Vitals 예측)
  - 모바일 반응형
  - HTTPS 여부
  - URL 구조 (슬래시, 하이픈)

[콘텐츠 SEO]
  - H1~H6 계층 구조
  - 이미지 alt 태그
  - 내부/외부 링크
  - 키워드 밀도
  - 중복 콘텐츠
```

### 2. 점수 리포트
```
SEO Score: 78/100

[PASS] ✅ title 태그 적절 (52자)
[PASS] ✅ H1 태그 1개
[FAIL] ❌ meta description 없음
[FAIL] ❌ og:image 미설정
[WARN] ⚠️ 이미지 3개 alt 태그 없음
[WARN] ⚠️ sitemap.xml 미생성
```

### 3. 자동 수정
```
- meta 태그 자동 생성/삽입
- og 태그 자동 추가
- sitemap.xml 생성
- robots.txt 생성/업데이트
- JSON-LD 구조화 데이터 삽입
- 이미지 alt 태그 AI 자동 생성
```

### 4. 키워드 리서치 (선택)
```
- WebSearch로 경쟁 키워드 분석
- 추천 키워드 목록 생성
- 콘텐츠 최적화 제안
```

## 출력
- `docs/YYYY-MM-DD/seo-audit.md` — 점수 + 상세 리포트
- 코드 수정 (메타 태그, 구조화 데이터 등)
- `public/sitemap.xml`, `public/robots.txt` 생성

## MCP 연동
- **playwright MCP**: 페이지 렌더링 + Lighthouse 호출
- **WebSearch**: 키워드 리서치 (내장 툴, MCP 불필요)
