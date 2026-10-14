"""UserPromptSubmit 훅 모듈 공용 도구 — ctx · 입력 추출 · 경로 · 파일 쓰기 · 스크립트 로더.

각 훅 모듈 (.claude/hooks/prompt/<이름>.py) 은 run(ctx) 를 노출한다.
  반환: str (additionalContext 텍스트) | dict ({"additionalContext":..., "systemMessage":...}) | None (할 말 없음)
prompt-dispatch.py 가 모듈을 settings 순서대로 import 해 실행하고 결과를 합친다.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

# 훅 스크립트 위치 기준 (원본 .sh 의 $(dirname "$0")/../.. 와 동일)
HOOKS_DIR = Path(os.path.abspath(__file__)).parent.parent
ROOT = HOOKS_DIR.parent.parent
SCRIPTS_DIR = ROOT / ".claude" / "scripts"


class Ctx:
    """훅 공용 입력 — stdin 은 한 번만 읽어 모든 모듈이 공유한다."""

    def __init__(self, raw: str) -> None:
        self.raw = raw
        # bash $(cat) 은 끝의 개행을 지운다 — JSON 원문을 그대로 매칭하던 훅용
        self.raw_stripped = raw.rstrip("\n")
        self.parse_error = ""          # json.loads(stdin or '{}') 방식 (save-user-prompt)
        payload = None
        try:
            payload = json.loads(raw or "{}")
        except Exception as e:  # 원본도 파싱 실패 시 조용히 빈 값
            self.parse_error = str(e)
        # json.load(stdin) 방식 — 빈 입력도 오류 (lookup-history)
        self.parse_error_strict = "Expecting value: line 1 column 1 (char 0)" if raw.strip() == "" else self.parse_error
        self.payload = payload if isinstance(payload, dict) else {}
        # ${CLAUDE_PROJECT_DIR:-$PWD}
        self.project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        self.root = ROOT
        self.debug = False
        self.hook = ""
        self.marks: dict[str, list[tuple[str, float]]] = {}
        self._t0 = time.perf_counter()

    # 하위 단계 시간 기록 (로그에 hook:label=ms 로 남는다)
    def mark(self, label: str) -> None:
        self.marks.setdefault(self.hook, []).append((label, (time.perf_counter() - self._t0) * 1000))

    def start_hook(self, name: str) -> None:
        self.hook = name
        self._t0 = time.perf_counter()

    def has_plugins(self) -> bool:
        """서브프로젝트 가드 — plugins/ 없으면 kit 훅 skip."""
        return os.path.isdir(os.path.join(self.project_dir, "plugins"))

    def field(self, *keys: str) -> str:
        """d.get(k1) or d.get(k2) or '' (첫 번째 truthy 값)."""
        for k in keys:
            v = self.payload.get(k)
            if v:
                return v if isinstance(v, str) else str(v)
        return ""

    def prompt_jq(self) -> str:
        """jq -r '.prompt // ""' 와 동일 (null/false -> 빈 문자열)."""
        v = self.payload.get("prompt")
        if v is None or v is False:
            return ""
        return v if isinstance(v, str) else str(v)


# 2026-10-03/05 (69ad9c9): /loop(Cron) 프롬프트("[LOOP] ...") · 배경 작업 알림(<task-notification>) 은 사람 입력이 아니다.
# stdin JSON 원문에서 "prompt" 값의 시작을 본다 (원본 _LOOP_RE 와 동일).
LOOP_RE = r'"prompt"\s*:\s*"(\[LOOP\] |<task-notification>)'


def is_loop_prompt_raw(raw: str) -> bool:
    return re.search(LOOP_RE, raw, re.S) is not None


def is_loop_prompt(prompt: str) -> bool:
    """PROMPT 값 자체가 [LOOP] / <task-notification> 로 시작 (원본 `== "[LOOP]"*` 패턴)."""
    return prompt.startswith("[LOOP]") or prompt.startswith("<task-notification>")


def bash_strip(s: str) -> str:
    """bash $(...) — 끝의 개행만 제거."""
    return s.rstrip("\n")


def head_bytes(s: str, n: int) -> str:
    """head -c N (바이트 기준 자름 · 글자 중간에서 잘리면 깨진 바이트를 그대로 둔다 — 원본 동일)."""
    return s.encode("utf-8", "replace")[:n].decode("utf-8", "surrogateescape")


def _enc(text: str) -> bytes:
    """head_bytes 가 남긴 깨진 바이트(surrogateescape)를 원래 바이트로 되돌려 쓴다."""
    try:
        return text.encode("utf-8", "surrogateescape")
    except UnicodeEncodeError:
        return text.encode("utf-8", "replace")


def msys_path(p) -> str:
    """Git Bash pwd 표기 (C:\\a\\b -> /c/a/b) — 원본 훅이 출력하던 경로 형식 유지."""
    s = str(p)
    if os.name == "nt" and len(s) > 1 and s[1] == ":":
        return "/" + s[0].lower() + s[2:].replace("\\", "/")
    return s


def search(pattern: str, text: str, ignorecase: bool = False) -> bool:
    """bash [[ =~ ]] (POSIX ERE · . 가 개행도 매치) 대응 불리언 매치."""
    return re.search(pattern, text, re.S | (re.I if ignorecase else 0)) is not None


def append_text(path, text: str) -> None:
    """바이너리 append (Windows 텍스트 모드 개행 변환 방지 · bash >> 와 동일)."""
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
    """bash mapfile -t (개행으로만 분리 · 끝 개행은 항목 아님)."""
    data = read_text(path)
    lines = data.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def ts_local(fmt: str) -> str:
    return time.strftime(fmt)


def ts_iso_tz() -> str:
    """printf '%(%FT%T%z)T' -1 와 동일 (+0900)."""
    lt = time.localtime()
    off = lt.tm_gmtoff or 0
    sign = "+" if off >= 0 else "-"
    off = abs(off)
    return time.strftime("%Y-%m-%dT%H:%M:%S", lt) + f"{sign}{off // 3600:02d}{(off % 3600) // 60:02d}"


_SCRIPT_CACHE: dict[str, object] = {}


def load_script(name: str):
    """.claude/scripts/<name>.py (하이픈 파일명 포함) 를 in-process 로 로드. 없으면 None."""
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


# ============================================================================
# 도구 훅 (PreToolUse / PostToolUse) 공용 — .claude/hooks/tool-dispatch.py + .claude/hooks/tool/*.py
# 각 모듈은 run(ctx) -> Result | Spawn | None.  (None = 무출력 · exit 0)
# 원본 bash 훅이 JSON 원문을 bash 내장·grep·sed 로 뽑던 방식을 그대로 재현한다 (이스케이프된 \ 포함).
# ============================================================================
import fnmatch
import subprocess


class Result:
    """훅 1개의 실행 결과 — 원본 프로세스의 (exit code, stdout, stderr) 와 같은 의미."""

    __slots__ = ("rc", "out", "err")

    def __init__(self, rc: int = 0, out: str = "", err: str = "") -> None:
        self.rc = rc
        self.out = out
        self.err = err


class Spawn:
    """드물게만 타는 무거운 경로(git 커밋·외부 도구 호출) — 원본 스크립트를 그대로 실행한다.

    디스패처가 병렬로 띄우고 수거한다 (원본이 동시 실행이던 것과 동일).
    rel: 프로젝트 루트 기준 스크립트 경로 · args: 원본이 받던 인자 (settings 의 "$FILE" 등)
    """

    __slots__ = ("rel", "args")

    def __init__(self, rel: str, args: tuple = ()) -> None:
        self.rel = rel
        self.args = tuple(args)


def tool_name(ctx) -> str:
    return ctx.field("tool_name", "toolName")


def tool_input(ctx) -> dict:
    ti = ctx.payload.get("tool_input")
    return ti if isinstance(ti, dict) else {}


def bash_cat(raw: str) -> str:
    """INPUT=$(cat) — 끝의 개행만 제거."""
    return raw.rstrip("\n")


def bash_read(raw: str) -> str:
    """read -r -d '' INPUT — 앞뒤 IFS 공백(스페이스·탭·개행) 제거."""
    return raw.strip(" \t\n")


def bash_field(inp: str, key: str) -> str:
    """${INPUT#*"key":} → 앞 따옴표 제거 → 앞 ' "' 제거 → 첫 따옴표 이후 제거 (bash 내장 치환 체인)."""
    tag = '"%s":' % key
    i = inp.find(tag)
    v = inp[i + len(tag):] if i >= 0 else inp
    if v.startswith('"'):
        v = v[1:]
    if v.startswith(' "'):
        v = v[2:]
    j = v.find('"')
    return v[:j] if j >= 0 else v


def bash_basename(s: str) -> str:
    r"""Git Bash(msys) basename — / 와 \ 둘 다 구분자, 끝의 구분자 무시."""
    t = s.rstrip("/\\")
    if not t:
        return "/" if s else ""
    k = max(t.rfind("/"), t.rfind("\\"))
    return t[k + 1:]


def glob_any(s: str, *patterns: str) -> bool:
    """bash case 글롭 — * 는 / 도 매치."""
    return any(fnmatch.fnmatchcase(s, p) for p in patterns)


_WS = r"[ \t\r\f\v]"


def sed_json_value(inp: str, key: str):
    r"""echo $INPUT | sed -n 's/.*"key"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1."""
    rx = re.compile(r'.*"%s"%s*:%s*"([^"]*)"' % (key, _WS, _WS))
    for line in inp.split("\n"):
        m = rx.match(line)
        if m:
            return m.group(1)
    return None


def grep_o_first(inp: str, pattern: str):
    """grep -oE PATTERN | head -1 (줄 단위 · 첫 매치 전체 텍스트)."""
    rx = re.compile(pattern)
    for line in inp.split("\n"):
        m = rx.search(line)
        if m:
            return m.group(0)
    return None


def grep_key_value_a(inp: str, key: str) -> str:
    r"""grep -oE '"key"\s*:\s*"[^"]+' | head -1 | sed 's/.*"\([^"]*\)$/\1/' → 값 (없으면 빈 문자열)."""
    m = grep_o_first(inp, r'"%s"[ \t\r\f\v]*:[ \t\r\f\v]*"[^"]+' % key)
    if m is None:
        return ""
    return m[m.rfind('"') + 1:]


def grep_key_value_b(inp: str, key: str) -> str:
    r"""grep -oE '"key"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/' → 값."""
    m = grep_o_first(inp, r'"%s"[ \t\r\f\v]*:[ \t\r\f\v]*"[^"]+"' % key)
    if m is None:
        return ""
    mm = re.match(r'.*"([^"]*)"$', m)
    return mm.group(1) if mm else m


def project_guard(ctx) -> bool:
    """[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] — 서브프로젝트 가드 (없으면 False)."""
    return ctx.has_plugins()


def ensure_dir(path) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        pass


def project_path(ctx, *parts: str) -> str:
    """${CLAUDE_PROJECT_DIR:-$PWD}/... (환경변수 기준 — 훅 스크립트 위치 기준이 아님)."""
    return os.path.join(ctx.project_dir, *parts)


def root_path(*parts: str) -> str:
    """훅 스크립트 위치 기준 PROJECT_ROOT/... (원본의 $(dirname "$0")/../.. 와 동일)."""
    return os.path.join(str(ROOT), *parts)


def run_script_text(cmd: list, stdin_text: str = "", cwd=None, timeout: float = 30.0):
    """보조 프로세스 실행 → (rc, stdout, stderr) 문자열. 드문 경로 전용."""
    p = subprocess.run(cmd, input=stdin_text.encode("utf-8", "replace"), capture_output=True,
                       cwd=cwd, timeout=timeout)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def write_dispatch_log(path: str, lines: list, max_bytes: int = 1_000_000, keep: int = 3000) -> None:
    """디스패처 로그 append (크기 상한 초과 시 끝 N줄만 유지)."""
    try:
        ensure_dir(os.path.dirname(path))
        if os.path.exists(path) and os.path.getsize(path) > max_bytes:
            with open(path, "rb") as f:
                tail = f.read().splitlines()[-keep:]
            with open(path, "wb") as f:
                f.write(b"\n".join(tail) + b"\n")
        with open(path, "ab") as f:
            f.write(("\n".join(lines) + "\n").encode("utf-8", "replace"))
    except Exception:
        pass  # noqa: BLE001


_JQ = []


def has_jq() -> bool:
    """command -v jq — jq 가 있으면 원본 훅이 다른 분기(jq 파서)를 타므로, 그런 훅은 원본 스크립트로 위임한다."""
    if not _JQ:
        import shutil

        _JQ.append(shutil.which("jq") is not None)
    return _JQ[0]
