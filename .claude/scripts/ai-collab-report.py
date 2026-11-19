#!/usr/bin/env python3
"""ai-collab-report — Claude CLI ↔ ChatGPT GitHub 협업 (.ai-collab/) 보고서·요청 처리 (R325·R326 · 상주 X · 훅 X).

명령:
  report <요청ID> [--base <커밋>] [--status PASS|PARTIAL|BLOCKED]   커밋 직후 실행 → reports/<요청ID>.md + state.json 갱신
  check-requests                                                   requests/*.md 검증만 (실행 안 함 · GitHub 문서 ≠ 사용자 승인)
  prune                                                            검토 끝난 완료 보고서 정리 (내용은 Git 이력·원장에 남음)

원칙: 같은 (요청ID, head 커밋) 은 다시 만들지 않는다 · 요청 1건 = 보고서 1개 (누적 복사 X) · 파일을 최소한으로.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
COLLAB = ROOT / ".ai-collab"
STATE = COLLAB / "state.json"
LEDGER = ROOT / ".claude" / "state" / "request-ledger.json"
GATE = ROOT / ".claude" / "state" / "regression-gate.json"
_RID = re.compile(r"^R\d{1,6}$")


def _git(*args: str) -> str:
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=30)
    return r.stdout.strip() if r.returncode == 0 else ""


def _load(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save_state(st: dict) -> None:
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, STATE)                      # 쓰는 도중 끊겨도 원본 state.json 보존


def _state() -> dict:
    st = _load(STATE, {})
    st.setdefault("repository", "bernakilljos/orchestration")
    st.setdefault("requests", {})
    return st


def cmd_report(rid: str, base: str = "", status: str = "") -> int:
    if not _RID.match(rid):
        print(f"[ai-collab] 요청 ID 형식 아님: {rid!r} (예: R325)", file=sys.stderr)
        return 2
    req = next((r for r in _load(LEDGER, {}).get("requests", []) if r.get("id") == rid), None)
    if req is None:
        print(f"[ai-collab] 원장에 없는 요청: {rid}", file=sys.stderr)
        return 2
    head = _git("rev-parse", "HEAD")
    if not head:
        print("[ai-collab] git HEAD 확인 실패", file=sys.stderr)
        return 2
    st = _state()
    ent = st["requests"].get(rid) or {}
    if ent.get("head_commit") == head:
        print(f"[ai-collab] 변경 없음 — {rid} 는 이미 {head[:8]} 기준 보고됨 (중복 생성 X)")
        return 0
    base = base or ent.get("head_commit") or _git("rev-parse", "HEAD~1")
    if base and not _git("cat-file", "-t", base):
        print(f"[ai-collab] 기준 커밋 없음: {base}", file=sys.stderr)
        return 2
    files = [ln for ln in _git("diff", "--name-status", f"{base}..{head}").splitlines() if ln][:80]
    commits = _git("log", "--format=%h %s", f"{base}..{head}").splitlines()[:20]
    status = status or {"completed": "PASS"}.get(req.get("status"), req.get("verification") or "PARTIAL")
    gate = _load(GATE, {})
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    branch = _git("rev-parse", "--abbrev-ref", "HEAD") or "main"
    meta = {"request_id": rid, "repository": st["repository"], "branch": branch, "base_commit": base,
            "head_commit": head, "status": status, "created_at": now, "review_required": True}
    desc = re.sub(r"<[^>]+>", " ", req.get("desc") or "").strip()
    lines = ["---"] + [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in meta.items()] + ["---", "",
             f"# {rid} 작업 보고", "", f"- 요청 요약: {desc[:240]}", f"- 상태: {status}",
             f"- 근거(원장): {(req.get('evidence') or '기록 없음')[:600]}", "",
             "## 커밋", *[f"- {c}" for c in commits], "", "## 변경 파일", *[f"- `{f}`" for f in files], "",
             "## 시험", f"- 회귀 게이트: {gate.get('status', '미실행')} · {str(gate.get('summary') or '').strip('= ')[:120]}",
             f"- 새 실패: {len(gate.get('new_failures') or [])}건", ""]
    open_items = [i for i in (req.get("items") or []) if i.get("state") not in ("done", "na")]
    if open_items or status != "PASS":
        lines += ["## 남은 문제", *[f"- [{i.get('i')}] {(i.get('text') or '')[:120]} ({i.get('state')})" for i in open_items[:20]]]
        if req.get("status") == "approval_required":
            lines.append("- 사용자 승인(/approve) 필요")
    COLLAB.joinpath("reports").mkdir(parents=True, exist_ok=True)
    out = COLLAB / "reports" / f"{rid}.md"
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    st["requests"][rid] = {"head_commit": head, "base_commit": base, "status": status, "report": f"reports/{rid}.md",
                           "reported_at": now, "reviewed": False}
    st["last_head"] = head
    _save_state(st)
    print(f"[ai-collab] {out.relative_to(ROOT)} · {base[:8]}..{head[:8]} · 파일 {len(files)} · 상태 {status}")
    return 0


def cmd_check_requests() -> int:
    """requests/*.md 검증만 — 실행·승인으로 간주하지 않는다. 결과를 표준 출력으로 (파일 추가 생성 X)."""
    st = _state()
    rows = []
    for p in sorted((COLLAB / "requests").glob("*.md")):
        txt = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^request_id:\s*\"?([^\"\n]+)", txt, re.M)
        b = re.search(r"^base_commit:\s*\"?([0-9a-f]{7,40})", txt, re.M)
        rid = (m.group(1).strip() if m else "")
        why = []
        if not _RID.match(rid):
            why.append("request_id 없음·형식 오류")
        if not b or not _git("cat-file", "-t", b.group(1)):
            why.append("기준 커밋 없음")
        if rid in st.get("handled", {}):
            why.append("이미 처리됨 (중복)")
        rows.append({"file": p.name, "request_id": rid, "ok": not why, "why": why,
                     "next": "사용자가 대화에서 지시해야 실행 (GitHub 문서는 승인 아님)"})
    print(json.dumps(rows, ensure_ascii=False, indent=1))
    return 0


def cmd_prune() -> int:
    """검토 끝난(reviewed) 완료(PASS) 보고서만 지운다 · 미완료·승인 대기·검토 전은 남긴다 · 내용은 Git 이력에 보존."""
    st = _state()
    gone = []
    for rid, ent in list(st["requests"].items()):
        reviewed = ent.get("reviewed") or (COLLAB / "reviews" / f"{rid}.md").is_file()   # ChatGPT 가 검토 결과를 남김
        if reviewed and ent.get("status") == "PASS" and ent.get("report"):
            p = COLLAB / ent.get("report", f"reports/{rid}.md")
            if p.is_file() and p.resolve().is_relative_to((COLLAB / "reports").resolve()):
                p.unlink()
            ent["report"] = ""
            ent["pruned_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            gone.append(rid)
    _save_state(st)
    print(f"[ai-collab] 정리 {len(gone)}건: {' '.join(gone) or '없음'}")
    return 0


def main(argv: list) -> int:
    if not argv:
        print(__doc__)
        return 2
    op = argv[0]
    if op == "report" and len(argv) >= 2:
        opts = dict(zip(argv[2::2], argv[3::2]))
        return cmd_report(argv[1], opts.get("--base", ""), opts.get("--status", ""))
    if op == "check-requests":
        return cmd_check_requests()
    if op == "prune":
        return cmd_prune()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
