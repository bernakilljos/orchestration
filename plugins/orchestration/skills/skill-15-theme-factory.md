# Skill 15: Theme Factory

## 목적
프로젝트의 테마/디자인 시스템을 자동 생성·관리한다.
브랜드 가이드라인 기반으�� 색상, 타이포그래피, 컴포넌트 스타일을 일관되게 유지.

## 트리거
- 사용자가 "테마 만들어", "디자인 시스템", "theme factory", "ThemeFactory" 언급
- 새 프로젝트 초기 설정 시

## 실행 흐름

### 1. 브랜드 가이드라인 로드
```
1. context/brand-guidelines.md 파일 확인
2. 없으면 → 기본 질문으로 수집:
   - 프로젝트명, 주요 색상(Primary/Secondary/Accent)
   - 폰트 (제목/본문), 라운딩 정도, 그림자 스타일
   - 로고 URL (선택)
3. 수집 후 → context/brand-guidelines.md 자동 생성
```

### 2. 테마 파일 생성
```
프로젝트 스택 감지 후 적절한 형식으로 생성:

Vue/React:
  → src/assets/theme.css (CSS Variables)
  → src/assets/theme.js (JS Object export)

Tailwind:
  → tailwind.config.js의 theme.extend 업데이트

SCSS:
  → src/assets/_variables.scss

일반:
  → context/theme.json (범용 JSON)
```

### 3. 생성되는 항목
```
Colors:
  --color-primary, --color-primary-light, --color-primary-dark
  --color-secondary, --color-accent
  --color-background, --color-surface
  --color-text, --color-text-secondary
  --color-success, --color-warning, --color-error

Typography:
  --font-heading, --font-body, --font-mono
  --font-size-xs ~ --font-size-3xl
  --line-height-tight, --line-height-normal, --line-height-relaxed

Spacing:
  --space-1 ~ --space-12 (4px 단위)

Border:
  --radius-sm, --radius-md, --radius-lg, --radius-full
  --border-width, --border-color

Shadow:
  --shadow-sm, --shadow-md, --shadow-lg

Breakpoints:
  --bp-sm (640px), --bp-md (768px), --bp-lg (1024px), --bp-xl (1280px)
```

### 4. 다크모드 자동 생성
```
- 라이트 테마 기반으로 다크모드 변수 자��� 계산
- prefers-color-scheme 미디어 쿼리 포함
- [data-theme="dark"] 선택자도 생성
```

### 5. 컴포넌트 스타일 가이드
```
docs/YYYY-MM-DD/theme-guide.md 생성:
  - 색상 팔레트 (hex + 사용처)
  - 타이포그래피 스케일
  - 버튼/카드/인풋 스타일 예시
  - Do's and Don'ts
```

## 출력 파일
- `context/brand-guidelines.md` (브랜드 정의)
- `src/assets/theme.css` 또는 `context/theme.json` (테��� 변수)
- `docs/YYYY-MM-DD/theme-guide.md` (스타일 가이드 문서)

## MCP 연동
- **Figma MCP**: 디자인 토큰 읽어와서 테마에 반영
- **Canva MCP**: 브랜드 키트에서 색상/폰�� 추출
- **Gamma MCP**: 브랜드 가이드라인 프레젠테이션 생성

## 사용 예시
```
사용자: "테마 만들어줘. 메인 색상은 #2563EB, 서브 #10B981"
  → brand-guidelines.md 생성
  → theme.css + theme.json 생성
  → theme-guide.md 문서 생성

사용자: "Figma에서 디자인 토큰 가져와서 테마 만들어"
  → Figma MCP로 디자인 토큰 추출
  → 테마 파일 생성
```
