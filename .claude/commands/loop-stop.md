---
description: 실행 중인 모든 codex-auto / gemini-auto 루프를 중단
allowed-tools: Bash(echo:*), Write
---

## Your task

1. Create the stop file to signal all workers to halt:
   - Write `.claude/tasks/stop` with content "stop"

2. Inform user:
   ```
   [STOP] 루프 중단 신호 전송됨
   - codex-auto / gemini-auto 워커들이 다음 루프에서 자동 종료됩니다
   - 즉시 종료하려면 각 터미널에서 Ctrl+C
   - 재시작: 세션 재진입 또는 `codex-auto-global` / `codex-auto` 직접 실행
   ```

Do this immediately without asking.
