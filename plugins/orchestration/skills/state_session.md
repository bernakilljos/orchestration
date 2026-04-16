# state_session — 세션 상태 관리

> **분류:** `state_` (상태 저장/복구 계열)
> **통합 레거시:** `skill-09-memory-reset`, `check-agents` command
> **참조 plugin:** `.claude-plugin/plugin.json` → `entry_points.state_save`

## 목적
세션 스냅샷 저장·복구 + 에이전트 상태 조회를 단일 skill로 처리한다.
컨텍스트가 80%를 넘거나 파이프라인 단계가 완료될 때 자동 트리거된다.

---

## 액션: SNAPSHOT (현재 상태 저장)

**트리거:**
- 컨텍스트 80% 이상
- 파이프라인 단계 완료 (hook-01, codex-auto 완료, gemini-auto 완료 등)
- 사용자 요청 ("저장해줘", "스냅샷", "/reset")

**저장 경로:** `.claude/context-cache/session-snapshot.md`

```markdown
## Session Snapshot - [YYYY-MM-DD HH:MM]

### Current Task
- Title:  [task title]
- Goal:   [구현 목표]
- Status: [research | implementing | reviewing | deploying]

### Pipeline Steps
- [x] SKILL-01 research
- [ ] SKILL-02 implement    ← 현재 여기
- [ ] SKILL-03 review

### Next Command
codex-auto [N]

### Modified Files
- path/to/file1
- path/to/file2

### Key Decisions
- [결정 사항 1]
- [결정 사항 2]
```

---

## 액션: RESTORE (이전 세션 복구)

**트리거:** 세션 시작 시 `.claude/context-cache/session-snapshot.md` 존재 확인

```
1. 파일 존재 → 요약 출력:
   [Recovery] 이전 세션 스냅샷 발견
     Task:      [title]
     Status:    [status]
     Next:      [command]
   계속하시겠습니까? [Y/N]

2. Y → snapshot의 Next Command 실행
3. N → 스냅샷 보관, 새 작업 시작
4. 파일 없음 → 조용히 스킵
```

---

## 액션: STATUS (에이전트 + 워커 현황)

```
출력 형식:

| Agent       | 설치         | 프로세스  | 비고              |
|------------|-------------|---------|-----------------|
| codex-auto  | AVAILABLE   | N개 실행 중 | ...            |
| gemini-auto | AVAILABLE   | N개 실행 중 | ...            |
| claude-auto | NOT FOUND   | -       | 미설치            |

태스크 현황:
  pending:   .claude/tasks/task-*.md 파일 수
  locked:    .claude/tasks/locks/*.lock 파일 수
  completed: .claude/tasks/done/*.md 파일 수
  stop_flag: .claude/tasks/stop 파일 존재 여부

Orca 상태:
  heartbeat: [cat .claude/orca-heartbeat]
  workers:   [cat .claude/orca-workers] (없으면 "1 (default)")
  enabled:   [orca-enabled 존재 여부]
```

---

## 체크포인트 자동 저장 시점

| 완료 시점 | 저장 내용 |
|---------|---------|
| hook-01 pre-task | 태스크 등록, 잠긴 파일 목록 |
| SKILL-01 research | 분석 결과, 위험 요소 |
| codex-auto 완료 | 구현 파일 목록, next=gemini-auto |
| gemini-auto 완료 | 리뷰 결과, Claude 채택 결정 대기 |
| hook-04 pre-deploy | 배포 전 상태 |
