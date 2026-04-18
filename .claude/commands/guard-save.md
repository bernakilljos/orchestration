---
description: "현재 세션 상태 즉시 스냅샷 저장 — 토큰 소진 대비 방어적 저장"
---

# /guard-save — 즉시 스냅샷 저장

## 목적
사용자가 명시적으로 "지금 상태 저장" 요청할 때 실행.
토큰 여유 있을 때 방어적으로 저장해두면 이후 소진되어도 안전.

## 실행
1. `plugins/exec_session_guard/skills/guard_snapshot.md` 의 SAVE 액션 수행
2. `.claude/context-cache/session-snapshot.md` 에 아래 포맷으로 **덮어쓰기**:

```markdown
## Session Snapshot - [YYYY-MM-DD HH:MM]

### Current Task
- Title:  [작업 제목]
- Goal:   [구현 목표]
- Status: [research | implementing | reviewing | deploying | blocked]

### Pipeline Progress
- [x] 완료된 단계
- [ ] 현재 단계  ← 여기
- [ ] 남은 단계

### Next Command
[다음에 실행할 정확한 명령 — 복붙 가능하게]

### Modified Files
- path/to/file (new | modified | deleted)

### Key Decisions
- [결정 — 근거 포함]

### Pending / Caution
- [미해결 이슈]

### Reference Files
- [다음 세션에서 다시 읽어야 할 파일 경로들]
```

3. 완료 후 1줄로 결과 보고:
   `[guard-save] saved at HH:MM — next: <Next Command>`

## 인자
없음. 현재 컨텍스트에서 모든 정보 추출.

## 금지
- 확인 질문 없이 즉시 저장 (사용자가 이미 요청했으므로)
- 스냅샷 전체 내용 출력 금지 (파일 경로만 안내)
- 개인정보·API키·토큰은 `[REDACTED]`로 마스킹
