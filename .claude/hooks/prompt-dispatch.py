#!/usr/bin/env python
"""UserPromptSubmit 단일 디스패처 — 훅 13개를 python 프로세스 1개로.

배경: 이 PC 는 프로세스 기동 1회에 ~0.5초 (보안 에이전트) 라 bash 훅 13개가 프롬프트당
수십 개 프로세스를 띄워 5~6초가 걸렸다. 각 훅의 로직은 그대로 두고 모듈로 옮겨 in-process 실행한다.

구조: .claude/hooks/prompt/<훅이름_언더스코어>.py 가 훅 1개씩 (run(ctx) -> str | dict | None).
      이 파일은 아래 HOOKS 순서(settings.json 순서)대로 import · 실행하고 결과를 합치기만 한다.
      모듈 하나가 죽거나 느려도 나머지는 계속 (try/except + 스레드 타임아웃).

출력: additionalContext = 각 훅 텍스트를 원래 순서로 "\\n\\n" 연결한 JSON 1개 (할 말 없으면 무출력).
옵션: --debug-per-hook  훅별 텍스트 dict 를 JSON 으로 출력 (테스트용 · 로그 안 남김)
      --rag-worker      (내부용) RAG 캐시 갱신 detached 워커
환경: PROMPT_DISPATCH_NO_SPAWN=1  RAG detached 워커를 띄우지 않음 (테스트용)
로그: .claude/logs/prompt-dispatch.log (훅별 ms · 에러)
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import traceback
import warnings

warnings.simplefilter("ignore")

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))
sys.path.insert(0, os.path.join(HOOKS_DIR, "prompt"))

# (훅 이름 = 원본 .sh 파일명, 모듈명) — .claude/settings.json UserPromptSubmit 순서
HOOKS = [
    ("user-prompt-auto-planner", "user_prompt_auto_planner"),
    ("detect-repeat-request", "detect_repeat_request"),
    ("detect-user-emotion", "detect_user_emotion"),
    ("detect-efficiency", "detect_efficiency"),
    ("detect-deflection", "detect_deflection"),
    ("periodic-rules-reminder", "periodic_rules_reminder"),
    ("save-user-prompt", "save_user_prompt"),
    ("lookup-history", "lookup_history"),
    ("inject-compact-reminder", "inject_compact_reminder"),
    ("websearch-trigger-detect", "websearch_trigger_detect"),
    ("suggest-skills", "suggest_skills"),
    ("aggregate-rule-adherence", "aggregate_rule_adherence"),
    ("recurrence-tracker", "recurrence_tracker"),
    ("suggest-command-from-context", "suggest_command_from_context"),
    ("auto-explore-on-task", "auto_explore_on_task"),  # 2026-10-13 신설 (713c91f) 이식
    ("surface-log-errors", "surface_log_errors"),  # 2026-10-16 상태줄 오류·경고를 세션이 먼저 처리
    ("usage-offload-notice", "usage_offload_notice"),  # 2026-10-17 세션·주간 90%+ codex · 95%+ gemini 위임
    ("inject-experience", "inject_experience"),  # 2026-10-19 A1 관련 검증 경험 top 3 자동 주입
]

HOOK_TIMEOUT_SEC = 6.0  # 훅 1개 상한 (원본 settings timeout 10~15초 안쪽)
TOTAL_BUDGET_SEC = 12.0  # 전체 상한 — 넘으면 남은 훅은 건너뛴다
LOG_MAX_BYTES = 1_000_000


def _run_one(ctx, name: str, modname: str, box: dict) -> None:
    try:
        import importlib

        mod = importlib.import_module(modname)
        box["out"] = mod.run(ctx)
    except BaseException as e:  # noqa: BLE001 — 한 모듈의 실패가 다른 훅에 번지지 않게
        box["err"] = f"{type(e).__name__}: {e}"
        box["tb"] = traceback.format_exc(limit=3).strip().splitlines()[-1]


def _split(out):
    """훅 반환값 -> (additionalContext 텍스트, 나머지 필드 dict)."""
    if out is None:
        return "", {}
    if isinstance(out, dict):
        rest = {k: v for k, v in out.items() if k != "additionalContext"}
        return str(out.get("additionalContext") or ""), rest
    return str(out), {}


def _write_log(line_list):
    try:
        path = os.path.join(ROOT, ".claude", "logs", "prompt-dispatch.log")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path) and os.path.getsize(path) > LOG_MAX_BYTES:
            with open(path, "rb") as f:
                keep = f.read().splitlines()[-3000:]
            with open(path, "wb") as f:
                f.write(b"\n".join(keep) + b"\n")
        with open(path, "ab") as f:
            f.write(("\n".join(line_list) + "\n").encode("utf-8", "replace"))
    except Exception:
        pass  # noqa: BLE001


def main(argv) -> int:
    if "--rag-worker" in argv:
        from user_prompt_auto_planner import rag_worker

        rag_worker()
        return 0

    debug = "--debug-per-hook" in argv
    t_start = time.perf_counter()

    from _common import Ctx, ts_iso_tz

    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    ctx = Ctx(raw)
    ctx.debug = debug

    results: dict[str, object] = {}
    timings: list[tuple[str, float]] = []
    problems: list[str] = []
    for name, modname in HOOKS:
        if time.perf_counter() - t_start > TOTAL_BUDGET_SEC:
            problems.append(f"SKIP {name}: 전체 상한 {TOTAL_BUDGET_SEC:.0f}s 초과")
            results[name] = None
            continue
        ctx.start_hook(name)
        box: dict = {}
        t0 = time.perf_counter()
        th = threading.Thread(target=_run_one, args=(ctx, name, modname, box), daemon=True)
        th.start()
        th.join(HOOK_TIMEOUT_SEC)
        ms = (time.perf_counter() - t0) * 1000
        timings.append((name, ms))
        if th.is_alive():
            problems.append(f"TIMEOUT {name}: {HOOK_TIMEOUT_SEC:.0f}s 초과 (결과 버림)")
            results[name] = None
        elif "err" in box:
            problems.append(f"ERROR {name}: {box['err']}")
            results[name] = None
        else:
            results[name] = box.get("out")

    texts: dict[str, str] = {}
    extras: dict[str, list] = {}
    for name, _m in HOOKS:
        t, rest = _split(results.get(name))
        texts[name] = t
        for k, v in rest.items():
            extras.setdefault(k, []).append(v)

    out_bytes = b""
    if debug:
        out_bytes = json.dumps(texts, ensure_ascii=False).encode("utf-8")
    else:
        pieces = [t.strip("\r\n") for t in texts.values()]
        joined = "\n\n".join(p for p in pieces if p)
        obj: dict = {}
        for k, vs in extras.items():
            obj[k] = "\n\n".join(str(v) for v in vs) if k == "systemMessage" else vs[-1]
        if joined:
            obj["hookSpecificOutput"] = {"hookEventName": "UserPromptSubmit", "additionalContext": joined}
        if obj:
            out_bytes = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    if out_bytes:
        sys.stdout.buffer.write(out_bytes)
        sys.stdout.buffer.flush()

    if not debug:
        total = (time.perf_counter() - t_start) * 1000
        parts = " ".join(f"{n}={ms:.0f}" for n, ms in timings)
        marks = " ".join(
            f"{h}.{lb}={v:.0f}" for h, ms_list in ctx.marks.items() for lb, v in ms_list
        )
        lines = [f"[{ts_iso_tz()}] total={total:.0f}ms {parts}" + (f" | {marks}" if marks else "")]
        lines += [f"[{ts_iso_tz()}]   {p}" for p in problems]
        _write_log(lines)

    # 타임아웃으로 남은 daemon 스레드가 있어도 즉시 종료
    if any(t.is_alive() for t in threading.enumerate() if t is not threading.current_thread()):
        sys.stdout.flush()
        os._exit(0)
    return 0


if __name__ == "__main__":
    # 하위 프로세스 없이 정상 종료 — 지시 외 가드: plugins 없는 프로젝트는 각 훅이 자체 가드로 skip
    sys.exit(main(sys.argv[1:]))
