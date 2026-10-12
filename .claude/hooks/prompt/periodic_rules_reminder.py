"""periodic-rules-reminder.sh 이식 — 10번째 프롬프트마다 규칙 리마인드 (긴 대화 attention 유지).

상태: .claude/state/session-turns.d/<세션id>.prompts (세션별 카운터)
"""
from __future__ import annotations

import glob
import os
import re
from pathlib import Path

from _common import is_loop_prompt_raw, read_text, write_text

MESSAGE = (
    "\n"
    " [규칙 리마인드 — 10번째 프롬프트]\n"
    "0. **대상 확정 우선** — 첫 응답 첫 줄에 \"대상: <path>\" 명시. kit/설정/target/글로벌 4갈래. 확정 전 grep-Read-Edit X. (direction-first.md)\n"
    "1. git commit -> guide.txt+CLAUDE.md+settings.json 같이\n"
    "2. 도메인별 X -> 공통 도구 보강\n"
    "3. 사용자 카테고리만 -> 알아서 세부 채움\n"
    "4. 물어보지 말고 실행 (Zero-touch)\n"
    "5. sync + auto-stats 자동\n"
    "\n"
)


def _basename(p: str) -> str:
    """bash basename (Git Bash 는 역슬래시 경로도 처리)."""
    parts = [x for x in p.replace("\\", "/").split("/") if x]
    return parts[-1] if parts else ""


def _session_id(project_dir: str) -> str:
    """원본: ls -t ~/.claude/projects/*<basename>*/*.jsonl | head -1 -> 파일명(확장자 제외). 없으면 unknown.

    주의 (원본 동일): ~/.claude/projects 폴더명은 '.'·'_' 가 '-' 로 바뀌어 있어 basename 에 '.' 나 '_' 가
    있는 프로젝트는 매치가 안 되고 unknown 이 된다.
    """
    base = _basename(project_dir)
    pat = os.path.join(str(Path.home()), ".claude", "projects", "*" + glob.escape(base) + "*", "*.jsonl")
    files = glob.glob(pat)
    if not files:
        return "unknown"
    newest = max(files, key=lambda f: (os.path.getmtime(f), f))
    sid = os.path.basename(newest)
    return re.sub(r"\.jsonl$", "", sid) or "unknown"


def run(ctx):
    if not ctx.has_plugins():
        return None
    # /loop·배경 알림 프롬프트에는 안내를 넣지 않는다 (카운터도 올리지 않음)
    if is_loop_prompt_raw(ctx.raw_stripped):
        return None

    state = os.path.join(ctx.project_dir, ".claude", "state")
    sid = _session_id(ctx.project_dir)
    os.makedirs(os.path.join(state, "session-turns.d"), exist_ok=True)
    counter = os.path.join(state, "session-turns.d", sid + ".prompts")

    count = 0
    if os.path.isfile(counter):
        s = re.sub(r"\s+", "", read_text(counter))
        count = int(s) if re.fullmatch(r"-?\d+", s) else 0
    count += 1
    write_text(counter, f"{count}\n")

    if count % 10 == 0:
        return MESSAGE
    return None
