---
description: codex-auto / gemini-auto 자동 시작 활성화 + 지금 즉시 워커 시작
allowed-tools: Bash(where:*), Bash(echo:*), Bash(del:*), Bash(powershell:*), Bash(start:*)
---

## Context

- codex-auto 가용: !`where codex-auto 2>nul && echo YES || echo NO`
- gemini-auto 가용: !`where gemini-auto 2>nul && echo YES || echo NO`
- orca-stopped 플래그: !`if exist .claude\orca-stopped (echo STOPPED) else (echo OK)`
- 워커 수 설정: !`if exist .claude\orca-workers (type .claude\orca-workers) else (echo 1)`

## Your task

1. `.claude/orca-stopped` 삭제:
   ```
   del .claude\orca-stopped 2>nul
   ```

2. `.claude/orca-enabled` 생성:
   ```
   echo enabled > .claude\orca-enabled
   ```

3. `.claude/orca-heartbeat` 갱신 (현재 시각):
   - Use Bash tool to write current timestamp

4. 워커 수 결정:
   - `.claude/orca-workers` 파일 있으면 그 숫자 사용
   - 없으면 기본값 1

5. codex-auto가 YES면 → `start "Codex-Worker-1" cmd /c codex-auto [워커수]` 실행
6. gemini-auto가 YES면 → `start "Gemini-Verifier-1" cmd /c gemini-auto [워커수]` 실행

7. 결과 보고:
   | 에이전트 | 상태 | 워커 수 |
   |---------|------|--------|
   | codex-auto | 시작됨/없음 | N |
   | gemini-auto | 시작됨/없음 | N |
   
   "자동 종료: Claude 종료 후 5분 이내 자동 중단됩니다."
