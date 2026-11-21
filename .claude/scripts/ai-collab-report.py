#!/usr/bin/env python3
"""ai-collab-report — Claude CLI ↔ ChatGPT GitHub 협업 (.ai-collab/) 보고서·요청 처리 (R325·R326 · 상주 X · 훅 X).

명령:
  report <요청ID> [--base <커밋>] [--status PASS|PARTIAL|BLOCKED]   커밋 직후 실행 → reports/<요청ID>.md + state.json 갱신
  check-requests                                                   requests/*.md 검증만 (실행 안 함 · GitHub 문서 ≠ 사용자 승인)
  prune                                                            검토 끝난 완료 보고서 정리 (내용은 Git 이력·원장에 남음)
  poll                                                             5분 주기 확인 1회 — 처리 확정 안 된 requests·reviews 만 출력 (새것 0 · 없음 3)
  ack <요청ID|경로>                                                 처리 확정 (검증·보고 뒤 · report 는 연결 커밋 있는 지시를 자동 확정)
  queue [--no-write]                                               남은 PARTIAL 하위 항목 큐 → next-actions collab 블록 (R354 · 재개 주입)
  wait [--interval 300] [--max-sec 604800]                          셸이 poll 반복 → 새 파일 있을 때만 끝남 (Bash 백그라운드 · 대기 중 모델 호출 0)

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
    # R354: 하위 항목(남은 일)·근거가 바뀌어도 head·상태가 같으면 «변경 없음» 으로 건너뛰어 보고서가 옛 남은 일을 보여 줬다 → 지문에 포함
    sig = json.dumps([[i.get("i"), i.get("state"), i.get("owner"), i.get("text")] for i in (req.get("items") or [])] +
                     [req.get("evidence") or ""], ensure_ascii=False)
    import hashlib as _h
    sig = _h.sha1(sig.encode("utf-8")).hexdigest()[:12]
    if ent.get("head_commit") == head and ent.get("status") == status and ent.get("items_sig", sig) == sig:
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
        lines += ["## 남은 문제", *[f"- [{i.get('i')}] {(i.get('text') or '')[:120]} ({i.get('state')}"
                                     f"{' · 외부 증거 필요' if i.get('owner') == 'external' else ''})" for i in open_items[:30]]]
        if not req.get("items"):   # R354: 남은 일이 원장에 없으면 큐·재개가 못 읽는다 — 빈 제목만 두지 않고 사실대로
            lines.append("- (원장 하위 항목 없음 — 남은 일 미정리 · `request-ledger.py item-add` 로 등록 필요)")
        if req.get("status") == "approval_required":
            lines.append("- 사용자 승인(/approve) 필요")
    COLLAB.joinpath("reports").mkdir(parents=True, exist_ok=True)
    out = COLLAB / "reports" / f"{rid}.md"
    # R354: 다시 만들 때 자동 생성 절(머리·커밋·변경 파일·시험·남은 문제)만 교체하고 사람이 쓴 절(판정·분석·표)은 원문 그대로 보존
    #   (종전: 통째로 다시 써서 상세 분석이 사라짐 → 항목만 갱신해도 보고서가 빈약해지던 것)
    kept = []
    if out.is_file():
        for sec in re.split(r"(?m)^(?=## )", out.read_text(encoding="utf-8", errors="replace")):
            title = sec[3:].split("\n", 1)[0].strip() if sec.startswith("## ") else ""
            if title and title not in _GENERATED_SECTIONS:
                kept.append(sec.rstrip())
    out.write_text("\n".join(lines).rstrip() + "\n" + ("\n" + "\n\n".join(kept) + "\n" if kept else ""), encoding="utf-8")
    st["requests"][rid] = {"head_commit": head, "base_commit": base, "range_tip": tip, "status": status,
                           "report": f"reports/{rid}.md", "reported_at": now, "reviewed": False, "items_sig": sig}
    st["last_head"] = tip          # 마지막 «작업» 커밋 · 이 보고서를 올리는 게시 커밋(.ai-collab/ 만 변경)은 그 뒤에 생긴다
    if (COLLAB / "requests" / f"{rid}.md").is_file() and mine:   # 같은 ID 지시를 처리한 작업 커밋이 있으면 처리됨 (check-requests 중복 판정)
        st.setdefault("handled", {})[rid] = head
        rpath = f".ai-collab/requests/{rid}.md"   # R332: 처리 확정은 poll 이 아니라 여기 (연결 커밋이 있는 보고 뒤)
        rblob = (st.get("inflight", {}).get(rpath) or {}).get("blob")   # R333: 전달받은(inflight) 판만 · 못 받은 판을 확정하지 않음
        if rblob:
            _ack(st, rpath, rblob)
    _save_state(st)
    cmd_queue(quiet=True)    # R354: 보고 직후 남은 일 큐 갱신
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


_GENERATED_SECTIONS = {"커밋", "변경 파일", "시험", "남은 문제"}   # report 가 매번 다시 만드는 절 (나머지는 보존)


def _lease_sec() -> int:
    try:
        return max(60, int(os.environ.get("AI_COLLAB_LEASE_SEC", "1200")))
    except ValueError:
        return 1200


def _reported_after_change(st: dict, rid: str, path: str) -> bool:
    """이 요청의 보고서가 요청 파일의 마지막 변경(origin/main 커밋 시각) 뒤에 만들어졌나. 확인 불가 = False (다시 알림 쪽)."""
    at = ((st.get("requests") or {}).get(rid) or {}).get("reported_at")
    changed = _git("log", "-1", "--format=%cI", "origin/main", "--", path).strip()
    if not at or not changed:
        return False
    try:
        return datetime.fromisoformat(changed) < datetime.fromisoformat(at)       # 같은 초 = 다시 알림 쪽
    except ValueError:
        return False


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
    new, busy, reported, changed = [], [], [], False
    for path, blob in _remote_files().items():
        if seen.get(path) == blob:
            continue
        m = re.fullmatch(r"\.ai-collab/requests/(R\d{1,6})\.md", path)
        if m and m.group(1) in handled and path not in seen:   # R332 이전에 처리한 지시 (handled 만 있음) — 재실행 X
            _ack(st, path, blob)
            changed = True
            continue
        # R346 후속 9 (2026-11-20): 보고서(PARTIAL·BLOCKED)를 이미 올린 요청이 임대 시간마다 영원히 다시 전달돼
        #   (처리 확정은 연결 커밋·완료가 있어야 함 · R347~R349 = 20분마다 대기가 깨어나 할 일 없이 모델 호출) →
        #   요청 파일의 마지막 변경 뒤에 보고서가 있으면 «이 판은 보고됨» (열린 상태 유지 · 확정 X · 요청이 바뀌면 다시 전달).
        if m and _reported_after_change(st, m.group(1), path):
            reported.append(path)
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
    left = cmd_queue(quiet=True) if reported else 0   # R354: 다시 깨우지 않는 대신 남은 일을 재개 큐에 남김
    if not new:
        print(f"[ai-collab] 새 요청·검토 없음{f' (처리 중 {len(busy)}건: ' + ' '.join(busy) + ')' if busy else ''}"
              f"{f' (보고됨·미확정 {len(reported)}건 · ' + (f'남은 실행 가능 항목 {left} → next-actions collab)' if left >= 0 else '재개 큐 기록 실패 — stderr·state.json queue_error)') if reported else ''}")
        return 3
    print(json.dumps(new, ensure_ascii=False, indent=1))
    return 0


def _open_queue() -> list:
    """R354: 보고(PARTIAL·BLOCKED)는 했지만 끝나지 않은 협업 요청의 열린 하위 항목 — 정본은 원장 items.
    [(rid, status, [항목…], 항목 없음 여부)] · 협업 보고서가 있는 요청만 (사용자 대화 요청과 섞지 않음)."""
    reqs = (_state().get("requests") or {})
    out = []
    for r in _load(LEDGER, {}).get("requests", []):
        rid = r.get("id") or ""
        ent = reqs.get(rid)
        if not ent or ent.get("pruned_at") or r.get("status") == "completed":
            continue
        if r.get("verification") not in ("PARTIAL", "BLOCKED") and r.get("status") != "approval_required":
            continue
        items = [x for x in (r.get("items") or []) if x.get("state") not in ("done", "na")]
        out.append((rid, r.get("verification") or r.get("status"), items, not (r.get("items") or [])))
    return out


def cmd_queue(write: bool = True, quiet: bool = False) -> int:
    """R354: 남은 일 큐를 출력하고 next-actions 의 collab 블록에 적는다 (세션 재시작·compact 뒤 재개 주입 · 나이 무관).
    poll 이 보고된 PARTIAL 을 다시 깨우지 않는 것(R346 후속 9)은 유지 — 대신 남은 일이 여기 남아 조용히 정체하지 않는다.
    항목 없는 PARTIAL 은 «남은 일 미정리» 로 따로 표시 (조용히 빠지지 않게 · item-add 로 정리할 대상)."""
    q = _open_queue()
    lines, n_claude, n_ext = [], 0, 0
    for rid, status, items, unlisted in q:
        if unlisted:
            lines.append(f"- {rid} ({status}) — 남은 일 미정리: 보고서 «남은 것» 을 `request-ledger.py item-add {rid} …` 로 등록")
            continue
        for x in items:
            ext = x.get("owner") == "external"
            n_ext += ext
            n_claude += not ext
            lines.append(f"- {rid}#{x.get('i')} [{'external' if ext else 'claude'}] {(x.get('text') or '')[:140]}")
    head = (f"협업 요청 {len(q)}건 · 실행 가능 [claude] {n_claude} · 외부 증거 필요 [external] {n_ext}"
            f" · 미정리 {sum(1 for *_, u in q if u)} (정본: request-ledger.json items · 갱신: ai-collab-report.py queue)")
    body = (head + "\n" + "\n".join(lines)) if q else ""
    if not quiet:
        print(body or "[ai-collab] 남은 협업 요청 없음")
    if write:
        # R354 검토 P1: 자식 종료 코드를 보지 않아 기록 실패(권한·잠금·폴더 충돌)가 성공처럼 지나가 재개 큐가 낡은 채 남았다 →
        #   rc·stderr 검사 · 실패는 stderr + state.json queue_error (다음 성공 때 해제) · 재시도 1회 없음 (다음 report·poll 이 다시 시도)
        na = Path(__file__).resolve().parent / "auto-save-next-actions.py"
        err = ""
        try:
            r = subprocess.run([sys.executable, "-X", "utf8", str(na), "collab"], input=body.encode("utf-8"),
                               env={**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)}, capture_output=True, timeout=30)
            if r.returncode != 0:
                tail = (r.stderr or b"").decode("utf-8", "replace").strip().splitlines()[-1:] or [""]
                err = f"rc={r.returncode} {tail[0][:200]}"
        except (OSError, subprocess.SubprocessError) as e:
            err = f"{type(e).__name__}: {str(e)[:200]}"
        st = _state()
        if err:
            print(f"[ai-collab] collab 큐 기록 실패 — {err} (다음 세션 재개 큐가 낡았을 수 있음 · "
                  f".claude/state/next-actions.md 확인)", file=sys.stderr)
            st["queue_error"] = {"rc": err.split()[0], "detail": err,
                                 "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            saved = _save_state_quiet(st, err)
            # R354 3차 검토 P2: state 저장마저 실패하면 stderr 에만 남아 다음 세션이 놓친다 → 운영 로그에도 시각 있는 ERROR 1줄
            #   (기존 SessionStart·프롬프트 «로그 오류 자동 점검» surface_log_errors 가 .claude/logs/*.log 를 읽어 다음 세션에 주입)
            _log_queue_error(err if saved else f"{err} · state.json queue_error 기록도 실패")
            return -1
        had = st.pop("queue_error", None) is not None
        ref = _log_tail_queue_error_ref()
        if ref is not None:
            # R354 4차 검토 P2: 복구한 뒤에도 24시간 안의 ERROR 줄이 다음 세션에 다시 주입됐다 → 해소 표시 1줄을 남긴다 (스캐너가 이전 ERROR 를 뺀다)
            # R354 7차 검토 P2: 같은 접두어·다른 원인 오류까지 해소하지 않도록 같은 상관 ID(ref) 를 적는다 (ID 없는 옛 줄은 옛 형식 그대로)
            _log_queue_line(f"[RESOLVED] {_QUEUE_LOG_MARK}{f' (ref={ref})' if ref else ''} — 다음 queue 에서 복구됨 (재개 큐 재생성 완료)")
        if had and not _save_state_quiet(st, "queue_error 해제"):
            return -1
    return n_claude


_QUEUE_LOG_MARK = "collab 재개 큐 기록 실패"


def _queue_log_path() -> Path:
    return ROOT / ".claude" / "logs" / "ai-collab.log"


def _log_tail_queue_error_ref():
    """운영 로그 끝부분에서 재개 큐에 관한 마지막 줄이 아직 해소되지 않은 ERROR 면 그 상관 ID (ID 없는 옛 줄 = "") ·
    해소됐거나 없으면 None (끝 16KB 만 읽음 · 읽기 실패면 None)."""
    try:
        with _queue_log_path().open("rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - 16384))
            tail = f.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return None
    for ln in reversed(tail):
        if _QUEUE_LOG_MARK in ln:
            if "[ERROR]" not in ln or "[RESOLVED]" in ln:
                return None
            m = re.search(r"\(ref=([\w-]{6,})\)", ln)
            return m.group(1) if m else ""
    return None


def _log_queue_error(detail: str) -> bool:
    """재개 큐 기록 실패를 .claude/logs/ai-collab.log 에 남김 (state.json 과 별개 통로). 로그도 못 쓰면 stderr 만 (False).
    상관 ID: 아직 해소 안 된 같은 장애가 이어지면 같은 ID · 새 장애면 새 ID (해소 표시가 이 장애만 정확히 가리키게)."""
    import uuid
    ref = _log_tail_queue_error_ref() or uuid.uuid4().hex[:10]
    return _log_queue_line(f"[ERROR] {_QUEUE_LOG_MARK} (ref={ref}) — {detail[:300]} "
                           f"(다음 세션 재개 큐가 낡았을 수 있음 · python .claude/scripts/ai-collab-report.py queue 로 재확인)")


def _log_queue_line(text: str) -> bool:
    try:
        p = _queue_log_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {text}\n")
        return True
    except OSError as e:
        print(f"[ai-collab] 운영 로그 기록도 실패 — {type(e).__name__} (stderr 가 유일한 기록)", file=sys.stderr)
        return False


def _save_state_quiet(st: dict, context: str) -> bool:
    """R354 2차 검토: queue_error 를 적는 저장 자체가 실패하면 예외가 원래 오류를 덮었다 →
    실패도 stderr 에 따로 남기고 False (원자 교체라 기존 state.json 은 그대로 · 다음 queue·report·poll 이 다시 시도 · 재시도 루프 X)."""
    try:
        _save_state(st)
        return True
    except OSError as e:
        print(f"[ai-collab] queue_error 기록 실패 — {type(e).__name__}: {str(e)[:160]} "
              f"(기존 state.json 유지 · 원래 상황: {context[:120]})", file=sys.stderr)
        try:
            STATE.with_suffix(".tmp").unlink()
        except OSError:
            pass
        return False


_ACK_PATH = re.compile(r"\.ai-collab/(requests|reviews)/(R\d{1,6})\.md")


def _request_done(rid: str) -> str:
    """지시 처리 완료 증거 — 제목에 rid 를 적은 작업 커밋(보고서 게시 커밋 제외) 또는 원장 completed+근거. 없으면 ''.
    원장이 승인 대기·미완료(PARTIAL·BLOCKED)면 커밋이 있어도 '' (끝나지 않은 일을 확정하지 않음)."""
    req = next((r for r in _load(LEDGER, {}).get("requests", []) if r.get("id") == rid), None)
    if req and (req.get("status") == "approval_required" or
                (req.get("status") != "completed" and req.get("verification") in ("PARTIAL", "BLOCKED", "FAIL"))):
        return ""
    pat = re.compile(r"(?<![A-Za-z0-9])" + re.escape(rid) + r"(?!\d)")
    for blk in _git("log", "-n", "300", "--format=%H%x1f%s%x1e").split("\x1e"):
        parts = blk.strip("\n").split("\x1f")
        if len(parts) == 2 and pat.search(parts[1]) and not _publication_only(parts[0]):
            return f"커밋 {parts[0][:8]}"
    if req and req.get("status") == "completed" and (req.get("evidence") or "").strip():
        return "원장 completed"
    return ""


def _review_verdict(blob: str) -> str:
    """검토 파일(blob) 머리의 명시 판정 — verdict 가 approved·changes_requested 이고 reviewed_commit 이 저장소에 있는 40자 SHA 일 때만."""
    fm = _frontmatter(_git("cat-file", "-p", blob)) if blob else None
    if not fm:
        return ""
    v, c = fm.get("verdict", "").lower(), fm.get("reviewed_commit", "")
    if v in _VERDICTS and _SHA40.fullmatch(c) and _git("cat-file", "-t", c) == "commit":
        return f"판정 {v}"
    return ""


def cmd_wait(interval: float = 300.0, max_sec: float = 7 * 86400.0) -> int:
    """R333: 세션 cron 이 5분마다 모델 턴을 깨워 poll 하던 것 (실측 192턴 · 모델 호출 397 · 캐시 읽기 1.37억 토큰이 모두 «없음») →
    셸이 혼자 poll 을 반복하고 새 파일이 있을 때(0)만 끝나 Claude 를 한 번 깨운다. Bash run_in_background 로 실행 (세션과 수명 같음 · 상주 서비스 X).
    fetch 실패는 연속 3회일 때만 2 로 끝냄 (일시 장애로 확인이 멈추지 않게) · 시간 초과 = 3."""
    import time as _t
    t0 = _t.time()
    fails = 0
    while True:
        rc = cmd_poll()
        if rc == 0:
            return 0
        fails = fails + 1 if rc == 2 else 0
        if fails >= 3:
            return 2
        if _t.time() - t0 + interval > max_sec:
            print("[ai-collab] 대기 시간 끝 — 새 요청·검토 없음")
            return 3
        sys.stdout.flush()
        _t.sleep(interval)


def cmd_ack(target: str) -> int:
    """처리 확정 — 경로(.ai-collab/requests/R332.md) 또는 요청 ID(R332 = 그 ID 의 requests·reviews 중 처리 중인 것).
    R333 (외부 검토): 검증 없이 아무 경로·아무 판이나 확정하던 것 → 아래를 모두 만족할 때만 확정한다.
      ① 협업 폴더의 requests/·reviews/ 경로 ② poll 로 전달받은(inflight) 파일 ③ 전달받은 판 = origin 의 지금 판(바뀌었으면 새 판을 다시 받아 처리)
      ④ 지시 = 처리 완료 증거(연결 작업 커밋·원장 completed · 승인 대기·미완료 X) / 검토 = 머리의 명시 판정."""
    st = _state()
    inflight = st.get("inflight", {})
    if _RID.match(target):
        paths = [p for p in (f".ai-collab/requests/{target}.md", f".ai-collab/reviews/{target}.md") if p in inflight]
        if not paths:
            print(f"[ai-collab] 확정 거부: {target} 는 전달받아 처리 중인 파일이 없음 (poll 로 먼저 받아야 함)", file=sys.stderr)
            return 2
    else:
        paths = [target.replace("\\", "/")]
    remote = _remote_files()
    done, refused = [], []
    for p in paths:
        m = _ACK_PATH.fullmatch(p)
        cur = inflight.get(p) or {}
        if not m:
            refused.append(f"{p}: 협업 폴더 requests/·reviews/ 경로 아님")
        elif not cur.get("blob"):
            refused.append(f"{p}: 전달받지 않음 (poll 로 먼저 받아야 함)")
        elif remote.get(p) != cur["blob"]:
            refused.append(f"{p}: 전달 뒤 내용이 바뀜 — 새 판을 다시 받아 처리해야 함")
        else:
            why = _request_done(m.group(2)) if m.group(1) == "requests" else _review_verdict(cur["blob"])
            if not why:
                refused.append(f"{p}: 처리 완료 증거 없음 (지시 = 제목에 ID 를 적은 작업 커밋·원장 completed · 검토 = 머리의 명시 판정)")
            else:
                _ack(st, p, cur["blob"])
                done.append(f"{p} ({why})")
    if done:
        _save_state(st)
        print(f"[ai-collab] 처리 확정 {len(done)}건: {' · '.join(done)}")
    for r in refused:
        print(f"[ai-collab] 확정 거부 — {r}", file=sys.stderr)
    return 0 if done and not refused else 2


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
    if op == "queue":
        return 1 if cmd_queue(write="--no-write" not in argv[1:]) < 0 else 0
    if op == "ack" and len(argv) >= 2:
        return cmd_ack(argv[1])
    if op == "wait":
        opts = dict(zip(argv[1::2], argv[2::2]))
        try:
            return cmd_wait(float(opts.get("--interval", 300)), float(opts.get("--max-sec", 7 * 86400)))
        except ValueError:
            print("[ai-collab] --interval·--max-sec 는 초 단위 숫자", file=sys.stderr)
            return 2
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
