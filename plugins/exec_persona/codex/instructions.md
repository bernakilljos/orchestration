# exec_persona — Codex 지시서

## Codex 역할
persona/mode 커맨드는 Claude 전용.
Codex는 task-instruction.md 의 mode 필드를 참조:

- `mode: godmode`  → 최대 출력, 플레이스홀더 금지, 완성 코드만
- `mode: 10x`      → 빠르게, 핵심만, 군더더기 없이
- `mode: brief`    → 요약 보고서만 작성
- mode 없음        → 기본 처리

## 처리 순서
1. task-instruction.md 의 mode 확인
2. mode에 맞게 출력 수준 조정
3. 구현 완료 → 완료 보고
