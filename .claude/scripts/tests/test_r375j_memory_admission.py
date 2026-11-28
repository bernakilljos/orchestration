"""R375 메모리 압박 P0 — 공통 자원 admission (repair_sandbox.memory_admission) 표적 시험.
정상·저메모리·회복·진동(히스테리시스)·작업 비용·여유 중복 소비·측정 불가·정책값 검증·상태 기록(잠금·미래 시각)·
호출부(broker 접수 중 재판정·회귀 게이트 절대 여유·run_dag wave 재판정) 정합. (2026-11-28 독립 검토 864fda9d 반례 포함)"""
import json
import sys
import threading
from pathlib import Path

import pytest

LIB = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(LIB))
import repair_sandbox as sb  # noqa: E402

POL = {"min_commit_free_gb": 2, "max_commit_percent": 90, "mem_constrained_percent": 80, "min_phys_free_gb": 1,
       "mem_resume_percent": 75, "agent_max_parallel": 3, "mem_constrained_parallel": 1, "estimate_margin": 1.2,
       "agent_est_gb": 1.0}


def cm(pct, free=8.0, phys=None):
    d = {"measured": True, "percent": pct, "free_gb": free, "used_gb": 20.0, "limit_gb": 25.0}
    if phys is not None:
        d["phys_free_gb"] = phys
    return d


def walk(seq, pol=POL):
    prior, out = None, []
    for p in seq:
        prior = sb.memory_admission(cm(p), pol, prior)["level"]
        out.append(prior)
    return out


def test_levels_and_parallel():
    assert [sb.memory_admission(cm(p), POL)["level"] for p in (50, 80, 89.9, 90.0, 90.5)] == \
        ["normal", "constrained", "constrained", "constrained", "blocked"]          # 90% 경계 = 초과만 blocked
    a = sb.memory_admission(cm(50), POL)
    assert a["max_parallel"] == 3 and not a["defer_optional"]
    c = sb.memory_admission(cm(85), POL)
    assert c["max_parallel"] == 1 and c["defer_optional"]
    assert sb.memory_admission(cm(95), POL)["max_parallel"] == 0


def test_hysteresis_prevents_oscillation():
    assert walk([70, 81, 79, 78, 76, 74]) == ["normal", "constrained", "constrained", "constrained", "constrained", "normal"]
    assert walk([91, 89, 86, 84, 76, 74]) == ["blocked", "blocked", "blocked", "constrained", "constrained", "normal"]


def test_old_gate_oscillated_new_gate_holds():
    """역검증: 예전 memory_gate(상한 단독)는 91→89→91 에서 거부·허용·거부를 번갈아 냈다 · 지금은 회복 전까지 보류."""
    def old_gate(c):   # 055e4fd5 이전 정의 재현
        return c["free_gb"] < 2 or c["percent"] > 90
    assert [old_gate(cm(p)) for p in (91, 89, 91)] == [True, False, True]
    assert walk([91, 89, 91]) == ["blocked", "blocked", "blocked"]


def test_low_percent_but_low_free_or_phys_blocks():
    """검토 반례: 퍼센트가 낮아도 commit 여유 1GB · 물리 RAM 부족이면 blocked (예전 broker·게이트는 퍼센트만 봤다)."""
    assert sb.memory_admission(cm(40, free=1.0), POL)["level"] == "blocked"
    a = sb.memory_admission(cm(40, free=8.0, phys=0.5), POL)
    assert a["level"] == "blocked" and "물리" in a["reason"]
    assert sb.memory_admission(cm(40, free=8.0, phys=4.0), POL)["level"] == "normal"


def test_job_cost_and_duplicate_consumption_budget():
    # 작업 비용 0 이면 여유 2.5GB 도 normal · 작업당 1GB(×1.2) 이면 2.5-1.2 < 2 = blocked
    assert sb.memory_admission(cm(60, free=2.5), POL, est_gb=0)["level"] == "normal"
    a = sb.memory_admission(cm(60, free=2.5), POL, est_gb=1.0)
    assert a["level"] == "blocked" and a["max_parallel"] == 0
    # 여유 5GB · 작업당 1.2GB → (5-2)/1.2 = 2개만 동시에 (정책 3개라도 같은 여유를 3번 쓰지 않게)
    assert sb.memory_admission(cm(60, free=5.0), POL, est_gb=1.0)["max_parallel"] == 2
    # 물리 여유도 예산: 물리 2.5GB · 최소 1 → (2.5-1)/1.2 = 1개
    assert sb.memory_admission(cm(60, free=20.0, phys=2.5), POL, est_gb=1.0)["max_parallel"] == 1


def test_unknown_keeps_essential_limits_optional():
    a = sb.memory_admission({"measured": False, "reason": "x"}, POL)
    assert a["level"] == "unknown" and a["max_parallel"] == 1 and a["defer_optional"]   # 최대 병렬 복귀 X
    assert sb.memory_gate(POL, {"measured": False}) is None                            # 필수 작업은 계속


def test_policy_values_validated(monkeypatch):
    bad = {**POL, "max_commit_percent": float("nan"), "min_commit_free_gb": -3, "agent_max_parallel": "x",
           "mem_resume_percent": 85}
    t = sb.admission_thresholds(bad)
    assert t["block_pct"] == 90 and t["min_free_gb"] == 2 and t["max_parallel"] == 3     # 기본값으로
    assert t["resume_pct"] == 80                                                         # 재개 > 진입 = 진입선으로
    assert {"max_commit_percent", "min_commit_free_gb", "agent_max_parallel"} <= set(t["invalid"])
    monkeypatch.setenv("ORCA_MEM_CONSTRAINED_PERCENT", "70")
    assert sb.memory_admission(cm(72), POL)["level"] == "constrained"
    monkeypatch.setenv("ORCA_MAX_COMMIT_PERCENT", "60")                                   # 상한 < 진입선 = 진입선으로
    assert sb.admission_thresholds(POL)["block_pct"] == 70


def test_state_persists_across_calls(tmp_path, monkeypatch):
    st = tmp_path / "adm.json"
    monkeypatch.setenv("ORCA_MEM_ADMISSION_STATE", str(st))
    a = sb.admission_now(cm(91), POL, est_gb=0)
    assert a["level"] == "blocked" and a["state_written"]
    assert json.loads(st.read_text(encoding="utf-8"))["level"] == "blocked"
    b = sb.admission_now(cm(88), POL, est_gb=0)
    assert b["level"] == "blocked" and b["prior"] == "blocked"
    g = sb.memory_gate(POL, cm(88), est_gb=0)
    assert g and g["deferred"] and "회복 대기" in g["reason"]


def test_corrupt_stale_future_state_ignored(tmp_path, monkeypatch):
    import time
    st = tmp_path / "adm.json"
    monkeypatch.setenv("ORCA_MEM_ADMISSION_STATE", str(st))
    st.write_text("{깨짐", encoding="utf-8")
    assert sb.admission_now(cm(50), POL, est_gb=0)["level"] == "normal"
    for ts, lvl in ((0, "blocked"), (time.time() + 3600, "blocked"), (time.time(), "weird")):   # 만료·미래 시각·모르는 값
        st.write_text(json.dumps({"level": lvl, "ts": ts}), encoding="utf-8")
        a = sb.admission_now(cm(88), POL, est_gb=0)
        assert a["prior"] is None and a["level"] == "constrained"


def test_concurrent_threads_and_lock_unavailable(tmp_path, monkeypatch):
    st = tmp_path / "adm.json"
    monkeypatch.setenv("ORCA_MEM_ADMISSION_STATE", str(st))
    errs, out = [], []

    def worker(p):
        try:
            out.append(sb.admission_now(cm(p), POL, est_gb=0)["level"])
        except Exception as e:  # noqa: BLE001
            errs.append(e)
    ths = [threading.Thread(target=worker, args=(50 + i % 3,)) for i in range(12)]
    [t.start() for t in ths]
    [t.join() for t in ths]
    assert not errs and len(out) == 12 and set(out) == {"normal"}
    assert not list(tmp_path.glob("*.tmp"))                                        # 스레드 간 tmp 충돌·잔여 없음
    import proc_lock
    fd = proc_lock.try_lock(str(st) + ".lock")                                     # 다른 프로세스가 잠금을 쥔 상황
    try:
        a = sb.admission_now(cm(91), POL, est_gb=0)
        assert a["level"] == "blocked" and a["state_written"] is False             # 판정은 하되 기록 안 함
    finally:
        proc_lock.release(fd)


def test_state_not_written_under_pytest_unless_explicit(monkeypatch):
    monkeypatch.delenv("ORCA_MEM_ADMISSION_STATE", raising=False)
    assert sb._admission_state_path() is None
    monkeypatch.delenv("PYTEST_CURRENT_TEST")
    p = sb._admission_state_path()
    assert p is not None and p.name.endswith("memory-admission.json")
    assert ("_memory-admission" in p.name) == (not sb.IS_OPERATIONAL_ROOT)


def test_broker_uses_full_measurement_and_rechecks(monkeypatch, tmp_path):
    import broker as b
    monkeypatch.delenv("ORCA_MEM_ADMISSION_STATE", raising=False)
    assert b._memory_level(cm(50)) == "normal" and b._memory_level(cm(85)) == "constrained"
    assert b._memory_level(cm(40, free=1.0)) == "blocked"                 # 예전: 퍼센트만 넘겨 normal 이었음
    assert b._memory_level({"measured": False}) == "unknown"
    gc = b.gc(tmp_path, force=True, cm={"measured": False})
    assert gc == {"ran": False, "reason": "memory None%"}                 # 측정 불가 = 선택 작업(gc) 미룸


def test_regression_gate_wait_blocks_on_absolute_shortage(monkeypatch):
    import independent_verifier as iv
    monkeypatch.setenv("ORCA_GATE_MEM_WAIT_SEC", "0")
    monkeypatch.setattr(sb, "commit_memory", lambda: cm(40, free=1.0))      # 낮은 퍼센트 + 여유 1GB
    res = {}
    msg = iv._wait_memory_for_heavy(res)
    assert msg and "절대 여유 부족" in msg                                   # 예전: 40% < 80 이라 즉시 진행
    monkeypatch.setattr(sb, "commit_memory", lambda: cm(65, free=8.0))
    monkeypatch.setenv("ORCA_MEM_CONSTRAINED_PERCENT", "60")
    assert iv._wait_memory_for_heavy({}) is None                              # 60~90%: 대기 만료 후 순차 진행 (사용자 정책 유지)
    monkeypatch.setenv("ORCA_MAX_COMMIT_PERCENT", "64")
    assert "64" in (iv._wait_memory_for_heavy({}) or "")


def _dag(monkeypatch, tmp_path, seq, max_parallel=None, wait="0"):
    import agent_registry as ar
    it = iter(seq)
    last = {"v": seq[-1]}

    def fake_adm(*a, **k):
        v = next(it, last["v"])
        return {"max_parallel": v, "level": "blocked" if v == 0 else "normal"}
    monkeypatch.setattr(sb, "admission_now", fake_adm)
    monkeypatch.setenv("ORCA_DAG_MEM_WAIT_SEC", wait)
    ag = {"name": "a", "tools": ["Read"], "model": "m", "body": "", "selection": "t"}
    monkeypatch.setattr(ar, "load_agents", lambda: [ag])
    monkeypatch.setattr(ar, "select_agent", lambda *a, **k: ag)
    monkeypatch.setattr(ar, "_changed_files", lambda cwd: [])
    calls = []
    tasks = [{"id": f"t{i}", "needs": ["read"], "prompt": "p", "allow_paths": [f"f{i}"],
              "depends_on": ([f"t{i-1}"] if i in (3, 4) else [])} for i in range(5)]
    r = ar.run_dag(tasks, str(tmp_path), max_parallel=max_parallel,
                   dispatch=lambda *a, **k: calls.append(1) or {"ok": True, "result": ""})
    return r, calls


def test_run_dag_rechecks_each_wave_and_defers_when_blocked(monkeypatch, tmp_path):
    # wave1 = normal 3 → wave2 판정 blocked 지속 → 남은 작업 deferred (예전: 시작 때 한 번 판정 · blocked 를 1 로 바꿔 실행)
    r, calls = _dag(monkeypatch, tmp_path, [3, 0])
    assert [len(w) for w in r["waves"]] == [3] and len(calls) == 3
    deferred = [k for k, v in r["results"].items() if v.get("deferred")]
    assert deferred and all("admission blocked" in r["results"][k]["reason"] for k in deferred)
    assert [m["start"] for m in r["memory_admission"]][:2] == [3, 0]


def test_run_dag_explicit_parallel_is_cap_not_bypass(monkeypatch, tmp_path):
    r, calls = _dag(monkeypatch, tmp_path, [1, 1, 1, 1, 1], max_parallel=3)     # 명시 3 이어도 admission 1 이면 1개씩
    assert max(len(w) for w in r["waves"]) == 1 and len(calls) == 5
    r2, _ = _dag(monkeypatch, tmp_path, [3, 3, 3], max_parallel=2)              # admission 3 · 명시 2 → 2
    assert max(len(w) for w in r2["waves"]) == 2


def test_run_dag_waits_then_resumes(monkeypatch, tmp_path):
    import agent_registry as ar
    monkeypatch.setattr(ar.time, "sleep", lambda s: None)
    r, calls = _dag(monkeypatch, tmp_path, [0, 0, 2], wait="60")                # 대기 중 회복 → 재개
    assert len(calls) == 5 and not any(v.get("deferred") for v in r["results"].values())
