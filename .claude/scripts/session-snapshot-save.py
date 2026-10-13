#!/usr/bin/env python3
"""세션 스냅샷 저장 — /clear 전에 또는 cycle 끝마다 자동 호출.

저장 내용:
- 현재 cycle 번호
- 미완료 task (pending 1~28)
- 마지막 5개 git commit
- 마지막 30min report 경로
- 핵심 결함 (logs 분석)
- 다음 action

위치: .claude/context-cache/session-snapshot.md
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / ".claude" / "context-cache"
CACHE.mkdir(parents=True, exist_ok=True)
SNAPSHOT = CACHE / "session-snapshot.md"


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, cwd=ROOT, encoding="utf-8", errors="replace", timeout=15)
    except Exception as e:
        return f"(error: {e})"


def main() -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    git_log = _run(["git", "log", "--oneline", "-10"])
    git_status = _run(["git", "status", "--short"])

    reports_dir = ROOT / ".claude" / "logs" / "30min-reports"
    last_reports = []
    if reports_dir.exists():
        files = sorted(reports_dir.glob("*.md"), reverse=True)[:3]
        last_reports = [f.name for f in files]

    pending_dir = ROOT / ".claude" / "pending"
    pending_items = []
    if pending_dir.exists():
        for f in sorted(pending_dir.glob("*.md"))[:30]:
            pending_items.append(f.name)

    # 직전 세션의 사용자 지시 — hook-trace.log 에서 실측 (하드코딩 금지)
    recent_prompts = "(기록 없음)"
    trace = ROOT / ".claude" / "logs" / "hook-trace.log"
    if trace.exists():
        lines = []
        try:
            for ln in trace.read_text(encoding="utf-8", errors="replace").splitlines()[-400:]:
                if "user-prompt-auto-planner" in ln and "|" in ln:
                    ts = ln.split("]")[0].lstrip("[") if "]" in ln else ""
                    txt = ln.split("|", 1)[1].strip()
                    if txt:
                        lines.append(f"- [{ts}] {txt[:160]}")
        except Exception:
            lines = []
        if lines:
            recent_prompts = chr(10).join(lines[-5:][::-1])

    queue_dir = ROOT / ".claude" / "tasks" / "queue"
    queue_count = len(list(queue_dir.glob("*.md"))) if queue_dir.exists() else 0

    done_dir = ROOT / ".claude" / "tasks" / "done"
    done_count = len(list(done_dir.glob("*.md"))) if done_dir.exists() else 0

    content = f"""# 세션 스냅샷 — {now}

자동 저장. SessionStart hook 이 이 파일 발견하면 systemMessage 로 로드.

## 현재 상태

- 작업 디렉토리: {ROOT}
- 저장 시각: {now}

## 미완료 task (pending)

{chr(10).join(f"- {p}" for p in pending_items) if pending_items else "- (pending 없음)"}

## Codex 큐 상태

- 큐 대기: {queue_count}
- 완료 (시도): {done_count}

## 최근 30min reports

{chr(10).join(f"- .claude/logs/30min-reports/{r}" for r in last_reports) if last_reports else "- (없음)"}

## 최근 git commits

```
{git_log.strip()}
```

## Working tree

```
{git_status.strip() if git_status.strip() else "(clean)"}
```

## 직전 세션의 사용자 지시 (최근 순)

{recent_prompts}

## 이어서 할 일

위 지시와 Working tree 의 미커밋 변경이 곧 진행 중이던 작업이다.
새로 시작하지 말고 여기서 이어갈 것. 하드코딩된 할 일 목록은 두지 않는다
(2026-09-08: 3개월 전 목록이 계속 주입되던 결함 교정).
핵심 룰은 MEMORY.md 인덱스가 세션 시작 시 별도로 주입한다.
"""
    SNAPSHOT.write_text(content, encoding="utf-8")
    print(f"[snapshot] saved {SNAPSHOT}")

    backup = CACHE / f"session-snapshot-{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    backup.write_text(content, encoding="utf-8")
    backups = sorted(CACHE.glob("session-snapshot-*.md"), reverse=True)
    for old in backups[7:]:
        old.unlink()


if __name__ == "__main__":
    main()
