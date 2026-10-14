"""plugins/exec_orch/hooks/hook-01-pre-task.sh 이식 — current-tasks.json 보장 + locked_files 충돌 + 12기법 누락 경고.

stdout 은 모두 평문 ("[HOOK-01] ..."). 충돌(jq 있을 때만) 은 exit 1 (비차단).
"""
from __future__ import annotations

import json
import os
import re
import shutil

from _common import Result, read_text


def _find_root(ctx) -> str:
    cpd = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if cpd and os.path.isdir(cpd):
        return cpd
    d = os.getcwd()
    for _ in range(12):
        if os.path.isdir(os.path.join(d, ".git")) or (
                os.path.isdir(os.path.join(d, ".claude")) and os.path.isdir(os.path.join(d, "plugins"))):
            return d
        p = os.path.dirname(d)
        if p == d:
            break
        d = p
    return os.getcwd()


def run(ctx):
    out = ""
    project = _find_root(ctx)
    tasks_dir = os.path.join(project, ".claude", "tasks")
    current = os.path.join(tasks_dir, "current-tasks.json")
    os.makedirs(tasks_dir, exist_ok=True)
    if not os.path.isfile(current):
        with open(current, "wb") as f:
            f.write(b'{"tasks":[]}\n')
        out += "[HOOK-01] current-tasks.json 생성\n"

    task_instr = os.path.join(tasks_dir, "task-instruction.md")
    if os.path.isfile(task_instr):
        text = read_text(task_instr)
        lines = text.split("\n")
        targets = [ln[len("- target: "):] for ln in lines if ln.startswith("- target: ")]
        if targets and shutil.which("jq"):
            locked = set()
            try:
                d = json.loads(read_text(current))
                for t in (d.get("tasks") or []):
                    for x in (t.get("locked_files") or []):
                        locked.add(str(x))
            except Exception:
                pass
            for tgt in targets:
                if not tgt:
                    continue
                if tgt in locked:
                    out += "[HOOK-01] [X] 파일 잠금 충돌: %s\n" % tgt
                    return Result(1, out, "")
        missing = ""

        def has(pat):
            return any(re.search(pat, ln) for ln in lines)

        if not has(r"^## 1\) Role|^## Role"):
            missing += " role"
        if not has(r"^## .*Negative|DO NOT:"):
            missing += " negative"
        if not has(r"^## .*Context|Project root:"):
            missing += " context"
        if not has(r"Acceptance|Few-shot|INPUT:.*OUTPUT:"):
            missing += " few-shot"
        if missing:
            out += "[HOOK-01] [WARN] task-instruction.md 12 기법 누락:%s\n" % missing
            out += "[HOOK-01]   -> plugins/exec_orch/codex/task-instruction-template.md 참고\n"
            out += "[HOOK-01]   -> skill: plugins/exec_orch/skills/prompt-techniques.md\n"
    out += "[HOOK-01] OK\n"
    return Result(0, out, "")
