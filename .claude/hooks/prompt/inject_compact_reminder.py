"""inject-compact-reminder.sh ?댁떇 ???좏겙 ?ъ슜瑜?60%+ ??/clear쨌compact ?덈궡 二쇱엯.

留덉?留?assistant usage 瑜??몄뀡 jsonl ?앹뿉?쒕?????갑?μ쑝濡??쎈뒗??(121MB 湲??뚯씪??利됱떆).
git ? ?ъ슜瑜?75%+ ?먯꽌 _safe_to_clear ?먯젙???뚮쭔 ?몄텧 (?먮낯怨??숈씪?섍쾶 寃뚯씠??.
"""
from __future__ import annotations

import glob
import json
import os
import re


def run(ctx):
    root = str(ctx.root)
    if not os.path.isdir(os.path.join(root, "plugins")):
        return None

    home = os.path.expanduser("~")
    cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    safe = re.sub(r"[^a-zA-Z0-9]", "-", cwd)
    proj = os.path.join(home, ".claude", "projects", safe)
    if not os.path.isdir(proj):
        return None
    # 2026-09-19: stdin ??transcript_path 媛 ?뺣낯 (mtime 理쒖떊 jsonl 異붿젙? ?숈떆 ?몄뀡?먯꽌 ?由?
    own = ctx.payload.get("transcript_path") or ""
    if own and isinstance(own, str) and os.path.isfile(own):
        jsonls = [own]
    else:
        jsonls = sorted(glob.glob(os.path.join(proj, "*.jsonl")), key=os.path.getmtime, reverse=True)
    if not jsonls:
        return None
    last_usage = None
    model_id = ""
    # 泥섏쓬遺???앷퉴吏 ?쎌쑝硫??몄뀡 jsonl(121MB ?ㅼ륫)?먯꽌 10珥? -> ?앹뿉?쒕???256KB ??嫄곌씀濡?    try:
        with open(jsonls[0], "rb") as f:
            f.seek(0, 2)
            pos = f.tell()
            tail = b""
            while pos > 0 and last_usage is None:
                step = min(262144, pos)
                pos -= step
                f.seek(pos)
                buf = f.read(step) + tail
                lines = buf.split(b"\n")
                tail = lines[0] if pos > 0 else b""  # ?섎┛ 泥?以꾩? ?ㅼ쓬 釉붾줉怨??댁뼱 遺숈엫
                for raw in reversed(lines[1:] if pos > 0 else lines):
                    if b'"assistant"' not in raw:
                        continue
                    try:
                        rec = json.loads(raw.decode("utf-8", errors="replace"))
                    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
                        continue
                    if rec.get("type") == "assistant":
                        msg = rec.get("message") or {}
                        u = msg.get("usage") or {}
                        # ?꾨? 0 ??usage(?쒕룄 珥덇낵 ?덈궡 ?? ??嫄대꼫?곌퀬 吏곸쟾 ?ㅼ젣 ?묐떟???대떎
                        if ((u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0)
                                + (u.get("cache_creation_input_tokens") or 0)) > 0:
                            last_usage = u
                            model_id = msg.get("model") or ""
                            break
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return None

    if not last_usage:
        return None

    tokens = int(
        (last_usage.get("input_tokens") or 0)
        + (last_usage.get("cache_read_input_tokens") or 0)
        + (last_usage.get("cache_creation_input_tokens") or 0)
    )

    # ?곹븳 - ?뺣낯? statusline_context.py 媛 湲곕줉??.claude/state/context-limit.json
    limit = None
    try:
        with open(os.path.join(cwd, ".claude", "state", "context-limit.json"), encoding="utf-8") as f:
            limit = int(json.load(f).get("limit") or 0) or None
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        pass
    if not limit:
        limit = 1_000_000 if ("[1m]" in (model_id or "") or tokens > 200_000) else 200_000
    pct = tokens / limit * 100

    RED = "\033[1;31m"
    YEL = "\033[1;33m"
    RST = "\033[0m"

    if pct >= 75:
        ok, why = _safe_to_clear(cwd)
        if ok is True:
            verdict = f"吏湲?/clear ?대룄 ?덉쟾 ({why}) - 0珥덉뿉 鍮꾩썙吏怨????몄뀡??理쒓렐 24h ?묒뾽 ?먮룞 蹂듦뎄."
        elif ok is False:
            verdict = f"吏湲덉? /clear 蹂대쪟 - {why}. 而ㅻ컠 癒쇱?."
        else:
            verdict = f"/clear ?덉쟾 ?먯젙 遺덇? ({why})."
        if pct >= 90:
            return f"{RED}[!!] ?좏겙 {pct:.0f}% ({tokens:,}/{limit:,}) - {verdict} 吏꾪뻾 以묒씠硫?洹몃?濡?- 97% ?먮룞 compact (?ㅼ륫 以묒븰 173珥?.{RST}\n"
        return f"{YEL}[!] ?좏겙 {pct:.0f}% ({tokens:,}/{limit:,}) - ?묒뾽 寃쎄퀎?먯꽌 /clear 沅뚯옣 쨌 {verdict} 議곌린 /compact ??鍮⑤씪吏吏 ?딆쓬 (?ㅼ륫 56留??좏겙 211珥?.{RST}\n"
    if pct >= 60:
        return f"[i] ?좏겙 {pct:.0f}% - compact ?꾨컯. ?욎쑝濡????뚯씪 read ?먯젣.\n"
    return None


def _safe_to_clear(root):
    """/clear ?덉쟾 ?먯젙 ??寃곌낵瑜?60珥??ъ궗??(2026-10-12: ICM 泥섎읆 ?섏쐞 ??μ냼媛 ?щ읉?대㈃ 留??꾨＼?꾪듃 git ??1.8~3珥?."""
    import json as _json
    import time as _time

    cache = os.path.join(root, ".claude", "state", "clear-safe-cache.json")
    try:
        with open(cache, encoding="utf-8") as f:
            c = _json.load(f)
        if _time.time() - c.get("ts", 0) < 60:
            return (c.get("ok"), c.get("why", ""))
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        pass
    ok, why = _safe_to_clear_git(root)
    try:
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        with open(cache, "w", encoding="utf-8") as f:
            _json.dump({"ts": _time.time(), "ok": ok, "why": why}, f, ensure_ascii=False)
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        pass
    return (ok, why)


def _safe_to_clear_git(root):
    """/clear ?덉쟾 ?먯젙 ??異붿쟻 以??뚯씪??誘몄빱諛??섏젙(M/A/D/R) ???덉쑝硫?蹂대쪟. 75%+ ???뚮쭔 ?몄텧 (git ?ъ슜)."""
    import subprocess

    repos = [root] if os.path.isdir(os.path.join(root, ".git")) else [
        os.path.join(root, d) for d in sorted(os.listdir(root))
        if os.path.isdir(os.path.join(root, d, ".git"))]
    reasons = []
    for repo in repos[:6]:
        try:
            r = subprocess.run(["git", "--no-optional-locks", "-C", repo, "status", "--porcelain"],
                               capture_output=True, text=True, timeout=8, encoding="utf-8", errors="replace")
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            return (None, "git ?뺤씤 ?ㅽ뙣")
        lost = [x[3:].strip().strip('"') for x in (r.stdout or "").splitlines() if len(x) > 3 and x[:2] != "??"]
        lost = [q for q in lost if not q.startswith(("docs/deploy-history/",))]  # hook ?먮룞 湲곕줉? ?쒖쇅
        if lost:
            head = ", ".join(lost[:3]) + (f" ??{len(lost) - 3}" if len(lost) > 3 else "")
            reasons.append(f"{os.path.basename(repo)} 誘몄빱諛?{len(lost)}嫄?{head})")
    if reasons:
        return (False, " 쨌 ".join(reasons))
    return (True, "誘몄빱諛?0")

