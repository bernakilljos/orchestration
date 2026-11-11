#!/usr/bin/env python3
"""
Lightweight OpenTelemetry-inspired tracing without external dependencies.

Pure Python implementation for:
- Trace ID generation and propagation
- Span tracking (start/end timing)
- Context correlation across function calls
- Integration with structured_logger

Usage:
    from lib.trace import Tracer, get_trace_id, set_trace_id

    tracer = Tracer(__name__)
    with tracer.span("operation_name"):
        # Code to trace
        pass

    # Or manual tracing
    set_trace_id("custom-trace-id")
    tracer.span_start("my_span")
    # ... do work ...
    tracer.span_end("my_span")
"""

import time
import json
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import threading
from contextlib import contextmanager

try:
    from .structured_logger import (
        get_trace_id,
        set_trace_id,
        new_trace_id,
        get_logger
    )
except ImportError:   # 명령줄 직접 실행 (python lib/trace.py show …) · 훅의 파일 로드
    import importlib.util as _ilu
    _sl_spec = _ilu.spec_from_file_location("_trace_structured_logger", str(Path(__file__).with_name("structured_logger.py")))
    _sl = _ilu.module_from_spec(_sl_spec)
    _sl_spec.loader.exec_module(_sl)
    get_trace_id, set_trace_id, new_trace_id, get_logger = _sl.get_trace_id, _sl.set_trace_id, _sl.new_trace_id, _sl.get_logger

class Span:
    """Represents a single span (unit of work)."""

    def __init__(self, trace_id: str, span_id: str, name: str, start_time: float):
        self.trace_id = trace_id
        self.span_id = span_id
        self.name = name
        self.start_time = start_time
        self.end_time: Optional[float] = None
        self.attributes: Dict[str, Any] = {}
        self.status = "UNSET"  # UNSET, OK, ERROR
        self.error: Optional[str] = None

    def set_attribute(self, key: str, value: Any):
        """Set a span attribute."""
        self.attributes[key] = value

    def set_status(self, status: str, error: Optional[str] = None):
        """Set span status (OK, ERROR)."""
        self.status = status
        if error:
            self.error = error

    def end(self):
        """Mark span as ended."""
        self.end_time = time.time()

    @property
    def duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dict (for JSON export)."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "name": self.name,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat() + "Z",
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() + "Z" if self.end_time else None,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error": self.error,
            "attributes": self.attributes,
        }

class Tracer:
    """Tracer for creating and managing spans."""

    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(name)
        self.spans: Dict[str, Span] = {}
        self.trace_id = new_trace_id()
        set_trace_id(self.trace_id)

    def set_trace_id(self, trace_id: str):
        """Set custom trace ID."""
        self.trace_id = trace_id
        set_trace_id(trace_id)

    def span_start(self, name: str, **attributes) -> str:
        """
        Start a new span.

        Args:
            name: Span name
            **attributes: Initial span attributes

        Returns:
            span_id
        """
        span_id = f"{len(self.spans):04d}"
        span = Span(self.trace_id, span_id, name, time.time())

        for key, value in attributes.items():
            span.set_attribute(key, value)

        self.spans[span_id] = span
        self.logger.debug(
            f"Span start: {name}",
            span_id=span_id,
            trace_id=self.trace_id
        )
        return span_id

    def span_end(self, span_id: str, status: str = "OK", error: Optional[str] = None):
        """
        End a span.

        Args:
            span_id: Span ID (returned by span_start)
            status: 'OK' or 'ERROR'
            error: Error message (if status=ERROR)
        """
        if span_id not in self.spans:
            self.logger.warning(f"Span not found: {span_id}")
            return

        span = self.spans[span_id]
        span.end()
        span.set_status(status, error)

        self.logger.debug(
            f"Span end: {span.name}",
            span_id=span_id,
            trace_id=self.trace_id,
            duration_ms=span.duration_ms,
            status=status
        )

    @contextmanager
    def span(self, name: str, **attributes):
        """
        Context manager for span creation.

        Usage:
            with tracer.span("my_operation", user_id=42):
                # Code here
                pass
        """
        span_id = self.span_start(name, **attributes)
        try:
            yield span_id
            self.span_end(span_id, status="OK")
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            self.span_end(span_id, status="ERROR", error=str(e))
            raise

    def set_span_attribute(self, span_id: str, key: str, value: Any):
        """Set an attribute on a span."""
        if span_id not in self.spans:
            return
        self.spans[span_id].set_attribute(key, value)

    def export_spans(self) -> str:
        """Export all spans as JSON."""
        spans = [span.to_dict() for span in self.spans.values()]
        return json.dumps(
            {
                "trace_id": self.trace_id,
                "name": self.name,
                "span_count": len(spans),
                "spans": spans,
            },
            indent=2,
            default=str
        )

    def save_spans(self, filename: Optional[str] = None):
        """Save spans to a JSON file."""
        if filename is None:
            log_dir = Path(__file__).parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            filename = log_dir / f"traces-{self.trace_id}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.export_spans())

        self.logger.info(f"Traces exported", file=str(filename), span_count=len(self.spans))

# ─────────────────────────────────────────────────────────────────────────────
# 2026-11-11 §78 요청 단위 추적 — 요청 접수부터 단계·시도(실패→대체→성공)·시간·근거를 같은 추적번호로 기록
#   추적번호 = Ledger 등록 때 만드는 event_id (R 번호는 별칭 · clear 시 재사용되므로 정본 아님)
#   정본 저장 = orca.db trace_events (표가 있을 때만) · 없으면 logs/trace-events.jsonl (운영 DB 스키마 변경은 별도 승인)
#   기록 실패는 본 작업을 멈추지 않는다 (fail-safe) · 문자열은 redact.mask 로 가림
# ─────────────────────────────────────────────────────────────────────────────
import os as _os
import sqlite3 as _sqlite3

_KIT_ROOT = Path(__file__).resolve().parents[3]
TRACE_SCHEMA = """CREATE TABLE IF NOT EXISTS trace_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, trace_id TEXT NOT NULL, ts REAL NOT NULL, kind TEXT NOT NULL,
  step TEXT, status TEXT, attempt INTEGER, duration_ms REAL, error TEXT, evidence TEXT, detail TEXT);
CREATE INDEX IF NOT EXISTS ix_trace_events_tid ON trace_events(trace_id, ts);"""
_STATUSES = {"start", "success", "fail", "retry", "fallback", "reuse", "blocked", "partial", "unknown", "info"}


def _root() -> Path:
    return Path(_os.environ.get("CLAUDE_PROJECT_DIR") or _KIT_ROOT)


def _mask(text):
    if text is None:
        return None
    try:
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("_trace_redact", str(Path(__file__).with_name("redact.py")))
        m = ilu.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m.mask(str(text))
    except Exception:  # noqa: BLE001 — 가림 실패 = 원문 대신 버림 (원문 저장 금지)
        return "[가림 실패로 생략]"


def set_current(trace_id: str, rid: str = "", desc: str = "") -> None:
    try:
        p = _root() / ".claude" / "state" / "current-trace.json"
        p.write_text(json.dumps({"trace_id": trace_id, "rid": rid, "desc": _mask(desc or "")[:160],
                                 "started_at": time.time()}, ensure_ascii=False), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def get_current() -> Optional[Dict[str, Any]]:
    try:
        d = json.loads((_root() / ".claude" / "state" / "current-trace.json").read_text(encoding="utf-8"))
        return d if d.get("trace_id") else None
    except Exception:  # noqa: BLE001
        return None


def _db_has_table(db: Path) -> bool:
    if not db.is_file():
        return False
    try:
        c = _sqlite3.connect(str(db), timeout=1)
        try:
            return bool(c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='trace_events'").fetchone())
        finally:
            c.close()
    except Exception:  # noqa: BLE001
        return False


def emit(kind: str, step: str = "", status: str = "info", trace_id: Optional[str] = None, attempt: Optional[int] = None,
         duration_ms: Optional[float] = None, error: Optional[str] = None, evidence: Optional[str] = None,
         detail: Any = None) -> str:
    """이벤트 1건 기록 · 돌려주는 값 = 'db' | 'jsonl' | 'none' (기록 실패해도 예외 X).
    추적번호가 없으면 현재 요청(current-trace.json) · 그것도 없으면 'none' (꾸며 넣지 않음)."""
    tid = trace_id or (get_current() or {}).get("trace_id")
    if not tid:
        return "none"
    st = status if status in _STATUSES else "unknown"
    row = {"trace_id": tid, "ts": time.time(), "kind": kind, "step": _mask(step)[:200] if step else None, "status": st,
           "attempt": attempt, "duration_ms": round(duration_ms, 1) if isinstance(duration_ms, (int, float)) else None,
           "error": _mask(error)[:1000] if error else None, "evidence": _mask(evidence)[:300] if evidence else None,
           "detail": _mask(json.dumps(detail, ensure_ascii=False, default=str))[:2000] if detail is not None else None}
    db = _root() / ".claude" / "state" / "orca.db"
    if _db_has_table(db):
        try:
            c = _sqlite3.connect(str(db), timeout=2)
            try:
                c.execute("INSERT INTO trace_events(trace_id,ts,kind,step,status,attempt,duration_ms,error,evidence,detail)"
                          " VALUES(:trace_id,:ts,:kind,:step,:status,:attempt,:duration_ms,:error,:evidence,:detail)", row)
                c.commit()
                return "db"
            finally:
                c.close()
        except Exception:  # noqa: BLE001 — DB 잠김·손상 → 파일로 (유실 방지)
            pass
    try:
        p = _root() / ".claude" / "logs" / "trace-events.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return "jsonl"
    except Exception:  # noqa: BLE001
        return "none"


def _resolve(ref: str) -> str:
    """R 번호 → 같은 세션 Ledger 의 event_id (없으면 ref 그대로)."""
    if not ref.upper().startswith("R"):
        return ref
    try:
        data = json.loads((_root() / ".claude" / "state" / "request-ledger.json").read_text(encoding="utf-8"))
        for r in data.get("requests", []):
            if r.get("id") == ref.upper() and r.get("event_id"):
                return r["event_id"]
    except Exception:  # noqa: BLE001
        pass
    return ref


def events(ref: str) -> list:
    tid = _resolve(ref)
    out = []
    db = _root() / ".claude" / "state" / "orca.db"
    if _db_has_table(db):
        try:
            c = _sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=2)
            c.row_factory = _sqlite3.Row
            out += [dict(r) for r in c.execute("SELECT * FROM trace_events WHERE trace_id=? ORDER BY ts", (tid,))]
            c.close()
        except Exception:  # noqa: BLE001
            pass
    p = _root() / ".claude" / "logs" / "trace-events.jsonl"
    if p.is_file():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("trace_id") == tid:
                out.append(r)
    return sorted(out, key=lambda r: r.get("ts") or 0)


def chains(evs: list) -> list:
    """같은 단계에서 실패 뒤 성공 = '실패 → 대체 → 성공' 연결 (기록에서 계산 · 없는 연결은 만들지 않음)."""
    res, open_fail = [], {}
    for e in evs:
        key = (e.get("kind"), e.get("step"))
        if e.get("status") == "fail":
            open_fail.setdefault(key, []).append(e)
        elif e.get("status") in ("success", "fallback") and open_fail.get(key):
            res.append({"step": e.get("step"), "kind": e.get("kind"), "failures": open_fail.pop(key), "success": e})
    for key, fs in open_fail.items():
        res.append({"step": key[1], "kind": key[0], "failures": fs, "success": None})
    return res


def _fmt(e: dict) -> str:
    t = datetime.fromtimestamp(e.get("ts") or 0).strftime("%H:%M:%S")
    ms = f" {e['duration_ms']:.0f}ms" if isinstance(e.get("duration_ms"), (int, float)) else ""
    err = f" · 오류: {e['error'][:120]}" if e.get("error") else ""
    ev = f" · 근거: {e['evidence']}" if e.get("evidence") else ""
    return f"{t} [{e.get('kind')}] {e.get('step') or ''} → {e.get('status')}{ms}{err}{ev}"


def _cli(argv: list) -> int:
    import sys as _sys
    cmd = argv[0] if argv else "show"
    if cmd == "init-db":   # 표 만들기 — 운영 orca.db 에는 승인 후에만 (격리 사본·시험은 경로 지정)
        db = Path(argv[1]) if len(argv) > 1 else _root() / ".claude" / "state" / "orca.db"
        c = _sqlite3.connect(str(db))
        c.executescript(TRACE_SCHEMA)
        c.close()
        print(f"trace_events 준비: {db}")
        return 0
    if cmd == "emit":
        a = json.loads(argv[1]) if len(argv) > 1 else {}
        print(emit(**a))
        return 0
    if cmd == "hook-failure":   # PostToolUseFailure 훅 입력(stdin) → 실패 시도 기록
        try:
            p = json.loads(_sys.stdin.read() or "{}")
        except ValueError:
            p = {}
        ti = p.get("tool_input") or {}
        brief = ti.get("command") or ti.get("file_path") or ""
        emit("tool", step=p.get("tool_name") or "tool", status="fail", error=str(p.get("error") or p.get("tool_response") or "")[:1000],
             detail={"input": str(brief)[:300]}, evidence="transcript:" + str(p.get("tool_use_id") or ""))
        return 0
    if cmd == "current":
        print(json.dumps(get_current(), ensure_ascii=False))
        return 0
    if cmd == "show":
        ref = argv[1] if len(argv) > 1 else (get_current() or {}).get("trace_id", "")
        if not ref:
            print("추적번호 없음 (current-trace.json 비어 있음)")
            return 1
        evs = events(ref)
        print(f"== 추적 {ref} → {_resolve(ref)} · 이벤트 {len(evs)}건")
        for e in evs:
            print("  " + _fmt(e))
        for ch in chains(evs):
            fails = " / ".join((f.get("error") or "오류 기록 없음")[:60] for f in ch["failures"])
            ok = _fmt(ch["success"]) if ch["success"] else "성공 기록 없음 (UNKNOWN)"
            print(f"  ⤷ 실패 {len(ch['failures'])}회 [{ch['kind']}:{ch['step']}] ({fails}) → {ok}")
        return 0
    if cmd == "demo":
        return _demo()
    print("사용: trace.py show [추적번호|R번호] | current | init-db [db] | emit '{json}' | hook-failure < stdin")
    return 64


def _demo():
    tracer = Tracer(__name__)
    tracer.logger.info("Tracer initialized", trace_id=tracer.trace_id)

    # Test span operations
    with tracer.span("test_operation_1", component="demo") as span_id:
        time.sleep(0.1)
        tracer.set_span_attribute(span_id, "status", "in_progress")

    # Manual span
    sid = tracer.span_start("test_operation_2", retry_count=0)
    time.sleep(0.05)
    tracer.set_span_attribute(sid, "result", "success")
    tracer.span_end(sid)

    # Export
    print("\n=== Trace Summary ===")
    print(f"Trace ID: {tracer.trace_id}")
    print(f"Total spans: {len(tracer.spans)}")
    for span in tracer.spans.values():
        print(f"  - {span.name} ({span.duration_ms:.1f}ms) [{span.status}]")

    tracer.save_spans()
    print("\n[OK] Traces saved to: .claude/logs/")


    return 0


if __name__ == "__main__":
    import sys as _s
    raise SystemExit(_cli(_s.argv[1:]))
