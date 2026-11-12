"""log_bash_command.py 이식 — Bash 명령을 .claude/logs/bash_commands.log 에 append.

stdin 은 원본과 같은 방식(시스템 기본 인코딩) 으로 읽는다 - 명령에 한글이 있으면 원본은 로그 파일만 만들고 쓰기에 실패한다
(_common.py 의 PY_STDIN_FIX 설명 참고).
"""
from __future__ import annotations

import json
import os
from datetime import datetime

from _common import py_stdin_text

try:  # 2026-11-10: 명령·설명 기록 전 비밀정보 가림 (정본 scripts/lib/redact · §64 · sys.path 오염 없이 파일로 로드)
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("redact_tool", os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts", "lib", "redact.py"))
    _sm = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_sm)
    _mask = _sm.mask
except Exception:  # noqa: BLE001 — 가림 모듈이 없으면 원문을 남기지 않는다
    def _mask(text):
        return "[MASKED]" if text else text


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
        line = f"{ts}\t{_mask(cmd)}\t{_mask(desc)}\n"
        # 2026-11-12 (R245): 해석 못 한 글자(surrogate)가 섞이면 utf-8 쓰기가 실패해 줄 전체가 조용히 빠졌다
        #   (IFRS 11-11 18:57~ 기록 0건) — 그 글자만 ? 로 바꿔 기록은 남긴다.
        line = line.encode("utf-8", "replace").decode("utf-8")
        with open(path, "a", encoding="utf-8") as f:  # 텍스트 모드 - 원본과 같은 개행 변환
            f.write(line)
    except Exception as e:  # noqa: BLE001 — 기록 실패를 숨기지 않는다 (계측 침묵 방지)
        try:
            project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
            with open(os.path.join(project_dir, ".claude", "logs", "log_bash_command.errors.log"), "a",
                      encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat(timespec='seconds')}\t{type(e).__name__}: {str(e)[:200]}\n")
        except Exception:  # noqa: BLE001
            pass
    return None
