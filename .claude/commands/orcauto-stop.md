---
description: codex-auto / gemini-auto 자동 시작 비활성화 + 실행 중인 워커 종료
allowed-tools: Bash(powershell:*), Bash(echo:*)
---

## Your task

1. `.claude/orca-stopped` 파일 생성 (자동 시작 비활성화 플래그):
   ```
   echo disabled > .claude\orca-stopped
   ```

2. `.claude/orca-enabled` 파일 삭제 (있으면):
   ```
   del .claude\orca-enabled 2>nul
   ```

3. 실행 중인 codex-auto / gemini-auto 워커 윈도우 종료:
   ```powershell
   Get-Process cmd -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -match 'Codex-Worker|Gemini-Verifier'} | Stop-Process -Force
   ```

4. 결과 보고:
   - orca-stopped 플래그 생성됨
   - 종료된 워커 수
   - "Claude 단독 모드. 재활성화: /orcauto-start"
