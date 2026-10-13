#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""?몄뀡 ?대젰 DB ??Claude Code ???湲곕줉(jsonl)??SQLite 濡??곸옱??遺꾩꽍?쒕떎.

??留뚮뱾?덈굹:
  ?몄뀡??"爰쇱??? ?먯씤??異붿쟻???뚮쭏??266MB 吏쒕━ jsonl ???먯쑝濡??ㅼ죱??
  ?몄젣쨌紐?% ?먯꽌쨌臾댁뾿???섎떎 硫덉톬?붿???湲곕줉?????덈뒗??吏덉쓽瑜?紐??덈떎.
  DB ???ｌ쑝硫???以?荑쇰━濡??듭씠 ?섏삩??

臾댁뾿???ｋ굹:
  sessions      ?몄뀡 ??以??붿빟 (湲곌컙쨌?댁닔쨌理쒕? 而⑦뀓?ㅽ듃쨌醫낅즺 異붿젙)
  turns         assistant ?묐떟留덈떎 ?좏겙 ?먯쑀 (而⑦뀓?ㅽ듃 % 異붿씠)
  tool_calls    ?꾧뎄 ?몄텧怨?寃곌낵 (臾댁뾿???섎떎 硫덉톬??
  prompts       ?ъ슜?먭? ?ㅼ젣濡?移?留?  hook_events   ???깃났쨌?ㅽ뙣 (諛⑹뼱 ?μ튂媛 ?뚯븯??
  ingest_state  ?뚯씪蹂??쎌? ?꾩튂 (利앸텇 ?곸옱)

?곕뒗 踰?
  python .claude/scripts/session-history-db.py --ingest      利앸텇 ?곸옱
  python .claude/scripts/session-history-db.py --stats       ?붿빟
  python .claude/scripts/session-history-db.py --crashes     爰쇱쭚 遺꾩꽍
  python .claude/scripts/session-history-db.py --session ID  ?몄뀡 ?곸꽭
  python .claude/scripts/session-history-db.py --sql "..."   ?꾩쓽 荑쇰━
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
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        pass

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
DB_PATH = PROJECT_ROOT / ".claude" / "state" / "sessions.db"
PROJECTS_DIR = Path.home() / ".claude" / "projects"

# 紐⑤뜽 而⑦뀓?ㅽ듃 李? ?몄뀡???쇱뼱遺숈? 吏?먯쓣 % 濡??ш린 ?꾪븳 湲곗?.
CONTEXT_LIMIT = int(os.environ.get("CONTEXT_LIMIT", "1000000"))
# ?꾧뎄 ?낅젰쨌寃곌낵???듭㎏濡??ｌ? ?딅뒗?? DB 媛 ?먮Ц留뚰겮 而ㅼ?硫?吏덉쓽媛 ?먮젮吏꾨떎.
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


# ?섏쨷??遺숈씤 移쇰읆. 湲곗〈 DB ?먮룄 議곗슜??異붽??쒕떎.
# ?쒕툕?먯씠?꾪듃 湲곕줉? 遺紐⑥? 媛숈? sessionId 瑜??곌퀬 agentId 濡쒕쭔 媛덈┛??
# ?욎뼱???몃㈃ 而⑦뀓?ㅽ듃 % 媛 ?ㅼ뿼?섎?濡?移쇰읆?쇰줈 媛덈씪 ?붾떎.
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
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return None


def brief(obj, cap=TEXT_CAP):
    if obj is None:
        return None
    if isinstance(obj, str):
        s = obj
    else:
        try:
            s = json.dumps(obj, ensure_ascii=False)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            s = str(obj)
    return s[:cap]


def full_len(obj):
    if obj is None:
        return 0
    if isinstance(obj, str):
        return len(obj)
    try:
        return len(json.dumps(obj, ensure_ascii=False))
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return len(str(obj))


def ingest_file(conn, path, force=False):
    """??jsonl ?뚯씪??利앸텇 ?곸옱. ?대? ?쎌? 諛붿씠?몃뒗 嫄대꼫?대떎."""
    st = path.stat()
    row = conn.execute("SELECT * FROM ingest_state WHERE file=?", (str(path),)).fetchone()
    offset = 0
    lines_done = 0
    if row and not force:
        # ?뚯씪??洹몃?濡쒕㈃ ?ㅼ떆 ?쎌? ?딅뒗??
        if st.st_size == row["size"] and abs(st.st_mtime - row["mtime"]) < 1:
            return 0
        # 以꾩? ?딆븯?쇰㈃ ?쎈뜕 ?먮━?먯꽌 ?댁뼱 ?쎈뒗??
        if st.st_size >= row["size"]:
            offset = row["offset"]
            lines_done = row["lines"]

    # ?쒕툕?먯씠?꾪듃 湲곕줉? <project>/<?몄뀡id>/subagents/agent-*.jsonl ???덈떎.
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
            except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
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
                # ?ъ슜?먭? 移?留먯씤吏, ?꾧뎄 寃곌낵?몄? 媛瑜몃떎.
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
                # ???꾩쨷 ?ъ슜?먭? ?쇱썙 ?ｌ? 留? ?ъ큺????? 援ш컙??蹂대뒗 ???대떎.
                conn.execute(
                    "INSERT OR REPLACE INTO prompts(uuid,session_id,ts,source,text) VALUES(?,?,?,?,?)",
                    ("q-" + str(sid)[:8] + "-" + str(ts), sid, ts, "queued",
                     brief(r.get("content"), 4000)),
                )

            # ?몄뀡 硫뷀????꾨Т ?덉퐫?쒖뿉?쒕굹 二쇱썙 ?대뒗??
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
    """?몄뀡 ?붿빟???ㅼ떆 怨꾩궛?쒕떎. 醫낅즺 ?ъ쑀??湲곕줉?먯꽌 異붿젙?쒕떎."""
    sids = [r[0] for r in conn.execute("SELECT session_id FROM sessions").fetchall()]
    for sid in sids:
        # ?몄뀡 ?붿빟? 硫붿씤 ?먯씠?꾪듃 ?대쭔 ?쇰떎. ?쒕툕?먯씠?꾪듃????而⑦뀓?ㅽ듃瑜??곕줈 ?대떎.
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
        last_kind = "?꾧뎄?湲? if (last and last["n_tool_use"]) else "湲"

        # 醫낅즺 ?ъ쑀 異붿젙. ?뺤젙???꾨땲???좏샇?????곸꽭??--session ?쇰줈 蹂몃떎.
        if (agg["n"] or 0) == 0:
            reason = "鍮덉꽭??
        elif maxp >= 85:
            reason = "而⑦뀓?ㅽ듃泥쒖옣"
        elif last_kind == "?꾧뎄?湲? and n_dangling > 0:
            reason = "?꾧뎄?묐떟?놁쓬"
        elif maxp >= 70:
            reason = "而⑦뀓?ㅽ듃寃쎄퀬沅?
        else:
            reason = "?뺤긽醫낅즺異붿젙"

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
    # 硫붿씤 ?몄뀡(*/x.jsonl) 怨??쒕툕?먯씠?꾪듃(*/?몄뀡/subagents/agent-*.jsonl) 瑜?紐⑤몢 ?묐뒗??
    files = sorted(PROJECTS_DIR.rglob("*.jsonl"))
    total = 0
    touched = 0
    for p in files:
        try:
            n = ingest_file(conn, p, force=args.force)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            print("  嫄대꼫? " + p.name + ": " + str(e))
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
    print("?곸옱 ?꾨즺 ???뚯씪 %d/%d 媛깆떊, ??以?%d" % (touched, len(files), total))
    print("?몄뀡 %d 쨌 ??%d 쨌 ?꾧뎄?몄텧 %d 쨌 ?꾨＼?꾪듃 %d 쨌 DB %.1fMB" % (ns, nt, nc, npm, size_mb))


def cmd_stats(args):
    conn = connect()
    print("=== ?몄뀡 ?붿빟 (理쒓렐 15) ===")
    print("%-9s %-22s %-17s %6s %5s %6s %6s %s"
          % ("id", "project", "?쒖옉", "遺?, "??, "理쒕?%", "?꾧뎄", "醫낅즺異붿젙"))
    for r in conn.execute(
            "SELECT substr(session_id,1,8) id, project, substr(started_at,1,16) t0,"
            " duration_min dur, n_turns, max_ctx_pct, n_tools, end_reason"
            " FROM sessions WHERE n_turns>0 ORDER BY started_at DESC LIMIT 15"):
        print("%-9s %-22s %-17s %6s %5s %6s %6s %s" % (
            r["id"], (r["project"] or "")[:22], r["t0"] or "",
            r["dur"] if r["dur"] is not None else "-",
            r["n_turns"], r["max_ctx_pct"], r["n_tools"], r["end_reason"]))
    print("")
    print("=== 醫낅즺 ?ъ쑀 遺꾪룷 ===")
    for r in conn.execute(
            "SELECT end_reason, COUNT(*) c FROM sessions WHERE n_turns>0"
            " GROUP BY end_reason ORDER BY c DESC"):
        print("  %-14s %d" % (r["end_reason"], r["c"]))


def cmd_crashes(args):
    conn = connect()
    print("=== 而⑦뀓?ㅽ듃 70% ?댁긽 媛??몄뀡 (?쇱뼱遺숆린 ?ъ슫 援ш컙) ===")
    for r in conn.execute(
            "SELECT substr(session_id,1,8) id, project, substr(ended_at,1,16) t1, n_turns,"
            " max_ctx, max_ctx_pct, last_kind, last_tool, last_gap_min"
            " FROM sessions WHERE max_ctx_pct>=70 ORDER BY max_ctx_pct DESC"):
        print("  %s %-20s %s ??-4d 理쒕? %d (%d%%) ??%s/%s 留덉?留됯컙寃?%s遺? % (
            r["id"], (r["project"] or "")[:20], r["t1"], r["n_turns"], r["max_ctx"],
            r["max_ctx_pct"], r["last_kind"], r["last_tool"] or "-", r["last_gap_min"]))
    print("")
    print("=== ?듭쓣 紐?諛쏆? ?꾧뎄 ?몄텧 (???꾩쨷 硫덉텣 ?먮━) ===")
    for r in conn.execute(
            "SELECT substr(session_id,1,8) id, MAX(ts) ts, tool_name, COUNT(*) c"
            " FROM tool_calls WHERE answered=0"
            " GROUP BY session_id, tool_name ORDER BY ts DESC LIMIT 20"):
        print("  %s %s %-16s x%d" % (r["id"], (r["ts"] or "")[:16], r["tool_name"], r["c"]))
    print("")
    print("=== 而⑦뀓?ㅽ듃 ?蹂?????(?대뵒???꾪뿕?댁??? ===")
    for r in conn.execute(
            "SELECT (ctx_pct/10)*10 band, COUNT(*) n FROM turns WHERE ctx_pct>0"
            " GROUP BY band ORDER BY band"):
        print("  %3d%% ?  %6d ?? %s" % (r["band"], r["n"], "#" * min(50, r["n"] // 40)))


def cmd_session(args):
    conn = connect()
    r = conn.execute("SELECT * FROM sessions WHERE session_id LIKE ?",
                     (args.session + "%",)).fetchone()
    if not r:
        print("洹몃윴 ?몄뀡???놁뒿?덈떎: " + args.session)
        return
    print("?몄뀡 " + r["session_id"] + " (" + str(r["project"]) + ")")
    print("  湲곌컙 %s ~ %s (%s遺?" % (r["started_at"], r["ended_at"], r["duration_min"]))
    print("  ??%d 쨌 ?꾨＼?꾪듃 %d 쨌 ?꾧뎄 %d (?ㅽ뙣 %d)"
          % (r["n_turns"], r["n_prompts"], r["n_tools"], r["n_tool_err"]))
    print("  而⑦뀓?ㅽ듃 理쒕? %d (%d%%) 쨌 留덉?留?%d" % (r["max_ctx"], r["max_ctx_pct"], r["last_ctx"]))
    print("  醫낅즺 異붿젙: %s (留덉?留?%s/%s, 吏곸쟾 媛꾧꺽 %s遺?"
          % (r["end_reason"], r["last_kind"], r["last_tool"], r["last_gap_min"]))
    print("")
    print("  --- 留덉?留??꾧뎄 ?몄텧 10嫄?---")
    for t in conn.execute(
            "SELECT ts, tool_name, answered, is_error, substr(input_brief,1,80) inp"
            " FROM tool_calls WHERE session_id=? ORDER BY ts DESC LIMIT 10", (r["session_id"],)):
        mark = "?뺤긽" if t["answered"] else "臾댁쓳??
        if t["is_error"]:
            mark = "?ㅽ뙣"
        print("   %s %-6s %-16s %s" % ((t["ts"] or "")[:19], mark, t["tool_name"],
                                       (t["inp"] or "").replace("\n", " ")))
    print("")
    print("  --- 而⑦뀓?ㅽ듃 異붿씠 (??12?? ---")
    for t in conn.execute(
            "SELECT ts, ctx_total, ctx_pct, output_tokens FROM turns"
            " WHERE session_id=? ORDER BY ts DESC LIMIT 12", (r["session_id"],)):
        print("   %s  %8d (%2d%%)  異쒕젰 %d"
              % ((t["ts"] or "")[:19], t["ctx_total"], t["ctx_pct"], t["output_tokens"]))


def cmd_sql(args):
    conn = connect()
    try:
        rows = conn.execute(args.sql).fetchall()
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        print("荑쇰━ ?ㅽ뙣: " + str(e))
        return
    if not rows:
        print("(寃곌낵 ?놁쓬)")
        return
    cols = rows[0].keys()
    print(" | ".join(cols))
    for r in rows[:args.limit]:
        print(" | ".join("" if r[c] is None else str(r[c])[:60] for c in cols))
    if len(rows) > args.limit:
        print("... 珥?%d?? % len(rows))


def main():
    ap = argparse.ArgumentParser(description="Claude ?몄뀡 ?대젰 DB")
    ap.add_argument("--ingest", action="store_true", help="jsonl ??DB 濡?利앸텇 ?곸옱")
    ap.add_argument("--force", action="store_true", help="泥섏쓬遺???ㅼ떆 ?곸옱")
    ap.add_argument("--stats", action="store_true", help="?몄뀡 ?붿빟")
    ap.add_argument("--crashes", action="store_true", help="爰쇱쭚 遺꾩꽍")
    ap.add_argument("--session", help="?몄뀡 ?곸꽭 (??8?먮━濡쒕룄 ??")
    ap.add_argument("--sql", help="?꾩쓽 SELECT")
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

