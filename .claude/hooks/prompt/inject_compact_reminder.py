"""inject-compact-reminder.sh 이식 — 토큰 사용률 60%+ 시 /clear·compact 안내 주입.

마지막 assistant usage 를 세션 jsonl 끝에서부터 역방향으로 읽는다 (121MB 급 파일도 즉시).
git 은 사용률 75%+ 에서 _safe_to_clear 판정할 때만 호출 (원본과 동일하게 게이트).
"""
from __future__ import annotations

import glob
import json
import os
import re


def run(ctx):
    root = str(ctx.root)
    if not os.path.isdir(os.path.join(root, "plugins")):
        return None

    home = os.path.expanduser("~")
    cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    safe = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
    proj = os.path.join(home, ".claude", "projects", safe)
    if not os.path.isdir(proj):
        return None
    # 2026-09-19: stdin 의 transcript_path 가 정본 (mtime 최신 jsonl 추정은 동시 세션에서 틀림)
    own = ctx.payload.get("transcript_path") or ""
    if own and isinstance(own, str) and os.path.isfile(own):
        jsonls = [own]
    else:
        jsonls = sorted(glob.glob(os.path.join(proj, "*.jsonl")), key=os.path.getmtime, reverse=True)
    if not jsonls:
        return None
    last_usage = None
    model_id = ""
    # 처음부터 끝까지 읽으면 세션 jsonl(121MB 실측)에서 10초+ -> 끝에서부터 256KB 씩 거꾸로
    try:
        with open(jsonls[0], "rb") as f:
            f.seek(0, 2)
            pos = f.tell()
            tail = b""
            while pos > 0 and last_usage is None:
                step = min(262144, pos)
                pos -= step
                f.seek(pos)
                buf = f.read(step) + tail
                lines = buf.split(b"\n")
                tail = lines[0] if pos > 0 else b""  # 잘린 첫 줄은 다음 블록과 이어 붙임
                for raw in reversed(lines[1:] if pos > 0 else lines):
                    if b'"assistant"' not in raw:
                        continue
                    try:
                        rec = json.loads(raw.decode("utf-8", errors="replace"))
                    except Exception:
                        continue
                    if rec.get("type") == "assistant":
                        msg = rec.get("message") or {}
                        u = msg.get("usage") or {}
                        # 전부 0 인 usage(한도 초과 안내 등) 는 건너뛰고 직전 실제 응답을 쓴다
                        if ((u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
                                + (u.get("cache_creation_input_tokens") or 0)) > 0:
                            last_usage = u
                            model_id = msg.get("model") or ""
                            break
    except Exception:
        return None

    if not last_usage:
        return None

    tokens = int(
        (last_usage.get("input_tokens") or 0)
        + (last_usage.get("cache_read_input_tokens") or 0)
        + (last_usage.get("cache_creation_input_tokens") or 0)
    )

    # 상한 - 정본은 statusline_context.py 가 기록한 .claude/state/context-limit.json
    limit = None
    try:
        with open(os.path.join(cwd, ".claude", "state", "context-limit.json"), encoding="utf-8") as f:
            limit = int(json.load(f).get("limit") or 0) or None
    except Exception:
        pass
    if not limit:
        limit = 1_000_000 if ("[1m]" in (model_id or "") or tokens > 200_000) else 200_000
    pct = tokens / limit * 100

    RED = "\033[1;31m"
    YEL = "\033[1;33m"
    RST = "\033[0m"

    if pct >= 75:
        ok, why = _safe_to_clear(cwd)
        if ok is True:
            verdict = f"지금 /clear 해도 안전 ({why}) - 0초에 비워지고 새 세션이 최근 24h 작업 자동 복구."
        elif ok is False:
            verdict = f"지금은 /clear 보류 - {why}. 커밋 먼저."
        else:
            verdict = f"/clear 안전 판정 불가 ({why})."
        if pct >= 90:
            return f"{RED}[!!] 토큰 {pct:.0f}% ({tokens:,}/{limit:,}) - {verdict} 진행 중이면 그대로 - 97% 자동 compact (실측 중앙 173초).{RST}\n"
        return f"{YEL}[!] 토큰 {pct:.0f}% ({tokens:,}/{limit:,}) - 작업 경계에서 /clear 권장 · {verdict} 조기 /compact 는 빨라지지 않음 (실측 56만 토큰 211초).{RST}\n"
    if pct >= 60:
        return f"[i] 토큰 {pct:.0f}% - compact 임박. 앞으로 큰 파일 read 자제.\n"
    return None


def _safe_to_clear(root):
    """/clear 안전 판정 — 추적 중 파일의 미커밋 수정(M/A/D/R) 이 있으면 보류. 75%+ 일 때만 호출 (git 사용)."""
    import subprocess

    repos = [root] if os.path.isdir(os.path.join(root, ".git")) else [
        os.path.join(root, d) for d in sorted(os.listdir(root))
        if os.path.isdir(os.path.join(root, d, ".git"))]
    reasons = []
    for repo in repos[:6]:
        try:
            r = subprocess.run(["git", "--no-optional-locks", "-C", repo, "status", "--porcelain"],
                               capture_output=True, text=True, timeout=8, encoding="utf-8", errors="replace")
        except Exception:
            return (None, "git 확인 실패")
        lost = [x[3:].strip().strip('"') for x in (r.stdout or "").splitlines() if len(x) > 3 and x[:2] != "??"]
        lost = [q for q in lost if not q.startswith(("docs/deploy-history/",))]  # hook 자동 기록은 제외
        if lost:
            head = ", ".join(lost[:3]) + (f" 외 {len(lost) - 3}" if len(lost) > 3 else "")
            reasons.append(f"{os.path.basename(repo)} 미커밋 {len(lost)}건({head})")
    if reasons:
        return (False, " · ".join(reasons))
    return (True, "미커밋 0")
