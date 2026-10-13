"""lookup-history.sh ?댁떇 ???꾨＼?꾪듃 ?ㅼ썙?쒕줈 orca.db ?대젰(?댁쟾 ??붋룹꽭???붿빟쨌?ъ궗???닿껐梨? 議고쉶 ??二쇱엯.

遺?묒슜: problem_solutions.hit_count / last_hit_ts / reusable_score / verified 媛깆떊 (?먮낯 ?숈씪).
?ㅻ쪟??.claude/logs/lookup-history.log 濡?
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
    # print(p[:500], end='') -> $(...) 媛 ??媛쒗뻾 ?쒓굅
    prompt = bash_strip(ctx.field("user_prompt", "prompt")[:500])
    if not prompt:
        return None

    # ?먮낯? ?꾨＼?꾪듃瑜?''' ''' 由ы꽣?대줈 python ?뚯뒪???쇱썙 ?ｌ뿀??(諛깆뒳?섏떆쨌''' 媛 ?덉쑝硫?源⑥쭚).
    # ?ш린?쒕뒗 蹂?섎줈 吏곸젒 ?꾨떖 ???뺤긽 寃쎈줈 寃곌낵???숈씪.
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
            out.append("## 愿???댁쟾 ???(?먮룞 議고쉶 - DB)")
            for sid, turn, role, content in rows:
                out.append(f"- [{sid[:8]}#{turn} {role}] {content}")
        # ?몄뀡 ?붿빟 理쒓렐 愿??        sum_rows = c.execute(
            "SELECT session_id, substr(summary,1,150) FROM session_summary WHERE summary LIKE ? OR key_decisions LIKE ? ORDER BY ended_at DESC LIMIT 2",
            (f"%{kws[0]}%", f"%{kws[0]}%"),
        ).fetchall()
        if sum_rows:
            out.append("")
            out.append("## 愿???몄뀡 ?붿빟")
            for sid, summ in sum_rows:
                out.append(f"- [{sid[:8]}] {summ}")
        # problem_solutions ?ъ궗??移댄깉濡쒓렇 (?묐갑??
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
                out.append("## ?ъ궗??媛?ν븳 ?닿껐梨?(?먮룞 議고쉶)")
                hit_ids = []
                for sid_s, cat, prob, sol, files, score in sol_rows:
                    out.append(f"- [{cat} - ??score}] 臾몄젣: {prob}")
                    if sol:
                        out.append(f"  ?닿껐: {sol}")
                    if files:
                        out.append(f"  ?뚯씪: {files[:150]}")
                    hit_ids.append(sid_s)
                # hit_count 利앷? 쨌 verified ?밴툒 쨌 score ?곹뼢
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
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            pass
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        append_text(log, f"[lookup] {e}\n")
    finally:
        if c is not None:
            try:
                c.close()
            except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
                pass
    return "\n".join(out) + "\n" if out else None

