"""detect-demo-pattern.sh 이식 - 데모/목업 패턴 감지 (systemMessage + .claude/logs/demo-pattern.log).

원본 grep -E 의 quirk 를 그대로 둔다: 대괄호 안의 x27 이스케이프나 [:s] 이스케이프는 grep 에서 백슬래시 · x · 2 · 7 / 콜론 · 백슬래시 · s 문자 집합이다.
"""
from __future__ import annotations

import os
import re
import time
from datetime import datetime

from _common import Result, Spawn, append_text, bash_cat, ensure_dir, glob_any, grep_o_first, has_jq, root_path

REL = ".claude/hooks/detect-demo-pattern.sh"
_FILE_RX = re.compile(r'"file_path"[ \t\r\f\v]*:[ \t\r\f\v]*"([^"]+)"')

_Q = r'["\\x27]'  # 원본 ["\x27] 와 같은 문자 집합 (따옴표 · 역슬래시 · x · 2 · 7)
_PATTERNS = [
    ("\\n  - 하드코딩 sample/mock 배열 (const mockX / sampleY / dummyZ)",
     r"^\s*(const|let|var)\s+(mock|sample|dummy|fake|example|test)[A-Z][a-zA-Z]*\s*=\s*\[", 0),
    ("\\n  - 하드코딩 상수 배열 (MOCK_USERS / SAMPLE_DATA 등)",
     r"^\s*(MOCK|SAMPLE|DUMMY|FAKE|EXAMPLE)_[A-Z_]+\s*=\s*\[", 0),
    ("\\n  - Stub return (status: ok 만 리턴)",
     r"return\s+\{\s*" + _Q + r"status" + _Q + r"\s*:\s*" + _Q + r"ok" + _Q + r"\s*\}\s*$", 0),
    ("\\n  - TODO connect real DB/API (스텁 상태 자백)",
     r"TODO[:\\s]+(connect|integrate|hook up|wire up|replace with)\s+(real|actual|production|prod)", re.I),
    ("\\n  - '시연/데모/MVP 정도' 주석 (실전 위반 자각)",
     r"(^|\s)#.*시연|(^|\s)//.*시연|(^|\s)#.*데모|(^|\s)//.*데모|MVP\s*정도", 0),
    ("\\n  - dummy email/domain (example@example.com 등)",
     _Q + r"(example|test|dummy|fake)@(example|test)\.(com|org)" + _Q, 0),
]
_COMPILED = None


def _compiled():
    global _COMPILED
    if _COMPILED is None:
        _COMPILED = [(msg, re.compile(p.encode("utf-8"), fl)) for msg, p, fl in _PATTERNS]
    return _COMPILED


def run(ctx):
    if has_jq():  # jq 환경은 출력 형식이 달라 원본에 위임
        return Spawn(REL)
    root = root_path()
    log_dir = os.path.join(root, ".claude", "logs")
    ensure_dir(log_dir)
    inp = bash_cat(ctx.raw)
    m = None
    for line in inp.split("\n"):
        m = _FILE_RX.search(line)
        if m:
            break
    fp = m.group(1) if m else ""
    if glob_any(fp, "*.md", "*.txt", "*.rst", "*.log", "*.json", "*/memory/*", "*/docs/*", "*/rules/*",
                "*/skills/*", "*/hooks/*"):
        return None
    if not os.path.isfile(fp):
        return None
    flag = os.path.join(root, ".claude", "state", "demo-mode-approved")
    if os.path.isfile(flag):
        try:
            age = int(time.time()) - int(os.stat(flag).st_mtime)
        except OSError:
            age = int(time.time())
        if age < 14400:
            return None
    try:
        with open(fp, "rb") as f:
            data = f.read()
    except OSError:
        return None
    lines = data.split(b"\n")
    matches = ""
    for msg, rx in _compiled():
        if any(rx.search(ln) for ln in lines):
            matches += msg
    if not matches:
        return None
    # 로그: printf '%b\n' "$MATCHES" -> \n 을 실제 개행으로
    ts = datetime.now().astimezone().isoformat(timespec="seconds")
    append_text(os.path.join(log_dir, "demo-pattern.log"), "[%s] %s 데모 패턴 감지\n" % (ts, fp))
    append_text(os.path.join(log_dir, "demo-pattern.log"), matches.replace("\\n", "\n") + "\n")
    msg = ("[[WARN] 데모/목업 패턴 감지 — %s]%s\\n\\n실전 원칙 위반 가능성. 사용자가 '목업/데모/시연/MVP' 명시 안 했으면 "
           "실전으로 재작성 필요.\\n승인 시 4시간 skip: touch .claude/state/demo-mode-approved") % (fp, matches)
    esc = msg.replace("\\", "\\\\").replace('"', '\\"') + "\\n"
    return Result(0, '{"systemMessage":"%s"}\n' % esc, "")
