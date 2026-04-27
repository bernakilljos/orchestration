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
```
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
**Learn More**: `<span>Opus 4.7 Baseline · 27 slides</span>` — 별도 표기.
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
