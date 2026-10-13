"""Memory ?먮룞 寃??濡쒕뱶 ???ъ슜??硫붿떆吏 -> 愿??feedback memory 異붿텧.

UserPromptSubmit hook ???듯빀:
1. ?ъ슜??硫붿떆吏 ?ㅼ썙??異붿텧
2. ~/.claude/projects/<proj>/memory/feedback_*.md 寃??
3. 留ㅼ묶 memory description 異붿텧 -> systemMessage 二쇱엯

紐⑹쟻: Memory 媛 ?덉뼱??Claude 媛 ?딅뒗 臾몄젣 ?닿껐 (5 ?듭떖 遺??以?#4 Memory 蹂댁셿).
"""
import sys
import re
import json
from pathlib import Path

# project memory dir ?먮룞 媛먯?
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_NAME = PROJECT_ROOT.name  # "orchestration_v1"
# Claude Code ??project memory 寃쎈줈 ??C:--pjt-orchestration-v1 ?뺤떇
# Claude Code project memory 寃쎈줈 ?먮룞 寃????`_` ??`-` 蹂??
def _candidate_memory_dirs():
    # `orchestration_v1` -> `orchestration-v1` 蹂??(Claude Code ??path -> dir ?뺢퇋??
    proj_normalized = PROJECT_NAME.replace("_", "-")
    base = Path.home() / ".claude" / "projects"
    if base.exists():
        for sub in base.iterdir():
            if sub.is_dir() and proj_normalized in sub.name:
                mem = sub / "memory"
                if mem.exists():
                    yield mem

MEMORY_DIR_CANDIDATES = list(_candidate_memory_dirs()) or [
    Path.home() / ".claude" / "memory",
]


def find_memory_dir() -> Path:
    for d in MEMORY_DIR_CANDIDATES:
        if d.exists():
            return d
    return None


def parse_frontmatter(content: str) -> dict:
    """YAML frontmatter 異붿텧."""
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def extract_keywords(message: str) -> set:
    """?ъ슜??硫붿떆吏 -> ?듭떖 ?ㅼ썙??異붿텧."""
    # ?쒓? 2湲??, ?곸뼱 3湲?? ?⑥뼱 異붿텧
    words = set()
    words.update(re.findall(r"[媛-??{2,}", message))
    words.update(w.lower() for w in re.findall(r"[a-zA-Z]{3,}", message))
    return words


def score_memory(mem_content: str, keywords: set) -> int:
    """memory ?댁슜 vs ?ㅼ썙??留ㅼ묶 ?먯닔."""
    fm = parse_frontmatter(mem_content)
    desc = fm.get("description", "") + " " + fm.get("name", "")
    desc_lower = desc.lower()
    score = 0
    for kw in keywords:
        if kw.lower() in desc_lower:
            score += 3  # description 留ㅼ묶? ??媛以?
        elif kw.lower() in mem_content.lower():
            score += 1
    return score


def _recall_long_term(keywords: set, top_n: int) -> list:
    """?κ린 = ~/.claude/projects/<proj>/memory/feedback_*.md"""
    mem_dir = find_memory_dir()
    if mem_dir is None:
        return []
    matches = []
    for mf in mem_dir.glob("feedback_*.md"):
        try:
            content = mf.read_text(encoding="utf-8")
        except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
            continue
        score = score_memory(content, keywords)
        if score > 0:
            fm = parse_frontmatter(content)
            matches.append({
                "tier": "long",
                "file": mf.name,
                "name": fm.get("name", mf.stem),
                "description": fm.get("description", "")[:200],
                "score": score,
            })
    matches.sort(key=lambda x: -x["score"])
    return matches[:top_n]


def _recall_short_term(keywords: set) -> list:
    """?④린 = .claude/context-cache/session-snapshot.md"""
    snap = PROJECT_ROOT / ".claude" / "context-cache" / "session-snapshot.md"
    if not snap.exists():
        return []
    try:
        content = snap.read_text(encoding="utf-8")
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return []
    score = sum(1 for kw in keywords if kw.lower() in content.lower())
    if score == 0:
        return []
    # ?ㅼ썙??留ㅼ묶 ?쇱씤 異붿텧 (top 2)
    lines = [l for l in content.split("\n") if any(kw.lower() in l.lower() for kw in keywords)]
    return [{
        "tier": "short",
        "file": "session-snapshot.md",
        "name": "?꾩옱 ?몄뀡 ?ㅻ깄??,
        "description": " - ".join(lines[:2])[:200],
        "score": score,
    }]


def _recall_mid_term(keywords: set, top_n: int = 2) -> list:
    """以묎린 = orca.db decisions table (理쒓렐 7??"""
    import sqlite3
    from datetime import datetime, timedelta
    db = PROJECT_ROOT / ".claude" / "state" / "orca.db"
    if not db.exists():
        return []
    try:
        conn = sqlite3.connect(str(db))
        cutoff = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        like_clause = " OR ".join(["user_msg LIKE ?" for _ in keywords])
        if not like_clause:
            return []
        params = [f"%{kw}%" for kw in list(keywords)[:5]] + [cutoff]
        cur = conn.execute(
            f"SELECT user_msg, ai_classified, ts FROM decisions WHERE ({like_clause}) AND ts >= ? ORDER BY ts DESC LIMIT ?",
            params + [top_n],
        )
        results = []
        for row in cur.fetchall():
            msg, ai, ts = row
            results.append({
                "tier": "mid",
                "file": "orca.db decisions",
                "name": f"怨쇨굅 寃곗젙 ({ts})",
                "description": f"[{ai}] {msg[:150]}",
                "score": 1,
            })
        conn.close()
        return results
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
        return []


def recall(message: str, top_n: int = 3) -> list:
    """?ъ슜??硫붿떆吏 -> 3-tier memory recall.

    - ?④린: session-snapshot (?꾩옱 ?몄뀡)
    - 以묎린: orca.db decisions (理쒓렐 7??
    - ?κ린: feedback memory (?꾩껜 ?숈뒿 寃곌낵)
    """
    keywords = extract_keywords(message)
    if not keywords:
        return []
    all_matches = []
    all_matches.extend(_recall_short_term(keywords))
    all_matches.extend(_recall_mid_term(keywords))
    all_matches.extend(_recall_long_term(keywords, top_n))
    # tier 蹂꾨줈 理쒖냼 1媛쒖뵫 蹂댁옣, ?⑺빐??top_n+2 源뚯?
    return all_matches[: top_n + 2]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        if not sys.stdin.isatty():
            msg = sys.stdin.read().strip()
        else:
            print("usage: recall-memory.py '<?ъ슜??硫붿떆吏>'")
            sys.exit(2)
    else:
        msg = " ".join(sys.argv[1:])
    results = recall(msg)
    print(json.dumps(results, ensure_ascii=False, indent=2))

