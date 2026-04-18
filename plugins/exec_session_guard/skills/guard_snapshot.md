# guard_snapshot — 세션 스냅샷 능동 저장

> **분류:** `exec_session_guard`
> **협력 skill:** `state_session` (SNAPSHOT 액션 재사용)
> **저장 경로:** `.claude/context-cache/session-snapshot.md`

## 목적
토큰 부족·강제 종료에 대비해 Claude가 직접 풍부한 스냅샷을 기록한다.
쉘 훅(stop-snapshot.sh)은 메타만 남기므로, 작업 맥락은 이 skill이 담당.

---

## 트리거
| 조건 | 동작 |
|------|------|
| 컨텍스트 70% 이상 | 자동 호출 |
| 파이프라인 단계 완료 | 체크포인트 저장 |
| `/guard-save` 슬래시 커맨드 | 즉시 저장 |
| 사용자 "저장해줘" / "스냅샷" | 즉시 저장 |
| 위험 작업 직전 (배포, 마이그레이션) | 방어적 저장 |

---

## 액션: SAVE

`.claude/context-cache/session-snapshot.md` 를 아래 포맷으로 **덮어쓰기**:

```markdown
## Session Snapshot - [YYYY-MM-DD HH:MM]

### Current Task
- Title:  [작업 제목 — 한 줄]
- Goal:   [구현 목표 — 왜 하는지 포함]
- Status: [research | implementing | reviewing | deploying | blocked]

### Pipeline Progress
- [x] 완료된 단계
- [ ] 현재 단계  ← 여기
- [ ] 남은 단계

### Next Command
[다음에 실행할 정확한 명령 — 복붙 가능하게]

### Modified Files
- path/to/file1  (new | modified | deleted)
- path/to/file2

### Key Decisions
- [결정 1 — 근거 포함]
- [결정 2]

### Pending / Caution
- [미해결 이슈]
- [주의할 부분]

### Reference Files
- [다음 세션에서 다시 읽어야 할 파일 경로들]

### Last Hook Record
[.claude/context-cache/guard.log 의 마지막 라인 — 쉘 훅이 남긴 최근 흔적]
```

---

## 병합 규칙
- 쉘 훅이 이미 `guard.log`에 남긴 최근 수정 파일·git status는 참고해서 "Modified Files" 보강
- 기존 snapshot이 있으면 **Title이 같은 경우**만 덮어쓰기, 다르면 `session-snapshot.prev.md`로 백업 후 새로 작성
- 개인정보·토큰·비밀번호는 `[REDACTED]`로 마스킹

---

## 실패 시
- 디스크 쓰기 실패 → 사용자에게 즉시 알림 ("스냅샷 저장 실패: 수동 저장 필요")
- 경로 없음 → `.claude/context-cache/` 생성 후 재시도
- 절대 조용히 실패하지 않음 (토큰 부족 상황이 바로 이 skill의 존재 이유)

---

## 복구는 하지 않음
이 skill은 저장 전용. 복구는 `state_session` skill의 RESTORE 액션이 담당.
세션 시작 시 CLAUDE.md의 Resume 절차가 알아서 호출.
