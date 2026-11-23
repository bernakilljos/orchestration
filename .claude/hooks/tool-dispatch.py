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
    ("scope-lock", "scope_lock", "Edit|Write", 3, None),
    ("ensure-ps1-bom", "ensure_ps1_bom", "Bash|PowerShell", 3, None),
    ("block-screen-capture", "block_screen_capture", "Bash|PowerShell", 3, None),
    ("block-visible-windows", "block_visible_windows", "Bash", 60, None),
    ("block-file-deletion", "block_file_deletion", "Bash|PowerShell", 3, None),
    ("block_dangerous_bash", "block_dangerous_bash", "Bash|PowerShell", 3, None),
    ("log_bash_command", "log_bash_command", "Bash|PowerShell", 3, None),
    ("pre-build-reminder", "pre_build_reminder", "Bash", 3, None),
    ("secret-scan", "secret_scan", "Bash|PowerShell", 3, None),
    ("pre-commit-secrets", "pre_commit_secrets", "Bash|PowerShell", 30, None),
    ("approval-gate-detect", "approval_gate_detect", "Bash|PowerShell", 5, None),
    ("pre-commit-full-check", "pre_commit_full_check", "Bash|PowerShell", 5, None),
    # R351 F1 (2026-11-20): pre-commit-infra-check 등록 제거 — 판정 경로가 full-check 와 같고 막는 경우가 그 부분 집합
    #   (문서 3종 모두 없음 ⊂ guide.txt 없음) 이라 매 커밋마다 같은 검사를 한 번 더 돌릴 뿐이었다 · 파일은 보존 (test_r351_commit_hooks_dedup)
    ("track-agent-dispatch", "track_agent_dispatch", "Agent", 5, "pending"),
]
POST = [
    ("check-korean-only", "check_korean_only", "Edit|Write", 60, None),
    ("ensure-ps1-bom", "ensure_ps1_bom", "Edit|Write", 3, None),
    ("detect-demo-pattern", "detect_demo_pattern", "Edit|Write", 3, None),
    ("post_write_pycheck", "post_write_pycheck", "Edit|Write", 30, None),
    ("markdown_formatter", "markdown_formatter", "Edit|Write", 5, None),
    ("check-indentation", "check_indentation", "Edit|Write", 3, None),
    ("prevent-whitespace-png", "prevent_whitespace_png", "Edit|Write", 5, None),
    ("check-js-syntax", "check_js_syntax", "Edit|Write", 5, None),
    ("check-html-balance", "check_html_balance", "Edit|Write", 5, None),
    ("enforce-file-naming", "enforce_file_naming", "Edit|Write", 60, None),
    ("hook-09-ocr-verify", "hook_09_ocr_verify", "Bash", 60, None),
    # 2026-11-09: 소비된 승인의 실행 결과 기록 (승인 소비 ≠ 실행 성공) · 실패·중단은 PostToolUse 가 안 와 consumed/running = 결과 미확인
    ("approval-gate-result", "approval_gate_detect", "Bash|PowerShell", 5, "post"),
    ("orca-heartbeat", "heartbeat", ".*", 60, None),
    ("korean-report-drift", "korean_report_drift", ".*", 3, None),   # §83 턴 중간 영어 보고 즉시 교정 안내
    ("periodic-snapshot", "periodic_snapshot", ".*", 5, None),
    ("propagate-rule-change", "propagate_rule_change", "Edit|Write", 60, None),
    # R357: 종전 settings 의 별도 동기 훅 (bash 1 + python 3 · Edit 마다 응답 대기) → in-process 기록
    ("post-edit-ping-pong", "post_edit_ping_pong", "Edit|Write|MultiEdit", 10, None),
    # R357: 종전 settings 비동기 훅 auto-smoke-test.sh · index-rule-on-edit.sh — 판정은 여기서 · 대상일 때만 분리 실행
    ("post-edit-bg", "post_edit_bg", "Edit|Write", 5, None),
]
# SubagentStart / SubagentStop (2026-10-16) — 백그라운드 서브에이전트의 실제 시작·종료는 여기로만 온다
#   (PostToolUse Agent 는 백그라운드면 «실행 직후» 에 와서 종료 신호로 쓸 수 없다)
SUB = [
    ("track-agent-dispatch", "track_agent_dispatch", ".*", 5, "sub"),
    ("log-subagent", "log_subagent", ".*", 10, None),
]
TABLE = {"pre": PRE, "post": POST, "sub": SUB}

# R363 (2026-11-23): Stop 훅 18개가 응답 끝마다 각각 Git 실행기 + bash(-c) + bash 스크립트(+conhost) 로 떠 프로세스 약 70개 (추적 실측)
#   → settings 에는 이 디스패처 1개만 · 원본 스크립트는 그대로 실행 (로직 이식 없음 · 훅마다 실행기·bash 2단계 절약)
#   (이름, 실행기 bash|python, 원본 경로, 인자, settings timeout 초, 추가 환경 변수) · 순서 = 종전 settings Stop 순서
#   동기 3개 = 응답을 붙잡고 차단 판정 (병렬 실행 · exit 2 / JSON decision=block 사유 모두 보존 · 설정 순서로 이어 붙임)
#   비동기 15개 = 분리 실행기(stop-async) 1개가 병렬로 돌리고 각자 timeout 을 지킨다 (넘으면 하위 트리 종료) · 응답을 붙잡지 않음
STOP_ASYNC = [
    ("hook-08-ai-handoff", "bash", "plugins/exec_orch/hooks/hook-08-ai-handoff.sh", ("auto",), 10, None),
    ("stop-snapshot", "bash", "plugins/exec_session_guard/hooks/stop-snapshot.sh", ("Stop",), 10, None),
    ("outbox-write", "bash", "plugins/exec_session_guard/hooks/outbox-write.sh", ("Stop",), 10, None),
    ("auto-compact-check", "bash", "plugins/exec_session_guard/hooks/auto-compact-check.sh", (), 10, None),
    ("stop-doc-summary", "bash", "plugins/doc_auto/hooks/stop-doc-summary.sh", (), 10, None),
    ("check-infra-sync", "bash", ".claude/hooks/check-infra-sync.sh", (), 10, None),
    ("auto-update-stats", "bash", ".claude/scripts/auto-update-stats.sh", (), 10, None),
    ("hook-06-notify", "bash", "plugins/exec_orch/hooks/hook-06-notify.sh", (), 10, None),
    ("audit-bat-lines", "python", ".claude/scripts/audit-bat-lines.py", (), 60, None),
    ("audit-install-dryrun", "python", ".claude/scripts/audit-install-dryrun.py", (), 90, None),
    ("sync-to-team", "bash", ".claude/scripts/sync-to-team.sh", (), 30, {"SYNC_IF_CHANGED": "1"}),
    ("save-session-summary", "bash", ".claude/hooks/save-session-summary.sh", (), 60, None),
    ("session-stop-snapshot", "bash", ".claude/hooks/session-stop-snapshot.sh", (), 10, None),
    ("auto-save-next-actions", "bash", ".claude/hooks/auto-save-next-actions.sh", (), 10, None),
    ("stop-active-goals-resume", "bash", ".claude/hooks/stop-active-goals-resume.sh", (), 15, None),
]
STOP_SYNC = [
    ("stop-request-ledger-gate", "bash", ".claude/hooks/stop-request-ledger-gate.sh", (), 10, None),
    ("stop-standing-gate", "bash", ".claude/hooks/stop-standing-gate.sh", (), 10, None),
    ("stop-six-guards", "bash", ".claude/hooks/stop-six-guards.sh", (), 15, None),
]

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
        from _common import child_creationflags   # R363: 콘솔이 있으면 물려받음 (자식마다 conhost 생성 방지)
        kw["creationflags"] = child_creationflags()
    box: dict = {"t0": time.perf_counter()}
    try:
        from _common import bash_exe   # R346 후속 8: ["bash",…] 는 Windows 에서 System32 WSL 실행기가 PATH 보다 먼저
        proc = subprocess.Popen([bash_exe(), path] + list(sp.args), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
            # 2026-10-16: 차단 사유를 stdout 에 찍는 훅(pre-commit-full-check 등)은 사유가 통째로 사라져
            #   "No stderr output" 만 보였다 — stderr 가 비면 stdout 을 사유로 쓴다.
            blockers.append(r.err if r.err.strip() else r.out)
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


def _stop_spawn(entry, raw_bytes: bytes) -> dict:
    """STOP_* 항목 1개를 원본 그대로 띄운다 (bash <경로> <인자> 또는 python <경로>) · 입출력은 스레드가 수거."""
    import subprocess

    name, interp, rel, args, _tmo, env_add = entry
    path = os.path.join(ROOT, *rel.split("/"))
    box: dict = {"t0": time.perf_counter()}
    if not os.path.isfile(path):
        box["err"] = "MISSING"
        return box
    try:
        from _common import bash_exe
        exe = bash_exe() if interp == "bash" else sys.executable
        from _common import child_creationflags   # R363: 콘솔이 있으면 물려받음 (훅마다 conhost 1개씩 생기던 것)
        kw = {"creationflags": child_creationflags()} if os.name == "nt" else {}
        env = {**os.environ, **env_add} if env_add else None
        proc = subprocess.Popen([exe, path, *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, cwd=ROOT, env=env, **kw)
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


def _stop_run(entries, raw_bytes: bytes):
    """병렬로 띄우고 각자 timeout 으로 수거 → ([(name, Result|None)], timings, problems)."""
    boxes = [(e, _stop_spawn(e, raw_bytes)) for e in entries]
    results, timings, problems = [], [], []
    for e, b in boxes:
        name, tmo = e[0], float(e[4] or 60)
        if b.get("err") == "MISSING":
            results.append((name, None))
            continue
        remain = max(0.1, tmo - (time.perf_counter() - b.get("t0", time.perf_counter())))
        res, perr = _spawn_collect(b, remain)
        timings.append((name, (time.perf_counter() - b.get("t0", time.perf_counter())) * 1000))
        if perr:
            problems.append(f"{name}: {perr}")
        results.append((name, res))
    return results, timings, problems


def _stop_detach_async(raw_bytes: bytes) -> bool:
    """비동기 Stop 훅 실행기(stop-async)를 분리 실행 — 작업 묶음 밖(BREAKAWAY)으로 · 막힌 환경이면 종전 플래그로 한 번 더."""
    import subprocess

    # R363: DETACHED_PROCESS 는 콘솔이 없어 자식 15개가 각자 conhost 를 만들었다 (실측 16~19개/응답) → 콘솔을 물려받게
    #   (분배기에 콘솔이 있으면 0 · 없으면 CREATE_NO_WINDOW 로 숨은 콘솔 1개) · 작업 묶음 밖(BREAKAWAY)은 그대로
    from _common import child_creationflags
    base = child_creationflags() if os.name == "nt" else 0
    for flags in ((base | 0x01000000, base) if os.name == "nt" else (0,)):   # 0x01000000 = CREATE_BREAKAWAY_FROM_JOB
        try:
            kw = {"creationflags": flags} if os.name == "nt" else {"start_new_session": True}
            p = subprocess.Popen([sys.executable, "-X", "utf8", os.path.abspath(__file__), "stop-async"],
                                 stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 cwd=ROOT, close_fds=True, **kw)
            try:
                p.stdin.write(raw_bytes)
                p.stdin.close()
            except OSError:
                pass
            return True
        except OSError:
            continue
    return False


def _stop_main(event: str) -> int:
    """stop = 비동기 실행기 분리 + 동기 3개 차단 판정 · stop-async = 비동기 15개 실행 (출력 없음)."""
    from _common import ts_iso_tz, write_dispatch_log

    t_start = time.perf_counter()
    raw_bytes = sys.stdin.buffer.read()
    log = os.path.join(ROOT, ".claude", "logs", "tool-dispatch.log")
    if event == "stop-async":
        results, timings, problems = _stop_run(STOP_ASYNC, raw_bytes)
        lines = [f"[{ts_iso_tz()}] stop-async total={(time.perf_counter() - t_start) * 1000:.0f}ms "
                 + " ".join(f"{n}={ms:.0f}" for n, ms in timings)]
        lines += [f"[{ts_iso_tz()}]   {p}" for p in problems]
        lines += [f"[{ts_iso_tz()}]   rc {n}={r.rc}" for n, r in results if r is not None and r.rc not in (0,)]
        write_dispatch_log(log, lines)
        return 0
    detached = _stop_detach_async(raw_bytes)
    results, timings, problems = _stop_run(STOP_SYNC, raw_bytes)
    if not detached:   # 분리 실행이 막힌 환경: 응답이 늦어지더라도 비동기 훅이 빠지지 않게 여기서 돌린다
        r2, t2, p2 = _stop_run(STOP_ASYNC, raw_bytes)
        timings += t2
        problems += p2
    reasons, others = [], []
    for name, r in results:
        if r is None:
            continue
        if r.rc == 2:
            reasons.append((r.err if r.err.strip() else r.out).rstrip("\n"))
            continue
        if r.rc == 0 and r.out.strip():
            j = _as_json(r.out)
            if isinstance(j, dict) and j.get("decision") == "block":
                reasons.append(str(j.get("reason") or "").rstrip("\n"))
            elif isinstance(j, dict):
                others.append((name, r))
    rc, out = 0, ""
    if reasons:
        sys.stderr.buffer.write(_enc("\n".join(x for x in reasons if x) + "\n"))
        sys.stderr.buffer.flush()
        rc = 2
    elif others:
        mrc, mout, _merr, _plain = _merge(others)
        out = mout
    if out:
        sys.stdout.buffer.write(_enc(out))
        sys.stdout.buffer.flush()
    lines = [f"[{ts_iso_tz()}] stop total={(time.perf_counter() - t_start) * 1000:.0f}ms async={'detached' if detached else 'inline'} rc={rc} "
             + " ".join(f"{n}={ms:.0f}" for n, ms in timings)]
    lines += [f"[{ts_iso_tz()}]   {p}" for p in problems]
    write_dispatch_log(log, lines)
    return rc


def main(argv) -> int:
    if argv and argv[0] in ("stop", "stop-async"):
        return _stop_main(argv[0])
    if not argv or argv[0] not in TABLE:
        sys.stderr.write("usage: tool-dispatch.py pre|post|sub [--debug-per-hook]\n")
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
    if event == "post" or (event == "pre" and rc == 2):   # §78 도구 시도 기록 (성공 = post · 차단 = pre rc 2 · 실패 = PostToolUseFailure)
        try:
            from _common import trace_emit
            ti = (json.loads(raw or "{}").get("tool_input") or {}) if raw else {}
            brief = ti.get("command") or ti.get("file_path") or ti.get("description") or ""
            trace_emit("tool", step=tname, status="success" if event == "post" else "blocked", duration_ms=total,
                       # R259: 200자로 자르면 앞이 긴 명령의 뒤쪽 git commit·merge-to-target --apply 가 사라져
                       #   상태줄 개발 단계가 실제로 한 커밋·전파를 «안 함» 으로 셌다 (R257·R258 4/6) · 기록 상한(2000) 안에서 1800
                       detail={"input": str(brief)[:1800], "hooks_ms": round(total)},
                       error="; ".join(problems)[:300] if problems else None)
        except Exception:  # noqa: BLE001
            pass

    if any(t.is_alive() for t in threading.enumerate() if t is not threading.current_thread()):
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(rc)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
