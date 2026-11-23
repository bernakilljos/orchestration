"""auto-smoke-test.sh · index-rule-on-edit.sh 이식 - Edit/Write 후 해당 파일일 때만 백그라운드 작업을 띄운다 (로그 전용 · 비차단).

R357 (2026-11-23): 두 훅은 settings 의 비동기 훅으로 Edit 마다 각각 Git 실행기 + bash (+ conhost) 를 띄웠지만,
대부분은 «대상 파일 아님» 으로 바로 끝났다 (bash 안 판정만 하는 데 프로세스 3개씩). 판정은 디스패처 안에서 하고
대상일 때만 원본과 같은 작업을 분리 실행한다. 판정 규칙은 원본 그대로:
- 경로 = tool_input.file_path · 역슬래시 → / · 연속 / 하나로
- smoke: *.sql *Controller.java *Service.java *controller*.py *service*.py *router*.py *.html *.jsx *.tsx *.vue (대소문자 구분)
         → bash .claude/scripts/smoke-test-screen.sh <경로> >> .claude/logs/smoke-test.log (SMOKE_TEST_ACTIVE=1)
- 색인: */.claude/rules/*.md *CLAUDE.md */memory/*.md → python lookup-rule.py --rebuild >> .claude/logs/lookup-index.log (RULE_INDEX_ACTIVE=1)
- 재귀 가드 환경 변수(SMOKE_TEST_ACTIVE · RULE_INDEX_ACTIVE) 가 이미 있으면 그 작업은 건너뛴다 (원본과 같음)
"""
from __future__ import annotations

import fnmatch
import os
import re
import shutil

from _common import bash_exe, tool_input

_SMOKE = ("*.sql", "*Controller.java", "*Service.java", "*controller*.py", "*service*.py", "*router*.py",
          "*.html", "*.jsx", "*.tsx", "*.vue")
_INDEX = ("*/.claude/rules/*.md", "*CLAUDE.md", "*/memory/*.md")


def _norm(fp: str) -> str:
    fp = fp.replace("\\", "/")
    return re.sub(r"/{2,}", "/", fp)


def _match(fp: str, pats) -> bool:
    return any(fnmatch.fnmatchcase(fp, p) for p in pats)   # bash case 의 * 도 / 를 넘는다 = fnmatchcase 와 같음


def _detach(args, log: str, env_add: dict) -> None:
    import subprocess
    kw = {}
    if os.name == "nt":
        kw["creationflags"] = 0x08000000 | 0x00000008   # CREATE_NO_WINDOW | DETACHED_PROCESS
    else:
        kw["start_new_session"] = True
    try:
        os.makedirs(os.path.dirname(log), exist_ok=True)
        with open(log, "ab") as out:
            subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=out, stderr=out, close_fds=True,
                             env={**os.environ, **env_add}, **kw)
    except Exception:  # noqa: BLE001 - 원본도 백그라운드 실패를 알리지 않았다 (로그 전용)
        pass


def _python(project_dir: str) -> str:
    try:
        with open(os.path.join(project_dir, ".claude", "state", "python-path.txt"), encoding="utf-8") as f:
            p = f.read().strip()
        if p:
            return p
    except OSError:
        pass
    return shutil.which("python") or "python"


def run(ctx):
    pd = ctx.project_dir
    if not os.path.isdir(os.path.join(pd, ".claude")):
        return None
    fp = tool_input(ctx).get("file_path") or ""
    if not isinstance(fp, str) or not fp:
        return None
    fp = _norm(fp)
    if not os.environ.get("SMOKE_TEST_ACTIVE") and _match(fp, _SMOKE):
        script = os.path.join(pd, ".claude", "scripts", "smoke-test-screen.sh")
        if os.path.isfile(script):
            _detach([bash_exe(), script, fp], os.path.join(pd, ".claude", "logs", "smoke-test.log"), {"SMOKE_TEST_ACTIVE": "1"})
    if not os.environ.get("RULE_INDEX_ACTIVE") and _match(fp, _INDEX):
        _detach([_python(pd), os.path.join(pd, ".claude", "scripts", "lookup-rule.py"), "--rebuild"],
                os.path.join(pd, ".claude", "logs", "lookup-index.log"), {"RULE_INDEX_ACTIVE": "1"})
    return None
