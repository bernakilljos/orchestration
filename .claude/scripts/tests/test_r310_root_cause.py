"""R310 근본 원인 기록 — 증상과 원인 분리 · 증거 없는 확정 거부 · 같은 원인 재사용 · 해결 실패 시 상태 갱신 (임시 DB 만)."""
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RT = ROOT / ".claude" / "scripts" / "recurrence-tracker.py"


def _run(tmp, *args):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp), "PYTHONUTF8": "1"}
    (tmp / ".claude" / "state").mkdir(parents=True, exist_ok=True)
    return subprocess.run([sys.executable, "-X", "utf8", str(RT), *args], env=env, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=60)


def _db(tmp):
    return sqlite3.connect(tmp / ".claude" / "state" / "orca.db")


def test_confirmed_needs_evidence_and_suspected_is_tagged(tmp_path):
    ev = json.loads(_run(tmp_path, "record", "미반영", "dev", "반영 안 됐잖아").stdout)["event_id"]
    bad = _run(tmp_path, "root-cause", str(ev), "--cause", "캐시 무효화 누락", "--status", "confirmed")
    assert bad.returncode == 2 and "증거 필수" in bad.stderr
    ok = _run(tmp_path, "root-cause", str(ev), "--cause", "캐시 무효화 누락")
    assert ok.returncode == 0
    rc, st = _db(tmp_path).execute("SELECT root_cause, auto_fix_status FROM recurrence_events WHERE id=?", (ev,)).fetchone()
    assert rc.startswith("[추정]") and st == "suspected"  # 추측은 확정 원인으로 저장되지 않음


def test_same_cause_reuses_improvement_and_failed_fix_reopens(tmp_path):
    e1 = json.loads(_run(tmp_path, "record", "미반영", "dev", "a").stdout)["event_id"]
    r1 = json.loads(_run(tmp_path, "root-cause", str(e1), "--cause", "statusline 캐시 600초", "--status", "confirmed",
                         "--evidence", "statusline_context.py:120 TTL=600 실측", "--fix", "TTL 30초 · test_x").stdout)
    e2 = json.loads(_run(tmp_path, "record", "미반영", "dev", "b").stdout)["event_id"]
    r2 = json.loads(_run(tmp_path, "root-cause", "미반영", "--cause", "statusline 캐시 600초", "--status", "confirmed",
                         "--evidence", "같은 증상 재현 rc=0 · 로그 동일").stdout)
    assert r2["event_id"] == e2 and r2["reused"] and r2["improvement_id"] == r1["improvement_id"]
    assert _run(tmp_path, "fix-result", str(e2), "failed", "--evidence", "재현됨").returncode == 0
    v, s = _db(tmp_path).execute("SELECT verified, status FROM recurrence_improvements WHERE improvement_id=?",
                                 (r1["improvement_id"],)).fetchone()
    assert (v, s) == (0, "FIX_FAILED")
    assert _run(tmp_path, "fix-result", str(e2), "passed").returncode == 2  # 증거 없는 통과 거부


def test_quality_small_sample_is_not_shown_as_rate(tmp_path):
    """B1: 분모 30 미만 = 표본 부족 (pct 없음) · 원장 없음 = 미측정 (0 아님)."""
    _run(tmp_path, "record", "미반영", "dev", "x")
    q = json.loads(_run(tmp_path, "quality").stdout)
    assert q["reinstruct"]["state"] == "미측정" and q["reinstruct"]["pct"] is None
    assert q["same_cause"]["state"] == "미측정"


def test_counterexample_hint_only_for_multi_item_requests():
    sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "prompt"))
    import ledger_auto_register as lar
    assert lar._counterexample_hint({"items": [1, 2]}) == ""
    assert lar._counterexample_hint({}) == ""
    h = lar._counterexample_hint({"items": [1, 2, 3]})
    assert "경계" in h and "양방향" in h
