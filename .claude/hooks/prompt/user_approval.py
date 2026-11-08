"""사용자 승인 확정 — 실제 사용자 프롬프트에서만 approval-gate 승인·거부를 기록한다 (2026-11-08 P0-2).

UserPromptSubmit 은 사용자가 입력했을 때만 발생하므로 Agent 가 만든 텍스트로는 실행되지 않는다.
프롬프트 전체가 '/approve <id>' 또는 '/reject <id> [사유]' 한 줄일 때만 인정한다
(붙여 넣은 문서·보고 안에 섞인 같은 문구는 전체 일치가 안 되므로 무시).
명령줄 approve/reject 는 approval-gate.py 에서 비활성, 도구 호출로 부르는 것은 approval_gate_detect 가 차단한다.
"""
from __future__ import annotations

import importlib.util
import os
import re

_CMD = re.compile(r"/(approve|reject)[ \t]+((?:appr|push)-[A-Za-z0-9_.-]{1,64})(?:[ \t]+([^\r\n]{0,200}))?")


def _gate(ctx):
    path = os.path.join(ctx.project_dir, ".claude", "scripts", "approval-gate.py")
    spec = importlib.util.spec_from_file_location("_approval_gate_user", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(ctx):
    if not ctx.has_plugins():
        return None
    m = _CMD.fullmatch((ctx.field("user_prompt", "prompt") or "").strip())
    if not m:
        return None
    action, task_id, reason = m.group(1), m.group(2), (m.group(3) or "").strip()
    if action == "approve" and reason:
        return None   # /approve 뒤 추가 문구 = 사람 확인 문장 아님 → 인정 X
    gate = _gate(ctx)
    if action == "approve":
        res = gate.approve(task_id, gate.USER_APPROVER)
    else:
        res = gate.reject(task_id, gate.USER_APPROVER, reason)
    if res.get("error"):
        return f"[사용자 승인] {task_id} 처리 안 됨 — {res['error']}"
    if action == "approve":
        return (f"[사용자 승인] {task_id} 승인 기록됨 (사용자 프롬프트). 같은 명령·같은 폴더에서 {gate.APPROVAL_TTL_SEC // 60}분 안 1회 실행 가능. "
                "Claude 는 approval-gate approve 를 다시 실행하지 않는다.")
    return f"[사용자 승인] {task_id} 거부 기록됨 (사유: {reason or '-'})."
