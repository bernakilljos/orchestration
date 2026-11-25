#!/usr/bin/env python3
"""ai-collab-report — Claude CLI ↔ ChatGPT GitHub 협업 (.ai-collab/) 보고서·요청 처리 (R325·R326 · 상주 X · 훅 X).

명령:
  report <요청ID> [--base <커밋>] [--status PASS|PARTIAL|BLOCKED] [--head <커밋> --reason <근거>]   커밋 직후 실행 → reports/<요청ID>.md + state.json 갱신
        (--head: 메시지에 요청 ID 를 빠뜨린 후속 수정 커밋을 기준 SHA 로 · base..tip 안 · 게시 전용 아님 · 자동 선택보다 최신만 ·
         --reason 8자 이상 필수 → state head_override_reason · 보고서 머리 head_override 줄 (R354 18차))
  truth-check <요청ID|경로>...                                      보고 진실 게이트 (R371 C1 · 설치·삭제·회귀·head 주장 vs 실측 · 위반 1)
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
_RID = re.compile(r"^[A-Z]{1,2}\d{1,6}$")   # 2026-11-25: 원장 R### 외에 ChatGPT 지시서 ID(L001 등) 허용 · 원장에는 "[L001] …" 로 등록


def _git(*args: str) -> str:
    try:   # R355: 시간 초과·실행 실패 예외 = 실패(반환 코드≠0)와 같게 빈 값 (예외로 대기 전체가 죽던 것)
        r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=30)
    except (subprocess.SubprocessError, OSError) as e:
        print(f"[ai-collab] git {' '.join(args[:2])} 실패: {type(e).__name__}", file=sys.stderr)
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


_REMOTE: dict = {}   # 한 실행 안에서 한 번만 조회


def _remote_ref() -> str:
    """원격 기본 브랜치 — ① origin/HEAD(symbolic-ref) ② 명시 설정(state.json "branch" 또는 env AI_COLLAB_BRANCH) 순.
    어느 쪽이든 origin/<브랜치> 커밋이 실제로 있어야 채택 · 둘 다 없으면 "" (= BLOCKED · 호출부가 알린다).
    2026-11-25: lottoclaude 기본 브랜치가 master 인데 origin/main 이 박혀 있어 지시서·리뷰를 영원히 못 봤다 (저장소마다 다름 · 고정 금지).
    R589 리뷰 1번 (11-25): main/master 추측·origin/main 최종 대체를 없앰 — 추측이 틀리면 «새 것 없음» 으로 조용히 보였다."""
    if "ref" not in _REMOTE:
        cands = [_git("symbolic-ref", "-q", "--short", "refs/remotes/origin/HEAD")]
        explicit = (os.environ.get("AI_COLLAB_BRANCH") or str(_load(STATE, {}).get("branch") or "")).strip()
        if explicit:
            cands.append(explicit if explicit.startswith("origin/") else "origin/" + explicit)
        _REMOTE["ref"] = next((c for c in cands if c and _git("rev-parse", "-q", "--verify", c + "^{commit}")), "")
    return _REMOTE["ref"]


_BLOCKED_REF = ("[ai-collab] BLOCKED: 원격 기본 브랜치를 확인할 수 없음 — origin/HEAD 없음·명시 설정(.ai-collab/state.json"
                " \"branch\" · AI_COLLAB_BRANCH) 없음 또는 그 브랜치가 원격에 없음 (`git remote set-head origin -a` 로 받기)")


def _repo_slug() -> str:
    """state.json repository 기본값 — origin URL 의 <소유자>/<저장소> · 못 읽으면 "" (다른 저장소 이름으로 채우지 않는다 · R589 리뷰 1번)."""
    m = re.search(r"[:/]([^/:\s]+/[^/\s]+?)(?:\.git)?/?$", _git("remote", "get-url", "origin"))
    return m.group(1) if m else ""


_RANK = {"BLOCKED": 0, "FAIL": 0, "PARTIAL": 1, "PASS": 2}


_PUBLICATION_EXTRA = {"guide.txt"}   # 게시 커밋에 함께 실리는 변경 기록 한 줄 (README 절차 3 · 구현 없는 회차)


def _publication_only(commit: str) -> bool:
    """이 커밋이 보고서 게시 커밋인가 — .ai-collab/ 변경이 있고 나머지는 guide.txt 뿐.
    R354 20차: 게시 커밋 c50557d4 가 guide.txt 한 줄을 실어 작업 커밋으로 판정 → 자동 head 로 뽑혔다.
    guide.txt 만 바꾼 커밋·코드가 섞인 커밋은 작업 커밋 그대로."""
    names = [n for n in _git("show", "--name-only", "--format=", commit).splitlines() if n]
    pub = [n for n in names if n.startswith(".ai-collab/")]
    return bool(pub) and all(n.startswith(".ai-collab/") or n in _PUBLICATION_EXTRA for n in names)


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
    st.setdefault("repository", _repo_slug())
    st.setdefault("requests", {})
    return st


def cmd_report(rid: str, base: str = "", status: str = "", head_override: str = "", reason: str = "") -> int:
    if not _RID.match(rid):
        print(f"[ai-collab] 요청 ID 형식 아님: {rid!r} (예: R325 · L001)", file=sys.stderr)
        return 2
    reqs = _load(LEDGER, {}).get("requests", [])
    # 원장 ID 그대로(R589) 또는 외부 지시서 ID 를 desc 머리에 "[L001] …" 로 적어 등록한 원장 항목 (2026-11-25)
    req = next((r for r in reqs if r.get("id") == rid), None) \
        or next((r for r in reqs if re.match(r"^\s*\[" + re.escape(rid) + r"\]", r.get("desc") or "")), None)
    if req is None:
        print(f"[ai-collab] 원장에 없는 요청: {rid} (원장 id 또는 desc 머리 [{rid}])", file=sys.stderr)
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
    reason = " ".join((reason or "").split())
    if head_override and len(reason) < 8:     # R354 18차: 수동 지정은 근거를 남긴다 (자동 선택 규칙을 벗어나는 결정)
        print("[ai-collab] --head 거부: --reason <근거 8자 이상> 필수 — 왜 자동 선택(제목에 요청 ID 든 최신 작업 커밋) 대신 이 SHA 인지",
              file=sys.stderr)
        return 2
    if head_override:      # R354 15차: 0cf9163f 처럼 ID 를 빠뜨린 후속 수정이 빠져 head 가 CI 실패한 앞 SHA 에 남았다
        full = _git("rev-parse", "--verify", "-q", head_override + "^{commit}")
        span = _git("rev-list", f"{base}..{tip}").split()
        why = ("커밋 없음" if not full else "보고서 게시 전용 커밋" if _publication_only(full)
               else "범위 밖 (base..tip 아님)" if full not in span
               else "자동 선택 head 보다 최신이 아님" if head not in _git("rev-list", f"{base}..{full}").split() or full == head
               else "")
        if why:
            print(f"[ai-collab] --head 거부: {head_override} — {why}", file=sys.stderr)
            return 2
        head = full
    elif ent.get("head_override") and ent.get("head_commit") and ent["head_commit"] != head:
        # R354 16차: --head 로 맞춘 뒤 생략하고 다시 보고하면 예전 ID 커밋으로 되돌아갔다 →
        #   지정 head 가 아직 base..tip 안이고 자동 선택보다 최신이면 그대로 둔다 (더 새 ID 커밋이 생기면 자동 선택)
        prev = ent["head_commit"]
        if prev in _git("rev-list", f"{base}..{tip}").split() and head in _git("rev-list", f"{base}..{prev}").split():
            head, head_override = prev, prev
            reason = ent.get("head_override_reason") or reason
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
    branch = _git("rev-parse", "--abbrev-ref", "HEAD") or "(미확인)"   # R589 리뷰 1번: "main" 추측 X
    meta = {"request_id": rid, "repository": st["repository"] or "(미확인)", "branch": branch, "base_commit": base,
            "head_commit": head, "status": status, "created_at": now, "review_required": True,
            "commit_link": "verified" if mine else "unverified"}
    if req.get("id") and req.get("id") != rid:
        meta["ledger_id"] = req["id"]            # 외부 지시서 ID 로 보고할 때 원장 번호도 남김
    if head_override:
        meta["head_override"] = f"{head} — {reason}"
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
    final = "\n".join(lines).rstrip() + "\n" + ("\n" + "\n\n".join(kept) + "\n" if kept else "")
    bad = truth_violations(final, _probe_installed() if _CLAIM_INSTALLED.search(final) else None,
                           gate_status=str(gate.get("status") or ""))
    if bad:      # R371 C1: 실제 상태와 어긋난 보고는 쓰지 않는다
        for b in bad:
            print(f"[ai-collab] 진실 게이트 위반 — 게시 거부: {b}", file=sys.stderr)
        return 3
    out.write_text(final, encoding="utf-8")
    st["requests"][rid] = {"head_commit": head, "base_commit": base, "range_tip": tip, "status": status,
                           "report": f"reports/{rid}.md", "reported_at": now, "reviewed": False, "items_sig": sig,
                           **({"head_override": True, "head_override_reason": reason} if head_override else {})}
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


# R371 C1: 보고 진실 게이트 — 보고서 문구가 실제 상태와 어긋나면 게시하지 않는다
#   (installed:false 인데 INSTALLED · 대상이 남아 있는데 삭제 완료 · 회귀 RUNNING 인데 PASS · head PENDING 인데 배포/DONE)
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_CLAIM_INSTALLED = re.compile(r"\bINSTALLED\b|installed\s*[:=]\s*true|설치\s*(완료|됨)", re.I)
_CLAIM_DELETED = re.compile(r"DELETE_DONE|삭제\s*(완료|됨)|Test-Path\s*=?\s*False", re.I)
_WIN_PATH = re.compile(r"[A-Za-z]:\\[^\s`'\"|)(\]*,·]+")
_CLAIM_DEPLOYED = re.compile(r"\b(DEPLOYED|DONE)\b|배포\s*완료")
_RUNNING = re.compile(r"\bRUNNING\b|회귀[^\n]{0,20}진행\s*중")


def _probe_installed():
    """관리자 실행기 설치 여부 (True·False · 확인 불가 None) — elevated-task.ps1 -Action Status JSON."""
    ps1 = ROOT / ".claude" / "scripts" / "elevated-task.ps1"
    if os.name != "nt" or not ps1.is_file():
        return None
    try:
        out = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1),
                              "-Action", "Status"], capture_output=True, timeout=30,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
        m = re.search(rb"\{.*\}", out, re.S)
        return bool(json.loads(m.group(0)).get("installed")) if m else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _commit_exists(sha: str) -> bool:
    return _git("cat-file", "-t", sha) == "commit"


def truth_violations(text: str, installed=None, exists=os.path.exists, gate_status: str = "",
                     commit_exists=_commit_exists) -> list:
    """보고서 본문과 실제 상태 대조 → 위반 목록 (빈 목록 = 통과). 사실값은 인자로 받아 시험에서 바꿔 끼운다.
    R371 후속 리뷰: 설치 상태 UNKNOWN 인데 설치 주장 · 삭제 주장과 경로가 다른 줄 · head 누락 · 형식만 맞는 가짜 SHA 도 막는다."""
    fm = _frontmatter(text) or {}
    status = str(fm.get("status") or "").upper()
    head = str(fm.get("head_commit") or "").strip()
    lines = text.splitlines()
    out = []
    for ln in lines:
        if _CLAIM_INSTALLED.search(ln) and not re.search(r"installed\s*[:=]\s*false|NOT_INSTALLED|미설치", ln, re.I):
            if installed is False:
                out.append(f"설치 주장인데 실측 installed:false — {ln.strip()[:100]}")
            elif installed is None:
                out.append(f"설치 상태 확인 불가(UNKNOWN)인데 설치 주장 — {ln.strip()[:100]}")
            break
    for i, ln in enumerate(lines):
        if _CLAIM_DELETED.search(ln):
            near = " ".join(lines[max(0, i - 1):i + 3])          # 주장과 경로가 다른 줄(앞 1·뒤 2줄)이어도 대조
            for p in dict.fromkeys(_WIN_PATH.findall(near)):
                if exists(p.rstrip(".")):
                    out.append(f"삭제 주장인데 대상이 아직 있음(Test-Path True) — {p}")
    body_running = any(_RUNNING.search(ln) for ln in lines)
    if status == "PASS" and (gate_status.lower() == "running" or body_running):
        out.append("회귀 게이트가 RUNNING(진행 중)인데 상태 PASS")
    claims_done = status == "PASS" or bool(_CLAIM_DEPLOYED.search(text))
    if claims_done and not _HEX40.match(head):
        out.append(f"head_commit 이 실제 40자리 SHA 가 아님({head or '누락'}) — PASS·DEPLOYED·DONE 주장 불가")
    elif claims_done and not commit_exists(head):
        out.append(f"head_commit {head[:12]} 이 저장소에 없는 커밋 — PASS·DEPLOYED·DONE 주장 불가")
    return out


def cmd_truth_check(target: str) -> int:
    p = COLLAB / "reports" / f"{target}.md" if _RID.match(target) else Path(target)
    if not p.is_file():
        print(f"[ai-collab] 보고서 없음: {p}", file=sys.stderr)
        return 2
    text = p.read_text(encoding="utf-8", errors="replace")
    inst = _probe_installed() if _CLAIM_INSTALLED.search(text) else None
    bad = truth_violations(text, inst, gate_status=str(_load(GATE, {}).get("status") or ""))
    for b in bad:
        print(f"[ai-collab] 진실 게이트 위반 {p.name}: {b}", file=sys.stderr)
    if not bad:
        print(f"[ai-collab] 진실 게이트 통과: {p.name}")
    return 1 if bad else 0


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
    """이 요청의 보고서가 요청 파일의 마지막 변경(원격 기본 브랜치 커밋 시각) 뒤에 만들어졌나. 확인 불가 = False (다시 알림 쪽)."""
    at = ((st.get("requests") or {}).get(rid) or {}).get("reported_at")
    ct = _last_commit_times().get(path)        # R375 5차: 파일마다 git log 대신 한 번 읽은 경로별 시각
    if not at or ct is None:
        return False
    try:
        a = datetime.fromisoformat(at)
        changed = datetime.fromtimestamp(ct, tz=timezone.utc) if a.tzinfo else datetime.fromtimestamp(ct)
        return changed < a       # 같은 초 = 다시 알림 쪽
    except (ValueError, OverflowError, OSError):
        return False


def _remote_files() -> dict:
    """원격 기본 브랜치(_remote_ref) 의 requests/·reviews/ 파일 {경로: blob} (.gitkeep 제외)."""
    out = {}
    if not _remote_ref():          # BLOCKED — 빈 브랜치 이름으로 조회하면 «파일 없음» 으로 보인다
        return out
    for ln in _git("ls-tree", "-r", _remote_ref(), "--", ".ai-collab/requests", ".ai-collab/reviews").splitlines():
        meta, _, path = ln.partition("\t")
        if path and not path.endswith(".gitkeep") and meta:
            out[path] = meta.split()[-1]
    return out


def _ack(st: dict, path: str, blob: str) -> None:
    """처리 확정 — 이 내용(blob)은 다시 알리지 않는다. 처리 중 표시는 지운다."""
    st.setdefault("seen", {})[path] = blob
    st.setdefault("inflight", {}).pop(path, None)


_LAST_CT: dict = {}   # 한 번의 확인(pending·poll) 동안만 쓰는 {경로: 마지막 커밋 시각} — git log 1회로 전부
#   (R375 5차: 파일마다 git log 2회 = 실측 54회·7초 → 세션 시작 훅 10초 제한에서 잘려 미처리 리뷰가 주입되지 않음)
#   확인을 시작할 때마다 비운다 (fetch 로 원격 기본 브랜치가 바뀌었을 수 있음 · 오래 도는 wait 루프에서도 최신).


def _last_commit_times() -> dict:
    """원격 기본 브랜치 기준 .ai-collab/ 아래 경로별 마지막 커밋 시각 (이번 확인 안에서는 다시 읽지 않는다)."""
    if "t" in _LAST_CT:
        return _LAST_CT["t"]
    out: dict = {}
    ct = None
    if not _remote_ref():
        _LAST_CT["t"] = out
        return out
    for ln in _git("log", "--format=@@CT %ct", "--name-only", _remote_ref(), "--", ".ai-collab").splitlines():
        if ln.startswith("@@CT "):
            ct = ln[5:].strip()
        elif ln.strip() and ct and ct.isdigit():
            out.setdefault(ln.strip(), int(ct))   # 최신 커밋부터 나오므로 처음 본 값 = 마지막 커밋
    _LAST_CT["t"] = out
    return out


def _report_newer_on_remote(rid: str, path: str) -> bool:
    """원격 기본 브랜치에서 reports/<rid>.md 의 마지막 커밋이 지시·리뷰 파일의 마지막 커밋보다 나중이면 True (그 판은 보고됨)."""
    times = _last_commit_times()
    rep, src = times.get(f".ai-collab/reports/{rid}.md"), times.get(path)
    return bool(rep is not None and src is not None and rep > src)


def pending_lines(fetch_timeout: float = 8.0) -> list:
    """R372: 세션 시작용 읽기 전용 확인 — 처리 확정(seen) 안 된 requests/·reviews/ 를 한 줄씩 (inflight·state 쓰기 X).
    fetch 가 안 되면 이미 받아 둔 원격 기본 브랜치 기준으로 (오프라인이어도 아는 만큼은 알린다)."""
    _LAST_CT.clear()
    out = []
    try:
        r = subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "origin"], capture_output=True, text=True,
                           timeout=fetch_timeout)
        if r.returncode != 0:
            out.append(f"(원격 확인 실패 — 마지막으로 받아 둔 {_remote_ref()} 기준)")
    except (subprocess.SubprocessError, OSError):
        out.append(f"(원격 확인 시간 초과 — 마지막으로 받아 둔 {_remote_ref()} 기준)")
    if not _remote_ref():                       # R589 리뷰 1번: 브랜치 미확인 = «없음» 이 아니라 BLOCKED
        return out + [_BLOCKED_REF]
    st = _state()
    seen, handled = st.get("seen", {}), st.get("handled", {})
    items = []
    for path, blob in sorted(_remote_files().items()):
        if seen.get(path) == blob:
            continue
        m = re.fullmatch(r"\.ai-collab/(requests|reviews)/([A-Z]{1,2}\d{1,6})\.md", path)
        if not m:
            continue
        kind, rid = m.groups()
        if kind == "requests" and (rid in handled and path not in seen or _reported_after_change(st, rid, path)):
            continue
        if _report_newer_on_remote(rid, path):   # 워터마크 = git 이력 (세션·state 와 무관): 이 판 뒤에 보고서가 올라갔으면 처리된 판
            continue
        if kind == "reviews":
            v = _review_verdict(blob) or "판정 없음"
            if v.endswith("approved"):
                continue
            items.append(f"- 리뷰 {rid}: {v} → 지적 사항 수정·시험·push·보고 (`{path}`)")
        else:
            items.append(f"- 지시 {rid}: 미처리 → 읽고 실행 (`{path}`)")
    return (out + items) if items else []


def cmd_poll() -> int:
    """R330 5분 주기 확인 1회분 — origin 을 받아 requests/·reviews/ 에서 아직 처리 확정 안 된 파일만 알린다.
    새 파일 있음 = 0 (내용 출력 · «처리 중» 표시) · 없음·처리 중만 = 3 · fetch 실패 = 2 · 원격 기본 브랜치 미확인 = 4 (BLOCKED). 실행·승인으로 간주하지 않는다.
    R332 (외부 검토): 알리기만 해도 seen(처리 확정)으로 적어, 세션이 처리 도중 끊기면 다음 주기에 사라지던 것 →
    poll 은 inflight(처리 중 · 임대 시간)만 적고, 처리 확정(seen)은 보고(report)·ack 가 적는다.
    임대 시간 안 = 다른 주기·세션이 같은 요청을 겹쳐 받지 않음 · 지나면 다시 전달 (중단·재시작 복구)."""
    _LAST_CT.clear()
    try:
        r = subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "origin"], capture_output=True, text=True, timeout=60)
    except (subprocess.SubprocessError, OSError) as e:   # R355: 시간 초과 = fetch 실패 (2)
        print(f"[ai-collab] fetch 실패: {type(e).__name__}", file=sys.stderr)
        return 2
    if r.returncode != 0:
        print(f"[ai-collab] fetch 실패: {(r.stderr or '').strip()[:160]}", file=sys.stderr)
        return 2
    if not _remote_ref():                       # R589 리뷰 1번: fetch 성공·브랜치 미확인 = BLOCKED 4 (정상 무변경 3 과 구별)
        print(_BLOCKED_REF, file=sys.stderr)
        return 4
    st = _state()
    seen = st.setdefault("seen", {})
    inflight = st.setdefault("inflight", {})
    handled = st.get("handled", {})
    now = datetime.now(timezone.utc)
    new, busy, reported, changed = [], [], [], False
    for path, blob in _remote_files().items():
        if seen.get(path) == blob:
            continue
        m = re.fullmatch(r"\.ai-collab/requests/([A-Z]{1,2}\d{1,6})\.md", path)
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
        # R375 후속 (2026-11-24): 세션 시작 목록(pending_lines)과 대기(poll)의 «보고됨» 판정이 달랐다 —
        #   poll 은 state.json 기록만 봐서 손으로 쓴 보고서(R363·R364 등)가 있는 지시·리뷰를 계속 «새 것» 으로 돌려
        #   wait 가 켜지자마자 끝났다 (리뷰를 기다리는 루프가 실제로는 돌지 못함). → 같은 git 이력 워터마크를 쓴다.
        mr = m or re.fullmatch(r"\.ai-collab/reviews/([A-Z]{1,2}\d{1,6})\.md", path)
        if mr and _report_newer_on_remote(mr.group(1), path):
            reported.append(path)
            continue
        if not m and mr and _review_verdict(blob).endswith("approved"):   # 승인 리뷰 = 할 일 없음 (pending 과 같은 기준)
            _ack(st, path, blob)
            changed = True
            continue
        cur = inflight.get(path) or {}
        same = cur.get("blob") == blob
        n = int(cur.get("n", 0) or 0) if same else 0
        if same:
            try:
                age = (now - datetime.fromisoformat(cur.get("at", ""))).total_seconds()
            except ValueError:
                age = _lease_sec()
            # R364 (2026-11-23): 내용이 그대로인데 20분마다 무기한 재전달(백오프 없음) → 재전달할 때마다 간격 2배 (최대 16배)
            if age < _lease_sec() * (2 ** min(n, 4)):
                busy.append(path)
                continue
        new.append({"path": path, "blob": blob, "text": _git("cat-file", "-p", blob)[:4000],
                    "redelivery": bool(cur)})
        inflight[path] = {"blob": blob, "at": now.isoformat(timespec="seconds"), "n": (n + 1) if same else 0}
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
        # R354 11차 검토: 해소 표시를 먼저 남기고 queue_error 해제가 실패하면 «다 복구» 가 아닌데 해소로 보였다 → 해제 성공 뒤에만
        if had and not _save_state_quiet(st, "queue_error 해제"):
            return -1
        ref = _log_tail_queue_error_ref()
        if ref is not None:
            # R354 4차 검토 P2: 복구한 뒤에도 24시간 안의 ERROR 줄이 다음 세션에 다시 주입됐다 → 해소 표시 1줄을 남긴다 (스캐너가 이전 ERROR 를 뺀다)
            # R354 7차 검토 P2: 같은 접두어·다른 원인 오류까지 해소하지 않도록 같은 상관 ID(ref) 를 적는다 (ID 없는 옛 줄은 옛 형식 그대로)
            _log_queue_line(f"[RESOLVED] {_QUEUE_LOG_MARK}{f' (ref={ref})' if ref else ''} — 다음 queue 에서 복구됨 (재개 큐 재생성 완료)")
        # (queue_error 해제 저장은 해소 표시 앞으로 옮김 · R354 11차)
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


_ACK_PATH = re.compile(r"\.ai-collab/(requests|reviews)/([A-Z]{1,2}\d{1,6})\.md")


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
        try:
            rc = cmd_poll()
        except (subprocess.SubprocessError, OSError) as e:   # R355: 일시 조회 실패 예외 = fetch 실패와 같이 세고 다음 주기에 재시도
            print(f"[ai-collab] 확인 실패 (다음 주기 재시도): {type(e).__name__}", file=sys.stderr)
            rc = 2
        if rc in (0, 4):                        # 4 = BLOCKED (설정 문제 · 기다려도 안 풀림 → 바로 끝내 알림)
            return rc
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
    remote = _remote_files() if _remote_ref() else None   # None = BLOCKED (원격 판 대조가 필요한 단계에서만 4)
    blocked = False
    done, refused = [], []
    for p in paths:
        m = _ACK_PATH.fullmatch(p)
        cur = inflight.get(p) or {}
        if not m:
            refused.append(f"{p}: 협업 폴더 requests/·reviews/ 경로 아님")
        elif not cur.get("blob"):
            refused.append(f"{p}: 전달받지 않음 (poll 로 먼저 받아야 함)")
        elif remote is None:
            blocked = True
            refused.append(f"{p}: 원격 판 대조 불가 — {_BLOCKED_REF}")
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
    return 0 if done and not refused else (4 if blocked else 2)


def main(argv: list) -> int:
    if not argv:
        print(__doc__)
        return 2
    op = argv[0]
    if op == "report" and len(argv) >= 2:
        opts = dict(zip(argv[2::2], argv[3::2]))
        return cmd_report(argv[1], opts.get("--base", ""), opts.get("--status", ""), opts.get("--head", ""),
                          opts.get("--reason", ""))
    if op == "check-requests":
        return cmd_check_requests()
    if op == "pending":
        lines = pending_lines()
        print("\n".join(lines) if lines else "[ai-collab] 미처리 지시·리뷰 없음")
        return 0 if lines else 3
    if op == "truth-check" and len(argv) >= 2:
        return max(cmd_truth_check(t) for t in argv[1:])
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
