#!/usr/bin/env python3
"""?몄뀡 ?ㅻ깄???????/clear ?꾩뿉 ?먮뒗 cycle ?앸쭏???먮룞 ?몄텧.

????댁슜:
- ?꾩옱 cycle 踰덊샇
- 誘몄셿猷?task (pending 1~28)
- 留덉?留?5媛?git commit
- 留덉?留?30min report 寃쎈줈
- ?듭떖 寃고븿 (logs 遺꾩꽍)
- ?ㅼ쓬 action

?꾩튂: .claude/context-cache/session-snapshot.md
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
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
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

    # 吏곸쟾 ?몄뀡???ъ슜??吏????hook-trace.log ?먯꽌 ?ㅼ륫 (?섎뱶肄붾뵫 湲덉?)
    recent_prompts = "(湲곕줉 ?놁쓬)"
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
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            lines = []
        if lines:
            recent_prompts = chr(10).join(lines[-5:][::-1])

    queue_dir = ROOT / ".claude" / "tasks" / "queue"
    queue_count = len(list(queue_dir.glob("*.md"))) if queue_dir.exists() else 0

    done_dir = ROOT / ".claude" / "tasks" / "done"
    done_count = len(list(done_dir.glob("*.md"))) if done_dir.exists() else 0

    content = f"""# ?몄뀡 ?ㅻ깄????{now}

?먮룞 ??? SessionStart hook ?????뚯씪 諛쒓껄?섎㈃ systemMessage 濡?濡쒕뱶.

## ?꾩옱 ?곹깭

- ?묒뾽 ?붾젆?좊━: {ROOT}
- ????쒓컖: {now}

## 誘몄셿猷?task (pending)

{chr(10).join(f"- {p}" for p in pending_items) if pending_items else "- (pending ?놁쓬)"}

## Codex ???곹깭

- ???湲? {queue_count}
- ?꾨즺 (?쒕룄): {done_count}

## 理쒓렐 30min reports

{chr(10).join(f"- .claude/logs/30min-reports/{r}" for r in last_reports) if last_reports else "- (?놁쓬)"}

## 理쒓렐 git commits

```
{git_log.strip()}
```

## Working tree

```
{git_status.strip() if git_status.strip() else "(clean)"}
```

## 吏곸쟾 ?몄뀡???ъ슜??吏??(理쒓렐 ??

{recent_prompts}

## ?댁뼱??????
??吏?쒖? Working tree ??誘몄빱諛?蹂寃쎌씠 怨?吏꾪뻾 以묒씠???묒뾽?대떎.
?덈줈 ?쒖옉?섏? 留먭퀬 ?ш린???댁뼱媛?寃? ?섎뱶肄붾뵫??????紐⑸줉? ?먯? ?딅뒗??(2026-09-08: 3媛쒖썡 ??紐⑸줉??怨꾩냽 二쇱엯?섎뜕 寃고븿 援먯젙).
?듭떖 猷곗? MEMORY.md ?몃뜳?ㅺ? ?몄뀡 ?쒖옉 ??蹂꾨룄濡?二쇱엯?쒕떎.
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

