---
description: "빠른 종합 체크 — 서비스 상태 + 테스트 + 스크린샷 한 번에"
allowed-tools: Bash(powershell:*), Bash(npm:*), Bash(where:*)
---

## Context
- 서비스 상태: !`powershell -NoProfile -Command "Get-Process wscript -ErrorAction SilentlyContinue | Where-Object {$_.Path -like '*status-push*'} | Measure-Object | Select-Object -ExpandProperty Count"`
- 로컬 서버: !`powershell -NoProfile -Command "netstat -ano | Select-String ':300[0-9]\s' | Select-Object -First 1"`
- 테스트 결과: !`npm test 2>/dev/null | tail -5 || echo "테스트 없음"`
- Playwright: !`claude mcp list 2>/dev/null | grep -i playwright && echo OK || echo 없음`

## Your task

빠른 3단계 체크:

### 1. 서비스 체크
status-push / remote-agent 실행 여부 확인.
중단됐으면 자동 재시작:
```
wscript "%USERPROFILE%\.claude\status-push-silent.vbs"
wscript "%USERPROFILE%\.claude\remote-agent-silent.vbs"
```

### 2. 테스트 실행
Context의 테스트 결과 기반으로 PASS/FAIL 판단.
FAIL 있으면 → `/validate` 실행 권고.

### 3. 스크린샷
로컬 서버 감지되면 → `/screenshot` 실행해서 현재 화면 캡처.

### 결과 요약표
| 항목 | 상태 | 비고 |
|------|------|------|
| status-push | OK/중단 | |
| remote-agent | OK/중단 | |
| 테스트 | PASS/FAIL | N개 중 N개 통과 |
| 스크린샷 | 완료/서버없음 | |

문제 있으면 → `/validate`, `/security`, `/performance` 실행 권고.
