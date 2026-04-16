---
description: "성능 검사 — 응답시간·메모리·번들크기·Lighthouse 점수"
allowed-tools: Bash(npm:*), Bash(powershell:*), Bash(where:*), Bash(curl:*)
---

## Context
- 로컬 서버: !`powershell -NoProfile -Command "netstat -ano | Select-String ':300[0-9]' | Select-Object -First 1"`
- Lighthouse: !`where lighthouse 2>/dev/null && echo OK || echo 없음`
- 프로젝트 타입: !`if exist package.json (echo nodejs) else (echo unknown)`

## Your task

### Step 1 — 응답시간 측정 (직접 실행)

```powershell
# 로컬 서버 응답시간 10회 측정
$times = 1..10 | ForEach-Object {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  try { Invoke-WebRequest http://localhost:3000 -UseBasicParsing -TimeoutSec 5 | Out-Null } catch {}
  $sw.ElapsedMilliseconds
}
$avg = ($times | Measure-Object -Average).Average
Write-Host "평균 응답시간: ${avg}ms"
Write-Host "최대: $(($times | Measure-Object -Maximum).Maximum)ms"
Write-Host "최소: $(($times | Measure-Object -Minimum).Minimum)ms"
```

### Step 2 — 번들 크기 분석 (Node.js)

```
# 빌드
npm run build 2>&1

# 번들 크기 확인
powershell: Get-ChildItem dist -Recurse | Measure-Object -Property Length -Sum
```

### Step 3 — Lighthouse 점수 (있으면)

```
lighthouse http://localhost:3000 --output json --output-path docs/YYYY-MM-DD/validation/lighthouse.json --chrome-flags="--headless"
```

주요 지표 추출:
- Performance: N/100
- Accessibility: N/100
- Best Practices: N/100
- SEO: N/100

### Step 4 — 메모리 사용량

```powershell
Get-Process node -ErrorAction SilentlyContinue |
  Select-Object Name, CPU, WorkingSet64 |
  ForEach-Object { Write-Host "$($_.Name): $([math]::Round($_.WorkingSet64/1MB, 1))MB" }
```

### Step 5 — 보고서

`docs/YYYY-MM-DD/validation/performance-report.md` 저장:

```markdown
# 성능 검사 보고서 — YYYY-MM-DD

## 응답시간
- 평균: Nms | 최대: Nms | 최소: Nms
- 기준: 200ms 이하 PASS

## 번들 크기
- 총: NMB
- 기준: 5MB 이하 PASS

## Lighthouse
| 항목 | 점수 | 기준 |
|------|------|------|
| Performance | N | 90+ |
| Accessibility | N | 90+ |

## 메모리
- Node.js: NMB
- 기준: 500MB 이하 PASS

## 결론
PASS / FAIL
```
