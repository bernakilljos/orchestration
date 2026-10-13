#!/usr/bin/env python3
"""lookup-rule.py — AI 가 룰/메모리/스크립트를 빠르게 검색
근거: CLAUDE.md 룰-메모리-스크립트 누적 -> grep 비효율. RAG/벡터 DB 활용.

사용:
  python lookup-rule.py "검증 후 보고"        # 의미 기반 검색
  python lookup-rule.py "거짓 보고" --top 5    # top-K
  python lookup-rule.py --rebuild              # 인덱스 재구성
  python lookup-rule.py --status               # 인덱스 상태

전략 (자동 선택):
  1차 (의존성 0): frontmatter + 본문 TF 점수화 (Python 내장)
  2차 (chromadb 설치 시): 벡터 DB 의미 검색 (자동 전환)

인덱싱 대상:
  - .claude/rules/*.md
  - ~/.claude/projects/<proj>/memory/*.md
  - .claude/scripts/*.{py,sh} (frontmatter / 첫 docstring)
  - CLAUDE.md § 7 금지 항목
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

# === 인덱싱 대상 디렉토리 ===
TARGETS = [
    ("rule", PROJECT_ROOT / ".claude" / "rules", "*.md"),
    ("memory", Path.home() / ".claude" / "projects", "**/memory/*.md"),
    ("script", PROJECT_ROOT / ".claude" / "scripts", "*.py"),
    ("script", PROJECT_ROOT / ".claude" / "scripts", "*.sh"),
    ("hook", PROJECT_ROOT / ".claude" / "hooks", "*.sh"),
]

CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"


def extract_frontmatter(text: str) -> dict:
    """파일 첫 frontmatter (--- 사이) 추출."""
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
    """script 의 첫 docstring/주석 블록 추출."""
    if lang == "py":
        m = re.search(r'"""(.+?)"""', text, re.DOTALL)
        if m:
            return m.group(1).strip()[:500]
    elif lang == "sh":
        # 첫 # comment 블록
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
    """CLAUDE.md § 7 금지 항목 추출."""
    if not CLAUDE_MD.exists():
        return []
    text = CLAUDE_MD.read_text(encoding="utf-8")
    # § 7. 금지 사항 ~ ---
    m = re.search(r"## 7\. 금지 사항\s*\n(.+?)\n---", text, re.DOTALL)
    if not m:
        return []
    body = m.group(1)
    items = []
    for num, content in re.findall(r"^(\d+)\.\s+(.+?)(?=\n\d+\.\s|\Z)", body, re.DOTALL | re.MULTILINE):
        # 첫 줄 (제목)
        first_line = content.strip().split("\n")[0]
        items.append({
            "type": "claude_md",
            "id": f"§7-{num}",
            "title": first_line[:80],
            "body": content.strip()[:600],
            "path": "CLAUDE.md",
        })
    return items


def build_index() -> list:
    """전체 인덱싱 -> list of {type, id, title, body, path, keywords}"""
    index = []

    for entry_type, base, pattern in TARGETS:
        if not base.exists():
            continue
        for p in base.glob(pattern):
            if not p.is_file():
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except Exception:
                continue

            fm = extract_frontmatter(text)
            title = fm.get("name") or p.stem
            desc = fm.get("description", "")

            if entry_type == "script":
                lang = "py" if p.suffix == ".py" else "sh"
                doc = extract_doc(text, lang)
                body = (desc + " " + doc).strip() or text[:500]
            else:
                # rule / memory — 본문 첫 500자 (frontmatter 후)
                content_after_fm = re.sub(r"^---.+?---\s*", "", text, count=1, flags=re.DOTALL)
                body = (desc + " " + content_after_fm[:600]).strip()

            index.append({
                "type": entry_type,
                "id": p.stem,
                "title": title,
                "body": body,
                "path": str(p.relative_to(PROJECT_ROOT) if PROJECT_ROOT in p.parents else p),
            })

    # CLAUDE.md § 7 룰
    index.extend(extract_claude_md_rules())

    return index


# === 검색 (1차: TF 기반) ===
def tokenize(text: str) -> list:
    """간단 토큰화 (한글-영문 단어)."""
    text = text.lower()
    # 한글-영문-숫자 단어
    tokens = re.findall(r"[가-힣]+|[a-z][a-z0-9]+", text)
    return tokens


def score(query: str, item: dict) -> float:
    """간단 TF 점수: query 단어가 item 에 얼마나 나오는지."""
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
        # 부분 매치 (substring)
        for tok, cnt in counter.items():
            if q in tok and q != tok:
                s += cnt / len(item_tokens) * 30
    # title 매치 가중
    title_tokens = tokenize(item.get("title", ""))
    for q in q_tokens:
        if q in title_tokens:
            s += 50
        for tok in title_tokens:
            if q in tok:
                s += 20
    return s


def search(query: str, top: int = 8) -> list:
    """Top-K 결과."""
    if not INDEX_JSON.exists():
        rebuild()
    index = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    results = [(score(query, item), item) for item in index]
    results = [r for r in results if r[0] > 0]
    results.sort(key=lambda x: -x[0])
    return results[:top]


# === 인덱스 재구성 ===
def rebuild():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    idx = build_index()
    INDEX_JSON.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(idx)


def status():
    if not INDEX_JSON.exists():
        print("[NO INDEX] --rebuild 먼저 실행")
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

    # 검색
    query = args[0]
    top = 8
    if "--top" in args:
        i = args.index("--top")
        top = int(args[i + 1])

    results = search(query, top)
    if not results:
        print(f"[no match] '{query}' — 다른 키워드 시도")
        return

    print(f"[QUERY] {query} -> {len(results)} 결과:\n")
    for i, (sc, item) in enumerate(results, 1):
        type_label = f"[{item['type']}]"
        print(f"{i}. {type_label:10} {item['title']}  (score {sc:.1f})")
        if item.get("path"):
            print(f"   {item['path']}")
        # body 첫 줄
        body_first = item.get("body", "").strip().split("\n")[0][:100]
        if body_first:
            print(f"   {body_first}")
        print()


if __name__ == "__main__":
    main()
