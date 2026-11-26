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
