---
description: "스크린샷 캡처 — Playwright로 페이지 캡처 + 시각적 검증"
allowed-tools: Bash(powershell:*), Bash(npm:*), Bash(where:*)
---

## Context
- Playwright MCP: !`claude mcp list 2>/dev/null | grep -i playwright && echo OK || echo 없음`
- 로컬 서버 포트: !`powershell -NoProfile -Command "netstat -ano | Select-String ':300[0-9]\s' | Select-Object -First 3"`
- 오늘 날짜: !`date /t 2>nul`

## Your task

입력: `$ARGUMENTS` (URL 또는 포트번호. 없으면 localhost:3000)

### Step 1 — 출력 폴더 생성
```
docs/YYYY-MM-DD/validation/screenshots/
```

### Step 2 — Playwright MCP로 캡처

Playwright OK →
```
playwright MCP 호출:
  url: $ARGUMENTS 또는 http://localhost:3000
  
  캡처 페이지 목록:
  1. / (메인)
  2. /login (있으면)
  3. $ARGUMENTS 에 명시된 추가 경로

  각 캡처:
    - 파일: docs/YYYY-MM-DD/validation/screenshots/[페이지].png
    - 전체 페이지 (full-page: true)
    - 뷰포트: 1280x720
```

Playwright 없으면 → PowerShell 화면 캡처:
```powershell
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$s = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap($s.Width, $s.Height)
[System.Drawing.Graphics]::FromImage($bmp).CopyFromScreen($s.Location, [System.Drawing.Point]::Empty, $s.Size)
$bmp.Save("docs/YYYY-MM-DD/validation/screenshots/screen.png")
```

### Step 3 — 결과
캡처된 스크린샷 목록 + 경로 보고.
이상한 화면(에러 페이지, 빈 화면) 감지 시 FLAG.
