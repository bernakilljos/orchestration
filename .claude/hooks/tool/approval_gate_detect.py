"""approval-gate-detect.sh 이식 (3184b27 판) - 위험 명령(5 카테고리) 감지 시 approval-gate 등록 + 차단 (exit 2).

위험 판정 detect_risk / 등록 request_approval 은 approval-gate.py 의 함수를 in-process 로 호출한다 (정본 1곳 · python 하위 프로세스 0개).
원본의 1차 필터(위험 단어가 하나도 없으면 python 을 띄우지 않고 통과) 도 같은 의미로 유지한다.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import traceback

from _common import Result, append_text, bash_read, ensure_dir, load_script, project_guard, project_path

_S = r"[ \t\n\r\f\v]"
_RISKWORD = re.compile(
    r"drop|truncate|delete|rm" + _S + r"|git" + _S + r"+(push|reset|branch)|sudo|curl|wget|runas|chmod|batch|daily-limit|setx|"
    r"reg" + _S + r"+(add|delete)|alembic|systemctl|npm" + _S + r"+publish|docker" + _S + r"+push|gh" + _S + r"+release|terraform|"
    r"\biex\b|invoke-expression|set-executionpolicy|setenvironmentvariable|verb" + _S + r"+runas|"
    # 2026-11-08 P0·P1 확장 (push 변형·자기 승인·직접 유료 호출·삭제·배포·DB·설정)
    r"push|clean|checkout|restore|stash|rmtree|remove-item|find|kubectl|vercel|netlify|firebase|scp|"
    r"codex|gemini|claude|anthropic|openai|googleapis|approv|reject|decide|update|insert|replace|dispatch|"
    r"settings|\.env|set-content|add-content|out-file|tee|cp" + _S + r"|mv" + _S + r"|copy|move",
    re.I)


def _extract_cmd(inp: str) -> str:
    # 2026-11-08: JSON 으로 읽는다 — 문자열 자르기는 명령 안의 \"} 에서 끊겨 뒷부분(실제 위험 명령)이 검사에서 빠졌다
    try:
        d = json.loads(inp)
    except ValueError:
        d = None
    if isinstance(d, dict):
        ti = d.get("tool_input") if isinstance(d.get("tool_input"), dict) else d
        if isinstance(ti.get("command"), str):
            return ti["command"]
    tag = '"command":'
    i = inp.find(tag)
    cmd = inp[i + len(tag):] if i >= 0 else inp
    if cmd.startswith('"'):
        cmd = cmd[1:]
    if cmd.startswith(' "'):
        cmd = cmd[2:]
    for sep in ('", "', '","', '"}'):
        j = cmd.find(sep)
        if j >= 0:
            cmd = cmd[:j]
    cmd = cmd.replace('\\"', '"')     # JSON 의 \" -> "
    cmd = cmd.replace("\\\\", "\\")   # JSON 의 \\ -> \
    return cmd


def _strip_git_commit_message(cmd: str) -> str:
    """2026-10-26 외부 AI 지적: git commit -m 안 message body (문자열 '언급') 는 실행 대상 X.
    실행 vs 언급 구분 — msg body 안 위험 문자열은 매칭 제외.
    "DROP TABLE DB 실행" (위험) vs "feat: DROP TABLE 패턴 fix" (문서 기록) 구분."""
    if not re.search(r'\bgit\s+commit\b', cmd):
        return cmd
    # heredoc: -m "$(cat <<'EOF' ... EOF\n)"
    cmd2 = re.sub(
        r'-m\s+"\$\(cat\s+<<[\'"]?([A-Z0-9_]+)[\'"]?\s*\n.*?\n\1\s*\n\s*\)"',
        '-m "<MSG>"', cmd, flags=re.S
    )
    # 단순 -m "..." 또는 -m '...'
    cmd2 = re.sub(r'-m\s+"[^"]*"', '-m "<MSG>"', cmd2)
    cmd2 = re.sub(r"-m\s+'[^']*'", "-m '<MSG>'", cmd2)
    return cmd2


_SEARCH_CMDS = ("grep", "egrep", "fgrep", "rg", "ag", "findstr")


def _strip_inert_text(cmd: str) -> str:
    """2026-10-30: 실행되지 않는 '언급' 만 제외 (위험 명령 차단 자체는 그대로).
    ① cat 이 파일로만 쓰는 heredoc 본문 (`cat >> f <<'EOF' ... EOF`) — 파이프로 셸에 넘기면 제외 X
    ② 검색 명령(grep·rg 등) 세그먼트의 따옴표 검색어 — 같은 줄의 다른 명령 세그먼트는 그대로 검사
    bash/sh/python 등으로 실행되는 heredoc 은 손대지 않는다."""
    # hook 입력은 JSON 이라 줄바꿈이 '\\n' 문자로 들어온다 → 실제 줄바꿈으로 (실측: 미변환 시 heredoc 인식 0)
    cmd = cmd.replace("\\n", "\n").replace("\\t", "\t")

    def _heredoc(m):
        head = m.group(1)
        if ">" in head and "|" not in head:
            return f"{head}\n<DOC>\n{m.group(2)}"
        return m.group(0)
    cmd = re.sub(r"((?:^|(?<=[;&\n]))\s*cat\b[^\n]*?<<-?\s*['\"]?(\w+)['\"]?[^\n]*)\n.*?\n(\2)(?=\s*(?:\n|$))",
                 lambda m: _heredoc(type("M", (), {"group": lambda s, i: (m.group(0), m.group(1), m.group(3))[i]})()),
                 cmd, flags=re.S)
    parts = re.split(r"(\s*(?:&&|\|\||;|\n)\s*)", cmd)
    for i, seg in enumerate(parts):
        words = seg.strip().split()
        if words and os.path.basename(words[0]).lower() in _SEARCH_CMDS:
            parts[i] = re.sub(r"'[^']*'|\"[^\"]*\"", "'<PATTERN>'", seg)
    return "".join(parts)


_RX_SCRIPT = re.compile(r"""(?:"([^"]+\.(?:ps[dm]?1|py|sh|bat|cmd))"|'([^']+\.(?:ps[dm]?1|py|sh|bat|cmd))'|"""
                        r"""([^\s"'`;|&<>()]+\.(?:ps[dm]?1|py|sh|bat|cmd)))(?![\w.])""", re.I)


def _artifacts(cmd: str, raw_cwd: str) -> dict:
    """명령이 실행하는 스크립트 파일의 sha256 (2026-11-09 · 승인 후 내용 변경 차단).
    없는 파일은 'missing' — 승인 때 없던 파일이 실행 때 생겨도 다름으로 잡힌다."""
    import importlib.util  # Git Bash /c/… 경로·환경 변수·상대 경로 정규화 정본(ensure_ps1_bom._norm) 재사용
    spec = importlib.util.spec_from_file_location(
        "_agd_ps1_bom", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ensure_ps1_bom.py"))
    bom = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bom)
    _norm = bom._norm
    out: dict = {}
    for m in _RX_SCRIPT.finditer(cmd):
        p = os.path.normcase(os.path.abspath(_norm(next(g for g in m.groups() if g), raw_cwd or os.getcwd())))
        if p in out or len(out) >= 20:
            continue
        try:
            with open(p, "rb") as f:
                out[p] = hashlib.sha256(f.read()).hexdigest()
        except OSError:
            out[p] = "missing"
    return out


def _fingerprint(ctx):
    """(원문 명령, 검사용 명령, 작업 위치, 요청 번호) — 승인 요청·소비·결과 기록이 같은 번호를 쓰게 한 곳에서 계산."""
    inp = bash_read(ctx.raw)
    if not inp or not _RISKWORD.search(inp):
        return None
    raw_cmd = _extract_cmd(inp)
    if not raw_cmd:
        return None
    # 2026-10-26: 실행 vs 언급 구분 — git commit message body 안 위험 문자열은 매칭 제외
    cmd = _strip_inert_text(_strip_git_commit_message(raw_cmd))
    # 2026-11-08: 요청 번호 = 명령·작업 위치 지문 (시각 X) → 승인 후 같은 명령을 다시 내면 그 승인을 1회만 쓴다.
    # 다른 명령·다른 폴더는 지문이 달라 그 승인을 전용할 수 없다.
    try:
        raw_cwd = str(json.loads(ctx.raw or "{}").get("cwd") or "")
    except (ValueError, AttributeError):
        raw_cwd = ""
    cwd = raw_cwd.replace("\\", "/").rstrip("/").lower()
    task_id = "appr-" + hashlib.sha256((cwd + "\n" + cmd).encode("utf-8", "surrogateescape")).hexdigest()[:12]
    return raw_cmd, cmd, raw_cwd, task_id


def run_action(ctx, action):
    """PostToolUse: 이 명령으로 소비된 승인이 있으면 실행 결과를 기록한다 (차단·출력 없음)."""
    if action != "post" or not project_guard(ctx):
        return None
    fp = _fingerprint(ctx)
    if fp is None:
        return None
    mod = load_script("approval-gate")
    if mod is None or not hasattr(mod, "record_result"):
        return None
    try:
        resp = json.loads(ctx.raw or "{}").get("tool_response")
    except (ValueError, AttributeError):
        resp = None
    resp = resp if isinstance(resp, dict) else {}
    outcome = "interrupted" if resp.get("interrupted") else "finished"
    text = "%s%s" % (resp.get("stdout") or "", resp.get("stderr") or "")
    info = {"output_sha256": hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16], "output_tail": text[-300:]}
    log = project_path(ctx, ".claude", "logs", "approval-gate.log")
    try:
        if mod.record_result(fp[3], outcome, info):
            append_text(log, "[%s] RESULT: %s | task_id=%s\n" % (time.strftime("%Y-%m-%d_%H:%M:%S"), outcome, fp[3]))
    except Exception as e:  # noqa: BLE001 — 기록 실패는 근거만 남긴다 (상태는 consumed/running = 결과 미확인 그대로)
        append_text(log, "RESULT-FAIL " + "".join(traceback.format_exception_only(type(e), e)))
    return None


def run(ctx):
    log_dir = project_path(ctx, ".claude", "logs")
    ensure_dir(log_dir)
    log = os.path.join(log_dir, "approval-gate.log")
    if not project_guard(ctx):
        return None
    fp = _fingerprint(ctx)
    if fp is None:
        return None
    raw_cmd, cmd, raw_cwd, task_id = fp
    gate = project_path(ctx, ".claude", "scripts", "approval-gate.py")
    if not os.path.isfile(gate):
        return None
    # 원본은 detect 호출에 2>>"$LOG" 리다이렉트가 있어 로그 파일이 (비어 있어도) 생긴다
    try:
        open(log, "ab").close()
    except OSError:
        pass
    mod = load_script("approval-gate")
    if mod is None:
        return None
    risk = mod.detect_risk(cmd)
    if risk is None:
        return None
    category = risk.get("category") or ""
    desc = risk.get("description") or ""
    if not category:
        return None
    state = "none"
    try:
        arts = _artifacts(raw_cmd, raw_cwd)
        state = mod.consume_approval(task_id, artifacts=arts)
    except Exception as e:  # noqa: BLE001 — 해시 계산·확인 실패 = 차단 유지 (fail-closed · 예외를 밖으로 내면 디스패처가 통과시킨다)
        arts = None
        append_text(log, "".join(traceback.format_exception_only(type(e), e)))
    if state == "consumed":
        append_text(log, "[%s] ALLOW-ONCE: %s | task_id=%s | cmd=%s\n" % (time.strftime("%Y-%m-%d_%H:%M:%S"), category, task_id, cmd))
        return None
    if state == "changed":
        append_text(log, "[%s] SCRIPT-CHANGED: %s | task_id=%s\n" % (time.strftime("%Y-%m-%d_%H:%M:%S"), category, task_id))
        desc = "승인 뒤 실행할 스크립트 내용이 바뀌어 이전 승인을 쓰지 않음 — 바뀐 내용 확인 후 다시 승인 필요 · " + desc
    # request 등록 - 출력(JSON)·오류는 로그로, 실패해도 계속 (원본: >>"$LOG" 2>&1 || true). 대기 중이면 새로 쓰지 않는다.
    if state != "waiting":
        try:
            res = mod.request_approval(task_id, cmd, category, desc, artifacts=arts)
            append_text(log, json.dumps(res, ensure_ascii=False, indent=2) + "\n")
        except Exception as e:  # noqa: BLE001
            append_text(log, "".join(traceback.format_exception_only(type(e), e)))
    append_text(log, "[%s] BLOCK: %s | task_id=%s | cmd=%s\n" % (time.strftime("%Y-%m-%d_%H:%M:%S"), category, task_id, cmd))
    err = ('{\n'
           '  "decision": "block",\n'
           '  "reason": " 위험 명령 감지 (%s): %s. 사용자가 프롬프트에 /approve %s 또는 /reject %s [reason] 입력 — '
           'Claude 는 승인 명령을 실행하지 않는다. 승인 후 같은 명령을 같은 폴더에서 1회 실행 가능 (30분)",\n'
           '  "systemMessage": "HITL Approval Gate — task_id=%s | category=%s | 사용자 /approve <id> 후 같은 명령 1회"\n'
           '}\n') % (category, desc, task_id, task_id, task_id, category)
    return Result(2, "", err)
