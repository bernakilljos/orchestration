---
name: ppt-pitfalls-checklist
description: |
  PPT 생성 시 자주 마주치는 함정 13가지 체크리스트. 잘림(overflow)·파일명 정렬·페이지번호·OCR 검증·이미지 채움 관련 실수 방지.
  사용자가 "PPT 만들어줘", "슬라이드 생성", "발표자료", "/design_ppt", "/make-ppt", "PPT 분할", "페이지 추가", "잘림", "여백" 등을 언급할 때 자동 활성화.
  HTML→Playwright→PPTX 파이프라인 작업 (outputs/ppt/html-source/slides/) 시작 시 항상 적용.
---

# PPT Pitfalls — 13 가지 함정과 회피법

> **출처**: 2026-04-27 Claude Code 27→40장 확장 작업의 실제 함정.
> **목적**: 같은 실수를 반복하지 않도록 체크리스트화.

---

## 1. 잘림 (Overflow) — 가장 큰 카테고리

### 함정 1. `display: flex` 하위에 `min-height: 0` 누락
**증상**: 그리드/플렉스 자식이 부모 영역을 넘어가도 잘림 안 일어나고 쥐어 짜짐.
**원인**: flex 자식의 기본 `min-height: auto` 가 콘텐츠 크기 강제.
**해결**:
```css
.slide-NN { display: flex; flex-direction: column; height: 1080px; overflow: hidden; }
.sNN-body { flex: 1; min-height: 0; overflow: hidden; }   /* ← 필수 */
.sNN-left { display: flex; flex-direction: column; min-height: 0; }   /* ← 필수 */
```

### 함정 2. 코드 박스 `flex: 1` 사용
**증상**: 코드 박스 마지막 줄들이 잘림. 코드 영역이 부모 영역 부족분만큼만 표시.
**원인**: `flex: 1` 은 영역을 늘리려 하지만 부모가 작으면 콘텐츠 잘라먹음.
**해결**:
```css
.sNN-code {
  flex: 0 0 auto;          /* ← 자연 크기 사용 */
  white-space: pre;
  overflow: hidden;
}
```

### 함정 3. 코드 줄 수 + 폰트 라인 높이 = 박스 초과
**증상**: 16줄 코드 + font-size 20px line-height 1.5 = 480px → 박스 영역 부족.
**해결 단계 (위에서 아래로 시도)**:
1. font-size 18px → 16px → 14px 단계 축소
2. 코드 인라인 합치기 (예: `"hooks": [{ "command": ... }]` 한 줄로)
3. 비필수 줄 삭제
4. 그래도 안 되면 **분할** (slide-NN + slide-NNa)

### 함정 4. 사이드 박스 ul 항목 안 보임
**증상**: 박스 헤더 (◆ MCP 특징) 만 보이고 li 항목 4개 안 보임.
**원인**: 좌측 코드 박스가 너무 커서 우측 박스 위로 침범 또는 박스 자체가 영역 밖.
**해결**:
- grid 비율 조정 (`1.7fr 1fr` → `1.1fr 1fr`)
- 코드 박스 폰트·padding 축소
- ul 항목 폰트·padding 축소

---

## 2. 파일명 / 정렬 함정

### 함정 5. 새 슬라이드 어디에 끼울지 모름
**규칙**: `glob('slide-*.html')` + `sorted()` = 알파벳 순.
**검증**:
```text
"slide-04.html" < "slide-04b.html" < "slide-04c.html" < "slide-05.html"   ✓
```

**활용**:
- slide-04 다음에 = `slide-04a.html`
- slide-04a 다음에 = `slide-04b.html`
- slide-12b (이미 존재) 다음에 = `slide-12c.html`

### 함정 6. PNG 출력 번호와 HTML 파일명 다름
**현상**: `slide-04b.html` 이 렌더되면 PNG 는 `slide-05.png` 로 출력.
**이유**: `generate-final-ppt.py` 가 정렬 후 1, 2, 3... 재번호.
**주의**: 페이지번호 갱신할 때 **HTML 파일명 ≠ 페이지번호** 인지 인식하고 처리.

---

## 3. 페이지번호 함정

### 함정 7. 새 슬라이드 추가 후 NN/총수 그대로
**증상**: 일부 "5/27" + 일부 "13/40" 혼재.
**해결**:
```bash
python .claude/scripts/update-ppt-page-numbers.py
```
모든 HTML 의 `<span class="mono caption">XX / YY</span>` 일괄 갱신.

### 함정 8. Cover / Learn More 페이지번호 표기 다름
**Cover**: `<div class="value">27</div>` (SLIDES 메트릭) — NN/총수 형식 X.
**Learn More**: `<span>Opus 4.8 Baseline · 27 slides</span>` — 별도 표기.
**해결**: update-ppt-page-numbers.py 에 두 패턴도 처리 룰 추가.

---

## 4. 검증 함정

### 함정 9. Sub-Agent "전체 OK" 거짓 보고
**현상**: Task 로 위임한 검증 에이전트가 "27/27 PASS" 라고 보고.
**실제**: 사용자 OCR 결과 4장 잘림.
**해결**: **메인 Claude 가 직접 OCR** — Read tool 로 PNG 직접 보기. 위임하지 마라.

### 함정 10. 미세 잘림은 "거의 OK" 가 아니라 잘림
**예시**: 코드 마지막 `}` 닫힘 살짝 잘림.
**판단**: 1px 라도 잘림이면 잘림. 수정 대상.
**예외**: 디자인 의도 (예: SVG 가장자리 페이드) 는 잘림 아님.

---

## 5. 이미지 / 자산 함정

### 함정 11. DALL-E API 직접 호출 시도
**증상**: API 키 없어서 실패.
**대안 (이 프로젝트에서 검증됨)**:
- **Iconify** (heroicons + simple-icons + lucide) — 200K SVG 무료
- **SVG 자체 작성** — 정밀 컨트롤 (예: 동심원·연결도)
- **CSS 그라디언트** — radial-gradient 2~3개 + linear-gradient 조합으로 분위기
- **점 그리드 패턴** — 데코레이션
- **Unsplash** — `https://source.unsplash.com/1920x1080/?<keyword>` (네트워크 필요)

### 함정 12. Mermaid 특수문자 처리 실패
**증상**: `/init` 같은 슬래시·따옴표·`?` 가 포함된 라벨 → 💣 폭탄 아이콘 표시.
**해결**: 단순 영숫자만 사용. 슬래시·코드 표기는 라벨 밖에서 (HTML 으로).

---

## 6. 권한 / 환경 함정

### 함정 13. PowerPoint 가 PPTX 잠금
**증상**: 재렌더 시 `PermissionError: [Errno 13] file in use`.
**해결**: 사용자에게 "PowerPoint에서 PPT 파일 닫아주세요" 요청 후 재시도.
**예방**: 작업 시작 전 PowerPoint 종료 안내.

---

## 7. 빠른 자가진단 표

| 증상 | 가장 가능성 높은 원인 | 즉시 확인할 것 |
|------|----------------------|----------------|
| 코드 마지막 줄 잘림 | font-size · 줄 수 초과 | font-size 줄이거나 분할 |
| 카드 하단 빈 공간 큼 | 콘텐츠 부족 | out 라벨·시간·아이콘 추가 |
| 박스 헤더만 보임 | 좌측 코드 침범 | grid 비율 + 박스 폰트 축소 |
| SVG 위치 어긋남 | viewBox·max-width 문제 | max-width 줄이고 flex-shrink:0 |
| 페이지 번호 불일치 | 일괄 갱신 누락 | update-ppt-page-numbers.py |
| Sub-Agent "OK" 후 잘림 | 위임 검증 신뢰 | 메인 Claude 가 직접 OCR |
| PermissionError | PowerPoint 잠금 | 파일 닫기 |
| Mermaid 폭탄 아이콘 | 특수문자 라벨 | 단순 라벨로 변경 |
| `?.` 파서 에러 | optional chaining | 사용 금지 (CLAUDE.md) |

---

## 8. 워크플로우 체크리스트 (저장용)

```markdown
## PPT 작업 시작 전
- [ ] PowerPoint 종료 확인
- [ ] outputs/ppt/html-source/styles/design-system.css 존재 확인
- [ ] generate-final-ppt.py 동작 확인

## HTML 작성 중
- [ ] .slide-NN { height: 1080px; overflow: hidden } 적용
- [ ] flex/grid 자식에 min-height: 0
- [ ] 코드 박스는 flex: 0 0 auto
- [ ] 코드 12줄 이하 또는 font-size 14~16px

## 새 슬라이드 추가 시
- [ ] 파일명 알파벳 정렬 위치 검토 (slide-NN[a-z].html)
- [ ] eyebrow PART · TITLE 라벨 일관
- [ ] 페이지번호 NN/총수 새 번호로

## 렌더링 후
- [ ] 27장(또는 40장) 모두 Read tool 로 OCR
- [ ] 코드 박스 마지막 줄 닫힘 } 확인
- [ ] PART Divider 색 분배 일관
- [ ] 페이지번호 1/N ~ N/N 정합
- [ ] Cover 의 SLIDES 메트릭 정확
- [ ] Learn More "N slides" 표기 정확

## 커밋 전
- [ ] 잘림 0건 확인
- [ ] PowerPoint 에서 직접 열어 확인
- [ ] git status — 빠진 파일 없는지
```

---

## 9. 출처 / 추가 참조

- 본 작업 commit: `cd61abb` (40 슬라이드 확장)
- 이전 commit: `9d7f968` (27장 검증 fix), `1431783` (27장 페이지번호 통일)
- 디자인 원칙: `.claude/rules/best-practices.md`
- 플러그인 구조: `plugins/design_ppt/`
- 렌더링 스크립트: `.claude/scripts/generate-final-ppt.py`
- 페이지번호 갱신: `.claude/scripts/update-ppt-page-numbers.py` (신규)

---

## 10. 우측 여백 함정 (2026-04-29 발견) ⚠️

**증상**: 본문 슬라이드 (`class="body"` 사용) 가 우측 720px 빈 여백.
Cover/TOC/Closing 은 정상.

**원인**: `design-system.css` 에 `.body, .body-lead { max-width: 1200px }` 규칙 존재.
`.body` (그리드 컨테이너) 가 1200px 로 잘리면 1920-1200=720px 여백.

**Fix**: `.body` 만 빼고 `.body-lead` 만 max-width 유지
```css
.body-lead { max-width: 1200px; }   /* 소제목 가독성 OK */
/* .body 는 max-width 제거 — 1920px 풀 사용 */
```

**검증** (PIL 픽셀 — OCR Read 보다 빠름):
```python
from PIL import Image
def cream(r,g,b): return 240<r<252 and 235<g<250 and 225<b<245
img = Image.open(png).convert('RGB')
y = img.height // 2
for x in range(img.width-1, 0, -1):
    if not cream(*img.getpixel((x,y))):
        print(f'right margin = {(img.width-x)*1920//img.width}px@1920')
        break
```

**권장 padding**: 본문 슬라이드도 `60px 80px 40px 80px` (Cover/TOC 와 동일).
Edge-to-edge (padding 0) 보다 80px 좌우 여백이 시각적으로 깔끔.

---

## 11. 본문 슬라이드 시각 보강 패턴 (2026-04-29)

본문 슬라이드가 단조로워 보이면 다음 기법으로 Cover/TOC 수준 시각 풍요로움 달성:

### A. 80px 여백 데코레이션 (subtle pattern)
좌·우 80px padding 영역을 `::before`/`::after` 가상 요소 + repeating-linear-gradient 로 채움.
```css
.slide-NN::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 80px;
  background: repeating-linear-gradient(
    180deg,
    transparent 0 8px,
    rgba(184,134,78,0.04) 8px 12px
  );
  pointer-events: none;
}
```
- 핵심: opacity **0.03-0.05** (콘텐츠 가리지 X)
- 슬라이드 PART 색상 활용 (gold/sage/plum/terracotta/deep-gold)

### B. 카드 코너 그라디언트
박스 우상단에 미세한 radial-gradient 로 입체감.
```css
.box::after {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 40px; height: 40px;
  background: radial-gradient(circle at top right, rgba(184,134,78,0.08), transparent 50%);
  pointer-events: none;
}
```

### C. border-left → ::before 전환
z-index 컨트롤이 자유로워짐.
```css
/* BEFORE */
.box.rules { border-left: 5px solid #7A4E6B; }

/* AFTER — z-index/포지셔닝 자유 */
.box.rules { position: relative; }
.box.rules::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 5px;
  background: #7A4E6B;
  border-radius: 14px 0 0 14px;
}
```

### D. 박스 배경 opacity 미세조정
- 기본 0.78 → **0.82~0.88** 로 올려 contrast 강화
- box-shadow 도 미세하게 (`0 6-10px blur, opacity 0.05~0.10`)

### E. 명령어 chip 스타일
font-weight 600, padding 8px 7px, code bg opacity 0.08 → 0.10.

### 결과 (sub-agent 1회 작업)
14개 본문 슬라이드 보강 완료, 41장 전체 렌더 성공, 잘림/오버플로 없음.

### 적용 시 주의
- decoration 은 `pointer-events: none` 필수 (클릭 방해 X)
- z-index 컨트롤 — 데코가 콘텐츠 위로 가지 않도록
- 모든 데코는 opacity 0.10 이하 권장

---

## 12. Design System v2 — Round 11~50 학습 (2026-04-30)

automation/plugins/team 3 PPT (43장) 에 50 라운드 polish 적용 후 도출된 표준 패턴. 새 PPT 만들 때 design-system.css 시드로 사용.

### A. SVG 여백 장식 (33/41 본문 슬라이드 적용)
좌·우 40px 가상 컬럼 stripe — 80px 여백보다 한 단계 압축.
```css
.slide-NN::before {  /* 좌측 */
  content: ''; position: absolute; left: 20px; top: 60px; bottom: 50px;
  width: 40px; border-radius: 20px;
  background: repeating-linear-gradient(0deg,
    rgba(184,134,78,0.05) 0 2px, transparent 2px 6px);
  pointer-events: none; z-index: 0;
}
.slide-NN::after {   /* 우측 */
  content: ''; position: absolute; right: 20px; top: 60px; bottom: 50px;
  width: 40px; border-radius: 20px;
  background: repeating-linear-gradient(180deg,
    rgba(107,142,127,0.05) 0 2px, transparent 2px 6px);
  pointer-events: none; z-index: 0;
}
```
**PART 별 색상 매핑**: gold (exec) · sage (design/team) · plum (mcp) · terracotta (ai)

### B. 카드 다층 box-shadow (R17~R20)
플랫 → 입체. 다층으로 깊이감.
```css
.card { box-shadow:
  0 1px 2px rgba(26,29,36,0.04),
  0 4px 12px rgba(184,134,78,0.06),
  0 12px 32px rgba(26,29,36,0.04);
}
.bullet-box, .mermaid-wrapper, .compare-col { /* 동일 패턴 */ }
```

### C. 카드 코너 그라디언트 (R15~R16)
우상단 + 좌하단 subtle radial-gradient → 매트릭스같은 입체감.
```css
.card::before { /* top-right 200px */
  content: ''; position: absolute; top: 0; right: 0;
  width: 200px; height: 200px;
  background: radial-gradient(circle at top right,
    rgba(184,134,78,0.06), transparent 60%);
  pointer-events: none;
}
.card::after { /* bottom-left sage */
  content: ''; position: absolute; bottom: 0; left: 0;
  width: 160px; height: 160px;
  background: radial-gradient(circle at bottom left,
    rgba(107,142,127,0.05), transparent 55%);
  pointer-events: none;
}
```

### D. 코드박스 신택스 컬러 (R21~R24)
한글 주석 옅게 (`#6E685C` 50% opacity) + 키워드 진하게.
```css
.code-block .keyword { color: #B8864E; font-weight: 700; }
.code-block .string  { color: #6B8E7F; }
.code-block .number  { color: #B25A3E; }
.code-block .comment { color: #6E685C; opacity: 0.7; font-style: italic; }
.code-block .line-number { color: #C9C5BC; user-select: none;
  display: inline-block; width: 28px; text-align: right; padding-right: 12px; }
.code-block { border: 1px solid rgba(107,142,127,0.18);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.6); /* sage glow */ }
```

### E. 페이지번호 통일 (R25)
모든 슬라이드 동일 스펙.
```css
.mono.caption /* 페이지번호 */ {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px; font-weight: 600;
  letter-spacing: 0.06em; color: var(--stone);
}
```

### F. 아이콘 일관성 (R26~R28)
- eyebrow 인라인: **18px**
- 카드 큰 아이콘: **44px**
- hover (PPT 정적이라 prefers-reduced-motion 고려):
```css
iconify-icon { transition: opacity 0.2s, transform 0.2s; }
iconify-icon:hover { opacity: 0.85; transform: scale(1.04); }
```

### G. 자간·행간 (R31~R32)
한글 가독성 핵심.
```css
.body-lead { line-height: 1.52; letter-spacing: -0.008em; }
body, .body { line-height: 1.58; letter-spacing: -0.006em; }
```

### H. 데코 opacity 표준값 (R33~R36)
| 요소 | opacity | blend |
|:-|:-|:-|
| fill-decor | 0.06 | normal |
| decor-circle | 0.32 + blur(8px) | normal |
| decor-grid | 0.25, rotate(15deg) | normal |
| decor-dots | 0.20 | multiply |

### I. 구분선·배지·하이라이트 (R37~R40)
```css
/* divider 3등급 */
.divider-strong { height: 2px; background: var(--ink); opacity: 0.18; }
.divider-medium { height: 1px; background: var(--ink); opacity: 0.10; }
.divider-soft   { height: 1px; background: linear-gradient(90deg,
  transparent, rgba(26,29,36,0.08), transparent); }

/* 배지 3등급 (gold/sage/terracotta) */
.badge-primary { background: var(--gold); color: white; padding: 3px 10px;
  border-radius: 100px; font-size: 11px; font-weight: 700; }
.badge-secondary { background: rgba(107,142,127,0.18); color: #4A6F60; }
.badge-warning { background: rgba(178,90,62,0.16); color: #8A3E26; }

/* 텍스트 강조 (4 accent) */
.accent-gold { color: var(--gold); font-weight: 700; }
.accent-sage { color: var(--sage); font-weight: 700; }
.accent-plum { color: #7A4E6B; font-weight: 700; }
.accent-terra { color: var(--terracotta); font-weight: 700; }
```

### J. Cover 미세조정 (R41~R44)
- 측면 stripe opacity: **0.05** (이전 0.06)
- radial overlay: 1100px → **1200px** 확산
- grid overlay: opacity **0.035** (이전 0.04)
- footer: backdrop-filter blur 24px + inset glow

### K. 유틸리티 클래스 (R47~R49)
디자인 시스템 v2 의 마지막 조각.
```css
/* 색상 */
.text-gold, .text-sage, .text-plum, .text-terra, .text-stone, .text-ink
.bg-gold-soft, .bg-sage-soft, .bg-plum-soft (모두 0.10 opacity)
.border-gold, .border-sage, ...

/* 간격 (4·8·12·16·24·32·48·64px) */
.p-1 ~ .p-12, .px-N, .py-N, .m-N, .gap-N

/* flex */
.flex, .flex-col, .items-center, .justify-between, .gap-2 ~ .gap-12
```

### 검증 워크플로우 (필수)
모든 polish 작업 후 다음 순서:
1. **렌더**: `python .claude/scripts/generate-{which}-ppt.py`
2. **PIL**: `python .claude/scripts/verify-ppt-overflow.py --dir outputs/ppt-{which}`
3. **OCR (필요시)**: PNG 직접 Read 로 phantom 필터링
4. **3 파일 sync**: design-system.css 변경시 automation/plugins/team 모두 동일

### 50 라운드 결과 (2026-04-30)
- 43/43 슬라이드 PIL PASS
- 매 라운드 real fix (no-op 0)
- HEAD: e43fddf (push 완료)
- 40 commit 모두 "fix(ppt): Round NN — <요약>" 포맷

### 안티패턴
- 한 라운드에 여러 PPT 동시 수정 후 중간 commit 빠뜨림 → R56061a6 같은 잔존 발생
- design-system.css 한 파일만 수정 → 3 PPT 시각 분기
- PPT 락 (`~$*.pptx`) 무시하고 재렌더 시도 → PermissionError
- 새 슬라이드 파일 생성 (slide-NN_new.html, slide-NN.bak) → orphan
- PNG Read 만으로 fix 결정 → phantom (HTML 코드로 재확인 필수)

---

## 13. 차트·다이어그램·카드 그리드 패턴 (R51 — 2026-04-30)

R50 까지 디자인 시스템 표준화 후, R51 에서 **임팩트 시각화 8장** 보강 작업으로 도출된 재사용 패턴.
"표만 있는 슬라이드"·"단순 텍스트 2 컬럼"·"좁은 SVG" 가 발견되면 적용.

### A. BEFORE / AFTER 막대 차트 (단일 비교 강조)
사용처: 비용 절감 · 성능 향상 · 토큰 절약 등 한 번에 보여줄 때.

```html
<div class="savings">
  <div class="big">−92%</div>
  <div class="chart">
    <div class="barrow before">
      <span class="tag">BEFORE</span>
      <span class="track"><span class="fill"></span></span>
      <span class="price">$108 / 월</span>
    </div>
    <div class="barrow after">
      <span class="tag">AFTER</span>
      <span class="track"><span class="fill"></span></span>
      <span class="price">$9 / 월</span>
    </div>
  </div>
</div>
```
```css
.savings { display: grid; grid-template-columns: auto 1fr;
  background: linear-gradient(135deg, rgba(107,142,127,0.18), rgba(184,134,78,0.12));
  border: 1px solid rgba(107,142,127,0.4); border-radius: 14px;
  padding: 14px 22px; column-gap: 22px; align-items: center; flex: 0 0 auto; }
.savings .big { font-family: 'Fraunces', serif; font-size: 56px;
  font-weight: 700; color: var(--sage); grid-row: span 2; }
.savings .barrow { display: grid; grid-template-columns: 64px 1fr 78px;
  gap: 10px; align-items: center; }
.savings .barrow .track { height: 18px; background: rgba(0,0,0,0.05);
  border-radius: 4px; overflow: hidden; }
.savings .barrow .fill { height: 100%; border-radius: 4px;
  box-shadow: inset 0 -2px 0 rgba(0,0,0,0.08); }
.savings .barrow.before .fill { width: 100%;
  background: linear-gradient(90deg, var(--terracotta), #D4724E); }
.savings .barrow.after .fill { width: 8.3%;       /* ← 비율 직접 계산 */
  background: linear-gradient(90deg, var(--sage), #8FAA9D); }
```

**핵심**:
- AFTER 막대 width 는 BEFORE 대비 비율로 직접 (예: 9/108 = 8.3%)
- `.savings { flex: 0 0 auto }` — 부모 flex 안에서 압축 방지
- 큰 숫자 (-92%) + 막대 + sub 라인 = 3 요소 grid 로 묶음

### B. KPI Sparkline (4 KPI 트렌드 표시)
사용처: 대시보드 슬라이드. 큰 숫자 + 24h 트렌드 미니 라인.

```html
<div class="stat cost">
  <div class="lbl">오늘 비용</div>
  <div class="val">$3.42</div>
  <div class="delta up">↓ 어제 $4.10 (−16%)</div>
  <svg class="spark" viewBox="0 0 200 36" preserveAspectRatio="none">
    <path class="area" d="M0,12 L17,8 L33,15 ... L200,28 L200,36 L0,36 Z"/>
    <path class="line" d="M0,12 L17,8 L33,15 ... L200,28"/>
  </svg>
</div>
```
```css
.stat .spark { width: 100%; height: 36px; margin-top: 6px; opacity: 0.85; }
.stat .spark path.line { fill: none; stroke-width: 2.2; }
.stat .spark path.area { stroke: none; opacity: 0.18; }
.stat.cost .spark path.line { stroke: var(--gold); }
.stat.cost .spark path.area { fill: var(--gold); }
/* task=sage, token=plum, fail=terracotta — KPI 카테고리 색상 매핑 */
```

**핵심**:
- viewBox 200×36 + `preserveAspectRatio="none"` → 카드 폭에 맞춰 가변 stretch
- area path 는 line 의 마지막 점에서 `L200,36 L0,36 Z` 로 닫음 (밑변)
- 13 개 점 (`x: 0, 17, 33, ..., 200`) — 시간축 분포
- y 좌표는 트렌드 의도대로 (상승=감소, 하락=증가, 0=상단)

### C. Timeline 막대 + 그라디언트 + RETRY 라벨
사용처: 단계적 backoff·escalation 시각화.

```html
<div class="timeline">
  <div class="bar t1"><span class="lab">10m</span><span class="step">RETRY 1</span></div>
  <div class="bar t2"><span class="lab">20m</span><span class="step">RETRY 2</span></div>
  <div class="bar t3"><span class="lab">40m</span><span class="step">RETRY 3</span></div>
  <div class="bar t4"><span class="lab">2h</span><span class="step">RETRY 4</span></div>
</div>
```
```css
.timeline { display: flex; gap: 12px; align-items: flex-end;
  height: 150px; padding: 8px 4px 0 4px; position: relative; }
.timeline::before { content: ''; position: absolute;
  left: 0; right: 0; bottom: 0; height: 1px;
  background: rgba(184,134,78,0.25); }   /* baseline */
.bar { flex: 1; border-radius: 6px 6px 0 0;
  display: flex; align-items: flex-start; justify-content: center;
  padding-top: 8px; box-shadow: inset 0 -3px 0 rgba(0,0,0,0.06); }
.bar.t1 { height: 22%; background: linear-gradient(180deg,
  rgba(184,134,78,0.5), rgba(184,134,78,0.7)); }
.bar.t2 { height: 44%; background: linear-gradient(180deg, ..., 0.8); }
.bar.t3 { height: 70%; background: linear-gradient(180deg, ..., 0.9); }
.bar.t4 { height: 100%; background: linear-gradient(180deg,
  var(--gold), var(--deep-gold)); }
.bar .lab { font-size: 17px; font-weight: 700;
  color: rgba(255,255,255,0.95); text-shadow: 0 1px 2px rgba(0,0,0,0.15); }
.bar.t1 .lab { color: var(--deep-gold); text-shadow: none; }  /* 짧은 막대는 흰 배경 */
.bar .step { position: absolute; bottom: -22px; ... font-size: 12px; }
```

**핵심**:
- 짧은 막대는 라벨 색을 deep-gold (흰색이면 안 보임)
- `box-shadow: inset 0 -3px 0` — 막대 베이스에 미세 강조
- `.step` 라벨은 `position: absolute; bottom: -22px` 로 막대 밖으로 빼기

### D. SVG 다이어그램 — 그라디언트 + 화살표 marker + 카테고리 색
사용처: 시스템 구조도 · 의존성 그래프 · 흐름도.

```html
<svg viewBox="0 0 720 500" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="g-claude" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#F7EBD4"/>
      <stop offset="100%" stop-color="#E8DEC8"/>
    </linearGradient>
    <marker id="arr-gold" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="6" markerHeight="6" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#B8864E"/>
    </marker>
  </defs>

  <!-- 노드: 카테고리별 색 + 그라디언트 fill -->
  <rect x="270" y="195" width="180" height="125" rx="16"
        fill="url(#g-claude)" stroke="#B8864E" stroke-width="3.5"/>
  <text font-family="Fraunces" font-size="24" font-weight="700">Claude Opus</text>

  <!-- 화살표: marker-end 로 자동 -->
  <line x1="360" y1="116" x2="360" y2="190"
        stroke="#B8864E" stroke-width="2.5" marker-end="url(#arr-gold)"/>

  <!-- 그룹 박스 (점선 dashed border) — 카테고리 묶음 -->
  <rect x="30" y="160" width="200" height="200" rx="14"
        fill="rgba(107,142,127,0.08)" stroke="#6B8E7F"
        stroke-width="1.5" stroke-dasharray="6,4"/>
</svg>
```

**핵심**:
- `<defs>` 에 gradient + marker 미리 정의 (재사용)
- marker 의 `refX="9" refY="5"` — 화살표 끝점 정확히 노드 경계에
- 카테고리 색: gold (lead) · sage (impl) · plum (review) · terra (warn) · deep-gold (hub)
- 그룹 박스: `stroke-dasharray="6,4"` 로 시각적 묶음
- Stage 라벨 (예: "CODEX POOL ×4") 박스 위에 16~18px font + letter-spacing 으로 카테고리 명시

### E. 표 → 카드 그리드 변환 (10행+ 가독성 떨어질 때)
**증상**: 8~10행 표 안 텍스트 너무 작음 (16px 이하).
**해결**: 4×2 또는 3×2 카드 그리드로 변환.

```html
<div class="body">  <!-- grid-template-columns: repeat(4, 1fr); rows: 1fr 1fr -->
  <div class="card">
    <div class="num">CASE 01</div>
    <div class="symptom">
      <iconify-icon icon="heroicons:exclamation-triangle"></iconify-icon>
      <div class="t">setup 관리자 권한 요청 후 멈춤</div>
    </div>
    <div class="cause">UAC 거부 또는 그룹 정책 차단</div>
    <div class="fix">우클릭 → "관리자 권한으로 실행"</div>
  </div>
  <!-- ... 7 more cards -->
</div>
```
```css
.body { display: grid; grid-template-columns: repeat(4, 1fr);
  grid-template-rows: 1fr 1fr; gap: 16px; }
.card { background: rgba(255,255,255,0.88); border-radius: 14px;
  padding: 16px 18px; display: flex; flex-direction: column; gap: 8px;
  position: relative; overflow: hidden; }
.card::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0;
  width: 4px; background: var(--terracotta); }   /* 좌측 컬러 바 */
.card .num { font-size: 11px; letter-spacing: 0.18em; color: var(--stone); }
.card .symptom { display: flex; gap: 8px;
  padding-bottom: 8px; border-bottom: 0.5px dashed rgba(178,90,62,0.3); }
.card .symptom .t { font-size: 16px; font-weight: 700; color: var(--terracotta); }
.card .cause::before { content: '원인 · ';
  font-size: 11px; letter-spacing: 0.1em; font-weight: 700;
  color: var(--deep-gold); text-transform: uppercase; }
.card .fix { margin-top: auto; padding-top: 8px;
  border-top: 0.5px dashed rgba(107,142,127,0.3); }
.card .fix::before { content: '✓ '; color: var(--sage); font-weight: 700; }
```

**핵심**:
- 카드 안 3 영역: 증상 (header, 강조) / 원인 (mid, stone) / 해결 (footer, ink + ✓)
- `margin-top: auto` 로 fix 섹션을 카드 하단에 push
- 행 수 8 = 4×2, 6 = 3×2, 12 = 4×3 (더 많으면 슬라이드 분할 권장)

### F. 결정 트리 배너 (분기 시각화)
**사용처**: "단순 텍스트 2 컬럼" 위에 시각적 분기 다이어그램 추가.

```html
<div class="decision-banner">
  <div class="tick">
    <iconify-icon icon="heroicons:bolt"></iconify-icon>
    <span>매 30s · HEARTBEAT TICK</span>
  </div>
  <svg viewBox="0 0 800 60" preserveAspectRatio="none">
    <line x1="10" y1="30" x2="320" y2="30" stroke="#8A6235" stroke-width="2"/>
    <polygon points="320,8 380,30 320,52 260,30"
             fill="#FAF5EA" stroke="#8A6235" stroke-width="2"/>   <!-- diamond -->
    <text x="320" y="35" text-anchor="middle">의도된 stop?</text>
    <line x1="380" y1="30" x2="540" y2="14"
          stroke="#6B8E7F" stroke-width="2" marker-end="url(#ar-sage)"/>
    <text x="460" y="6">NO → 자동 복구</text>
    <line x1="380" y1="30" x2="540" y2="46"
          stroke="#B25A3E" stroke-width="2" marker-end="url(#ar-terra)"/>
    <text x="460" y="59">YES → 정지 유지</text>
  </svg>
  <div class="legend">
    <span class="chip alive">5 ALIVE</span>
    <span class="chip stop">5 STOP</span>
  </div>
</div>
```

**핵심**:
- diamond 점 4개로 그리기: `points="cx,top cx+w/2,cy cx,bottom cx-w/2,cy"`
- NO 분기는 sage, YES 분기는 terracotta (의미 색)
- 좌측 trigger icon + 우측 카테고리 chip 으로 양 끝 라벨링

### G. 안티패턴 (R51 발견)
- `.savings` grid 자식이 `flex: 1` 안에 들어가면 압축됨 → `flex: 0 0 auto`
- AFTER 막대 `width: %` 를 데이터 비율로 계산 안 하면 임팩트 사라짐
- SVG marker 의 `refX/refY` 안 맞추면 화살표가 노드 안으로 들어가거나 떨어져 보임
- 카드 그리드 변환 시 행수 9 이면 3×3 또는 분할 — 4×2 짝수 그리드만 가능
- decision diamond 텍스트 폰트 12~14px 권장 (작으면 안 보이고 크면 diamond 밖으로 나옴)

---

## 14. Screens 워크플로우 (docs/screens/our-html — 2026-04-30)

PPT 외에 **README · 블로그 · 깃 리포 표지** 용 단일 PNG 이미지가 필요할 때.
별도 워크플로우 — `docs/screens/` 에 카테고리별 이미지 모아둠.

### 폴더 구조

```text
docs/screens/
├── arch/         외부 참고 자료 (Brij Pandey 등)
├── func/         외부 참고 자료
├── dashboard/    외부 참고 자료
├── login/        외부 참고 자료
├── our-html/     ← 우리 자체 HTML 소스
│   ├── _styles.css           공통 디자인 시스템
│   ├── arch-*.html           시스템 아키텍처 / 흐름도
│   └── func-*.html           기능 / 혜택 일러
├── our-arch/     렌더 결과 (arch-*.png)
└── our-func/     렌더 결과 (func-*.png)
```

### 명명 규칙
- `arch-<topic>.html` → `our-arch/arch-<topic>.png` (시스템 다이어그램)
- `func-<topic>.html` → `our-func/func-<topic>.png` (기능 일러)
- 다른 prefix (예: `dash-`, `flow-`) 가 필요하면 `render-screens.py` `out_path_for()` 확장

### 디자인 원칙 (PPT 와 차별)
| 요소 | PPT 슬라이드 | Screens (단일 이미지) |
|------|--------------|----------------------|
| 페이지 번호 | 필수 (NN/총수) | 없음 |
| eyebrow | "PART NN · TOPIC" | "◆ ORCHESTRATION KIT · TOPIC" |
| 제목 | h1 56~64px | h1 80~96px (더 크게) |
| 본문 비중 | 7~10 박스/카드 | 1~2 핵심 + 큰 visual |
| 하단 footer | 출처 표기 | 브랜드 + 카테고리 |
| 배경 | 다양 (bg-tech 등) | `_styles.css .canvas` 통일 |
| 의도 | 1 페이지 = 1 컨셉 | 1 이미지 = 1 메시지 |

### `_styles.css` 공통 시스템
- `.canvas { width: 1920px; height: 1080px; padding: 80px 100px }` 고정
- `.eyebrow` `.h1` `.h1 .accent` `.lead` `.footer` `.dot-grid` `.content` 표준 클래스
- 색상은 PPT 와 동일 (gold/sage/plum/terracotta/deep-gold/cream)

### 렌더 명령
```bash
python .claude/scripts/render-screens.py                    # all
python .claude/scripts/render-screens.py arch-system        # one (no .html)
```

### 검증
- PIL overflow 체크 안 함 (단일 이미지라 잘림 정의가 다름)
- OCR 직접 (Read tool) → 핵심 메시지 한 번에 잡히는지

### 활용 예시
- `our-arch/arch-system-overview.png` → README.md 상단 hero
- `our-func/func-cost-saving.png` → 마케팅 페이지 / 트윗
- `our-arch/arch-plugin-ecosystem.png` → 플러그인 카탈로그 표지

### 안티패턴
- screens 에 PPT 페이지 번호 (NN/총수) 추가 — 단일 이미지에 어색
- `_styles.css` 안 쓰고 매 HTML 마다 padding/font 다르게 — 카탈로그 일관성 깨짐
- prefix 없는 파일명 (예: `overview.html`) — 자동 분류 안 됨 → arch/func 결정 어려움
- 공통 CSS `_styles.css` 를 sync 대상 plugins/ 에 넣지 않음 (PPT design-system.css 와 별개 유지)
