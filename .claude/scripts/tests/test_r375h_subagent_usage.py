"""R375 사용자 지시 4 (2026-11-27): 배정 평가의 원자료 — 서브에이전트 기록이 토큰 0·성공 1 고정(631건)이던 것.

격리: ORCHESTRATION_ROOT = tmp_path (운영 orca.db 사용 X).
"""
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[3]
REC = KIT / ".claude" / "scripts" / "lib" / "record_call.py"
sys.path.insert(0, str(REC.parent))
import record_call  # noqa: E402


def _transcript(p: Path):
    rows = [
        {"type": "assistant", "message": {"id": "m1", "model": "claude-haiku-5-5",
                                          "usage": {"input_tokens": 3, "output_tokens": 10,
                                                    "cache_read_input_tokens": 100, "cache_creation_input_tokens": 50}}},
        {"type": "assistant", "message": {"id": "m1", "model": "claude-haiku-5-5",            # 같은 메시지 스트리밍 = 1번만
                                          "usage": {"input_tokens": 3, "output_tokens": 20,
                                                    "cache_read_input_tokens": 100, "cache_creation_input_tokens": 50}}},
        {"type": "user", "message": {"role": "user", "content": "x"}},
        "깨진 줄",
        {"type": "assistant", "message": {"id": "m2", "model": "claude-haiku-5-5",
                                          "usage": {"input_tokens": 1, "output_tokens": 5, "cache_read_input_tokens": 200}}},
    ]
    p.write_text("\n".join(r if isinstance(r, str) else json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def test_usage_from_transcript_sums_unique_messages(tmp_path):
    t = tmp_path / "agent.jsonl"
    _transcript(t)
    assert record_call.usage_from_transcript(str(t)) == (4, 25, 300, 50, "claude-haiku-5-5")
    assert record_call.usage_from_transcript(str(tmp_path / "없음.jsonl")) is None


def _init_db(root: Path, env: dict) -> None:
    """격리 DB 스키마 준비 (운영 init 경로 그대로 · ORCHESTRATION_ROOT 로 tmp 지정)."""
    subprocess.run([sys.executable, "-c", "import sys;sys.path.insert(0,sys.argv[1]);import state_db;state_db.init_schema()",
                    str(REC.parent)], env=env, check=True, capture_output=True, timeout=60)


def _db_rows(root: Path):
    c = sqlite3.connect(root / ".claude" / "state" / "orca.db")
    try:
        return c.execute("select tokens_in, tokens_out, cost_usd, success, error_class from metrics").fetchall(), \
            c.execute("select today_spent_usd from budget").fetchall()
    finally:
        c.close()


def test_record_from_transcript_tokens_known_cost_unknown_no_budget(tmp_path):
    """토큰은 실측으로 기록 · 비용은 NULL(구독은 청구액 아님) · 예산 누계에 더하지 않음 · 성공 여부 모름 표시."""
    (tmp_path / ".claude" / "scripts").mkdir(parents=True)
    t = tmp_path / "agent.jsonl"
    _transcript(t)
    env = {**os.environ, "ORCHESTRATION_ROOT": str(tmp_path), "PYTHONIOENCODING": "utf-8"}
    _init_db(tmp_path, env)
    r = subprocess.run([sys.executable, "-X", "utf8", str(REC), "--ai", "claude", "--model", "subagent-x",
                        "--usage-from-transcript", str(t), "--latency-ms", "1000", "--success", "1",
                        "--error-class", "outcome_unknown", "--task-id", "subagent-1"],
                       env=env, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    rows, budget = _db_rows(tmp_path)
    assert rows == [(4 + 300 + 50, 25, None, 1, "outcome_unknown")]
    assert all((b[0] or 0) == 0 for b in budget)


def test_record_without_transcript_stays_unknown(tmp_path):
    (tmp_path / ".claude" / "scripts").mkdir(parents=True)
    env = {**os.environ, "ORCHESTRATION_ROOT": str(tmp_path), "PYTHONIOENCODING": "utf-8"}
    _init_db(tmp_path, env)
    r = subprocess.run([sys.executable, "-X", "utf8", str(REC), "--ai", "claude", "--model", "subagent-x",
                        "--usage-from-transcript", str(tmp_path / "없음.jsonl"), "--latency-ms", "5",
                        "--success", "1", "--error-class", "outcome_unknown"], env=env, capture_output=True, text=True,
                       timeout=60)
    assert r.returncode == 0, r.stderr
    rows, _ = _db_rows(tmp_path)
    assert rows == [(0, 0, None, 1, "outcome_unknown")]                 # 못 읽으면 종전처럼 UNKNOWN (0 을 측정값으로 X)


def test_log_subagent_passes_transcript_and_outcome_unknown(tmp_path, monkeypatch):
    """훅은 공식 입력 agent_transcript_path 를 자식 기록기에 넘기고 성공을 «모름» 으로 표시 (기다리지 않음)."""
    sys.path.insert(0, str(KIT / ".claude" / "hooks" / "prompt"))            # _common (tool-dispatch 와 같은 경로)
    sys.path.insert(0, str(KIT / ".claude" / "hooks" / "tool"))
    import importlib
    import log_subagent
    importlib.reload(log_subagent)
    (tmp_path / ".claude" / "scripts" / "lib").mkdir(parents=True)
    (tmp_path / ".claude" / "scripts" / "lib" / "record_call.py").write_text("", encoding="utf-8")
    t = tmp_path / "agent.jsonl"
    _transcript(t)
    seen = []
    monkeypatch.setattr(log_subagent.subprocess, "Popen", lambda args, **k: seen.append(args))
    monkeypatch.setattr(log_subagent, "project_path", lambda ctx, *p: str(tmp_path.joinpath(*p)))
    ctx = type("C", (), {"payload": {"hook_event_name": "SubagentStop", "agent_id": "a1", "agent_type": "Explore",
                                     "agent_transcript_path": str(t)}})()
    log_subagent.run(ctx)
    args = seen[0]
    assert args[args.index("--usage-from-transcript") + 1] == str(t)
    assert args[args.index("--error-class") + 1] == "outcome_unknown" and "--usage-unknown" not in args


def test_r375i_success_rate_excludes_outcome_unknown(tmp_path):
    """R375 8차 P1: outcome_unknown 행(success=1 이 들어 있음)은 성공률 분모·분자에서 제외 · 아는 결과 0건 = None(UNKNOWN)."""
    env = {**os.environ, "ORCHESTRATION_ROOT": str(tmp_path), "PYTHONIOENCODING": "utf-8"}
    _init_db(tmp_path, env)
    code = r"""
import sys, json; sys.path.insert(0, sys.argv[1]); import state_db as s
for _ in range(3):
    s.record_metric("claude-agent:x", "m", 1, 1, 0.0, 0, True, task_id="t", error_class="outcome_unknown")
s.record_metric("claude-agent:x", "m", 1, 1, 0.0, 0, False, task_id="t", error_class="tool_error")
s.record_metric("claude-agent:y", "m", 1, 1, 0.0, 0, True, task_id="t", error_class="outcome_unknown")
s.record_metric("claude", "subagent-?", 0, 0, 0.0, 0, True, task_id="subagent-a1")       # 13500384 이전 형식 (error_class 없음)
s.record_metric("claude", "m", 1, 1, 0.0, 0, True, task_id="task-9")                     # 일반 호출 = 결과 앎
r = s.get_metrics_summary(hours=1)
print(json.dumps({k: [v["count"], v["outcome_known"], v["success_rate"]] for k, v in r.items()}))
"""
    out = subprocess.run([sys.executable, "-c", code, str(REC.parent)], env=env, capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    got = json.loads(out.stdout.strip().splitlines()[-1])
    assert got["claude-agent:x"] == [4, 1, 0.0]          # 예전: 3/4 = 75% (모르는 3건이 성공으로 셈)
    assert got["claude-agent:y"] == [1, 0, None]         # 예전: 100%
    assert got["claude"] == [2, 1, 1.0]                  # 구형 서브에이전트 행은 모름 · 일반 호출 1건만 분모


def test_r375i_repair_first_pass_and_rework_tokens():
    """R375 8차 P1: 첫 통과율·재작업 토큰은 metrics.success(프로세스 정상 종료)가 아니라 목표 결과 + 라운드별 세션으로.
    세션이 metrics 에 없는 목표(Phase 15 이전)는 토큰 UNKNOWN 으로 따로 · judge 연결 없으면 judge 토큰 UNKNOWN."""
    import ops_metrics as om
    c = sqlite3.connect(":memory:")
    c.executescript("""
CREATE TABLE goals (goal_id INTEGER, status TEXT, created_at REAL);
CREATE TABLE goal_tasks (goal_id INTEGER, task_id TEXT, sequence INTEGER);
CREATE TABLE tasks (task_id TEXT, task_file TEXT);
CREATE TABLE metrics (task_id TEXT, ai TEXT, tokens_in INTEGER, tokens_out INTEGER);
""")

    def goal(gid, st, sessions, judge=None):
        c.execute("INSERT INTO goals VALUES (?,?,?)", (gid, st, 100.0))
        c.execute("INSERT INTO goal_tasks VALUES (?,?,0)", (gid, f"g{gid}-agent-fix"))
        spec = {"agent_sessions": sessions, **({"judge_session": judge} if judge else {})}
        c.execute("INSERT INTO tasks VALUES (?,?)", (f"g{gid}-agent-fix", json.dumps(spec)))

    goal(1, "VERIFIED", ["s1"], judge="j1")                  # 첫 통과
    goal(2, "VERIFIED", ["s2a", "s2b"])                      # 2라운드 통과 = 재작업
    goal(3, "FAILED", ["s3"])                                # 실패
    goal(4, "VERIFIED", ["old"])                             # metrics 없음(이전 형식) = 첫 통과지만 토큰 미연결
    goal(5, "RUNNING", ["s5"])                               # 결과 미정 = 분모 X
    for sid, ai, ti, to in (("s1", "claude-agent:fix", 100, 10), ("j1", "claude-agent:judge", 50, 5),
                            ("s2a", "claude-agent:fix", 200, 20), ("s2b", "claude-agent:fix", 300, 30),
                            ("s3", "claude-agent:fix", 400, 40), ("s5", "claude-agent:fix", 9, 9)):
        c.execute("INSERT INTO metrics VALUES (?,?,?,?)", (sid, ai, ti, to))
    r = om.repair_quality(c, 0)
    assert r["finished"] == 4 and r["first_pass"] == 2 and r["first_pass_rate"] == 0.5
    assert r["token_linked_goals"] == 3 and r["token_unlinked_goals"] == 1
    assert r["fix_tokens"] == 110 + 220 + 330 + 440 and r["rework_tokens"] == 330
    assert r["judge_tokens"] == 55 and r["judge_linked_goals"] == 1
    c.execute("UPDATE tasks SET task_file=? WHERE task_id='g1-agent-fix'", (json.dumps({"agent_sessions": ["s1"]}),))
    assert om.repair_quality(c, 0)["judge_tokens"] == "UNKNOWN"          # judge 연결 0 = 0 이 아니라 UNKNOWN
