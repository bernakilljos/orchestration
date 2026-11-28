"""SQLite state management library for orchestration_v1 kit.

Provides atomic transaction handling, worker tracking, task locking, metrics,
and quota management via WAL-enabled SQLite.
"""

import sqlite3
import os
import json
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict, List, Any
import threading

# Thread-local lock to prevent concurrent DB access issues on Windows
_db_lock = threading.Lock()


def get_db_path() -> Path:
  """Return path to orca.db, creating .claude/state if needed."""
  project_root = _get_project_root()
  state_dir = project_root / ".claude" / "state"
  state_dir.mkdir(parents=True, exist_ok=True)
  return state_dir / "orca.db"


def _get_project_root() -> Path:
  """Get project root from env or by walking up from script location."""
  if "ORCHESTRATION_ROOT" in os.environ:
    return Path(os.environ["ORCHESTRATION_ROOT"])
  # Walk up from .claude/scripts/lib/state_db.py
  current = Path(__file__).parent
  while current != current.parent:
    if (current / ".claude" / "scripts").exists():
      return current
    current = current.parent
  # Fallback
  return Path.cwd()


def get_db() -> sqlite3.Connection:
  """Open connection to orca.db with WAL and busy timeout."""
  db_path = get_db_path()
  conn = sqlite3.connect(str(db_path), timeout=30.0)
  conn.row_factory = sqlite3.Row
  conn.execute("PRAGMA journal_mode=WAL")
  conn.execute("PRAGMA synchronous=NORMAL")
  conn.execute("PRAGMA busy_timeout=5000")
  return conn


@contextmanager
def tx():
  """Context manager for atomic transactions with IMMEDIATE locking."""
  with _db_lock:
    conn = get_db()
    try:
      conn.execute("BEGIN IMMEDIATE")
      yield conn
      conn.commit()
    except Exception as e:
      conn.rollback()
      raise
    finally:
      conn.close()


# ── 훅 응답 경로용 시간 상한 기록 (R375 Hook 응답성 · 2026-11-28) ─────────────────
# 훅(Edit 직후 등)이 orca.db 에 기록할 때 잠금을 오래 기다리면 Edit 응답이 멈춘다 (실측: 잠금 중 약 15초).
# 문장마다 busy_timeout 을 새로 주면 문장 수만큼 대기가 늘어나므로, 전체 마감(deadline)에서 남은 시간만 쓴다.
# 시간 안에 못 쓴 기록은 버리지 않고 스풀(이벤트 1건 = 파일 1개)에 남겨 다음 성공 세션에서 이어 쓴다 (감사 기록 조용한 유실 X).
HOOK_DB_BUDGET_DEFAULT = 0.5


def hook_db_budget() -> float:
  """ORCA_HOOK_DB_TIMEOUT 검증 — 숫자 아님·NaN·무한·0.05 미만·5 초과 = 기본 0.5초."""
  import math
  try:
    v = float(os.environ.get("ORCA_HOOK_DB_TIMEOUT", HOOK_DB_BUDGET_DEFAULT))
    if math.isfinite(v) and 0.05 <= v <= 5.0:
      return v
  except (TypeError, ValueError):
    pass
  return HOOK_DB_BUDGET_DEFAULT


def _is_busy(e: Exception) -> bool:
  msg = str(e).lower()
  return isinstance(e, sqlite3.OperationalError) and ("locked" in msg or "busy" in msg)


class BoundedSession:
  """전체 마감 안에서만 SQL 실행 · close 는 호출부 finally.
  SQLite 자체 대기(busy_timeout)는 끈다 — 실측: 문장 하나가 busy_timeout 의 2~2.7배를 기다렸고(준비·실행 단계 각각) ·
  interrupt 로도 대기가 끊기지 않았다 (2026-11-28) → 잠기면 즉시 실패시키고 마감 전까지 짧게 쉬며 재시도 (상한이 정확)."""
  RETRY_SLEEP = 0.02

  def __init__(self, db_path, budget: Optional[float] = None):
    self.deadline = time.monotonic() + (hook_db_budget() if budget is None else float(budget))
    self.conn = sqlite3.connect(str(db_path), timeout=0)
    self.conn.execute("PRAGMA busy_timeout = 0")

  def remaining(self) -> float:
    return self.deadline - time.monotonic()

  def _retry(self, fn):
    while True:
      if self.remaining() <= 0:
        raise TimeoutError("hook db budget exceeded")
      try:
        return fn()
      except sqlite3.OperationalError as e:
        if not _is_busy(e) or self.remaining() <= self.RETRY_SLEEP:
          raise
        time.sleep(self.RETRY_SLEEP)

  def sql(self, stmt: str, params=()):
    return self._retry(lambda: self.conn.execute(stmt, params))

  def commit(self) -> None:
    self._retry(self.conn.commit)

  def close(self) -> None:
    try:
      self.conn.close()
    except Exception:  # noqa: BLE001
      pass


def spool_path(db_path) -> Path:
  """예전 단일 JSON 줄 스풀 (읽기·이관 전용 · 새 기록은 spool_dir 에 이벤트 1건 = 파일 1개)."""
  return Path(db_path).with_name("hook-db-spool.jsonl")


def spool_dir(db_path) -> Path:
  """스풀 폴더 — 이벤트 1건 = 파일 1개 (R375 7차 검토: 단일 파일 append·replace 경쟁으로 실제 유실 재현)."""
  return Path(db_path).with_name("hook-db-spool.d")


SPOOL_MAX_EVENTS = 5000                 # 폴더 안 대기 이벤트 상한 (동시 writer 수만큼만 넘을 수 있음)
SPOOL_EVENT_MAX_BYTES = 64 * 1024       # 이벤트 1건 상한 (응답 경로 읽기량 묶음)
SPOOL_STALE_TMP_SEC = 3600              # 쓰다 만 임시 파일 = 이 시간 뒤 held/ 로 옮겨 보존


def _allowed_stmt(stmt) -> bool:
  t = " ".join(str(stmt).split()).upper()
  if ";" in t.rstrip("; "):
    return False                          # 한 문장만
  return t.startswith("INSERT INTO ") or t.startswith(("CREATE TABLE IF NOT EXISTS ", "CREATE INDEX IF NOT EXISTS "))


def _valid_event(rec) -> bool:
  """재생 전 이벤트 전체 선검증 — 하나라도 허용 밖이면 아무것도 실행하지 않음 (부분 커밋 X)."""
  if not isinstance(rec, dict) or not isinstance(rec.get("id"), str):
    return False
  for key in ("setup", "ops"):
    items = rec.get(key) or []
    if not isinstance(items, list):
      return False
    for it in items:
      if not (isinstance(it, list) and len(it) == 2 and isinstance(it[0], str) and isinstance(it[1], list)
              and _allowed_stmt(it[0])):
        return False
  return bool(rec.get("ops"))


def _count_at_least(d: Path, n: int) -> bool:
  try:
    with os.scandir(d) as it:
      c = 0
      for e in it:
        if e.name.endswith(".json"):
          c += 1
          if c >= n:
            return True
  except OSError:
    return False
  return False


def spool_append(db_path, kind: str, ops: list, why: str, setup: tuple = ()) -> str:
  """기록 못 한 이벤트를 파일 1개로 원자 생성 (임시 파일 → os.replace) — 재생과 같은 파일을 만지지 않아 경쟁 유실 없음.
  반환: 'spooled' | 'spool-full'(상한 · 진단 로그) | 'spool-fail:<오류>'."""
  import uuid
  d = spool_dir(db_path)
  try:
    d.mkdir(parents=True, exist_ok=True)
    if _count_at_least(d, SPOOL_MAX_EVENTS):
      _spool_diag(db_path, f"spool full ({kind}) — 대기 {SPOOL_MAX_EVENTS}건 이상 · 이번 기록 미보관 · {why}")
      return "spool-full"
    eid = f"{time.time_ns():020d}-{os.getpid()}-{uuid.uuid4().hex[:12]}"
    data = json.dumps({"id": eid, "ts": time.time(), "kind": kind, "why": why,
                       "setup": [[str(x), []] for x in setup], "ops": [[str(o[0]), list(o[1])] for o in ops]},
                      ensure_ascii=False)
    if len(data.encode("utf-8")) > SPOOL_EVENT_MAX_BYTES:
      _spool_diag(db_path, f"spool event too large ({kind}) — 이번 기록 미보관 · {why}")
      return "spool-fail:too-large"
    tmp = d / f".tmp-{eid}"
    with open(tmp, "w", encoding="utf-8") as f:
      f.write(data)
      f.flush()
      os.fsync(f.fileno())                  # 내용을 디스크에 내린 뒤 이름 공개 (전원 장애 때 반쪽 이벤트 X)
    os.replace(tmp, d / f"{eid}.json")
    return "spooled"
  except Exception as e:  # noqa: BLE001
    _spool_diag(db_path, f"spool append 실패 ({kind}): {type(e).__name__} · {why}")
    return f"spool-fail:{type(e).__name__}"


def _spool_diag(db_path, msg: str) -> None:
  try:
    log = Path(db_path).parent.parent / "logs" / "hook-db-spool.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
      f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
  except Exception:  # noqa: BLE001
    pass


def _park(db_path, src: Path, sub: str, why: str) -> None:
  """지우지 않고 하위 폴더로 옮겨 보존 (held=손상·비허용 · failed=영구 오류 · unknown=반영 여부 불명)."""
  try:
    dst = src.parent / sub
    dst.mkdir(exist_ok=True)
    os.replace(src, dst / src.name)
    _spool_diag(db_path, f"spool {sub}/ 보관: {src.name} — {why}")
  except OSError as e:
    _spool_diag(db_path, f"spool {sub}/ 이동 실패(그대로 둠): {src.name} — {type(e).__name__} · {why}")


SPOOL_APPLIED_DDL = ("CREATE TABLE IF NOT EXISTS hook_spool_applied ("
                     "event_id TEXT PRIMARY KEY, kind TEXT, applied_at TEXT)")
SPOOL_MIGRATE_BATCH = 200               # 예전 스풀 이관: 한 번에 옮기는 줄 수 (남은 마감 안에서만 · 진행 위치 기록 후 다음 회차 이어서)
SPOOL_SCAN_MAX = 2000                   # 재생 1회에 훑는 폴더 항목 상한 (5000건 대기에서도 응답 경로 묶음)


def _migrate_legacy(db_path, d: Path, sess: "BoundedSession") -> bool:
  """예전 단일 스풀 파일 → 이벤트 파일 (잠금 안 · 남은 마감 안에서 SPOOL_MIGRATE_BATCH 줄씩 · 진행 바이트 위치 기록).
  이벤트 id = 파일 전체 해시 + 줄 번호 + 줄 해시 (결정적) → 중간 실패·재시작으로 같은 이벤트를 다시 만들어도
  hook_spool_applied 가 한 번만 반영 (DB 멱등). 반환 = 이관 끝(또는 할 것 없음) 여부."""
  import hashlib
  sp = spool_path(db_path)
  mig = sp.with_name(sp.name + ".migrating")
  pos_f = sp.with_name(sp.name + ".migrating.pos")
  if sp.exists() and not mig.exists():
    try:
      os.replace(sp, mig)
    except OSError:
      return True                             # 예전 판 writer 가 열고 있음 → 다음에 (이관 대상 아님으로 진행)
  if not mig.exists():
    return True
  d.mkdir(parents=True, exist_ok=True)
  fh = hashlib.sha1()
  with open(mig, "rb") as f:                  # 파일 identity (같은 줄 번호·내용이어도 다른 파일이면 다른 id)
    for chunk in iter(lambda: f.read(1 << 20), b""):
      fh.update(chunk)
  fid = fh.hexdigest()[:12]
  try:
    pos, idx = (int(x) for x in pos_f.read_text(encoding="ascii").split())
  except (OSError, ValueError):
    pos, idx = 0, 0
  moved = 0
  with open(mig, "rb") as f:
    f.seek(pos)
    while moved < SPOOL_MIGRATE_BATCH and sess.remaining() > 0.1:
      raw = f.readline()
      if not raw:
        break
      ln = raw.decode("utf-8", errors="replace").rstrip("\r\n")
      i, idx = idx, idx + 1
      if ln.strip():
        name = f"00000000000000000000-legacy-{fid}-{i:06d}-{hashlib.sha1(ln.encode('utf-8')).hexdigest()[:8]}"
        try:
          rec = json.loads(ln)
          ok = isinstance(rec, dict)
        except json.JSONDecodeError:
          ok = False
        if ok:
          body = json.dumps({"id": name, "ts": rec.get("ts"), "kind": rec.get("kind"), "why": rec.get("why"),
                             "setup": [], "ops": rec.get("ops") or []}, ensure_ascii=False)
          dst = d / f"{name}.json"
        else:
          (d / "held").mkdir(exist_ok=True)
          body, dst = ln, d / "held" / f"{name}.legacy-line"
        tmp = d / f".tmp-{name}"
        tmp.write_text(body, encoding="utf-8")
        os.replace(tmp, dst)
        moved += 1
      pos = f.tell()
    finished = not f.readline()
  if finished:
    mig.unlink()
    try:
      pos_f.unlink()
    except OSError:
      pass
    _spool_diag(db_path, f"예전 스풀 이관 끝 ({idx}줄 · 파일 {fid})")
    return True
  pos_f.write_text(f"{pos} {idx}", encoding="ascii")
  return False


def _applied(sess: "BoundedSession", eid: str):
  """반영 증거 조회 — True/False · 조회 실패 = None (판단 보류)."""
  try:
    return sess.sql("SELECT 1 FROM hook_spool_applied WHERE event_id = ?", (eid,)).fetchone() is not None
  except Exception:  # noqa: BLE001
    return None


def spool_replay(sess: "BoundedSession", db_path, max_events: int = 20) -> int:
  """남은 시간 안에서 오래된 이벤트부터 반영 — 반영한 이벤트 수.
  멱등 소비 계약 (R375 18차 검토): 반영 증거 hook_spool_applied(event_id) 를 이벤트 SQL 과 **같은 트랜잭션**에 기록.
  x.json → x.inflight(점유) → 선검증 → [증거 INSERT + setup + ops] commit → 파일 삭제(실패 시 .done).
  이전 소비자가 남긴 .inflight 는 증거로 결정: 증거 있음 = commit 됨 → 삭제만 · 증거 없음 = commit 안 됨(트랜잭션 원자성) → .json 으로 되돌려 재생.
  이미 증거가 있는 이벤트(이관 재시작 등)는 SQL 을 다시 실행하지 않고 정리만. unknown/ (증거 장치 전 보관분)은 자동 재생하지 않음."""
  import heapq
  d = spool_dir(db_path)
  if (not d.exists() and not spool_path(db_path).exists()) or sess.remaining() <= 0.05:
    return 0
  try:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent))
    import proc_lock as pl
  except Exception:  # noqa: BLE001
    return 0
  fd = pl.try_lock(str(d) + ".lock")
  if fd is None:
    return 0
  done = 0
  try:
    try:
      sess.sql(SPOOL_APPLIED_DDL)
    except Exception as e:  # noqa: BLE001 — 증거 표 없이는 소비하지 않음 (멱등 보장 불가)
      _spool_diag(db_path, f"반영 증거 표 준비 실패 — 이번 회차 재생 안 함 ({type(e).__name__})")
      return 0
    try:
      _migrate_legacy(db_path, d, sess)
    except Exception as e:  # noqa: BLE001 — 이관 중 실패 = 이번 회차 소비 안 함 (다음 회차 이어서 · 멱등이라 중복 X)
      _spool_diag(db_path, f"예전 스풀 이관 보류 — 이번 회차 재생 안 함: {type(e).__name__}")
      return 0
    if not d.exists():
      return 0
    now, names, scanned = time.time(), [], 0
    with os.scandir(d) as it:
      for e in it:
        scanned += 1
        if scanned > SPOOL_SCAN_MAX or (scanned % 200 == 0 and sess.remaining() <= 0.1):
          break                                # 큰 대기열에서도 한 회차 훑기량 묶음 (나머지는 다음 회차)
        if not e.is_file():
          continue
        nm = e.name
        if nm.endswith(".done"):
          try:
            os.unlink(e.path)
          except OSError:
            pass
        elif nm.endswith(".inflight"):
          eid_guess = nm[:-9]
          src = d / (eid_guess + ".json")
          try:
            with open(e.path, "rb") as f:
              rec = json.loads(f.read(SPOOL_EVENT_MAX_BYTES + 1).decode("utf-8"))
            eid = rec.get("id") if isinstance(rec, dict) else None
          except (OSError, ValueError):
            eid = None
          st_ = _applied(sess, eid) if isinstance(eid, str) else None
          if st_ is True:
            try:
              os.unlink(e.path)                  # commit 됨 → 정리만 (재생 X)
            except OSError:
              pass
          elif st_ is False:
            try:
              os.replace(e.path, src)            # commit 안 됨 → 되돌려 재생 대상으로
              names.append(src.name)
            except OSError:
              pass
          elif eid is None:
            _park(db_path, Path(e.path), "held", "중단된 점유 파일이 손상 (아무것도 실행 안 함)")
          # 조회 실패(None) = 판단 보류 · 그대로 두고 다음 회차
        elif nm.startswith(".tmp-"):
          try:
            if now - e.stat().st_mtime > SPOOL_STALE_TMP_SEC:
              _park(db_path, Path(e.path), "held", "쓰다 만 임시 파일")
          except OSError:
            pass
        elif nm.endswith(".json"):
          names.append(nm)
    for name in heapq.nsmallest(max_events, names):
      if sess.remaining() <= 0.05:
        break
      src, inf = d / name, d / (name[:-5] + ".inflight")
      try:
        os.replace(src, inf)
      except OSError:
        continue
      try:
        with open(inf, "rb") as f:
          raw = f.read(SPOOL_EVENT_MAX_BYTES + 1)
        rec = json.loads(raw.decode("utf-8")) if len(raw) <= SPOOL_EVENT_MAX_BYTES else None
      except (OSError, ValueError):
        rec = None
      if not _valid_event(rec):
        _park(db_path, inf, "held", "손상·크기 초과·허용 밖 문장 (아무것도 실행 안 함)")
        continue
      dup = False
      try:
        for stmt, params in rec.get("setup") or []:
          sess.sql(stmt, params)
        try:
          sess.sql("INSERT INTO hook_spool_applied(event_id, kind, applied_at) VALUES(?, ?, ?)",
                   (rec["id"], str(rec.get("kind") or ""), time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())))
        except sqlite3.IntegrityError:
          dup = True                             # 이미 반영된 이벤트 (이관 재시작·중단 후 재생성) → SQL 재실행 X
        if not dup:
          for stmt, params in rec["ops"]:
            sess.sql(stmt, params)
          sess.commit()
        else:
          sess.conn.rollback()
      except Exception as e:  # noqa: BLE001
        try:
          sess.conn.rollback()
        except Exception:  # noqa: BLE001
          pass
        if isinstance(e, TimeoutError) or _is_busy(e):     # 일시적 → 원래 이름으로 되돌리고 중단
          try:
            os.replace(inf, src)
          except OSError:
            pass                                 # 남은 .inflight 는 다음 회차가 증거로 결정
          break
        _park(db_path, inf, "failed", f"영구 오류 {type(e).__name__}: {e}")
        continue
      if not dup:
        done += 1
      try:
        os.unlink(inf)
      except OSError:
        try:
          os.replace(inf, d / (name[:-5] + ".done"))
        except OSError:
          pass                                   # 남은 .inflight 는 다음 회차가 증거로 정리 (재생 X)
  except Exception as e:  # noqa: BLE001
    _spool_diag(db_path, f"spool replay 실패: {type(e).__name__}")
  finally:
    pl.release(fd)
  return done


def bounded_insert(db_path, kind: str, ops: list, budget: Optional[float] = None, setup: tuple = ()) -> str:
  """훅 기록 정본 — setup(CREATE IF NOT EXISTS) + ops(INSERT) 를 전체 마감 안에서 · 실패는 스풀(setup 동봉) · 성공하면 스풀 이어 쓰기.
  ops 에 발생 시각을 명시 값으로 넣을 것 (재생 때 DEFAULT CURRENT_TIMESTAMP 로 시각이 바뀌지 않게).
  반환: 'ok' | 'ok+replay<n>' | 'spooled' | 'spool-full' | 'spool-fail:..' | 'skip:DB 없음'."""
  if not Path(db_path).exists():
    return "skip:DB 없음"
  sess = None
  try:
    sess = BoundedSession(db_path, budget)
    for stmt in setup:
      sess.sql(stmt)
    for stmt, params in ops:
      sess.sql(stmt, params)
    sess.commit()
  except Exception as e:  # noqa: BLE001 — 잠금·시간 초과·디스크 = 스풀
    if sess is not None:
      sess.close()
      sess = None
    return spool_append(db_path, kind, [list(o) for o in ops], type(e).__name__, setup)
  try:
    n = spool_replay(sess, db_path)
    return f"ok+replay{n}" if n else "ok"
  finally:
    sess.close()


def ensure_history_tables(conn) -> None:
  """이력 테이블 4종 (conversations·session_summary·problem_solutions·file_audit). Idempotent.

  2026-10-02: 쓰는 쪽(conversation_logger·save_solution·audit_file_write)만 있고 DDL 이 kit 에
  없어서, 새 PC 의 orca.db 에서는 INSERT 가 except 에 삼켜져 이력이 0건이었다.
  schema_version 조기 return 과 무관하게 매번 실행한다 (기존 DB 에도 보강).
  컬럼은 각 INSERT/SELECT 문 기준. hit_count·last_hit_ts 는 promote-solutions 가 쓰는 컬럼.
  """
  conn.executescript("""
    CREATE TABLE IF NOT EXISTS conversations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      session_id TEXT, turn INTEGER, role TEXT, content TEXT,
      content_hash TEXT, tokens INTEGER, tags TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id, turn);
    CREATE TABLE IF NOT EXISTS session_summary (
      session_id TEXT PRIMARY KEY,
      started_at TIMESTAMP, ended_at TIMESTAMP, turns INTEGER,
      summary TEXT, key_decisions TEXT, files_touched TEXT, tokens_total INTEGER,
      updated_at TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS problem_solutions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      session_id TEXT, problem TEXT, category TEXT, keywords TEXT,
      approach TEXT, solution TEXT, files_modified TEXT, commands_run TEXT,
      verified INTEGER DEFAULT 0, reusable_score INTEGER DEFAULT 5,
      problem_hash TEXT UNIQUE, hit_count INTEGER DEFAULT 0, last_hit_ts TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS file_audit (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      session_id TEXT, action TEXT, path TEXT, size INTEGER,
      hash TEXT, actor TEXT, reason TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_file_audit_ts ON file_audit(ts);
  """)
  # 이미 만들어진 테이블에 빠진 컬럼 보강 (CREATE IF NOT EXISTS 는 컬럼을 안 더한다)
  #   2026-10-02: session_summary.updated_at 누락 → conversation_logger 의 ON CONFLICT UPDATE 실패,
  #   resume-last-24h 의 WHERE updated_at 조회가 조용히 빈 결과
  need = {
    "session_summary": [("updated_at", "TIMESTAMP")],
    "problem_solutions": [("hit_count", "INTEGER DEFAULT 0"), ("last_hit_ts", "TIMESTAMP")],
    # approval-gate.py 가 쓰는 승인 게이트 컬럼 — tasks DDL 에 없어 새 PC 에서 승인 기능 불능
    "tasks": [("approval_state", "TEXT DEFAULT 'not_required'"), ("risk_category", "TEXT"), ("risk_detail", "TEXT"), ("approved_at", "INTEGER"), ("approved_by", "TEXT")],
  }
  for tbl, cols in need.items():
    have = {r[1] for r in conn.execute(f"PRAGMA table_info({tbl})")}
    if not have:
      continue  # 아직 없는 테이블 (새 DB 의 tasks 등) — 생성 후 init_schema 끝에서 다시 보강 (1006 A2 실측 FAIL)
    for col, typ in cols:
      if col not in have:
        conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {typ}")


def init_schema() -> None:
  """Initialize database schema if missing. Idempotent."""
  with tx() as conn:
    ensure_history_tables(conn)
    # Check schema version
    # 2026-11-20 (R346 후속): schema_version 행만 보고 '초기화됨' 으로 돌아가, 다른 모듈이 schema_version 만 먼저 만든 DB 에서는
    #   tasks 등 기본 표가 끝내 생기지 않았다 (새 clone 전체 시험에서 'no such table: tasks' 4건 · Windows CI 필수 실패 원인).
    #   아래 구문은 전부 IF NOT EXISTS · INSERT OR IGNORE 라 다시 돌려도 안전 → 핵심 표가 모두 있을 때만 건너뛴다.
    try:
      cur = conn.execute("SELECT version FROM schema_version LIMIT 1")
      have = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
      if cur.fetchone() and {"workers", "tasks", "metrics", "quota", "budget", "session"} <= have:
        return  # Already initialized
    except sqlite3.OperationalError:
      pass  # noqa: BLE001

    # Create tables
    conn.executescript("""
      CREATE TABLE IF NOT EXISTS workers (
        worker_id TEXT PRIMARY KEY,
        ai_type TEXT NOT NULL,
        pid INTEGER,
        started_at INTEGER NOT NULL,
        last_heartbeat INTEGER NOT NULL,
        status TEXT NOT NULL,
        quota_backoff_until INTEGER,
        quota_retry_count INTEGER DEFAULT 0
      );

      CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        task_file TEXT NOT NULL,
        ai_assigned TEXT,
        worker_id TEXT,
        status TEXT NOT NULL,
        locked_at INTEGER,
        locked_until INTEGER,
        created_at INTEGER NOT NULL,
        completed_at INTEGER,
        retry_count INTEGER DEFAULT 0
      );

      CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT,
        ai TEXT NOT NULL,
        model_id TEXT,
        tokens_in INTEGER NOT NULL DEFAULT 0,
        tokens_out INTEGER NOT NULL DEFAULT 0,
        cost_usd REAL,
        latency_ms INTEGER NOT NULL,
        success INTEGER NOT NULL,
        cache_hit INTEGER DEFAULT 0,
        retry INTEGER DEFAULT 0,
        recorded_at INTEGER NOT NULL,
        error_class TEXT
      );

      CREATE INDEX IF NOT EXISTS idx_metrics_recorded
        ON metrics(recorded_at);
      CREATE INDEX IF NOT EXISTS idx_metrics_ai
        ON metrics(ai);
      CREATE INDEX IF NOT EXISTS idx_metrics_task_id
        ON metrics(task_id);

      CREATE TABLE IF NOT EXISTS quota (
        ai TEXT PRIMARY KEY,
        exceeded INTEGER NOT NULL DEFAULT 0,
        exceeded_since INTEGER,
        expires_at INTEGER,
        last_error TEXT,
        updated_at INTEGER NOT NULL
      );

      CREATE TABLE IF NOT EXISTS budget (
        id INTEGER PRIMARY KEY DEFAULT 1,
        daily_limit_usd REAL,
        today_spent_usd REAL DEFAULT 0,
        today_date TEXT NOT NULL,
        breaker_tripped INTEGER DEFAULT 0,
        breaker_tripped_at INTEGER,
        updated_at INTEGER NOT NULL,
        CHECK (id = 1)
      );

      CREATE TABLE IF NOT EXISTS session (
        id INTEGER PRIMARY KEY DEFAULT 1,
        orca_enabled INTEGER DEFAULT 1,
        orca_stopped_reason TEXT,
        claude_heartbeat INTEGER NOT NULL,
        CHECK (id = 1)
      );

      CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY,
        applied_at INTEGER
      );
    """)

    # Insert initial records
    now = int(time.time())
    today = time.strftime("%Y-%m-%d", time.gmtime(now))

    conn.execute(
      "INSERT OR IGNORE INTO budget (id, today_spent_usd, today_date, updated_at) "
      "VALUES (1, 0, ?, ?)",
      (today, now)
    )
    conn.execute(
      "INSERT OR IGNORE INTO session (id, orca_enabled, claude_heartbeat) "
      "VALUES (1, 1, ?)",
      (now,)
    )
    conn.execute(
      "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (1, ?)",
      (now,)
    )
    # 새 DB: 위에서 막 만든 tasks 등에 보강 컬럼 추가 (앞 호출에선 테이블이 없어 건너뜀)
    ensure_history_tables(conn)


# Worker management
def register_worker(worker_id: str, ai_type: str, pid: int) -> None:
  """Register or update worker. Creates entry if missing."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "INSERT OR REPLACE INTO workers "
      "(worker_id, ai_type, pid, started_at, last_heartbeat, status) "
      "VALUES (?, ?, ?, ?, ?, 'idle')",
      (worker_id, ai_type, pid, now, now)
    )


def update_heartbeat(worker_id: str) -> None:
  """Update worker's last_heartbeat timestamp."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "UPDATE workers SET last_heartbeat = ? WHERE worker_id = ?",
      (now, worker_id)
    )


def mark_worker_dead(worker_id: str, reason: str = None) -> None:
  """Mark worker as dead."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "UPDATE workers SET status = 'dead', last_heartbeat = ? "
      "WHERE worker_id = ?",
      (now, worker_id)
    )


def get_live_workers(max_age_sec: int = 300) -> List[Dict[str, Any]]:
  """Return list of workers with recent heartbeat."""
  now = int(time.time())
  cutoff = now - max_age_sec
  with tx() as conn:
    rows = conn.execute(
      "SELECT worker_id, ai_type, pid, status FROM workers "
      "WHERE last_heartbeat >= ? AND status != 'dead' "
      "ORDER BY worker_id",
      (cutoff,)
    ).fetchall()
  return [dict(row) for row in rows]


def set_worker_quota_wait(worker_id: str, backoff_sec: int) -> None:
  """Set worker quota backoff until timestamp."""
  until = int(time.time()) + backoff_sec
  with tx() as conn:
    conn.execute(
      "UPDATE workers SET quota_backoff_until = ?, quota_retry_count = quota_retry_count + 1 "
      "WHERE worker_id = ?",
      (until, worker_id)
    )


# Task + lock management
def try_lock_task(task_id: str, task_file: str, worker_id: str, ttl_sec: int = 1800) -> bool:
  """Atomically lock task for worker. Returns True if successful."""
  now = int(time.time())
  locked_until = now + ttl_sec
  with tx() as conn:
    # Check if already locked by someone else
    row = conn.execute(
      "SELECT worker_id, locked_until FROM tasks WHERE task_id = ?",
      (task_id,)
    ).fetchone()

    if row:
      if row["worker_id"] and row["locked_until"] and row["locked_until"] > now:
        return False  # Already locked by another worker
      # Stale lock, take over
      conn.execute(
        "UPDATE tasks SET worker_id = ?, locked_at = ?, locked_until = ?, status = 'locked' "
        "WHERE task_id = ?",
        (worker_id, now, locked_until, task_id)
      )
      return True

    # New task, insert lock
    conn.execute(
      "INSERT INTO tasks "
      "(task_id, task_file, ai_assigned, worker_id, status, locked_at, locked_until, created_at) "
      "VALUES (?, ?, NULL, ?, 'locked', ?, ?, ?)",
      (task_id, task_file, worker_id, now, locked_until, now)
    )
  return True


def release_task_lock(task_id: str, final_status: str) -> None:
  """Release task lock and set final status."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "UPDATE tasks SET status = ?, worker_id = NULL, locked_at = NULL, "
      "locked_until = NULL, completed_at = ? WHERE task_id = ?",
      (final_status, now, task_id)
    )


def expire_stale_locks() -> int:
  """Free locks that exceed TTL. Returns count freed."""
  now = int(time.time())
  with tx() as conn:
    cur = conn.execute(
      "UPDATE tasks SET worker_id = NULL, status = 'pending' "
      "WHERE locked_until IS NOT NULL AND locked_until < ? AND status = 'locked'",
      (now,)
    )
  return cur.rowcount


# Metrics
def record_metric(
  ai: str,
  model_id: str,
  tokens_in: int,
  tokens_out: int,
  cost_usd: Optional[float],
  latency_ms: int,
  success: bool,
  task_id: Optional[str] = None,
  cache_hit: bool = False,
  error_class: Optional[str] = None,
) -> None:
  """Record API call metric."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "INSERT INTO metrics "
      "(task_id, ai, model_id, tokens_in, tokens_out, cost_usd, latency_ms, "
      "success, cache_hit, recorded_at, error_class) "
      "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
      (task_id, ai, model_id, tokens_in, tokens_out, cost_usd, latency_ms,
       1 if success else 0, 1 if cache_hit else 0, now, error_class)
    )


# 결과를 모르는 지표 행 (정본 · R375 8차 검토 P1) — 성공률·배정 소비처는 이 행을 분모·분자에서 뺀다:
#   ① error_class='outcome_unknown' (13500384 이후 서브에이전트 훅 · success 열은 NOT NULL 이라 1)
#   ② 그 이전 서브에이전트 훅 행 (task_id 'subagent-…' · error_class 없음 · success 1 고정이던 611건) — 운영 DB 는 고치지 않고 읽을 때 구분
OUTCOME_UNKNOWN_SQL = ("(COALESCE(error_class,'') = 'outcome_unknown' OR "
                       "(COALESCE(task_id,'') LIKE 'subagent-%' AND error_class IS NULL))")


def get_metrics_summary(hours: int = 24) -> Dict[str, Any]:
  """Return aggregated metrics for last N hours."""
  since = int(time.time()) - (hours * 3600)
  with tx() as conn:
    rows = conn.execute(
      # R375 8차 검토 P1: error_class=outcome_unknown(결과를 모름 · 서브에이전트 훅) 행은 성공률 분모·분자에서 뺀다
      #   (success 열은 NOT NULL 이라 1 이 들어 있음 → 그대로 더하면 성공률 100% 거짓 값) · 아는 결과 0건 = None(UNKNOWN)
      "SELECT ai, COUNT(*) as count, "
      f"SUM(CASE WHEN {OUTCOME_UNKNOWN_SQL} THEN 0 ELSE 1 END) as known, "
      f"SUM(CASE WHEN {OUTCOME_UNKNOWN_SQL} THEN 0 ELSE success END) as successes, "
      "SUM(tokens_in) as total_tokens_in, SUM(tokens_out) as total_tokens_out, "
      "SUM(cost_usd) as total_cost, AVG(latency_ms) as avg_latency, "
      "SUM(cache_hit) as cache_hits "
      "FROM metrics WHERE recorded_at >= ? GROUP BY ai ORDER BY ai",
      (since,)
    ).fetchall()

  summary = {}
  for row in rows:
    ai = row["ai"]
    summary[ai] = {
      "count": row["count"],
      "outcome_known": row["known"] or 0,
      "success_rate": ((row["successes"] or 0) / row["known"]) if row["known"] else None,
      "tokens_in": row["total_tokens_in"] or 0,
      "tokens_out": row["total_tokens_out"] or 0,
      "total_cost_usd": row["total_cost"] or 0.0,
      "avg_latency_ms": row["avg_latency"] or 0,
      "cache_hits": row["cache_hits"] or 0,
    }
  return summary


# Quota management
def set_quota_exceeded(ai: str, expires_at: int, error_msg: str) -> None:
  """Mark AI as quota-exceeded until expires_at."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "INSERT OR REPLACE INTO quota "
      "(ai, exceeded, exceeded_since, expires_at, last_error, updated_at) "
      "VALUES (?, 1, ?, ?, ?, ?)",
      (ai, now, expires_at, error_msg, now)
    )


def is_quota_exceeded(ai: str) -> bool:
  """Check if AI is quota-exceeded. Auto-clears if expired."""
  now = int(time.time())
  with tx() as conn:
    row = conn.execute(
      "SELECT exceeded, expires_at FROM quota WHERE ai = ?",
      (ai,)
    ).fetchone()

    if not row:
      return False

    if row["exceeded"] == 0:
      return False

    if row["expires_at"] and row["expires_at"] < now:
      # Expired, clear it
      conn.execute("UPDATE quota SET exceeded = 0, expires_at = NULL WHERE ai = ?", (ai,))
      return False

  return True


def clear_quota(ai: str) -> None:
  """Manually clear quota exceeded flag."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "UPDATE quota SET exceeded = 0, expires_at = NULL, updated_at = ? WHERE ai = ?",
      (now, ai)
    )


# Budget management
def add_spend(cost_usd: float) -> float:
  """Add to today's spend, return new total."""
  check_daily_rollover()
  with tx() as conn:
    conn.execute(
      "UPDATE budget SET today_spent_usd = today_spent_usd + ? WHERE id = 1",
      (cost_usd,)
    )
    row = conn.execute(
      "SELECT today_spent_usd FROM budget WHERE id = 1"
    ).fetchone()
  return row["today_spent_usd"] if row else cost_usd


def is_breaker_tripped() -> bool:
  """Check if budget breaker is tripped."""
  with tx() as conn:
    row = conn.execute(
      "SELECT breaker_tripped, daily_limit_usd FROM budget WHERE id = 1"
    ).fetchone()
  if not row:
    return False
  return row["breaker_tripped"] == 1


def trip_breaker(reason: str = None) -> None:
  """Manually trip the budget breaker."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "UPDATE budget SET breaker_tripped = 1, breaker_tripped_at = ? WHERE id = 1",
      (now,)
    )


def reset_breaker() -> None:
  """Reset the budget breaker."""
  with tx() as conn:
    conn.execute(
      "UPDATE budget SET breaker_tripped = 0, breaker_tripped_at = NULL WHERE id = 1"
    )


# Agent 결제 경계 예산 (2026-11-03 · 유료 headless Agent 호출 직전 강제)
#   예약(open) → 정산(settled 실측 / unknown 예약액 그대로 / released 미실행 0).
#   실측 비용은 기존대로 add_spend 로 today_spent_usd 에 들어가고, 이 표는 미정산·UNKNOWN·체인 합계만 책임진다.
def _ensure_agent_budget_table(conn) -> None:
  conn.execute("""
    CREATE TABLE IF NOT EXISTS agent_budget_reservations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      day TEXT NOT NULL,
      chain_id TEXT,
      role TEXT,
      reserved_usd REAL NOT NULL,
      charged_usd REAL,
      status TEXT NOT NULL,
      created_at INTEGER NOT NULL,
      expires_at INTEGER NOT NULL,
      settled_at INTEGER,
      note TEXT
    )""")


def agent_budget_reserve(amount_usd: float, role: str, chain_id: str = None, policy: dict = None,
                         ttl_s: int = 1800, dry_run: bool = False) -> Dict[str, Any]:
  """유료 Agent 1회 시작 전 예산 예약. 하나라도 걸리면 {"ok": False, "reason": ...} · 호출 0건.
  검사: 차단기 · 일일 예산(NULL=미설정=금지) · 호출당 상한 · 동시 실행 수 · 체인(수정+Judge) 호출 수·합계.
  DB 오류도 차단 (fail-closed). dry_run=True 는 예약 없이 판정만."""
  pol = policy or {}
  def deny(reason, retryable):
    return {"ok": False, "budget_blocked": True, "retryable": retryable, "deferred": retryable,
            "reason": reason}
  try:
    check_daily_rollover()
    now = int(time.time())
    day = time.strftime("%Y-%m-%d", time.gmtime(now))
    with tx() as conn:
      _ensure_agent_budget_table(conn)
      b = conn.execute(
        "SELECT daily_limit_usd, today_spent_usd, breaker_tripped FROM budget WHERE id = 1"
      ).fetchone()
      if b is None:
        return deny("budget 행 없음 · 유료 호출 금지", True)
      if b["breaker_tripped"] == 1:
        return deny("비용 차단기 작동 중 · 유료 호출 금지", True)
      limits = [float(v) for v in (b["daily_limit_usd"], pol.get("agent_daily_budget_usd")) if v is not None]
      if not limits:
        return deny("일일 예산 미설정 (NULL) · 무제한으로 취급하지 않음 · 유료 호출 금지", True)
      daily = min(limits)
      per_call = float(pol.get("agent_max_budget_usd", 3.0))
      if not 0 < float(amount_usd) <= per_call:
        return deny(f"호출당 상한 위반: {amount_usd} (상한 {per_call})", False)
      rows = conn.execute(
        "SELECT status, reserved_usd, charged_usd, expires_at FROM agent_budget_reservations WHERE day = ?",
        (day,)).fetchall()
      open_rows = [r for r in rows if r["status"] == "open"]
      unknown = sum(float(r["charged_usd"] or 0) for r in rows if r["status"] == "unknown")
      committed = float(b["today_spent_usd"] or 0) + unknown + sum(float(r["reserved_usd"]) for r in open_rows)
      if committed + float(amount_usd) > daily:
        return deny(f"일일 예산 부족: 사용·예약 ${committed:.4f} + 요청 ${float(amount_usd):.2f} > 한도 ${daily:.2f}",
                    True)
      max_par = int(pol.get("agent_max_parallel", 3))
      running = sum(1 for r in open_rows if r["expires_at"] > now)
      if running >= max_par:
        return deny(f"동시 실행 예산 초과: 실행 중 {running} ≥ {max_par}", True)
      if chain_id:
        ch = conn.execute(
          "SELECT status, reserved_usd, charged_usd FROM agent_budget_reservations "
          "WHERE chain_id = ? AND status != 'released'", (chain_id,)).fetchall()
        max_calls = int(pol.get("agent_max_calls_per_chain", 3))
        if len(ch) >= max_calls:
          return deny(f"재시도 상한: 체인 {chain_id} 호출 {len(ch)} ≥ {max_calls}", False)
        ch_spent = sum(float(r["reserved_usd"] if r["charged_usd"] is None else r["charged_usd"]) for r in ch)
        ch_cap = float(pol.get("agent_chain_budget_usd", 5.0))
        if ch_spent + float(amount_usd) > ch_cap:
          return deny(f"체인 예산 초과 (수정+Judge 합산): ${ch_spent:.4f} + ${float(amount_usd):.2f} > ${ch_cap:.2f}",
                      False)
      if dry_run:
        return {"ok": True, "dry_run": True, "daily_limit_usd": daily, "committed_usd": round(committed, 6)}
      cur = conn.execute(
        "INSERT INTO agent_budget_reservations (day, chain_id, role, reserved_usd, status, created_at, expires_at) "
        "VALUES (?, ?, ?, ?, 'open', ?, ?)", (day, chain_id, role, float(amount_usd), now, now + int(ttl_s)))
      return {"ok": True, "reservation_id": cur.lastrowid, "daily_limit_usd": daily,
              "committed_usd": round(committed, 6)}
  except Exception as e:
    return deny(f"예산 확인 실패 (fail-closed): {e}", True)


def agent_budget_settle(reservation_id: int, cost_usd: Optional[float], launched: bool) -> str:
  """예약 정산. 미실행 = released(0) · 실측 = settled(실측) · 실행했는데 사용량 UNKNOWN = unknown(예약액 그대로 차감)."""
  if launched and cost_usd is not None:
    status, charged = "settled", float(cost_usd)
  elif launched:
    status, charged = "unknown", None
  else:
    status, charged = "released", 0.0
  with tx() as conn:
    _ensure_agent_budget_table(conn)
    if status == "unknown":
      conn.execute("UPDATE agent_budget_reservations SET status = ?, charged_usd = reserved_usd, settled_at = ? "
                   "WHERE id = ? AND status = 'open'", (status, int(time.time()), reservation_id))
    else:
      conn.execute("UPDATE agent_budget_reservations SET status = ?, charged_usd = ?, settled_at = ? "
                   "WHERE id = ? AND status = 'open'", (status, charged, int(time.time()), reservation_id))
  return status


def check_daily_rollover() -> None:
  """Reset today_spent_usd if date changed."""
  today = time.strftime("%Y-%m-%d", time.gmtime(int(time.time())))
  now = int(time.time())
  with tx() as conn:
    row = conn.execute(
      "SELECT today_date FROM budget WHERE id = 1"
    ).fetchone()
    if row and row["today_date"] != today:
      conn.execute(
        "UPDATE budget SET today_spent_usd = 0, today_date = ?, updated_at = ? WHERE id = 1",
        (today, now)
      )


# Session management
def update_claude_heartbeat() -> None:
  """Update Claude Code session heartbeat."""
  now = int(time.time())
  with tx() as conn:
    conn.execute(
      "UPDATE session SET claude_heartbeat = ? WHERE id = 1",
      (now,)
    )


def is_claude_alive(max_age_sec: int = 300) -> bool:
  """Check if Claude Code session is alive."""
  now = int(time.time())
  with tx() as conn:
    row = conn.execute(
      "SELECT claude_heartbeat FROM session WHERE id = 1"
    ).fetchone()
  if not row:
    return False
  return (now - row["claude_heartbeat"]) <= max_age_sec


def set_orca_enabled(enabled: bool, reason: str = None) -> None:
  """Set orca enabled/disabled state."""
  now = int(time.time())
  reason_text = reason if reason else ("enabled" if enabled else "stopped")
  with tx() as conn:
    conn.execute(
      "UPDATE session SET orca_enabled = ?, orca_stopped_reason = ? WHERE id = 1",
      (1 if enabled else 0, reason_text if not enabled else None)
    )


def get_all_registered_workers_raw() -> List[Dict[str, Any]]:
  """Return all workers from database (no filtering)."""
  with tx() as conn:
    rows = conn.execute(
      "SELECT worker_id, ai_type, pid, status, quota_backoff_until, "
      "quota_retry_count, started_at, last_heartbeat FROM workers "
      "ORDER BY worker_id"
    ).fetchall()
  return [dict(row) for row in rows]


def get_workers_by_status(status: str) -> List[Dict[str, Any]]:
  """Return workers with a specific status."""
  with tx() as conn:
    rows = conn.execute(
      "SELECT worker_id, ai_type, pid, status, quota_retry_count "
      "FROM workers WHERE status = ? ORDER BY worker_id",
      (status,)
    ).fetchall()
  return [dict(row) for row in rows]
