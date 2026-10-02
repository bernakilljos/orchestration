#!/usr/bin/env python
"""
aggregate-rule-adherence.py — 룰 위반 지수 집계 (디자인·개발)

orca.db conversations 스캔 → 사용자 재지적 패턴 count →
.claude/state/rule-adherence.json 저장. statusline 이 이 JSON 읽음.

cache TTL 10분 (매 턴 재계산 X).
"""
from __future__ import annotations
import json, sqlite3, re, sys, os, time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / ".claude" / "state" / "orca.db"
OUT = ROOT / ".claude" / "state" / "rule-adherence.json"
TTL = 600  # 10분

# 디자인 룰 위반 지표 (사용자 재지적 어휘)
DESIGN_PATTERNS = {
    "이모지":          r'이모지|이모티콘|emoji',
    "여백":            r'여백|빈 공간|비어|밋밋|밋밋해',
    "버전관리":        r'-v2|-v3|_v2|_v3|final_final|버전\s*접미|v2\s*(만들|파일)',
    "산출물기한":      r'OVERDUE|산출물.*기한|freshness|오래\s*됐|낡은',
}
# 개발 룰 위반 지표
DEV_PATTERNS = {
    "증명지시":        r'증명해|확인해 봐|검증해',
    "안됐":            r'안\s*되었|안\s*됐|안\s*되어있|적용\s*안|효과\s*없|작동\s*안',
    "전수조사skip":    r'농땡이|대충|장난|제대로.*해|전수조사|다\s*(보지|보시)',
}

def count_in_window(rows, patterns, days):
    cutoff = datetime.now() - timedelta(days=days)
    cnt = Counter()
    for (ts, txt) in rows:
        if not txt: continue
        try:
            tsd = datetime.fromisoformat(ts)
        except Exception:
            continue
        if tsd < cutoff: continue
        for k, pat in patterns.items():
            if re.search(pat, txt):
                cnt[k] += 1
    return dict(cnt)

def main():
    # TTL 체크
    if OUT.exists():
        age = time.time() - OUT.stat().st_mtime
        if age < TTL and os.environ.get("FORCE") != "1":
            return  # cache valid
    if not DB.exists():
        return
    try:
        c = sqlite3.connect(DB)
        rows = c.execute(
            "SELECT ts, content FROM conversations WHERE role='user' "
            "AND ts >= ? ORDER BY ts DESC LIMIT 5000",
            ((datetime.now() - timedelta(days=90)).isoformat(),)
        ).fetchall()
    except Exception as e:
        print(f"[ERR] {e}", file=sys.stderr); return

    design_30 = count_in_window(rows, DESIGN_PATTERNS, 30)
    design_7  = count_in_window(rows, DESIGN_PATTERNS, 7)
    dev_30    = count_in_window(rows, DEV_PATTERNS, 30)
    dev_7     = count_in_window(rows, DEV_PATTERNS, 7)

    def recur_rate(c7, c30):
        total_30 = sum(c30.values())
        total_7  = sum(c7.values())
        return round(total_7 / total_30 * 100) if total_30 else 0

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "user_turns_90d": len(rows),
        "design": {
            "counts_90d": design_30,
            "counts_7d":  design_7,
            "recur_rate_pct": recur_rate(design_7, design_30),
        },
        "dev": {
            "counts_90d": dev_30,
            "counts_7d":  dev_7,
            "recur_rate_pct": recur_rate(dev_7, dev_30),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    try: main()
    except Exception as e: print(f"[ERR] {e}", file=sys.stderr); sys.exit(0)
