---
description: "전체 검증 — 테스트 실행 + 스크린샷 캡처 + 결과 증거 저장"
allowed-tools: Bash(npm:*), Bash(python:*), Bash(pytest:*), Bash(mvn:*), Bash(powershell:*)
---

## Context
- 프로젝트 타입: !`if exist package.json (echo nodejs) else if exist pom.xml (echo java) else if exist requirements.txt (echo python) else (echo unknown)`
- Playwright MCP: !`claude mcp list 2>/dev/null | grep -i playwright && echo OK || echo 없음`
- 테스트 파일 수: !`find . -name "*.test.*" -o -name "*_test.*" -o -name "test_*" 2>/dev/null | grep -v node_modules | grep -v .git | wc -l`
- 오늘 날짜: !`date /t 2>nul || date +%Y-%m-%d`

## Your task

파이프라인: **테스트 실행 → 스크린샷 캡처 → 결과 보고서**

---

### Step 1 — 테스트 실행 (직접 실행)

**Node.js:**
```
npm test 2>&1
```

**Python:**
```
pytest -v --tb=short 2>&1
```

**Java:**
```
mvn test -q 2>&1
```

결과를 `docs/YYYY-MM-DD/validation/test-result.txt` 에 저장.

---

### Step 2 — 스크린샷 캡처 (Playwright MCP)

Playwright MCP OK → 실행 중인 로컬 서버 스크린샷:

```
mcp__playwright 또는 playwright MCP 호출:
  1. http://localhost:3000 (또는 감지된 포트)
  2. 주요 페이지 순서대로 캡처:
     - 메인 페이지
     - 로그인 페이지 (있으면)
     - 핵심 기능 페이지
  3. 각 스크린샷: docs/YYYY-MM-DD/validation/screenshots/페이지명.png
```

Playwright 없으면:
```
powershell -NoProfile -Command "
  Add-Type -AssemblyName System.Windows.Forms
  Add-Type -AssemblyName System.Drawing
  $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
  $bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
  $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
  $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
  $bitmap.Save('docs/YYYY-MM-DD/validation/screenshots/screen.png')
"
```

---

### Step 3 — 코드 정적 분석

**보안 취약점:**
```
npm audit 2>&1 | tail -5     (Node.js)
pip-audit 2>&1 | tail -5     (Python)
```

**Lint:**
```
npm run lint 2>&1 | tail -20   (Node.js)
flake8 . --count 2>&1          (Python)
```

결과를 `docs/YYYY-MM-DD/validation/lint-result.txt` 에 저장.

---

### Step 4 — task-instruction.md 대조 검증

`.claude/tasks/task-instruction.md` 의 `## Expected Output` 섹션과 실제 결과 비교:

- 명시된 파일이 실제로 생성됐는지 확인
- API 엔드포인트 응답 확인 (curl)
- DB 마이그레이션 적용 확인

---

### Step 5 — 보고서 생성

`docs/YYYY-MM-DD/validation/report.md` 저장:

```markdown
# 검증 보고서 — YYYY-MM-DD HH:MM

## 테스트 결과
- 총: N개 | 통과: N개 | 실패: N개
- 실패 항목: [목록]

## 스크린샷
- [메인페이지](screenshots/main.png)
- [기능페이지](screenshots/feature.png)

## 보안
- npm audit: N개 취약점
- 심각도: low/medium/high

## Lint
- 오류: N개 | 경고: N개

## Expected Output 대조
- [x] 파일A 생성 확인
- [ ] 파일B 미생성 (FAIL)

## 결론
PASS / FAIL — [요약]
```

---

### Step 6 — 결과 전달

- PASS → exec_orch 파이프라인의 Gemini Validator로 전달
- FAIL → Claude에게 에스컬레이션 + 재시도 카운트 업데이트
  `.claude/state/retry-count.json` 업데이트
