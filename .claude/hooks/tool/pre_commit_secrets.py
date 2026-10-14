"""plugins/sec_scan/hooks/pre-commit-secrets.sh 이식 — git commit/push 시 gitleaks (또는 자체 패턴) 로 시크릿 차단 (exit 2).

git commit / git push 명령이 아니면 즉시 통과. 해당될 때만 (gitleaks 외부 도구 호출) 원본 스크립트에 위임한다.
"""
from __future__ import annotations

import os

from _common import Spawn, ensure_dir, grep_key_value_b, has_jq, bash_cat, project_guard, project_path


def run(ctx):
    # 원본은 가드보다 먼저 로그 디렉터리를 만든다
    ensure_dir(project_path(ctx, ".claude", "logs"))
    if not project_guard(ctx):
        return None
    inp = bash_cat(ctx.raw)
    if not inp:
        return None
    if has_jq():
        return Spawn("plugins/sec_scan/hooks/pre-commit-secrets.sh")
    cmd = grep_key_value_b(inp, "command")
    if "git commit" in cmd or "git push" in cmd:
        return Spawn("plugins/sec_scan/hooks/pre-commit-secrets.sh")
    return None
