---
description: status-push / remote-agent 실행 상태 확인 + 필요시 재시작
allowed-tools: Bash(powershell:*), Bash(wscript:*), Bash(reg:*)
---

## Context

- status-push running: !`powershell -NoProfile -Command "Get-Process wscript -ErrorAction SilentlyContinue | Where-Object {$_.Path -like '*status-push*'} | Measure-Object | Select-Object -ExpandProperty Count"`
- remote-agent running: !`powershell -NoProfile -Command "Get-Process wscript,powershell -ErrorAction SilentlyContinue | Where-Object {$_.Path -like '*remote-agent*'} | Measure-Object | Select-Object -ExpandProperty Count"`
- registry status-push: !`reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v OrchestrationStatusPush 2>/dev/null && echo REGISTERED || echo MISSING`
- registry remote-agent: !`reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v OrchestrationRemoteAgent 2>/dev/null && echo REGISTERED || echo MISSING`

## Your task

Check the above context and report status:

| 서비스 | 실행 중 | 레지스트리 등록 |
|--------|---------|----------------|
| status-push | ... | ... |
| remote-agent | ... | ... |

**IF any service is NOT running:**
- Restart it: `wscript "%USERPROFILE%\.claude\status-push-silent.vbs"` (if not running)
- Restart it: `wscript "%USERPROFILE%\.claude\remote-agent-silent.vbs"` (if not running)
- Report what was restarted

**IF registry key is MISSING:**
- Re-register using reg add command
- Report what was registered

Use Bash tool to fix issues automatically without asking.
