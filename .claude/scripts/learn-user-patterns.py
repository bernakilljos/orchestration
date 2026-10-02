#!/usr/bin/env python
"""
learn-user-patterns.py — 사용자 반복 지시 패턴 자동 학습

orca.db conversations + problem_solutions 분석 → 반복 트리거 키워드 top N 추출
→ .claude/state/learned-user-patterns.json 저장
→ SessionStart hook 가 systemMessage 로 안내

주 1회 자동 (일요일 04:30 · learn-style.py 와 같이) + 사용자 명시 시 (/recall-patterns)
"""
from __future__ import annotations
import json, os, sqlite3, re, sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / ".claude" / "state" / "orca.db"
OUT = ROOT / ".claude" / "state" / "learned-user-patterns.json"
RULES = ROOT / ".claude" / "rules" / "user-emotion.md"

# 이미 매핑된 트리거 (user-emotion.md 에서 추출)
EXISTING_TRIGGERS = set()
if RULES.exists():
    txt = RULES.read_text(encoding="utf-8", errors="ignore")
    # | **"X"·"Y"·"Z"** | ... | 패턴에서 X·Y·Z 추출
    for m in re.finditer(r'\*\*["\']([^"\'\*]+)["\']', txt):
        for tok in re.split(r'[·,、/]', m.group(1)):
            tok = tok.strip().strip('"\'')
            if 1 < len(tok) < 20:
                EXISTING_TRIGGERS.add(tok.lower())

# 사용자 자주 쓰는 어휘 추출 (명사·동사 어미 · 2~15 chars)
TOKEN_RE = re.compile(r'[가-힣a-zA-Z]{2,15}')
# 불용어 (일반어 제외)
STOPWORDS = {
    "그리고","그래서","이거","저거","우리","지금","아니","오늘","내가","너가","그냥","좀",
    "같이","모두","전부","이게","그게","저게","이런","그런","저런","하는","있는","없는","있어","없어",
    "되는","안되","되어","있어야","있자나","자나","이야","같아","같다","싶어","싶다","하자","하지",
    "the","and","for","with","this","that","what","how","why","when","where","your","from","have","has",
}

def extract_tokens(text: str) -> list[str]:
    toks = []
    for m in TOKEN_RE.findall(text or ""):
        t = m.lower()
        if t in STOPWORDS or t in EXISTING_TRIGGERS: continue
        if len(t) < 2: continue
        toks.append(t)
    return toks

def main():
    if not DB.exists():
        print("[WARN] orca.db 없음 · skip"); return
    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    counter = Counter()
    phrase_examples: dict[str, str] = {}
    try:
        c = sqlite3.connect(DB)
        rows = c.execute(
            "SELECT content FROM conversations WHERE role='user' AND ts >= ? LIMIT 2000",
            (cutoff,)
        ).fetchall()
    except Exception as e:
        print(f"[WARN] conversations 조회 실패: {e}"); return

    for (content,) in rows:
        if not content: continue
        snippet = content[:200]
        for tok in extract_tokens(snippet):
            counter[tok] += 1
            # 예시 문장 저장 (처음 1개)
            if tok not in phrase_examples and len(snippet) < 100:
                phrase_examples[tok] = snippet.strip()

    # top 30 (3회+ 반복만)
    top = [(k, v) for k, v in counter.most_common(100) if v >= 3][:30]
    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "orca.db.conversations · 최근 30일 · role=user",
        "existing_triggers_count": len(EXISTING_TRIGGERS),
        "total_user_turns": len(rows),
        "top_patterns": [
            {"trigger": k, "count": v, "example": phrase_examples.get(k, "")}
            for k, v in top
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {OUT.name} · top {len(top)} 패턴 · total user turns {len(rows)}")
    print(f"  top 5: {[t['trigger'] for t in result['top_patterns'][:5]]}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERR] {e}", file=sys.stderr); sys.exit(0)
