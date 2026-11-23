#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Golden regression tests (10 scenarios) — 사용자 요청 2026-10-16."""
from __future__ import annotations
import json, os, subprocess, sys
from datetime import datetime
from pathlib import Path

# Windows CP949 → UTF-8 (checkmark / crossmark 출력 보장)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

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
    # 2026-11-18 R293: 운영 원장을 시험 원장으로 바꿔 끼웠다가 되돌리던 것 → Claude 창 여러 개가 동시에 Stop 하면
    #   서로의 «백업» 이 시험 원장이 되어 운영 원장 292건이 1건으로 덮였다 (실측 사고 · 임시 백업도 안 지워 %TEMP% 누적).
    #   이제 임시 폴더를 프로젝트 루트로 삼아 실행 (CLAUDE_PROJECT_DIR) — 운영 원장은 읽지도 쓰지도 않는다.
    import tempfile, subprocess, os as _os
    with tempfile.TemporaryDirectory(prefix='golden-ledger-') as td:
        test_rl = Path(td)/'.claude'/'state'/'request-ledger.json'
        test_rl.parent.mkdir(parents=True)
        test_rl.write_text('{"session_id":"test","created_at":"t","requests":[{"id":"T_R1","desc":"test","status":"pending","ts":"t"}]}', encoding='utf-8')
        # evidence 없이 complete
        subprocess.run(['python','-X','utf8',str(ROOT/'.claude/scripts/request-ledger.py'),'complete','T_R1'],
                       capture_output=True, text=True, timeout=30, encoding='utf-8',  # R303 5초 → 30초 (동시 Stop·부하 때 거짓 FAIL)
                       env=dict(_os.environ, CLAUDE_PROJECT_DIR=td, ORCA_TEST_MODE='1'))  # R303 시험 표시 — 임시 폴더 밖 원장이면 request-ledger 가 쓰기 거부
        import json as _j
        data = _j.loads(test_rl.read_text(encoding='utf-8'))
        # 뻥 방지 확인: evidence 없으면 completed 되면 안됨
        return data['requests'][0]['status'] != 'completed'

def _run_sr_gate():
    import subprocess
    r = subprocess.run(['python','-X','utf8',str(ROOT/'.claude/scripts/standing-requirements.py'),'gate'],
                     capture_output=True, text=True, timeout=5, encoding='utf-8')
    return r.returncode == 0

TESTS = [
    ("T01","Request Ledger n/n gate",
     lambda: _ex(".claude/scripts/request-ledger.py") and _ex(".claude/hooks/stop-request-ledger-gate.sh")
     # R363: Stop 훅은 tool-dispatch stop 1개로 묶였다 — settings 직접 등록 또는 디스패처 동기 표(STOP_SYNC) 등록 둘 다 인정
     and (_ct(".claude/settings.json","stop-request-ledger-gate.sh")
          or (_ct(".claude/settings.json",'tool-dispatch.py\\" stop') and _ct(".claude/hooks/tool-dispatch.py",'".claude/hooks/stop-request-ledger-gate.sh"')))),
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
    # test-cache.json 작성 (READY 산정 source · 사용자 "품질 미평가 왜" 해결)
    try:
        cache = ROOT / ".claude" / "state" / "test-cache.json"
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({
            "passed": passed, "total": len(TESTS),
            "ts": datetime.now().isoformat(timespec="seconds"),
            "source": "golden-test.py",
        }, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return 0 if passed==len(TESTS) else 1

if __name__ == "__main__":
    sys.exit(main())
