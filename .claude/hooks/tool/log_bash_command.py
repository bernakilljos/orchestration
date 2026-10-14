"""log_bash_command.py 이식 — Bash 명령을 .claude/logs/bash_commands.log 에 append.

stdin 은 원본과 같은 방식(시스템 기본 인코딩) 으로 읽는다 - 명령에 한글이 있으면 원본은 로그 파일만 만들고 쓰기에 실패한다
(_common.py 의 PY_STDIN_FIX 설명 참고).
"""
from __future__ import annotations

import json
import os
from datetime import datetime

from _common import py_stdin_text


def run(ctx):
    try:
        payload = json.loads(py_stdin_text(ctx))
    except Exception:
        return None
    try:
        ti = payload.get("tool_input", {}) or {}
        cmd = ti.get("command") or ""
        desc = ti.get("description") or ""
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        log_dir = os.path.join(project_dir, ".claude", "logs")
        os.makedirs(log_dir, exist_ok=True)
        path = os.path.join(log_dir, "bash_commands.log")
        ts = datetime.now().isoformat(timespec="seconds")
        with open(path, "a", encoding="utf-8") as f:  # 텍스트 모드 - 원본과 같은 개행 변환
            f.write(f"{ts}\t{cmd}\t{desc}\n")
    except Exception:
        pass  # noqa: BLE001
    return None
