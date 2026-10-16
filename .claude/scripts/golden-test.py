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


def _run_gate_test():
    # evidence 없이 complete 시도 → status != completed 확인 (뻥 방지)
    import tempfile, shutil, subprocess
    orig = ROOT/'.claude/state/request-ledger.json'
    backup = tempfile.mktemp(suffix='.json')
    if orig.exists(): shutil.copy(orig, backup)
    try:
        test_rl = ROOT/'.claude/state/request-ledger.json'
        test_rl.write_text('{"session_id":"test","created_at":"t","requests":[{"id":"T_R1","desc":"test","status":"pending","ts":"t"}]}', encoding='utf-8')
        # evidence 없이 complete
        r = subprocess.run(['python','-X','utf8',str(ROOT/'.claude/scripts/request-ledger.py'),'complete','T_R1'],
                         capture_output=True, text=True, timeout=5, encoding='utf-8')
        import json as _j
        data = _j.loads(test_rl.read_text(encoding='utf-8'))
        # 뻥 방지 확인: evidence 없으면 completed 되면 안됨
        return data['requests'][0]['status'] != 'completed'
    finally:
        if Path(backup).exists(): shutil.copy(backup, orig)

def _run_sr_gate():
    import subprocess
    r = subprocess.run(['python','-X','utf8',str(ROOT/'.claude/scripts/standing-requirements.py'),'gate'],
                     capture_output=True, text=True, timeout=5, encoding='utf-8')
    return r.returncode == 0

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
    ("T11","Request Ledger gate 실제 차단 (뻥 completed 방지)",
     lambda: _run_gate_test()),
    ("T12","Codex 라우팅 1-step 종단 (명시 -> ai=codex 반환)",
     lambda: _classify("codex로 리뷰해줘").get("ai")=="codex" and _classify("codex 로 3개 파일 수정").get("ai")=="codex"),
    ("T13","Standing Requirements gate 실제 통과",
     lambda: _run_sr_gate()),
    ("T10","미측정 != 정상",
     lambda: _ct(".claude/scripts/statusline_context.py","⏳")
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
    print("="*60); print(f"총 {passed}/{len(TESTS)} PASS")
    if failed: print(f"FAIL: {', '.join(failed)}")
    return 0 if passed==len(TESTS) else 1

if __name__ == "__main__":
    sys.exit(main())
