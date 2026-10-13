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
