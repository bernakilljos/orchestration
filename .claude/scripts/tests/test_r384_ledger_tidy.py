"""R384 (2026-11-24) 원장 현행화 — 저장할 때마다 지난 세션 승인 대기 자동 정리 · PARTIAL 은 Claude 가 할 일이 있을 때만 «다음»."""
import importlib.util
import uuid
from datetime import datetime, timedelta
from pathlib import Path

_P = Path(__file__).resolve().parents[1] / "request-ledger.py"
_spec = importlib.util.spec_from_file_location("request_ledger_tidy", _P)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

NOW = datetime(2026, 11, 24, 12, 0, 0)


def _r(rid, status, sess, hours_ago, **kw):
    d = {"id": rid, "status": status, "session_id": sess,
         "ts": (NOW - timedelta(hours=hours_ago)).isoformat(timespec="seconds")}
    d.update(kw)
    return d


def test_stale_approval_from_ended_session_deferred_not_completed():
    old, cur = uuid.uuid4().hex, uuid.uuid4().hex          # 세션 이름은 매번 무작위 (하드코딩 X)
    data = {"requests": [
        _r("R1", "approval_required", old, 48),             # 지난 세션 · 24h+ → 보류
        _r("R2", "approval_required", uuid.uuid4().hex, 2),  # 다른 세션 · 24h 미만 → 그대로 (같은 세션이면 그 세션 = 활성)
        _r("R3", "approval_required", cur, 72),             # 현재 세션 → 그대로 (오래돼도)
        _r("R4", "verified", old, 99, verification="PARTIAL"),   # 승인 대기 아님 → 그대로
        _r("R5", "pending", cur, 0),
    ]}
    assert m.expire_stale_approvals(data, NOW) == ["R1"]
    st = {r["id"]: r["status"] for r in data["requests"]}
    assert st == {"R1": "deferred", "R2": "approval_required", "R3": "approval_required",
                  "R4": "verified", "R5": "pending"}
    r1 = data["requests"][0]
    assert "완료 아님" in r1["deferred_reason"] and r1["deferred_at"]
    assert m.expire_stale_approvals(data, NOW) == []        # 두 번째 호출 = 변화 없음 (멱등)


def test_partial_without_claude_items_is_waiting_external_not_next():
    s = uuid.uuid4().hex
    cur = _r("R9", "pending", s, 0)
    reqs = [
        _r("R6", "verified", s, 1, verification="PARTIAL"),                                    # 항목 없음 → 외부
        _r("R7", "verified", s, 1, verification="PARTIAL",
           items=[{"i": 1, "state": "open", "owner": "external", "text": "x"}]),               # 외부 항목만 → 외부
        _r("R8", "verified", s, 1, verification="PARTIAL",
           items=[{"i": 1, "state": "open", "owner": "claude", "text": "y"}]),                 # Claude 할 일 → 다음
        cur,
    ]
    q = m.queue_view(reqs, cur)
    assert q["remaining"] == 4                               # 미완료 수는 숨기지 않음
    assert q["running"] == "R9"
    assert [n for n in q["next"]] == ["R8(0/1)부분"]
    assert sorted(w.split()[0] for w in q["waiting"]) == ["R6", "R7"]
    assert all(w.endswith("외부") for w in q["waiting"])


def test_r375_review2_active_session_not_assumed_from_last_item_and_timezone():
    """R375 리뷰 2: 마지막 배열 항목 ≠ 현재 세션 · 시간대 포함 시각 · 해석 불가 시각 · 만료 기간 정본."""
    a, b = uuid.uuid4().hex, uuid.uuid4().hex
    data = {"requests": [
        _r("R1", "approval_required", a, 30),                 # 세션 a: 30h 전 승인 대기
        _r("R2", "pending", a, 1),                            # 세션 a 는 1h 전에도 활동 → 활성 (보류 X)
        _r("R3", "approval_required", b, 30),                 # 세션 b: 활동 없음 → 보류 (배열 마지막이어도)
    ]}
    tz_old = (NOW - timedelta(hours=40)).astimezone().isoformat(timespec="seconds")   # 시간대 포함 시각
    data["requests"].append({"id": "R4", "status": "approval_required", "session_id": uuid.uuid4().hex, "ts": tz_old})
    data["requests"].append({"id": "R5", "status": "approval_required", "session_id": uuid.uuid4().hex, "ts": "언제"})
    assert sorted(m.expire_stale_approvals(data, NOW)) == ["R3", "R4"]
    assert {r["id"]: r["status"] for r in data["requests"]}["R5"] == "approval_required"   # 해석 불가 = 그대로
    assert m._stale_sec() == m._approval_ttl_sec() > 0                              # 정본(approval-gate) 에서 읽음


# ── R375 2차 검토 P1 (2026-11-25): 승인 만료 기간 단일 출처 = lib/config.py (소스 정규식 읽기 제거) ──
def _fresh(name, path, monkeypatch, **env):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import importlib.util as u
    sp = u.spec_from_file_location(name, path)
    m = u.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def test_r375_ttl_single_source_and_env_override(monkeypatch):
    import sys as _s
    kit = Path(__file__).resolve().parents[3] / ".claude" / "scripts"
    monkeypatch.delenv("LEDGER_APPROVAL_STALE_SEC", raising=False)
    monkeypatch.delenv("CLAUDE_KIT_APPROVAL_REQUEST_TTL_SEC", raising=False)
    led = _fresh("led_ttl1", kit / "request-ledger.py", monkeypatch)
    gate = _fresh("gate_ttl1", kit / "approval-gate.py", monkeypatch)
    assert led._approval_ttl_sec() == gate.REQUEST_TTL_SEC == 86400          # 기본값 같음
    for val, want in (("7200", 7200), ("0", 86400), ("-5", 86400), ("abc", 86400)):   # 정책 변경 · 잘못된 값 = 기본
        monkeypatch.setenv("CLAUDE_KIT_APPROVAL_REQUEST_TTL_SEC", val)
        g2 = _fresh(f"gate_ttl_{val}", kit / "approval-gate.py", monkeypatch)
        assert led._approval_ttl_sec() == g2.REQUEST_TTL_SEC == want, val    # 두 쪽이 항상 같은 값


def test_r375_ttl_config_failure_is_reported_not_silent(monkeypatch, capsys, tmp_path):
    kit = Path(__file__).resolve().parents[3] / ".claude" / "scripts"
    monkeypatch.delenv("LEDGER_APPROVAL_STALE_SEC", raising=False)
    led = _fresh("led_ttl2", kit / "request-ledger.py", monkeypatch)
    fake = tmp_path / "request-ledger.py"
    fake.write_text("", encoding="utf-8")
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "config.py").write_text("raise RuntimeError('broken policy')", encoding="utf-8")
    monkeypatch.setattr(led, "__file__", str(fake))
    monkeypatch.setitem(led._approval_ttl_sec.__globals__, "__file__", str(fake))
    assert led._approval_ttl_sec() == 86400
    assert "broken policy" in capsys.readouterr().err                         # 조용히 대체하지 않음


def test_r375_gate_ignores_foreign_config_module(monkeypatch):
    import sys as _s
    import types
    kit = Path(__file__).resolve().parents[3] / ".claude" / "scripts"
    monkeypatch.setitem(_s.modules, "config", types.ModuleType("config"))   # 다른 패키지의 config 가 먼저 불려 있어도
    g = _fresh("gate_ttl_foreign", kit / "approval-gate.py", monkeypatch)
    assert g.REQUEST_TTL_SEC > 0


def test_r375_statusline_import_does_not_read_policy(monkeypatch):
    kit = Path(__file__).resolve().parents[3] / ".claude" / "scripts"
    led = _fresh("led_ttl3", kit / "request-ledger.py", monkeypatch)
    assert led.APPROVAL_STALE_SEC == 0                                          # 불러오기만 해선 정책을 읽지 않음 (지연 읽기 유지)
