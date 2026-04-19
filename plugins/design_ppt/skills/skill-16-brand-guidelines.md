# Skill 16: Brand Guidelines

## 목적
프로젝트의 브랜드 가이드라인을 정의·관리·적용한다.
모든 디자인/코드/문서에서 일관된 브랜드 아이덴티티를 유지.

## 트리거
- "brand guidelines", "브랜드 가이드", "brand-guidelines" 언급
- "로고", "색상 규칙", "브랜딩", "CI/BI" 언급
- 디자인 관련 작업 시작 전 자동 참조

## 가이드라인 파일
`context/brand-guidelines.md` — 단일 소스 오브 트루스

## 실행 흐름

### 1. 가이드라인 생성 (없을 때)
```
사용자에게 순서대로 수집:

[필수]
1. 프로젝트/브랜드명
2. 주요 색상 (Primary: hex)
3. 보조 색상 (Secondary: hex)
4. 강조 색상 (Accent: hex)

[선택 — 안 주면 자동 결정]
5. 폰트 (제목/본문)
6. 로고 (URL 또는 파일 경로)
7. 톤앤매너 (전문적/친근한/활기찬/미니멀)
8. 타겟 사용자 (B2B/B2C, 연령대)

→ context/brand-guidelines.md 생성
```

### 2. 가이드라인 파일 구조
```markdown
# Brand Guidelines — {프로젝트명}

## Identity
- **Name**: 프로젝트명
- **Tagline**: 한 줄 설명
- **Tone**: professional / friendly / energetic / minimal

## Colors
| Role | Hex | RGB | Usage |
|------|-----|-----|-------|
| Primary | #2563EB | 37,99,235 | 주요 버튼, 헤더, 링크 |
| Primary Light | #60A5FA | | 호버, 배경 |
| Primary Dark | #1D4ED8 | | 액티브, 강조 |
| Secondary | #10B981 | | 성공, 보조 액션 |
| Accent | #F59E0B | | 알림, 배지 |
| Background | #FFFFFF | | 기본 배경 |
| Surface | #F8FAFC | | 카드, 패널 |
| Text | #1E293B | | 본문 텍스트 |
| Text Secondary | #64748B | | 부가 텍스트 |
| Error | #EF4444 | | 에러 상태 |
| Warning | #F59E0B | | 경고 상태 |
| Success | #10B981 | | 성공 상태 |

## Typography
| Role | Font | Weight | Size |
|------|------|--------|------|
| Heading | Pretendard | 700 | 24-32px |
| Body | Pretendard | 400 | 14-16px |
| Caption | Pretendard | 300 | 12px |
| Code | JetBrains Mono | 400 | 13px |

## Logo
- Primary: [경로 또는 URL]
- Minimum size: 24px height
- Clear space: logo height의 50%
- 금지: 비율 변경, 색상 임의 변경, 배경과 대비 부족

## Spacing
- Base unit: 4px
- Padding: 8px (sm), 16px (md), 24px (lg)
- Gap: 8px (items), 16px (sections), 32px (pages)

## Border & Shadow
- Radius: 4px (button), 8px (card), 16px (modal)
- Shadow: 0 1px 3px rgba(0,0,0,0.1)
- Border: 1px solid #E2E8F0

## Do & Don't
- DO: 지정된 색상만 사용
- DO: 최소 4.5:1 대비율 유지
- DON'T: 브랜드 색상 위에 저대비 텍스트
- DON'T: 3종 이상 폰트 혼용
```

### 3. 가이드라인 적용 (다른 skill과 연동)
```
[Skill-15 Theme Factory]
  → brand-guidelines.md 읽어서 theme.css/theme.json 자동 생성

[Skill-08 Design]
  → 디자인 작업 전 가이드라인 참조

[Agent-06 Designer]
  → Figma/Canva 작업 시 브랜드 색상/폰트 적용

[Gamma MCP]
  → 프레젠테이션 생성 시 브랜드 테마 반영

[코드 리뷰 시]
  → 하드코딩된 색상이 가이드라인과 일치하는지 체크
```

### 4. 가이드라인 업데이트
```
사용자: "Primary 색상 #3B82F6으로 변경해줘"
  → context/brand-guidelines.md 업데이트
  → theme.css/theme.json 자동 재생성
  → 변경 영향 범위 리포트
```

### 5. 외부 소스에서 가져오기
```
Figma: get_design_context → 디자인 토큰 추출 → 가이드라인 생성
Canva: list-brand-kits → 브랜드 키트 가져오기 → 가이드라인 생성
URL:   WebFetch (내장 툴, MCP 불필요) → 기존 사이트 색상/폰트 분석 → 가이드라인 생성
```

## 출력
- `context/brand-guidelines.md` — 브랜드 정의 (단일 소스)
- 연동: theme.css, theme.json, Figma, Canva, Gamma

## 자동 참조 조건
다음 작업 시 brand-guidelines.md를 자동으로 읽어 적용:
- UI 컴포넌트 구현
- 디자인 에셋 생성 (Figma/Canva)
- 프레젠테이션 생성 (Gamma)
- 스타일 관련 코드 리뷰
