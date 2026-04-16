---
description: 실행 중인 모든 codex-auto / gemini-auto 루프를 즉시 중단
allowed-tools: Bash(echo:*), Bash(powershell:*), Write
---

## Your task

즉시 다음 순서로 실행한다. 묻지 않는다.

### 1. stop 파일 생성 (루프 신호)
```
echo stop > .claude\tasks\stop
```

### 2. orca-stopped 플래그 생성
```
echo disabled > .claude\orca-stopped
del .claude\orca-enabled 2>/dev/null
```

### 3. 실행 중인 워커 프로세스 즉시 종료
```powershell
Get-Process cmd -ErrorAction SilentlyContinue |
  Where-Object { $_.MainWindowTitle -match 'Codex-Worker|Gemini-Verifier|codex-auto|gemini-auto' } |
  Stop-Process -Force

Get-Process node -ErrorAction SilentlyContinue |
  Where-Object { $_.Path -match 'codex|gemini' } |
  Stop-Process -Force -ErrorAction SilentlyContinue
```

### 4. 결과 보고
```
[STOP] 루프 중단 완료
  - stop 파일 생성됨
  - orca-stopped 플래그 설정됨
  - 종료된 워커: N개
  - 즉시 종료 (다음 루프 대기 없음)
  - 재시작: /vibe-loop
```
