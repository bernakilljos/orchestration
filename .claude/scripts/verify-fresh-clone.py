#!/usr/bin/env python3
"""verify-fresh-clone — "git pull 만 받은 새 PC 에서도 동작하나" 정적 검사.

2026-10-02 사고: 쓰는 코드만 있고 그릇(DDL·상태파일 생성기)이 없어서, 수동으로 쌓인
다른 PC 에서만 동작했다. 아래 2가지를 kit 전체에서 전수 검사한다.

  1. INSERT/UPDATE 하는 모든 테이블에 CREATE TABLE IF NOT EXISTS 가 kit 안에 있는가
  2. .claude/state/*.json 을 읽는 파일마다, 그 파일을 쓰는 생성기가 hook(settings.json)
     에서 (직접 또는 1단계 호출로) 실행되는가

결과: 위반 0 = exit 0 · 위반 있음 = exit 1 + 목록. 분모(검사 대상 수)를 항상 출력.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = [ROOT / ".claude" / "scripts", ROOT / ".claude" / "hooks", ROOT / "plugins"]
EXTS = {".py", ".sh"}

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def files():
    for d in SCAN_DIRS:
        for p in d.rglob("*"):
            if p.suffix in EXTS and "__pycache__" not in p.parts and p.name != Path(__file__).name:
                yield p


def main() -> int:
    texts = {p: p.read_text(encoding="utf-8", errors="replace") for p in files()}
    all_text = "\n".join(texts.values())

    # 1) 테이블 DDL
    created = set(re.findall(r"CREATE (?:VIRTUAL )?TABLE IF NOT EXISTS\s+(\w+)", all_text))  # FTS5 등 VIRTUAL 포함
    written: dict[str, set[str]] = {}
    for p, t in texts.items():
        for tbl in re.findall(r"(?:INSERT(?:\s+OR\s+\w+)?\s+INTO|UPDATE)\s+(\w+)\s*(?:\(|SET)", t):
            written.setdefault(tbl, set()).add(str(p.relative_to(ROOT)))
    no_ddl = {t: w for t, w in written.items() if t not in created}

    # 1-b) 쓰는 컬럼이 DDL(또는 ALTER ADD COLUMN)에 있는가 — 2026-10-02 session_summary.updated_at 누락 사고
    ddl_cols: dict[str, set[str]] = {}
    for m in re.finditer(r"CREATE TABLE IF NOT EXISTS\s+(\w+)\s*\((.*?)\)\s*;", all_text, re.S):
        body = re.sub(r"--[^\n]*", "", m.group(2))   # SQL 주석 제거 (오탐 방지)
        cols = {c.strip().split()[0] for c in body.split(",") if c.strip()}
        ddl_cols.setdefault(m.group(1), set()).update(cols)
    alter_cols = set(re.findall(r"ADD COLUMN\s+(\w+)", all_text)) | set(re.findall(r"""\("(\w+)",\s*"(?:TIMESTAMP|INTEGER|TEXT)""", all_text))
    bad_cols: list[str] = []
    for p, t in texts.items():
        for m in re.finditer(r"INSERT(?:\s+OR\s+\w+)?\s+INTO\s+(\w+)\s*\(([^)]*)\)(.{0,800}?)(?:\"\"\"|\"\s*,|\)\s*$)", t, re.S):
            tbl = m.group(1)
            if tbl not in ddl_cols:
                continue
            # 파이썬 문자열 이어붙이기("a, " "b") 의 따옴표·공백 제거
            cols = {re.sub(r"[\s\"']", "", c) for c in m.group(2).split(",")} - {""}
            tail = m.group(3)
            if "DO UPDATE SET" in tail:
                cols |= set(re.findall(r"(\w+)\s*=", tail.split("DO UPDATE SET", 1)[1]))
            for c in sorted(cols - ddl_cols[tbl] - alter_cols - {"excluded"}):
                bad_cols.append(f"{tbl}.{c} ({p.relative_to(ROOT)})")

    # 2) state 파일 생성기 → hook 연결
    # hooks 섹션의 command 만 (statusLine 은 생성기가 아니라 소비자라 제외)
    sj = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8-sig"))
    cmds = [h.get("command", "") for evs in (sj.get("hooks") or {}).values()
            for m in evs or [] for h in m.get("hooks", [])]
    hooked = {Path(m).name for c in cmds for m in re.findall(r"[\w./-]+\.(?:sh|py)", c)}
    # hook 스크립트가 **실행하는** 스크립트까지 1단계 확장 (주석 언급은 제외)
    run_re = re.compile(r"^(?!\s*#).*?(?:bash|python3?|sh|\$PY)\b[^\n]*?([\w.-]+\.(?:sh|py))", re.M)
    reach = set(hooked)
    for p, t in texts.items():
        if p.name in hooked:
            reach |= {m for m in run_re.findall(t)}
    # statusLine 명령도 매 렌더 실행되는 생성기 (자기 캐시를 스스로 씀) — 확장은 안 함
    sl = (sj.get("statusLine") or {}).get("command", "")
    reach |= {Path(m).name for m in re.findall(r"[\w./-]+\.(?:sh|py)", sl)}
    state_reads: dict[str, set[str]] = {}
    for p, t in texts.items():
        for f in re.findall(r"""["']\.claude["'],\s*["']state["'],\s*["']([\w.-]+\.json)["']""", t):
            state_reads.setdefault(f, set()).add(p.name)
    orphan_state = {}
    for f, readers in state_reads.items():
        # 생성기 = 그 파일명을 다루는 '읽는 쪽이 아닌' 파일. 읽는 쪽만 있으면 자기 캐시
        # (statusline 이 쓰고 읽는 rate-limits 등) → 읽는 쪽이 실행 경로에 있으면 정상.
        producers = {p.name for p, t in texts.items() if f in t and p.name not in readers}
        if not producers:
            producers = set(readers)
        if not (producers & reach):
            orphan_state[f] = (sorted(readers), sorted(producers))

    print(f"[verify-fresh-clone] 검사 파일 {len(texts)} · 쓰는 테이블 {len(written)} · state 읽기 {len(state_reads)}")
    bad = 0
    for t, w in sorted(no_ddl.items()):
        bad += 1
        print(f"  [FAIL] 테이블 {t}: DDL 없음 (쓰는 곳 {', '.join(sorted(w))[:160]})")
    for bc in sorted(set(bad_cols)):
        bad += 1
        print(f"  [FAIL] 컬럼 {bc}: DDL·ALTER 에 없음")
    for f, (r, pr) in sorted(orphan_state.items()):
        bad += 1
        print(f"  [FAIL] state/{f}: 읽는 곳 {r} · 생성기 {pr or '없음'} — hook 미연결")
    print(f"[verify-fresh-clone] {'PASS' if bad == 0 else 'FAIL'} 위반 {bad}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
