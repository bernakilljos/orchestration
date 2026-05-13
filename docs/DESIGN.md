---
version: 1.0
name: orchestration_v1
description: Multi-AI Orchestration Kit 의 한글-중심 인포그래픽 디자인 시스템. 강의·교재·기술 문서용 HTML/CSS+SVG → PNG → docx/pptx 임베드 워크플로우 최적화. 4-색 그라데이션 배경 (cream/lilac/cyan/rose) 위에 deep navy 텍스트, 6단계 layered gradient cards, 1300×900 viewport 강제. 한글 가독성 + 5살 청자 톤이 핵심.
inspired_by: getdesign.md (Google Stitch DESIGN.md 컨셉)
applies_to:
  - .claude/scripts/build-korean-html-diagrams.py
  - .claude/scripts/build-arch-lecture-doc.py
  - 모든 design_pdf / design_ppt 플러그인 빌더

# ─────────────────────────────────────────
# 1. Color Palette & Roles
# ─────────────────────────────────────────
colors:
  # Brand identity
  primary: "#1F3864"            # deep navy — 모든 제목·H1·banner·테이블 헤더
  primary-light: "#3F6FB5"      # medium blue — banner gradient pair, 강조 텍스트
  primary-dark: "#3B1B5C"       # deep purple — title gradient 시작점
  accent-rose: "#C00050"        # rose red — title gradient 끝, 위험·강조
  accent-yellow: "#FFE699"      # banner 안 강조 텍스트 (b 태그)

  # Semantic
  ink: "#1F3864"                # 모든 본문 강 강조 (제목, 카드 타이틀)
  body: "#333333"               # 카드 본문 텍스트
  body-soft: "#444444"          # flow 단계 설명
  muted: "#5C6B84"              # subtitle, caption
  hairline: "#e2e8f0"           # 표 cell border

  # Canvas — 4색 그라데이션 (signature 4-stop)
  canvas-cream: "#FFFAF0"
  canvas-rose: "#FFF8FA"
  canvas-cyan: "#F0F4FF"
  canvas-lilac: "#FAF6FF"
  # CSS: background:linear-gradient(135deg,#FAF6FF 0%,#F0F4FF 35%,#FFF8FA 70%,#FFFAF0 100%);

  # Surfaces
  surface-card: "linear-gradient(135deg,#fff,#f7f9fc)"
  surface-table-row: "linear-gradient(135deg,#fff,#f8fafc)"

  # Gradient cards (5 variants + danger) — 카드 카테고리 색
  gradient-1: ["#FFF8E1", "#FFE699", "#D69E2E"]   # amber  / 경고·핵심
  gradient-2: ["#E0E7FF", "#C7D2FE", "#4F46E5"]   # indigo / 보통·정보
  gradient-3: ["#DCFCE7", "#A7F3D0", "#10B981"]   # emerald / 성공·안전
  gradient-4: ["#FCE7F3", "#FBCFE8", "#DB2777"]   # rose   / 주의·여성적
  gradient-5: ["#DBEAFE", "#93C5FD", "#2563EB"]   # blue   / 신뢰·정보
  danger:     ["#FFE4E1", "#FFCCCC", "#DC2626"]   # red    / 위험·금기

  # Layer system — 6 단계 (l1~l6) — 흐름·단계 표현용
  layer-1-red:    {bg: "#FFF5F5 → #FFEBEB", border: "#E53E3E", icon: "#FC8181 → #E53E3E"}
  layer-2-orange: {bg: "#FFFAF0 → #FFF1D5", border: "#DD6B20", icon: "#F6AD55 → #DD6B20"}
  layer-3-yellow: {bg: "#FEFCBF → #FAF089", border: "#D69E2E", icon: "#ECC94B → #D69E2E"}
  layer-4-green:  {bg: "#F0FFF4 → #C6F6D5", border: "#38A169", icon: "#68D391 → #38A169"}
  layer-5-blue:   {bg: "#EBF8FF → #BEE3F8", border: "#3182CE", icon: "#63B3ED → #3182CE"}
  layer-6-purple: {bg: "#FAF5FF → #E9D8FD", border: "#805AD5", icon: "#B794F4 → #805AD5"}

# ─────────────────────────────────────────
# 2. Typography Rules
# ─────────────────────────────────────────
typography:
  font-stack-kor: "'Malgun Gothic','맑은 고딕','Pretendard',sans-serif"

  title:
    fontSize: 42px
    fontWeight: 900
    letterSpacing: "-0.5px"
    color: "transparent"
    background: "linear-gradient(135deg,#3B1B5C 0%,#1F3864 35%,#3F6FB5 70%,#C00050 100%)"
    backgroundClip: "text"
    marginBottom: 4px
    textAlign: center
    note: "메인 페이지 제목 — 4-color gradient text. 모든 PNG 의 첫 줄."

  subtitle:
    fontSize: 18px
    color: "#5C6B84"
    fontWeight: 500
    textAlign: center
    marginBottom: 14px
    note: "제목 아래 한 줄 설명"

  card-title:
    fontSize: 33px
    fontWeight: 800
    color: "#1F3864"
    marginBottom: 8px

  card-desc:
    fontSize: 21px
    color: "#333"
    lineHeight: 1.55

  flow-title:
    fontSize: 18px
    fontWeight: 800
    color: "#1F3864"
    marginBottom: 2px

  flow-desc:
    fontSize: 13px
    color: "#444"
    lineHeight: 1.35

  banner-title:
    fontSize: 20px
    fontWeight: 800
    color: "#fff"
    opacity: 0.95

  banner-content:
    fontSize: 15px
    color: "#fff"
    opacity: 0.94
    lineHeight: 1.5

  table-header:
    fontSize: 21px
    fontWeight: 700
    color: "#fff"
    padding: "10px 12px"

  table-cell:
    fontSize: 19px
    color: "#1F3864"
    padding: "9px 12px"
    lineHeight: 1.5

  card-num:
    fontSize: 48px
    fontWeight: 900
    opacity: 0.12
    color: "#1F3864"
    position: "absolute top:10 right:14"
    note: "카드 우측 상단 반투명 큰 번호 (워터마크 효과)"

  chip:
    fontSize: 22px
    fontWeight: 600
    padding: "5px 14px"
    borderRadius: 14px
    background: "rgba(31,56,100,0.08)"
    color: "#1F3864"

# ─────────────────────────────────────────
# 3. Component Stylings
# ─────────────────────────────────────────
components:
  card:
    padding: "13px 14px"
    borderRadius: 13px
    boxShadow: "0 5px 14px rgba(0,0,0,0.08)"
    background: "linear-gradient(135deg,#fff,#f7f9fc)"
    border: "2px solid #4472C4"
    note: "기본 카드. gradient-N / danger 클래스로 색상 변형."

  banner:
    marginTop: 10px
    padding: "10px 16px"
    background: "linear-gradient(135deg,#1F3864,#3F6FB5)"
    color: "#fff"
    borderRadius: 12px
    boxShadow: "0 6px 18px rgba(31,56,100,0.25)"
    note: "우리 시스템 매핑·결론용. 페이지 하단 fixed (margin-top:auto)."

  flow-step:
    display: flex
    alignItems: center
    gap: 12px
    padding: "6px 12px"
    borderRadius: 10px
    boxShadow: "0 3px 10px rgba(0,0,0,0.07)"
    marginBottom: 4px
    note: "수직 흐름 step (1~6 레이어). l1~l6 클래스로 색 변형."

  flow-icon-box:
    width: 42px
    height: 42px
    borderRadius: 10px
    note: "이모지 또는 아이콘 컨테이너. 레이어별 gradient bg."

  compare-tbl:
    width: 100%
    borderCollapse: separate
    borderSpacing: 5px
    note: "표 — 한눈에 비교용. 헤더 navy 그라데이션, 셀 흰색."

  chip:
    inline: "padding:5px 14px; border-radius:14px"
    bg: "rgba(31,56,100,0.08)"
    note: "태그·메타데이터 표시"

# ─────────────────────────────────────────
# 4. Layout Principles
# ─────────────────────────────────────────
layout:
  viewport: "1300x900 강제 (ratio 0.692 ≈ docx A4 landscape inside 0.701 일치)"
  body:
    width: 1300px
    height: 900px
    padding: "14px 22px"
    overflow: hidden
    display: flex
    flexDirection: column
    justifyContent: space-between
    note: "콘텐츠 자연 분배 — 흰 여백 0 + 잘림 0 동시 보장"

  grids:
    grid2: "2 columns, gap 20px"
    grid3: "3 columns, gap 18px"
    grid4: "4 columns, gap 14px"
    row5: "5 columns, gap 14px"

  spacing-scale:
    xs: 4px
    sm: 8px
    md: 14px
    lg: 20px
    xl: 24px
    page-padding: "14px 22px"

# ─────────────────────────────────────────
# 5. Depth & Elevation
# ─────────────────────────────────────────
elevation:
  card: "0 5px 14px rgba(0,0,0,0.08)"
  flow-step: "0 3px 10px rgba(0,0,0,0.07)"
  banner: "0 6px 18px rgba(31,56,100,0.25)"
  note: "그림자 일관 — y-offset 3~6px, blur 10~18px, opacity 0.07~0.25"

# ─────────────────────────────────────────
# 6. Do's and Don'ts
# ─────────────────────────────────────────
guardrails:
  do:
    - "viewport 1300×900 정확히 (overflow:hidden) — docx A4 landscape inside 비율 일치"
    - "body flex space-between — 콘텐츠 자연 분배"
    - "title = 4-color gradient text (#3B1B5C → #1F3864 → #3F6FB5 → #C00050)"
    - "banner content 한 줄 이내 (margin-top:auto 로 페이지 끝 fixed)"
    - "card padding ≤ 2% viewport (14px / 22px)"
    - "한글 폰트 우선 (Malgun Gothic / Pretendard)"
    - "5살 청자 톤 — 일상 비유 + 친근 어조"

  dont:
    - "banner content `<br>` 또는 두 줄 → 마지막 줄 잘림"
    - "viewport ≠ docx inside 비율 → 흰 여백 또는 잘림"
    - "card 너무 많은 텍스트 (5줄 초과)"
    - "title 안에 두 줄 줄바꿈 (페이지 fit 못 함)"
    - "영문 폰트 우선 (한글 가독성 ↓)"

# ─────────────────────────────────────────
# 7. Responsive (디지털 산출물 비율표)
# ─────────────────────────────────────────
output-ratios:
  docx-landscape-A4:
    viewport: "1300x900"
    ratio: 0.69
    use: "강의 docx 임베드"
  docx-portrait-A4:
    viewport: "1100x1600"
    ratio: 1.45
  pptx-16-9:
    viewport: "1920x1040"
    ratio: 0.54
  pptx-4-3:
    viewport: "1440x1020"
    ratio: 0.71
  pdf-A4-landscape:
    viewport: "1600x1130"
    ratio: 0.71

# ─────────────────────────────────────────
# 8. Agent Prompt Guide — AI 에이전트용
# ─────────────────────────────────────────
agent-prompts:
  quick-start: |
    "이 DESIGN.md 를 참고해서 1300×900 한글 인포그래픽 PNG 1장 만들어줘.
    title = 4-color gradient text, body flex space-between, banner 한 줄,
    카드는 gradient-2 / l5 같은 정해진 클래스 사용. .claude/scripts/build-korean-html-diagrams.py
    의 page() 함수 패턴 따름."

  diagram-flow: |
    "흐름·단계 시각화 = .flow-step + .l1~l6 6단계 컬러. 수직 정렬 + flow-icon-box 안 이모지."

  table-comparison: |
    "비교표 = .compare-tbl + navy gradient header + 흰 셀 배경. 폰트 19~21px."

  card-grid: |
    "카드 그리드 = .grid2/3/4 + .gradient-1~5/danger. 카드당 5줄 이내."

  banner-conclusion: |
    "페이지 하단 결론 = .banner (navy gradient bg + white text). margin-top:auto.
    content 한 줄만. b 태그로 #FFE699 강조."
