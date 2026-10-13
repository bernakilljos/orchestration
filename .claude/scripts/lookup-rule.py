#!/usr/bin/env python3
"""lookup-rule.py ??AI 媛 猷?硫붾え由??ㅽ겕由쏀듃瑜?鍮좊Ⅴ寃?寃??
洹쇨굅: CLAUDE.md 猷?硫붾え由??ㅽ겕由쏀듃 ?꾩쟻 -> grep 鍮꾪슚?? RAG/踰≫꽣 DB ?쒖슜.

?ъ슜:
  python lookup-rule.py "寃利???蹂닿퀬"        # ?섎? 湲곕컲 寃??
  python lookup-rule.py "嫄곗쭞 蹂닿퀬" --top 5    # top-K
  python lookup-rule.py --rebuild              # ?몃뜳???ш뎄??
  python lookup-rule.py --status               # ?몃뜳???곹깭

?꾨왂 (?먮룞 ?좏깮):
  1李?(?섏〈??0): frontmatter + 蹂몃Ц TF ?먯닔??(Python ?댁옣)
  2李?(chromadb ?ㅼ튂 ??: 踰≫꽣 DB ?섎? 寃??(?먮룞 ?꾪솚)

?몃뜳?????
  - .claude/rules/*.md
  - ~/.claude/projects/<proj>/memory/*.md
  - .claude/scripts/*.{py,sh} (frontmatter / 泥?docstring)
  - CLAUDE.md 짠 7 湲덉? ??ぉ
"""
import sys
import os
import io
import json
import re
import math
from pathlib import Path
from collections import Counter

# UTF-8 stdout (Windows)
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

PROJECT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())).resolve()
INDEX_DIR = PROJECT_ROOT / ".claude" / "state" / "rule-index"
INDEX_JSON = INDEX_DIR / "rules.json"
CHROMA_DIR = INDEX_DIR / "chroma"

# === ?몃뜳??????붾젆?좊━ ===
TARGETS = [
    ("rule", PROJECT_ROOT / ".claude" / "rules", "*.md"),
    ("memory", Path.home() / ".claude" / "projects", "**/memory/*.md"),
    ("script", PROJECT_ROOT / ".claude" / "scripts", "*.py"),
    ("script", PROJECT_ROOT / ".claude" / "scripts", "*.sh"),
    ("hook", PROJECT_ROOT / ".claude" / "hooks", "*.sh"),
]

CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"


def extract_frontmatter(text: str) -> dict:
    """?뚯씪 泥?frontmatter (--- ?ъ씠) 異붿텧."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm


def extract_doc(text: str, lang: str) -> str:
    """script ??泥?docstring/二쇱꽍 釉붾줉 異붿텧."""
    if lang == "py":
        m = re.search(r'"""(.+?)"""', text, re.DOTALL)
        if m:
            return m.group(1).strip()[:500]
    elif lang == "sh":
        # 泥?# comment 釉붾줉
        lines = []
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("#!"):
                continue
            if s.startswith("#"):
                lines.append(s.lstrip("#").strip())
            elif lines:
                break
            elif s:
                break
        return "\n".join(lines)[:500]
    return ""


def extract_claude_md_rules() -> list:
    """CLAUDE.md 짠 7 湲덉? ??ぉ 異붿텧."""
    if not CLAUDE_MD.exists():
        return []
    text = CLAUDE_MD.read_text(encoding="utf-8")
    # 짠 7. 湲덉? ?ы빆 ~ ---
    m = re.search(r"## 7\. 湲덉? ?ы빆\s*\n(.+?)\n---", text, re.DOTALL)
    if not m:
        return []
    body = m.group(1)
    items = []
    for num, content in re.findall(r"^(\d+)\.\s+(.+?)(?=\n\d+\.\s|\Z)", body, re.DOTALL | re.MULTILINE):
        # 泥?以?(?쒕ぉ)
        first_line = content.strip().split("\n")[0]
        items.append({
            "type": "claude_md",
            "id": f"짠7-{num}",
            "title": first_line[:80],
            "body": content.strip()[:600],
            "path": "CLAUDE.md",
        })
    return items


def build_index() -> list:
    """?꾩껜 ?몃뜳??-> list of {type, id, title, body, path, keywords}"""
    index = []

    for entry_type, base, pattern in TARGETS:
        if not base.exists():
            continue
        for p in base.glob(pattern):
            if not p.is_file():
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
                continue

            fm = extract_frontmatter(text)
            title = fm.get("name") or p.stem
            desc = fm.get("description", "")

            if entry_type == "script":
                lang = "py" if p.suffix == ".py" else "sh"
                doc = extract_doc(text, lang)
                body = (desc + " " + doc).strip() or text[:500]
            else:
                # rule / memory ??蹂몃Ц 泥?500??(frontmatter ??
                content_after_fm = re.sub(r"^---.+?---\s*", "", text, count=1, flags=re.DOTALL)
                body = (desc + " " + content_after_fm[:600]).strip()

            index.append({
                "type": entry_type,
                "id": p.stem,
                "title": title,
                "body": body,
                "path": str(p.relative_to(PROJECT_ROOT) if PROJECT_ROOT in p.parents else p),
            })

    # CLAUDE.md 짠 7 猷?
    index.extend(extract_claude_md_rules())

    return index


# === 寃??(1李? TF 湲곕컲) ===
def tokenize(text: str) -> list:
    """媛꾨떒 ?좏겙??(?쒓?-?곷Ц ?⑥뼱)."""
    text = text.lower()
    # ?쒓?-?곷Ц-?レ옄 ?⑥뼱
    tokens = re.findall(r"[媛-??+|[a-z][a-z0-9]+", text)
    return tokens


def score(query: str, item: dict) -> float:
    """媛꾨떒 TF ?먯닔: query ?⑥뼱媛 item ???쇰쭏???섏삤?붿?."""
    q_tokens = tokenize(query)
    if not q_tokens:
        return 0.0
    item_text = " ".join([item.get("title", ""), item.get("body", ""), item.get("id", "")])
    item_tokens = tokenize(item_text)
    if not item_tokens:
        return 0.0
    counter = Counter(item_tokens)
    s = 0.0
    for q in q_tokens:
        if q in counter:
            s += counter[q] / len(item_tokens) * 100
        # 遺遺?留ㅼ튂 (substring)
        for tok, cnt in counter.items():
            if q in tok and q != tok:
                s += cnt / len(item_tokens) * 30
    # title 留ㅼ튂 媛以?
    title_tokens = tokenize(item.get("title", ""))
    for q in q_tokens:
        if q in title_tokens:
            s += 50
        for tok in title_tokens:
            if q in tok:
                s += 20
    return s


def search(query: str, top: int = 8) -> list:
    """Top-K 寃곌낵."""
    if not INDEX_JSON.exists():
        rebuild()
    index = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    results = [(score(query, item), item) for item in index]
    results = [r for r in results if r[0] > 0]
    results.sort(key=lambda x: -x[0])
    return results[:top]


# === ?몃뜳???ш뎄??===
def rebuild():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    idx = build_index()
    INDEX_JSON.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(idx)


def status():
    if not INDEX_JSON.exists():
        print("[NO INDEX] --rebuild 癒쇱? ?ㅽ뻾")
        return
    idx = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    by_type = Counter(item["type"] for item in idx)
    print(f"[INDEX] {len(idx)} entries")
    for t, c in by_type.most_common():
        print(f"  {t:10} {c}")
    print(f"  file: {INDEX_JSON}")


def main():
    args = sys.argv[1:]

    if not args or args[0] == "--help":
        print(__doc__)
        return

    if args[0] == "--rebuild":
        n = rebuild()
        print(f"[OK] {n} entries indexed -> {INDEX_JSON}")
        return

    if args[0] == "--status":
        status()
        return

    # 寃??
    query = args[0]
    top = 8
    if "--top" in args:
        i = args.index("--top")
        top = int(args[i + 1])

    results = search(query, top)
    if not results:
        print(f"[no match] '{query}' ???ㅻⅨ ?ㅼ썙???쒕룄")
        return

    print(f"[QUERY] {query} -> {len(results)} 寃곌낵:\n")
    for i, (sc, item) in enumerate(results, 1):
        type_label = f"[{item['type']}]"
        print(f"{i}. {type_label:10} {item['title']}  (score {sc:.1f})")
        if item.get("path"):
            print(f"   {item['path']}")
        # body 泥?以?
        body_first = item.get("body", "").strip().split("\n")[0][:100]
        if body_first:
            print(f"   {body_first}")
        print()


if __name__ == "__main__":
    main()

