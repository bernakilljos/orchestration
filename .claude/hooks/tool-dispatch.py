#!/usr/bin/env python
"""PreToolUse / PostToolUse 단일 디스패처 - 도구 호출 1회당 동기 bash 훅 N개를 python 프로세스 1개로.

배경: 이 PC 는 프로세스 기동 1회에 ~0.5초 (보안 에이전트) 라 Bash 호출 1회에 동기 훅 13개(6~7초),
      Edit/Write 1회에 23개(8~12초) 가 걸렸다. UserPromptSubmit 에 적용한 prompt-dispatch.py 와 같은 방식으로
      각 훅의 로직은 그대로 두고 모듈로 옮겨 in-process 로 실행한다.

사용: python tool-dispatch.py pre|post [--debug-per-hook]   (stdin = Claude Code 훅 페이로드 JSON)

구조: .claude/hooks/tool/<훅이름_언더스코어>.py 가 훅 1개씩 (run(ctx) -> Result | Spawn | None).
      공용 도구는 .claude/hooks/prompt/_common.py 하나만 쓴다 (prompt-dispatch.py 와 공유).
      이 파일은 아래 표(settings.json 순서) 에서 (event, tool matcher) 가 맞는 훅만 골라 순서대로 실행하고 결과를 합친다.
      Spawn = 드물게만 타는 무거운 경로(git 커밋 · 외부 도구) - 원본 .sh 를 그대로 병렬 실행해 수거한다.

합치기 규칙 (Claude Code 가 훅 여러 개의 결과를 합치던 것과 같은 의미):
  - exit 2 (차단): 해당 훅의 stderr 그대로. 여러 개면 설정 순서대로 이어 붙임. 디스패처도 exit 2.
  - exit 0 + stdout JSON: systemMessage 는 줄바꿈으로 연결 · permissionDecision 은 deny > ask > allow ·
    additionalContext 는 빈 줄로 연결 · continue 는 하나라도 false 면 false · decision/reason 은 연결.
  - exit 0 + 평문 stdout: 다른 훅의 JSON 과 한 스트림에 섞을 수 없어 JSON 이 있으면 로그로만 남김 (평문은 원래도 transcript 전용).
  - exit 1 등 비차단: stdout 무시 · stderr 만 전달. 디스패처 exit 0.
옵션: --debug-per-hook  훅별 {rc,out,err} 를 JSON 으로 출력 (테스트용 · 로그 안 남김)
로그: .claude/logs/tool-dispatch.log (훅별 ms · 에러)
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import threading
import time
import traceback
import warnings

warnings.simplefilter("ignore")

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HOOKS_DIR))
TOOL_DIR = os.path.join(HOOKS_DIR, "tool")
sys.path.insert(0, os.path.join(HOOKS_DIR, "prompt"))

# (훅 이름 = 원본 스크립트 파일명, 모듈명, 도구 matcher, 원본 settings timeout 초, action)
# 순서 = .claude/settings.json 의 PreToolUse / PostToolUse 동기 훅 순서 (async 훅은 이 표에 없다 - settings 에 그대로 둔다)
PRE = [
    ("detect-asset-creation", "detect_asset_creation", "Edit|Write", 3, None),
    ("protect-critical-files", "protect_critical_files", "Edit|Write", 60, None),
    ("block-version-suffix", "block_version_suffix", "Edit|Write", 3, None),
    ("check-mojibake", "check_mojibake", "Edit|Write", 3, None),
    ("block-tricks", "block_tricks", "Edit|Write", 3, None),
    ("hook-01-pre-task", "hook_01_pre_task", "Edit|Write", 3, None),
    ("check-claude-md-size", "check_claude_md_size", "Edit|Write", 3, None),
    ("check-hardcoded-paths", "check_hardcoded_paths", "Edit|Write", 3, None),
    ("block-korean-removal", "block_korean_removal", "Edit|Write", 3, None),
    ("prevent-emoji-in-code", "prevent_emoji_in_code", "Edit|Write", 3, None),
    ("prevent-version-suffix", "prevent_version_suffix", "Edit|Write", 3, None),
    ("block-visible-windows", "block_visible_windows", "Bash", 60, None),
    ("block-file-deletion", "block_file_deletion", "Bash", 3, None),
    ("block_dangerous_bash", "block_dangerous_bash", "Bash", 3, None),
    ("log_bash_command", "log_bash_command", "Bash", 3, None),
    ("pre-build-reminder", "pre_build_reminder", "Bash", 3, None),
    ("secret-scan", "secret_scan", "Bash", 3, None),
    ("pre-commit-secrets", "pre_commit_secrets", "Bash", 30, None),
    ("approval-gate-detect", "approval_gate_detect", "Bash", 5, None),
    ("pre-commit-full-check", "pre_commit_full_check", "Bash", 5, None),
    ("pre-commit-infra-check", "pre_commit_infra_check", "Bash", 5, None),
    ("track-agent-dispatch", "track_agent_dispatch", "Agent", 5, "start"),
]
POST = [
    ("check-korean-only", "check_korean_only", "Edit|Write", 60, None),
    ("detect-demo-pattern", "detect_demo_pattern", "Edit|Write", 3, None),
    ("post_write_pycheck", "post_write_pycheck", "Edit|Write", 30, None),
    ("markdown_formatter", "markdown_formatter", "Edit|Write", 5, None),
    ("check-indentation", "check_indentation", "Edit|Write", 3, None),
    ("prevent-whitespace-png", "prevent_whitespace_png", "Edit|Write", 5, None),
    ("check-js-syntax", "check_js_syntax", "Edit|Write", 5, None),
    ("check-html-balance", "check_html_balance", "Edit|Write", 5, None),
    ("enforce-file-naming", "enforce_file_naming", "Edit|Write", 60, None),
    ("hook-09-ocr-verify", "hook_09_ocr_verify", "Bash", 60, None),
    ("orca-heartbeat", "heartbeat", ".*", 60, None),
    ("periodic-snapshot", "periodic_snapshot", ".*", 5, None),
    ("propagate-rule-change", "propagate_rule_change", "Edit|Write", 60, None),
    ("track-agent-dispatch", "track_agent_dispatch", "Agent", 5, "end"),
]
TABLE = {"pre": PRE, "post": POST}

TOTAL_BUDGET_SEC = 55.0  # 전체 상한 - 넘으면 남은 훅은 건너뛴다
SPAWN_MIN_SEC = float(os.environ.get("TOOL_DISPATCH_SPAWN_MIN_SEC") or 0.0)  # 테스트 부하용 하한 (기본 0 = 원본 settings timeout 그대로)
CREATE_NO_WINDOW = 0x08000000


def _load_module(modname: str):
    spec = importlib.util.spec_from_file_location("tool_" + modname, os.path.join(TOOL_DIR, modname + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _run_one(ctx, modname: str, action, box: dict) -> None:
    try:
        mod = _load_module(modname)
        box["out"] = mod.run_action(ctx, action) if action else mod.run(ctx)
    except BaseException as e:  # noqa: BLE001 - 한 모듈의 실패가 다른 훅에 번지지 않게
        box["err"] = f"{type(e).__name__}: {e}"
        box["tb"] = traceback.format_exc(limit=3).strip().splitlines()[-1]


def _spawn_start(sp, raw_bytes: bytes) -> dict:
    """원본 .sh 를 settings 와 같은 방식(bash <경로> <인자>) 으로 띄운다. 입출력은 별도 스레드가 수거."""
    import subprocess

    path = ROOT + "/" + sp.rel
    kw = {}
    if os.name == "nt":
        kw["creationflags"] = CREATE_NO_WINDOW
    box: dict = {"t0": time.perf_counter()}
    try:
        proc = subprocess.Popen(["bash", path] + list(sp.args), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, **kw)
    except Exception as e:  # noqa: BLE001
        box["err"] = f"SPAWN-FAIL: {type(e).__name__}: {e}"
        return box
    box["proc"] = proc

    def _comm():
        try:
            o, e = proc.communicate(raw_bytes)
            box["res"] = (proc.returncode, o, e)
        except BaseException as ex:  # noqa: BLE001
            box["err"] = f"COMM-FAIL: {type(ex).__name__}: {ex}"

    th = threading.Thread(target=_comm, daemon=True)
    th.start()
    box["th"] = th
    return box


def _kill_tree(proc) -> None:
    """시간 초과한 위임 훅을 자식까지 함께 종료한다 (Windows 에선 bash 만 죽고 python 이 좀비로 남는 것을 막는다)."""
    import subprocess

    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True,
                           creationflags=CREATE_NO_WINDOW, timeout=10)
        else:
            proc.kill()
    except Exception:  # noqa: BLE001
        try:
            proc.kill()
        except Exception:  # noqa: BLE001
            pass


def _spawn_collect(box: dict, timeout: float):
    from _common import Result

    th = box.get("th")
    if th is None:
        return None, box.get("err", "SPAWN-FAIL")
    th.join(max(0.1, timeout))
    if th.is_alive():
        _kill_tree(box["proc"])
        return None, "TIMEOUT (spawn 결과 버림)"
    res = box.get("res")
    if res is None:
        return None, box.get("err", "NO-RESULT")
    rc, o, e = res
    return Result(rc, o.decode("utf-8", "replace").replace("\r\n", "\n"),
                  e.decode("utf-8", "replace").replace("\r\n", "\n")), None


def _enc(text: str) -> bytes:
    """출력 직렬화 - 원본이 내보낸 (utf-8 이 아닌 바이트를 포함한) 텍스트를 surrogateescape 로 그대로 되돌린다."""
    try:
        return text.encode("utf-8", "surrogateescape")
    except UnicodeEncodeError:
        return text.encode("utf-8", "replace")


def _as_json(text: str):
    s = text.strip()
    if not s.startswith("{"):
        return None
    try:
        d = json.loads(s)
    except Exception:  # noqa: BLE001
        return None
    return d if isinstance(d, dict) else None


_RANK = {"deny": 3, "ask": 2, "defer": 1, "allow": 0}


def _merge(results):
    """[(name, Result)] -> (exit code, stdout 텍스트, stderr 텍스트, 로그용 평문 목록)."""
    blockers, errs, jsons, plain = [], [], [], []
    for _name, r in results:
        if r is None:
            continue
        if r.rc == 2:
            blockers.append(r.err)
        elif r.rc == 0:
            if r.out.strip():
                j = _as_json(r.out)
                if j is None:
                    plain.append(r.out)
                else:
                    jsons.append(j)
            if r.err:
                errs.append(r.err)
        else:
            if r.err:
                errs.append(r.err)

    merged: dict = {}
    sys_msgs, ctxs, reasons_decision, hso = [], [], [], {}
    decisions = []  # (permissionDecision, reason)
    cont = None
    blk_reasons = []
    for j in jsons:
        for k, v in j.items():
            if k == "systemMessage":
                if v:
                    sys_msgs.append(str(v))
            elif k == "continue":
                cont = False if (cont is False or v is False) else bool(v)
            elif k == "decision":
                merged["decision"] = v
            elif k == "reason":
                if v:
                    blk_reasons.append(str(v))
            elif k == "hookSpecificOutput" and isinstance(v, dict):
                for hk, hv in v.items():
                    if hk == "additionalContext":
                        if hv:
                            ctxs.append(str(hv))
                    elif hk == "permissionDecision":
                        decisions.append((str(hv), str(v.get("permissionDecisionReason") or "")))
                    elif hk == "permissionDecisionReason":
                        pass
                    else:
                        hso[hk] = hv
            else:
                merged[k] = v
    if sys_msgs:
        merged["systemMessage"] = "\n".join(sys_msgs)
    if cont is not None:
        merged["continue"] = cont
    if blk_reasons:
        merged["reason"] = "\n".join(blk_reasons)
    final_dec = None
    if decisions:
        final_dec = max((d for d, _r in decisions), key=lambda d: _RANK.get(d, -1))
        hso["permissionDecision"] = final_dec
        rs = [r for d, r in decisions if d == final_dec and r]
        if rs:
            hso["permissionDecisionReason"] = "\n".join(rs)
    if ctxs:
        hso["additionalContext"] = "\n\n".join(ctxs)
    if hso:
        hso = dict(hso)
        merged["hookSpecificOutput"] = hso

    if blockers:
        parts = []
        for b in blockers:
            parts.append(b if (b == "" or b.endswith("\n")) else b + "\n")
        err = "".join(parts)
        if final_dec == "deny" and "permissionDecisionReason" in hso:
            err += hso["permissionDecisionReason"] + "\n"
        return 2, "", err, plain
    err = "".join(e if e.endswith("\n") else e + "\n" for e in errs)
    if merged:
        return 0, json.dumps(merged, ensure_ascii=False) + "\n", err, plain
    return 0, "".join(plain), err, []


def main(argv) -> int:
    if not argv or argv[0] not in TABLE:
        sys.stderr.write("usage: tool-dispatch.py pre|post [--debug-per-hook]\n")
        return 0
    event = argv[0]
    debug = "--debug-per-hook" in argv
    t_start = time.perf_counter()

    from _common import Ctx, Spawn, tool_name, ts_iso_tz, write_dispatch_log

    raw_bytes = sys.stdin.buffer.read()
    raw = raw_bytes.decode("utf-8", errors="replace")
    ctx = Ctx(raw)
    ctx.raw_bytes = raw_bytes
    ctx.debug = debug
    tname = tool_name(ctx)

    entries = [h for h in TABLE[event] if re.fullmatch(h[2], tname)]
    results: list = []  # [(name, Result|None)]
    timings: list = []
    problems: list = []
    spawns: list = []  # (index, name, box, timeout)

    for name, modname, _matcher, tmo, action in entries:
        if time.perf_counter() - t_start > TOTAL_BUDGET_SEC:
            problems.append(f"SKIP {name}: 전체 상한 {TOTAL_BUDGET_SEC:.0f}s 초과")
            results.append((name, None))
            continue
        ctx.start_hook(name)
        box: dict = {}
        t0 = time.perf_counter()
        th = threading.Thread(target=_run_one, args=(ctx, modname, action, box), daemon=True)
        th.start()
        th.join(float(tmo) + 3.0)
        ms = (time.perf_counter() - t0) * 1000
        timings.append((name, ms))
        if th.is_alive():
            problems.append(f"TIMEOUT {name}: {tmo}s 초과 (결과 버림)")
            results.append((name, None))
            continue
        if "err" in box:
            problems.append(f"ERROR {name}: {box['err']} @ {box.get('tb', '')}")
            results.append((name, None))
            continue
        out = box.get("out")
        if isinstance(out, Spawn):
            sb = _spawn_start(out, raw_bytes)
            spawns.append((len(results), name, sb, max(float(tmo), SPAWN_MIN_SEC)))
            results.append((name, None))
        else:
            results.append((name, out))

    for idx, name, sb, tmo in spawns:
        now = time.perf_counter()
        remain = min(tmo - (now - sb.get("t0", now)), max(1.0, TOTAL_BUDGET_SEC + 5 - (now - t_start)))
        res, perr = _spawn_collect(sb, remain)
        timings.append((name + "[spawn]", (time.perf_counter() - sb.get("t0", t_start)) * 1000))
        if perr:
            problems.append(f"SPAWN {name}: {perr}")
        results[idx] = (name, res)

    if debug:
        dbg = {}
        for name, r in results:
            dbg[name] = None if r is None else {"rc": r.rc, "out": r.out, "err": r.err}
        if problems:
            dbg["__problems__"] = problems
        sys.stdout.buffer.write(json.dumps(dbg, ensure_ascii=False).encode("utf-8"))
        sys.stdout.buffer.flush()
        return 0

    rc, out, err, plain = _merge(results)
    if out:
        sys.stdout.buffer.write(_enc(out))
        sys.stdout.buffer.flush()
    if err:
        sys.stderr.buffer.write(_enc(err))
        sys.stderr.buffer.flush()

    total = (time.perf_counter() - t_start) * 1000
    parts = " ".join(f"{n}={ms:.0f}" for n, ms in timings)
    lines = [f"[{ts_iso_tz()}] {event} {tname} total={total:.0f}ms {parts}"]
    lines += [f"[{ts_iso_tz()}]   {p}" for p in problems]
    if plain:
        lines.append(f"[{ts_iso_tz()}]   plain-stdout(JSON 과 병합 불가로 로그만): " + " | ".join(
            s.strip().replace("\n", " / ")[:200] for s in plain))
    write_dispatch_log(os.path.join(ROOT, ".claude", "logs", "tool-dispatch.log"), lines)

    if any(t.is_alive() for t in threading.enumerate() if t is not threading.current_thread()):
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(rc)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
