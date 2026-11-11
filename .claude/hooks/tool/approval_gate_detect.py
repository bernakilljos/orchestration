"""approval-gate-detect.sh 이식 (3184b27 판) - 위험 명령(5 카테고리) 감지 시 approval-gate 등록 + 차단 (exit 2).

위험 판정 detect_risk / 등록 request_approval 은 approval-gate.py 의 함수를 in-process 로 호출한다 (정본 1곳 · python 하위 프로세스 0개).
원본의 1차 필터(위험 단어가 하나도 없으면 python 을 띄우지 않고 통과) 도 같은 의미로 유지한다.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import traceback

from _common import Result, append_text, bash_read, ensure_dir, load_script, project_guard, project_path

_S = r"[ \t\n\r\f\v]"
_RISKWORD = re.compile(
    r"drop|truncate|delete|rm" + _S + r"|git" + _S + r"+(push|reset|branch)|sudo|curl|wget|runas|chmod|batch|daily-limit|setx|"
    r"reg" + _S + r"+(add|delete)|alembic|systemctl|npm" + _S + r"+publish|docker" + _S + r"+push|gh" + _S + r"+release|terraform|"
    r"\biex\b|invoke-expression|set-executionpolicy|setenvironmentvariable|verb" + _S + r"+runas|"
    # 2026-11-08 P0·P1 확장 (push 변형·자기 승인·직접 유료 호출·삭제·배포·DB·설정)
    r"push|clean|checkout|restore|stash|rmtree|remove-item|find|kubectl|vercel|netlify|firebase|scp|"
    r"codex|gemini|claude|anthropic|openai|googleapis|approv|reject|decide|update|insert|replace|dispatch|"
    r"settings|\.env|set-content|add-content|out-file|tee|cp" + _S + r"|mv" + _S + r"|copy|move",
    re.I)


def _extract_cmd(inp: str) -> str:
    # 2026-11-08: JSON 으로 읽는다 — 문자열 자르기는 명령 안의 \"} 에서 끊겨 뒷부분(실제 위험 명령)이 검사에서 빠졌다
    try:
        d = json.loads(inp)
    except ValueError:
        d = None
    if isinstance(d, dict):
        ti = d.get("tool_input") if isinstance(d.get("tool_input"), dict) else d
        if isinstance(ti.get("command"), str):
            return ti["command"]
    tag = '"command":'
    i = inp.find(tag)
    cmd = inp[i + len(tag):] if i >= 0 else inp
    if cmd.startswith('"'):
        cmd = cmd[1:]
    if cmd.startswith(' "'):
        cmd = cmd[2:]
    for sep in ('", "', '","', '"}'):
        j = cmd.find(sep)
        if j >= 0:
            cmd = cmd[:j]
    cmd = cmd.replace('\\"', '"')     # JSON 의 \" -> "
    cmd = cmd.replace("\\\\", "\\")   # JSON 의 \\ -> \
    return cmd


def _strip_git_commit_message(cmd: str) -> str:
    """2026-10-26 외부 AI 지적: git commit -m 안 message body (문자열 '언급') 는 실행 대상 X.
    실행 vs 언급 구분 — msg body 안 위험 문자열은 매칭 제외.
    "DROP TABLE DB 실행" (위험) vs "feat: DROP TABLE 패턴 fix" (문서 기록) 구분."""
    if not re.search(r'\bgit\s+commit\b', cmd):
        return cmd
    # 2026-11-09: 따옴표 친 구분자(<<'EOF')만 — 따옴표 없는 heredoc·큰따옴표 안의 $( ) ` 는 셸이 실행하므로 가리지 않는다
    # heredoc: -m "$(cat <<'EOF' ... EOF\n)"
    cmd2 = re.sub(
        r'-m\s+"\$\(cat\s+<<-?\s*([\'"])([A-Za-z0-9_]+)\1\s*\n.*?\n\2\s*\n\s*\)"',
        '-m "<MSG>"', cmd, flags=re.S
    )
    # heredoc: -F - <<'EOF' ... EOF (표준 입력으로 메시지)
    cmd2 = re.sub(
        r"(-F\s*-\s*)<<-?\s*(['\"])([A-Za-z0-9_]+)\2[^\n]*\n.*?\n\3(?=\s*(?:\n|$))",
        r"\1<<'MSG'\n<MSG>\nMSG", cmd2, flags=re.S
    )
    # 단순 -m "..." 또는 -m '...'
    cmd2 = re.sub(r'-m\s+"([^"]*)"', lambda m: m.group(0) if ("$(" in m.group(1) or "`" in m.group(1))
                  else '-m "<MSG>"', cmd2)
    cmd2 = re.sub(r"-m\s+'[^']*'", "-m '<MSG>'", cmd2)
    return cmd2


_SEARCH_CMDS = ("grep", "egrep", "fgrep", "rg", "ag", "findstr")


def _leading_cd_base(parts: list) -> str:
    """§84 첫 세그먼트가 `cd <절대 경로>` 이고 그 뒤에 작업 위치를 바꾸는 명령이 더 없으며 폴더가 실제로 있을 때만 그 경로.
    (2026-11-11 재현: `cd /c/pjt/orchestration_v1; python .claude/scripts/auto-save-next-actions.py manual-add "…Git…push…"`
     → 상대 경로라 인자를 글로 보지 못해 git push 로 판정)"""
    segs = [p for p in parts if p.strip() and not re.fullmatch(r"\s*(?:&&|\|\||;|\n)\s*", p)]
    if not segs:
        return ""
    m = re.fullmatch(r"\s*cd\s+(\"[^\"]+\"|'[^']+'|[^\s;&|]+)\s*", segs[0])
    if not m or any(_RX_CHDIR.search(x) for x in segs[1:]):
        return ""
    d = m.group(1).strip("\"'")
    d = re.sub(r"^/([a-zA-Z])/", r"\1:/", d)
    return d if os.path.isabs(d) and os.path.isdir(d) else ""


def _strip_inert_text(cmd: str) -> str:
    """2026-10-30: 실행되지 않는 '언급' 만 제외 (위험 명령 차단 자체는 그대로).
    ① cat 이 파일로만 쓰는 heredoc 본문 (`cat >> f <<'EOF' ... EOF`) — 파이프로 셸에 넘기면 제외 X
    ② 검색 명령(grep·rg 등) 세그먼트의 따옴표 검색어 — 같은 줄의 다른 명령 세그먼트는 그대로 검사
    bash/sh/python 등으로 실행되는 heredoc 은 손대지 않는다."""
    # hook 입력은 JSON 이라 줄바꿈이 '\\n' 문자로 들어온다 → 실제 줄바꿈으로 (실측: 미변환 시 heredoc 인식 0)
    cmd = cmd.replace("\\n", "\n").replace("\\t", "\t")

    def _heredoc(m):
        head = m.group(1)
        if ">" in head and "|" not in head:
            return f"{head}\n<DOC>\n{m.group(2)}"
        return m.group(0)
    cmd = re.sub(r"((?:^|(?<=[;&\n]))\s*cat\b[^\n]*?<<-?\s*['\"]?(\w+)['\"]?[^\n]*)\n.*?\n(\2)(?=\s*(?:\n|$))",
                 lambda m: _heredoc(type("M", (), {"group": lambda s, i: (m.group(0), m.group(1), m.group(3))[i]})()),
                 cmd, flags=re.S)
    parts = re.split(r"(\s*(?:&&|\|\||;|\n)\s*)", cmd)
    base = _leading_cd_base(parts)
    for i, seg in enumerate(parts):
        words = seg.strip().split()
        if words and os.path.basename(words[0]).lower() in _SEARCH_CMDS:
            parts[i] = re.sub(r"'[^']*'|\"[^\"]*\"", "'<PATTERN>'", seg)
        elif words and _inert_args_segment(seg, base):
            parts[i] = _RX_QUOTED.sub(_mask_inert_quote, seg)
    return "".join(parts)


# 2026-11-09: 실행되지 않는 인자 안의 '언급' (예: manual-add "… git push 승인 대기") 오탐.
#   문자열 제외가 아니라 «이 세그먼트는 인자를 실행하지 않는다» 가 확정될 때만 따옴표 안을 가린다:
#   ① 첫 명령이 출력 전용(echo·printf·Write-Host·Write-Output) 또는 허용 목록 kit 스크립트(HEAD 와 같은 내용)
#   ② 따옴표 밖에 파이프·리다이렉트·heredoc·명령 치환이 없음 ③ 따옴표 안에 명령 치환($( · `) 없음
#   셸·인터프리터 래퍼(bash -c · eval · python -c · cmd /c · powershell -Command · xargs) 는 해당 없음 → 그대로 검사.
_RX_QUOTED = re.compile(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"")
_INERT_LEADERS = {"echo", "printf", "write-host", "write-output"}
_INERT_KIT_SCRIPTS = {("auto-save-next-actions.py", "manual-add")}   # 인자를 파일에 글로만 적는 kit 스크립트
_RX_PY = re.compile(r"^(?:py|python(?:3(?:\.\d+)?)?)(?:w)?(?:\.exe)?$", re.I)


def _mask_inert_quote(m):
    q = m.group(0)
    if q.startswith('"') and ("$(" in q or "`" in q):
        return q
    return "'<TEXT>'"


_KIT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_PY_SAFE_FLAGS = {"-u", "-B", "-I", "-E", "-s", "-Xutf8"}


def _kit_script_unchanged(path: str) -> bool:
    """허용 kit 스크립트는 «이 kit 저장소의 그 파일» 이고 kit HEAD 와 내용이 같을 때만 (2026-11-09 리뷰 MUST 3:
    경로 끝만 보면 다른 저장소에 커밋한 같은 이름 스크립트가 통과). 확인 실패 = 해당 없음 (fail-closed)."""
    import subprocess
    try:
        name = os.path.basename(path)
        want = os.path.realpath(os.path.join(_KIT_ROOT, ".claude", "scripts", name))
        if os.path.normcase(os.path.realpath(path)) != os.path.normcase(want):
            return False
        kw = dict(cwd=_KIT_ROOT, capture_output=True, text=True, timeout=2)
        rel = ".claude/scripts/" + name
        head = subprocess.run(["git", "rev-parse", "HEAD:" + rel], **kw).stdout.strip()
        work = subprocess.run(["git", "hash-object", rel], **kw).stdout.strip()
        return bool(head) and head == work
    except Exception:  # noqa: BLE001
        return False


def _inert_args_segment(seg: str, base: str = "") -> bool:
    # §84 맨 끝 출력 다듬기(2>&1 · | tail/head -N)는 인자를 실행하지 않는다 — 그것만 떼고 판정 (다른 파이프는 그대로 불허)
    seg = re.sub(r"(?:\s+2>&1)?(?:\s*\|\s*(?:tail|head)(?:\s+-n)?\s+-?\d+)?\s*$", "", seg)
    skeleton = _RX_QUOTED.sub("''", seg)
    # 2026-11-09 리뷰 MUST 1·2: 셸이 따옴표 짝을 정규식과 다르게 읽는 문자(\ ^ $' $")·백그라운드 & ·
    #   짝 안 맞는 따옴표가 따옴표 밖에 있으면 판정하지 않는다 (가리지 않음 → 그대로 검사)
    if (re.search(r"[|<>`&^]|\$\(|\$'|\$\"", skeleton) or "\\" in skeleton   # 리뷰 재공격 MUST: ' 우회
            or skeleton.count("'") % 2 or '"' in skeleton):
        return False
    words = skeleton.split()
    env_prefix = False
    while words and re.match(r"^\w+=", words[0]):     # VAR=값 접두
        words = words[1:]
        env_prefix = True
    if not words:
        return False
    lead = words[0].lower()                            # 경로 붙은 ./echo · 가짜 python 은 해당 없음 (리뷰 재공격 SHOULD)
    if lead in _INERT_LEADERS:
        return True
    if not _RX_PY.match(lead) or env_prefix:          # PYTHONPATH= 등은 인자를 볼 코드를 바꿀 수 있음 (리뷰 SHOULD 4)
        return False
    raw_words = seg.split()
    while raw_words and re.match(r"^\w+=", raw_words[0]):
        raw_words = raw_words[1:]
    rest = raw_words[1:]
    while rest and rest[0].startswith("-"):           # 허용 옵션만 (리뷰 SHOULD 5) · -c·-m 등 나머지는 해당 없음
        if rest[0] == "-X" and len(rest) > 1 and rest[1] == "utf8":
            rest = rest[2:]
        elif rest[0] in _PY_SAFE_FLAGS:
            rest = rest[1:]
        else:
            return False
    if len(rest) < 2:
        return False
    script = re.sub(r"^/([a-zA-Z])/", r"\1:/", rest[0])
    name = os.path.basename(script).lower()
    if (name, rest[1].lower()) not in _INERT_KIT_SCRIPTS:
        return False
    # 상대 경로는 셸과 훅의 작업 위치가 다를 수 있어 해당 없음 (리뷰 SHOULD 6)
    #   §84: 명령 맨 앞 `cd <절대 경로>` 1회로 기준 폴더가 확정되면 그 기준으로 해석 (kit HEAD 내용 일치 조건 유지)
    if not os.path.isabs(script) and base:
        script = os.path.join(base, script)
    return os.path.isabs(script) and os.path.isfile(script) and _kit_script_unchanged(script)


_RX_SCRIPT = re.compile(r"""(?:"([^"]+\.(?:ps[dm]?1|py|sh|bat|cmd))"|'([^']+\.(?:ps[dm]?1|py|sh|bat|cmd))'|"""
                        r"""([^\s"'`;|&<>()]+\.(?:ps[dm]?1|py|sh|bat|cmd)))(?![\w.])""", re.I)


class _ArtifactRefused(Exception):
    """스크립트 내용을 확정할 수 없는 명령 — 승인으로 풀지 않고 차단 (사유를 사용자에게 그대로 보인다)."""


_RX_CHDIR = re.compile(r"(?:^|[;&|\n(]\s*)(?:cd|pushd|chdir|set-location|push-location|sl)\b|-workingdirectory\b", re.I)
_ART_MAX_FILES = 20
_ART_TIMEOUT_SEC = 2.5


def _artifacts(cmd: str, raw_cwd: str) -> dict:
    """명령이 실행하는 스크립트 파일의 sha256 (2026-11-09 · 승인 후 내용 변경 차단).
    없는 파일은 'missing' — 승인 때 없던 파일이 실행 때 생겨도 다름으로 잡힌다.
    확정할 수 없으면 _ArtifactRefused (2026-11-09 리뷰: UNC 경로 open 이 42초 걸려 훅 시간 초과 → 디스패처가 통과시킴 ·
    20개 초과를 조용히 버림 · cd 뒤 상대 경로는 다른 파일을 가리킴)."""
    import importlib.util  # Git Bash /c/… 경로·환경 변수·상대 경로 정규화 정본(ensure_ps1_bom._norm) 재사용
    import threading
    spec = importlib.util.spec_from_file_location(
        "_agd_ps1_bom", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ensure_ps1_bom.py"))
    bom = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bom)
    paths: list = []
    chdir = bool(_RX_CHDIR.search(cmd))
    for m in _RX_SCRIPT.finditer(cmd):
        raw = next(g for g in m.groups() if g).strip()
        expanded = os.path.expandvars(os.path.expanduser(raw))
        if expanded.startswith(("\\\\", "//")):  # UNC·\\?\·\\.\ 장치 경로 모두 여기 해당 — 열지 않는다
            raise _ArtifactRefused("네트워크·장치 경로 스크립트(%s)는 내용을 확정할 수 없음" % raw)
        if chdir and not (os.path.isabs(expanded) or re.match(r"^/[a-zA-Z]/", expanded)):
            raise _ArtifactRefused("작업 위치를 바꾸는 명령(cd 등)과 상대 경로 스크립트(%s)가 함께 있음 — 절대 경로로 실행" % raw)
        p = os.path.normcase(os.path.abspath(bom._norm(raw, raw_cwd or os.getcwd())))
        if p not in paths:
            paths.append(p)
    if len(paths) > _ART_MAX_FILES:
        raise _ArtifactRefused("실행 스크립트가 %d개로 상한 %d개 초과" % (len(paths), _ART_MAX_FILES))
    out: dict = {}

    def _hash_all():
        for p in paths:
            try:
                with open(p, "rb") as f:
                    out[p] = hashlib.sha256(f.read()).hexdigest()
            except OSError:
                out[p] = "missing"
        out["__done__"] = "1"

    th = threading.Thread(target=_hash_all, daemon=True)
    th.start()
    th.join(_ART_TIMEOUT_SEC)
    if out.pop("__done__", None) is None:
        raise _ArtifactRefused("스크립트 내용 확인이 %.1f초 안에 끝나지 않음 (네트워크 드라이브 등)" % _ART_TIMEOUT_SEC)
    return dict(out)


#: 2026-11-10 §75 — 실행하는 셸 스크립트의 «내용» 도 위험 판정 (종전엔 해시만 계산 · 명령줄이 `bash /abs/x.sh` 면
#:   1차 필터에서 바로 통과 → 스크립트 안 `claude -p`·전역 명령 덮어쓰기가 승인 없이 실행된 사고).
#:   .py 는 대상 아님 (시험 데이터 오탐 · 문자열 차단은 보안 근거 아님 — 알려진 한계) · $VAR 로 조립한 경로는 따라가지 못함.
_RX_SHELL_SCRIPT = re.compile(r"""(?:"([^"]+\.(?:ps[dm]?1|sh|bash|bat|cmd))"|'([^']+\.(?:ps[dm]?1|sh|bash|bat|cmd))'|"""
                              r"""([^\s"'`;|&<>()$]+\.(?:ps[dm]?1|sh|bash|bat|cmd)))(?![\w.])""", re.I)
_RX_CD_TARGET = re.compile(r"""(?:^|[;&|\n(]\s*)(?:cd|pushd|chdir|set-location|sl)\s+(?:"([^"]+)"|'([^']+)'|([^\s;&|)]+))""", re.I)
_SCAN_MAX_BYTES = 512 * 1024
_SCAN_DEPTH = 2
#: 2026-11-11 §77 오탐: `rm -f x.sh` (스크립트 파일 삭제) 를 실행으로 보고 본문을 검사함.
#:   실행하지 않는 명령의 피연산자일 때만 제외 — 파이프로 넘기거나 eval·source·xargs·$()·백틱이 있으면 제외 안 함 (보수적).
#:   cp·mv 는 옮긴 뒤 실행될 수 있어 그대로 검사.
_NON_EXEC_CMDS = {"rm", "del", "erase", "ls", "dir", "cat", "type", "head", "tail", "stat", "wc", "file", "du",
                  "md5sum", "sha1sum", "sha256sum", "grep", "remove-item", "ri", "get-filehash", "get-item",
                  "test-path", "get-content", "gc"}
_NON_EXEC_GIT = {"add", "rm", "diff", "log", "show", "status", "blame"}
_RX_INDIRECT_EXEC = re.compile(r"\b(?:eval|source|xargs|iex|invoke-expression)\b|\$\(|`", re.I)


def _non_exec_operand(text: str, pos: int) -> bool:
    """pos 의 스크립트 경로가 «실행하지 않는 명령의 피연산자» 인가 (확실할 때만 True)."""
    if _RX_INDIRECT_EXEC.search(text):
        return False
    starts = [text.rfind(c, 0, pos) for c in ";&|\n("]
    seg_start = max(starts) + 1
    ends = [i for i in (text.find(c, pos) for c in ";&|\n)") if i != -1]
    seg_end = min(ends) if ends else len(text)
    if seg_end < len(text) and text[seg_end] == "|" and text[seg_end:seg_end + 2] != "||":
        return False   # 출력이 다음 명령으로 넘어감 (cat x.sh | bash)
    words = [w for w in re.split(r"\s+", text[seg_start:pos].strip()) if w]
    while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
        words.pop(0)   # VAR=x 접두
    if not words:
        return False   # 경로가 첫 단어 = 직접 실행
    first = os.path.basename(words[0].strip("\"'")).lower()
    if first.endswith(".exe"):
        first = first[:-4]
    if first == "git":
        rest = words[1:]
        while len(rest) >= 2 and rest[0] in ("-C", "-c"):   # git -C <폴더> / -c k=v 다음이 하위 명령 (§78 오탐)
            rest = rest[2:]
        return bool(rest) and rest[0].lower() in _NON_EXEC_GIT
    return first in _NON_EXEC_CMDS


def _kit_tracked_unchanged(path: str) -> bool:
    """kit 저장소 안의 파일이 HEAD 커밋 내용 그대로인가 (확인 실패 = 아님 · fail-closed)."""
    import subprocess
    try:
        real = os.path.normcase(os.path.realpath(path))
        root = os.path.normcase(os.path.realpath(_KIT_ROOT))
        if not real.startswith(root + os.sep):
            return False
        rel = os.path.relpath(os.path.realpath(path), os.path.realpath(_KIT_ROOT)).replace("\\", "/")
        kw = dict(cwd=_KIT_ROOT, capture_output=True, text=True, timeout=2)
        head = subprocess.run(["git", "rev-parse", "HEAD:" + rel], **kw).stdout.strip()
        work = subprocess.run(["git", "hash-object", rel], **kw).stdout.strip()
        return bool(head) and head == work
    except Exception:  # noqa: BLE001
        return False


def _script_contents(raw_cmd: str, raw_cwd: str) -> tuple:
    """명령이 실행하는 셸 스크립트 본문 [(경로, 내용)] + 아직 없는 스크립트 여부.
    중첩 호출은 _SCAN_DEPTH 단계까지 · kit 에 커밋된 그대로인 스크립트는 제외 · 확정 불가 = _ArtifactRefused."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_agd_ps1_bom2", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ensure_ps1_bom.py"))
    bom = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bom)
    found: list = []
    missing = False
    seen: set = set()
    queue = [(raw_cmd, raw_cwd or os.getcwd(), 0, bool(_RX_CHDIR.search(raw_cmd)))]
    while queue:
        text, base, depth, chdir = queue.pop(0)
        tn = text.replace("\\n", "\n")
        for m in _RX_SHELL_SCRIPT.finditer(tn):
            if _non_exec_operand(tn, m.start()):
                continue   # §77 삭제·조회 대상일 뿐 실행 아님
            raw = next(g for g in m.groups() if g).strip()
            expanded = os.path.expandvars(os.path.expanduser(raw))
            if "$" in expanded or "%" in expanded:
                continue   # 셸 변수로 조립한 경로 — 따라갈 수 없음 (한계)
            if expanded.startswith(("\\\\", "//")):
                raise _ArtifactRefused("네트워크·장치 경로 스크립트(%s)는 내용을 확정할 수 없음" % raw)
            relative = not (os.path.isabs(expanded) or re.match(r"^/[a-zA-Z]/", expanded))
            bases = [base]
            if chdir and relative:   # cd 뒤 상대 경로 — 셸이 어느 폴더 기준으로 읽을지 모르므로 후보 폴더 전부 검사 (보수적)
                for t in _RX_CD_TARGET.findall(text.replace("\\n", "\n")):
                    t = next(x for x in t if x)
                    if "$" not in t and "%" not in t:
                        bases.append(bom._norm(t, base))
            cands = [os.path.normcase(os.path.abspath(bom._norm(raw, b))) for b in bases]
            exist = [p for p in cands if os.path.isfile(p)]
            if not exist:
                missing = missing or depth == 0
                continue
            for p in exist:
                if p in seen:
                    continue
                seen.add(p)
                if len(seen) > _ART_MAX_FILES:
                    raise _ArtifactRefused("실행 스크립트가 상한 %d개 초과" % _ART_MAX_FILES)
                if _kit_tracked_unchanged(p):
                    continue
                with open(p, "rb") as f:
                    body = f.read(_SCAN_MAX_BYTES + 1)
                if len(body) > _SCAN_MAX_BYTES:
                    raise _ArtifactRefused("스크립트(%s)가 %dKB 를 넘어 내용 검사 불가" % (raw, _SCAN_MAX_BYTES // 1024))
                content = body.decode("utf-8", "replace")
                found.append((p, content))
                if depth + 1 < _SCAN_DEPTH:
                    queue.append((content, os.path.dirname(p), depth + 1, bool(_RX_CHDIR.search(content))))
    return found, missing


def _scan_scripts(raw_cmd: str, cmd: str, raw_cwd: str, detect) -> tuple:
    """(위험 dict 또는 None, {경로: sha256}) — 시간 제한 안에서. 시간 초과 = _ArtifactRefused.
    스크립트 참조는 실행되지 않는 글(파일로만 쓰는 heredoc·검색어)을 걷어 낸 cmd 에서만 찾는다 (오탐 방지)."""
    import threading
    box: dict = {}

    def _work():
        try:
            box["r"] = _script_contents(cmd, raw_cwd)
        except BaseException as e:  # noqa: BLE001
            box["e"] = e
    th = threading.Thread(target=_work, daemon=True)
    th.start()
    th.join(_ART_TIMEOUT_SEC * 2)
    if "e" in box:
        raise box["e"]
    if "r" not in box:
        raise _ArtifactRefused("스크립트 내용 검사가 %.1f초 안에 끝나지 않음" % (_ART_TIMEOUT_SEC * 2))
    found, missing = box["r"]
    hashes = {p: hashlib.sha256(c.encode("utf-8", "surrogateescape")).hexdigest() for p, c in found}
    if missing:   # 같은 명령 안에서 만드는 스크립트 (cat > x.sh <<EOF …; bash x.sh) — 가리기 전 원문 전체를 검사
        r = detect(raw_cmd.replace("\\n", "\n"))
        if r:
            r = dict(r, description="아직 없는 스크립트를 만들어 실행 · " + (r.get("description") or ""))
            return r, hashes
    for p, content in found:
        r = detect(content)
        if r:
            return dict(r, description="스크립트 %s 안: %s" % (os.path.basename(p), r.get("description") or "")), hashes
    return None, hashes


_RX_GIT_PUSH = re.compile(r"\bgit\b[^;&|\n]*\bpush\b", re.I)
_RX_GIT_C = re.compile(r"\bgit\b(?:\s+-[^\s]+(?:\s+\S+)?)*?\s+(?:-C\b|--git-dir\b|--work-tree\b)", re.I)


def _push_head(cmd: str, raw_cwd: str):
    """push 명령이면 지금 HEAD (2026-11-09: 승인이 명령 글자만 묶어, 승인 뒤 커밋이 늘어도 그대로 올라가던 결함).
    저장소를 확정할 수 없으면(cd·git -C·--git-dir) _ArtifactRefused — 승인으로도 실행하지 않는다."""
    import subprocess
    plain = re.sub(r"[\"'\\^`]", "", cmd)
    if not _RX_GIT_PUSH.search(plain) or re.search(r"\bstash\s+push\b", plain, re.I):
        return None
    if _RX_CHDIR.search(plain) or _RX_GIT_C.search(plain):
        raise _ArtifactRefused("작업 위치를 바꾸는 명령(cd·git -C 등)과 push 가 함께 있어 올라갈 커밋을 확정할 수 없음")
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=raw_cwd or None, capture_output=True, text=True, timeout=3)
    except Exception as e:  # noqa: BLE001
        raise _ArtifactRefused("올라갈 커밋(HEAD) 확인 실패: %s" % type(e).__name__)
    head = r.stdout.strip()
    if r.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40,64}", head):
        raise _ArtifactRefused("올라갈 커밋(HEAD) 확인 실패")
    # HEAD 가 아닌 것을 올리는 push (커밋 해시 직접 지정 · 전체 ref · 미러) 는 범위를 확정할 수 없다
    tail = plain[_RX_GIT_PUSH.search(plain).end():]
    if re.search(r"(?<![\w-])[0-9a-f]{7,64}(?![\w-])|--all\b|--mirror\b|(?<![\w/])@\{", tail, re.I):
        raise _ArtifactRefused("커밋 해시·--all·--mirror 로 올릴 대상을 지정해 승인 범위를 확정할 수 없음 — Broker 경로로")
    return head


def _push_scope(raw_cwd: str, head: str) -> dict:
    """push 승인 범위: HEAD · 로컬 브랜치·태그 전체 · 현재 브랜치 · 원격 설정(URL 은 해시만)."""
    import subprocess
    out = {"git:HEAD": head, "git:refs": _local_refs(raw_cwd)}
    try:
        br = subprocess.run(["git", "symbolic-ref", "-q", "--short", "HEAD"], cwd=raw_cwd or None,
                            capture_output=True, text=True, timeout=3).stdout.strip()
        rem = subprocess.run(["git", "remote", "-v"], cwd=raw_cwd or None, capture_output=True, text=True, timeout=3)
    except Exception as e:  # noqa: BLE001
        raise _ArtifactRefused("브랜치·원격 확인 실패: %s" % type(e).__name__)
    if rem.returncode != 0:
        raise _ArtifactRefused("원격 설정 확인 실패")
    out["git:branch"] = br or "(detached)"
    out["git:remotes"] = hashlib.sha256(rem.stdout.encode("utf-8")).hexdigest()
    return out


def _local_refs(raw_cwd: str) -> str:
    """승인 때 로컬 브랜치·태그 전체 상태 (다른브랜치:main · --tags 처럼 HEAD 가 아닌 ref 를 올리는 push 대비)."""
    import subprocess
    try:
        r = subprocess.run(["git", "for-each-ref", "--format=%(refname) %(objectname)", "refs/heads", "refs/tags"],
                           cwd=raw_cwd or None, capture_output=True, text=True, timeout=3)
    except Exception as e:  # noqa: BLE001
        raise _ArtifactRefused("로컬 ref 확인 실패: %s" % type(e).__name__)
    if r.returncode != 0:
        raise _ArtifactRefused("로컬 ref 확인 실패")
    return hashlib.sha256(r.stdout.encode("utf-8")).hexdigest()


def _safe_log(log, text):
    try:
        append_text(log, text)
    except Exception:  # noqa: BLE001 — 로그 실패가 차단 결과를 지우지 않게 (2026-11-09 리뷰: 로그가 폴더면 통과하던 결함)
        pass


def _fingerprint(ctx):
    """(원문 명령, 검사용 명령, 작업 위치, 요청 번호) — 승인 요청·소비·결과 기록이 같은 번호를 쓰게 한 곳에서 계산."""
    inp = bash_read(ctx.raw)
    if not inp or not (_RISKWORD.search(inp) or _RX_SHELL_SCRIPT.search(inp)):   # §75: 셸 스크립트 실행은 내용 검사로
        return None
    raw_cmd = _extract_cmd(inp)
    if not raw_cmd:
        return None
    # 2026-10-26: 실행 vs 언급 구분 — git commit message body 안 위험 문자열은 매칭 제외
    cmd = _strip_inert_text(_strip_git_commit_message(raw_cmd))
    # 2026-11-08: 요청 번호 = 명령·작업 위치 지문 (시각 X) → 승인 후 같은 명령을 다시 내면 그 승인을 1회만 쓴다.
    # 다른 명령·다른 폴더는 지문이 달라 그 승인을 전용할 수 없다.
    try:
        raw_cwd = str(json.loads(ctx.raw or "{}").get("cwd") or "")
    except (ValueError, AttributeError):
        raw_cwd = ""
    cwd = raw_cwd.replace("\\", "/").rstrip("/").lower()
    task_id = "appr-" + hashlib.sha256((cwd + "\n" + cmd).encode("utf-8", "surrogateescape")).hexdigest()[:12]
    return raw_cmd, cmd, raw_cwd, task_id


def run_action(ctx, action):
    """PostToolUse: 이 명령으로 소비된 승인이 있으면 실행 결과를 기록한다 (차단·출력 없음)."""
    if action != "post" or not project_guard(ctx):
        return None
    fp = _fingerprint(ctx)
    if fp is None:
        return None
    mod = load_script("approval-gate")
    if mod is None or not hasattr(mod, "record_result"):
        return None
    try:
        resp = json.loads(ctx.raw or "{}").get("tool_response")
    except (ValueError, AttributeError):
        resp = None
    resp = resp if isinstance(resp, dict) else {}
    outcome = "interrupted" if resp.get("interrupted") else "finished"
    text = "%s%s" % (resp.get("stdout") or "", resp.get("stderr") or "")
    info = {"output_sha256": hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16],
            "output_chars": len(text)}  # 출력 원문은 저장하지 않는다 (비밀값 섞임 방지)
    log = project_path(ctx, ".claude", "logs", "approval-gate.log")
    try:
        tid = mod.find_request("base", fp[3], ("consumed",)) if hasattr(mod, "find_request") else None
        if tid and mod.record_result(tid, outcome, info):
            append_text(log, "[%s] RESULT: %s | task_id=%s\n" % (time.strftime("%Y-%m-%d_%H:%M:%S"), outcome, tid))
    except Exception as e:  # noqa: BLE001 — 기록 실패는 근거만 남긴다 (상태는 consumed/running = 결과 미확인 그대로)
        append_text(log, "RESULT-FAIL " + "".join(traceback.format_exception_only(type(e), e)))
    return None


def _block(reason: str, sysmsg: str):
    err = json.dumps({"decision": "block", "reason": reason, "systemMessage": sysmsg}, ensure_ascii=False, indent=2) + "\n"
    return Result(2, "", err)


def run(ctx):
    """2026-11-09 리뷰: 예외가 밖으로 나가면 tool-dispatch 가 결과를 버리고 통과시킨다 → 위험 단어가 있는 명령에서
    내부 오류가 나면 차단한다 (fail-closed)."""
    box: dict = {}
    try:
        return _run(ctx, box)
    except Exception as e:  # noqa: BLE001
        if not box.get("fp"):
            return None   # 위험 단어조차 없는 명령 — 일반 명령을 막지 않는다
        _safe_log(box.get("log") or "", "GATE-ERROR " + "".join(traceback.format_exception_only(type(e), e)))
        return _block(" 승인 게이트 내부 오류 (%s) — 안전을 위해 차단. 원인 확인 후 다시 실행" % type(e).__name__,
                      "HITL Approval Gate — 내부 오류로 차단 (fail-closed)")


def _run(ctx, box):
    log_dir = project_path(ctx, ".claude", "logs")
    log = os.path.join(log_dir, "approval-gate.log")
    box["log"] = log
    try:
        ensure_dir(log_dir)
    except OSError:
        pass
    if not project_guard(ctx):
        return None
    fp = _fingerprint(ctx)
    if fp is None:
        return None
    box["fp"] = fp
    raw_cmd, cmd, raw_cwd, task_id = fp
    gate = project_path(ctx, ".claude", "scripts", "approval-gate.py")
    if not os.path.isfile(gate):
        return None
    # 원본은 detect 호출에 2>>"$LOG" 리다이렉트가 있어 로그 파일이 (비어 있어도) 생긴다
    try:
        open(log, "ab").close()
    except OSError:
        pass
    mod = load_script("approval-gate")
    if mod is None:
        return None
    risk = mod.detect_risk(cmd)
    nested: dict = {}
    if risk is None:   # §75: 명령줄이 무해해 보여도 실행하는 셸 스크립트 안을 검사
        try:
            risk, nested = _scan_scripts(raw_cmd, cmd, raw_cwd, mod.detect_risk)
        except _ArtifactRefused as e:
            _safe_log(log, "[%s] REFUSED-SCAN: %s | cmd=%s\n" % (time.strftime("%Y-%m-%d_%H:%M:%S"), e, cmd))
            return _block(" 실행할 스크립트 내용을 확인할 수 없어 차단 — %s" % e,
                          "HITL Approval Gate — 스크립트 내용 확인 불가로 차단 (승인 요청 없음)")
    if risk is None:
        return None
    category = risk.get("category") or ""
    desc = risk.get("description") or ""
    if not category:
        return None
    try:
        arts = _artifacts(raw_cmd, raw_cwd)
        arts.update({"scan:" + p: h for p, h in nested.items()})   # 중첩 스크립트 내용도 승인 범위에 포함
        head = _push_head(raw_cmd, raw_cwd)
        if head:
            arts.update(_push_scope(raw_cwd, head))
            desc += " · 올라갈 HEAD %s · 브랜치 %s" % (head[:7], arts.get("git:branch"))
    except _ArtifactRefused as e:
        _safe_log(log, "[%s] REFUSED: %s | %s | cmd=%s\n" % (time.strftime("%Y-%m-%d_%H:%M:%S"), category, e, cmd))
        return _block(" 위험 명령 감지 (%s): %s. 실행할 스크립트 내용을 확정할 수 없어 승인으로도 실행하지 않음 — %s"
                      % (category, desc, e), "HITL Approval Gate — 스크립트 확정 불가로 차단 (승인 요청 없음)")
    # 2026-11-09 승인 불변성: 범위 지문(명령·폴더 + 스크립트 해시·HEAD·ref·브랜치·원격)이 같은 «승인된» 행만 소비한다.
    #   같은 범위의 대기 행이 있으면 그 번호를 그대로 안내 (수정 X) · 그 밖에는 항상 새 번호로 새 행 (기존 행 덮어쓰기 X).
    scope = mod.scope_key(task_id, arts)
    try:
        approved = mod.find_request("scope", scope, ("approved",))
        if approved and mod.consume_approval(approved, artifacts=arts) == "consumed":
            _safe_log(log, "[%s] ALLOW-ONCE: %s | task_id=%s | cmd=%s\n"
                      % (time.strftime("%Y-%m-%d_%H:%M:%S"), category, approved, cmd))
            return None
    except Exception as e:  # noqa: BLE001 — 확인 실패 = 차단 유지 (fail-closed)
        _safe_log(log, "".join(traceback.format_exception_only(type(e), e)))
    req_id = None
    try:
        req_id = mod.find_request("scope", scope, ("waiting",))
        if not req_id:
            if mod.find_request("base", task_id, ("approved", "waiting")):
                desc = "승인 뒤 실행 대상(스크립트 내용·올라갈 커밋 등)이 바뀌어 이전 요청을 쓰지 않음 — 새 요청 확인 후 승인 · " + desc
            req_id = mod.new_request(cmd, category, desc, arts, task_id, scope)
            _safe_log(log, "[%s] REQUEST: %s | task_id=%s | scope=%s\n"
                      % (time.strftime("%Y-%m-%d_%H:%M:%S"), category, req_id, scope))
    except Exception as e:  # noqa: BLE001
        _safe_log(log, "".join(traceback.format_exception_only(type(e), e)))
    shown = req_id or "(요청 등록 실패)"
    _safe_log(log, "[%s] BLOCK: %s | task_id=%s | cmd=%s\n" % (time.strftime("%Y-%m-%d_%H:%M:%S"), category, shown, cmd))
    return _block(" 위험 명령 감지 (%s): %s. 사용자가 프롬프트에 /approve %s 또는 /reject %s [reason] 입력 — "
                  "Claude 는 승인 명령을 실행하지 않는다. 승인 후 같은 명령을 같은 폴더에서 1회 실행 가능 (30분)"
                  % (category, desc, shown, shown),
                  "HITL Approval Gate — task_id=%s | category=%s | 사용자 /approve <id> 후 같은 명령 1회" % (shown, category))
