#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""statusline 서브 agent 수 + 폭 검증 (2026-10-26)."""
import json, os, subprocess, sys, shutil
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = r"C:\pjt\orchestration_v1"
AG = os.path.join(ROOT, ".claude", "state", "active-agents.json")
STATUS = os.path.join(ROOT, ".claude", "scripts", "statusline_context.py")

# 백업
try:
    with open(AG, "r", encoding="utf-8") as f:
        orig = f.read()
except Exception:
    orig = "[]"

payload = json.dumps({"session_id": "test",
                      "cwd": ROOT,
                      "model": {"id": "claude-opus-5-5[1m]"}})

results = []
for N in (0, 1, 2, 3, 6):
    fake = [{"id": f"t{i}", "type": "general-purpose",
             "description": f"long name test {i} xxxxxxxxxxxxxxxx",
             "start_ts": "2026-10-26T00:00:00Z", "model": "opus"} for i in range(N)]
    with open(AG, "w", encoding="utf-8") as f:
        json.dump(fake, f)
    r = subprocess.run([sys.executable, "-X", "utf8", STATUS],
                       input=payload, capture_output=True, text=True, timeout=15,
                       cwd=ROOT, encoding="utf-8", errors="replace")
    out = r.stdout
    lines = out.split("\n")
    has_drift = any("DRIFT" in ln for ln in lines)
    has_cost = any("비용" in ln for ln in lines)
    # literal ESC 노출: 라인에 \x1b 없이 '[18G' 또는 '[90m' 가 있으면 bug
    literal_bug = any(("[18G" in ln or "[90m" in ln) and "\x1b" not in ln for ln in lines)
    # 라인별 '│' 위치 (왼쪽 col 체크)
    import re
    cols = []
    for ln in lines:
        # ANSI 제거
        plain = re.sub(r"\x1b\[[0-9;]*[mG]", "", ln)
        idx = plain.find("│")
        if idx >= 0:
            cols.append(idx + 1)  # 1-indexed
    uniq_cols = sorted(set(cols))
    results.append({"N": N, "lines": len(lines), "DRIFT": has_drift,
                    "비용": has_cost, "literal_bug": literal_bug,
                    "left_bar_cols": uniq_cols[:3]})

# 복원
with open(AG, "w", encoding="utf-8") as f:
    f.write(orig)

print(f"{'N':>3} {'lines':>5} {'DRIFT':>5} {'비용':>5} {'bug':>5} {'left_bar_cols':<20}")
print("-" * 55)
for r in results:
    print(f"{r['N']:>3} {r['lines']:>5} {str(r['DRIFT']):>5} {str(r['비용']):>5} "
          f"{str(r['literal_bug']):>5} {r['left_bar_cols']}")

all_ok = all(r["DRIFT"] and r["비용"] and not r["literal_bug"] for r in results)
# 왼쪽 col 통일 (0명~6명 모두 동일 col 집합)
col_sets = [tuple(r["left_bar_cols"]) for r in results]
col_uniform = len(set(col_sets)) <= 2  # 서브 continuation 때문에 1~2 종류 OK
print(f"\n[결과] 모든 N 에서 DRIFT·비용 노출 + ESC bug X: {all_ok}")
print(f"[결과] left bar col 일관성: {col_uniform} (sets={set(col_sets)})")
