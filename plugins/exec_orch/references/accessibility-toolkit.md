# Accessibility Toolkit

> **목적**: 웹 접근성 · WCAG · 포용적 디자인 공통 도구 모음 (60+ 도구)
> **적용 범위**: 웹 · 모바일 · 문서 · PDF · 동영상 · 디지털 제품
> **카테고리**: 10개 영역 · 테스트 · 자동화 · 스크린리더 · ARIA · 색상 · 표준 · 한국

---

## 1. 접근성 테스트 도구 (자동화)

### 자동 스캔 도구

| 도구 | 대상 | 지원 언어 | 가격 | 설치 |
|---|---|---|---|---|
| **axe-core** (Deque) | 웹 · 모든 프레임워크 | JavaScript | 무료 + Pro | `npm install @axe-core/react` |
| **pa11y** | CLI · Node.js · 자동화 | JavaScript | 무료 오픈소스 | `npm install -g pa11y` |
| **Lighthouse** (Google) | 웹 · Chrome 내장 | JavaScript | 무료 | Chrome DevTools 통합 |
| **WAVE** | 웹 · 로컬 · API | 웹 기반 | 무료 + API | https://wave.webaim.org/ |
| **Tenon.io** | 웹 · REST API · SaaS | 웹 기반 | $299/월+ | REST API |
| **ARC Toolkit** (TPGi) | 웹 · 고급 분석 | 전문 도구 | 유료 | Chrome/Firefox 확장 |
| **NVDA 자동 테스트** | 스크린리더 호환성 | NVDA + Python | 무료 | `pip install nvaccess-nvdacontroller` |

### 설치 및 사용

```bash
# axe-core CLI 설치
npm install -g @axe-core/cli

# 스캔 실행
axe https://example.com --standard wcag2aa --tags best-practice
axe https://example.com --format=json > report.json

# pa11y 설치
npm install -g pa11y pa11y-ci

# 한 페이지 테스트
pa11y https://example.com

# 여러 URL 자동화
pa11y-ci --config .pa11y.json
```

### CI/CD 통합 예제

```yaml
# GitHub Actions (axe)
name: Accessibility Tests
on: [push, pull_request]
jobs:
  a11y:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run axe-core scan
        run: |
          npm install -g @axe-core/cli
          axe http://localhost:3000 --standard wcag2aa --exit-code=2
```

---

## 2. 프레임워크별 자동화 도구

### React

```bash
npm install --save-dev jest-axe @axe-core/react
```

```javascript
// jest-axe 테스트
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

test('Button has no accessibility violations', async () => {
  const { container } = render(<button>Click me</button>);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### Playwright

```bash
npm install --save-dev @axe-core/playwright
```

```javascript
// Playwright E2E 테스트
import { injectAxe, checkA11y } from 'axe-playwright';

test('Login page accessibility', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  await injectAxe(page);
  await checkA11y(page, null, {
    detailedReport: true,
    detailedReportOptions: { html: true }
  });
});
```

### Cypress

```bash
npm install --save-dev @axe-core/cypress
```

```javascript
// cypress/e2e/accessibility.cy.js
describe('Accessibility Tests', () => {
  it('Home page has no a11y violations', () => {
    cy.visit('http://localhost:3000');
    cy.injectAxe();
    cy.checkA11y();
  });
});
```

---

## 3. 스크린리더 (텍스트 음성 변환)

### 공식 도구

| 스크린리더 | OS | 가격 | 강점 | 약점 |
|---|---|---|---|---|
| **NVDA** | Windows | 무료 오픈소스 | 무료 · 강력 · 커뮤니티 | 성능 · 일부 웹사이트 호환성 |
| **JAWS** | Windows | $90-125 | 업계 표준 · 높은 호환성 · 기능 풍부 | 비싸짐 · 가파른 학습곡선 |
| **VoiceOver** | macOS · iOS | 무료 (OS 기본) | Mac/iPhone 최적화 · 성숙도 | Mac 중심 |
| **TalkBack** | Android | 무료 (OS 기본) | Android 최적화 · 무료 | 개별 앱 지원 의존 |
| **Orca** | Linux | 무료 오픈소스 | 무료 · Linux 최적화 | 커뮤니티 작음 |
| **JAWS Mobile** | iOS/Android | 유료 | 모바일 특화 | 비싼 라이선스 |

### 설치 및 테스트

```bash
# NVDA (Windows)
# https://www.nvaccess.org/ 에서 다운로드

# VoiceOver (macOS)
# System Preferences > Accessibility > VoiceOver > Enable
# 단축키: Cmd + F5

# TalkBack (Android)
# Settings > Accessibility > Text-to-speech > TalkBack > Enable

# NVDA 자동 테스트 (Python)
pip install pywinauto pyautogui
```

### 테스트 체크리스트

```markdown
스크린리더 호환성 테스트:
- [ ] 모든 버튼에 접근 가능한 이름 있음 (aria-label 또는 텍스트)
- [ ] 이미지에 alt 텍스트 있음
- [ ] 폼 라벨과 입력 필드가 연결됨 (<label for="...">)
- [ ] 키보드 네비게이션 가능 (Tab · Enter · Space)
- [ ] 포커스 표시자 시각적으로 명확
- [ ] 동적 콘텐츠 업데이트 시 aria-live 사용
- [ ] 테이블에 <th> 헤더 있음
- [ ] 모든 기능이 마우스 없이 접근 가능
```

---

## 4. 색상 접근성 & 명도 대비

### 대비 검사 도구

| 도구 | 기능 | 사용법 |
|---|---|---|
| **WebAIM Contrast Checker** | 색상 쌍 대비 검사 | https://webaim.org/resources/contrastchecker/ |
| **Contrast Ratio** (Lea Verou) | 실시간 대비 계산 | https://contrast-ratio.com/ |
| **Stark** | Figma/Sketch 플러그인 | 디자인 단계 검사 |
| **Color Oracle** | 색맹 시뮬레이션 (데스크톱) | https://colororacle.org/ |
| **Who Can Use** | 색상 조합 포용성 | https://www.whocanuse.com/ |
| **Colorable** | 대비 온팔레트 | https://colorable.jxnblk.com/ |

### WCAG 2.1 대비 기준

```text
콘텐츠 유형별 최소 명도 대비 (Luminance Contrast Ratio):

1. 일반 텍스트
   - AA: 4.5:1 (정상 시력)
   - AAA: 7:1 (약시)
   
2. 큰 텍스트 (18pt+ 또는 14pt bold+)
   - AA: 3:1
   - AAA: 4.5:1

3. UI 컴포넌트 & 그래픽
   - AA: 3:1 (경계선 · 버튼 · 아이콘)
   - AAA: 해당 없음 (최소 AA만)

예:
✅ 검정(#000000) on 흰색(#FFFFFF): 21:1 (WCAG AAA)
❌ 회색(#777777) on 흰색(#FFFFFF): 4.4:1 (AA, AAA 실패)
```

### CSS 권장 사항

```css
/* 명도 대비 높음 */
body {
  color: #212121;  /* 진한 회색 또는 검정 */
  background-color: #ffffff;  /* 흰색 */
}

a {
  color: #0066cc;  /* 파란색 (링크) */
  text-decoration: underline;  /* 색상만 아닌 추가 표시 */
}

button:focus {
  outline: 3px solid #0066cc;  /* 명확한 포커스 표시 */
  outline-offset: 2px;
}
```

---

## 5. ARIA (Accessible Rich Internet Applications)

### 자주 쓰는 ARIA 속성

| 속성 | 목적 | 예시 |
|---|---|---|
| `aria-label` | 접근 가능한 이름 (시각 보이지 않음) | `<button aria-label="메뉴 열기">☰</button>` |
| `aria-labelledby` | 다른 요소와 연결 | `<div id="title">제목</div><main aria-labelledby="title">` |
| `aria-describedby` | 추가 설명 | `<input aria-describedby="password-hint">` |
| `aria-live` | 동적 업데이트 알림 | `<div aria-live="polite" aria-atomic="true">업데이트됨</div>` |
| `aria-hidden="true"` | 스크린리더에서 숨김 | `<span aria-hidden="true">→</span>` |
| `role` | 요소의 의미 | `<div role="button">클릭</div>` |
| `aria-expanded` | 열림/닫힘 상태 | `<button aria-expanded="false" aria-controls="menu">` |
| `aria-current` | 현재 페이지 표시 | `<a href="/" aria-current="page">홈</a>` |
| `aria-required` | 필수 필드 | `<input aria-required="true">` |
| `aria-invalid` | 오류 상태 | `<input aria-invalid="true" aria-errormessage="error-msg">` |

### 패턴 (Best Practices)

```html
<!-- ❌ 나쁜 예 -->
<div onclick="toggleMenu()">메뉴</div>

<!-- ✅ 좋은 예 -->
<button 
  aria-expanded="false"
  aria-controls="navigation"
  aria-label="주 네비게이션 메뉴 열기">
  메뉴
</button>
<nav id="navigation" hidden>
  <!-- 메뉴 항목 -->
</nav>
```

---

## 6. 키보드 네비게이션 & 포커스 관리

### JavaScript 라이브러리

```bash
npm install focus-trap focus-visible inert-polyfill
```

```javascript
// focus-trap: 모달 내 포커스 갇힘
import FocusTrap from 'focus-trap';

const modal = document.querySelector('[role="dialog"]');
const focusTrap = new FocusTrap(modal);
focusTrap.activate();  // 모달 열릴 때
focusTrap.deactivate();  // 모달 닫힐 때

// focus-visible: CSS 포커스 표시
import 'focus-visible';
button:focus-visible {
  outline: 3px solid #0066cc;
}
```

### 키보드 이벤트 처리

```javascript
// ❌ 잘못된 예: Enter만 처리
<div onclick="handleClick()" onkeydown={e => e.key === 'Enter' && handleClick()}>

// ✅ 올바른 예: Button 사용 또는 Space도 처리
<button onclick="handleClick()">클릭</button>

// 또는 div에서:
<div role="button" tabindex="0" onkeydown={e => {
  if (e.key === 'Enter' || e.key === ' ') handleClick();
}}>
```

### 탭 순서 관리

```html
<!-- tabindex 사용 (최소화) -->
<form>
  <input type="text" placeholder="이름" tabindex="1">
  <input type="email" placeholder="이메일" tabindex="2">
  <button type="submit" tabindex="3">제출</button>
</form>

<!-- 권장: DOM 순서 따르기 (tabindex 불필요) -->
<form>
  <input type="text" placeholder="이름">
  <input type="email" placeholder="이메일">
  <button type="submit">제출</button>
</form>
```

---

## 7. 웹 문서 접근성 (PDF · Word · PPTX)

### PDF 접근성 검사

| 도구 | 기능 | 가격 |
|---|---|---|
| **PAC (PDF Accessibility Checker)** | PDF 자동 검사 · 상세 리포트 | 무료 오픈소스 |
| **axe for PDF** | axe 통합 · 웹 기반 | 유료 |
| **Adobe Acrobat A11y** | 내장 기능 · 자동 수정 | Adobe DC 구독 (월 $14.99+) |
| **PAVE** | PDF 시각화 · 검증 | 무료 |

```bash
# PAC 설치 및 사용
# https://www.access-for-all.ch/en/pdf-pac.html 에서 다운로드
# GUI로 PDF 선택 → Scan → 리포트 생성
```

### Word (.docx) 접근성

```markdown
Word 문서 접근성 체크리스트:
- [ ] 제목 계층구조 (H1 → H2 → H3) 올바름
- [ ] 모든 이미지에 alt 텍스트 있음 (우클릭 → 그림 설명 편집)
- [ ] 테이블에 헤더 행 표시됨 (Design > Table Design > Header Row)
- [ ] 색상만으로 정보 전달 X (텍스트 + 기호 함께)
- [ ] 링크 텍스트가 의미 있음 ("여기 클릭" X → "정책 문서" ✓)
- [ ] 글꼴 크기 ≥12pt
- [ ] 명도 대비 4.5:1 이상

검사 도구:
Tools > Accessibility Checker (Word 2019+)
```

### PowerPoint (.pptx) 접근성

```markdown
PowerPoint 접근성:
- [ ] 슬라이드 제목 모두 있음
- [ ] 슬라이드 예쇄 순서 정확 (Slide Sorter)
- [ ] 이미지 alt 텍스트 (우클릭 → 그림 설명 편집)
- [ ] 테이블 헤더 표시
- [ ] 색상 대비 4.5:1 이상
- [ ] 동영상에 자막 있음
- [ ] 애니메이션 깜빡임 주기 < 3초 (광민감성 발작 방지)

검사 도구:
Review > Check Accessibility
```

---

## 8. 웹 콘텐츠 접근성 지침 (WCAG)

### WCAG 2.1 레벨별 요구사항

| 레벨 | 준수 난이도 | 요구사항 | 기준 |
|---|---|---|---|
| **A** | 기본 | 기본 접근성 (22개 기준) | 웹사이트 최소 권장 |
| **AA** | 중간 | 일반 사용자 접근 (50개 기준) | 정부 · 공공 · 대기업 표준 |
| **AAA** | 고급 | 약시 · 난청자 포함 (78개 기준) | 의료 · 교육 등 특정 분야 |

### 핵심 기준 (WCAG 2.1 AA)

```text
1.4.3 명도 대비 (최소): 4.5:1 (텍스트) · 3:1 (UI)
2.1.1 키보드: 모든 기능 키보드 접근 가능
2.1.2 키보드 함정 없음: 포커스 이동 가능
2.4.3 포커스 순서: 의미 있는 순서
2.4.7 포커스 시각화: 포커스 표시자 명확
3.2.1 포커스 변경 시 자동 제출 X
3.3.1 오류 식별: 오류 위치 + 설명
3.3.2 레이블 또는 지시: form 레이블 명확
4.1.2 이름 · 역할 · 값: ARIA 올바르게 사용
```

### WCAG 2.2 (2023년 신규)

추가 기준 (주요):
- **2.4.11 포커스 외형**: 포커스 아웃라인 최소 2px · 대비 3:1
- **2.5.7 드래그 대체**: Drag-and-drop 외 방법 제공
- **3.3.7 문맥 관련 도움**: 제출 전 오류 확인 기회

---

## 9. 한국 웹 접근성 표준

### 웹 접근성 인증 (한국정보화진흥원)

```markdown
웹 접근성 품질인증(WA) 기준:
- 정부 표준: 22개 항목
  1. 인식의 용이성
  2. 운용의 용이성
  3. 이해의 용이성
  4. 견고성

기본 준수:
- 한글 맞춤법 준수
- 텍스트 대체: alt 텍스트 · 자막 (한국어)
- 색상 대비: 3:1 이상 (WCAG AA)
- 키보드 네비게이션
- 링크 텍스트 의미: "클릭" X → "정책 열람" O
```

### 인증 획득 절차

```text
1. 웹사이트 자체 평가 (감시기관 도구)
2. 감시기관 신청 (한국정보화진흥원 지정)
3. 현장 점검 (약 2주)
4. 개선 권고안 제시
5. 재심사 후 인증서 발급
```

### 한국어 특화 체크리스트

```markdown
한국 사용자 중심:
- [ ] 한글 맞춤법 (문화체육관광부 표준)
- [ ] 한글 자모 분리 불가 (한글 특수성)
- [ ] 영문 약어 첫 사용 시 풀어쓰기 (예: WCAG → 웹 콘텐츠 접근성 지침)
- [ ] 숫자 표기: "2026년 5월 20일" O (달력 맞춤)
- [ ] 이름 · 성별 · 나이 자동 선택 금지 (차별 방지)
- [ ] 방언 · 경어 톤 일관성 (e.g., 존댓글 통일)
```

---

## 10. 접근성 설계 원칙 (Inclusive Design)

### 7가지 핵심 원칙

| 원칙 | 실천 |
|---|---|
| **1. 인식 가능** | 모든 사용자가 콘텐츠 감지 가능 (시각 · 청각 · 촉각) |
| **2. 운용 가능** | 키보드 · 마우스 · 음성 등 다양한 입력 지원 |
| **3. 이해 가능** | 명확한 언어 · 예측 가능한 동작 · 오류 방지 |
| **4. 견고성** | 현재 · 미래 기술에서도 작동 (호환성) |
| **5. 공정성** | 성별 · 나이 · 장애 · 문화 · 언어 등 차별 제거 |
| **6. 포용성** | 모두를 위한 설계 (특정 집단만 위한 X) |
| **7. 존중성** | 사용자 자율성 · 프라이버시 · 선택권 존중 |

### 디자인 체크리스트

```markdown
모든 사용자를 위한 설계:
- [ ] 텍스트 크기 조정 가능 (최소 200%)
- [ ] 색상 코드 + 기호 (색상만 X)
- [ ] 자막 · 음성 설명 제공
- [ ] 읽기 시간 · 비상 정지 가능 (깜빡임 방지)
- [ ] 마우스 호버 · 포커스 상태 명확히 표시
- [ ] 복잡한 단어 풀이 또는 용어집
- [ ] 개인정보 수집 최소화 · 명확한 설명
- [ ] 암호 요구사항 현실적 (8자 O, 특수문자 4종류 X)
```

---

## 11. 도구 통합 워크플로우

### 개발 프로세스

```yaml
개발 단계별:
  디자인:
    - Figma/Sketch에 Stark 플러그인 사용 → 색상 대비 검사
  
  개발:
    - axe DevTools 또는 Lighthouse Chrome DevTools 자동 스캔
    - 코드 리뷰: alt 텍스트 · ARIA · 키보드 검사
  
  테스트:
    - jest-axe 또는 Cypress axe 자동화 테스트
    - NVDA/VoiceOver 수동 스크린리더 테스트
    - 키보드 네비게이션 (Tab · Enter · Space)
  
  배포 전:
    - pa11y-ci 최종 스캔
    - WAVE 수동 점검
  
  배포 후 (정기):
    - 월 1회: axe-core 전체 스캔
    - 분기 1회: 사용자 테스트 (장애인 포함)
```

### 자동화 예제 (GitHub Actions)

```yaml
name: Accessibility CI
on: [push, pull_request]

jobs:
  a11y:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      
      - name: Install dependencies
        run: npm install
      
      - name: Build
        run: npm run build
      
      - name: Start preview
        run: npm run preview &
      
      - name: Run axe scan
        run: npx @axe-core/cli http://localhost:3000 --standard wcag2aa
      
      - name: Run Jest + jest-axe
        run: npm run test:a11y
      
      - name: Run pa11y-ci
        run: npx pa11y-ci --config .pa11y.json
```

---

## 12. 비용 최적화

| 시나리오 | 권장 도구 조합 | 비용 |
|---|---|---|
| **스타트업** | axe DevTools (무료) + NVDA (무료) + GitHub Actions | $0 |
| **팀 개발** | axe-core (npm) + jest-axe + Lighthouse (자동) | $0 (오픈소스) |
| **엔터프라이즈** | Deque axe Pro ($1,000+) + ARC Toolkit + 수동 감사 | $2,000+/년 |
| **정부/공공** | WCAG 2.1 AA 준수 + 한국정보화진흥원 인증 신청 | 인증료 없음 (감시기관 평가료) |

---

## 13. 학습 자료

### 공식 가이드
- **WCAG 2.1**: https://www.w3.org/WAI/WCAG21/quickref/
- **WAI-ARIA Authoring Practices**: https://www.w3.org/WAI/ARIA/apg/
- **WebAIM 기사**: https://webaim.org/articles/
- **한국정보화진흥원**: https://www.nia.or.kr/ (웹접근성 표준)

### 커뮤니티
- **a11y Slack**: https://a11y.slack.com/
- **A11yProject**: https://www.a11yproject.com/
- **Stack Overflow**: #accessibility #wcag #a11y

### 도서 & 강좌
- "Building Accessible Websites" (Joe Dolson)
- "Inclusive Components" (블로그): https://inclusive-components.design/
- **Udemy**: "Web Accessibility by Google" 등

---

## 14. 의사결정 트리

```text
접근성 요구사항 정의?
├─ 입문 (개인 블로그)
│  └─ WCAG A (기본)
│     도구: axe DevTools + NVDA (무료)
├─ 중급 (스타트업 · SaaS)
│  └─ WCAG AA (표준)
│     자동: jest-axe + GitHub Actions
│     수동: NVDA 테스트 월 1회
├─ 고급 (정부 · 공공)
│  └─ WCAG AAA 또는 한국 WA 인증
│     감시기관 신청 → 현장 점검 → 인증
└─ 진행 중 (기존 웹사이트)
   ├─ 우선순위: 색상 대비 > 키보드 > ARIA
   ├─ 점진적 개선 (100% 목표 X, 80%+ 현실적)
   └─ 사용자 피드백 수집 (장애인 포함)
```

---

**최종 업데이트**: 2026-05-20
