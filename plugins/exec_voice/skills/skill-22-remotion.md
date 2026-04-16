# Skill 22: Remotion (프로그래매틱 동영상 생성)

## 목적
React 코드로 동영상을 프로그래밍 방식으로 생성한다.
데이터 기반 동영상, 자동 자막, 인포그래픽 애니메이션 등.

## 트리거
- "동영상 만들어", "remotion", "프로그래매틱 비디오", "React 동영상"
- "인트로 영상", "데이터 시각화 영상", "자막 영상"

## 설치 (자동)
```bash
npm install -g @remotion/cli
npm create video@latest  # 프로젝트 초기화
```

## 실행 흐름

### 1. 동영상 유형 감지
```
- 데이터 기반: 차트/그래프 애니메이션
- 텍스트 기반: 자막, 타이포그래피 모션
- 슬라이드쇼: 이미지 전환 + 텍스트
- 인포그래픽: 숫자/통계 애니메이션
- 인트로/아웃트로: 로고 모션
- 소셜 미디어: Instagram/YouTube Shorts 포맷
```

### 2. 프로젝트 구조 생성
```
src/
├── Root.tsx              # 메인 컴포지션
├── compositions/
│   ├── Intro.tsx         # 인트로 시퀀스
│   ├── MainContent.tsx   # 본 콘텐츠
│   └── Outro.tsx         # 아웃트로
├── components/
│   ├── AnimatedText.tsx  # 텍스트 애니메이션
│   ├── Chart.tsx         # 차트 컴포넌트
│   └── Transition.tsx    # 전환 효과
└── data/
    └── content.json      # 동영상 데이터
```

### 3. 코드 생성 규칙
```
- React + TypeScript
- Remotion의 useCurrentFrame(), useVideoConfig() 활용
- spring() 함수로 자연스러운 애니메이션
- interpolate() 함수로 값 매핑
- brand-guidelines.md의 색상/폰트 자동 반영
- 30fps 기본, 1080p (1920x1080)
```

### 4. 렌더링
```bash
# 미리보기
npx remotion preview

# MP4 렌더링
npx remotion render src/index.ts MainVideo out/video.mp4

# GIF 렌더링 (SNS용)
npx remotion render src/index.ts MainVideo out/video.gif --image-format png
```

### 5. 포맷별 프리셋
```
YouTube:     1920x1080, 30fps, 60-600초
Shorts/Reel: 1080x1920, 30fps, 15-60초
Twitter:     1280x720, 30fps, 15-140초
LinkedIn:    1920x1080, 30fps, 30-300초
```

## 출력
- `src/` — Remotion 프로젝트 소스
- `out/video.mp4` — 렌더링된 동영상
- `docs/YYYY-MM-DD/remotion-{name}.md` — 설계 문서

## MCP 연동
- **Figma MCP**: 디자인 에셋 가져와서 영상에 반영
- **Canva MCP**: 배경/소스 이미지 생성
- brand-guidelines.md → 색상/폰트 자동 적용
