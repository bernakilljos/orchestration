#!/usr/bin/env python3
"""ai-collab-report — Claude CLI ↔ ChatGPT GitHub 협업 (.ai-collab/) 보고서·요청 처리 (R325·R326 · 상주 X · 훅 X).

명령:
  report <요청ID> [--base <커밋>] [--status PASS|PARTIAL|BLOCKED]   커밋 직후 실행 → reports/<요청ID>.md + state.json 갱신
  check-requests                                                   requests/*.md 검증만 (실행 안 함 · GitHub 문서 ≠ 사용자 승인)
  prune                                                            검토 끝난 완료 보고서 정리 (내용은 Git 이력·원장에 남음)
  poll                                                             5분 주기 확인 1회 — 처리 확정 안 된 requests·reviews 만 출력 (새것 0 · 없음 3)
  ack <요청ID|경로>                                                 처리 확정 (검증·보고 뒤 · report 는 연결 커밋 있는 지시를 자동 확정)

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


_RANK = {"BLOCKED": 0, "FAIL": 0, "PARTIAL": 1, "PASS": 2}


def _publication_only(commit: str) -> bool:
    """이 커밋이 .ai-collab/ 아래만 바꿨나 (보고서 게시 커밋)."""
    names = [n for n in _git("show", "--name-only", "--format=", commit).splitlines() if n]
    return bool(names) and all(n.startswith(".ai-collab/") for n in names)


def _work_head() -> str:
    """HEAD 에서 거슬러 올라가 보고서 게시 커밋을 건너뛴 첫 작업 커밋."""
    for c in _git("rev-list", "--max-count=50", "HEAD").splitlines():
        if not _publication_only(c):
            return c
    return _git("rev-parse", "HEAD")


def _commits_for(rid: str, base: str, tip: str) -> list:
    """base..tip 작업 커밋 중 메시지에 rid 가 낱말로 든 것 [(전체 해시, 제목)] 최신순 (R32 ≠ R325)."""
    pat = re.compile(r"(?<![A-Za-z0-9])" + re.escape(rid) + r"(?!\d)")
    out = []
    for blk in _git("log", "--format=%H%x1f%s%x1f%b%x1e", f"{base}..{tip}").split("\x1e"):
        parts = blk.strip("\n").split("\x1f")
        # 제목 줄만 본다 — 본문은 다른 요청을 «설명» 하며 언급하기도 한다 (실측: 365ff8ec 본문의 "R325·R326 이 같은 범위" → R326 오분류)
        if len(parts) >= 2 and pat.search(parts[1]) and not _publication_only(parts[0]):
            out.append((parts[0], parts[1]))
    return out


def _load(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save_state(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)   # 첫 poll 이 보고서보다 먼저 와도 (.ai-collab 없음) 실패하지 않게
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
    tip = _work_head()                                 # 보고서 게시 커밋(.ai-collab/ 만 바꾼 것)은 작업 커밋이 아니다
    if not tip:
        print("[ai-collab] git HEAD 확인 실패", file=sys.stderr)
        return 2
    st = _state()
    ent = st["requests"].get(rid) or {}
    ledger_status = {"completed": "PASS"}.get(req.get("status"), req.get("verification") or "PARTIAL")
    # 원장보다 좋은 상태로는 올리지 못한다 (예: 원장 PARTIAL 인데 --status PASS) · 더 낮게 적는 것만 허용
    if status and _RANK.get(status, -1) > _RANK.get(ledger_status, -1):
        print(f"[ai-collab] 상태 거부: 원장 {rid} = {ledger_status} 인데 {status} 로 보고할 수 없음", file=sys.stderr)
        return 2
    status = status or ledger_status
    base = base or ent.get("base_commit" if ent.get("range_tip") == tip else "range_tip") or _git("rev-parse", f"{tip}~1")
    if base and not _git("cat-file", "-t", base):
        print(f"[ai-collab] 기준 커밋 없음: {base}", file=sys.stderr)
        return 2
    mine = _commits_for(rid, base, tip)                # 이 요청 ID 를 메시지에 적은 작업 커밋만 (요청별 증거 분리)
    head = mine[0][0] if mine else tip
    if ent.get("head_commit") == head and ent.get("status") == status:
        print(f"[ai-collab] 변경 없음 — {rid} 는 이미 {head[:8]}·{status} 로 보고됨 (중복 생성 X)")
        return 0
    if mine:
        files = sorted({ln for c, _ in mine for ln in _git("show", "--name-status", "--format=", c).splitlines() if ln})[:80]
        commits = [f"{c[:8]} {s}" for c, s in mine][:20]
    else:
        # R328 (외부 검토): 연결 커밋이 없을 때 범위 전체로 돌아가면 다른 작업의 변경이 섞인다 → 추측하지 않고 «검증 불가»
        files, commits = [], []
        if _RANK.get(status, -1) > _RANK["PARTIAL"]:
            status = "PARTIAL"
    gate = _load(GATE, {})
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    branch = _git("rev-parse", "--abbrev-ref", "HEAD") or "main"
    meta = {"request_id": rid, "repository": st["repository"], "branch": branch, "base_commit": base,
            "head_commit": head, "status": status, "created_at": now, "review_required": True,
            "commit_link": "verified" if mine else "unverified"}
    if not mine:
        commits = [f"연결 커밋 없음 · 변경 내역 검증 불가 — {base[:8]}..{tip[:8]} 안에 제목에 {rid} 를 적은 작업 커밋이 없음 "
                   "(다른 작업과 섞이지 않게 범위 전체를 추측해 적지 않음)"]
        files = ["(검증 불가 — 위 참고)"]
    desc = " ".join(re.sub(r"<[^>]+>", " ", req.get("desc") or "").split())   # 붙여 넣은 원문 줄바꿈 → 한 줄 요약
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
    st["requests"][rid] = {"head_commit": head, "base_commit": base, "range_tip": tip, "status": status,
                           "report": f"reports/{rid}.md", "reported_at": now, "reviewed": False}
    st["last_head"] = tip          # 마지막 «작업» 커밋 · 이 보고서를 올리는 게시 커밋(.ai-collab/ 만 변경)은 그 뒤에 생긴다
    if (COLLAB / "requests" / f"{rid}.md").is_file() and mine:   # 같은 ID 지시를 처리한 작업 커밋이 있으면 처리됨 (check-requests 중복 판정)
        st.setdefault("handled", {})[rid] = head
        rpath = f".ai-collab/requests/{rid}.md"   # R332: 처리 확정은 poll 이 아니라 여기 (연결 커밋이 있는 보고 뒤)
        rblob = (st.get("inflight", {}).get(rpath) or {}).get("blob") or _remote_files().get(rpath)
        if rblob:
            _ack(st, rpath, rblob)
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


_VERDICTS = {"approved", "changes_requested"}
_SHA40 = re.compile(r"[0-9a-f]{40}")


def _frontmatter(txt: str):
    """문서 맨 앞의 YAML 머리 하나만 {키: 값} 으로 · 머리 없음·닫는 줄 없음·중복 키·형식 밖 줄 = None.
    R332 (외부 검토): 본문·인용문에 쓴 «verdict: approved» 를 승인으로 읽던 것 — 머리 밖은 보지 않는다."""
    lines = txt.lstrip("﻿").replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    out = {}
    for ln in lines[1:]:
        if ln.strip() == "---":
            return out
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):[ \t]*(.*?)[ \t]*(?:#.*)?$", ln)
        if not m or m.group(1) in out:            # 들여쓴 줄·목록·중복 키 = 판정 불가
            return None
        val = m.group(2)
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        out[m.group(1)] = val
    return None                                    # 닫는 --- 없음


def _review_approves(rid: str, head: str) -> bool:
    """reviews/<rid>.md 맨 앞 YAML 머리의 verdict 가 approved 이고 reviewed_commit(40자 SHA)이 보고서 head_commit 과 같을 때만 True.
    본문·인용문 값·중복 키·누락·잘못된 값·다른(이전) 커밋 검토·파일 없음 = False (보고서 유지)."""
    p = COLLAB / "reviews" / f"{rid}.md"
    try:
        fm = _frontmatter(p.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return False
    if not fm or not head:
        return False
    verdict = fm.get("verdict", "").lower()
    commit = fm.get("reviewed_commit", "")
    if verdict not in _VERDICTS or verdict != "approved":   # changes_requested·pending·오타 = 보존
        return False
    return bool(_SHA40.fullmatch(commit)) and commit == head   # R329: 전체 40자 SHA 정확 일치


def cmd_prune() -> int:
    """검토 끝난(reviewed) 완료(PASS) 보고서만 지운다 · 미완료·승인 대기·검토 전은 남긴다 · 내용은 Git 이력에 보존."""
    st = _state()
    gone = []
    for rid, ent in list(st["requests"].items()):
        # R329 (외부 검토): 검토 파일이 «있기만» 하면 지우던 것 → 명시 승인 + 승인한 커밋 = 이 보고서 커밋일 때만
        if _review_approves(rid, ent.get("head_commit", "")) and ent.get("status") == "PASS" and ent.get("report"):
            p = COLLAB / ent.get("report", f"reports/{rid}.md")
            if p.is_file() and p.resolve().is_relative_to((COLLAB / "reports").resolve()):
                p.unlink()
            ent["report"] = ""
            ent["pruned_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            gone.append(rid)
    _save_state(st)
    print(f"[ai-collab] 정리 {len(gone)}건: {' '.join(gone) or '없음'}")
    return 0


def _lease_sec() -> int:
    try:
        return max(60, int(os.environ.get("AI_COLLAB_LEASE_SEC", "1200")))
    except ValueError:
        return 1200


def _remote_files() -> dict:
    """origin/main 의 requests/·reviews/ 파일 {경로: blob} (.gitkeep 제외)."""
    out = {}
    for ln in _git("ls-tree", "-r", "origin/main", "--", ".ai-collab/requests", ".ai-collab/reviews").splitlines():
        meta, _, path = ln.partition("\t")
        if path and not path.endswith(".gitkeep") and meta:
            out[path] = meta.split()[-1]
    return out


def _ack(st: dict, path: str, blob: str) -> None:
    """처리 확정 — 이 내용(blob)은 다시 알리지 않는다. 처리 중 표시는 지운다."""
    st.setdefault("seen", {})[path] = blob
    st.setdefault("inflight", {}).pop(path, None)


def cmd_poll() -> int:
    """R330 5분 주기 확인 1회분 — origin 을 받아 requests/·reviews/ 에서 아직 처리 확정 안 된 파일만 알린다.
    새 파일 있음 = 0 (내용 출력 · «처리 중» 표시) · 없음·처리 중만 = 3 · fetch 실패 = 2. 실행·승인으로 간주하지 않는다.
    R332 (외부 검토): 알리기만 해도 seen(처리 확정)으로 적어, 세션이 처리 도중 끊기면 다음 주기에 사라지던 것 →
    poll 은 inflight(처리 중 · 임대 시간)만 적고, 처리 확정(seen)은 보고(report)·ack 가 적는다.
    임대 시간 안 = 다른 주기·세션이 같은 요청을 겹쳐 받지 않음 · 지나면 다시 전달 (중단·재시작 복구)."""
    r = subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "origin"], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        print(f"[ai-collab] fetch 실패: {(r.stderr or '').strip()[:160]}", file=sys.stderr)
        return 2
    st = _state()
    seen = st.setdefault("seen", {})
    inflight = st.setdefault("inflight", {})
    handled = st.get("handled", {})
    now = datetime.now(timezone.utc)
    new, busy, changed = [], [], False
    for path, blob in _remote_files().items():
        if seen.get(path) == blob:
            continue
        m = re.fullmatch(r"\.ai-collab/requests/(R\d{1,6})\.md", path)
        if m and m.group(1) in handled and path not in seen:   # R332 이전에 처리한 지시 (handled 만 있음) — 재실행 X
            _ack(st, path, blob)
            changed = True
            continue
        cur = inflight.get(path) or {}
        if cur.get("blob") == blob:
            try:
                age = (now - datetime.fromisoformat(cur.get("at", ""))).total_seconds()
            except ValueError:
                age = _lease_sec()
            if age < _lease_sec():
                busy.append(path)
                continue
        new.append({"path": path, "blob": blob, "text": _git("cat-file", "-p", blob)[:4000],
                    "redelivery": bool(cur)})
        inflight[path] = {"blob": blob, "at": now.isoformat(timespec="seconds")}
        changed = True
    if new:
        st["last_poll_hit"] = now.isoformat(timespec="seconds")
    if changed:
        _save_state(st)
    if not new:
        print(f"[ai-collab] 새 요청·검토 없음{f' (처리 중 {len(busy)}건: ' + ' '.join(busy) + ')' if busy else ''}")
        return 3
    print(json.dumps(new, ensure_ascii=False, indent=1))
    return 0


def cmd_ack(target: str) -> int:
    """처리 확정 — 경로(.ai-collab/requests/R332.md) 또는 요청 ID(R332 = 그 ID 의 requests·reviews 중 처리 중인 것).
    검증·보고를 마친 뒤에만 부른다. origin 의 현재 내용(blob)으로 확정 → 그 뒤 바뀐 내용은 다시 알린다."""
    st = _state()
    remote = _remote_files()
    if _RID.match(target):
        paths = [p for p in (f".ai-collab/requests/{target}.md", f".ai-collab/reviews/{target}.md")
                 if p in st.get("inflight", {}) or (p in remote and st.get("seen", {}).get(p) != remote[p])]
    else:
        paths = [target]
    done = []
    for p in paths:
        blob = (st.get("inflight", {}).get(p) or {}).get("blob") or remote.get(p)
        if blob:
            _ack(st, p, blob)
            done.append(p)
    if not done:
        print(f"[ai-collab] 확정할 것 없음: {target}", file=sys.stderr)
        return 2
    _save_state(st)
    print(f"[ai-collab] 처리 확정 {len(done)}건: {' '.join(done)}")
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
    if op == "poll":
        return cmd_poll()
    if op == "ack" and len(argv) >= 2:
        return cmd_ack(argv[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
