"""
save_solution ???몄뀡 醫낅즺 ??臾몄젣-?닿껐-?뚯씪-紐낅졊 ?먮룞 罹≪쿂 -> orca.db.problem_solutions
洹쇨굅: 2026-09-02 ?ъ슜??吏????"?쎄린(?먮룞 議고쉶) + ?곌린(泥섎━ 寃곌낵 湲곕줉) ?묐갑??- 珥덉턀怨?
?몄텧: Stop / SessionEnd hook + ?섎룞 CLI
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / ".claude" / "state" / "orca.db"


def _sid() -> str:
    return os.environ.get("CLAUDE_CODE_SESSION_ID", "unknown")


def _extract_category(text: str) -> str:
    """臾몄젣-?닿껐?먯꽌 移댄뀒怨좊━ ?먮룞 異붿텧."""
    text_l = text.lower()
    for cat, kws in [
        ("db", ["sql", "sqlite", "database", "?뚯씠釉?, "orca.db", "migration"]),
        ("hook", ["hook", "sessionstart", "posttooluse", "userpromptsubmit"]),
        ("mcp", ["mcp", "claude-mem", "headroom", "task-observer", "omniroute"]),
        ("rule", ["rule", "猷?, ".claude/rules"]),
        ("skill", ["skill", "?ㅽ궗", ".claude/skills"]),
        ("commit", ["commit", "git", "push", "branch"]),
        ("install", ["install", "setup", "pip install", "npm install"]),
        ("ui", ["shadcn", "tailwind", "antd", "mui", "ui", "?붾㈃", "?붿옄??]),
        ("memory", ["memory", "硫붾え由?, "conversations", "session_summary", "?대젰"]),
        ("finetune", ["?뚯씤?쒕떇", "fine-tune", "lora", "qlora", "unsloth", "peft"]),
        ("embedding", ["?꾨쿋??, "embed", "chromadb", "vector", "sentence-transformers"]),
        ("optimize", ["理쒖쟻??, "optim", "compress", "vacuum", "cache"]),
        ("file", ["?뚯씪", "紐낅챸", "naming", "cleanup", "audit"]),
    ]:
        for kw in kws:
            if kw in text_l:
                return cat
    return "general"


def _extract_keywords(text: str, k: int = 8) -> str:
    words = re.findall(r"[媛-?즑-zA-Z]{3,}", text)
    seen = []
    for w in words:
        wl = w.lower()
        if wl not in seen and not wl.isdigit():
            seen.append(wl)
        if len(seen) >= k:
            break
    return ",".join(seen)


def _capture_session(session_id: str = None) -> dict:
    """?대쾲 ?몄뀡??理쒓렐 ???寃곗젙-?뚯씪-紐낅졊 醫낇빀."""
    sid = session_id or _sid()
    if not DB.exists():
        return {}
    with sqlite3.connect(str(DB)) as c:
        # 理쒓렐 ?ъ슜???꾨＼?꾪듃 (泥?臾몄젣)
        user_prompts = c.execute(
            "SELECT content FROM conversations WHERE session_id=? AND role='user' ORDER BY turn LIMIT 5",
            (sid,),
        ).fetchall()
        if not user_prompts:
            return {}
        problem = " ".join(p[0][:200] for p in user_prompts)[:1000]

        # ?몄뀡???쒕룞 ?붿빟
        activations = c.execute(
            "SELECT name FROM activations WHERE ts >= datetime('now','-2 hours') ORDER BY ts DESC LIMIT 20"
        ).fetchall()

        # ?뚯씪 audit
        try:
            files = c.execute(
                "SELECT path, action FROM file_audit WHERE session_id=? ORDER BY ts DESC LIMIT 20",
                (sid,),
            ).fetchall()
        except sqlite3.OperationalError:
            files = []

        # 理쒓렐 寃곗젙
        decisions = c.execute(
            "SELECT ai_classified FROM decisions WHERE ts >= datetime('now','-2 hours') ORDER BY ts DESC LIMIT 10"
        ).fetchall()

    approach = " | ".join(a[0] for a in activations if a[0])[:1500]
    solution = " | ".join(d[0] for d in decisions if d[0])[:2000]
    files_str = ",".join(sorted(set(f[0] for f in files)))[:1500]

    return {
        "session_id": sid,
        "problem": problem,
        "category": _extract_category(problem + " " + solution),
        "keywords": _extract_keywords(problem + " " + solution),
        "approach": approach,
        "solution": solution,
        "files_modified": files_str,
        "commands_run": "",
    }


def save(data: dict, verified: int = 0, reusable_score: int = 5) -> int | None:
    if not data or not data.get("problem"):
        return None
    ph = hashlib.sha256(data["problem"].encode("utf-8", errors="replace")).hexdigest()[:16]
    with sqlite3.connect(str(DB)) as c:
        try:
            cur = c.execute(
                """INSERT OR REPLACE INTO problem_solutions
                   (session_id,problem,category,keywords,approach,solution,files_modified,commands_run,verified,reusable_score,problem_hash)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    data.get("session_id", _sid()),
                    data["problem"],
                    data.get("category", "general"),
                    data.get("keywords", ""),
                    data.get("approach", ""),
                    data.get("solution", ""),
                    data.get("files_modified", ""),
                    data.get("commands_run", ""),
                    verified,
                    reusable_score,
                    ph,
                ),
            )
            c.commit()
            return cur.lastrowid
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
            sys.stderr.write(f"[save-solution] {e}\n")
            return None


def search(query: str, top_k: int = 5) -> list[dict]:
    if not DB.exists() or not query:
        return []
    kws = re.findall(r"[媛-?즑-zA-Z]{3,}", query)[:5]
    if not kws:
        return []
    where = " OR ".join(
        "keywords LIKE ? OR problem LIKE ? OR category LIKE ?" for _ in kws
    )
    params = []
    for k in kws:
        params.extend([f"%{k}%", f"%{k}%", f"%{k}%"])
    with sqlite3.connect(str(DB)) as c:
        rows = c.execute(
            f"""SELECT ts, category, problem, approach, solution, files_modified, reusable_score
                FROM problem_solutions WHERE {where}
                ORDER BY reusable_score DESC, ts DESC LIMIT ?""",
            (*params, top_k),
        ).fetchall()
    return [
        {
            "ts": r[0],
            "category": r[1],
            "problem": r[2][:200],
            "approach": r[3][:300] if r[3] else "",
            "solution": r[4][:400] if r[4] else "",
            "files_modified": r[5][:200] if r[5] else "",
            "reusable_score": r[6],
        }
        for r in rows
    ]


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "auto"
    if cmd == "auto":
        # Stop hook ?먮룞 罹≪쿂
        data = _capture_session()
        rid = save(data, verified=0, reusable_score=5)
        if rid:
            print(f"[ok] solution saved id={rid} category={data.get('category')}")
        else:
            print("[skip] no problem to capture")
    elif cmd == "manual":
        # ?섎룞 ?깆옱: save_solution.py manual "臾몄젣" "?닿껐" [移댄뀒怨좊━] [?먯닔]
        problem = sys.argv[2]
        solution = sys.argv[3]
        category = sys.argv[4] if len(sys.argv) > 4 else _extract_category(problem + solution)
        score = int(sys.argv[5]) if len(sys.argv) > 5 else 8
        rid = save(
            {
                "session_id": _sid(),
                "problem": problem,
                "category": category,
                "keywords": _extract_keywords(problem + " " + solution),
                "approach": "",
                "solution": solution,
                "files_modified": "",
                "commands_run": "",
            },
            verified=1,
            reusable_score=score,
        )
        print(f"[ok] manual solution saved id={rid}")
    elif cmd == "search":
        query = " ".join(sys.argv[2:])
        results = search(query, top_k=5)
        print(f"## 寃?? {query} - {len(results)} 寃곌낵")
        for r in results:
            print(f"\n[{r['category']} - score={r['reusable_score']} - {r['ts']}]")
            print(f"  臾몄젣: {r['problem']}")
            if r['solution']:
                print(f"  ?닿껐: {r['solution']}")
            if r['files_modified']:
                print(f"  ?뚯씪: {r['files_modified']}")
    else:
        print("usage: save_solution.py {auto|manual <臾몄젣> <?닿껐> [移댄뀒怨좊━] [?먯닔]|search <荑쇰━>}")

