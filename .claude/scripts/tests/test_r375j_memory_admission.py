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


def cm(pct, free=8.0, phys=8.0):
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


# ── 2026-11-28 2차 독립 검토 f2376021 반례 ──────────────────────────────────────
FULL = {"measured": True, "percent": 50.0, "free_gb": 4.5, "phys_free_gb": 8.0, "used_gb": 20.0, "limit_gb": 25.0}


def _book(monkeypatch, tmp_path):
    p = tmp_path / "mem-res.json"
    monkeypatch.setenv("ORCA_MEM_RESERVATIONS", str(p))
    monkeypatch.delenv("ORCA_MEM_ADMISSION_STATE", raising=False)
    return p


def test_cross_process_reservation_prevents_double_spend(monkeypatch, tmp_path):
    """독립 프로세스 2개가 같은 여유를 각각 소비하던 반례 — 자식이 예약을 쥔 동안 부모는 시작 0 · 자식이 죽으면(OOM·강제 종료) 자동 만료."""
    import subprocess
    import time
    p = _book(monkeypatch, tmp_path)
    child = ("import sys,time,json;sys.path.insert(0,sys.argv[1]);import repair_sandbox as sb;"
             "a=sb.reserve_memory(3,'child',pol=json.loads(sys.argv[2]),cm=json.loads(sys.argv[3]));"
             "print(len(a['granted']),flush=True);time.sleep(60)")
    proc = subprocess.Popen([sys.executable, "-c", child, str(LIB), json.dumps(POL), json.dumps(FULL)],
                            stdout=subprocess.PIPE, text=True)
    try:
        assert proc.stdout.readline().strip() == "2"                 # (4.5−2)÷1.2 = 2
        a = sb.reserve_memory(3, "parent", pol=POL, cm=FULL)
        assert a["granted"] == [] and a["level"] == "blocked" and a["reserved_gb_others"] == 2.4
        assert sb.memory_admission(FULL, POL)["max_parallel"] == 2    # 예약 장부 없이 판정하면 2 를 또 줬다 (예전 동작)
    finally:
        proc.kill()
        proc.wait()
    time.sleep(0.2)
    b = sb.reserve_memory(3, "parent", pol=POL, cm=FULL)
    assert len(b["granted"]) == 2                                     # 죽은 주인의 예약은 제외
    assert sb.release_memory(b["granted"]) and json.loads(p.read_text(encoding="utf-8"))["reservations"] == {}


def test_reservation_pid_reuse_ttl_only_when_unverifiable_and_essential(monkeypatch, tmp_path):
    """3차 검토: 살아 있는 소유자의 예약은 TTL·시계 이동과 무관하게 유지 · TTL 은 소유 상태 조회 불가일 때만 · PID 재사용 = 제외."""
    import os
    import time
    p = _book(monkeypatch, tmp_path)
    now = time.time()
    me = sb._proc_start(os.getpid())
    ghost = 999999                                                  # 조회 불가로 만들 PID
    real = sb._proc_start
    monkeypatch.setattr(sb, "_proc_start", lambda pid: None if int(pid) == ghost else real(pid))
    base = {"gb": 2.4, "ttl": 600, "owner": "x"}
    p.write_text(json.dumps({"reservations": {
        "reused": dict(base, pid=os.getpid(), start=(me or 0) - 1000, ts=now),   # 같은 PID · 다른 시작 시각 = 재사용 → 제외
        "unk_old": dict(base, pid=ghost, start=None, ts=now - 700),            # 조회 불가 + TTL 지남 → 제외
        "unk_future": dict(base, pid=ghost, start=None, ts=now + 3600),        # 조회 불가 + 미래 시각 → 제외
        "bad": {"pid": "x"}}}), encoding="utf-8")
    a = sb.reserve_memory(3, "t", pol=POL, cm=FULL)
    assert a["reserved_gb_others"] == 0 and len(a["granted"]) == 2
    d = json.loads(p.read_text(encoding="utf-8"))["reservations"]
    for rid in a["granted"]:                                        # 내 예약을 TTL 지난·미래 시각으로 바꿔도 살아 있으면 유지
        d[rid]["ts"] = now - 99999
    p.write_text(json.dumps({"reservations": d}), encoding="utf-8")
    assert set(sb._live_mem({"reservations": d}, time.time())) == set(a["granted"])
    b = sb.reserve_memory(1, "fix", essential=True, pol=POL, cm=FULL)  # 선택 작업 예약 2.4 가 필수 복구를 굶기지 않음
    assert len(b["granted"]) == 1
    c = sb.reserve_memory(1, "opt", pol=POL, cm=FULL)                 # 선택 작업은 필수 예약까지 합산 → 0
    assert c["granted"] == []
    sb.release_memory(a["granted"] + b["granted"])


def test_observed_cost_raises_estimate(monkeypatch, tmp_path):
    _book(monkeypatch, tmp_path)
    for _ in range(5):
        g = sb.reserve_memory(1, "t", pol=POL, cm=dict(FULL, free_gb=20.0, phys_free_gb=20.0))["granted"]
        sb.release_memory(g, observed_gb=3.0)
    a = sb.reserve_memory(3, "t", pol=POL, cm=dict(FULL, free_gb=20.0, phys_free_gb=20.0))
    assert a["est_gb_used"] == 3.0 and len(a["granted"]) == 3         # (20−2)÷3.6 = 5 → 상한 3
    sb.release_memory(a["granted"], observed_gb=float("nan"))          # 비정상 관측값은 기록 안 함


@pytest.mark.parametrize("bad", [{"free_gb": float("nan")}, {"phys_free_gb": float("inf")}, {"percent": 120},
                                 {"free_gb": None}, {"phys_free_gb": "x"}, {"percent": float("nan")}])
def test_partial_or_nonfinite_measurement_is_unknown(bad):
    m = dict(FULL, **bad)
    a = sb.memory_admission(m, dict(POL, mem_constrained_parallel=5, agent_max_parallel=2))
    assert a["level"] == "unknown" and a["max_parallel"] == 2 and a["measure_invalid"]   # unknown 도 전체 상한 이하
    assert sb.memory_gate(POL, m) is None                              # 필수 작업은 계속


def test_missing_field_and_bad_est_and_stale_ts():
    m = dict(FULL)
    m.pop("phys_free_gb")
    assert sb.memory_admission(m, POL)["level"] == "unknown"           # 예전: 물리 여유 누락 = 정상 통과
    assert sb.memory_admission(dict(FULL, ts=0), POL)["level"] == "unknown"
    a = sb.memory_admission(FULL, POL, est_gb=float("nan"))
    assert a["level"] == "normal" and "est_gb" in a["thresholds"]["invalid"]


def test_broker_cap_follows_level_change_mid_intake(monkeypatch, tmp_path):
    """normal 로 시작해 접수 중 constrained 로 바뀌면 누적 5건에서 멈춤 (예전: 최초 cap 50 유지)."""
    import broker as b
    seq = iter([cm(50)] + [cm(50)] * 2 + [cm(85)] * 100)
    monkeypatch.setattr(b, "_memory_cm", lambda: next(seq))
    monkeypatch.setattr(b, "_memory_level", lambda c: "constrained" if c["percent"] >= 80 else "normal")
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    for i in range(12):
        (inbox / f"r{i:02}.json").write_text("{}", encoding="utf-8")
    taken = []
    monkeypatch.setattr(b, "_guard", lambda r: None)
    lk = tmp_path / "lock"
    lk.write_text("", encoding="utf-8")
    monkeypatch.setattr(b, "_lock", lambda r: lk)
    monkeypatch.setattr(b, "_config", lambda r: {"inbox": str(inbox)})
    monkeypatch.setattr(b, "_gate", lambda r: None)
    monkeypatch.setattr(b, "_Git", lambda r: None)
    monkeypatch.setattr(b, "_recover", lambda *a: [])
    monkeypatch.setattr(b, "_intake", lambda r, c, g, gi, src, log: taken.append(src.stem))
    monkeypatch.setattr(b, "_execute_approved", lambda *a: [])
    gc_cm = []
    monkeypatch.setattr(b, "gc", lambda *a, **k: gc_cm.append(k.get("cm")) or {"ran": False})
    log = b.process(tmp_path)
    assert len(taken) == 5 and any("상한 5" in (x.get("reason") or "") for x in log)
    assert gc_cm == [None]                                              # gc 는 승인 실행 뒤 새로 측정


def test_gc_pct_only_compat_uses_full_measurement(monkeypatch, tmp_path):
    import broker as b
    monkeypatch.setattr(b, "_memory_cm", lambda: {"measured": False})
    assert b.gc(tmp_path, pct=10, force=True)["ran"] is False          # 퍼센트만으로 정상 판정 X → 측정 불가 = 미룸


def test_run_dag_releases_reservation_on_failure_and_bad_wait(monkeypatch, tmp_path):
    import agent_registry as ar
    p = _book(monkeypatch, tmp_path)
    monkeypatch.setattr(sb, "commit_memory", lambda: dict(FULL, free_gb=20.0, phys_free_gb=20.0))
    monkeypatch.setattr(sb, "_policy", lambda: dict(POL, dag_mem_wait_sec=0))
    monkeypatch.setenv("ORCA_DAG_MEM_WAIT_SEC", "nan")                 # 예전: NaN 이면 blocked 때 영원히 대기
    ag = {"name": "a", "tools": ["Read"], "model": "m", "body": "", "selection": "t"}
    monkeypatch.setattr(ar, "load_agents", lambda: [ag])
    monkeypatch.setattr(ar, "select_agent", lambda *a, **k: ag)
    monkeypatch.setattr(ar, "_changed_files", lambda cwd: [])
    seen = []

    def boom(*a, **k):
        seen.append(len(json.loads(p.read_text(encoding="utf-8"))["reservations"]))
        raise RuntimeError("start failed")
    tasks = [{"id": f"t{i}", "needs": ["read"], "prompt": "p", "allow_paths": [f"f{i}"]} for i in range(2)]
    r = ar.run_dag(tasks, str(tmp_path), dispatch=boom)
    assert seen and max(seen) >= 1 and all(v["status"] == "failed" for v in r["results"].values())
    assert json.loads(p.read_text(encoding="utf-8"))["reservations"] == {}      # 시작 실패에도 해제
    monkeypatch.setattr(sb, "commit_memory", lambda: dict(FULL, free_gb=1.0))  # blocked + 대기값 NaN → 정책 0초 → 즉시 deferred
    r2 = ar.run_dag(tasks, str(tmp_path), dispatch=boom)
    assert all(v.get("deferred") for v in r2["results"].values())


def test_partial_measurement_never_looser_than_known_fields():
    """부분 측정을 unknown 으로 풀어 주면 이미 확정된 부족을 놓친다 — 유효 필드만으로 blocked 면 blocked."""
    for m in ({"measured": True, "percent": 50.0, "free_gb": 0.5},                      # 물리 여유 누락 + commit 여유 부족
              {"measured": True, "percent": 95.0, "free_gb": float("nan")},             # 여유 NaN + 95%
              {"measured": True, "percent": 50.0, "free_gb": 8.0, "phys_free_gb": 0.2, "used_gb": None}):
        m2 = dict(m)
        a = sb.memory_admission(m2, POL)
        assert a["level"] in ("blocked",) or not sb._measure_problems(m2), (m, a)
        assert a["max_parallel"] == 0 or not sb._measure_problems(m2)
    assert sb.memory_admission({"measured": True, "percent": 50.0, "free_gb": 8.0}, POL)["level"] == "unknown"


# ── 2026-11-28 3차 독립 검토 0d49fa5e 반례 ──────────────────────────────────────
def _own(gb=2.4, **k):
    import os
    import time
    return dict({"pid": os.getpid(), "start": sb._proc_start(os.getpid()), "gb": gb, "ttl": 600, "ts": time.time(),
                 "owner": "other", "pids": []}, **k)


def test_lock_failure_blocks_optional_but_essential_gets_limited_budget(monkeypatch, tmp_path):
    import proc_lock
    p = _book(monkeypatch, tmp_path)
    fd = proc_lock.try_lock(str(p) + ".lock")                       # 다른 쪽이 장부 잠금을 쥔 상태
    try:
        a = sb.reserve_memory(3, "opt", pol=POL, cm=FULL)
        assert a["max_parallel"] == 0 and a["granted"] == [] and a["book"] == "failed" and "잠금" in a["book_problem"]
        e = sb.reserve_memory(3, "fix", essential=True, pol=POL, cm=FULL)
        assert len(e["granted"]) == 1 and e["granted"][0].startswith("unbooked-")   # 필수 = 제한 예산 1 · 장부 밖 표시
        assert sb.release_memory(e["granted"])
    finally:
        proc_lock.release(fd)


def test_corrupt_or_unreadable_book_blocks_optional_and_is_preserved(monkeypatch, tmp_path):
    p = _book(monkeypatch, tmp_path)
    p.write_text("{not json", encoding="utf-8")
    a = sb.reserve_memory(2, "opt", pol=POL, cm=FULL)
    assert a["granted"] == [] and "손상" in a["book_problem"]
    assert p.read_text(encoding="utf-8") == "{not json"             # 손상 장부를 덮어쓰지 않음 (진단 보존)
    p.write_text(json.dumps({"reservations": []}), encoding="utf-8")   # 형식 오류도 손상
    assert sb.reserve_memory(2, "opt", pol=POL, cm=FULL)["granted"] == []
    p.unlink()
    assert len(sb.reserve_memory(2, "opt", pol=POL, cm=FULL)["granted"]) == 2   # 파일 없음 = 빈 장부 (정상)


def test_write_failure_yields_no_reservation(monkeypatch, tmp_path):
    p = _book(monkeypatch, tmp_path)
    monkeypatch.setattr(sb._MemBook, "write", lambda self, d: (_ for _ in ()).throw(OSError("disk")))
    a = sb.reserve_memory(2, "opt", pol=POL, cm=FULL)
    assert a["granted"] == [] and a["max_parallel"] == 0 and "쓰기" in a["book_problem"]
    assert not p.exists()


def test_run_dag_does_not_dispatch_without_reservation(monkeypatch, tmp_path):
    import agent_registry as ar
    import proc_lock
    p = _book(monkeypatch, tmp_path)
    monkeypatch.setattr(sb, "commit_memory", lambda: dict(FULL, free_gb=20.0, phys_free_gb=20.0))
    monkeypatch.setattr(sb, "_policy", lambda: dict(POL, dag_mem_wait_sec=0))
    ag = {"name": "a", "tools": ["Read"], "model": "m", "body": "", "selection": "t"}
    monkeypatch.setattr(ar, "load_agents", lambda: [ag])
    monkeypatch.setattr(ar, "select_agent", lambda *a, **k: ag)
    monkeypatch.setattr(ar, "_changed_files", lambda cwd: [])
    calls = []
    fd = proc_lock.try_lock(str(p) + ".lock")
    try:
        r = ar.run_dag([{"id": "t0", "needs": ["read"], "prompt": "p"}], str(tmp_path),
                       dispatch=lambda *a, **k: calls.append(1) or {"ok": True})
    finally:
        proc_lock.release(fd)
    assert calls == [] and r["results"]["t0"].get("deferred")       # 예전: 예약 실패여도 n_start 만큼 실행


def test_child_alive_keeps_reservation_after_parent_exit(monkeypatch, tmp_path):
    import os
    import subprocess
    import time
    p = _book(monkeypatch, tmp_path)
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    time.sleep(0.2)
    me = {"pid": os.getpid(), "start": sb._proc_start(os.getpid())}
    book = {"reservations": {"r1": {"pid": dead.pid, "start": 1.0, "gb": 2.4, "ttl": 1, "ts": time.time() - 999,
                                    "pids": [me]},                        # 부모 종료 · 자식(여기선 이 프로세스) 생존 · TTL 지남
                             "r2": {"pid": dead.pid, "start": 1.0, "gb": 2.4, "ttl": 600, "ts": time.time(), "pids": []}}}
    assert set(sb._live_mem(book, time.time())) == {"r1"}
    g = sb.reserve_memory(1, "t", pol=POL, cm=dict(FULL, free_gb=20.0, phys_free_gb=20.0))["granted"]
    assert sb.update_reservations(g, pids=[os.getpid()], used_gb=0.5)
    e = json.loads(p.read_text(encoding="utf-8"))["reservations"][g[0]]
    assert e["used_gb"] == 0.5 and e["pids"][0]["pid"] == os.getpid()
    sb.release_memory(g)


def test_reservation_ids_unique_in_same_ms(monkeypatch, tmp_path):
    _book(monkeypatch, tmp_path)
    ids = []
    for _ in range(20):
        ids += sb.reserve_memory(3, "t", pol=dict(POL, agent_max_parallel=3), cm=dict(FULL, free_gb=500.0, phys_free_gb=500.0))["granted"]
    assert len(ids) == len(set(ids)) == 60
    sb.release_memory(ids)


def test_executor_failure_releases_reservations(monkeypatch, tmp_path):
    import agent_registry as ar
    p = _book(monkeypatch, tmp_path)
    monkeypatch.setattr(sb, "commit_memory", lambda: dict(FULL, free_gb=20.0, phys_free_gb=20.0))
    ag = {"name": "a", "tools": ["Read"], "model": "m", "body": "", "selection": "t"}
    monkeypatch.setattr(ar, "load_agents", lambda: [ag])
    monkeypatch.setattr(ar, "select_agent", lambda *a, **k: ag)
    monkeypatch.setattr(ar, "_changed_files", lambda cwd: [])

    class Boom:
        def __init__(self, *a, **k):
            raise RuntimeError("cannot start thread")
    monkeypatch.setattr(ar, "ThreadPoolExecutor", Boom)
    with pytest.raises(RuntimeError):
        ar.run_dag([{"id": f"t{i}", "needs": ["read"], "prompt": "p", "allow_paths": [f"f{i}"]} for i in range(2)],
                   str(tmp_path), dispatch=lambda *a, **k: {"ok": True})
    assert json.loads(p.read_text(encoding="utf-8"))["reservations"] == {}


def test_ts_nan_and_partial_measurement_subtracts_and_unknown_global_cap(monkeypatch, tmp_path):
    assert "ts" in sb._measure_problems(dict(FULL, ts=float("nan")))
    p = _book(monkeypatch, tmp_path)
    p.write_text(json.dumps({"reservations": {"o1": _own(2.4)}}), encoding="utf-8")
    part = {k: v for k, v in FULL.items() if k != "phys_free_gb"}         # 물리 누락 · commit 여유 4.5
    a = sb.reserve_memory(1, "t", pol=POL, cm=part)
    assert a["granted"] == [] and a["level"] == "blocked"            # 4.5 − 2.4 예약 = 2.1 → 작업 1.2 넣으면 최소 2 미만
    p.write_text(json.dumps({"reservations": {"o1": _own(0.1)}}), encoding="utf-8")
    big = {k: v for k, v in dict(FULL, free_gb=50.0).items() if k != "phys_free_gb"}
    b = sb.reserve_memory(3, "t", pol=POL, cm=big)                   # unknown · 전역 상한 1 − 다른 예약 1 = 0
    assert b["level"] == "unknown" and b["granted"] == []


def test_used_gb_not_double_counted_and_observed_from_run_dag(monkeypatch, tmp_path):
    import agent_registry as ar
    p = _book(monkeypatch, tmp_path)
    p.write_text(json.dumps({"reservations": {"o1": _own(2.4, used_gb=2.0)}}), encoding="utf-8")
    assert sb.reserve_memory(1, "t", pol=POL, cm=FULL)["reserved_gb_others"] == 0.4   # 이미 측정에 잡힌 2.0 은 빼지 않음
    p.write_text(json.dumps({"reservations": {}}), encoding="utf-8")
    monkeypatch.setattr(sb, "commit_memory", lambda: dict(FULL, free_gb=20.0, phys_free_gb=20.0))
    monkeypatch.setattr(ar._TreeWatch, "stop", lambda self: 2.5)
    ag = {"name": "a", "tools": ["Read"], "model": "m", "body": "", "selection": "t"}
    monkeypatch.setattr(ar, "load_agents", lambda: [ag])
    monkeypatch.setattr(ar, "select_agent", lambda *a, **k: ag)
    monkeypatch.setattr(ar, "_changed_files", lambda cwd: [])
    ar.run_dag([{"id": "t0", "needs": ["read"], "prompt": "p"}], str(tmp_path), dispatch=lambda *a, **k: {"ok": True})
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["reservations"] == {} and d["observed"]["default"] == [2.5]   # 예전: run_held 가 관측 없이 해제
