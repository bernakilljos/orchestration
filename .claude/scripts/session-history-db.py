#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""세션 이력 DB — Claude Code 대화 기록(jsonl)을 SQLite 로 적재해 분석한다.

왜 만들었나:
  세션이 "꺼지는" 원인을 추적할 때마다 266MB 짜리 jsonl 을 손으로 뒤졌다.
  언제·몇 % 에서·무엇을 하다 멈췄는지는 기록에 다 있는데 질의를 못 했다.
  DB 에 넣으면 한 줄 쿼리로 답이 나온다.

무엇을 넣나:
  sessions      세션 한 줄 요약 (기간·턴수·최대 컨텍스트·종료 추정)
  turns         assistant 응답마다 토큰 점유 (컨텍스트 % 추이)
  tool_calls    도구 호출과 결과 (무엇을 하다 멈췄나)
  prompts       사용자가 실제로 친 말
  hook_events   훅 성공·실패 (방어 장치가 돌았나)
  ingest_state  파일별 읽은 위치 (증분 적재)

쓰는 법:
  python .claude/scripts/session-history-db.py --ingest      증분 적재
  python .claude/scripts/session-history-db.py --stats       요약
  python .claude/scripts/session-history-db.py --crashes     꺼짐 분석
  python .claude/scripts/session-history-db.py --session ID  세션 상세
  python .claude/scripts/session-history-db.py --sql "..."   임의 쿼리
"""
import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
DB_PATH = PROJECT_ROOT / ".claude" / "state" / "sessions.db"
PROJECTS_DIR = Path.home() / ".claude" / "projects"

# 모델 컨텍스트 창. 세션이 얼어붙은 지점을 % 로 재기 위한 기준.
CONTEXT_LIMIT = int(os.environ.get("CONTEXT_LIMIT", "1000000"))
# 도구 입력·결과는 통째로 넣지 않는다. DB 가 원문만큼 커지면 질의가 느려진다.
TEXT_CAP = 2000

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  session_id   TEXT PRIMARY KEY,
  project      TEXT,
  cwd          TEXT,
  git_branch   TEXT,
  cli_version  TEXT,
  started_at   TEXT,
  ended_at     TEXT,
  duration_min REAL,
  n_turns      INTEGER DEFAULT 0,
  n_prompts    INTEGER DEFAULT 0,
  n_tools      INTEGER DEFAULT 0,
  n_tool_err   INTEGER DEFAULT 0,
  max_ctx      INTEGER DEFAULT 0,
  max_ctx_pct  INTEGER DEFAULT 0,
  last_ctx     INTEGER DEFAULT 0,
  out_tokens   INTEGER DEFAULT 0,
  models       TEXT,
  last_gap_min REAL,
  last_kind    TEXT,
  last_tool    TEXT,
  end_reason   TEXT,
  file         TEXT,
  file_size    INTEGER,
  updated_at   TEXT
);
CREATE TABLE IF NOT EXISTS turns (
  uuid         TEXT PRIMARY KEY,
  session_id   TEXT,
  ts           TEXT,
  model        TEXT,
  effort       TEXT,
  request_id   TEXT,
  input_tokens INTEGER DEFAULT 0,
  cache_read   INTEGER DEFAULT 0,
  cache_create INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  thinking     INTEGER DEFAULT 0,
  ctx_total    INTEGER DEFAULT 0,
  ctx_pct      INTEGER DEFAULT 0,
  n_tool_use   INTEGER DEFAULT 0,
  text_len     INTEGER DEFAULT 0,
  stop_reason  TEXT
);
CREATE TABLE IF NOT EXISTS tool_calls (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id   TEXT,
  turn_uuid    TEXT,
  tool_use_id  TEXT UNIQUE,
  ts           TEXT,
  tool_name    TEXT,
  input_brief  TEXT,
  is_error     INTEGER DEFAULT 0,
  result_len   INTEGER DEFAULT 0,
  answered     INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS prompts (
  uuid         TEXT PRIMARY KEY,
  session_id   TEXT,
  ts           TEXT,
  source       TEXT,
  text         TEXT
);
CREATE TABLE IF NOT EXISTS hook_events (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id   TEXT,
  ts           TEXT,
  hook_name    TEXT,
  status       TEXT
);
CREATE TABLE IF NOT EXISTS ingest_state (
  file         TEXT PRIMARY KEY,
  size         INTEGER,
  mtime        REAL,
  offset       INTEGER,
  lines        INTEGER,
  ingested_at  TEXT
);
CREATE INDEX IF NOT EXISTS ix_turns_sess   ON turns(session_id, ts);
CREATE INDEX IF NOT EXISTS ix_turns_pct    ON turns(ctx_pct);
CREATE INDEX IF NOT EXISTS ix_tools_sess   ON tool_calls(session_id, ts);
CREATE INDEX IF NOT EXISTS ix_tools_name   ON tool_calls(tool_name);
CREATE INDEX IF NOT EXISTS ix_prompts_sess ON prompts(session_id, ts);
CREATE INDEX IF NOT EXISTS ix_hooks_sess   ON hook_events(session_id, ts);
"""


# 나중에 붙인 칼럼. 기존 DB 에도 조용히 추가된다.
# 서브에이전트 기록은 부모와 같은 sessionId 를 쓰고 agentId 로만 갈린다.
# 섞어서 세면 컨텍스트 % 가 오염되므로 칼럼으로 갈라 둔다.
LATER_COLUMNS = [
    ("turns", "agent_id", "TEXT"),
    ("tool_calls", "agent_id", "TEXT"),
    ("prompts", "agent_id", "TEXT"),
    ("sessions", "n_sub_turns", "INTEGER DEFAULT 0"),
    ("sessions", "n_sub_agents", "INTEGER DEFAULT 0"),
    ("sessions", "sub_out_tokens", "INTEGER DEFAULT 0"),
]


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    for table, col, typ in LATER_COLUMNS:
        have = [r[1] for r in conn.execute("PRAGMA table_info(%s)" % table)]
        if col not in have:
            conn.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, col, typ))
    conn.commit()
    return conn


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def brief(obj, cap=TEXT_CAP):
    if obj is None:
        return None
    if isinstance(obj, str):
        s = obj
    else:
        try:
            s = json.dumps(obj, ensure_ascii=False)
        except Exception:
            s = str(obj)
    return s[:cap]


def full_len(obj):
    if obj is None:
        return 0
    if isinstance(obj, str):
        return len(obj)
    try:
        return len(json.dumps(obj, ensure_ascii=False))
    except Exception:
        return len(str(obj))


def ingest_file(conn, path, force=False):
    """한 jsonl 파일을 증분 적재. 이미 읽은 바이트는 건너뛴다."""
    st = path.stat()
    row = conn.execute("SELECT * FROM ingest_state WHERE file=?", (str(path),)).fetchone()
    offset = 0
    lines_done = 0
    if row and not force:
        # 파일이 그대로면 다시 읽지 않는다.
        if st.st_size == row["size"] and abs(st.st_mtime - row["mtime"]) < 1:
            return 0
        # 줄지 않았으면 읽던 자리에서 이어 읽는다.
        if st.st_size >= row["size"]:
            offset = row["offset"]
            lines_done = row["lines"]

    # 서브에이전트 기록은 <project>/<세션id>/subagents/agent-*.jsonl 에 있다.
    if path.parent.name == "subagents":
        project = path.parents[2].name
    else:
        project = path.parent.name
    n_new = 0

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        f.seek(offset)
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            lines_done += 1
            try:
                r = json.loads(raw)
            except Exception:
                continue
            n_new += 1
            t = r.get("type")
            sid = r.get("sessionId") or r.get("session_id")
            if not sid:
                continue
            ts = r.get("timestamp")
            aid = r.get("agentId")

            if t == "assistant":
                m = r.get("message") or {}
                u = m.get("usage") or {}
                inp = u.get("input_tokens") or 0
                cr = u.get("cache_read_input_tokens") or 0
                cc = u.get("cache_creation_input_tokens") or 0
                out = u.get("output_tokens") or 0
                think = (u.get("output_tokens_details") or {}).get("thinking_tokens") or 0
                ctx = inp + cr + cc
                pct = int(ctx * 100 / CONTEXT_LIMIT) if CONTEXT_LIMIT else 0
                blocks = m.get("content") or []
                n_tu = 0
                tlen = 0
                if isinstance(blocks, list):
                    for b in blocks:
                        if not isinstance(b, dict):
                            continue
                        if b.get("type") == "tool_use":
                            n_tu += 1
                            conn.execute(
                                "INSERT INTO tool_calls"
                                "(session_id,turn_uuid,tool_use_id,ts,tool_name,input_brief,agent_id)"
                                " VALUES(?,?,?,?,?,?,?)"
                                " ON CONFLICT(tool_use_id) DO UPDATE SET"
                                " tool_name=excluded.tool_name, ts=excluded.ts",
                                (sid, r.get("uuid"), b.get("id"), ts, b.get("name"),
                                 brief(b.get("input")), aid),
                            )
                        elif b.get("type") == "text":
                            tlen += len(b.get("text") or "")
                conn.execute(
                    "INSERT OR REPLACE INTO turns"
                    "(uuid,session_id,ts,model,effort,request_id,input_tokens,cache_read,"
                    "cache_create,output_tokens,thinking,ctx_total,ctx_pct,n_tool_use,text_len,"
                    "stop_reason,agent_id)"
                    " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (r.get("uuid"), sid, ts, m.get("model"), r.get("effort"), r.get("requestId"),
                     inp, cr, cc, out, think, ctx, pct, n_tu, tlen, m.get("stop_reason"), aid),
                )

            elif t == "user":
                m = r.get("message") or {}
                c = m.get("content")
                # 사용자가 친 말인지, 도구 결과인지 가른다.
                is_tool_result = False
                if isinstance(c, list):
                    for b in c:
                        if isinstance(b, dict) and b.get("type") == "tool_result":
                            is_tool_result = True
                            conn.execute(
                                "UPDATE tool_calls SET is_error=?, result_len=?, answered=1"
                                " WHERE tool_use_id=?",
                                (1 if b.get("is_error") else 0,
                                 full_len(b.get("content")), b.get("tool_use_id")),
                            )
                if not is_tool_result:
                    origin = r.get("origin") or {}
                    if origin.get("kind") == "human" or r.get("promptSource"):
                        conn.execute(
                            "INSERT OR REPLACE INTO prompts(uuid,session_id,ts,source,text,agent_id)"
                            " VALUES(?,?,?,?,?,?)",
                            (r.get("uuid"), sid, ts, r.get("promptSource"), brief(c, 4000), aid),
                        )

            elif t == "attachment":
                a = r.get("attachment") or {}
                if isinstance(a, dict) and str(a.get("type", "")).startswith("hook_"):
                    conn.execute(
                        "INSERT INTO hook_events(session_id,ts,hook_name,status) VALUES(?,?,?,?)",
                        (sid, ts, a.get("hookName"), a.get("type")),
                    )

            elif t == "queue-operation":
                # 턴 도중 사용자가 끼워 넣은 말. 재촉이 잦은 구간을 보는 데 쓴다.
                conn.execute(
                    "INSERT OR REPLACE INTO prompts(uuid,session_id,ts,source,text) VALUES(?,?,?,?,?)",
                    ("q-" + str(sid)[:8] + "-" + str(ts), sid, ts, "queued",
                     brief(r.get("content"), 4000)),
                )

            # 세션 메타는 아무 레코드에서나 주워 담는다.
            if r.get("cwd"):
                conn.execute(
                    "INSERT INTO sessions(session_id,project,cwd,git_branch,cli_version,file,file_size)"
                    " VALUES(?,?,?,?,?,?,?)"
                    " ON CONFLICT(session_id) DO UPDATE SET cwd=excluded.cwd,"
                    " git_branch=excluded.git_branch, cli_version=excluded.cli_version,"
                    " file=excluded.file, file_size=excluded.file_size",
                    (sid, project, r.get("cwd"), r.get("gitBranch"), r.get("version"),
                     str(path), st.st_size),
                )
            else:
                conn.execute(
                    "INSERT OR IGNORE INTO sessions(session_id,project,file,file_size) VALUES(?,?,?,?)",
                    (sid, project, str(path), st.st_size),
                )

        end_offset = f.tell()

    conn.execute(
        "INSERT INTO ingest_state(file,size,mtime,offset,lines,ingested_at) VALUES(?,?,?,?,?,?)"
        " ON CONFLICT(file) DO UPDATE SET size=excluded.size, mtime=excluded.mtime,"
        " offset=excluded.offset, lines=excluded.lines, ingested_at=excluded.ingested_at",
        (str(path), st.st_size, st.st_mtime, end_offset, lines_done,
         datetime.now(timezone.utc).isoformat(timespec="seconds")),
    )
    conn.commit()
    return n_new


def rollup(conn):
    """세션 요약을 다시 계산한다. 종료 사유는 기록에서 추정한다."""
    sids = [r[0] for r in conn.execute("SELECT session_id FROM sessions").fetchall()]
    for sid in sids:
        # 세션 요약은 메인 에이전트 턴만 센다. 서브에이전트는 제 컨텍스트를 따로 쓴다.
        agg = conn.execute(
            "SELECT COUNT(*) n, MAX(ctx_total) mx, MAX(ctx_pct) mxp, SUM(output_tokens) out,"
            " MIN(ts) t0, MAX(ts) t1, GROUP_CONCAT(DISTINCT model) models"
            " FROM turns WHERE session_id=? AND agent_id IS NULL", (sid,)).fetchone()
        sub = conn.execute(
            "SELECT COUNT(*) n, COUNT(DISTINCT agent_id) na, SUM(output_tokens) out"
            " FROM turns WHERE session_id=? AND agent_id IS NOT NULL", (sid,)).fetchone()
        npr = conn.execute(
            "SELECT COUNT(*) FROM prompts WHERE session_id=? AND agent_id IS NULL",
            (sid,)).fetchone()[0]
        ntl, nerr = conn.execute(
            "SELECT COUNT(*), SUM(is_error) FROM tool_calls WHERE session_id=? AND agent_id IS NULL",
            (sid,)).fetchone()
        last = conn.execute(
            "SELECT ts, ctx_total, ctx_pct, n_tool_use FROM turns"
            " WHERE session_id=? AND agent_id IS NULL ORDER BY ts DESC LIMIT 1", (sid,)).fetchone()
        prev = conn.execute(
            "SELECT ts FROM turns WHERE session_id=? AND agent_id IS NULL"
            " ORDER BY ts DESC LIMIT 1 OFFSET 1", (sid,)).fetchone()

        t0, t1 = parse_ts(agg["t0"]), parse_ts(agg["t1"])
        dur = round((t1 - t0).total_seconds() / 60, 1) if t0 and t1 else None
        gap = None
        if last and prev:
            a, b = parse_ts(last["ts"]), parse_ts(prev["ts"])
            if a and b:
                gap = round((a - b).total_seconds() / 60, 1)

        n_dangling = conn.execute(
            "SELECT COUNT(*) FROM tool_calls WHERE session_id=? AND agent_id IS NULL AND answered=0",
            (sid,)).fetchone()[0]
        last_tool = conn.execute(
            "SELECT tool_name FROM tool_calls WHERE session_id=? AND agent_id IS NULL"
            " ORDER BY ts DESC LIMIT 1", (sid,)).fetchone()

        maxp = agg["mxp"] or 0
        last_kind = "도구대기" if (last and last["n_tool_use"]) else "글"

        # 종료 사유 추정. 확정이 아니라 신호다 — 상세는 --session 으로 본다.
        if (agg["n"] or 0) == 0:
            reason = "빈세션"
        elif maxp >= 85:
            reason = "컨텍스트천장"
        elif last_kind == "도구대기" and n_dangling > 0:
            reason = "도구응답없음"
        elif maxp >= 70:
            reason = "컨텍스트경고권"
        else:
            reason = "정상종료추정"

        conn.execute(
            "UPDATE sessions SET started_at=?, ended_at=?, duration_min=?, n_turns=?, n_prompts=?,"
            " n_tools=?, n_tool_err=?, max_ctx=?, max_ctx_pct=?, last_ctx=?, out_tokens=?,"
            " models=?, last_gap_min=?, last_kind=?, last_tool=?, end_reason=?, updated_at=?,"
            " n_sub_turns=?, n_sub_agents=?, sub_out_tokens=?"
            " WHERE session_id=?",
            (agg["t0"], agg["t1"], dur, agg["n"] or 0, npr, ntl or 0, nerr or 0,
             agg["mx"] or 0, maxp, (last["ctx_total"] if last else 0), agg["out"] or 0,
             agg["models"], gap, last_kind,
             (last_tool["tool_name"] if last_tool else None), reason,
             datetime.now(timezone.utc).isoformat(timespec="seconds"),
             sub["n"] or 0, sub["na"] or 0, sub["out"] or 0, sid),
        )
    conn.commit()


def cmd_ingest(args):
    conn = connect()
    # 메인 세션(*/x.jsonl) 과 서브에이전트(*/세션/subagents/agent-*.jsonl) 를 모두 훑는다.
    files = sorted(PROJECTS_DIR.rglob("*.jsonl"))
    total = 0
    touched = 0
    for p in files:
        try:
            n = ingest_file(conn, p, force=args.force)
        except Exception as e:
            print("  건너뜀 " + p.name + ": " + str(e))
            continue
        if n:
            touched += 1
            total += n
    rollup(conn)
    size_mb = DB_PATH.stat().st_size / 1024 / 1024
    ns = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    nt = conn.execute("SELECT COUNT(*) FROM turns").fetchone()[0]
    nc = conn.execute("SELECT COUNT(*) FROM tool_calls").fetchone()[0]
    npm = conn.execute("SELECT COUNT(*) FROM prompts").fetchone()[0]
    print("적재 완료 — 파일 %d/%d 갱신, 새 줄 %d" % (touched, len(files), total))
    print("세션 %d · 턴 %d · 도구호출 %d · 프롬프트 %d · DB %.1fMB" % (ns, nt, nc, npm, size_mb))


def cmd_stats(args):
    conn = connect()
    print("=== 세션 요약 (최근 15) ===")
    print("%-9s %-22s %-17s %6s %5s %6s %6s %s"
          % ("id", "project", "시작", "분", "턴", "최대%", "도구", "종료추정"))
    for r in conn.execute(
            "SELECT substr(session_id,1,8) id, project, substr(started_at,1,16) t0,"
            " duration_min dur, n_turns, max_ctx_pct, n_tools, end_reason"
            " FROM sessions WHERE n_turns>0 ORDER BY started_at DESC LIMIT 15"):
        print("%-9s %-22s %-17s %6s %5s %6s %6s %s" % (
            r["id"], (r["project"] or "")[:22], r["t0"] or "",
            r["dur"] if r["dur"] is not None else "-",
            r["n_turns"], r["max_ctx_pct"], r["n_tools"], r["end_reason"]))
    print("")
    print("=== 종료 사유 분포 ===")
    for r in conn.execute(
            "SELECT end_reason, COUNT(*) c FROM sessions WHERE n_turns>0"
            " GROUP BY end_reason ORDER BY c DESC"):
        print("  %-14s %d" % (r["end_reason"], r["c"]))


def cmd_crashes(args):
    conn = connect()
    print("=== 컨텍스트 70% 이상 간 세션 (얼어붙기 쉬운 구간) ===")
    for r in conn.execute(
            "SELECT substr(session_id,1,8) id, project, substr(ended_at,1,16) t1, n_turns,"
            " max_ctx, max_ctx_pct, last_kind, last_tool, last_gap_min"
            " FROM sessions WHERE max_ctx_pct>=70 ORDER BY max_ctx_pct DESC"):
        print("  %s %-20s %s 턴%-4d 최대 %d (%d%%) 끝=%s/%s 마지막간격 %s분" % (
            r["id"], (r["project"] or "")[:20], r["t1"], r["n_turns"], r["max_ctx"],
            r["max_ctx_pct"], r["last_kind"], r["last_tool"] or "-", r["last_gap_min"]))
    print("")
    print("=== 답을 못 받은 도구 호출 (턴 도중 멈춘 자리) ===")
    for r in conn.execute(
            "SELECT substr(session_id,1,8) id, MAX(ts) ts, tool_name, COUNT(*) c"
            " FROM tool_calls WHERE answered=0"
            " GROUP BY session_id, tool_name ORDER BY ts DESC LIMIT 20"):
        print("  %s %s %-16s x%d" % (r["id"], (r["ts"] or "")[:16], r["tool_name"], r["c"]))
    print("")
    print("=== 컨텍스트 대별 턴 수 (어디서 위험해지나) ===")
    for r in conn.execute(
            "SELECT (ctx_pct/10)*10 band, COUNT(*) n FROM turns WHERE ctx_pct>0"
            " GROUP BY band ORDER BY band"):
        print("  %3d%% 대  %6d 턴  %s" % (r["band"], r["n"], "#" * min(50, r["n"] // 40)))


def cmd_session(args):
    conn = connect()
    r = conn.execute("SELECT * FROM sessions WHERE session_id LIKE ?",
                     (args.session + "%",)).fetchone()
    if not r:
        print("그런 세션이 없습니다: " + args.session)
        return
    print("세션 " + r["session_id"] + " (" + str(r["project"]) + ")")
    print("  기간 %s ~ %s (%s분)" % (r["started_at"], r["ended_at"], r["duration_min"]))
    print("  턴 %d · 프롬프트 %d · 도구 %d (실패 %d)"
          % (r["n_turns"], r["n_prompts"], r["n_tools"], r["n_tool_err"]))
    print("  컨텍스트 최대 %d (%d%%) · 마지막 %d" % (r["max_ctx"], r["max_ctx_pct"], r["last_ctx"]))
    print("  종료 추정: %s (마지막=%s/%s, 직전 간격 %s분)"
          % (r["end_reason"], r["last_kind"], r["last_tool"], r["last_gap_min"]))
    print("")
    print("  --- 마지막 도구 호출 10건 ---")
    for t in conn.execute(
            "SELECT ts, tool_name, answered, is_error, substr(input_brief,1,80) inp"
            " FROM tool_calls WHERE session_id=? ORDER BY ts DESC LIMIT 10", (r["session_id"],)):
        mark = "정상" if t["answered"] else "무응답"
        if t["is_error"]:
            mark = "실패"
        print("   %s %-6s %-16s %s" % ((t["ts"] or "")[:19], mark, t["tool_name"],
                                       (t["inp"] or "").replace("\n", " ")))
    print("")
    print("  --- 컨텍스트 추이 (끝 12턴) ---")
    for t in conn.execute(
            "SELECT ts, ctx_total, ctx_pct, output_tokens FROM turns"
            " WHERE session_id=? ORDER BY ts DESC LIMIT 12", (r["session_id"],)):
        print("   %s  %8d (%2d%%)  출력 %d"
              % ((t["ts"] or "")[:19], t["ctx_total"], t["ctx_pct"], t["output_tokens"]))


def cmd_sql(args):
    conn = connect()
    try:
        rows = conn.execute(args.sql).fetchall()
    except Exception as e:
        print("쿼리 실패: " + str(e))
        return
    if not rows:
        print("(결과 없음)")
        return
    cols = rows[0].keys()
    print(" | ".join(cols))
    for r in rows[:args.limit]:
        print(" | ".join("" if r[c] is None else str(r[c])[:60] for c in cols))
    if len(rows) > args.limit:
        print("... 총 %d행" % len(rows))


def main():
    ap = argparse.ArgumentParser(description="Claude 세션 이력 DB")
    ap.add_argument("--ingest", action="store_true", help="jsonl 을 DB 로 증분 적재")
    ap.add_argument("--force", action="store_true", help="처음부터 다시 적재")
    ap.add_argument("--stats", action="store_true", help="세션 요약")
    ap.add_argument("--crashes", action="store_true", help="꺼짐 분석")
    ap.add_argument("--session", help="세션 상세 (앞 8자리로도 됨)")
    ap.add_argument("--sql", help="임의 SELECT")
    ap.add_argument("--limit", type=int, default=40)
    a = ap.parse_args()

    if a.ingest:
        cmd_ingest(a)
    elif a.crashes:
        cmd_crashes(a)
    elif a.session:
        cmd_session(a)
    elif a.sql:
        cmd_sql(a)
    elif a.stats:
        cmd_stats(a)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
