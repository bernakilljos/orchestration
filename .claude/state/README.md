# .claude/state/ — 상태 파일 저장소

## 용도
신규 상태 파일 전용 디렉터리.
재시도 카운터, 워커 상태 스냅샷 등 runtime 상태를 저장한다.

## 기존 orca-* 파일 위치 (하위 호환 유지)

| 파일 | 위치 | 설명 |
|------|------|------|
| `orca-enabled`   | `.claude/` (루트) | 자동 시작 활성화 플래그 |
| `orca-stopped`   | `.claude/` (루트) | 자동 시작 비활성화 플래그 |
| `orca-heartbeat` | `.claude/` (루트) | 마지막 활동 시각 (워커 생존 신호) |
| `orca-workers`   | `.claude/` (루트) | 워커 수 설정 |

기존 경로를 참조하는 CLAUDE.md, commands, scripts가 많으므로 이동하지 않는다.

## 이 디렉터리에 저장하는 파일 (신규)

| 파일 | 설명 |
|------|------|
| `retry-count.json`    | 태스크별 재시도 횟수 추적 |
| `last-task-id.txt`    | 마지막 처리된 태스크 ID |
| `worker-status.json`  | 워커별 상태 스냅샷 |

## retry-count.json 스키마

```json
{
  "task-id": "TASK-001",
  "retries": 0,
  "max_retries": 3,
  "last_error": "",
  "updated_at": "2026-04-15T12:00:00"
}
```

## worker-status.json 스키마

```json
{
  "codex": { "pid": null, "status": "idle", "last_task": "", "updated_at": "" },
  "gemini": { "pid": null, "status": "idle", "last_task": "", "updated_at": "" }
}
```

## 마이그레이션 계획
향후 orca-* 파일도 이 디렉터리로 이동 예정.
이동 시 CLAUDE.md + command 파일의 경로 참조 일괄 업데이트 필요.
