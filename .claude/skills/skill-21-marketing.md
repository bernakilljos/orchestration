# Skill 21: Marketing Skill

## 목적
마케팅 콘텐츠(카피, SNS 포스트, 이메일, 랜딩페이지)를 자동 생성한다.
브랜드 가이드라인 기반으로 톤앤매너 일관성 유지.

## 트리거
- "마케팅 콘텐츠", "marketing", "카피 작성", "SNS 포스트", "이메일 캠페인"
- "랜딩페이지 만들어", "광고 문구"

## 실행 흐름

### 1. 브랜드 컨텍스트 로드
```
1. context/brand-guidelines.md 읽기 (있으면)
2. 톤앤매너, 타겟 오디언스, 핵심 메시지 파악
3. 없으면 사용자에게 기본 정보 수집
```

### 2. 콘텐츠 유형별 생성

#### SNS 포스트
```
- 플랫폼별 최적화 (Instagram, Twitter/X, LinkedIn, Facebook)
- 해시태그 자동 생성
- 이미지 캡션
- 캐러셀/슬라이드 텍스트
- CTA (Call to Action) 포함
```

#### 이메일 캠페인
```
- 제목 (A/B 테스트용 2-3개)
- 본문 (HTML 템플릿)
- CTA 버튼 텍스트
- 프리헤더 텍스트
- 구독 취소 안내
```

#### 랜딩페이지 카피
```
- Hero 섹션 (헤드라인 + 서브 헤드라인)
- 특징/혜택 (Feature-Benefit)
- 사회적 증거 (리뷰, 숫자)
- FAQ
- CTA
- web-artifacts 스킬로 HTML 미리보기 생성
```

#### 광고 카피
```
- Google Ads (제목 30자 x3 + 설명 90자 x2)
- Facebook/Instagram Ads (프라이머리 텍스트 + 헤드라인)
- 네이버 검색광고 (제목 15자 + 설명 45자)
```

### 3. A/B 테스트 변형
```
각 콘텐츠에 대해 2-3개 변형 자동 생성:
  - 변형 A: 이성적 어필 (데이터, 숫자)
  - 변형 B: 감성적 어필 (스토리, 공감)
  - 변형 C: 긴급성 어필 (한정, 마감)
```

### 4. SEO 연동
```
- skill-20 (Claude SEO) 호출하여 키워드 최적화
- 메타 디스크립션 자동 생성
- 검색 의도에 맞는 콘텐츠 구조
```

## 출력
- `docs/YYYY-MM-DD/marketing-{type}.md` — 생성된 콘텐츠
- `docs/YYYY-MM-DD/artifact-landing.html` — 랜딩페이지 (web-artifacts 연동)
- Gamma MCP: 마케팅 프레젠테이션 자동 생성

## MCP 연동
- **Gamma MCP**: 마케팅 프레젠테이션
- **Canva MCP**: SNS 이미지/배너 디자인
- **Gmail MCP**: 이메일 캠페인 초안 생성
- **WebSearch**: 경쟁사/키워드 리서치 (내장 툴, MCP 불필요)
