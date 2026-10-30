"""real_repair_chain.py — 실 코드 수정 종단 chain helper (Phase 7 · 2026-10-30).

사용자 지시 (8acdde1 후속 · "실제 실패 코드 · Agent 분석 · 격리 수정 · 재검증"):
  Scaffold 생성 X · 기존 자산 (repair_sandbox + Edit tool + pytest + verifier) 연결 helper.

Phase 7-R3 데모 (P7-REAL-REPAIR-DEMO) 재사용 가능 chain:
  1. prepare_sandbox(demo_id) — repair_sandbox.create + state 파일
  2. reproduce_failure(sandbox_cwd, test_cmd) — 실패 재현 (exit != 0 요구)
  3. collect_failure_evidence(sandbox_cwd, cmd, result) — stderr·exit 저장
  4. prepare_fix_prompt(evidence) — Claude Task tool subagent 호출용 prompt 생성
     (실 fix 는 메인 Claude Edit tool · Python 자동 호출 X · 사용자 지시 반영)
  5. verify_fix(sandbox_cwd, test_cmd) — fix 후 재실행
  6. check_sandbox_isolation(sandbox_cwd) — ROOT 누출 X 재확인
  7. save_evidence(demo_id, chain_data) — .claude/state/<demo_id>_evidence.json

안전 원칙:
  - sandbox 격리 전제 (ROOT 수정 X)
  - Agent 자동 호출 X (사용자 지시: "Python 에서 Task tool 호출 가정 X")
  - 특정 오류 하드코딩 X (범용 chain)
  - 성공은 **테스트 실패→성공 전환** 으로만 판정 (하드코딩 return 금지)
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[3])
LIB = ROOT / ".claude" / "scripts" / "lib"
STATE = ROOT / ".claude" / "state"


def prepare_sandbox(demo_id: str) -> Dict[str, Any]:
    """repair_sandbox 생성 (기존 자산 재사용)."""
    sys.path.insert(0, str(LIB))
    try:
        import repair_sandbox as _sb
    except Exception as e:
        return {"ok": False, "stage": "import", "error": str(e)}
    r = _sb.create(demo_id)
    return {**r, "stage": "prepare_sandbox"}


def reproduce_failure(sandbox_cwd: str, test_cmd: str,
                      timeout: int = 60) -> Dict[str, Any]:
    """격리 공간에서 실패 cmd 실행 · exit != 0 요구 (실패 재현 못 하면 종단 무의미)."""
    cwd = Path(sandbox_cwd)
    if not cwd.exists():
        return {"ok": False, "stage": "reproduce_failure", "error": f"sandbox not found: {sandbox_cwd}"}
    try:
        r = subprocess.run(
            test_cmd, shell=True, cwd=str(cwd),
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
            env={**os.environ, "ALLOW_VISIBLE_WINDOW": "1"},
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "stage": "reproduce_failure",
                "error": f"timeout ({timeout}s)"}
    reproduced = r.returncode != 0
    return {
        "ok": reproduced,
        "stage": "reproduce_failure",
        "reproduced": reproduced,
        "test_cmd": test_cmd,
        "exit_code": r.returncode,
        "stdout_tail": (r.stdout or "")[-800:],
        "stderr_tail": (r.stderr or "")[-800:],
        "note": "exit != 0 확인됨 (실패 재현 OK)" if reproduced
                else "exit == 0 — 실패 재현 못함 · 종단 불가",
    }


def prepare_minimal_agent_prompt(sandbox_cwd: str, test_cmd: str,
                                  error_file: str = "", error_line: str = "") -> str:
    """Phase 8-R2: Subagent 호출용 **최소** prompt (prompt-too-long 방지).

    사용자 지시 (be2d36a 후속):
      - 전체 대화 대신 작업별 최소 컨텍스트 전달
      - prompt-too-long · context-confusion 방지
      - 작업별 독립 Agent 호출

    설계:
      - 400자 이내 (이전 1500+ 자 실패 사례 반영)
      - 세션 맥락 무시 명시 ("지금 당장 1가지만")
      - tool 명시 (Read·Edit·Bash)
      - 반환 포맷 간결 (JSON 1줄)
      - 세션 과거 요약 X · systemMessage 영향 X
    """
    err_info = ""
    if error_file:
        err_info = f" at {error_file}"
        if error_line:
            err_info += f":{error_line}"
    return (
        f"Fix code in {sandbox_cwd}{err_info}.\n"
        f"Steps: 1) Read failing file. 2) Edit minimal fix. 3) Run `{test_cmd}` to confirm.\n"
        f"Rules: Edit only files inside {sandbox_cwd}. Minimal change. Keep function signatures.\n"
        f"Return 1 JSON line: {{\"edit_file\":\"\",\"edit_line\":N,\"exit_code\":N,\"passed\":\"X/Y\"}}"
    )


def prepare_fix_prompt(evidence: Dict[str, Any]) -> str:
    """Claude Task tool subagent 호출용 prompt 생성 (실 fix 는 사용자/메인 Claude).

    사용자 지시: "지원되지 않는 Task tool 을 Python 에서 직접 호출 X"
    → 이 함수는 prompt 만 생성 · 실 호출은 메인 Claude 세션 안에서.
    """
    stderr = evidence.get("stderr_tail", "")[:400]
    stdout = evidence.get("stdout_tail", "")[:400]
    exit_code = evidence.get("exit_code", -1)
    test_cmd = evidence.get("test_cmd", "")
    sandbox_cwd = evidence.get("sandbox_cwd", "")
    return (
        "# 격리 공간 실 코드 수정 요청\n\n"
        f"작업 디렉토리 (sandbox · ROOT 밖): {sandbox_cwd}\n\n"
        f"## 실패 재현\n"
        f"- cmd: `{test_cmd}`\n"
        f"- exit: {exit_code}\n"
        f"- stderr:\n```\n{stderr}\n```\n"
        f"- stdout:\n```\n{stdout}\n```\n\n"
        f"## 요청\n"
        f"1. 위 stderr 분석 → 실제 결함 파일 확인 (Read tool)\n"
        f"2. 결함 위치 **최소 수정** (Edit tool · 격리 디렉토리 안만)\n"
        f"3. test cmd 재실행 → PASS 확인 (Bash tool)\n"
        f"4. 결과 1줄 리포트: EDIT_LINE=<라인> · PYTEST_EXIT=<코드> · PASSED=<N>/<total>\n\n"
        f"지침:\n"
        f"- 사용자 지시: sandbox cwd 밖 파일 수정 금지\n"
        f"- 함수 로직 유지 (return 하드코딩 X)\n"
        f"- 최소 변경 (문법·import 복구 등)\n"
    )


def verify_fix(sandbox_cwd: str, test_cmd: str,
               timeout: int = 60) -> Dict[str, Any]:
    """fix 후 test 재실행 · exit=0 요구."""
    cwd = Path(sandbox_cwd)
    try:
        r = subprocess.run(
            test_cmd, shell=True, cwd=str(cwd),
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
            env={**os.environ, "ALLOW_VISIBLE_WINDOW": "1"},
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "stage": "verify_fix", "error": "timeout"}
    passed = r.returncode == 0
    # pytest "N passed" 추출 (범용 · 하드코딩 X)
    m = re.search(r"(\d+)\s+passed", (r.stdout or "") + (r.stderr or ""))
    passed_count = int(m.group(1)) if m else None
    return {
        "ok": passed,
        "stage": "verify_fix",
        "exit_code": r.returncode,
        "passed_count": passed_count,
        "stdout_tail": (r.stdout or "")[-500:],
        "stderr_tail": (r.stderr or "")[-500:],
    }


def check_sandbox_isolation(sandbox_cwd: str,
                            expected_file_touches: Optional[list] = None) -> Dict[str, Any]:
    """sandbox 격리 재확인 — ROOT 쪽 파일 누출 없는지."""
    cwd = Path(sandbox_cwd)
    issues = []
    # ROOT 안 수상한 파일 (sandbox 안 파일명과 같은) 체크
    if expected_file_touches:
        for fname in expected_file_touches:
            leak = ROOT / fname
            if leak.exists() and leak.resolve() != (cwd / fname).resolve():
                issues.append({"kind": "root_leak", "file": fname,
                               "root_path": str(leak)})
    # git diff on main (sandbox 수정이 main branch 로 자동 반영됐는지)
    try:
        r = subprocess.run(
            ["git", "diff", "--name-only"], cwd=str(ROOT),
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "ALLOW_VISIBLE_WINDOW": "1"},
        )
        root_dirty = [p for p in (r.stdout or "").splitlines()
                      if ".repair-sandbox/" not in p and p.strip()]
        if root_dirty and expected_file_touches:
            for p in root_dirty:
                if any(f in p for f in expected_file_touches):
                    issues.append({"kind": "unexpected_root_diff", "path": p})
    except Exception:
        pass
    return {
        "ok": len(issues) == 0,
        "stage": "check_sandbox_isolation",
        "issues": issues,
    }


def save_evidence(demo_id: str, chain_data: Dict[str, Any]) -> str:
    """evidence 저장 · 재사용 가능 포맷."""
    STATE.mkdir(parents=True, exist_ok=True)
    path = STATE / f"{demo_id}_evidence.json"
    chain_data.setdefault("saved_at", int(time.time()))
    chain_data.setdefault("demo_id", demo_id)
    path.write_text(json.dumps(chain_data, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return str(path)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 10-R2 (2026-10-30): Agent 수정 경로 자동 연결.
#   Python 은 Task tool 을 호출할 수 없다 → 이미 kit 이 쓰는 headless `claude -p`
#   (claude-auto.bat 와 같은 경로) 를 subprocess 로 실행한다. 결과 JSON 의 session_id 가
#   실제 Agent 실행 ID 이며 invocation="auto" 로 기록한다 (메인 Claude 수동 호출과 구분).
# ─────────────────────────────────────────────────────────────────────────────

# 역할 분리 (2026-10-30 Phase 11): fix Agent = 코드 수정만 (셸 없음) · 테스트 실행은 runner 가 격리 sandbox 에서
# 수행하고 실패 출력을 다음 라운드 Agent 에 되돌려 준다. Agent 자기보고가 검증 근거가 되지 않는다.
FIX_TOOLS = ["Read", "Edit", "Glob", "Grep"]
JUDGE_TOOLS = ["Read", "Glob", "Grep"]


def _agent_env(use_login_auth: bool) -> Dict[str, str]:
    env = {**os.environ, "ALLOW_VISIBLE_WINDOW": "0"}
    if use_login_auth:
        # 자식 프로세스만: env 의 API key 대신 로그인(OAuth) 계정 사용 — 메인 세션과 같은 인증.
        # 영구 설정(레지스트리·settings) 은 건드리지 않는다.
        env.pop("ANTHROPIC_API_KEY", None)
    return env


def dispatch_agent(prompt: str, cwd: str, model: str, allowed_tools: list,
                   role: str, timeout: int = 900, max_budget_usd: Optional[float] = None,
                   use_login_auth: bool = True, system_prompt: str = "") -> Dict[str, Any]:
    """headless Claude Agent 1회 자동 실행. 프로젝트 hook 은 로드하지 않는다 (--setting-sources user)."""
    import shutil
    if max_budget_usd is None:      # 자원 정책 단일 계층 (sandbox-policy.json)
        sys.path.insert(0, str(LIB))
        import repair_sandbox as _sbp
        max_budget_usd = float(_sbp._policy().get("agent_max_budget_usd", 3.0))
    exe = shutil.which("claude")
    if not exe:
        return {"ok": False, "invocation": "auto", "role": role, "error": "claude CLI not found"}
    argv = [exe, "-p", prompt, "--model", model, "--output-format", "json",
            "--setting-sources", "user", "--permission-mode", "dontAsk",
            "--allowedTools", *allowed_tools, "--max-budget-usd", str(max_budget_usd)]
    if system_prompt:
        argv += ["--append-system-prompt", system_prompt]
    started = time.time()
    try:
        r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace", env=_agent_env(use_login_auth),
                           stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"ok": False, "invocation": "auto", "role": role, "model": model,
                "error": f"timeout ({timeout}s)"}
    data = {}
    for line in reversed((r.stdout or "").strip().splitlines()):
        try:
            data = json.loads(line)
            break
        except Exception:
            continue
    usage = data.get("usage") or {}
    ok = r.returncode == 0 and bool(data) and not data.get("is_error")
    tok_in = sum(int(usage.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens",
                                                   "cache_read_input_tokens"))
    _record_agent_usage(role, model, tok_in, int(usage.get("output_tokens") or 0), data.get("total_cost_usd"),
                        int((time.time() - started) * 1000), ok, data.get("session_id"))
    return {
        "ok": ok,
        "invocation": "auto",
        "tokens_in": tok_in, "tokens_out": usage.get("output_tokens"),
        "role": role,
        "model": model,
        "agent_session_id": data.get("session_id"),
        "num_turns": data.get("num_turns"),
        "cost_usd": data.get("total_cost_usd"),
        "duration_s": round(time.time() - started, 1),
        "exit_code": r.returncode,
        "result": (data.get("result") or "")[-50000:],  # 구조화 JSON 응답이 잘리지 않게 (2000 자 절단으로 discovery JSON 파싱 실패 실측)
        "stderr_tail": (r.stderr or "")[-300:],
        "argv_shape": ["claude", "-p", "<prompt>"] + argv[3:],
    }


def _record_agent_usage(role, model, tok_in, tok_out, cost, latency_ms, ok, session_id) -> None:
    """Agent 1회 실행의 실제 토큰·비용을 metrics 에 기록 (Phase 15 · 기존 state_db.record_metric 재사용)."""
    try:
        sys.path.insert(0, str(LIB))
        import state_db
        state_db.record_metric(ai=f"claude-agent:{role.split(':')[0]}", model_id=model, tokens_in=tok_in,
                               tokens_out=tok_out, cost_usd=cost, latency_ms=latency_ms, success=ok,
                               task_id=session_id or None, error_class=None if ok else "agent_error")
    except Exception:
        pass


def _git_out(cwd: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60)
    return r.stdout or ""


def policy_check(sandbox_cwd: str, allow_paths: list, protected_paths: list,
                 root_status_before: str) -> Dict[str, Any]:
    """Agent 자기보고와 무관하게 실제 변경을 검사 (fail-closed)."""
    cwd = Path(sandbox_cwd)
    changed = []
    for line in _git_out(cwd, "status", "--porcelain").splitlines():
        p = line[3:].strip().strip('"')
        if p:
            changed.append(p.replace("\\", "/"))
    out_of_scope = [p for p in changed
                    if not any(p == a or p.startswith(a.rstrip("/") + "/") for a in allow_paths)]
    touched_protected = [p for p in changed if p in protected_paths]
    # ROOT 는 로그·scheduler·다른 세션 때문에 늘 바뀐다 → Agent 가 건드릴 수 있는 경로만 비교 (전체 비교는 오탐)
    watch = set(allow_paths) | set(protected_paths) | set(changed)
    pick = lambda st: sorted(l for l in st.splitlines() if l[3:].strip().strip('"').replace("\\", "/") in watch)
    root_after = "\n".join(pick(_git_out(ROOT, "status", "--porcelain")))
    root_status_before = "\n".join(pick(root_status_before))
    issues = []
    if not changed:
        issues.append("no_change")
    if out_of_scope:
        issues.append("out_of_scope")
    if touched_protected:
        issues.append("protected_modified")
    if root_after != root_status_before:
        issues.append("root_modified")
    return {"ok": not issues, "issues": issues, "changed": changed,
            "out_of_scope": out_of_scope, "touched_protected": touched_protected}


def _first_json_object(text: str) -> Optional[Dict[str, Any]]:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _register_repair_task(repair_goal_id: int, test_cmd: str, agent_session_id: str) -> str:
    import sqlite3
    tid = f"g{repair_goal_id}-agent-fix"
    spec = {"kind": "fix", "cmd": f"agent:claude-p session={agent_session_id}",
            "verify": test_cmd, "verify_type": "shell", "safe_mode": True}
    with sqlite3.connect(str(STATE / "orca.db")) as c:
        c.execute("INSERT OR REPLACE INTO tasks (task_id, task_file, status, created_at, retry_count) "
                  "VALUES (?, ?, 'running', ?, 0)", (tid, json.dumps(spec), int(time.time())))
        c.execute("INSERT OR IGNORE INTO goal_tasks (goal_id, task_id, sequence) VALUES (?, ?, 0)",
                  (repair_goal_id, tid))
    return tid


def _set_task_spec_sessions(tid: str, sessions: list) -> None:
    import sqlite3
    with sqlite3.connect(str(STATE / "orca.db")) as c:
        row = c.execute("SELECT task_file FROM tasks WHERE task_id=?", (tid,)).fetchone()
        spec = json.loads(row[0]) if row and row[0] else {}
        spec["cmd"] = "agent:claude-p sessions=" + ",".join(s or "?" for s in sessions)
        spec["agent_sessions"] = sessions
        c.execute("UPDATE tasks SET task_file=? WHERE task_id=?", (json.dumps(spec), tid))


def _set_task_status(tid: str, status: str) -> None:
    import sqlite3
    with sqlite3.connect(str(STATE / "orca.db")) as c:
        c.execute("UPDATE tasks SET status=?, completed_at=? WHERE task_id=?",
                  (status, int(time.time()), tid))


def agent_repair_chain(repair_goal_id: int, sandbox_id: str, test_cmd: str,
                       allow_paths: list, protected_paths: list,
                       apply_target: str, failure_summary: str = "",
                       fix_model: str = "claude-opus-5-5",
                       judge_model: str = "claude-opus-5-5",
                       max_fix_rounds: int = 2) -> Dict[str, Any]:
    """재현 → Agent 자동 수정 → 정책 검사 → runner pytest (실패 시 출력 되돌려 재수정) → 통계+LLM Judge → commit → ff 반영."""
    sys.path.insert(0, str(LIB))
    import repair_sandbox as _sb
    import runner as _rn
    import supervisor as _sup
    import independent_verifier as _iv

    out: Dict[str, Any] = {"repair_goal_id": repair_goal_id, "sandbox_id": sandbox_id,
                           "sandbox_root": str(_sb.SANDBOX_ROOT), "stages": []}

    def fail(stage, **kw):
        _sup.advance(repair_goal_id, "FAILED", f"agent_repair_chain:{stage}", actor="self-healing")
        out.update({"ok": False, "failed_stage": stage, **kw})
        return out

    entry = _sb._load_state().get(sandbox_id)
    if not entry or not Path(entry["path"]).exists():
        return fail("sandbox", error=f"sandbox not found: {sandbox_id}")
    cwd = entry["path"]
    _sup.advance(repair_goal_id, "PLANNING", "agent repair start", actor="self-healing")
    _sup.advance(repair_goal_id, "RUNNING", "agent repair start", actor="self-healing")

    # 1. 실패 재현 (재현 못 하면 수정 근거 없음)
    pre = reproduce_failure(cwd, test_cmd, timeout=180)
    out["stages"].append({"stage": "reproduce", "exit_code": pre.get("exit_code"),
                          "reproduced": pre.get("reproduced")})
    if not pre.get("reproduced"):
        return fail("reproduce", detail=pre)

    root_before = _git_out(ROOT, "status", "--porcelain")

    # 2~4. Agent 수정 → 정책 검사 → runner pytest. 실패 시 runner 출력을 다음 라운드 Agent 에 전달.
    tid = _register_repair_task(repair_goal_id, test_cmd, "")
    out["agent_fix_rounds"] = []
    failure_out = (pre.get("stdout_tail") or "")[-1200:] + "\n" + (pre.get("stderr_tail") or "")[-400:]
    vr: Dict[str, Any] = {}
    for rnd in range(1, max_fix_rounds + 1):
        fix_prompt = (
            f"A test is failing in this directory. Command: `{test_cmd}`\n"
            f"Latest test output from the runner (tail):\n{failure_out}\n"
            f"{failure_summary}\n"
            f"Find the root cause in the source and fix it with the smallest change. "
            f"You may edit only: {', '.join(allow_paths)}. Do NOT edit tests ({', '.join(protected_paths)}). "
            f"Do not hardcode return values. You cannot run commands: after you finish, an isolated runner "
            f"executes the tests and reports back. Reply with one JSON line: "
            f'{{"edit_file":"...","root_cause":"..."}}'
        )
        fix = dispatch_agent(fix_prompt, cwd, fix_model, FIX_TOOLS, role="fix")
        rec = {"round": rnd, "agent_session_id": fix.get("agent_session_id"), "ok": fix.get("ok"),
               "cost_usd": fix.get("cost_usd"), "duration_s": fix.get("duration_s"),
               "result": (fix.get("result") or "")[-600:]}
        out["agent_fix_rounds"].append(rec)
        out["agent_fix"] = fix
        out["stages"].append({"stage": "agent_fix", "round": rnd, "ok": fix.get("ok"),
                              "agent_session_id": fix.get("agent_session_id")})
        if not fix.get("ok"):
            return fail("agent_fix")

        pol = policy_check(cwd, allow_paths, protected_paths, root_before)
        out["policy"] = pol
        out["stages"].append({"stage": "policy", "round": rnd, "ok": pol["ok"], "issues": pol["issues"]})
        if not pol["ok"]:
            return fail("policy")

        vr = _rn.run(test_cmd, task_id=tid, worker_id="self-healing", timeout=300, cwd=cwd)
        m = re.search(r"(\d+)\s+passed", (vr.get("stdout") or ""))
        rec.update({"runner_exec_id": vr.get("exec_id"), "runner_exit_code": vr.get("exit_code")})
        out["stages"].append({"stage": "pytest", "round": rnd, "exec_id": vr.get("exec_id"),
                              "exit_code": vr.get("exit_code"),
                              "passed_count": int(m.group(1)) if m else None})
        if vr.get("exit_code") == 0:
            break
        failure_out = (vr.get("stdout") or "")[-1200:] + "\n" + (vr.get("stderr") or "")[-400:]

    passed = vr.get("exit_code") == 0
    if passed:
        _rn.mark_verified(vr.get("exec_id"), True)
    _set_task_spec_sessions(tid, [r["agent_session_id"] for r in out["agent_fix_rounds"]])
    _set_task_status(tid, "completed" if passed else "failed")
    out["diff"] = _git_out(Path(cwd), "diff")[:4000]
    out["test_before"] = {"exit_code": pre.get("exit_code"), "tail": (pre.get("stdout_tail") or "")[-300:]}
    out["test_after"] = {"exit_code": vr.get("exit_code"), "tail": (vr.get("stdout") or "")[-300:]}
    if not passed:
        return fail("pytest", rounds=len(out["agent_fix_rounds"]))

    # 5. 통계 judge → 독립 LLM Judge (별도 Agent 세션 · 읽기 전용 도구) → judge_absorb 결합
    jh = _iv.judge_handoff(repair_goal_id, sandbox_cwd=cwd, allow_paths=allow_paths)
    out["stages"].append({"stage": "stat_judge", "verdict": jh.get("stat_verdict")})
    if not jh.get("requires_llm_judge"):
        return fail("stat_judge")
    judge_prompt = (
        "You are an independent code-review judge. Do not trust the developer. "
        "Base your verdict only on the diff, the test results and the files here.\n"
        f"Original failure:\n{(pre.get('stdout_tail') or '')[-800:]}\n"
        f"Diff:\n{out['diff'][:3000]}\n"
        f"Tests after fix (exit {vr.get('exit_code')}):\n{(vr.get('stdout') or '')[-400:]}\n"
        f"Allowed paths: {allow_paths}. Tests must not be modified: {protected_paths}.\n"
        "Check: real root-cause fix (not hardcoded return / test bypass), scope, side effects. "
        "Reply with ONLY a JSON object: "
        '{"satisfies_requirement":bool,"missing_requirements":[],"unexpected_side_effects":[],'
        '"scope_adequacy":"ok|too_narrow|too_broad","confidence":0-10,'
        '"recommendation":"VERIFIED|UNVERIFIED|REPAIRING|OUT_OF_SCOPE","reasoning":"..."}'
    )
    jd = dispatch_agent(judge_prompt, cwd, judge_model, JUDGE_TOOLS, role="judge",
                        timeout=600, max_budget_usd=2.0)
    out["agent_judge"] = jd
    verdict_json = _first_json_object(jd.get("result", "")) if jd.get("ok") else None
    if not verdict_json:
        return fail("llm_judge", error="judge 결과 JSON 없음")
    ab = _iv.judge_absorb(repair_goal_id, json.dumps(verdict_json))
    final = (ab.get("final_verdict") or {}).get("status")
    out["judge"] = {"llm_verdict": verdict_json, "final_verdict": ab.get("final_verdict")}
    out["stages"].append({"stage": "llm_judge", "agent_session_id": jd.get("agent_session_id"),
                          "final": final})
    if final != "VERIFIED":
        return fail("judge_verdict")

    # 6. 안전한 반영: sandbox commit → target branch fast-forward (작업 트리 무변경)
    cm = _sb.commit_changes(sandbox_id, f"fix(self-healing): goal #{repair_goal_id} "
                                        f"agent={fix.get('agent_session_id')}")
    if not cm.get("ok") or not cm.get("committed"):
        return fail("commit", detail=cm)
    _sb.test(sandbox_id, test_cmd)  # apply_merge 전제: last_test exit 0 (재확인)
    ap = _sb.apply_merge(sandbox_id, target_branch=apply_target)
    out["apply"] = {**ap, "commit": cm.get("commit")}
    out["stages"].append({"stage": "apply", "ok": ap.get("ok"), "target": apply_target})
    if not ap.get("ok"):
        return fail("apply")
    _sup.advance(repair_goal_id, "VERIFIED",
                 f"agent fix {fix.get('agent_session_id')} · judge {jd.get('agent_session_id')} · "
                 f"applied {apply_target}@{cm.get('commit', '')[:7]}", actor="self-healing")
    out["ok"] = True
    return out


def _cli_main(argv):
    if len(argv) < 2:
        print("usage: real_repair_chain.py {prepare|reproduce|verify|isolation|prompt} [args]")
        return 2
    cmd = argv[1]
    if cmd == "prepare":
        if len(argv) < 3:
            print("usage: prepare <demo_id>")
            return 2
        print(json.dumps(prepare_sandbox(argv[2]), ensure_ascii=False, indent=2))
        return 0
    if cmd == "reproduce":
        if len(argv) < 4:
            print("usage: reproduce <sandbox_cwd> <test_cmd>")
            return 2
        print(json.dumps(reproduce_failure(argv[2], argv[3]), ensure_ascii=False, indent=2))
        return 0
    if cmd == "verify":
        if len(argv) < 4:
            print("usage: verify <sandbox_cwd> <test_cmd>")
            return 2
        print(json.dumps(verify_fix(argv[2], argv[3]), ensure_ascii=False, indent=2))
        return 0
    if cmd == "isolation":
        if len(argv) < 3:
            print("usage: isolation <sandbox_cwd> [file1,file2,...]")
            return 2
        files = argv[3].split(",") if len(argv) > 3 else None
        print(json.dumps(check_sandbox_isolation(argv[2], files),
                         ensure_ascii=False, indent=2))
        return 0
    if cmd == "prompt":
        # stdin 으로 evidence JSON 받음
        try:
            ev = json.loads(sys.stdin.read())
        except Exception as e:
            print(json.dumps({"error": f"stdin json: {e}"}))
            return 1
        print(prepare_fix_prompt(ev))
        return 0
    print(f"unknown cmd: {cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(_cli_main(sys.argv))
