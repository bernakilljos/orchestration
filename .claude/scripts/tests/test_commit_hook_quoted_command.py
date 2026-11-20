"""11-15: 커밋 검사 훅이 원시 JSON 에서 '"command":"[^"]*"' 로 명령을 뽑아 첫 \\" 에서 잘렸다 —
git commit 앞에 따옴표가 하나라도 있으면 회귀 게이트·문서 동반 검사가 통째로 건너뛰어졌다 (실제로 blocked 게이트로 커밋이 들어감)."""
import json
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[2] / "hooks"
sys.path.insert(0, str(HOOKS / "prompt"))
sys.path.insert(0, str(HOOKS / "tool"))

import _common  # noqa: E402
import pre_commit_full_check  # noqa: E402
import pre_commit_infra_check  # noqa: E402

CMD = 'cd /x; grep -o \'"status": *"[a-z]*"\' a.json | head -1; git commit -q -F - <<\'EOF\'\nmsg "q"\nEOF'


def _ctx(cmd):
    return _common.Ctx(json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}}))


def test_tool_command_keeps_text_after_quotes():
    assert _common.tool_command(_ctx(CMD)) == CMD


def test_full_check_fires_when_quote_precedes_commit(monkeypatch):
    monkeypatch.setattr(pre_commit_full_check, "project_guard", lambda ctx: True)
    assert pre_commit_full_check.run(_ctx(CMD)) is not None
    assert pre_commit_full_check.run(_ctx('echo "git commit" > x')) is None  # 글자만 있는 것은 그대로 무시


def test_infra_check_fires_when_quote_precedes_commit():
    assert pre_commit_infra_check.run(_ctx(CMD)) is not None


def test_broken_json_falls_back_past_escaped_quotes():
    raw = '{"tool_input":{"command":"grep \\"a\\" x; git commit -m y"'
    assert _common.tool_command(_common.Ctx(raw)).endswith("git commit -m y")


# 11-15(사이클 1038): 'timeout 590 git commit' 처럼 감싸는 명령이 앞에 붙으면 커밋으로 못 봐 회귀 게이트를 건너뛰었다
#   (c4d9e9e3d 가 게이트 기록 없이 들어감) — 그리고 파이썬 쪽이 넘겨도 sh 가 첫 \" 에서 명령을 잘라 다시 exit 0 했다.
import subprocess  # noqa: E402

WRAPPED = ["timeout 590 git commit -q -m y", "cd /x; timeout -k 5 590 git commit -m y", "time git commit -m y",
           "nice -n 5 git commit -m y", "nohup git commit -m y", "env A=1 git commit -m y", "FOO=1 timeout 9 git commit -m y"]


def test_full_check_sees_commit_behind_wrapper(monkeypatch):
    monkeypatch.setattr(pre_commit_full_check, "project_guard", lambda ctx: True)
    for c in WRAPPED:
        assert pre_commit_full_check.run(_ctx(c)) is not None, c
    assert pre_commit_full_check.run(_ctx("timeout 9 echo git commit")) is None


def _sh_reaches_staged_check(script, cmd):
    """sh 가 명령을 커밋으로 알아보고 본 검사(git diff --cached)까지 가는가 — bash -x 흔적으로 본다."""
    root = Path(__file__).resolve().parents[3]
    inp = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    r = subprocess.run([_common.bash_exe(), "-x", str(root / ".claude" / "hooks" / script)], input=inp, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env={**__import__("os").environ, "CLAUDE_PROJECT_DIR": str(root)}, timeout=60)
    return "diff --cached" in r.stderr


def test_sh_keeps_command_after_quotes():
    for script in ("pre-commit-full-check.sh", "pre-commit-infra-check.sh"):
        assert _sh_reaches_staged_check(script, CMD), script
