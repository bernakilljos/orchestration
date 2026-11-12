#!/usr/bin/env python
"""
auto-save-next-actions.py — .claude/state/next-actions.md 의 유일한 writer.

왜:
- /clear·재부팅 후 resume-last-24h.py 가 next-actions.md 를 새 세션에 주입한다.
- 2026-11-09 결함: 자동 갱신 2곳이 파일을 통째로 다시 써서 사람이 남긴 작업 지시가 사라졌고,
  supervisor 출력이 콘솔 인코딩(cp949)으로 섞여 파일이 UTF-8 이 아니게 되자
  읽는 쪽이 조용히 실패해 «이어서 할 일» 이 통째로 주입되지 않았다.

파일 구조:
- 자동 블록: <!-- AUTO:<name> BEGIN --> ... <!-- AUTO:<name> END --> — 해당 writer 만 교체
    goals  : supervisor(orca.db) 미완 goal (stop-active-goals-resume.sh)
    answer : 마지막 assistant 응답의 «다음 세션 / 이어서 할 일» 섹션 (Stop·SessionEnd)
- 자동 블록 밖의 모든 글 = 수동 작업 지시. 자동 갱신은 절대 지우거나 고치지 않는다.
  지우는 것은 사용자 지시가 있을 때 `manual-clear` 로만.

동시성: 잠금 파일(O_EXCL) 안에서 읽기→병합→임시 파일→os.replace.
잠금을 무시한 외부 쓰기(편집기 등)는 교체 직전 해시를 다시 비교해 감지하고 다시 병합한다.

CLI:
  answer                 (기본 · Stop/SessionEnd) 마지막 응답에서 섹션 추출 → answer 블록
  goals                  stdin JSON(supervisor active) → goals 블록 (0건이면 블록 제거)
  manual-add "<글>"      수동 지시에 한 줄 추가
  manual-clear           수동 지시 비움 (사용자 명시 지시 시만)
  show                   현재 파일 (복구 읽기)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
DB = ROOT / ".claude" / "state" / "orca.db"
OUT = ROOT / ".claude" / "state" / "next-actions.md"

PATTERN = re.compile(
    r"^(#{1,3})\s*(Next Actions?|다음\s*세션|다음에\s*할\s*일|이어서\s*할\s*일|이어서|Phase\s+\d+[^\n]*)[^\n]*\n(.+?)(?=\n#{1,3}\s|\Z)",
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)
# 2026-11-12 (R245): 제목을 '#' 대신 굵은 글씨 한 줄로 쓴 경우 — «**남은 후속 항목 (아직 고치지 않음)**»
#   이 저장되지 않아 재부팅 뒤 복원 목록에서 빠졌다. 굵은 줄 제목 + 남은/후속/미완료 이름도 받는다.
#   본문은 다음 굵은 줄 제목 · '#' 제목 · 빈 줄 2개 · 끝 전까지.
BOLD_PATTERN = re.compile(
    r"^\*\*\s*((?:남은|후속|미완료|미완|이어서|다음에?)[^*\n]{0,40}?(?:항목|작업|할\s*일|과제|일))[^*\n]*\*\*[^\n]*\n(.+?)"
    r"(?=\n\*\*[^\n]+\*\*\s*\n|\n#{1,3}\s|\n\s*\n\s*\n|\Z)",
    re.MULTILINE | re.DOTALL,
)
EMPTY_MARKERS = re.compile(r"\b(완료|done|끝|empty|없음|비움|clear)\b", re.IGNORECASE)

_RX_BLOCK = re.compile(r"<!-- AUTO:(\w+) BEGIN -->\n?(.*?)<!-- AUTO:\1 END -->\n?", re.S)
_LEGACY_MARK = "# 이어서 할 일 — 자동 재기록"
BLOCK_ORDER = ("goals", "answer")
LOCK_WAIT_SEC = 8.0
LOCK_STALE_SEC = 30.0


# ── 읽기 ─────────────────────────────────────────────────────────────
def read_robust(path: Path = None) -> str:
    """UTF-8 → cp949 → UTF-8(replace). 인코딩이 섞인 파일 때문에 재개가 조용히 실패하지 않게."""
    path = path or OUT
    try:
        b = path.read_bytes()
    except OSError:
        return ""
    for enc in ("utf-8-sig", "cp949"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", "replace")


def parse(text: str) -> tuple[str, dict]:
    """(수동 지시, {블록명: 본문}). 마커 이전 형식(자동 재기록 ~ ---)도 goals 블록으로 인식."""
    text = text.replace("\r\n", "\n")
    blocks = {}

    def _take(m):
        blocks[m.group(1)] = m.group(2).strip("\n")
        return ""
    rest = _RX_BLOCK.sub(_take, text)
    i = rest.find(_LEGACY_MARK)
    if i >= 0:   # 2026-11-09 이전 stop 훅이 만든 블록 — 그 앞뒤 글은 수동 지시로 보존
        j = rest.find("\n---\n", i)
        end = j + 5 if j >= 0 else len(rest)
        blocks.setdefault("goals", rest[i:end].strip("\n"))
        rest = rest[:i] + rest[end:]
    manual = re.sub(r"^\s*## 수동 작업 지시[^\n]*\n", "", rest.strip("\n"), count=1)
    manual = re.sub(r"\n{3,}", "\n\n", manual).strip("\n")
    return manual, blocks


def render(manual: str, blocks: dict) -> str:
    parts = []
    if manual.strip():
        parts.append("## 수동 작업 지시 (자동 갱신이 지우지 않음 · 사용자 지시로만 정리)\n\n" + manual.strip("\n"))
    for name in list(BLOCK_ORDER) + sorted(k for k in blocks if k not in BLOCK_ORDER):
        body = (blocks.get(name) or "").strip("\n")
        if body:
            parts.append(f"<!-- AUTO:{name} BEGIN -->\n{body}\n<!-- AUTO:{name} END -->")
    return ("\n\n".join(parts) + "\n") if parts else ""


# ── 쓰기 (잠금 + 원자적 교체 + 충돌 감지) ────────────────────────────
def _lock_path() -> Path:
    return OUT.with_name(OUT.name + ".lock")


def _acquire() -> bool:
    lp = _lock_path()
    deadline = time.time() + LOCK_WAIT_SEC
    while True:
        try:
            fd = os.open(str(lp), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"{os.getpid()} {time.time()}".encode())
            os.close(fd)
            return True
        except FileExistsError:
            try:
                if time.time() - lp.stat().st_mtime > LOCK_STALE_SEC:
                    lp.unlink()   # 죽은 writer 가 남긴 잠금
                    continue
            except OSError:
                pass
            if time.time() > deadline:
                return False
            time.sleep(0.05)


def _release() -> None:
    try:
        _lock_path().unlink()
    except OSError:
        pass


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def update(mutate) -> bool:
    """mutate(manual, blocks) -> (manual, blocks). 잠금 안에서 최신 내용 위에 적용."""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not _acquire():
        print("[next-actions] 잠금 대기 초과 — 이번 갱신 건너뜀 (기존 내용 유지)", file=sys.stderr)
        return False
    try:
        for _ in range(3):
            before = OUT.read_bytes() if OUT.exists() else b""
            manual, blocks = parse(read_robust())
            manual, blocks = mutate(manual, dict(blocks))
            new = render(manual, blocks)
            tmp = OUT.with_name(f"{OUT.name}.tmp.{os.getpid()}")
            tmp.write_text(new, encoding="utf-8")
            now = OUT.read_bytes() if OUT.exists() else b""
            if _sha(now) != _sha(before):   # 잠금 밖 쓰기가 끼어듦 → 버리고 최신 위에 다시
                tmp.unlink(missing_ok=True)
                continue
            if new == read_robust():
                tmp.unlink(missing_ok=True)
                return True
            os.replace(tmp, OUT)
            return True
        print("[next-actions] 동시 변경이 계속돼 갱신 건너뜀 (기존 내용 유지)", file=sys.stderr)
        return False
    finally:
        _release()


def set_block(name: str, body: str | None) -> bool:
    def _m(manual, blocks):
        if body and body.strip():
            blocks[name] = body
        else:
            blocks.pop(name, None)
        return manual, blocks
    return update(_m)


# ── 재개용 텍스트 (resume-last-24h.py) ───────────────────────────────
def resume_text(max_age_sec: float) -> str:
    """수동 지시는 나이와 무관하게 항상 · 자동 블록은 max_age 안일 때만."""
    if not OUT.exists():
        return ""
    manual, blocks = parse(read_robust())
    out = []
    if manual.strip():
        out.append("### 수동 작업 지시 (사람이 남김 · 오래돼도 유지)\n" + manual.strip())
    try:
        fresh = (time.time() - OUT.stat().st_mtime) < max_age_sec
    except OSError:
        fresh = False
    if fresh:
        for name in BLOCK_ORDER:
            if blocks.get(name):
                body = blocks[name].strip()
                if name == "answer":   # 2026-11-12 (R245): 기억만 하고 "진행해" 를 기다리던 결함
                    body = ("### 자동 재개 대상 — 직전 세션이 남긴 미완료 작업\n"
                            "일반 개발·기록·시험·로컬 커밋은 사용자 확인 없이 바로 이어서 실행한다. "
                            "실행 전 git log·trace·Ledger 로 이미 끝난 것인지 확인해 중복 실행하지 않는다. "
                            "push·인증정보·Windows 권한·운영 데이터 파괴 변경만 건너뛰고 보고한다.\n\n" + body)
                out.append(body)
    return "\n\n".join(out)


# ── 입력원 ───────────────────────────────────────────────────────────
def _latest_assistant_content() -> str | None:
    if not DB.exists():
        return None
    try:
        c = sqlite3.connect(DB)
        row = c.execute(
            "SELECT content FROM conversations WHERE role='assistant' ORDER BY id DESC LIMIT 1"
        ).fetchone()
    except Exception:
        return None
    return row[0] if row else None


def _extract_sections(text: str) -> str | None:
    matches = []
    for m in PATTERN.finditer(text):
        matches.append(f"{m.group(1)} {m.group(2).strip()}\n{m.group(3).strip()}")
    for m in BOLD_PATTERN.finditer(text):
        body = m.group(2).strip()
        if body:
            matches.append(f"### {m.group(1).strip()}\n{body}")
    return "\n\n".join(matches) if matches else None


def cmd_answer() -> int:
    content = _latest_assistant_content()
    if not content:
        return 0
    sections = _extract_sections(content)
    if sections is None:
        return 0   # 섹션 없음 — 기존 유지
    body = sections.strip()
    if not body or (EMPTY_MARKERS.search(body) and len(body) < 60):
        set_block("answer", None)   # «완료» — 자동 블록만 비움 (수동 지시는 유지)
        return 0
    set_block("answer", body)
    return 0


def cmd_goals(raw: str) -> int:
    try:
        goals = json.loads(raw or "[]")
    except ValueError:
        print("[next-actions] goals 입력이 JSON 아님 — 기존 유지", file=sys.stderr)
        return 0
    if not goals:
        set_block("goals", None)
        return 0
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = (
        f"### 미완 Goals {len(goals)} 건 — 자동 재기록 ({ts} · 정본 orca.db supervisor)\n\n"
        "next-actions.md 저장만으로 완료 선언 X (2026-10-27). 다음 세션은 확인 질문 없이 이어서 진행.\n\n"
        "```json\n" + json.dumps(goals, ensure_ascii=False, indent=2) + "\n```\n\n"
        "복구: `python .claude/scripts/lib/supervisor.py active` · `... advance-all`"
    )
    set_block("goals", body)
    return 0


def main(argv) -> int:
    cmd = argv[1] if len(argv) > 1 else "answer"
    if cmd == "answer":
        return cmd_answer()
    if cmd == "goals":
        return cmd_goals(sys.stdin.buffer.read().decode("utf-8", "replace"))
    if cmd == "manual-add":
        line = " ".join(argv[2:]).strip()
        if not line:
            return 2
        return 0 if update(lambda m, b: ((m + "\n" if m else "") + line, b)) else 1
    if cmd == "manual-clear":
        return 0 if update(lambda m, b: ("", b)) else 1
    if cmd == "show":
        sys.stdout.write(read_robust())
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print(f"[auto-save-next-actions] fatal: {e}", file=sys.stderr)
        sys.exit(0)
