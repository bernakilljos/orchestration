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
