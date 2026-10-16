#!/usr/bin/env python
"""Golden regression tests (10 scenarios) — 사용자 요청 2026-10-16."""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])

def _classify(msg):
    r = subprocess.run(["python","-X","utf8",str(ROOT/".claude/scripts/classify-task.py"),msg],
        capture_output=True,text=True,timeout=10,encoding="utf-8")
    try: return json.loads(r.stdout)
    except: return {}

def _ex(p): return (ROOT/p).exists()
def _ct(p, s):
    f = ROOT/p
    return f.exists() and s in f.read_text(encoding="utf-8",errors="ignore")

TESTS = [
    ("T01","Request Ledger n/n gate",
     lambda: _ex(".claude/scripts/request-ledger.py") and _ex(".claude/hooks/stop-request-ledger-gate.sh")
     and _ct(".claude/settings.json","stop-request-ledger-gate.sh")),
    ("T02","Codex 명시 라우팅",
     lambda: _classify("codex로 리뷰해줘").get("ai")=="codex"),
    ("T03","디자인 임의 변경 X",
     lambda: _ct(".claude/rules/execution-contract.md","고객 화면")),
    ("T04","공통 컴포넌트 재사용 증명",
     lambda: _ct(".claude/rules/operating-principles.md","이미 이 기능이 존재")),
    ("T05","수정 후 검증 의무",
     lambda: _ex(".claude/rules/verify-after-edit-mandatory.md")),
    ("T06","고객 플로우 업무 중심",
     lambda: _ct(".claude/rules/execution-contract.md","업무 흐름")),
    ("T07","WebSearch hook 등록",
     lambda: _ex(".claude/hooks/websearch-trigger-detect.sh")
     and _ct(".claude/hooks/prompt-dispatch.py","websearch_trigger_detect")),
    ("T08","scope-lock + 범위 lock",
     lambda: _ex(".claude/scripts/scope-lock.py")
     and _ct(".claude/rules/execution-contract.md","범위 lock")),
    ("T09","중간보고 금지",
     lambda: _ct(".claude/rules/execution-contract.md","보고 금지")),
    ("T10","미측정 != 정상",
     lambda: _ct(".claude/scripts/statusline_context.py","미측정")
     and _ct(".claude/rules/operating-principles.md","미측정")),
]

def main():
    passed = 0; failed = []
    print("="*60); print("Golden Tests · 10 scenarios"); print("="*60)
    for tid, name, chk in TESTS:
        try: ok = bool(chk())
        except: ok = False
        print(f"  {'✓' if ok else '✗'} {tid} {'PASS' if ok else 'FAIL'}: {name}")
        if ok: passed += 1
        else: failed.append(tid)
    print("="*60); print(f"총 {passed}/10 PASS")
    if failed: print(f"FAIL: {', '.join(failed)}")
    return 0 if passed==10 else 1

if __name__ == "__main__":
    sys.exit(main())
