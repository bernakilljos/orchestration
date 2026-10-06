#!/usr/bin/env bash
# inject-compact-reminder - 토큰 70%+ 시 UserPromptSubmit 에 systemMessage 로 compact 알림 강제 주입
# 근거: 사용자 지시 (2026-09-03) - "멍청해지고있으니 compact 을 해야한다던지 주입"
# 발동: UserPromptSubmit hook
set -e
SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SELF/../.." && pwd)"

# sub-project guard
[ -d "$ROOT/plugins" ] || exit 0

# python 자동 검색
if command -v python >/dev/null 2>&1; then PY=python
elif command -v python3 >/dev/null 2>&1; then PY=python3
else exit 0
fi

# 최근 assistant usage 에서 토큰 사용률 계산
"$PY" -X utf8 - <<'PYEOF' 2>/dev/null
import json, os, glob, re, sys, subprocess

home = os.path.expanduser("~")
cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
safe = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
proj = os.path.join(home, ".claude", "projects", safe)
if not os.path.isdir(proj):
    sys.exit(0)
jsonls = sorted(glob.glob(os.path.join(proj, "*.jsonl")), key=os.path.getmtime, reverse=True)
if not jsonls:
    sys.exit(0)
last_usage = None
model_id = ""
try:
    with open(jsonls[0], encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("type") == "assistant":
                u = ((rec.get("message") or {}).get("usage")) or None
                m = ((rec.get("message") or {}).get("model")) or ""
                if u:
                    last_usage = u
                if m:
                    model_id = m
except Exception:
    sys.exit(0)

if not last_usage:
    sys.exit(0)

tokens = int(
    (last_usage.get("input_tokens") or 0)
    + (last_usage.get("cache_read_input_tokens") or 0)
    + (last_usage.get("cache_creation_input_tokens") or 0)
)

# 상한 - 정본은 statusline_context.py 가 기록한 .claude/state/context-limit.json.
# 이유: jsonl 의 message.model 은 "claude-opus-5" 로만 기록되어 "[1m]" 접미가 없다.
#       그래서 model_id 만 보면 1M 세션을 200K 로 오판 -> 93% 허위 경보 (2026-09-05 실측).
limit = None
try:
    with open(os.path.join(cwd, ".claude", "state", "context-limit.json"), encoding="utf-8") as f:
        limit = int(json.load(f).get("limit") or 0) or None
except Exception:
    pass
if not limit:
    # fallback - 정본 없을 때만 휴리스틱
    limit = 1_000_000 if ("[1m]" in (model_id or "") or tokens > 200_000) else 200_000
pct = tokens / limit * 100

# 2026-10-06 실측 (이 PC compact 29건): 소요가 토큰에 비례하지 않는다 —
#   21만 91s · 33만 169s · 56만 211s · 97~100만(자동) 중앙 173s. 50% 조기 compact 는 1회 시간은 같고 횟수만 2배.
#   → 90%+ 는 «작업 단위가 끝났으면 /clear (0초 · resume-last-24h 가 자동 복구)», 진행 중이면 97% 자동 compact 대기.
if pct >= 90:
    print(f"[!!] 토큰 {pct:.0f}% ({tokens:,}/{limit:,}) - 작업 단위가 끝났으면 /clear 권장 (0초 · 새 세션이 최근 24h 작업 자동 복구). 진행 중이면 그대로 - 97% 에서 자동 compact (실측 중앙 173초).")
elif pct >= 75:
    print(f"[!] 토큰 {pct:.0f}% ({tokens:,}/{limit:,}) - 다음 작업 단위 경계에서 /clear 권장. 조기 /compact 는 빨라지지 않음 (실측 56만 토큰 211초).")
elif pct >= 60:
    print(f"[i] 토큰 {pct:.0f}% - compact 임박. 앞으로 큰 파일 read 자제.")
PYEOF
exit 0
