"""요청 함 + 독립 Broker 실행기 (2026-11-10 · §63 S5 · §64 · 독립 검토 반영).

구조
  Agent(개발 계정) ── submit ──▶ 요청 함(inbox: Agent 는 쓰기만) ──▶ Broker(별도 계정) ── 승인된 push ──▶ 원격
  - Agent 쪽 = 클라이언트 (submit·client-status). 표준 라이브러리만 쓴다 → RPA·OCR 등 복사 설치 솔루션에 그대로 전파.
    Broker 가 없거나 git 이 없으면 위험 작업은 BLOCKED 로 돌려주고 끝 (일반 개발은 영향 없음).
  - Broker 쪽 = 실행기 (process·describe·approve·status). 승인 저장·불변·만료·1회 소비는 approval-gate.py 를 그대로 쓴다
    (ORCHESTRATION_ROOT = Broker 폴더 → 그 폴더의 .claude/state/orca.db · 코드 변경 0).

Broker 가 믿지 않는 것 (Agent 가 조작할 수 있음)
  - 요청 파일: 일반 파일·크기 상한·허용 키·형식만 · 원격 주소는 요청이 아니라 Broker 설정에서 · 번호 재사용 거부
  - 묶음: 일반 파일(디렉터리·junction·링크 거부)·머리말·크기 확인 뒤 Broker 쪽 사본에서만 가져온다 · 객체 fsck
  - Agent 저장소: Broker 는 Agent 저장소 안에서 git 을 실행하지 않는다 (훅·fsmonitor·sshCommand 가 Broker 계정으로 실행될 수 있음)
  - 결과 파일(outbox): 안내용 고정 코드만 · 판정 정본은 Broker DB · Agent 가 만든 결과·승인 표시는 무시
  - Agent 세션의 /approve 승인 ('user-prompt'): Broker 는 자기 승인 채널(broker-console) 승인만 쓴다
배치 전제 (코드로 강제 안 됨 · 설치 승인 S2·S3): 이 파일과 approval-gate.py·lib 는 Agent 가 쓸 수 없는 Broker 폴더의
  사본으로 실행한다 (`python -I`). Agent 가 수정 가능한 kit·솔루션 사본으로 Broker 를 돌리면 이 보호는 성립하지 않는다.

usage (Agent):  broker.py submit <repo_dir> <repo_id> <branch> [--inbox <dir>]
                broker.py client-status <request_id> [--inbox <dir>]
      (Broker): broker.py process <broker_root> | describe <broker_root> <task_id>
                | approve <broker_root> <task_id> <커밋 앞 8자리> | status <broker_root> <task_id>
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REQ_KEYS = {"v", "type", "repo_id", "branch", "sha", "submitted_at"}
_RX_BRANCH = re.compile(r"(?!.*\.\.)(?!/)(?!-)(?!.*//)(?!.*@\{)(?!.*\.lock(?:/|$))[A-Za-z0-9._/-]{1,100}(?<![./])")
_RX_SHA = re.compile(r"[0-9a-f]{40}")
_RX_ID = re.compile(r"req-[0-9a-f]{16}")
_RX_REPO = re.compile(r"[A-Za-z0-9._-]{1,64}")
BROKER_APPROVER = "broker-console"     # Broker 승인 채널 표시 — Agent 세션의 'user-prompt' 승인은 쓰지 않는다
MAX_REQ_BYTES = 4096
MAX_BUNDLE_BYTES = 512 * 1024 * 1024
MAX_PER_RUN = 50
LOCK_STALE_SEC = 3600
SCRIPTS = Path(__file__).resolve().parents[1]


# ── 공통 ────────────────────────────────────────────────────────────────
def _run(args, cwd=None, env=None, timeout=120):
    try:
        return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return subprocess.CompletedProcess(args, 127, "", str(e))


def _write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".partial")   # *.json 이 아님 → 처리 대상 아님
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


# ── Agent 쪽 클라이언트 (복사 설치용 · 표준 라이브러리만) ───────────────────
def find_inbox(project_dir=None, inbox=None):
    """요청 함 위치: 인자 → 환경 변수 ORCA_BROKER_INBOX → 솔루션 루트 .claude/broker-client.json {"inbox": …}."""
    if inbox:
        return Path(inbox)
    if os.environ.get("ORCA_BROKER_INBOX"):
        return Path(os.environ["ORCA_BROKER_INBOX"])
    start = Path(project_dir or os.getcwd()).resolve()
    for d in (start, *start.parents):          # 저장소가 솔루션 하위 폴더여도 찾는다
        cfg = d / ".claude" / "broker-client.json"
        if cfg.is_file():
            try:
                return Path(json.loads(cfg.read_text(encoding="utf-8"))["inbox"])
            except (OSError, ValueError, KeyError, TypeError):
                return None
    return None


def submit_push(repo_dir, repo_id: str, branch: str, inbox=None) -> dict:
    """현재 HEAD 를 묶음으로 만들어 요청 함에 넣는다. push 하지 않는다 (Broker 승인 후 Broker 가 실행)."""
    box = find_inbox(repo_dir, inbox)
    if not box or not box.is_dir():
        return {"status": "BLOCKED", "reason": "Broker 요청 함 없음 — 원격 반영 같은 위험 작업은 차단 · 일반 개발은 계속"}
    if not shutil.which("git"):
        return {"status": "BLOCKED", "reason": "git 없음 — 원격 반영 요청 불가 · 일반 개발은 계속"}
    if not _RX_BRANCH.fullmatch(branch or "") or not _RX_REPO.fullmatch(repo_id or ""):
        return {"status": "REJECTED", "reason": "저장소 id·브랜치 형식 오류"}
    head = _run(["git", "-C", str(repo_dir), "rev-parse", "HEAD"])
    sha = head.stdout.strip()
    if head.returncode != 0 or not _RX_SHA.fullmatch(sha):
        return {"status": "BLOCKED", "reason": "git 저장소가 아니거나 HEAD 없음"}
    rid = "req-" + hashlib.sha256(f"{repo_id}\n{branch}\n{sha}\n{time.time_ns()}\n{os.urandom(8).hex()}"
                                  .encode()).hexdigest()[:16]
    bundle = box / f"{rid}.bundle"
    b = _run(["git", "-C", str(repo_dir), "bundle", "create", str(bundle), "HEAD"], timeout=300)
    if b.returncode != 0:
        return {"status": "BLOCKED", "reason": "묶음 생성 실패: " + (b.stderr or "").strip()[-200:]}
    _write_json_atomic(box / f"{rid}.json", {"v": 1, "type": "push", "repo_id": repo_id, "branch": branch,
                                             "sha": sha, "submitted_at": int(time.time())})
    return {"status": "SUBMITTED", "request_id": rid, "sha": sha}


def client_status(request_id: str, inbox=None, project_dir=None) -> dict:
    """안내용 결과 (Broker 가 outbox 에 쓴 고정 코드). 판정 정본은 Broker DB — 이 값으로 성공을 단정하지 않는다."""
    box = find_inbox(project_dir, inbox)
    if not box:
        return {"status": "BLOCKED", "reason": "Broker 요청 함 없음"}
    if not _RX_ID.fullmatch(request_id or ""):
        return {"status": "REJECTED", "reason": "요청 번호 형식 오류"}
    try:
        d = json.loads((box.parent / "outbox" / f"{request_id}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError):
        return {"status": "UNKNOWN", "reason": "결과 없음 (처리 전이거나 Broker 미실행)"}
    d["note"] = "안내용 — 판정 정본은 Broker DB"
    return d


# ── Broker 쪽 실행기 ──────────────────────────────────────────────────────
_TASKS_DDL = ("CREATE TABLE IF NOT EXISTS tasks (task_id TEXT PRIMARY KEY, task_file TEXT NOT NULL, ai_assigned TEXT, "
              "worker_id TEXT, status TEXT NOT NULL, locked_at INTEGER, locked_until INTEGER, created_at INTEGER NOT NULL, "
              "completed_at INTEGER, retry_count INTEGER DEFAULT 0, approval_state TEXT, risk_category TEXT, "
              "risk_detail TEXT, approved_at INTEGER, approved_by TEXT)")


class _Reject(Exception):
    def __init__(self, code: str, msg: str):
        super().__init__(msg)
        self.code = code


def _gate(broker_root: Path):
    """approval-gate.py 를 Broker 폴더 DB 로 (ORCHESTRATION_ROOT · Broker 프로세스 전용) · 승인자 표시는 Broker 채널."""
    import sqlite3
    os.environ["ORCHESTRATION_ROOT"] = str(broker_root)
    db = broker_root / ".claude" / "state" / "orca.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db)) as c:
        c.execute(_TASKS_DDL)
    spec = importlib.util.spec_from_file_location("approval_gate_broker", SCRIPTS / "approval-gate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.USER_APPROVER = BROKER_APPROVER          # consume_approval 은 이 표시의 승인만 1회 사용
    if Path(mod.get_db_path()).resolve() != db.resolve():
        raise RuntimeError("Broker DB 경로 확인 실패 — 처리 중단")
    return mod


def _config(broker_root: Path) -> dict:
    return json.loads((broker_root / "broker-config.json").read_text(encoding="utf-8"))


class _Git:
    """Broker 쪽 git — 절대 경로 실행 파일 · 작업 폴더 = Broker 폴더 · 최소 환경 · 훅·fsmonitor 끔 · Broker 미러에만."""

    def __init__(self, broker_root: Path):
        exe = shutil.which("git")
        if not exe:
            raise RuntimeError("git 없음 — Broker 실행 불가")
        self.exe = str(Path(exe).resolve())
        self.root = broker_root
        self.empty = broker_root / "empty-hooks"
        self.empty.mkdir(parents=True, exist_ok=True)
        keep = ("SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "USERPROFILE", "HOME", "APPDATA", "LOCALAPPDATA",
                "PROGRAMDATA", "PROGRAMFILES", "USERNAME", "PATH")
        self.env = {k: v for k, v in os.environ.items() if k.upper() in keep}
        self.env.update({"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never", "GIT_ASKPASS": "", "SSH_ASKPASS": ""})

    def __call__(self, mirror: Path, *args, timeout=300):
        return _run([self.exe, "-c", f"core.hooksPath={self.empty}", "-c", "core.fsmonitor=false",
                     "-c", "core.sshCommand=ssh", "-c", "protocol.ext.allow=never",
                     "--git-dir", str(mirror), *args], cwd=str(self.root), env=self.env, timeout=timeout)


def _regular_file(p: Path, limit: int) -> os.stat_result:
    """링크·junction·디렉터리·과대 파일 거부."""
    st = os.lstat(p)
    if not stat.S_ISREG(st.st_mode) or os.path.islink(p) or getattr(os.path, "isjunction", lambda _: False)(p):
        raise _Reject("not_regular_file", "일반 파일이 아님 (디렉터리·링크·junction)")
    if getattr(st, "st_file_attributes", 0) & 0x400:          # FILE_ATTRIBUTE_REPARSE_POINT
        raise _Reject("not_regular_file", "재분석 지점 파일")
    if st.st_size > limit:
        raise _Reject("too_large", "크기 상한 초과")
    return st


def _outbox(cfg: dict, rid: str, data: dict) -> None:
    """Agent 가 읽는 안내 — 고정 코드만 (git 오류 문구·URL 은 넣지 않는다)."""
    if not _RX_ID.fullmatch(rid):
        return
    try:
        _write_json_atomic(Path(cfg["inbox"]).parent / "outbox" / f"{rid}.json",
                           {"request_id": rid, **data, "written_by": "broker"})
    except OSError:
        pass


def _keep(broker_root: Path, sub: str, name: str, data: bytes) -> None:
    d = broker_root / sub
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_bytes(data)


def _drop_inbox(*paths: Path) -> None:
    for p in paths:
        try:
            os.remove(p)
        except OSError:
            pass                       # 지우지 못해도 처리 기록이 있어 같은 번호는 다시 받지 않는다


def _artifacts(repo_id: str, branch: str, sha: str, remote_url: str) -> dict:
    return {"repo": repo_id, "git:branch": branch, "git:HEAD": sha,
            "git:remote": hashlib.sha256(remote_url.encode("utf-8")).hexdigest()[:16]}


def _remote_tip(git: _Git, mirror: Path, remote_url: str, branch: str):
    """(연결 성공 여부, 원격 브랜치 커밋 또는 None) — 정확한 ref 이름으로 비교."""
    ls = git(mirror, "ls-remote", remote_url, f"refs/heads/{branch}")
    if ls.returncode != 0:
        return False, None
    for line in ls.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == f"refs/heads/{branch}":
            return True, parts[0]
    return True, None


def _intake(broker_root: Path, cfg: dict, gate, git: _Git, src: Path, log: list) -> None:
    rid = src.stem
    bundle = src.with_suffix(".bundle")
    raw = b""
    try:
        if not _RX_ID.fullmatch(rid):
            raise _Reject("bad_id", "요청 번호 형식 아님")
        if any((broker_root / s / f"{rid}.json").exists() for s in ("processed", "rejected")):
            raise _Reject("reused_id", "이미 처리한 요청 번호 재사용")
        _regular_file(src, MAX_REQ_BYTES)
        raw = src.read_bytes()[:MAX_REQ_BYTES + 1]
        try:
            req = json.loads(raw.decode("utf-8"))
        except (ValueError, RecursionError, UnicodeDecodeError):
            raise _Reject("bad_json", "요청 파일을 읽을 수 없음")
        if (not isinstance(req, dict) or set(req) != REQ_KEYS or type(req.get("v")) is not int or req["v"] != 1
                or req.get("type") != "push"):
            raise _Reject("bad_fields", "허용되지 않은 요청 형식·필드 (원격 주소·승인·결과 표시는 받지 않음)")
        repo_id, branch, sha = req["repo_id"], req["branch"], req["sha"]
        repo = (cfg.get("repos") or {}).get(repo_id) if isinstance(repo_id, str) else None
        if (not repo or not isinstance(branch, str) or branch not in (repo.get("branches") or [])
                or not _RX_BRANCH.fullmatch(branch) or not isinstance(sha, str) or not _RX_SHA.fullmatch(sha)):
            raise _Reject("not_allowed", "등록되지 않은 저장소·브랜치이거나 커밋 형식 오류")
        _regular_file(bundle, MAX_BUNDLE_BYTES)
        work = broker_root / "work"
        work.mkdir(parents=True, exist_ok=True)
        copy = work / f"{rid}.bundle"
        with open(bundle, "rb") as fi, open(copy, "xb") as fo:      # Broker 사본 (읽는 도중 교체 무관)
            head = fi.read(64)
            if not (head.startswith(b"# v2 git bundle\n") or head.startswith(b"# v3 git bundle\n")):
                raise _Reject("bad_bundle", "git 묶음 파일이 아님")
            fo.write(head)
            shutil.copyfileobj(fi, fo, 1024 * 1024)
        if copy.stat().st_size > MAX_BUNDLE_BYTES:
            raise _Reject("too_large", "묶음 크기 상한 초과")
        mirror = broker_root / "mirror" / f"{repo_id}.git"
        if not mirror.exists():
            _run([git.exe, "init", "-q", "--bare", str(mirror)], cwd=str(broker_root), env=git.env)
        ref = f"refs/incoming/{rid}"
        if git(mirror, "rev-parse", "--verify", "-q", ref).returncode == 0:
            raise _Reject("reused_id", "이미 받은 요청 번호")
        f = git(mirror, "-c", "fetch.fsckObjects=true", "-c", "transfer.fsckObjects=true", "fetch", "-q",
                "--no-tags", "--no-recurse-submodules", str(copy), f"HEAD:{ref}")
        got = git(mirror, "rev-parse", "--verify", "-q", ref + "^{commit}").stdout.strip()
        try:
            copy.unlink()
        except OSError:
            pass
        if f.returncode != 0 or got != sha:
            if got:
                git(mirror, "update-ref", "-d", ref)
            raise _Reject("bundle_mismatch", "묶음의 커밋이 요청과 다름 (또는 묶음 손상·객체 검사 실패)")
    except _Reject as r:
        _keep(broker_root, "rejected", f"{rid}.json", raw or b"{}")
        _drop_inbox(src, bundle)
        log.append({"request_id": rid, "result": "rejected", "code": r.code, "reason": str(r)})
        _outbox(cfg, rid, {"state": "rejected", "code": r.code})
        return
    arts = _artifacts(repo_id, branch, sha, repo["remote_url"])
    base = f"broker-push\n{repo_id}\n{branch}"
    scope = gate.scope_key(base, arts)
    _keep(broker_root, "processed", f"{rid}.json", raw)
    _drop_inbox(src, bundle)
    same = gate.find_request("scope", scope, ("waiting", "approved"))
    tid = same or gate.new_request(
        f"broker push {repo_id} {sha[:12]} -> {branch}", "irreversible",
        json.dumps({"request_id": rid, "repo_id": repo_id, "branch": branch, "sha": sha}, ensure_ascii=False),
        arts, base, scope)
    log.append({"request_id": rid, "task_id": tid, "result": "duplicate" if same else "waiting"})
    _outbox(cfg, rid, {"task_id": tid, "state": "waiting"})


def _lock(broker_root: Path):
    p = broker_root / "process.lock"
    try:
        if p.exists() and time.time() - p.stat().st_mtime > LOCK_STALE_SEC:
            p.unlink()
        fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return p
    except OSError:
        return None


def process(broker_root) -> list:
    """요청 함을 한 번 처리하고, Broker 채널로 승인된 요청을 실행한다. 반환 = 처리 기록."""
    broker_root = Path(broker_root)
    lock = _lock(broker_root)
    if not lock:
        return [{"result": "locked", "reason": "다른 Broker 처리가 실행 중"}]
    try:
        cfg = _config(broker_root)
        gate = _gate(broker_root)
        git = _Git(broker_root)
        log: list = []
        for src in sorted(Path(cfg["inbox"]).glob("*.json"))[:MAX_PER_RUN]:
            try:
                _intake(broker_root, cfg, gate, git, src, log)
            except Exception as e:  # noqa: BLE001 — 한 건이 실패해도 나머지·승인 실행은 계속
                log.append({"request_id": src.stem, "result": "error", "reason": type(e).__name__})
        try:
            log.extend(_execute_approved(broker_root, cfg, gate, git))
        except Exception as e:  # noqa: BLE001
            log.append({"result": "error", "reason": "execute:" + type(e).__name__})
        return log
    finally:
        try:
            lock.unlink()
        except OSError:
            pass


def _expire(gate, tid: str, reason: str) -> None:
    import sqlite3
    with sqlite3.connect(str(gate.get_db_path())) as c:
        row = c.execute("SELECT risk_detail FROM tasks WHERE task_id=? AND approval_state='approved'", (tid,)).fetchone()
        if row:
            c.execute("UPDATE tasks SET approval_state='expired', status='cancelled', risk_detail=? "
                      "WHERE task_id=? AND approval_state='approved'",
                      (gate._merge_detail(row[0], expire_reason=reason, checked_at=int(time.time())), tid))


def _approved_rows(gate) -> list:
    import sqlite3
    with sqlite3.connect(str(gate.get_db_path())) as c:
        rows = c.execute("SELECT task_id, risk_detail, approved_at, approved_by FROM tasks WHERE task_file = "
                         "'<approval-gate>' AND approval_state = 'approved'").fetchall()
    out = []
    for tid, raw, at, by in rows:
        try:
            risk = json.loads(raw or "{}")
            d = json.loads(risk.get("detail") or "{}")
            if str(risk.get("base", "")).startswith("broker-push\n"):
                out.append((tid, d["request_id"], d["repo_id"], d["branch"], d["sha"], int(at or 0), by,
                            risk.get("artifacts") or {}))
        except (ValueError, KeyError, TypeError, AttributeError, RecursionError):
            continue
    return out


def _execute_approved(broker_root: Path, cfg: dict, gate, git: _Git) -> list:
    """Broker 채널로 승인된 요청만 1회 실행 — 커밋은 Broker 미러에 보관한 것 · 원격·브랜치는 지금의 Broker 설정."""
    out = []
    now = int(time.time())
    for tid, rid, repo_id, branch, sha, at, by, approved_arts in _approved_rows(gate):
        if by != BROKER_APPROVER:
            out.append({"request_id": rid, "task_id": tid, "result": "not_executed", "reason": "broker 승인 아님"})
            continue
        if now - at > gate.APPROVAL_TTL_SEC:
            _expire(gate, tid, "approval_ttl")            # 중복 판정에 영구히 남지 않게 (새 요청 가능)
            out.append({"request_id": rid, "task_id": tid, "result": "not_executed", "reason": "approval_ttl"})
            continue
        repo = (cfg.get("repos") or {}).get(repo_id)
        if not repo or branch not in (repo.get("branches") or []) or not _RX_SHA.fullmatch(sha):
            _expire(gate, tid, "not_allowed_now")         # 승인 뒤 허용 목록에서 빠진 저장소·브랜치
            out.append({"request_id": rid, "task_id": tid, "result": "not_executed", "reason": "not_allowed_now"})
            continue
        mirror = broker_root / "mirror" / f"{repo_id}.git"
        kept = git(mirror, "rev-parse", "--verify", "-q", f"refs/incoming/{rid}^{{commit}}").stdout.strip()
        arts = _artifacts(repo_id, branch, sha, repo["remote_url"])
        if kept != sha:
            arts = {**arts, "git:HEAD": kept or "<missing>"}   # 미러의 커밋이 다르면 승인과 불일치 → 만료
        ok, tip = _remote_tip(git, mirror, repo["remote_url"], branch)
        if not ok and arts == approved_arts:                # 승인과 같은 대상인데 연결만 안 될 때
            out.append({"request_id": rid, "task_id": tid, "result": "not_executed", "reason": "remote_unreachable"})
            _outbox(cfg, rid, {"task_id": tid, "state": "waiting_remote", "code": "remote_unreachable"})
            continue                                        # 승인은 소비하지 않는다 (유효 시간 안 재시도 가능)
        state = gate.consume_approval(tid, artifacts=arts)
        if state != "consumed":
            out.append({"request_id": rid, "task_id": tid, "result": "not_executed", "reason": state})
            continue
        res = _push(git, mirror, repo["remote_url"], sha, branch, tip)
        gate.record_result(tid, "finished" if res["pushed"] else "error", res)
        out.append({"request_id": rid, "task_id": tid, "result": "pushed" if res["pushed"] else "failed", **res})
        _outbox(cfg, rid, {"task_id": tid, "state": "executed", "pushed": res["pushed"], "code": res["code"]})
    return out


def _push(git: _Git, mirror: Path, remote_url: str, sha: str, branch: str, before) -> dict:
    """미러에서 원격으로 fast-forward push 만 (강제 없음). worker_git.push_approved 와 같은 조건."""
    tip_ref = f"refs/remote-tip/{branch}"
    if before:
        if git(mirror, "fetch", "-q", "--no-tags", remote_url, f"+refs/heads/{branch}:{tip_ref}").returncode != 0:
            return {"pushed": False, "code": "remote_fetch_failed", "remote_before": before}
        if git(mirror, "merge-base", "--is-ancestor", tip_ref, sha).returncode != 0:
            return {"pushed": False, "code": "not_fast_forward", "remote_before": before}
    p = git(mirror, "push", "-q", remote_url, f"{sha}:refs/heads/{branch}")
    ok_after, after = _remote_tip(git, mirror, remote_url, branch)
    ok = p.returncode == 0 and ok_after and after == sha
    return {"pushed": ok, "code": "pushed" if ok else "push_failed", "remote_before": before, "remote_after": after,
            "detail": None if ok else (p.stderr or p.stdout).strip()[-200:]}     # 상세는 Broker DB 에만


def describe(broker_root, task_id: str) -> dict:
    """승인 전 확인 — 무엇이 올라가는지 (원격에 없는 커밋 전체)."""
    broker_root = Path(broker_root)
    gate = _gate(broker_root)
    cfg = _config(broker_root)
    git = _Git(broker_root)
    st = gate.status(task_id)
    try:
        d = json.loads((st.get("risk_detail") or {}).get("detail") or "{}")
        repo = cfg["repos"][d["repo_id"]]
    except (ValueError, KeyError, TypeError, AttributeError):
        return {"error": "Broker 요청이 아님", "task_id": task_id}
    mirror = broker_root / "mirror" / f"{d['repo_id']}.git"
    ok, tip = _remote_tip(git, mirror, repo["remote_url"], d["branch"])
    rng = [d["sha"]] + ([f"^{tip}"] if tip and git(mirror, "cat-file", "-e", tip + "^{commit}").returncode == 0 else [])
    commits = git(mirror, "log", "--oneline", "-n", "50", *rng).stdout.splitlines()
    return {"task_id": task_id, "state": st.get("approval_state"), "repo_id": d["repo_id"], "branch": d["branch"],
            "sha": d["sha"], "remote_url": repo["remote_url"], "remote_reachable": ok, "remote_tip": tip,
            "commits_to_push": commits, "confirm_with": d["sha"][:8]}


def approve(broker_root, task_id: str, confirm: str = "") -> dict:
    """Broker 승인 채널 (과도기: Broker 콘솔 · 이후 §53-2 대역 외 채널로 교체). 커밋 앞 8자리 확인 필수."""
    info = describe(broker_root, task_id)
    if "error" in info:
        return info
    if not confirm or confirm != info["confirm_with"]:
        return {"error": "확인용 커밋 앞 8자리가 다름 — describe 로 내용 확인 후 다시", "describe": info}
    return _gate(Path(broker_root)).approve(task_id, by=BROKER_APPROVER)


def status(broker_root, task_id: str) -> dict:
    """판정 정본 — Broker DB 의 상태 (outbox 파일과 무관)."""
    return _gate(Path(broker_root)).status(task_id)


def _main(argv) -> int:
    for s in (sys.stdout, sys.stderr):        # 한국어 Windows 의 cp949 파이프에서도 안내가 깨지지 않게 (D22)
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    a = argv[1:]
    inbox = None
    if "--inbox" in a:
        i = a.index("--inbox")
        inbox = a[i + 1] if i + 1 < len(a) else None
        a = a[:i] + a[i + 2:]
    if len(a) == 4 and a[0] == "submit":
        r = submit_push(a[1], a[2], a[3], inbox)
    elif len(a) == 2 and a[0] == "client-status":
        r = client_status(a[1], inbox)
    elif len(a) == 2 and a[0] == "process":
        r = process(a[1])
    elif len(a) == 3 and a[0] == "describe":
        r = describe(a[1], a[2])
    elif len(a) == 4 and a[0] == "approve":
        r = approve(a[1], a[2], a[3])
    elif len(a) == 3 and a[0] == "status":
        r = status(a[1], a[2])
    else:
        print(__doc__)
        return 2
    print(json.dumps(r, ensure_ascii=False))
    if isinstance(r, dict) and (r.get("status") in ("BLOCKED", "REJECTED") or "error" in r):
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
