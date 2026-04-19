# exec_orca-auto — Orca Auto Worker 관리 (로컬 + 글로벌)

> **분류:** `exec_` (실행 계열)
> **레거시 커맨드:** `/orcauto-stop` (orcauto-start는 삭제됨 — 이 skill로 직접 실행)

## 목적
codex / gemini 워커의 로컬 큐 + **전역 큐** 관리.
- **로컬 모드:** 프로젝트 단위 큐 (`.claude/tasks/`). 단일 프로젝트 작업용. 기존 동작.
- **글로벌 모드 (신규):** 전역 큐 (`~/.claude/orca/tasks/`). 여러 프로젝트가 워커 풀을 공유. `/exec_orch` 가 기본으로 사용.

세션 시작 시 CLAUDE.md Step 1에서 자동 호출.

---

## 상태 파일

### 로컬 (프로젝트 단위, 기존)

| 파일 | 의미 |
|------|------|
| `.claude/orca-enabled`   | 자동 시작 활성화 |
| `.claude/orca-stopped`   | 비활성화 |
| `.claude/orca-heartbeat` | 마지막 Claude 활동 |
| `.claude/orca-workers-config.json` | 프로젝트 워커 수 (로컬 모드용) |

### 글로벌 (사용자 단위, 신규)

| 파일 | 의미 |
|------|------|
| `~/.claude/orca/tasks/task-*.md`       | 대기 태스크 (frontmatter에 project_root) |
| `~/.claude/orca/locks/{taskid}.lock`   | 워커 락 |
| `~/.claude/orca/done/`                 | 완료 태스크 |
| `~/.claude/orca/workers/*.hb`          | 워커 하트비트 (2분 미갱신 = 죽음) |
| `~/.claude/orca/workers-config.json`   | 전역 워커 상한 (`max_workers.codex` 등) |
| `~/.claude/orca/heartbeat`             | 모든 프로젝트가 공유하는 Claude 활동 시각 |
| `~/.claude/orca/stop`                  | 존재 시 모든 전역 워커 즉시 종료 |

---

## 액션: START (로컬 + 글로벌 동시)

```
전제 조건:
  - .claude/orca-enabled 존재 OR /orcauto-start 호출
  - .claude/orca-stopped 없음

실행 순서:
1. orca-stopped 삭제, orca-enabled 생성, orca-heartbeat 갱신
2. ~/.claude/orca/heartbeat 갱신 (글로벌 하트비트)
3. 로컬 워커 기동 (기존 동작):
     where codex-auto → 있으면 codex-auto [N] 실행 (프로젝트별 task-*.md 처리용)
     where gemini-auto → 있으면 gemini-auto [N] 실행
4. 글로벌 워커 기동 (신규):
     where codex-auto-global → codex-auto-global (인자 없이 = 상한까지 채움)
     where gemini-auto-global → gemini-auto-global
   * 이미 상한에 도달했으면 spawn 스킵 (exit 0)
5. 결과 표:
   | 스코프   | 에이전트    | 상태  | Alive/Max |
   |---------|------------|-------|-----------|
   | local   | codex-auto  | ...   | 4         |
   | global  | codex       | 2/4   | ...       |
```

## 액션: STOP

```
1. .claude/orca-stopped 생성, orca-enabled 삭제
2. 로컬 워커 윈도우 종료 (MainWindowTitle 매칭)
3. 글로벌 중단:
     touch ~/.claude/orca/stop   (5분 내 모든 글로벌 워커 자가 종료)
   * 영구 중단이면 ~/.claude/orca/stop 을 남겨둠
   * 재시작이면 START 액션이 이를 삭제
```

## 액션: STATUS

```
로컬:
  where codex-auto, where gemini-auto
  .claude/orca-enabled, .claude/orca-stopped, .claude/orca-heartbeat
  .claude/orca-workers-config.json 값

글로벌:
  cat ~/.claude/orca/workers-config.json
  ls ~/.claude/orca/workers/*.hb | filter (2분 내 갱신) → alive 수
  ls ~/.claude/orca/tasks/*.md | wc -l → 대기 태스크 수
  ls ~/.claude/orca/locks/*.lock | wc -l → 처리 중 태스크 수
```

---

## 로컬 vs 글로벌 언제 쓰나

- **로컬**: 단일 프로젝트에서 `.claude/tasks/task-*.md` 편집 후 codex-auto 직접 실행
- **글로벌**: `/exec_orch` 또는 `orca-dispatch <task> [agent]` — 여러 프로젝트가 워커 풀 공유

두 모드는 공존 가능. 글로벌 워커는 로컬 태스크를 건드리지 않음 (다른 큐).

## 자동 종료 규칙
- Claude 종료 후 5분 → 각 heartbeat 갱신 없음 → 워커 자가 종료
- 글로벌은 `~/.claude/orca/heartbeat`, 로컬은 `.claude/orca-heartbeat` 를 봄

## 워커 수 변경
- **로컬**: `.claude/orca-workers-config.json` 의 `workers.codex` 등
- **글로벌**: `~/.claude/orca/workers-config.json` 의 `max_workers.codex` 등
