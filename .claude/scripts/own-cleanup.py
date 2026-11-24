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
PROG = ROOT / ".claude" / "state" / "own-cleanup-progress.json"   # 지우기 시작한 끝난 세션 폴더 (예산 초과로 남은 것 이어 지우기)
LOG = ROOT / ".claude" / "logs" / "own-cleanup.log"

# kit 안 mkdtemp(prefix=…) 호출에서 온 이름 (시험 test_kit_prefixes_match_kit_code 가 대조)
KIT_TEMP_PREFIXES = ("r256-kit-", "agd-kit-", "tgt-iso-", "regress-base-", "orca-vertical-")
IDLE_PREFIX_SEC = 3600
IDLE_SCRATCH_SEC = 24 * 3600
IDLE_REG_SEC = 600
BUDGET_SEC = float(os.environ.get("OWN_CLEANUP_BUDGET_SEC", "6"))   # Stop 훅 제한(10초) 안 · 확인·삭제가 함께 쓰는 예산
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


def _entries(top: str, errs: list | None = None):
    """(경로, 링크·정션 여부, 폴더 여부) 를 아래에서 위 순서로. 링크·정션 안으로는 절대 들어가지 않는다.
    R258 실측: os.walk(followlinks=False) 는 Windows 정션 안으로 들어가 바깥 원본 파일까지 지웠다 (시험이 잡음).
    R375 4차 검토: 읽기 실패를 조용히 건너뛰면 «안 본 곳» 이 «변경 없음» 이 된다 → errs 에 모아 부르는 쪽이 보존 판정."""
    try:
        with os.scandir(top) as sc:
            it = list(sc)
    except OSError as e:
        if errs is not None:
            errs.append(f"폴더 읽기 실패 ({type(e).__name__}) {top}")
        return
    for e in it:
        link = _is_link(e.path)
        try:
            isdir = (not link) and e.is_dir(follow_symlinks=False)
        except OSError as ex:
            isdir = False
            if errs is not None:
                errs.append(f"폴더 판정 실패 ({type(ex).__name__}) {e.path}")
        if isdir:
            yield from _entries(e.path, errs)
        yield e.path, link, isdir


def _newest_mtime(p: Path, errs: list | None = None, deadline: float | None = None, files_only: bool = False) -> float:
    """폴더 안 가장 최근 수정 시각 (링크·정션은 따라가지 않고 그 자체 시각도 세지 않음) — 사용 중 판정.
    읽기 실패·시간 예산 초과는 errs 에 사유를 넣고 «지금» 을 돌려준다 (확인 못 한 것 = 최근 사용으로 · 보존).
    files_only: 폴더 시각 제외 (지우는 중에는 폴더 시각이 삭제 때문에 바뀐다)."""
    errs = [] if errs is None else errs
    try:
        newest = 0.0 if files_only else os.lstat(p).st_mtime
    except OSError as e:
        errs.append(f"시각 확인 실패 ({type(e).__name__}) {p}")
        return time.time()
    if p.is_dir() and not _is_link(str(p)):
        for q, link, isdir in _entries(str(p), errs):
            if deadline is not None and time.monotonic() > deadline:
                errs.append("시간 예산 소진 (변경 확인 미완료 · 다음 실행)")
                return time.time()
            if link or (files_only and isdir):
                continue
            try:
                newest = max(newest, os.lstat(q).st_mtime)
            except FileNotFoundError:
                pass                      # 확인 사이 사라진 항목 = 잃을 것 없음
            except OSError as e:
                errs.append(f"시각 확인 실패 ({type(e).__name__}) {q}")
    return time.time() if errs else newest


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


def _session_last_active(sid: str) -> float | None:
    """R391 (2026-11-24 디스크 22% 남음 · 끝난 세션 복제본 24.8GB 4일째 남음): 세션이 끝났는지 = 그 세션 대화 기록
    (<설정 폴더>/projects/*/<sid>.jsonl) 의 마지막 수정 시각. 폴더 안 최신 파일 시각은 바깥 도구가 복제본 안 git 객체를
    건드리기만 해도 갱신돼 끝난 세션이 영원히 «사용 중» 이 됐다. 기록을 못 찾으면 None (= 종전 판정)."""
    bases = []
    for env in ("CLAUDE_CONFIG_DIR",):
        if os.environ.get(env):
            bases.append(Path(os.environ[env]))
    bases.append(Path.home() / ".claude")
    best = None
    for b in bases:
        try:
            for f in (b / "projects").glob(f"*/{sid}.jsonl"):
                m = os.lstat(f).st_mtime
                best = m if best is None else max(best, m)
        except OSError:
            continue
    return best


# R375 2차 검토 P0 (2026-11-25): 대화 기록이 오래됐다는 것만으로 끝난 세션이라 단정하면 그 폴더를 아직 쓰는
#   워커·외부 도구·미Push 작업을 지울 수 있다 → 아래 넷 중 하나라도 해당하거나 확인이 불확실하면 보존하고,
#   지우기 직전에 한 번 더 확인한다. (대화 기록 판정은 그대로 — 바깥 도구의 1회 접촉이 영원히 보존시키던 R391 결함 방지)
RECENT_WRITE_SEC = int(os.environ.get("OWN_CLEANUP_RECENT_WRITE_SEC", "3600"))   # 이 시간 안 파일 변경 = 사용 중
_LEDGER_OPEN = ("pending", "implemented")   # request-ledger.py 의 «열린 요청» 과 같은 상태


def _birth(p: Path) -> float:
    st = os.stat(p)
    return getattr(st, "st_birthtime", None) or st.st_ctime


_PROCS: tuple | None = None   # run() 1차 판정 동안만 쓰는 프로세스 목록 (삭제 직전 재확인은 항상 새로 읽음)


def _proc_snapshot() -> tuple:
    import psutil
    nd = object()
    return (psutil.Process().username(),
            list(psutil.process_iter(["pid", "name", "cmdline", "cwd", "username", "create_time"], ad_value=nd)), nd)


def _still_running(pr) -> bool:
    try:
        return bool(pr.is_running())
    except Exception:  # noqa: BLE001 — 확인 불가 = 살아 있다고 본다 (보존 쪽)
        return True


def _users_of(p: Path, sid: str) -> str | None:
    """그 폴더를 작업 위치·인자로 쓰거나 세션 번호를 인자로 가진 실행 중 프로세스. 확인 불가 = 사유 문자열(보존).
    R375 3차 검토: 작업 위치·인자를 못 읽는 프로세스를 «안 씀» 으로 치지 않는다 — 같은 사용자 프로세스가 그 폴더가 생긴 뒤에
    시작됐는데 못 읽으면 그 세션이 띄운 것일 수 있어 보존 (로그인 때 뜬 상주 프로세스는 폴더보다 먼저라 제외 · 실측 186개 중 6개)."""
    try:
        import psutil
    except ImportError:
        return "프로세스 확인 불가 (psutil 없음)"
    key = os.path.normcase(str(_real(p)))
    try:
        born = _birth(p)
        me, procs, nd = _PROCS if _PROCS else _proc_snapshot()
    except Exception as e:  # noqa: BLE001
        return f"프로세스 확인 불가 ({type(e).__name__})"
    unknown = []
    for pr in procs:
        info = pr.info
        cwd, cmd = info.get("cwd"), info.get("cmdline")
        if isinstance(cwd, str) and cwd and (os.path.normcase(cwd) == key or _inside(Path(os.path.normcase(cwd)), Path(key))):
            return f"사용 중 프로세스 (작업 위치 · pid {info.get('pid')} {info.get('name')})"
        args = " ".join(cmd) if isinstance(cmd, list) else ""
        if args and (key in os.path.normcase(args).replace("/", os.sep) or (sid and sid in args)):
            return f"사용 중 프로세스 (인자 · pid {info.get('pid')} {info.get('name')})"
        if (cwd is nd or cmd is nd) and info.get("username") == me:   # 사용자를 못 읽는 것 = 다른 계정·시스템 (실측 · 우리 임시 폴더 밖)
            ct = info.get("create_time")
            if not isinstance(ct, (int, float)) or ct >= born:
                unknown.append(pr)
    unknown = [pr for pr in unknown if _still_running(pr)]   # 그새 끝난 프로세스는 폴더를 쓸 수 없다 (짧게 뜬 find·bash 등)
    if unknown:
        unknown = [f"{pr.info.get('pid')} {pr.info.get('name')}" for pr in unknown]
        return f"프로세스 확인 불가 (폴더 생성 뒤 시작 · 작업 위치 못 읽음 {unknown[:3]})"
    return None


def _open_ledger(sid: str) -> str | None:
    f = ROOT / ".claude" / "state" / "request-ledger.json"
    if not f.exists():
        return None
    try:
        reqs = json.loads(f.read_text(encoding="utf-8")).get("requests") or []
    except (OSError, ValueError, AttributeError):
        return "작업 원장 읽기 실패"
    open_ = [r.get("id") for r in reqs if r.get("session_id") == sid and r.get("status") in _LEDGER_OPEN]
    return f"그 세션의 열린 요청 {open_[:3]}" if open_ else None


SCAN_SEC = float(os.environ.get("OWN_CLEANUP_SCAN_SEC", "20"))   # 저장소 찾기 상한 — 넘으면 «탐색 미완료» 로 보존
# 무시(ignored) 파일 중 다시 만들 수 있는 캐시 — «이름=증거» 쌍 (환경 변수로 바꿈). 그 밖의 무시 파일(.env·로컬 설정 등)은 보존 사유.
# R375 4차 검토: 이름만 맞으면 지우던 것을 «다시 만들 수 있다는 증거» 까지 요구 — 증거는 그 폴더 기준 상대 경로 glob
#   (../*.py = 옆에 원본 소스 · ../package.json = 패키지 정의 · CACHEDIR.TAG = 도구가 남기는 캐시 표식). 증거 없으면 보존.
REGENERABLE = tuple(tuple(x.split("=", 1)) for x in os.environ.get(
    "OWN_CLEANUP_REGENERABLE",
    "__pycache__=../*.py,node_modules=../package.json,.pytest_cache=CACHEDIR.TAG,.mypy_cache=CACHEDIR.TAG,"
    ".ruff_cache=CACHEDIR.TAG").split(",") if "=" in x)


def _git_repos(p: Path, deadline: float | None = None):
    """폴더 안 git 저장소 전부 (깊이 제한 X · 저장소 안의 중첩 저장소도 · 링크는 따라가지 않음).
    (경로, None) 또는 탐색이 불완전하면 (경로, 사유) — 사유가 있으면 부르는 쪽이 보존한다 (R375 3차 검토)."""
    t0 = time.monotonic()
    stack = [str(p)]
    while stack:
        if time.monotonic() - t0 > SCAN_SEC:
            yield p, f"탐색 미완료 ({SCAN_SEC:g}초 초과)"
            return
        if deadline is not None and time.monotonic() > deadline:
            yield p, "시간 예산 소진 (저장소 탐색 미완료 · 다음 실행)"
            return
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                ents = list(it)
        except OSError as e:
            yield d, f"폴더 읽기 실패 ({type(e).__name__})"
            continue
        if any(e.name == ".git" for e in ents):
            yield d, None
        for e in ents:
            if e.name == ".git":
                continue
            try:
                if e.is_dir(follow_symlinks=False) and not _is_link(e.path):
                    stack.append(e.path)
            except OSError as ex:
                yield e.path, f"폴더 판정 실패 ({type(ex).__name__})"


def _regenerable(rel: str, repo: str = "") -> bool:
    """무시된 경로 rel 이 «이름 + 다시 만들 수 있다는 증거» 를 둘 다 갖춘 캐시 안에 있나."""
    import fnmatch
    import glob
    parts = rel.rstrip("/").split("/")
    for i, x in enumerate(parts):
        for pat, ev in REGENERABLE:
            if not fnmatch.fnmatch(x, pat):
                continue
            base = os.path.join(repo, *parts[:i + 1])
            if glob.glob(os.path.join(glob.escape(base), *ev.split("/"))):
                return True
    return False


def _git(repo: str, *args, inp: str | None = None, timeout: float = 5):
    import subprocess
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never", GIT_ASKPASS="", SSH_ASKPASS="")
    # --no-optional-locks: status 가 .git/index 를 고쳐 쓰면 삭제 직전 재확인이 «최근 변경» 으로 오판 (CI 실측)
    return subprocess.run(["git", "--no-optional-locks", "-C", repo, *args], input=inp, capture_output=True, text=True,
                          timeout=timeout, encoding="utf-8", errors="replace", env=env)


_REMOTE_TIPS: dict = {}   # 한 번의 run 안에서만 쓰는 원격 끝 커밋 (원격 주소 → sha 집합) — 같은 원격 복제본 여럿의 중복 조회 통합


class _OutOfTime(Exception):
    pass


def _left(deadline: float | None, want: float) -> float:
    if deadline is None:
        return want
    rem = deadline - time.monotonic()
    if rem <= 0.2:
        raise _OutOfTime()
    return min(want, rem)


def _repo_reason(repo: str, deadline: float | None = None) -> str | None:
    """저장소 하나 — 지우면 잃는 것이 있으면 사유 (확인 실패·시간 예산 소진도 사유 = 보존).
    R375 4차 검토: 모든 git 호출이 run 전체 예산(deadline)을 공유 · remote/cat-file 종료 코드도 확인 (실패 = 보존)."""
    import subprocess
    try:
        return _repo_reason_inner(repo, deadline)
    except _OutOfTime:
        return f"시간 예산 소진 (git 확인 미완료 · 다음 실행) {repo}"
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"git 확인 실패 ({type(e).__name__}) {repo}"


def _repo_reason_inner(repo: str, deadline: float | None) -> str | None:
    if True:
        r = _git(repo, "status", "--porcelain", "--untracked-files=all", "--ignored=matching", "--ignore-submodules=none",
                 timeout=_left(deadline, 5))
        if r.returncode != 0:
            return f"git 확인 실패 (종료 {r.returncode}) {repo}"
        lines = [x for x in r.stdout.splitlines() if x.strip()]
        if any(not x.startswith("!! ") for x in lines):
            return f"커밋 안 한 변경 {repo}"
        keep = [x[3:] for x in lines if not _regenerable(x[3:].strip('"'), repo)]
        if keep:
            return f"무시된 파일 (다시 못 만들 수 있음 {keep[:3]}) {repo}"
        r = _git(repo, "stash", "list", timeout=_left(deadline, 5))
        if r.returncode != 0:
            return f"git 확인 실패 (종료 {r.returncode}) {repo}"
        if r.stdout.strip():
            return f"stash 있음 {repo}"
        # 원격 추적 ref 는 오래됐을 수 있다 → 원격에 실제로 물어본 끝 커밋만 «올라간 증거» 로 친다 (detached HEAD·태그 포함)
        pos = ["--all"]   # HEAD(detached 포함)·브랜치·태그·원격 추적 ref 전부 — 원격이 실제로 가진 커밋만 빼고 남으면 보존
        rv = _git(repo, "remote", "-v", timeout=_left(deadline, 5))
        if rv.returncode != 0:
            return f"git 확인 실패 (remote 종료 {rv.returncode}) {repo}"
        urls = {}
        for ln in rv.stdout.splitlines():
            f = ln.split()
            if len(f) >= 2:
                urls[f[0]] = f[1]          # 이름 → 주소
        shas = set()
        for rm, url in sorted(urls.items()):
            # 네트워크 원격(scheme:// · user@host:)만 주소로 공유 · 로컬 경로 원격은 상대 경로일 수 있어 저장소별로 따로
            net = bool(re.match(r"^[a-z][a-z0-9+.-]*://|^[^/\\:]+@", url, re.I))
            key = (url, "" if net else os.path.normcase(repo))
            if key not in _REMOTE_TIPS:
                lr = _git(repo, "ls-remote", rm, timeout=_left(deadline, 15))
                if lr.returncode != 0:
                    return f"원격 확인 실패 ({rm} 종료 {lr.returncode}) {repo}"
                _REMOTE_TIPS[key] = {x.split()[0] for x in lr.stdout.splitlines() if x.strip()}
            shas |= _REMOTE_TIPS[key]
        have = []
        if shas:
            ck = _git(repo, "cat-file", "--batch-check", inp="\n".join(sorted(shas)) + "\n", timeout=_left(deadline, 5))
            if ck.returncode != 0:
                return f"git 확인 실패 (cat-file 종료 {ck.returncode}) {repo}"
            have = [x.split()[0] for x in ck.stdout.splitlines() if x.strip() and not x.endswith("missing")]
        rl = _git(repo, "rev-list", "-1", *pos, "--stdin", inp="".join(f"^{h}\n" for h in have),
                  timeout=_left(deadline, 5))
        if rl.returncode != 0:
            return f"git 확인 실패 (종료 {rl.returncode}) {repo}"
        if rl.stdout.strip():
            return f"원격에 없는 커밋 {rl.stdout.strip()[:8]} {repo}"
    return None


def _unpushed(p: Path, deadline: float | None = None) -> str | None:
    """안에 든 git 저장소에 잃을 것이 있거나 탐색·확인이 불완전하면 사유 (= 보존)."""
    for repo, err in _git_repos(p, deadline):
        if err:
            return f"{err} {repo}"
        why = _repo_reason(repo, deadline)
        if why:
            return why
    return None


def busy_reason(p: Path, sid: str, now: float, deadline: float | None = None) -> str | None:
    """끝난 세션 폴더를 지우면 안 되는 사유 (없으면 None). 지우기 직전에도 다시 부른다.
    deadline: run 전체 시간 예산 (time.monotonic 기준) — 모든 확인이 공유 · 못 끝낸 확인 = 보존하고 다음 실행에서 다시."""
    act = _session_last_active(sid)
    if act is not None and now - act < IDLE_SCRATCH_SEC:
        return f"세션 활동 중 (대화 기록 {IDLE_SCRATCH_SEC // 60}분 안에 갱신)"
    errs: list = []
    last = _newest_mtime(p, errs, deadline)
    if errs:
        return f"변경 확인 불완전 ({errs[0]})"
    if act is None and now - last < IDLE_SCRATCH_SEC:
        return f"사용 중 ({IDLE_SCRATCH_SEC // 60}분 안에 수정)"
    if now - last < RECENT_WRITE_SEC:
        return f"최근 파일 변경 ({RECENT_WRITE_SEC // 60}분 안)"
    return _open_ledger(sid) or _users_of(p, sid) or _unpushed(p, deadline)


def _identity(p: Path) -> dict:
    st = os.stat(p)
    return {"ino": int(st.st_ino), "birth": round(getattr(st, "st_birthtime", None) or st.st_ctime, 3)}


def resume_reason(p: Path, sid: str, rec, deadline: float | None = None) -> str | None:
    """지우기 시작했던 폴더를 이어서 지워도 되나 (R375 4차 검토 P0). 일반 판정의 git 확인은 반쯤 지운 .git 때문에
    영원히 실패하므로 대신: 같은 폴더(식별자)인지 · 삭제 시작 뒤 새·바뀐 파일이 없는지 · 그 뒤 세션 활동·열린 요청이 없는지 ·
    쓰는 프로세스가 없는지. 하나라도 아니거나 확인 불가면 보존. 기록이 무효(형식 불명·같은 경로 재생성)면 «일반 판정»."""
    if not isinstance(rec, dict) or "t" not in rec or "ino" not in rec:
        return "재개 기록 형식 불명 (일반 판정)"
    try:
        if _identity(p) != {"ino": rec["ino"], "birth": rec.get("birth")}:
            return "재개 대상이 다른 폴더 (같은 경로 재생성 · 일반 판정)"
    except OSError as e:
        return f"재개 대상 확인 실패 ({type(e).__name__})"
    started = float(rec["t"])
    act = _session_last_active(sid)
    if act is not None and act > started:
        return "재개 보류: 삭제 시작 뒤 세션 활동"
    errs: list = []
    newest = _newest_mtime(p, errs, deadline, files_only=True)
    if errs:
        return f"재개 보류: 변경 확인 불완전 ({errs[0]})"
    if newest > started:
        return "재개 보류: 삭제 시작 뒤 새·바뀐 파일"
    return _open_ledger(sid) or _users_of(p, sid)


def _remove(p: Path, deadline: float | None = None) -> int:
    """링크를 따라가지 않고 지운다 · 읽기 전용 파일도 (git 객체). 지운 항목 수.
    deadline(time.monotonic 기준) 을 넘으면 거기서 멈춘다 — 큰 폴더는 다음 작업 종료 때 이어서 (Stop 훅 제한 안에서)."""
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
        if deadline is not None and time.monotonic() > deadline:
            break
        # R391: Windows 260자 넘는 경로는 일반 경로로 지울 수 없다(WinError 3 · 실측 10개 남음) → 확장 경로(\\?\) 로
        if os.name == "nt" and len(q) >= 248 and not q.startswith("\\\\?\\"):
            q = "\\\\?\\" + os.path.abspath(q)
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


def _load_prog() -> dict:
    try:
        d = json.loads(PROG.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_prog(d: dict) -> bool:
    """원자적 저장 (임시 파일 → 교체) · 실패하면 False — 부르는 쪽은 기록 없이 지우지 않는다 (R375 4차 검토)."""
    tmp = PROG.with_name(f"{PROG.name}.{os.getpid()}.tmp")
    try:
        PROG.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, PROG)
        return True
    except OSError:
        try:
            tmp.unlink()
        except OSError:
            pass
        return False


def _lock_path() -> Path:
    return PROG.with_name("own-cleanup.lock")


def _acquire_lock() -> bool:
    """정리 실행은 하나만 (동시 Stop·SessionEnd · 여러 창). 잠금 주인 pid 가 살아 있으면 False (이번엔 지우지 않음 = 보존).
    주인이 죽은 잠금은 넘겨받는다. 확인 불가(psutil 없음·잠금 읽기 실패)면 살아 있다고 본다."""
    lp = _lock_path()
    for _ in range(2):
        try:
            lp.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(str(lp), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w") as f:
                f.write(str(os.getpid()))
            return True
        except FileExistsError:
            try:
                pid = int(lp.read_text(encoding="utf-8").strip() or "0")
            except (OSError, ValueError):
                return False
            try:
                import psutil
                alive = pid > 0 and psutil.pid_exists(pid)
            except ImportError:
                alive = True
            if alive:
                return False
            try:
                lp.unlink()
            except OSError:
                return False
        except OSError:
            return False
    return False


def _release_lock() -> None:
    lp = _lock_path()
    try:
        if lp.read_text(encoding="utf-8").strip() == str(os.getpid()):
            lp.unlink()
    except OSError:
        pass


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
    global _PROCS
    _REMOTE_TIPS.clear()
    locked = dry or _acquire_lock()
    try:
        return _run_body(session, dry, now, locked)
    finally:
        _PROCS = None
        _REMOTE_TIPS.clear()
        if locked and not dry:
            _release_lock()


def _run_body(session: str, dry: bool, now: float, locked: bool) -> dict:
    global _PROCS
    t0 = time.monotonic()
    deadline = t0 + BUDGET_SEC   # 탐색·프로세스·git·삭제가 모두 이 하나를 공유 (R375 4차 검토)
    removed, kept, deferred = [], [], 0
    prog = _load_prog() if locked else {}
    if locked and not dry and any(not os.path.lexists(k) for k in prog):   # 다 지워진 것 정리
        prog = {k: v for k, v in prog.items() if os.path.lexists(k)}
        _save_prog(prog)
    for p, kind, idle in candidates(session, now):
        if not os.path.lexists(str(p)):
            continue
        if not locked:   # 다른 정리 실행이 도는 중 — 이번엔 아무것도 지우지 않는다
            kept.append({"path": str(p), "kind": kind, "why": "다른 정리 실행 중 (잠금)"})
            continue
        if time.monotonic() > deadline:   # Stop 훅 제한(10초) 안에서 끝내고 나머지는 다음 작업 종료 때 (첫 실행 96개 10.4초 실측)
            deferred += 1
            continue
        why = safe_target(p)
        sid = p.parent.name
        resume = False
        if not why and kind == "ended-scratchpad" and str(p) in prog:
            # 이미 확인을 마치고 지우기 시작한 폴더 — 반쯤 지운 .git 은 git 확인이 실패해 영원히 남는다 →
            #   같은 폴더·삭제 시작 뒤 변경 없음·세션 활동 없음·열린 요청 없음·쓰는 프로세스 없음이면 이어서 지운다
            r = resume_reason(p, sid, prog[str(p)], deadline)
            if r and "일반 판정" in r:
                prog.pop(str(p), None)
                if not dry:
                    _save_prog(prog)
            else:
                resume, why = True, r
        if not why and not resume:
            try:   # 1차 판정용 프로세스 목록은 실행당 1회 공유 (종류 무관 · CI 러너 첫 읽기 수 초 · 삭제 직전 재확인은 새로)
                _PROCS = _PROCS or _proc_snapshot()
            except Exception:  # noqa: BLE001 — 실패하면 _users_of 가 직접 읽다가 «확인 불가» 로 보존
                _PROCS = None
            if kind == "ended-scratchpad":
                why = busy_reason(p, sid, now, deadline)
            else:
                # R375 4차 검토: kit 임시·등록 산출물도 같은 보호 계약 — 시각 확인 실패 = 보존 · 쓰는 프로세스 = 보존
                errs: list = []
                last = _newest_mtime(p, errs, deadline)
                if errs:
                    why = f"변경 확인 불완전 ({errs[0]})"
                elif now - last < idle:
                    why = f"사용 중 ({idle // 60}분 안에 수정)"
                else:
                    why = _users_of(p, "")
        if not why and not dry:
            _PROCS = None                                        # 재확인은 지금 프로세스 목록으로
            if resume:
                why = resume_reason(p, sid, prog[str(p)], deadline)
            elif kind == "ended-scratchpad":
                why = busy_reason(p, sid, time.time(), deadline)   # 지우기 직전 재확인 (판정과 삭제 사이 경합)
            else:
                why = _users_of(p, "")
            why = f"삭제 직전 재확인: {why}" if why else None
        if why:
            kept.append({"path": str(p), "kind": kind, "why": why})
            continue
        if not dry and kind == "ended-scratchpad" and not resume:
            try:
                prog[str(p)] = {"t": time.time(), **_identity(p)}
            except OSError as e:
                kept.append({"path": str(p), "kind": kind, "why": f"재개 기록 준비 실패 ({type(e).__name__})"})
                continue
            if not _save_prog(prog):   # 기록 없이 지우기 시작하면 반쯤 지운 폴더가 영원히 «git 확인 실패» 로 남는다
                prog.pop(str(p), None)
                kept.append({"path": str(p), "kind": kind, "why": "재개 기록 저장 실패 (지우지 않음)"})
                continue
        n = 0 if dry else _remove(p, deadline=deadline)
        left = bool(not dry and os.path.lexists(str(p)))
        if not dry and not left and prog.pop(str(p), None) is not None:
            _save_prog(prog)
        removed.append({"path": str(p), "kind": kind, "items": n, "partial": left})   # 남은 것은 다음 작업 종료 때 이어서
    _PROCS = None
    if not dry and locked:   # 등록 목록에서 사라진 것 정리
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
