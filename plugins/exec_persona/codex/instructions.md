# exec_persona — Codex 지시서

## Codex 역할
persona 커맨드는 Claude 전용.
Codex는 이 플러그인의 커맨드를 직접 실행하지 않는다.

대신 task-instruction.md에 모드가 명시되면 따른다:
- `mode: godmode` → 최대 출력, 완성된 코드만
- `mode: 10x` → 빠르게, 핵심만
- `mode: brief` → 요약 보고서만
