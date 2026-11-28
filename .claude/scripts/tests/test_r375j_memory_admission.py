"""R375 메모리 압박 P0 — 공통 자원 admission (repair_sandbox.memory_admission) 표적 시험.
정상·저메모리·회복·진동(히스테리시스)·작업 비용·측정 불가·상태 기록 경계·호출부(broker·회귀 게이트·run_dag) 정합."""
import json
import sys
from pathlib import Path

import pytest

LIB = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(LIB))
import repair_sandbox as sb  # noqa: E402

POL = {"min_commit_free_gb": 2, "max_commit_percent": 90, "mem_constrained_percent": 80,
       "mem_resume_percent": 75, "agent_max_parallel": 3, "mem_constrained_parallel": 1, "estimate_margin": 1.2}


def cm(pct, free=8.0):
    return {"measured": True, "percent": pct, "free_gb": free, "used_gb": 20.0, "limit_gb": 25.0}


def walk(seq, pol=POL):
    prior, out = None, []
    for p in seq:
        prior = sb.memory_admission(cm(p), pol, prior)["level"]
        out.append(prior)
    return out


def test_levels_and_parallel():
    assert [sb.memory_admission(cm(p), POL)["level"] for p in (50, 80, 89.9, 90.5)] == \
        ["normal", "constrained", "constrained", "blocked"]
    a = sb.memory_admission(cm(50), POL)
    assert a["max_parallel"] == 3 and not a["defer_optional"]
    c = sb.memory_admission(cm(85), POL)
    assert c["max_parallel"] == 1 and c["defer_optional"]
    assert sb.memory_admission(cm(95), POL)["max_parallel"] == 0


def test_hysteresis_prevents_oscillation():
    # 진입 80 · 재개 75: 79↔81 사이를 오가도 한 번 constrained 면 75 아래까지 유지
    assert walk([70, 81, 79, 78, 76, 74]) == ["normal", "constrained", "constrained", "constrained", "constrained", "normal"]
    # blocked 는 90-(80-75)=85 아래에서 해제 → 89·86 은 blocked 유지 · 84 = constrained · 74 = normal
    assert walk([91, 89, 86, 84, 76, 74]) == ["blocked", "blocked", "blocked", "constrained", "constrained", "normal"]


def test_old_gate_oscillated_new_gate_holds(monkeypatch):
    """역검증: 예전 memory_gate(상한 단독)는 91→89→91 에서 허용/거부를 번갈아 냈다 · 지금은 회복 전까지 보류."""
    def old_gate(c):   # 4c1ea594 이전 정의 재현
        return c["free_gb"] < 2 or c["percent"] > 90
    assert [old_gate(cm(p)) for p in (91, 89, 91)] == [True, False, True]
    assert walk([91, 89, 91]) == ["blocked", "blocked", "blocked"]


def test_job_cost_and_commit_free_floor():
    assert sb.memory_admission(cm(60, free=2.5), POL)["level"] == "normal"
    # 예상 1GB × 여유 1.2 = 1.2GB → 2.5-1.2 < 2 = blocked (퍼센트가 낮아도)
    a = sb.memory_admission(cm(60, free=2.5), POL, est_gb=1.0)
    assert a["level"] == "blocked" and "예상" in a["reason"]
    assert sb.memory_admission(cm(60, free=1.5), POL)["level"] == "blocked"


def test_unknown_does_not_block():
    a = sb.memory_admission({"measured": False, "reason": "x"}, POL)
    assert a["level"] == "unknown" and a["max_parallel"] == 3
    assert sb.memory_gate(POL, {"measured": False}) is None


def test_thresholds_env_override_and_bad_order(monkeypatch):
    monkeypatch.setenv("ORCA_MEM_CONSTRAINED_PERCENT", "70")
    assert sb.memory_admission(cm(72), POL)["level"] == "constrained"
    bad = {**POL, "mem_resume_percent": 85}           # 재개선 > 진입선 = 설정 실수 → 진입선으로 낮춤 (진동 방지)
    monkeypatch.delenv("ORCA_MEM_CONSTRAINED_PERCENT")
    assert sb.admission_thresholds(bad)["resume_pct"] == 80


def test_state_persists_across_calls(tmp_path, monkeypatch):
    st = tmp_path / "adm.json"
    monkeypatch.setenv("ORCA_MEM_ADMISSION_STATE", str(st))
    assert sb.admission_now(cm(91), POL)["level"] == "blocked"
    assert json.loads(st.read_text(encoding="utf-8"))["level"] == "blocked"
    a = sb.admission_now(cm(88), POL)                  # 다른 호출(프로세스)도 직전 단계를 이어받음
    assert a["level"] == "blocked" and a["prior"] == "blocked"
    g = sb.memory_gate(POL, cm(88))
    assert g and g["deferred"] and "회복 대기" in g["reason"]


def test_corrupt_or_stale_state_ignored(tmp_path, monkeypatch):
    st = tmp_path / "adm.json"
    monkeypatch.setenv("ORCA_MEM_ADMISSION_STATE", str(st))
    st.write_text("{깨짐", encoding="utf-8")
    assert sb.admission_now(cm(50), POL)["level"] == "normal"
    st.write_text(json.dumps({"level": "blocked", "ts": 0}), encoding="utf-8")   # TTL 지난 기록
    a = sb.admission_now(cm(88), POL)
    assert a["prior"] is None and a["level"] == "constrained"


def test_state_not_written_under_pytest_unless_explicit(monkeypatch, tmp_path):
    monkeypatch.delenv("ORCA_MEM_ADMISSION_STATE", raising=False)
    assert sb._admission_state_path() is None            # 운영·시험 root 모두 (시험 간 공유·운영 오염 방지)
    monkeypatch.delenv("PYTEST_CURRENT_TEST")
    p = sb._admission_state_path()                       # 시험 밖: 운영 root = .claude/state · 시험 root = 그 안
    assert p is not None and p.name.endswith("memory-admission.json")
    assert ("_memory-admission" in p.name) == (not sb.IS_OPERATIONAL_ROOT)


def test_broker_uses_common_admission(monkeypatch):
    import broker as b
    monkeypatch.delenv("ORCA_MEM_ADMISSION_STATE", raising=False)
    assert b._memory_level(50) == "normal" and b._memory_level(85) == "constrained" and b._memory_level(93) == "blocked"
    assert b._memory_level(None) == "unknown"
    monkeypatch.setenv("ORCA_MAX_COMMIT_PERCENT", "84")    # 정본 임계값을 바꾸면 broker 도 따라감 (예전 고정 90)
    assert b._memory_level(85) == "blocked"


def test_regression_gate_wait_uses_common_thresholds(monkeypatch):
    import independent_verifier as iv
    monkeypatch.setenv("ORCA_MEM_CONSTRAINED_PERCENT", "60")
    monkeypatch.setenv("ORCA_GATE_MEM_WAIT_SEC", "0")
    monkeypatch.setattr(sb, "commit_memory", lambda: cm(65))
    res = {}
    assert iv._wait_memory_for_heavy(res) is None and res["memory_wait"]["percent"] == 65   # 60% 기준이면 대기 진입(0초 → 순차 진행)
    monkeypatch.setenv("ORCA_MAX_COMMIT_PERCENT", "64")
    assert "64" in (iv._wait_memory_for_heavy({}) or "")                                   # 상한도 정본에서


@pytest.mark.parametrize("par, wave", [(3, 3), (1, 1), (0, 1)])
def test_run_dag_parallel_follows_admission(monkeypatch, tmp_path, par, wave):
    """정상 = 정책 3개 동시 · constrained = 1개씩(순차) · blocked = 1 (각 dispatch 의 memory_gate 가 보류)."""
    import agent_registry as ar
    monkeypatch.setattr(sb, "admission_now", lambda *a, **k: {"max_parallel": par, "level": "x"})
    ag = {"name": "a", "tools": ["Read"], "model": "m", "body": "", "selection": "t"}
    monkeypatch.setattr(ar, "load_agents", lambda: [ag])
    monkeypatch.setattr(ar, "select_agent", lambda *a, **k: ag)
    monkeypatch.setattr(ar, "_changed_files", lambda cwd: [])
    tasks = [{"id": f"t{i}", "needs": ["read"], "prompt": "p", "allow_paths": [f"f{i}"]} for i in range(3)]
    r = ar.run_dag(tasks, str(tmp_path), dispatch=lambda *a, **k: {"ok": True, "result": ""})
    waves = r.get("waves") or r.get("metrics", {}).get("waves")
    assert waves and max(len(w) for w in waves) == wave
