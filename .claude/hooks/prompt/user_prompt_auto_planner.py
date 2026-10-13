"""user-prompt-auto-planner.sh ?댁떇 ??????뺤젙 + 5?④퀎 plan + MoE 遺꾨쪟 + 硫붾え由?recall 二쇱엯.

?먮낯? python 5媛?(?꾨＼?꾪듃 異붿텧쨌遺꾨쪟쨌?ㅼ썙?쒗쉶?겶룻솢?숇줈洹맞룰껐?뺣줈洹? 瑜?留ㅻ쾲 ?꾩썱??
?ш린?쒕뒗 ?꾨? in-process. 臾닿굅??RAG(chromadb) 留?detached ?뚯빱濡??④릿??
"""
from __future__ import annotations

import json
import os
import re
import sys

from _common import (
    HOOKS_DIR,
    bash_strip,
    load_script,
    msys_path,
    read_text,
    search,
)

TRIGGER_PATTERN = "?댁쨾|怨좎퀜以??뺤씤|?먭?|??萸먯빞|?섎땲|?섎꽕|?덈뤌|?덈릺|?묐꽕|?щ꽕|吏ㅻ젮|吏ㅻ┛|吏ㅻ┝|?섎┝|?섎━|吏ㅻ━|?щ갚|?ъ쟾|?섏퀜|?덈낫|湲??蹂댁뿬???섎릺|?섎맖|?섑븯|遺議?????由?諛쒕룞|?띾븸???꾩닔議곗궗|?뺤떊|?뚰뵾|?대쭚|臾댁떆|???볦낀|fix|build|verify|check|review|test|update|add|change|?쒖씠由?諛⑹?|蹂댁셿|?대?吏|硫붾え由??깅뒫"
SUBAGENT_BIG_PATTERN = "?꾩닔議곗궗|?꾩껜.*?먯깋|?꾩껜.*寃??紐⑤뱺.*?뚯씪|紐⑤뱺.*?대뜑|肄붾뱶踰좎씠??whole.?code|grep.*all"
SUBAGENT_REVIEW_PATTERN = "由щ럭|review|肄붾뱶 寃??PR 寃??
OUTPUT_TEMPLATE = (
    "{\"hookSpecificOutput\":{\"hookEventName\":\"UserPromptSubmit\",\"additionalContext\":\"[????뺤젙 REQUIRED ??0?쒖쐞]\\n"
    "??泥??묐떟 泥?以??뺤떇 (留?吏???꾩닔): ??? <path> (kit/?ㅼ젙/target/湲濡쒕쾶) ??留욎쑝硫?吏꾪뻾, ?꾨땲硫??뺤젙\\n"
    "??4媛덈옒 ?꾨낫:\\n"
    "  1) ${PROJECT_ROOT} (kit ?먯껜 媛먯궗-猷?hook)\\n"
    "  2) ${PROJECT_ROOT}/setup/templates/ (install 諛고룷??template)\\n"
    "  3) install ????ㅼ슫???꾨줈?앺듃 (寃쎈줈 臾쇱뼱遊????ъ슜?먭? '?ㅼ슫??-'?섎뱶肄붾뵫 ?ㅼ륫'-'?щ컻 諛⑹? ?뚯옣'-鍮꾩쫰?덉뒪 吏?쒕챸 ?멸툒 ??\\n"
    "  4) ~/.claude/ (湲濡쒕쾶 ?ㅼ젙)\\n"
    "??????뺤젙 ??grep-Read-Edit-Bash 李⑹닔 = 猷??꾨컲. ?먮룞 ?꾨낫 ?섏뿴??X ?섍퀬 kit ?ㅼ?湲??쒖옉 = ?щ컻.\\n"
    "?곸꽭: .claude/rules/direction-first.md - feedback_confirm_target_first.md\\n"
    "\\n"
    "[auto-planner ENFORCED]\\n"
    "?ъ슜??硫붿떆吏???묒뾽 吏??寃고븿 吏???먭? ?ㅼ썙??媛먯?. 5?④퀎 ?섎Т 諛쒕룞:\\n"
    "1) ?꾩닔議곗궗 ???몄젒 ?쒖뒪???꾩뿭源뚯? 紐⑤뱺 ?꾩튂 ?묎린 (?⑥씪 ?꾨낫濡?寃곕줎 X)\\n"
    "2) 遺꾩꽍 ??diff/md5sum/蹂몃Ц?쇰줈 ?댁슜 寃利?(?뚯씪紐낅쭔 蹂닿퀬 ?⑥젙 X)\\n"
    "3) ?ㅽ뻾 ??諛쒓껄??臾몄젣瑜?肄붾뱶濡??섏젙\\n"
    "4) ?뺤씤 ???먮룞 寃利?(verify-image-fit / verify-docx-pages / verify-docx-structure / verify-ppt-overflow) 諛쒕룞-PASS ?뺤씤\\n"
    "5) 蹂닿퀬 ????紐⑸줉?쇰줈 寃곌낵 + ?⑥? 寃곗젙?ы빆\\n"
    "\\n"
    "湲덇린:\\n"
    "- ????뺤젙 ?놁씠 ?ㅽ뻾 李⑹닔 (0?쒖쐞 ?꾨컲)\\n"
    "- 遺遺?泥섎━ (???뚯씪留?蹂닿퀬 ?듬?)\\n"
    "- 寃利?X ?섍퀬 ?꾨즺 蹂닿퀬\\n"
    "- ?ъ슜?먯뿉寃?寃곗젙 ?좊꽆湲곌린 (?щ━?곗뺄 5媛吏 ??\\n"
    "- ?뚰뵾-?대쭚 (吏곸젒 ??-> 遺??-> ?됰룞)\\n"
    "- 留ㅻ쾲 ?ъ슜??吏??湲곕떎由?(auto-planner ?먮룞 諛쒕룞)\\n"
    "\\n"
    "?먮룞 諛쒕룞 ?몃━嫄? auto-planner.md skill\\n"
    "\\n"
    "${GUIDE}${SUBAGENT_GUIDE}${MEMORY_GUIDE}${ALARM_GUIDE}${COMPACT_GUIDE}\"}}"
)

# ?먮낯 踰꾧렇 ?명솚 ???ㅼ썙???뚯긽 寃곌낵媛 0嫄댁씠硫?`grep -c ... || echo 0` ??"0\n0" ??留뚮뱾怨?# log-decision.py 媛 int("0\n0") 濡?二쎌뼱 decisions ??湲곕줉?섏? ?딆븯??(?뚯긽 1嫄? ???뚮쭔 湲곕줉).
# ??log-decision.py ???몄옄媛 ?덉쑝硫?argv[1] (= "--ai") ??硫붿떆吏濡???ν븳??
# ?숈옉 洹몃?濡?蹂댁〈. 怨좎튂?ㅻ㈃ ??媛믪쓣 False / ?꾨＼?꾪듃濡?諛붽씔??
COMPAT_SKIP_ZERO_HIT_DECISION = True
COMPAT_DECISION_MSG = "--ai"


def _read_rag_cache(root) -> str:
    cache = root / ".claude" / "state" / "rag-last.json"
    if cache.is_file():
        return bash_strip(read_text(cache))
    return "[]"


def _spawn_rag(root, prompt: str) -> None:
    """RAG(?섎? 寃?? 媛깆떊 ??17珥?嫄몃━??chromadb 濡쒕뱶???숆린 寃쎈줈 遺덇? -> detached 1媛?(???덉쑝硫?skip)."""
    script = root / ".claude" / "scripts" / "rag-recall.py"
    lock = root / ".claude" / "state" / "rag-running"
    if not script.is_file() or lock.exists():
        return
    if os.environ.get("PROMPT_DISPATCH_NO_SPAWN") == "1":  # ?뚯뒪?몄슜
        return
    import subprocess

    try:
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.touch()
        env = dict(os.environ, AP_PROMPT=prompt, PYTHONIOENCODING="utf-8")
        kw = {}
        if os.name == "nt":
            kw["creationflags"] = 0x08000000 | 0x00000008  # CREATE_NO_WINDOW | DETACHED_PROCESS
        else:
            kw["start_new_session"] = True
        subprocess.Popen(
            [sys.executable, "-X", "utf8", str(HOOKS_DIR / "prompt-dispatch.py"), "--rag-worker"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            close_fds=True,
            **kw,
        )
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        try:
            lock.unlink()
        except OSError:
            pass


def rag_worker() -> None:
    """detached ?뚯빱 蹂몄껜 ??寃곌낵瑜?rag-last.json ???곌퀬 ???댁젣 (?깃났 ?쒖뿉留?援먯껜)."""
    from _common import ROOT

    state = ROOT / ".claude" / "state"
    cache, tmp, lock = state / "rag-last.json", state / "rag-last.json.tmp", state / "rag-running"
    try:
        prompt = os.environ.get("AP_PROMPT", "").strip()
        mod = load_script("rag-recall")
        results = mod.search(prompt, 3)
        with open(tmp, "wb") as f:
            f.write((json.dumps(results, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        os.replace(tmp, cache)
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        pass
    finally:
        try:
            lock.unlink()
        except OSError:
            pass


def _lines(rx: str, text: str, label: str, limit: int) -> list[str]:
    """grep -oE '"key": "..."' | sed | head -N."""
    return [f"- ({label}) {m}" for m in re.findall(rx, text)][:limit]


def run(ctx):
    # 2026-09-19: context-usage-pct.py ???섏쐞 ?꾨줈?몄뒪媛 ???몄뀡 transcript 瑜??쎈룄濡?stdin ??transcript_path 瑜??섍꼍???붾떎
    tp = ctx.payload.get("transcript_path") or ""
    if tp and isinstance(tp, str):
        os.environ["CLAUDE_TRANSCRIPT_PATH"] = tp

    p = ctx.payload.get("prompt") or ""
    if not isinstance(p, str):
        p = str(p)
    prompt = bash_strip(p[:1000])

    if not search(TRIGGER_PATTERN, prompt):
        return None

    root = ctx.root

    # MoE ?먮룞 遺꾨쪟
    ai, reason = "claude", "湲곕낯"
    cls = load_script("classify-task")
    if cls is not None:
        try:
            res = cls.classify(prompt.strip())
            ai = res.get("ai") or ai
            reason = res.get("reason") or reason
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            pass
    ctx.mark("classify")

    # ?ㅼ썙??3-tier ?뚯긽
    rec_text = "[]"
    rec = load_script("recall-memory")
    if rec is not None:
        try:
            rec_text = json.dumps(rec.recall(prompt.strip()), ensure_ascii=False, indent=2)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            rec_text = ""
    ctx.mark("recall")

    # RAG ???댁쟾 ?꾨＼?꾪듃媛 留뚮뱺 罹먯떆瑜??쎄퀬, 媛깆떊? detached 濡?    rag_text = _read_rag_cache(root)
    _spawn_rag(root, prompt)

    if ai == "codex":
        guide = f"[MoE ?먮룞] codex ?꾩엫 沅뚯옣 ({reason}). ?먮룞 dispatch: python .claude/scripts/auto-dispatch.py"
    elif ai == "gemini":
        guide = f"[MoE ?먮룞] Gemini Flash 沅뚯옣 ({reason}). gemini-auto ?뚯빱 ?쒖슜"
    elif ai == "haiku":
        guide = f"[MoE ?먮룞] Haiku 沅뚯옣 ({reason}). haiku-auto ?뚯빱 ?쒖슜"
    else:
        guide = f"[MoE ?먮룞] Claude 吏곸젒 泥섎━ ({reason})"

    subagent = ""
    if search(SUBAGENT_BIG_PATTERN, prompt):
        subagent = "\\n\\n[Subagent ?먮룞] '??肄붾뱶踰좎씠???먯깋' 媛먯? -> Task tool 濡?Explore subagent ?먮룞 ?몄텧 沅뚯옣 (硫붿씤 而⑦뀓?ㅽ듃 寃⑸━)"
    elif search(SUBAGENT_REVIEW_PATTERN, prompt):
        subagent = "\\n\\n[Subagent ?먮룞] '肄붾뱶 由щ럭' 媛먯? -> Task tool 濡?code-reviewer subagent ?먮룞 ?몄텧 沅뚯옣"

    # ?쒕룞 濡쒓렇 (?먮낯: background python) ??orca.db.activations + hook-trace.log
    la = load_script("log-activation")
    if la is not None:
        try:
            trig = "" if prompt.startswith("--") else prompt
            la.log("hook", "user-prompt-auto-planner", trig, "success", 0)
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            pass
    ctx.mark("log-activation")

    # Memory ?먮룞 recall 臾멸뎄 (?먮낯 grep/sed ?뚯씠?꾨씪?몄쓣 ?뺢퇋?앹쑝濡?
    mem_lines = _lines(r'"description"\s*:\s*"([^"]*)"', rec_text, "kw", 3)
    rag_lines = _lines(r'"preview"\s*:\s*"([^"]*)"', rag_text, "rag", 2)
    combined = mem_lines + rag_lines
    memory_guide = ""
    if combined:
        memory_guide = (
            "\\n\\n[Memory ?먮룞 recall ??kw=?ㅼ썙??/ rag=?섎?] 愿???숈뒿 (?щ컻 諛⑹?):\\n"
            + "".join(ln + "\\n" for ln in combined)
        )

    # 寃곗젙 濡쒓렇 (?먮낯: background python)
    ld = load_script("log-decision")
    if ld is not None:
        mem_count = sum(1 for ln in rec_text.split("\n") if '"file"' in ln)
        if mem_count > 0 or not COMPAT_SKIP_ZERO_HIT_DECISION:
            try:
                ld.log(COMPAT_DECISION_MSG, ai, mem_count)
            except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
                pass
    ctx.mark("log-decision")

    out = (
        OUTPUT_TEMPLATE.replace("${PROJECT_ROOT}", msys_path(root))
        .replace("${GUIDE}", guide)
        .replace("${SUBAGENT_GUIDE}", subagent)
        .replace("${MEMORY_GUIDE}", memory_guide)
        .replace("${ALARM_GUIDE}", "")
        .replace("${COMPACT_GUIDE}", "")
    )
    # ?먮낯? JSON ?띿뒪?몃? 吏곸젒 議곕┰??stdout ?쇰줈 ?덈떎 ??媛숈? 諛⑹떇?쇰줈 ?댁꽍 (源⑥?硫??됰Ц 痍④툒)
    try:
        return json.loads(out)["hookSpecificOutput"]["additionalContext"]
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return out

