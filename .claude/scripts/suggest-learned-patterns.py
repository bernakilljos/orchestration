#!/usr/bin/env python
"""
suggest-learned-patterns.py — 학습된 반복 패턴 중 **아직 매핑 안 된** 것을 제안
(자동 patch X · dry-run 전용 · 사용자 승인 후만 반영)

흐름:
1. .claude/state/learned-user-patterns.json 읽기
2. user-emotion.md 현재 매핑된 트리거와 대조
3. 미매핑 + count≥5 패턴만 "제안" 으로 저장
4. SessionStart hook 가 systemMessage 로 "N 개 신규 패턴 발견 · /apply-learned 로 반영" 안내
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
LEARNED = ROOT / ".claude" / "state" / "learned-user-patterns.json"
RULES = ROOT / ".claude" / "rules" / "user-emotion.md"
SUGGESTIONS = ROOT / ".claude" / "state" / "learned-pattern-suggestions.json"

MIN_COUNT = 5  # 안전 threshold
NOISE = {"id","task","on","reset","mcp","command","pm","local","pjt","claude","트랙",
         "ago","src","dst","usr","etc","tmp","log","dir","env","key","val"}  # 노이즈 (명백한 설정 어휘)

def extract_existing_triggers(txt: str) -> set[str]:
    out = set()
    # | **"X"·"Y"·"Z"** | 패턴
    for m in re.finditer(r'\*\*["\']([^"\'\*]+)["\']\*\*', txt):
        for tok in re.split(r'[·,、/]', m.group(1)):
            t = tok.strip().strip('"\'').lower()
            if t: out.add(t)
    return out

def main():
    if not LEARNED.exists():
        print(f"[WARN] {LEARNED.name} 없음 · learn-user-patterns.py 먼저")
        return
    data = json.loads(LEARNED.read_text(encoding="utf-8"))
    patterns = data.get("top_patterns", [])
    existing = extract_existing_triggers(RULES.read_text(encoding="utf-8", errors="ignore")) if RULES.exists() else set()

    suggestions = []
    for p in patterns:
        tok = p["trigger"].lower()
        if tok in NOISE: continue
        if tok in existing: continue
        if any(tok in e or e in tok for e in existing if len(e) > 2): continue  # 부분 매칭도 skip
        if p["count"] < MIN_COUNT: continue
        suggestions.append({
            "trigger": p["trigger"],
            "count": p["count"],
            "example": p["example"],
            "proposed_action": "매핑 미정 · 사용자 지정 필요"
        })

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "safe_threshold": MIN_COUNT,
        "existing_mappings": len(existing),
        "learned_total": len(patterns),
        "suggestions_count": len(suggestions),
        "note": "자동 patch X · 사용자가 /apply-learned 또는 직접 user-emotion.md 수정",
        "suggestions": suggestions,
    }
    SUGGESTIONS.parent.mkdir(parents=True, exist_ok=True)
    SUGGESTIONS.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {SUGGESTIONS.name} · 신규 제안 {len(suggestions)} 개 (count>={MIN_COUNT})")
    for s in suggestions[:5]:
        print(f"  [{s['count']}x] {s['trigger']}  —  {s['example'][:60]}")

if __name__ == "__main__":
    try: main()
    except Exception as e: print(f"[ERR] {e}", file=sys.stderr); sys.exit(0)
