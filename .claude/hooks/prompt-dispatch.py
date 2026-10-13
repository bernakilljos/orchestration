#!/usr/bin/env python
"""UserPromptSubmit ?⑥씪 ?붿뒪?⑥쿂 ????13媛쒕? python ?꾨줈?몄뒪 1媛쒕줈.

諛곌꼍: ??PC ???꾨줈?몄뒪 湲곕룞 1?뚯뿉 ~0.5珥?(蹂댁븞 ?먯씠?꾪듃) ??bash ??13媛쒓? ?꾨＼?꾪듃???섏떗 媛??꾨줈?몄뒪瑜??꾩썙 5~6珥덇? 嫄몃졇?? 媛??낆쓽 濡쒖쭅? 洹몃?濡??먭퀬 紐⑤뱢濡???꺼 in-process ?ㅽ뻾?쒕떎.

援ъ“: .claude/hooks/prompt/<?낆씠由??몃뜑?ㅼ퐫??.py 媛 ??1媛쒖뵫 (run(ctx) -> str | dict | None).
      ???뚯씪? ?꾨옒 HOOKS ?쒖꽌(settings.json ?쒖꽌)?濡?import 쨌 ?ㅽ뻾?섍퀬 寃곌낵瑜??⑹튂湲곕쭔 ?쒕떎.
      紐⑤뱢 ?섎굹媛 二쎄굅???먮젮???섎㉧吏??怨꾩냽 (try/except + ?ㅻ젅????꾩븘??.

異쒕젰: additionalContext = 媛????띿뒪?몃? ?먮옒 ?쒖꽌濡?"\\n\\n" ?곌껐??JSON 1媛?(??留??놁쑝硫?臾댁텧??.
?듭뀡: --debug-per-hook  ?낅퀎 ?띿뒪??dict 瑜?JSON ?쇰줈 異쒕젰 (?뚯뒪?몄슜 쨌 濡쒓렇 ???④?)
      --rag-worker      (?대??? RAG 罹먯떆 媛깆떊 detached ?뚯빱
?섍꼍: PROMPT_DISPATCH_NO_SPAWN=1  RAG detached ?뚯빱瑜??꾩슦吏 ?딆쓬 (?뚯뒪?몄슜)
濡쒓렇: .claude/logs/prompt-dispatch.log (?낅퀎 ms 쨌 ?먮윭)
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

# (???대쫫 = ?먮낯 .sh ?뚯씪紐? 紐⑤뱢紐? ??.claude/settings.json UserPromptSubmit ?쒖꽌
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
    ("suggest-command-from-context", "suggest_command_from_context"),
]

HOOK_TIMEOUT_SEC = 6.0  # ??1媛??곹븳 (?먮낯 settings timeout 10~15珥??덉そ)
TOTAL_BUDGET_SEC = 12.0  # ?꾩껜 ?곹븳 ???섏쑝硫??⑥? ?낆? 嫄대꼫?대떎
LOG_MAX_BYTES = 1_000_000


def _run_one(ctx, name: str, modname: str, box: dict) -> None:
    try:
        import importlib

        mod = importlib.import_module(modname)
        box["out"] = mod.run(ctx)
    except BaseException as e:  # noqa: BLE001 ????紐⑤뱢???ㅽ뙣媛 ?ㅻⅨ ?낆뿉 踰덉?吏 ?딄쾶
        box["err"] = f"{type(e).__name__}: {e}"
        box["tb"] = traceback.format_exc(limit=3).strip().splitlines()[-1]


def _split(out):
    """??諛섑솚媛?-> (additionalContext ?띿뒪?? ?섎㉧吏 ?꾨뱶 dict)."""
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
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        pass


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
            problems.append(f"SKIP {name}: ?꾩껜 ?곹븳 {TOTAL_BUDGET_SEC:.0f}s 珥덇낵")
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
            problems.append(f"TIMEOUT {name}: {HOOK_TIMEOUT_SEC:.0f}s 珥덇낵 (寃곌낵 踰꾨┝)")
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

    # ??꾩븘?껋쑝濡??⑥? daemon ?ㅻ젅?쒓? ?덉뼱??利됱떆 醫낅즺
    if any(t.is_alive() for t in threading.enumerate() if t is not threading.current_thread()):
        sys.stdout.flush()
        os._exit(0)
    return 0


if __name__ == "__main__":
    # ?섏쐞 ?꾨줈?몄뒪 ?놁씠 ?뺤긽 醫낅즺 ??吏????媛?? plugins ?녿뒗 ?꾨줈?앺듃??媛??낆씠 ?먯껜 媛?쒕줈 skip
    sys.exit(main(sys.argv[1:]))

