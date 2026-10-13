"""lookup-history.sh 이식 — 프롬프트 키워드로 orca.db 이력(이전 대화·세션 요약·재사용 해결책) 조회 후 주입.

부작용: problem_solutions.hit_count / last_hit_ts / reusable_score / verified 갱신 (원본 동일).
오류는 .claude/logs/lookup-history.log 로.
"""
from __future__ import annotations

import os
import re

from _common import append_text, bash_strip


def run(ctx):
    log = ctx.root / ".claude" / "logs" / "lookup-history.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    if not log.exists():
        log.touch()

    if ctx.parse_error_strict:
        append_text(log, f"[parse] {ctx.parse_error_strict}\n")
        return None
    # print(p[:500], end='') -> $(...) 가 끝 개행 제거
    prompt = bash_strip(ctx.field("user_prompt", "prompt")[:500])
    if not prompt:
        return None

    # 원본은 프롬프트를 ''' ''' 리터럴로 python 소스에 끼워 넣었다 (백슬래시·''' 가 있으면 깨짐).
    # 여기서는 변수로 직접 전달 — 정상 경로 결과는 동일.
    kws = [w for w in re.findall(r"\w{3,}", prompt) if not w.isdigit()][:8]
    if not kws:
        return None
    db = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."), ".claude", "state", "orca.db")
    if not os.path.exists(db):
        return None

    import sqlite3

    out: list[str] = []
    c = None
    try:
        c = sqlite3.connect(db)
        like = " OR ".join(["content LIKE ?"] * len(kws))
        params = [f"%{k}%" for k in kws]
        rows = c.execute(
            f"SELECT session_id, turn, role, substr(content,1,200) FROM conversations WHERE ({like}) AND session_id != ? ORDER BY id DESC LIMIT 3",
            (*params, os.environ.get("CLAUDE_CODE_SESSION_ID", "")),
        ).fetchall()
        if rows:
            out.append("## 관련 이전 대화 (자동 조회 - DB)")
            for sid, turn, role, content in rows:
                out.append(f"- [{sid[:8]}#{turn} {role}] {content}")
        # 세션 요약 최근 관련
        sum_rows = c.execute(
            "SELECT session_id, substr(summary,1,150) FROM session_summary WHERE summary LIKE ? OR key_decisions LIKE ? ORDER BY ended_at DESC LIMIT 2",
            (f"%{kws[0]}%", f"%{kws[0]}%"),
        ).fetchall()
        if sum_rows:
            out.append("")
            out.append("## 관련 세션 요약")
            for sid, summ in sum_rows:
                out.append(f"- [{sid[:8]}] {summ}")
        # problem_solutions 재사용 카탈로그 (양방향)
        like2 = " OR ".join(["keywords LIKE ? OR problem LIKE ?"] * min(len(kws), 4))
        params2: list[str] = []
        for k in kws[:4]:
            params2.extend([f"%{k}%", f"%{k}%"])
        try:
            cols = [r[1] for r in c.execute("PRAGMA table_info(problem_solutions)").fetchall()]
            if "hit_count" not in cols:
                c.execute("ALTER TABLE problem_solutions ADD COLUMN hit_count INTEGER DEFAULT 0")
            if "last_hit_ts" not in cols:
                c.execute("ALTER TABLE problem_solutions ADD COLUMN last_hit_ts TIMESTAMP")
            sol_rows = c.execute(
                f"SELECT id, category, substr(problem,1,120), substr(solution,1,200), files_modified, reusable_score FROM problem_solutions WHERE ({like2}) ORDER BY reusable_score DESC, ts DESC LIMIT 3",
                params2,
            ).fetchall()
            if sol_rows:
                out.append("")
                out.append("## 재사용 가능한 해결책 (자동 조회)")
                hit_ids = []
                for sid_s, cat, prob, sol, files, score in sol_rows:
                    out.append(f"- [{cat} - ★{score}] 문제: {prob}")
                    if sol:
                        out.append(f"  해결: {sol}")
                    if files:
                        out.append(f"  파일: {files[:150]}")
                    hit_ids.append(sid_s)
                # hit_count 증가 · verified 승급 · score 상향
                for hid in hit_ids:
                    c.execute(
                        "UPDATE problem_solutions SET hit_count=COALESCE(hit_count,0)+1, "
                        "last_hit_ts=CURRENT_TIMESTAMP, "
                        "reusable_score=CASE "
                        "WHEN COALESCE(hit_count,0)+1 >= 10 THEN 10 "
                        "WHEN COALESCE(hit_count,0)+1 >= 5 THEN MAX(reusable_score, 9) "
                        "WHEN COALESCE(hit_count,0)+1 >= 3 THEN MAX(reusable_score, 8) "
                        "ELSE MAX(reusable_score, 6) END, "
                        "verified=CASE WHEN COALESCE(hit_count,0)+1 >= 3 THEN 1 ELSE verified END "
                        "WHERE id=?",
                        (hid,),
                    )
                c.commit()
        except Exception:
            pass
    except Exception as e:
        append_text(log, f"[lookup] {e}\n")
    finally:
        if c is not None:
            try:
                c.close()
            except Exception:
                pass
    return "\n".join(out) + "\n" if out else None
