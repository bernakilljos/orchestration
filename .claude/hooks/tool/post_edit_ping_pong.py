"""post-edit-ping-pong.sh 이식 - Edit/Write 후 같은 수정 반복(핑퐁) 기록 (anti-ping-pong.record · 기록 전용 · 비차단).

R357 (2026-11-23): 원본은 동기 훅으로 Edit 마다 bash 1개 + python 3개 (경로 추출 · 미리보기 추출 · record) 를 띄워
응답을 붙잡았다 (bash 안에서 python 1개 ≈ 105ms · conhost 동반). 같은 일을 이미 떠 있는 디스패처 안에서 한다.
- 경로 = tool_input.file_path 또는 path · 미리보기 = new_string 또는 content 앞 200자 (원본 print + $(…) 처럼 끝 개행 제거)
- 세션 = 환경 변수 CLAUDE_SESSION_ID (없으면 unknown) — 원본과 같은 값
- 원본 출력({"path","count"} JSON) 은 훅 결과로 쓰이지 않았다 → 아무것도 돌려주지 않는다 · 실패는 원본처럼 로그에만
"""
from __future__ import annotations

import importlib.util
import os
import time

from _common import project_guard, tool_input

_MOD = None


def _apm(project_dir: str):
    global _MOD
    if _MOD is None:
        path = os.path.join(project_dir, ".claude", "scripts", "anti-ping-pong.py")
        if not os.path.isfile(path):
            return None
        spec = importlib.util.spec_from_file_location("anti_ping_pong", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _MOD = mod
    return _MOD


def run(ctx):
    if not project_guard(ctx):
        return None
    ti = tool_input(ctx)
    fp = ti.get("file_path") or ti.get("path") or ""
    if not fp:
        return None
    diff = str(ti.get("new_string") or ti.get("content") or "")[:200].rstrip("\n")
    try:
        mod = _apm(ctx.project_dir)
        if mod is None:
            return None
        mod.record(str(fp), diff, None, os.environ.get("CLAUDE_SESSION_ID") or "unknown")
    except Exception as e:  # noqa: BLE001 - 원본: 2>>anti-ping-pong.log · || true
        try:
            with open(os.path.join(ctx.project_dir, ".claude", "logs", "anti-ping-pong.log"), "a", encoding="utf-8") as f:
                f.write("[%s] post_edit_ping_pong: %s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), type(e).__name__, e))
        except OSError:
            pass
    return None
