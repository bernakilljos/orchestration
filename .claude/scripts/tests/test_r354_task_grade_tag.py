"""R354 (2026-11-24): /tasks 작업 목록 등급 표식 — PreToolUse Agent 에서 작업 설명 앞에 «특·상·중·하» 표식을 붙인다.

내장 목록 글자색은 바꿀 수 없어 설명 문자열에 표식(색 이모지 + 글자)을 넣는다. 특정 작업 이름 예외 처리 없이
모델 등급(입력 model > 에이전트 정의 > 상속)으로만 정한다.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DISPATCH = ROOT / ".claude" / "hooks" / "tool-dispatch.py"


def _run(tool_input, env_extra=None):
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Agent", "cwd": str(ROOT), "tool_input": tool_input}
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(ROOT))
    env.update(env_extra or {})
    r = subprocess.run([sys.executable, "-X", "utf8", str(DISPATCH), "pre"], input=json.dumps(payload).encode("utf-8"),
                       capture_output=True, env=env, timeout=60)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    out = r.stdout.decode("utf-8", "replace").strip()
    if not out:
        return None
    return json.loads(out).get("hookSpecificOutput", {}).get("updatedInput")


def test_grade_by_model_for_any_task_name():
    # 사용자 제보 두 사례 + 임의 이름 — 이름이 아니라 모델로 결정
    for desc in ("상시 검사 묶음 결과 확인", "03.PJT 폴더 목록 조회", "임의 작업"):
        for model, tag in (("", "🟣상"), ("opus", "🟣상"), ("sonnet", "🔵중"), ("haiku", "🟢하"), ("fable", "🔴특")):
            ti = {"description": desc, "prompt": "x", "subagent_type": "general-purpose"}
            if model:
                ti["model"] = model
            new = _run(ti)
            assert new["description"] == f"{tag} {desc}"
            assert new["prompt"] == "x" and new["subagent_type"] == "general-purpose"   # 다른 입력은 그대로


def test_already_tagged_or_empty_is_untouched():
    assert _run({"description": "🔵중 이미 표식", "prompt": "x"}) is None
    assert _run({"prompt": "x"}) is None


def test_switch_off():
    assert _run({"description": "작업", "prompt": "x"}, {"AGENT_GRADE_TAG": "0"}) is None


def test_no_ansi_in_description():
    new = _run({"description": "작업", "prompt": "x", "model": "haiku"})
    assert "\x1b" not in new["description"]
