"""R317 실전 REPAIR 5건 0% 원인 재현·수정 검증 (모두 임시 폴더 · 운영 orca.db 무관).

원인: supervisor 가 REPAIR goal 의 RUNNING 판정에 verify-improvement.py 의 없는 인자(--source-ref)를 넘겨
항상 exit 2 → REPAIRING ↔ RUNNING 왕복 → 재시도 상한 FAILED (수리 작업 0회). self-heal 수리 goal 도 같은 판정이 끼어들어
복구 성공을 FAILED 로 덮었다.
"""
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SUP = ROOT / ".claude" / "scripts" / "lib" / "supervisor.py"
RT = ROOT / ".claude" / "scripts" / "recurrence-tracker.py"
VI = ROOT / ".claude" / "scripts" / "verify-improvement.py"


def _sup(tmp, monkeypatch):
    (tmp / ".claude" / "state").mkdir(parents=True, exist_ok=True)
    (tmp / ".claude" / "scripts").mkdir(parents=True, exist_ok=True)
    # 운영과 같게 검증 스크립트를 둔다 (없으면 옛 코드가 판정을 건너뛰어 덮어쓰기 결함이 재현 안 됨)
    (tmp / ".claude" / "scripts" / "verify-improvement.py").write_bytes(VI.read_bytes())
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp))
    sp = importlib.util.spec_from_file_location(f"sup317_{id(tmp)}", SUP)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _rt(tmp, *args):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp), "PYTHONUTF8": "1"}
    env.pop("ORCA_TEST_MODE", None)
    return subprocess.run([sys.executable, "-X", "utf8", str(RT), *args], env=env, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=300)


def _goal(m, gid):
    with sqlite3.connect(str(m.DB)) as c:
        return c.execute("SELECT status, retry_count, failure_reason FROM goals WHERE goal_id=?", (gid,)).fetchone()


def _last_reason(m, gid):
    with sqlite3.connect(str(m.DB)) as c:
        return c.execute("SELECT reason FROM goal_transitions WHERE goal_id=? ORDER BY id DESC LIMIT 1", (gid,)).fetchone()[0]


def test_old_verify_call_always_failed(tmp_path):
    """수정 전 경로 재현: 예전 호출 형태는 어떤 규칙이든 exit 2 (판정이 아니라 사용법 오류)."""
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)}
    r = subprocess.run([sys.executable, str(VI), "--source-ref", "rule:미반영"], env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 2 and "unknown" in r.stderr
    assert '"--source-ref"' not in SUP.read_text(encoding="utf-8")   # 수정 후 판정 본문에 그 호출이 없다 (주석 설명만 남음)


def _trigger(tmp, m, rule, text):
    """recurrence-tracker 로 재발 기록 → 곧바로 그 규칙 REPAIR goal 생성 (운영처럼 기록과 goal 이 같은 순간)."""
    ev = json.loads(_rt(tmp, "record", rule, "dev", text).stdout)["event_id"]
    return ev, m.create_repair_goal(rule, "dev", 5, text)


def _fix(tmp, ev, cause, test):
    assert _rt(tmp, "root-cause", str(ev), "--cause", cause, "--evidence", "recurrence_tracker.py:30 패턴 실측 13/13",
               "--status", "confirmed").returncode == 0
    return _rt(tmp, "fix-result", str(ev), "passed", "--evidence", "감지 패턴 수정 · 회귀 시험", "--test", test)


def test_rule_repair_waits_instead_of_burning_retries_then_verifies_on_real_fix(tmp_path, monkeypatch):
    m = _sup(tmp_path, monkeypatch)
    ev, gid = _trigger(tmp_path, m, "미반영", "반영 안 됐잖아")
    for _ in range(6):                                   # 예전엔 이 주기 수면 retry 상한 FAILED
        m.advance_all_pending(trigger_source="stop_hook")
    st, retry, fr = _goal(m, gid)
    assert st == "BLOCKED" and retry == 0 and fr is None
    assert "해결 시험 통과 기록 없음" in _last_reason(m, gid)
    # 실제 해결 경로: 이 goal 을 만든 기록에 근본 원인 확정 → 연결 시험을 지금 실행해 통과 (가짜 VERIFIED 삽입 아님)
    (tmp_path / "t_fix.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    assert _fix(tmp_path, ev, "캐시 무효화 누락", "t_fix.py::test_ok").returncode == 0
    out = m.advance_all_pending(trigger_source="stop_hook")
    assert _goal(m, gid)[0] == "VERIFIED", out
    assert "해결 시험 통과" in _last_reason(m, gid)


def test_other_event_fix_does_not_verify_this_goal(tmp_path, monkeypatch):
    """R318 역방향: 같은 규칙이라도 이 goal 을 만든 기록이 아닌 다른 기록의 해결 통과로는 VERIFIED 금지."""
    m = _sup(tmp_path, monkeypatch)
    _, gid = _trigger(tmp_path, m, "미반영", "아직도 정렬이 안되어있어")
    with sqlite3.connect(str(m.DB)) as c:
        c.execute("UPDATE goals SET created_at=created_at-3600 WHERE goal_id=?", (gid,))   # 촉발 기록과 1시간 차이 = 다른 기록
    ev2 = json.loads(_rt(tmp_path, "record", "미반영", "dev", "반영 안 됐잖아").stdout)["event_id"]
    (tmp_path / "t_fix.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    assert _fix(tmp_path, ev2, "다른 원인", "t_fix.py::test_ok").returncode == 0
    for _ in range(3):
        m.advance_all_pending(trigger_source="stop_hook")
    assert _goal(m, gid)[:2] == ("BLOCKED", 0)


# ---------- R318 공통우회개발 감지: 금지 조항 ≠ 재발 지적 ----------

R318_PROHIBITIONS = [   # 운영 기록 중 지금 필터로도 잡히던 13건 원문 (recurrence_events 53~212)
    "개발: - 조사 생략 감지 - 요구사항 누락 방지 - 중복 구현 탐지 - 하드코딩 검사",
    "상태 머신을 재사용합니다. 별도의 상태 관리 시스템을 중복 구현하지 않습니다.",
    "Supervisor 재사용 - 새로운 병렬 상태 관리자 중복 구현 금지 - 운영 DB 마이그레이션 전에 백업",
    "Git·DB·Scheduler 보호 - 신규 파일과 중복 구현 최소화 - 근거 없는 추측 구현 금지",
    "Supervisor·Runner 유지 - 기존 기능 중복 구현 금지 - 실증 없는 완료 선언 금지",
    "검증된 사실로 보고하지 않기 - 이미 개발한 기능 중복 구현 금지 - 실제 테스트 없는 VERIFIED 금지",
    "기존 repair_sandbox.py를 재사용한 것은 중복 구현을 피했다는 점에서 좋은 결정입니다.",
    "Ledger·Goal DB·Git 보존 - 기존 기능 중복 구현 금지 - 변경 전 영향 분석",
    "Git·Ledger·운영 DB 보존 - 기존 정상 기능 중복 구현 금지 - 예시 패턴 추가로 범용성 주장 금지",
    "SAFE_PATTERNS 추가 금지 - 기존 정상 기능 중복 구현 금지 - 테스트 성공과 실제 운영 성공 구분",
    "이어서 진행한다. 이미 완료한 Phase 2·3 기능은 중복 구현하지 마라. 1. R75 자동 등록 오류 개선",
    "계정·인증 변경 금지 - 기존 정상 기능 중복 구현 금지 - 사용자 예시 하드코딩 금지",
    "자율 수정으로 완성하는 것이다. 기존 정상 기능을 중복 구현하지 않는다.",
]
R318_COMPLAINTS = ["또 중복 구현했네", "이거 중복 구현이잖아", "공통 함수 있는데 왜 우회했어 공통 유틸 우회",
                   "기존 거 있는데 새로 만들었어", "중복 구현된 거 같은데", "중복구현 했잖아"]


def _rt_pattern():
    import re
    sp = importlib.util.spec_from_file_location("rt318", ROOT / ".claude" / "hooks" / "prompt" / "recurrence_tracker.py")
    sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "prompt"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return re.compile(m.PATTERNS["dev"]["공통우회개발"], re.I)


def test_common_bypass_prohibition_clauses_not_recurrence():
    pat = _rt_pattern()
    hit = [t for t in R318_PROHIBITIONS if pat.search(t)]
    assert hit == [], hit


def test_common_bypass_real_complaints_still_counted():
    pat = _rt_pattern()
    miss = [t for t in R318_COMPLAINTS if not pat.search(t)]
    assert miss == [], miss


def test_reopened_fix_does_not_verify(tmp_path, monkeypatch):
    """역방향: 해결 기록이 있어도 재발로 verified=0(REOPENED)·FIX_FAILED 면 통과시키지 않는다."""
    m = _sup(tmp_path, monkeypatch)
    gid = m.create_repair_goal("공통우회개발", "dev", 3)
    m.advance_all_pending()
    with sqlite3.connect(str(m.DB)) as c:
        c.execute("CREATE TABLE IF NOT EXISTS recurrence_improvements (improvement_id INTEGER PRIMARY KEY, rule_id TEXT, "
                  "status TEXT, verified INTEGER)")
        c.execute("INSERT INTO recurrence_improvements (rule_id, status, verified) VALUES ('공통우회개발','REOPENED',0)")
        c.execute("INSERT INTO recurrence_improvements (rule_id, status, verified) VALUES ('공통우회개발','VERIFIED',0)")
        c.execute("INSERT INTO recurrence_improvements (rule_id, status, verified) VALUES ('다른규칙','VERIFIED',1)")
    for _ in range(3):
        m.advance_all_pending()
    assert _goal(m, gid)[:2] == ("BLOCKED", 0)


def test_self_heal_repair_goal_not_hijacked(tmp_path, monkeypatch):
    """self-heal 수리 goal(Agent 수리 중 RUNNING)은 supervisor 가 REPAIRING 으로 바꾸지 않는다 (e43·e52 덮어쓰기 재현)."""
    m = _sup(tmp_path, monkeypatch)
    gid = m.create_goal("Self-Healing: goal #1 복구", max_retry=1, timeout_h=4, workflow_type="REPAIR",
                        source_ref="repair:orig_goal=1")
    m.advance(gid, "PLANNING", "agent repair start", "self-healing")
    m.advance(gid, "RUNNING", "agent repair start", "self-healing")
    for _ in range(3):
        m.advance_all_pending(trigger_source="stop_hook")
    assert _goal(m, gid)[:2] == ("RUNNING", 0)
    assert m.advance(gid, "VERIFIED", "agent fix · judge", "self-healing")   # 수리 성공 기록이 그대로 들어간다


def test_trigger_link_window_boundary(tmp_path, monkeypatch):
    """R318 숫자 경계: goal 과 촉발 기록은 ±5초까지만 같은 것으로 본다 (5초 = 연결 · 6초 = 다른 기록 · 대기)."""
    m = _sup(tmp_path, monkeypatch)
    (tmp_path / "t_fix.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    res = {}
    for gap in (5, 6):
        ev, gid = _trigger(tmp_path, m, f"미반영{gap}", "반영 안 됐잖아")
        with sqlite3.connect(str(m.DB)) as c:
            c.execute("UPDATE goals SET created_at=CAST(strftime('%s', (SELECT detected_at FROM recurrence_events WHERE id=?)) AS INTEGER)+? "
                      "WHERE goal_id=?", (ev, gap, gid))
        assert _fix(tmp_path, ev, f"원인 {gap}", "t_fix.py::test_ok").returncode == 0
        res[gap] = gid
    for _ in range(4):   # PENDING → PLANNING → RUNNING → 판정 (3주기 + 여유 1)
        m.advance_all_pending(trigger_source="stop_hook")
    assert _goal(m, res[5])[0] == "VERIFIED"
    assert _goal(m, res[6])[0] == "BLOCKED"
