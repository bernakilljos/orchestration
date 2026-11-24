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
