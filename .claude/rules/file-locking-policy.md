# 파일 잠금 정책 (Writer = 1)

> **근거**: CLAUDE.md § 7-3 (`같은 파일 동시 수정 금지 (Writer=1)`).
> **이유**: 다중 워커 병렬 (codex ×4, haiku ×2) 환경에서 race condition 방지.

## 절대 룰

**한 파일 = 한 워커. 동시 쓰기 금지.** 잠금은 `.claude/tasks/locks/` 에 lock 파일.

## Lock 파일 구조

```text
.claude/tasks/locks/
├── <TASK-SLUG>.lock              # task 단위 lock
│   {
│     "task": "doc-auto-foo",
│     "worker": "codex-1",
│     "files": ["src/foo.py", "tests/test_foo.py"],
│     "started": "2026-05-31T12:34:56Z",
│     "pid": 12345
│   }
```

## 흐름 (hook-01-pre-task 자동)

```bash
# 1. task-instruction.md 의 § 3 files 추출
TARGET_FILES=$(grep -E "^- target: " .claude/tasks/task-<slug>.md | sed 's/^- target: //')

# 2. 다른 lock 의 files 와 교집합 검사
for tgt in $TARGET_FILES; do
  if grep -l "$tgt" .claude/tasks/locks/*.lock 2>/dev/null; then
    echo "❌ 파일 잠금 충돌: $tgt"
    exit 1
  fi
done

# 3. lock 파일 생성
cat > .claude/tasks/locks/<slug>.lock <<EOF
{
  "task": "<slug>",
  "worker": "$WORKER_ID",
  "files": [...],
  "started": "$(date -Iseconds)",
  "pid": $$
}
EOF
```

## 잠금 해제

- 정상 종료: task → `done/` 이동 시 자동 lock 삭제
- 비정상 종료 (kill·crash): watchdog 가 5분 마다 stale lock (pid 죽음) 정리

## Stale lock 정리 (`worker-health.sh`)

```bash
for lock in .claude/tasks/locks/*.lock; do
  pid=$(jq -r .pid "$lock")
  if ! kill -0 "$pid" 2>/dev/null; then
    rm "$lock"
    echo "[stale] $lock removed"
  fi
done
```

## 충돌 시 대응

| 상황 | 행동 |
|---|---|
| 같은 파일 lock 있음 | 새 task 거절 → 큐에 대기 (`.claude/tasks/pending/`) |
| 다른 워커 lock 죽었음 | watchdog 가 30초 내 정리 → 재시도 |
| 사용자가 강제 unlock | `rm .claude/tasks/locks/<slug>.lock` (위험) |

## 금지

1. **lock 없이 task 시작** — 충돌 방지 무력
2. **다른 워커 lock 강제 삭제** — 진행 중 작업 깨짐
3. **lock 안에 files 누락** — 다른 워커가 같은 파일 잡음
4. **lock 작성 후 즉시 commit** — 다른 worker 의 변경 덮어쓰기

## Git 동시성

- branch 단위 isolation (`auto/<slug>`) — main 직접 push X
- 동시 push 시 git rebase + retry (지수 backoff)

## 도구

- `.claude/scripts/route.py --status` — 현재 lock 목록
- `.claude/scripts/worker-health.sh` — stale lock 정리
- `.claude/scripts/watchdog-start.bat` — 5분 주기 health check

## 참조

- `CLAUDE.md § 7-3` (금지)
- `plugins/exec_orch/hooks/hook-01-pre-task.sh` (자동 충돌 검사)
- `.claude/scripts/lib/state_db.py` (lock 테이블)
- `.claude/rules/codex-rules.md` (codex task-instruction 의무)
- `.claude/rules/best-practices.md` § 멈춤 방지 (잠금 폴링 패턴)
