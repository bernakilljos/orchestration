"""scope-lock PreToolUse 모듈 — Edit/Write 대상이 요청 범위 밖이면 WARN (opt-in).

활성화는 `/scope activate <glob>` 또는 `python .claude/scripts/scope-lock.py activate <glob>`.
비활성 상태 (기본) 는 즉시 통과 (오버헤드 거의 0).
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

from _common import Result, bash_cat, grep_key_value_a

# scripts/ 를 sys.path 에 추가 (scope-lock.py 임포트)
_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
_SCRIPTS = _ROOT / ".claude" / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


def _check(file_path: str):
    """Dynamic import to avoid stale state."""
    import importlib
    spec = importlib.util.spec_from_file_location("_scope_lock_cli", _SCRIPTS / "scope-lock.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check(file_path)


def run(ctx):
    inp = bash_cat(ctx.raw)
    fp = grep_key_value_a(inp, "file_path")
    if not fp:
        return None
    # 상태 파일 없으면 즉시 통과 (오버헤드 최소)
    state_file = _ROOT / ".claude" / "state" / "scope-lock.json"
    if not state_file.exists():
        return None
    try:
        allowed, cfg = _check(fp)
    except Exception:
        return None
    if allowed:
        return None
    mode = (cfg or {}).get("mode", "warn")
    paths = (cfg or {}).get("paths", [])
    msg = (
        f"[scope-lock] 범위 외 수정 — target={fp}\\n"
        f"현재 범위: {paths} (mode={mode})\\n"
        "범위 조정: /scope activate <glob> · 해제: /scope deactivate"
    )
    if mode == "deny":
        # exit 2 로 차단
        return Result(2, "", f"[scope-lock] blocked out-of-scope edit: {fp}")
    # warn — systemMessage
    out = ('{"systemMessage": "%s"}\n') % msg.replace('"', '\\"')
    return Result(0, out, "")
