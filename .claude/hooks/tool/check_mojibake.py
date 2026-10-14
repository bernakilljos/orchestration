"""check-mojibake.sh 이식 — U+FFFD · cp949 오인 패턴 감지 시 deny (항상 {"continue": true} 또는 deny JSON 출력)."""
from __future__ import annotations

import json
import re

from _common import Result, bash_read

_BS = "\\"
_REPL = "\ufffd"
_REPL_ESC = _BS + "u" + "fffd"
_REPL_ESC_UC = _BS + "u" + "FFFD"
_U00 = _BS + "u00"
_LATIN = "ÂÃàáâãäåæçèéêëìíîïðñòó"
_P1 = re.compile(r"[ÂÃ][\x80-\xBF]{2,}")
_P2 = re.compile(r"[íìîïðñòó]{2,}")
_CONT = '{"continue": true}\n'
_DENY_REPL = ('{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny",'
              '"permissionDecisionReason":"한글 깨짐 감지 (U+FFFD). UTF-8 인코딩 확인 후 재시도."}}\n')
_DENY_MOJI = ('{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny",'
              '"permissionDecisionReason":"한글 깨짐 패턴 감지 (cp949 오인). UTF-8 로 재인코딩 후 재시도."}}\n')


def run(ctx):
    inp = bash_read(ctx.raw)
    if not inp:
        return Result(0, _CONT, "")
    # 1차 필터 — 깨짐 후보 문자가 없으면 판정 없이 통과
    cand = (_REPL in inp or _REPL_ESC in inp or _REPL_ESC_UC in inp or _U00 in inp
            or any(c in inp for c in _LATIN))
    if not cand:
        return Result(0, _CONT, "")
    try:
        d = json.loads(inp)
    except Exception:
        return Result(0, _CONT, "")
    ti = d.get("tool_input", {}) if isinstance(d, dict) else {}
    ti = ti or {}
    txt = ti.get("content") or ti.get("new_string") or ""
    if not isinstance(txt, str) or not txt:
        return Result(0, _CONT, "")
    if _REPL in txt:
        return Result(0, _DENY_REPL, "")
    if _P1.search(txt) or _P2.search(txt):
        return Result(0, _DENY_MOJI, "")
    return Result(0, _CONT, "")
