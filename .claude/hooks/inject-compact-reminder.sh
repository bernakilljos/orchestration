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
# 2026-10-06 — 처음부터 끝까지 읽으면 세션 jsonl(121MB 실측)에서 10초+ → timeout.
#   필요한 건 마지막 assistant usage 하나뿐이라 끝에서부터 256KB 씩 거꾸로 읽고 찾으면 즉시 멈춘다.
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
            tail = lines[0] if pos > 0 else b""   # 잘린 첫 줄은 다음 블록과 이어 붙임
            for raw in reversed(lines[1:] if pos > 0 else lines):
                if b'"assistant"' not in raw:
                    continue
                try:
                    rec = json.loads(raw.decode("utf-8", errors="replace"))
                except Exception:
                    continue
                if rec.get("type") == "assistant":
                    msg = rec.get("message") or {}
                    if msg.get("usage"):
                        last_usage = msg["usage"]
                        model_id = msg.get("model") or ""
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

# 2026-10-06 실측 (이 PC compact 29건): 소요가 토큰에 비례하지 않는다 —
#   21만 91s · 33만 169s · 56만 211s · 97~100만(자동) 중앙 173s. 50% 조기 compact 는 1회 시간은 같고 횟수만 2배.
#   → 90%+ 는 «작업 단위가 끝났으면 /clear (0초 · resume-last-24h 가 자동 복구)», 진행 중이면 97% 자동 compact 대기.
RED = "\033[1;31m"; YEL = "\033[1;33m"; RST = "\033[0m"

# /clear 안전 판정 (ICM·RMS 세션 개선 1006 을 일반화해 역병합)
#   Claude 는 /clear 를 누를 수 없다 → 대신 «지금 눌러도 되는가»를 실측해 단정한다.
#   잃으면 복구 못 하는 것 = 추적 중 파일의 미커밋 수정(M/A/D/R). 미추적(??)은 /clear 로 사라지지 않으므로 제외.
#   저장소 = 프로젝트 루트, 루트가 저장소가 아니면 바로 아래 하위 저장소들 (특정 폴더명 하드코딩 X).
def _safe_to_clear(root):
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
        lost = [q for q in lost if not q.startswith(("docs/deploy-history/",))]   # hook 자동 기록은 제외
        if lost:
            head = ", ".join(lost[:3]) + (f" 외 {len(lost) - 3}" if len(lost) > 3 else "")
            reasons.append(f"{os.path.basename(repo)} 미커밋 {len(lost)}건({head})")
    if reasons:
        return (False, " · ".join(reasons))
    return (True, "미커밋 0")

if pct >= 75:
    ok, why = _safe_to_clear(cwd)
    if ok is True:
        verdict = f"지금 /clear 해도 안전 ({why}) - 0초에 비워지고 새 세션이 최근 24h 작업 자동 복구."
    elif ok is False:
        verdict = f"지금은 /clear 보류 - {why}. 커밋 먼저."
    else:
        verdict = f"/clear 안전 판정 불가 ({why})."
    if pct >= 90:
        print(f"{RED}[!!] 토큰 {pct:.0f}% ({tokens:,}/{limit:,}) - {verdict} 진행 중이면 그대로 - 97% 자동 compact (실측 중앙 173초).{RST}")
    else:
        print(f"{YEL}[!] 토큰 {pct:.0f}% ({tokens:,}/{limit:,}) - 작업 경계에서 /clear 권장 · {verdict} 조기 /compact 는 빨라지지 않음 (실측 56만 토큰 211초).{RST}")
elif pct >= 60:
    print(f"[i] 토큰 {pct:.0f}% - compact 임박. 앞으로 큰 파일 read 자제.")
PYEOF
exit 0
