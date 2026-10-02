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

# 2026-09-19: "mtime 최신 jsonl" 을 처음부터 끝까지 읽다가 306MB /loop 세션에서 3.2초 → 3초 타임아웃으로 매번 취소돼
# 압축 알림이 한 번도 안 갔다. stdin 의 transcript_path 가 정본이고, 마지막 usage 는 꼬리 4MB 안에 있다.
INPUT="$(cat 2>/dev/null || true)"
export CLAUDE_TRANSCRIPT_PATH="$(printf '%s' "$INPUT" | "$PY" -X utf8 -c "import json,sys
try: print(json.load(sys.stdin).get('transcript_path') or '', end='')
except Exception: pass" 2>/dev/null)"

# 최근 assistant usage 에서 토큰 사용률 계산
"$PY" -X utf8 - <<'PYEOF' 2>/dev/null
import json, os, glob, re, sys, subprocess

home = os.path.expanduser("~")
cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
safe = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
proj = os.path.join(home, ".claude", "projects", safe)
if not os.path.isdir(proj):
    sys.exit(0)
own = os.environ.get("CLAUDE_TRANSCRIPT_PATH", "")
if own and os.path.isfile(own):
    jsonls = [own]
else:
    jsonls = sorted(glob.glob(os.path.join(proj, "*.jsonl")), key=os.path.getmtime, reverse=True)
if not jsonls:
    sys.exit(0)
last_usage = None
model_id = ""
try:
    # 꼬리 4MB 만 읽는다 — 마지막 assistant usage 만 필요하고, 300MB 를 다 읽으면 3초 타임아웃에 걸린다.
    # 꼬리에 없으면(뒤가 attachment 뿐인 세션) 64MB 로 한 번 더.
    for TAIL in (4 * 1024 * 1024, 64 * 1024 * 1024):
        with open(jsonls[0], "rb") as fb:
            fb.seek(0, 2)
            size = fb.tell()
            fb.seek(max(0, size - TAIL))
            chunk = fb.read().decode("utf-8", errors="replace")
        lines = chunk.split("\n")[1:] if size > TAIL else chunk.split("\n")
        for line in reversed(lines):
            if '"type":"assistant"' not in line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            u = ((rec.get("message") or {}).get("usage")) or None
            # 전부 0 인 usage(한도 초과 안내 등) 는 건너뛰고 직전 실제 응답을 쓴다
            if u and ((u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
                      + (u.get("cache_creation_input_tokens") or 0)) > 0:
                last_usage = u
                model_id = ((rec.get("message") or {}).get("model")) or ""
                break
        if last_usage or size <= TAIL:
            break
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

if pct >= 90:
    print(f"[!!] 토큰 {pct:.0f}% ({tokens:,}/{limit:,}) - /compact 즉시 실행 필수. 다음 응답 전 반드시. 컨텍스트 폭주 임박.")
elif pct >= 75:
    print(f"[!] 토큰 {pct:.0f}% ({tokens:,}/{limit:,}) - /compact 준비. 응답이 느려지거나 멍청해지면 즉시 실행.")
elif pct >= 60:
    print(f"[i] 토큰 {pct:.0f}% - compact 임박. 앞으로 큰 파일 read 자제.")
PYEOF
exit 0
