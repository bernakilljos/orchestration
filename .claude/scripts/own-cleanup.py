"""자기 작업 산출물 자동 정리 + 불필요한 자기 승인 요청 자동 취소 (2026-11-16 R258).

사용자 지시: "Claude 가 만든 임시 파일·불필요한 승인 요청을 사용자에게 정리하라고 떠넘기지 마라 ·
자동 승인 X · 자기 요청 자동 취소 O · 소유를 확인한 산출물만 삭제 · rm -rf 무조건 실행 X".

정리 대상 (셋 다 «임시 폴더(tempfile.gettempdir()) 안» 이어야 하고 사용 중이 아니어야 한다):
  ① kit 코드가 만드는 이름의 임시 폴더 (KIT_TEMP_PREFIXES · 근거 = kit 안의 mkdtemp(prefix=…) 호출) — 1시간 넘게 안 쓴 것
  ② 끝난 세션의 Claude 작업 폴더 <TEMP>/claude/<프로젝트>/<세션>/scratchpad — 지금 세션과 같은 프로젝트의 다른 세션 · 24시간 넘게 안 쓴 것
  ③ register 로 등록한 산출물 — 10분 넘게 안 쓴 것 (등록 = 생성 시점 추적)
지키는 것: 임시 폴더 밖 · 임시 폴더 자체 · kit·대상 프로젝트 · 링크·정션이 가리키는 곳(링크 자체만 지움) · 지금 세션 작업 폴더.

승인 요청 자동 취소: 대기 중인 게이트 요청 중 «임시 폴더 안만 지우는 명령» (data_loss · 절대 경로가 전부 임시 폴더 안 ·
  홈·프로젝트 변수·명령 치환 없음) 은 이 정리가 대신하므로 취소한다 (approval-gate.withdraw = 대기 → 만료 · 승인 아님).
  그 밖의 요청은 손대지 않고 «남은 승인 요청» 으로 기록만 한다.

사용:
  python own-cleanup.py run [--session <id>] [--dry]     (Stop·SessionEnd 훅 입력 JSON 을 stdin 으로 받아도 됨)
  python own-cleanup.py register <경로> [--session <id>]
결과: .claude/state/own-cleanup.json (마지막 결과) · .claude/logs/own-cleanup.log (1줄씩)
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import stat
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
STATE = ROOT / ".claude" / "state" / "own-cleanup.json"
REG = ROOT / ".claude" / "state" / "own-artifacts.json"
LOG = ROOT / ".claude" / "logs" / "own-cleanup.log"

# kit 안 mkdtemp(prefix=…) 호출에서 온 이름 (시험 test_kit_prefixes_match_kit_code 가 대조)
KIT_TEMP_PREFIXES = ("r256-kit-", "agd-kit-", "tgt-iso-", "regress-base-", "orca-vertical-")
IDLE_PREFIX_SEC = 3600
IDLE_SCRATCH_SEC = 24 * 3600
IDLE_REG_SEC = 600
BUDGET_SEC = 6.0
_PROTECT_ENV = ("CLAUDE_PROJECT_DIR",)


def _temp_root() -> Path:
    return Path(os.path.realpath(tempfile.gettempdir()))


def _real(p) -> Path:
    return Path(os.path.realpath(str(p)))


def _inside(child: Path, parent: Path) -> bool:
    try:
        c, p = os.path.normcase(str(child)), os.path.normcase(str(parent))
        return os.path.commonpath([c, p]) == p and c != p
    except ValueError:
        return False


def _is_link(p: str) -> bool:
    try:
        if os.path.islink(p) or (hasattr(os.path, "isjunction") and os.path.isjunction(p)):
            return True
        # Python 3.11 이하엔 os.path.isjunction 이 없어 Windows 정션이 일반 폴더로 보이고 _entries 가 그 안으로 들어갔다
        #   (2026-11-18 병합 실측 · 3.11.9: islink False · is_dir(nofollow) True · reparse 속성 True). 재분석 지점이면 전부 링크로 본다.
        return bool(getattr(os.lstat(p), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    except OSError:
        return False


def _protected() -> list:
    out = [_real(ROOT)]
    for k in _PROTECT_ENV:
        if os.environ.get(k):
            out.append(_real(os.environ[k]))
    return out


def _entries(top: str):
    """(경로, 링크·정션 여부, 폴더 여부) 를 아래에서 위 순서로. 링크·정션 안으로는 절대 들어가지 않는다.
    R258 실측: os.walk(followlinks=False) 는 Windows 정션 안으로 들어가 바깥 원본 파일까지 지웠다 (시험이 잡음)."""
    try:
        it = list(os.scandir(top))
    except OSError:
        return
    for e in it:
        link = _is_link(e.path)
        try:
            isdir = (not link) and e.is_dir(follow_symlinks=False)
        except OSError:
            isdir = False
        if isdir:
            yield from _entries(e.path)
        yield e.path, link, isdir


def _newest_mtime(p: Path) -> float:
    """폴더 안 가장 최근 수정 시각 (링크·정션은 따라가지 않고 그 자체 시각도 세지 않음) — 사용 중 판정."""
    try:
        newest = os.lstat(p).st_mtime
    except OSError:
        return time.time()
    if p.is_dir() and not _is_link(str(p)):
        for q, link, _d in _entries(str(p)):
            if link:
                continue
            try:
                newest = max(newest, os.lstat(q).st_mtime)
            except OSError:
                pass
    return newest


def safe_target(p: Path) -> str | None:
    """지워도 되는지 — 안 되면 사유 문자열, 되면 None."""
    tmp = _temp_root()
    rp = _real(p)
    if not _inside(rp, tmp):
        return "임시 폴더 밖"
    for pr in _protected():
        if rp == pr or _inside(pr, rp) or _inside(rp, pr):
            return "보호 대상(프로젝트) 포함·내부"
    return None


def _remove(p: Path) -> int:
    """링크를 따라가지 않고 지운다 · 읽기 전용 파일도 (git 객체). 지운 항목 수."""
    n = 0
    sp = str(p)
    if _is_link(sp):
        try:
            os.rmdir(sp) if os.path.isdir(sp) else os.unlink(sp)
            return 1
        except OSError:
            return 0
    if not p.is_dir():
        try:
            os.chmod(sp, stat.S_IWRITE)
            os.unlink(sp)
            return 1
        except OSError:
            return 0
    for q, link, isdir in _entries(sp):
        try:
            if link:             # 링크·정션 = 그 자체만 제거 (가리키는 곳 X)
                try:
                    os.rmdir(q)
                except OSError:
                    os.unlink(q)
            elif isdir:
                os.rmdir(q)
            else:
                os.chmod(q, stat.S_IWRITE)
                os.unlink(q)
            n += 1
        except OSError:
            pass
    try:
        os.rmdir(sp)
        n += 1
    except OSError:
        pass
    return n


def _registered() -> list:
    try:
        return json.loads(REG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def register(path: str, session: str = "") -> dict:
    p = Path(path)
    why = safe_target(p)
    if why:
        return {"error": f"등록 안 함 — {why}: {path}"}
    items = [x for x in _registered() if x.get("path") != str(_real(p))]
    items.append({"path": str(_real(p)), "session": session, "registered_at": int(time.time())})
    REG.parent.mkdir(parents=True, exist_ok=True)
    REG.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"registered": str(_real(p))}


def candidates(session: str, now: float) -> list:
    """(경로, 종류, 최소 미사용 초)"""
    tmp = _temp_root()
    out = []
    try:
        for e in os.scandir(tmp):
            if e.name.startswith(KIT_TEMP_PREFIXES):
                out.append((Path(e.path), "kit-temp", IDLE_PREFIX_SEC))
    except OSError:
        pass
    croot = tmp / "claude"
    # 끝난 세션 작업 폴더: 지금 세션을 알 때만 · 지금 세션과 같은 프로젝트 폴더의 다른 세션만 (다른 프로젝트 세션은 살아 있을 수 있음)
    projs = [p for p in croot.iterdir() if (p / session).is_dir()] if (session and croot.is_dir()) else []
    if projs:
        for proj in projs:
            if not proj.is_dir() or _is_link(str(proj)):
                continue
            try:
                sessions = list(proj.iterdir())
            except OSError:
                continue
            for s in sessions:
                sp = s / "scratchpad"
                if s.name != session and sp.is_dir() and not _is_link(str(sp)) and \
                        re.fullmatch(r"[0-9a-f-]{36}", s.name):
                    out.append((sp, "ended-scratchpad", IDLE_SCRATCH_SEC))
    for x in _registered():
        out.append((Path(x["path"]), "registered", IDLE_REG_SEC))
    return out


# ── 자기 승인 요청 자동 취소 ──────────────────────────────────────────
_RX_DELETE = re.compile(r"\brm\s+-[a-z]*r|\brmtree\b|\bremove-item\b|\brmdir\b|\brd\s+/s", re.I)
_RX_ABS = re.compile(r"(?:[A-Za-z]:[\\/]|(?<![\w.])/[a-z]/)[^\s\"';|&)]+")
_RX_DISQ = re.compile(r"\$HOME|\$\{?HOME|~[/\\]|(?<![\w])~(?=\s|$)|\$\{?CLAUDE_PROJECT_DIR|\$\{?USERPROFILE|%[A-Za-z_]+%|\$\(|`|\.\.[/\\]")


def _to_win(p: str) -> str:
    m = re.match(r"^/([a-z])/(.*)$", p)
    return f"{m.group(1).upper()}:/{m.group(2)}" if m else p


def temp_only_delete(command: str) -> bool:
    """임시 폴더 안만 지우는 명령인가 (보수적: 하나라도 불확실하면 False)."""
    if not command or not _RX_DELETE.search(command) or _RX_DISQ.search(command):
        return False
    paths = _RX_ABS.findall(command)
    if not paths:
        return False
    tmp = _temp_root()
    return all(_inside(_real(_to_win(p)), tmp) for p in paths)


def _gate():
    spec = importlib.util.spec_from_file_location("approval_gate_oc", ROOT / ".claude" / "scripts" / "approval-gate.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def review_approvals(dry: bool) -> dict:
    withdrawn, remaining = [], []
    try:
        g = _gate()
        waiting = g.list_waiting()
    except Exception as e:  # noqa: BLE001 — 조회 실패는 기록만 (정리를 막지 않음)
        return {"error": type(e).__name__, "withdrawn": [], "remaining": []}
    for w in waiting:
        st = g.status(w["task_id"])
        cmd = ((st.get("risk_detail") or {}).get("command")) or ""
        if st.get("risk_category") == "data_loss" and temp_only_delete(cmd):
            if not dry:
                r = g.withdraw(w["task_id"], "임시 폴더 안만 지우는 자기 요청 — own-cleanup 이 소유·범위 확인 후 정리 (R258)",
                               by="own-cleanup")
                if r.get("state") != "expired":
                    remaining.append({"task_id": w["task_id"], "why": r.get("error", "취소 실패")})
                    continue
            withdrawn.append(w["task_id"])
        else:
            remaining.append({"task_id": w["task_id"], "category": w.get("category"),
                              "command": (w.get("command_preview") or "")[:80]})
    return {"withdrawn": withdrawn, "remaining": remaining}


def run(session: str = "", dry: bool = False, now: float | None = None) -> dict:
    now = time.time() if now is None else now
    t0 = time.monotonic()
    removed, kept, deferred = [], [], 0
    for p, kind, idle in candidates(session, now):
        if not os.path.lexists(str(p)):
            continue
        if time.monotonic() - t0 > BUDGET_SEC:   # Stop 훅 제한(10초) 안에서 끝내고 나머지는 다음 작업 종료 때 (첫 실행 96개 10.4초 실측)
            deferred += 1
            continue
        why = safe_target(p)
        if not why and now - _newest_mtime(p) < idle:
            why = f"사용 중 ({idle // 60}분 안에 수정)"
        if why:
            kept.append({"path": str(p), "kind": kind, "why": why})
            continue
        n = 0 if dry else _remove(p)
        removed.append({"path": str(p), "kind": kind, "items": n})
    if not dry:   # 등록 목록에서 사라진 것 정리
        left = [x for x in _registered() if os.path.lexists(x.get("path", ""))]
        if REG.exists():
            REG.write_text(json.dumps(left, ensure_ascii=False, indent=1), encoding="utf-8")
    appr = review_approvals(dry)
    res = {"at": time.strftime("%Y-%m-%d %H:%M:%S"), "session": session, "dry": dry,
           "removed": removed, "kept": kept[:50], "kept_count": len(kept), "deferred": deferred, "approvals": appr}
    if not dry:
        try:
            STATE.parent.mkdir(parents=True, exist_ok=True)
            STATE.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
            LOG.parent.mkdir(parents=True, exist_ok=True)
            with LOG.open("a", encoding="utf-8") as f:
                f.write(f"{res['at']} 정리 {len(removed)} · 보존 {len(kept)} · 승인 취소 {len(appr.get('withdrawn', []))} "
                        f"· 남은 승인 {len(appr.get('remaining', []))} {[r['task_id'] for r in appr.get('remaining', [])]}\n")
        except OSError:
            pass
    return res


def _arg(name: str) -> str:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv[:-1] else ""


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    session = _arg("--session")
    if not session and not sys.stdin.isatty():
        try:
            session = (json.loads(sys.stdin.read() or "{}") or {}).get("session_id", "")
        except (ValueError, OSError):
            session = ""
    if cmd == "run":
        r = run(session, dry="--dry" in sys.argv)
        print(json.dumps({k: (v if k != "kept" else v[:5]) for k, v in r.items()}, ensure_ascii=False, indent=1))
        return 0
    if cmd == "register" and len(sys.argv) > 2:
        r = register(sys.argv[2], session)
        print(json.dumps(r, ensure_ascii=False))
        return 1 if "error" in r else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
