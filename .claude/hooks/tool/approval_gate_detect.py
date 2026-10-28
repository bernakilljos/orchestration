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
    r"reg" + _S + r"+(add|delete)|alembic|systemctl|npm" + _S + r"+publish|docker" + _S + r"+push|gh" + _S + r"+release|terraform",
    re.I)


def _extract_cmd(inp: str) -> str:
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


def run(ctx):
    log_dir = project_path(ctx, ".claude", "logs")
    ensure_dir(log_dir)
    log = os.path.join(log_dir, "approval-gate.log")
    if not project_guard(ctx):
        return None
    inp = bash_read(ctx.raw)
    if not inp:
        return None
    if not _RISKWORD.search(inp):
        return None
    cmd = _extract_cmd(inp)
    if not cmd:
        return None
    # 2026-10-26: 실행 vs 언급 구분 — git commit message body 안 위험 문자열은 매칭 제외
    cmd = _strip_git_commit_message(cmd)
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
    task_id = "appr-" + hashlib.sha256((cmd + str(int(time.time()))).encode("utf-8", "surrogateescape")).hexdigest()[:12]
    # request 등록 - 출력(JSON)·오류는 로그로, 실패해도 계속 (원본: >>"$LOG" 2>&1 || true)
    try:
        res = mod.request_approval(task_id, cmd, category, desc)
        append_text(log, json.dumps(res, ensure_ascii=False, indent=2) + "\n")
    except Exception as e:  # noqa: BLE001
        append_text(log, "".join(traceback.format_exception_only(type(e), e)))
    append_text(log, "[%s] BLOCK: %s | task_id=%s | cmd=%s\n" % (time.strftime("%Y-%m-%d_%H:%M:%S"), category, task_id, cmd))
    err = ('{\n'
           '  "decision": "block",\n'
           '  "reason": " 위험 명령 감지 (%s): %s. /approve %s 또는 /reject %s [reason]",\n'
           '  "systemMessage": "HITL Approval Gate — task_id=%s | category=%s | /approve <id> 로 승인 후 진행"\n'
           '}\n') % (category, desc, task_id, task_id, task_id, category)
    return Result(2, "", err)
