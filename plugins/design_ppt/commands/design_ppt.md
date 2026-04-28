---
description: "PPT 자동 생성 — HTML/CSS → Playwright → PPTX · 잘림 방지 + OCR 검증 워크플로우"
allowed-tools: Bash(python:*), Bash(playwright:*), Read, Write, Edit, Grep, Glob
---

# /design_ppt — PPT 자동 생성 (HTML/CSS → PPTX) ⭐

> **2026-04-27 업데이트**: 27→40장 확장 작업에서 학습한 함정 13개를 워크플로우에 반영.
> **핵심**: 잘림(overflow) 방지 + OCR 검증 + 파일명 정렬 + 페이지번호 일괄 갱신.

> 이 명령이 **PPT 만들기 기본 액션**입니다. `/make-ppt` 는 호환용 alias.

---

## 빠른 사용

```
/design_ppt "Claude Code 설계" 40
```
- 주제 + 분량 지정 → HTML 슬라이드 자동 생성 → Playwright 렌더 → PPTX 조립
- 모든 PNG OCR 검증 → 잘림 0건까지 iterate
- 결과: `outputs/ppt/orchestration-v1-FINAL.pptx`

특수 템플릿이 필요하면:
- `/ai-system-stages` — AI 시스템 6단계 (Prompt→…→Platform)
- `/arch-auto` — 아키텍처 다이어그램 자동
- `/arch-mindmap` — 마인드맵

설치/설정:
- `/ppt-install` — Playwright + python-pptx 의존성
- `/install-mcp` — Canva·Figma·Gamma MCP 연결

---

## 0. TL;DR — 절대 잊지 말 것 (10 계명)

1. **슬라이드는 1920×1080 고정** — `height: 1080px !important; overflow: hidden !important`
2. **그리드 안 잘림 방지** — `min-height: 0` 을 모든 flex/grid 자식에 추가
3. **코드 박스는 `flex: 0 0 auto`** — `flex: 1` 쓰면 영역 부족시 잘림
4. **코드 12줄 초과시 분할** — `slide-NN.html` + `slide-NNa.html` 로 (1/2), (2/2)
5. **파일명 정렬 = 알파벳 순** — `slide-04` < `slide-04b` < `slide-04c` < `slide-05`
6. **페이지번호는 새 슬라이드 추가시 무조건 일괄 갱신** — `update-ppt-page-numbers.py`
7. **렌더 후 반드시 모든 슬라이드 OCR 검증** — Read tool 로 PNG 직접 보기
8. **"에이전트가 PASS" 거짓말에 속지 마라** — 직접 OCR 로 잘림 확인
9. **PowerPoint 가 파일 잠금** — 재렌더 전 사용자에게 닫으라고 요청
10. **DALL-E 직접 호출 안 됨** — Iconify + SVG + Unsplash + 그라디언트 조합으로 채움

---

## 1. 워크플로우 (5 단계 + 검증 루프)

```
[1] 구조 설계 → [2] HTML 작성 → [3] 렌더링 → [4] OCR 검증 → [5] 수정·재렌더
                                                         ↓ (잘림 0건)
                                                    [완료] git commit
```

### Step 1 — 슬라이드 구조 설계

표준 골격 (40장 기준 권장):
```
01    Cover                  (제목·메트릭)
02    TOC 목차                (5 PART · 페이지 인덱스)
03    PART 0 인트로 (선택)
04    PART 01 Divider        (색: gold)
05~10 PART 01 본문
11    PART 02 Divider        (색: sage)
12~20 PART 02 본문 (.claude/ 9 요소)
21    PART 03 Divider        (색: plum)
22~26 PART 03 본문 (Ecosystem)
27    PART 04 Divider        (색: terracotta)
28~31 PART 04 본문 (Framework)
32    PART 05 Divider        (색: deep-gold)
33~39 PART 05 본문 (Practice)
40    Learn More             (출처·다음 단계)
```

PART 별 색 분배 = 시각적 구분 + 일관성. 하나의 PART 는 한 색만 사용.

### Step 2 — HTML 작성 (잘림 방지 패턴)

**필수 템플릿**:
```html
<style>
  .slide-NN {
    display: flex !important;
    flex-direction: column !important;
    height: 1080px !important;
    padding: 60px 80px 50px 80px !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
  }
  .sNN-body {
    flex: 1;
    display: grid;                          /* 또는 flex */
    grid-template-columns: 1.5fr 1fr;
    gap: 36px;
    margin-top: 24px;
    min-height: 0;                          /* 중요! 자식 잘림 방지 */
    overflow: hidden;
  }
  .sNN-left, .sNN-right {
    display: flex;
    flex-direction: column;
    min-width: 0;
    min-height: 0;                          /* 중요! */
    gap: 14px;
  }
  .sNN-code {
    background: #1A1D24;
    color: #39FF6C;
    font-family: 'JetBrains Mono', monospace;
    font-size: 16px;                        /* 코드 박스는 16~18px */
    line-height: 1.45;                      /* 1.4~1.55 sweet spot */
    padding: 18px 22px;
    border-radius: 12px;
    white-space: pre;
    overflow: hidden;
    flex: 0 0 auto;                         /* 중요! flex:1 X */
  }
</style>
```

**코드 줄 수 가이드** (font-size 16px 기준):
- ~12 줄: 안전, 한 슬라이드 OK
- 13~16 줄: font-size 14~15px 로 줄이거나 분할 검토
- 17 줄+: **분할 필수** — `slide-NN.html` + `slide-NNa.html`

### Step 3 — 렌더링

```bash
python .claude/scripts/generate-final-ppt.py
```

이 스크립트가:
- `outputs/ppt/html-source/slides/slide-*.html` 알파벳 순 정렬
- Playwright (1920×1080, device_scale=2) 로 PNG 변환
- PNG 를 `slide-01.png ... slide-NN.png` 로 자동 재번호
- python-pptx 로 PPTX 조립 → `outputs/ppt/orchestration-v1-FINAL.pptx`

**렌더링 전 PowerPoint 닫기 안내**:
파일 잠금 시 PermissionError. 사용자에게 "PPT 파일 닫아주세요" 요청.

### Step 4 — OCR 검증 (필수)

생성된 모든 PNG 를 Read tool 로 직접 본다:

```python
# 슬라이드 5장씩 묶어 검증
Read(slide-01.png), Read(slide-02.png), Read(slide-03.png), Read(slide-04.png), Read(slide-05.png)
# 각 슬라이드에서 확인:
# 1. 텍스트 잘림 (특히 코드 박스 마지막 줄)
# 2. 큰 빈 공간 (여백미 부족)
# 3. SVG/이미지 위치 어긋남
# 4. 페이지 번호 정합성 (NN/40)
```

**거짓말 탐지**: Sub-Agent 가 "27/27 PASS" 라고 보고해도 직접 OCR 로 재확인.
사용자가 OCR 캡처 보내면 그것이 진실이다.

### Step 5 — 수정·재렌더 (Iterative)

잘림 발견 패턴별 수정:

| 증상 | 원인 | 수정 |
|------|------|------|
| 코드 마지막 줄 잘림 | font-size 너무 큼 | font-size 18→16→14px 단계 축소 |
| 코드 박스 우측 공간 큼 | grid 비율 어긋남 | `1.7fr 1fr` → `1.1fr 1fr` 조정 |
| 카드 하단 빈 공간 | 카드 내용 적음 | `out` 라벨 + 시간 + 코드 chip 추가 |
| 박스 ul 항목 안 보임 | SVG 너무 큼 | `max-width` 줄이기 + `flex-shrink: 0` |
| 마지막 } 살짝 잘림 | 줄 수 1줄 초과 | 코드 한 줄 압축 (인라인 합치기) |

수정 후 → 재렌더 → 재검증 (잘림 0건까지 반복).

---

## 2. 새 슬라이드 끼워넣기 (파일명 정렬 룰)

**알파벳 순 정렬 활용**:
```
기존: slide-04.html, slide-05.html
사이에 끼워넣기:
  slide-04a.html  ← slide-04 다음, slide-05 이전
  slide-04b.html  ← slide-04a 다음
  slide-04c.html  ← slide-04b 다음
```

Python `glob('slide-*.html')` + `sorted()` = 자연 알파벳 정렬.
**검증**: `"slide-04." < "slide-04a" < "slide-04b" < "slide-05"` ✓

---

## 3. 페이지번호 일괄 갱신

새 슬라이드 추가 후 모든 슬라이드의 `NN / 총수` 일괄 변경 필요.

```bash
python .claude/scripts/update-ppt-page-numbers.py
```

이 스크립트가 자동으로:
- `outputs/ppt/html-source/slides/` glob 정렬
- 정렬 순서대로 1, 2, 3... 부여
- HTML 의 `<span class="mono caption">XX / YY</span>` 패턴을 새 번호로 교체
- Cover 의 SLIDES 메트릭, Learn More 의 "N slides" 도 함께 갱신

---

## 4. 분할 패턴 (코드 / 화면 너무 클 때)

**기존**: 1 슬라이드에 코드 14줄 + 사이드 박스 → 잘림.

**분할**:
```
slide-08.html  → settings.json · 권한 (1/2)
                  · permissions 코드 9줄 + 4 mode 카드 + 우측 3 박스
                  · 페이지 13/40

slide-08a.html → settings.json · 훅·MCP·플러그인 (2/2)
                  · hooks/MCP/plugins 코드 13줄 + 우측 3 박스
                  · 페이지 14/40
```

타이틀에 (1/2), (2/2) 표기. eyebrow 에 "PART 02 · SETTINGS (1/2)" 식.
하단 footer 에 "다음 페이지에서 → ..." 안내.

---

## 5. 자산·이미지 채움 (DALL-E 대신)

DALL-E API 직접 호출 안 됨. 대안 4 가지로 시각 풍요:

### A. Iconify (200K+ SVG 아이콘)
```html
<iconify-icon icon="heroicons:rocket-launch" class="bigicon"
              style="font-size: 220px; color: var(--gold);"></iconify-icon>
<iconify-icon icon="simple-icons:github"></iconify-icon>
```

### B. SVG 자체 작성 (정확한 컨트롤)
```html
<svg viewBox="0 0 480 340" style="width:100%; max-width:480px;">
  <circle cx="240" cy="170" r="48" fill="#F7F2EA" stroke="#B8864E" stroke-width="3"/>
  <text x="240" y="177" text-anchor="middle" font-size="18" font-weight="700">Claude</text>
  <!-- 연결선·서비스 노드들 -->
</svg>
```

### C. CSS 그라디언트 + 점 패턴 (배경)
```css
background:
  radial-gradient(ellipse 1100px 800px at 80% 20%, rgba(184,134,78,0.32), transparent 60%),
  radial-gradient(ellipse 800px 600px at 10% 90%, rgba(107,142,127,0.18), transparent 55%),
  linear-gradient(180deg, #FAF5EA 0%, #E8DEC8 100%);
```

### D. Unsplash (URL 임베드, 네트워크 필요)
```html
<div class="hero-bg" style="background-image: url('https://source.unsplash.com/1920x1080/?architecture,minimal');"></div>
```

**추천 조합**: Divider 슬라이드 = 큰 Iconify (220px) + 그라디언트 + 점 그리드.

---

## 6. 디자인 시스템

### 팔레트 (5색)
```css
--gold:       #B8864E    /* PART 01 / 강조 */
--sage:       #6B8E7F    /* PART 02 / 성공 */
--plum:       #7A4E6B    /* PART 03 / 정보 */
--terracotta: #B25A3E    /* PART 04 / 경고 */
--deep-gold:  #8A6235    /* PART 05 / 강조2 */
--ink:        #1A1D24    /* 본문 */
--stone:      #6E685C    /* 보조 */
--fog:        #D8D2C2    /* 보더 */
--cream:      #FAF5EA    /* 배경 */
```

### 폰트 3 종
```html
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&display=swap" rel="stylesheet">
```
- **Pretendard Variable**: 본문 한글 (sans)
- **JetBrains Mono**: 코드·라벨·숫자
- **Fraunces**: 큰 제목 (serif, italic accent)

### 외부 리소스
```html
<link href="../styles/design-system.css" rel="stylesheet">
<script src="https://code.iconify.design/iconify-icon/1.0.8/iconify-icon.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
```

---

## 7. 검증 자동화 (HOOK-09 + verify-ppt-overflow.py)

**자동 트리거**: `generate-*-ppt.py` 실행 후 HOOK-09 가 자동 발화 → `verify-ppt-overflow.py` 호출.

```bash
# 수동 실행도 가능
python .claude/scripts/verify-ppt-overflow.py
python .claude/scripts/verify-ppt-overflow.py --dir outputs/ppt-automation
python .claude/scripts/verify-ppt-overflow.py --threshold 0.10
```

이 스크립트가:
- 모든 `outputs/ppt*/html-source/png-output/slide-*.png` 의 하단·우측 가장자리 30px 픽셀 분석
- RGB < 80 (다크) 픽셀 비율이 임계치 (default 10%) 초과 → 잘림 의심 마킹
- 결과를 `outputs/<dir>/overflow-report.md` 자동 생성
- 의심 발견 시 exit code 2 + system message 로 Claude 에게 알림

**HOOK-09 활성화** (settings.json 1회 등록):
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "bash .claude/hooks/hook-09-ocr-verify.sh", "timeout": 60 }]
    }]
  }
}
```

> 픽셀 분석은 false-positive 가능 (검은 terminal 박스 등) — **Claude OCR 이 최종 판정**.
> 의심 슬라이드는 Claude 가 Read tool 로 직접 보고 의도된 디자인 vs 실제 잘림 판단.

---

## 8. 커밋 전 체크리스트

- [ ] 모든 슬라이드 OCR 로 직접 봤는가
- [ ] 코드 박스 마지막 줄 (특히 닫힘 `}`) 보이는가
- [ ] 페이지 번호 정합 (1/N ~ N/N) 인가
- [ ] Cover 의 SLIDES 메트릭이 실제 장수와 같은가
- [ ] Learn More 의 "N slides" 표기가 같은가
- [ ] PART Divider 색 분배 일관 (PART당 한 색) 인가
- [ ] PowerPoint 에서 직접 열어 확인했는가

---

## 9. 자주 하는 실수 — 사례집

> 자세히는 `skill-ppt-pitfalls.md` 참조.

1. ❌ Sub-Agent "전체 OK" 보고 → 실제 4장 잘림. **수동 OCR 필수**
2. ❌ `flex: 1` 코드 박스 → 영역 부족시 자동 잘림. **`flex: 0 0 auto`**
3. ❌ 새 슬라이드 추가 후 페이지번호 그대로 → "5/27" + "13/40" 혼재. **일괄 갱신**
4. ❌ `slide-04b.html` 만들었는데 PNG 가 slide-05.png 로 출력 — 정렬 자연스러움 OK
5. ❌ Cover 만 페이지번호 갱신 안 됨 — Cover 는 NN/총수 표기 없고 SLIDES 메트릭만
6. ❌ Mermaid 특수문자 `/init` 처리 못해 💣 표시 → 단순 라벨로 변경
7. ❌ optional chaining `?.` 사용 → CSS 파서 에러 (이 프로젝트 금지)
8. ❌ 한글·영문 혼용 description → 검증 스크립트 fail
9. ❌ DALL-E 직접 호출 시도 → API 키 없음. **Iconify + SVG + 그라디언트** 로 대체
10. ❌ 빈 task `done/` 이동 (위장 완료) → 절대 금지

---

## 10. 출처

- 워크플로우: 2026-04-27 27→40장 확장 작업 학습
- 디자인: DK.method (Brij K. Pandey)
- 폰트: Pretendard · JetBrains Mono · Fraunces
- 아이콘: heroicons · simple-icons (Iconify)
- 출력: `outputs/ppt/orchestration-v1-FINAL.pptx`
