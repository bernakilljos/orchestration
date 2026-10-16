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

# Windows cp949 환경에서 stdout·stderr UTF-8 강제 (키 cp949 저장 방지)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass  # noqa: BLE001

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / ".claude" / "state" / "orca.db"
SESSIONS_DB = ROOT / ".claude" / "state" / "sessions.db"
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
    "미반영":          r'안\s*되었|안\s*됐|안\s*되어있|적용\s*안|효과\s*없|작동\s*안|반영\s*안',
    "전수조사skip":    r'농땡이|대충|장난|제대로.*해|전수조사|다\s*(보지|보시)',
}

def count_in_window(rows, patterns, days):
    cutoff = datetime.now() - timedelta(days=days)
    cnt = Counter()
    for (ts, txt) in rows:
        if not txt: continue
        try:
            tsd = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if tsd.tzinfo:  # sessions.db 는 UTC(Z) · 로컬 naive 로 맞춰 비교
                tsd = tsd.astimezone().replace(tzinfo=None)
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
    # 정본 = sessions.db prompts(source='typed') — jsonl 증분 적재라 전 세션이 있다.
    # orca.db.conversations 는 save-user-prompt 훅이 놓친 게 많아 (2026-10-02 실측 12건 vs typed 133건)
    # 위반 0 으로 보여 상태줄 줄이 통째로 숨었다. 없을 때만 폴백.
    cutoff90 = (datetime.now() - timedelta(days=90)).isoformat()
    rows, source = [], ""
    try:
        if SESSIONS_DB.exists():
            c = sqlite3.connect(SESSIONS_DB)
            rows = c.execute(
                "SELECT ts, text FROM prompts WHERE source='typed' "
                "AND ts >= ? ORDER BY ts DESC LIMIT 5000", (cutoff90[:10],)
            ).fetchall()
            source = "sessions.db:prompts(typed)"
        if not rows and DB.exists():
            c = sqlite3.connect(DB)
            rows = c.execute(
                "SELECT ts, content FROM conversations WHERE role='user' "
                "AND ts >= ? ORDER BY ts DESC LIMIT 5000", (cutoff90,)
            ).fetchall()
            source = "orca.db:conversations"
    except Exception as e:
        print(f"[ERR] {e}", file=sys.stderr); return
    if not source:
        return

    design_90 = count_in_window(rows, DESIGN_PATTERNS, 90)
    design_30 = count_in_window(rows, DESIGN_PATTERNS, 30)
    design_7  = count_in_window(rows, DESIGN_PATTERNS, 7)
    dev_90    = count_in_window(rows, DEV_PATTERNS, 90)
    dev_30    = count_in_window(rows, DEV_PATTERNS, 30)
    # 2026-10-06 사용자 지시 「0이라도」 — 0건 항목도 상태줄에 보이도록 전 카테고리 키 유지
    design_30 = {k: design_30.get(k, 0) for k in DESIGN_PATTERNS}
    dev_30    = {k: dev_30.get(k, 0) for k in DEV_PATTERNS}
    dev_7     = count_in_window(rows, DEV_PATTERNS, 7)

    def recur_rate(c7, c30):
        total_30 = sum(c30.values())
        total_7  = sum(c7.values())
        return round(total_7 / total_30 * 100) if total_30 else 0

    # recurrence-tracker.py 통합 (2026-10-16 사용자 지시 — 재발률 재정의)
    rec_stats = None
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location(
            "_rec_tracker", str(ROOT / ".claude" / "scripts" / "recurrence-tracker.py")
        )
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        rec_stats = _mod.stats()
    except Exception:
        pass

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "user_turns_90d": len(rows),
        "design": {
            "counts_90d": design_90,
            "counts_30d": design_30,
            "counts_7d":  design_7,
            "recur_rate_pct": recur_rate(design_7, design_30),
        },
        "dev": {
            "counts_90d": dev_90,
            "counts_30d": dev_30,
            "counts_7d":  dev_7,
            "recur_rate_pct": recur_rate(dev_7, dev_30),
        },
    }
    # recurrence-tracker SoT 통계 (사용자 정의 재발률)
    if rec_stats:
        result["recurrence"] = rec_stats
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # ensure_ascii=True → 한국어 키 \uXXXX escape 로 저장 (Windows cp949 환경 호환)
    OUT.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="utf-8")

if __name__ == "__main__":
    try: main()
    except Exception as e: print(f"[ERR] {e}", file=sys.stderr); sys.exit(0)
