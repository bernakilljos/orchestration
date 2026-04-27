# design_ppt — PPT·디자인·다이어그램 자동화

> **Prefix**: `design_` | **버전**: 1.0 | **Status**: stable | **Phase**: 0
> **Precedence**: 10 | **Token estimate**: ~5500

## 📖 개요

HTML/CSS → Playwright → PPTX 파이프라인으로 고품질 발표자료 자동 생성.
2026-04-27 업데이트: 27→40장 확장 작업 학습으로 잘림 방지·OCR 검증·페이지번호 자동화 강화.

## 📋 커맨드

- `/make-ppt` ⭐ **기본** — HTML→PPTX 풀 파이프라인 (잘림 방지 워크플로우 내장)
- `/ai-system-stages` — AI 시스템 6단계 템플릿
- `/arch-auto` — 아키텍처 다이어그램 자동
- `/arch-mindmap` — 마인드맵
- `/design_ppt` — 디자인 가이드 허브
- `/ppt-install` — 의존성 설치 (Playwright + python-pptx)

## 🧠 스킬

- `skill-ppt-pitfalls` ⭐ **신규** — 13가지 함정 체크리스트 (잘림·정렬·페이지번호·OCR)
- `skill-08-design` ⭐ 핵심 — Canva/DALL-E/Figma 자산 생성
- `skill-14-auto-detail` ⭐ 핵심 — 짧은 요청 → 상세 instruction 자동 확장
- `skill-15-theme-factory` ⭐ 핵심 — 테마·팔레트 자동 생성
- `skill-16-brand-guidelines` — 브랜드 일관성
- `skill-21-marketing` — 마케팅 자료
- `skill-22-remotion` — 동영상 슬라이드
- `skill-arch-mindmap` — 마인드맵 생성

## 🤖 에이전트

- `agent-04-architect` — 슬라이드 구조 설계
- `agent-06-designer` — 디자인 시스템 적용

## 🪝 훅

- `hook-07-layout-lock` — 레이아웃 잠금 (spec)

## 🔗 의존성

- **플러그인**: `exec_orch`
- **외부**: Playwright (`pip install playwright && playwright install chromium`), python-pptx

## 💡 사용 예시

### 예시 1: 주제 기반 생성
```
/make-ppt "Claude Code 설계" 40
```
- HTML 슬라이드 자동 생성 → Playwright 렌더 → PPTX 조립
- 모든 PNG OCR 검증 → 잘림 0건까지 iterate
- 결과: `outputs/ppt/orchestration-v1-FINAL.pptx`

### 예시 2: 새 슬라이드 추가
```bash
# 1. 새 HTML 작성 (알파벳 정렬 위치)
vim outputs/ppt/html-source/slides/slide-04c.html

# 2. 페이지번호 일괄 갱신
python .claude/scripts/update-ppt-page-numbers.py

# 3. 재렌더링
python .claude/scripts/generate-final-ppt.py

# 4. OCR 검증 (Read tool 로 PNG 직접 보기)
```

### 예시 3: 잘림 발견 시
1. `skill-ppt-pitfalls` 의 자가진단 표 참고
2. font-size 또는 padding 단계 축소
3. 그래도 안 되면 분할 (`slide-NN.html` + `slide-NNa.html`)

## 🎯 핵심 노하우 (2026-04-27 업데이트)

### 잘림 방지 패턴
```css
.slide-NN { height: 1080px; overflow: hidden; }
.sNN-body { flex: 1; min-height: 0; overflow: hidden; }    /* 필수 */
.sNN-code { flex: 0 0 auto; }                              /* 필수 */
```

### 파일명 정렬
- `slide-04` < `slide-04a` < `slide-04b` < `slide-05` (알파벳 순)
- 새 슬라이드 끼워넣기 = `slide-NN[a-z].html`
- PNG 출력은 자동 1, 2, 3... 재번호

### OCR 검증
- **사용자가 OCR 보낸 게 진실** — Sub-Agent "PASS" 보고 신뢰 X
- 메인 Claude 가 Read tool 로 PNG 직접 보기

### 디자인 시스템 (5색 팔레트)
| 변수 | 값 | 용도 |
|------|-----|------|
| `--gold` | #B8864E | PART 01 / 강조 |
| `--sage` | #6B8E7F | PART 02 / 성공 |
| `--plum` (#7A4E6B) | inline | PART 03 / 정보 |
| `--terracotta` | #B25A3E | PART 04 / 경고 |
| `--deep-gold` | #8A6235 | PART 05 / 강조2 |

## 📝 참조

- 스펙: `plugin.json`
- 함정 모음: `skills/skill-ppt-pitfalls.md`
- 페이지번호 갱신: `.claude/scripts/update-ppt-page-numbers.py`
- 렌더링: `.claude/scripts/generate-final-ppt.py`
- 디자인 CSS: `outputs/ppt/html-source/styles/design-system.css`
- 공유 규칙: `.claude/rules/`
