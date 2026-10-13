"""UserPromptSubmit ??紐⑤뱢 怨듭슜 ?꾧뎄 ??ctx 쨌 ?낅젰 異붿텧 쨌 寃쎈줈 쨌 ?뚯씪 ?곌린 쨌 ?ㅽ겕由쏀듃 濡쒕뜑.

媛???紐⑤뱢 (.claude/hooks/prompt/<?대쫫>.py) ? run(ctx) 瑜??몄텧?쒕떎.
  諛섑솚: str (additionalContext ?띿뒪?? | dict ({"additionalContext":..., "systemMessage":...}) | None (??留??놁쓬)
prompt-dispatch.py 媛 紐⑤뱢??settings ?쒖꽌?濡?import ???ㅽ뻾?섍퀬 寃곌낵瑜??⑹튇??
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

# ???ㅽ겕由쏀듃 ?꾩튂 湲곗? (?먮낯 .sh ??$(dirname "$0")/../.. ? ?숈씪)
HOOKS_DIR = Path(os.path.abspath(__file__)).parent.parent
ROOT = HOOKS_DIR.parent.parent
SCRIPTS_DIR = ROOT / ".claude" / "scripts"


class Ctx:
    """??怨듭슜 ?낅젰 ??stdin ? ??踰덈쭔 ?쎌뼱 紐⑤뱺 紐⑤뱢??怨듭쑀?쒕떎."""

    def __init__(self, raw: str) -> None:
        self.raw = raw
        # bash $(cat) ? ?앹쓽 媛쒗뻾??吏?대떎 ??JSON ?먮Ц??洹몃?濡?留ㅼ묶?섎뜕 ?낆슜
        self.raw_stripped = raw.rstrip("\n")
        self.parse_error = ""          # json.loads(stdin or '{}') 諛⑹떇 (save-user-prompt)
        payload = None
        try:
            payload = json.loads(raw or "{}")
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:  # ?먮낯???뚯떛 ?ㅽ뙣 ??議곗슜??鍮?媛?            self.parse_error = str(e)
        # json.load(stdin) 諛⑹떇 ??鍮??낅젰???ㅻ쪟 (lookup-history)
        self.parse_error_strict = "Expecting value: line 1 column 1 (char 0)" if raw.strip() == "" else self.parse_error
        self.payload = payload if isinstance(payload, dict) else {}
        # ${CLAUDE_PROJECT_DIR:-$PWD}
        self.project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        self.root = ROOT
        self.debug = False
        self.hook = ""
        self.marks: dict[str, list[tuple[str, float]]] = {}
        self._t0 = time.perf_counter()

    # ?섏쐞 ?④퀎 ?쒓컙 湲곕줉 (濡쒓렇??hook:label=ms 濡??⑤뒗??
    def mark(self, label: str) -> None:
        self.marks.setdefault(self.hook, []).append((label, (time.perf_counter() - self._t0) * 1000))

    def start_hook(self, name: str) -> None:
        self.hook = name
        self._t0 = time.perf_counter()

    def has_plugins(self) -> bool:
        """?쒕툕?꾨줈?앺듃 媛????plugins/ ?놁쑝硫?kit ??skip."""
        return os.path.isdir(os.path.join(self.project_dir, "plugins"))

    def field(self, *keys: str) -> str:
        """d.get(k1) or d.get(k2) or '' (泥?踰덉㎏ truthy 媛?."""
        for k in keys:
            v = self.payload.get(k)
            if v:
                return v if isinstance(v, str) else str(v)
        return ""

    def prompt_jq(self) -> str:
        """jq -r '.prompt // ""' ? ?숈씪 (null/false -> 鍮?臾몄옄??."""
        v = self.payload.get("prompt")
        if v is None or v is False:
            return ""
        return v if isinstance(v, str) else str(v)


# 2026-10-03/05 (69ad9c9): /loop(Cron) ?꾨＼?꾪듃("[LOOP] ...") 쨌 諛곌꼍 ?묒뾽 ?뚮┝(<task-notification>) ? ?щ엺 ?낅젰???꾨땲??
# stdin JSON ?먮Ц?먯꽌 "prompt" 媛믪쓽 ?쒖옉??蹂몃떎 (?먮낯 _LOOP_RE ? ?숈씪).
LOOP_RE = r'"prompt"\s*:\s*"(\[LOOP\] |<task-notification>)'


def is_loop_prompt_raw(raw: str) -> bool:
    return re.search(LOOP_RE, raw, re.S) is not None


def is_loop_prompt(prompt: str) -> bool:
    """PROMPT 媛??먯껜媛 [LOOP] / <task-notification> 濡??쒖옉 (?먮낯 `== "[LOOP]"*` ?⑦꽩)."""
    return prompt.startswith("[LOOP]") or prompt.startswith("<task-notification>")


def bash_strip(s: str) -> str:
    """bash $(...) ???앹쓽 媛쒗뻾留??쒓굅."""
    return s.rstrip("\n")


def head_bytes(s: str, n: int) -> str:
    """head -c N (諛붿씠??湲곗? ?먮쫫 쨌 湲??以묎컙?먯꽌 ?섎━硫?源⑥쭊 諛붿씠?몃? 洹몃?濡??붾떎 ???먮낯 ?숈씪)."""
    return s.encode("utf-8", "replace")[:n].decode("utf-8", "surrogateescape")


def _enc(text: str) -> bytes:
    """head_bytes 媛 ?④릿 源⑥쭊 諛붿씠??surrogateescape)瑜??먮옒 諛붿씠?몃줈 ?섎룎???대떎."""
    try:
        return text.encode("utf-8", "surrogateescape")
    except UnicodeEncodeError:
        return text.encode("utf-8", "replace")


def msys_path(p) -> str:
    """Git Bash pwd ?쒓린 (C:\\a\\b -> /c/a/b) ???먮낯 ?낆씠 異쒕젰?섎뜕 寃쎈줈 ?뺤떇 ?좎?."""
    s = str(p)
    if os.name == "nt" and len(s) > 1 and s[1] == ":":
        return "/" + s[0].lower() + s[2:].replace("\\", "/")
    return s


def search(pattern: str, text: str, ignorecase: bool = False) -> bool:
    """bash [[ =~ ]] (POSIX ERE 쨌 . 媛 媛쒗뻾??留ㅼ튂) ???遺덈━??留ㅼ튂."""
    return re.search(pattern, text, re.S | (re.I if ignorecase else 0)) is not None


def append_text(path, text: str) -> None:
    """諛붿씠?덈━ append (Windows ?띿뒪??紐⑤뱶 媛쒗뻾 蹂??諛⑹? 쨌 bash >> ? ?숈씪)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "ab") as f:
        f.write(_enc(text))


def write_text(path, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as f:
        f.write(_enc(text))


def read_text(path) -> str:
    return Path(path).read_bytes().decode("utf-8", "replace")


def read_lines(path) -> list[str]:
    """bash mapfile -t (媛쒗뻾?쇰줈留?遺꾨━ 쨌 ??媛쒗뻾? ??ぉ ?꾨떂)."""
    data = read_text(path)
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def ts_local(fmt: str) -> str:
    return time.strftime(fmt)


def ts_iso_tz() -> str:
    """printf '%(%FT%T%z)T' -1 ? ?숈씪 (+0900)."""
    lt = time.localtime()
    off = lt.tm_gmtoff or 0
    sign = "+" if off >= 0 else "-"
    off = abs(off)
    return time.strftime("%Y-%m-%dT%H:%M:%S", lt) + f"{sign}{off // 3600:02d}{(off % 3600) // 60:02d}"


_SCRIPT_CACHE: dict[str, object] = {}


def load_script(name: str):
    """.claude/scripts/<name>.py (?섏씠???뚯씪紐??ы븿) 瑜?in-process 濡?濡쒕뱶. ?놁쑝硫?None."""
    if name in _SCRIPT_CACHE:
        return _SCRIPT_CACHE[name]
    path = SCRIPTS_DIR / (name + ".py")
    mod = None
    if path.is_file():
        spec = importlib.util.spec_from_file_location("pd_" + re.sub(r"\W", "_", name), str(path))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    _SCRIPT_CACHE[name] = mod
    return mod

