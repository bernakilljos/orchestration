"""
save_solution — 세션 종료 시 문제-해결-파일-명령 자동 캡처 -> orca.db.problem_solutions
근거: 2026-09-02 사용자 지적 — "읽기(자동 조회) + 쓰기(처리 결과 기록) 양방향 - 초최고"
호출: Stop / SessionEnd hook + 수동 CLI
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
    """문제-해결에서 카테고리 자동 추출."""
    text_l = text.lower()
    for cat, kws in [
        ("db", ["sql", "sqlite", "database", "테이블", "orca.db", "migration"]),
        ("hook", ["hook", "sessionstart", "posttooluse", "userpromptsubmit"]),
        ("mcp", ["mcp", "claude-mem", "headroom", "task-observer", "omniroute"]),
        ("rule", ["rule", "룰", ".claude/rules"]),
        ("skill", ["skill", "스킬", ".claude/skills"]),
        ("commit", ["commit", "git", "push", "branch"]),
        ("install", ["install", "setup", "pip install", "npm install"]),
        ("ui", ["shadcn", "tailwind", "antd", "mui", "ui", "화면", "디자인"]),
        ("memory", ["memory", "메모리", "conversations", "session_summary", "이력"]),
        ("finetune", ["파인튜닝", "fine-tune", "lora", "qlora", "unsloth", "peft"]),
        ("embedding", ["임베딩", "embed", "chromadb", "vector", "sentence-transformers"]),
        ("optimize", ["최적화", "optim", "compress", "vacuum", "cache"]),
        ("file", ["파일", "명명", "naming", "cleanup", "audit"]),
    ]:
        for kw in kws:
            if kw in text_l:
                return cat
    return "general"


def _extract_keywords(text: str, k: int = 8) -> str:
    words = re.findall(r"[가-힣a-zA-Z]{3,}", text)
    seen = []
    for w in words:
        wl = w.lower()
        if wl not in seen and not wl.isdigit():
            seen.append(wl)
        if len(seen) >= k:
            break
    return ",".join(seen)


def _capture_session(session_id: str = None) -> dict:
    """이번 세션의 최근 대화-결정-파일-명령 종합."""
    sid = session_id or _sid()
    if not DB.exists():
        return {}
    with sqlite3.connect(str(DB)) as c:
        # 최근 사용자 프롬프트 (첫 문제)
        user_prompts = c.execute(
            "SELECT content FROM conversations WHERE session_id=? AND role='user' ORDER BY turn LIMIT 5",
            (sid,),
        ).fetchall()
        if not user_prompts:
            return {}
        problem = " ".join(p[0][:200] for p in user_prompts)[:1000]

        # 세션의 활동 요약
        activations = c.execute(
            "SELECT name FROM activations WHERE ts >= datetime('now','-2 hours') ORDER BY ts DESC LIMIT 20"
        ).fetchall()

        # 파일 audit
        try:
            files = c.execute(
                "SELECT path, action FROM file_audit WHERE session_id=? ORDER BY ts DESC LIMIT 20",
                (sid,),
            ).fetchall()
        except sqlite3.OperationalError:
            files = []

        # 최근 결정
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
        except Exception as e:
            sys.stderr.write(f"[save-solution] {e}\n")
            return None


def search(query: str, top_k: int = 5) -> list[dict]:
    if not DB.exists() or not query:
        return []
    kws = re.findall(r"[가-힣a-zA-Z]{3,}", query)[:5]
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
        # Stop hook 자동 캡처
        data = _capture_session()
        rid = save(data, verified=0, reusable_score=5)
        if rid:
            print(f"[ok] solution saved id={rid} category={data.get('category')}")
        else:
            print("[skip] no problem to capture")
    elif cmd == "manual":
        # 수동 등재: save_solution.py manual "문제" "해결" [카테고리] [점수]
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
        print(f"## 검색: {query} - {len(results)} 결과")
        for r in results:
            print(f"\n[{r['category']} - score={r['reusable_score']} - {r['ts']}]")
            print(f"  문제: {r['problem']}")
            if r['solution']:
                print(f"  해결: {r['solution']}")
            if r['files_modified']:
                print(f"  파일: {r['files_modified']}")
    else:
        print("usage: save_solution.py {auto|manual <문제> <해결> [카테고리] [점수]|search <쿼리>}")
