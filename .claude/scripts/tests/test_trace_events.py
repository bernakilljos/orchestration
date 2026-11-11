"""§78 요청 단위 추적 — 접수부터 시도(실패→대체→성공)·시간·근거 · 가림 · 기록 장애 · 복원 (격리 폴더)."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / ".claude" / "scripts"
HOOKS = ROOT / ".claude" / "hooks"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture
def proj(tmp_path, monkeypatch):
    (tmp_path / ".claude" / "state").mkdir(parents=True)
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def tm(proj):
    return _load("trace_under_test", SCRIPTS / "lib" / "trace.py")


def test_no_trace_id_records_nothing(tm, proj):
    assert tm.emit("tool", step="Bash", status="success") == "none"
    assert not (proj / ".claude" / "logs" / "trace-events.jsonl").exists()


def test_jsonl_when_table_absent_then_db_after_init(tm, proj):
    tm.set_current("tid-1", "R1", "guide 고쳐줘")
    assert tm.emit("tool", step="Bash", status="success", duration_ms=12.3) == "jsonl"
    subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "lib" / "trace.py"), "init-db",
                    str(proj / ".claude" / "state" / "orca.db")], check=True, env=dict(os.environ))
    assert tm.emit("tool", step="Bash", status="fail", error="exit 1") == "db"
    evs = tm.events("tid-1")
    assert [e["status"] for e in evs] == ["success", "fail"]


def test_failure_then_fallback_success_is_chained(tm, proj):
    tm.set_current("tid-2", "R2", "x")
    tm.emit("tool", step="Bash", status="fail", error="UIA 대기 30s 초과")
    tm.emit("tool", step="Bash", status="fail", error="win32 경로 권한 없음")
    tm.emit("tool", step="Bash", status="success")
    tm.emit("test", step="regression-gate", status="fail", error="신규 실패 1")
    ch = tm.chains(tm.events("tid-2"))
    bash = [c for c in ch if c["step"] == "Bash"][0]
    assert len(bash["failures"]) == 2 and bash["success"]["status"] == "success"
    gate = [c for c in ch if c["step"] == "regression-gate"][0]
    assert gate["success"] is None     # 성공 기록 없음 = 연결을 만들지 않음


def test_secrets_masked(tm, proj):
    tm.set_current("tid-3", "R3", "")
    secret = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
    tm.emit("tool", step="Bash", status="fail", error="token=" + secret, detail={"cmd": "curl -H " + secret})
    raw = (proj / ".claude" / "logs" / "trace-events.jsonl").read_text(encoding="utf-8")
    assert secret not in raw


def test_corrupt_db_falls_back_to_jsonl(tm, proj):
    (proj / ".claude" / "state" / "orca.db").write_bytes(b"not a database")
    tm.set_current("tid-4", "R4", "")
    assert tm.emit("tool", step="Edit", status="success") == "jsonl"


def test_ledger_registration_starts_trace(proj):
    sys.path.insert(0, str(HOOKS / "prompt"))
    try:
        lar = _load("lar_under_test", HOOKS / "prompt" / "ledger_auto_register.py")
        r = lar._append_ledger_entry("guide.txt 오타 고쳐줘", "sess-abc", "execute")
    finally:
        sys.path.remove(str(HOOKS / "prompt"))
    assert r["status"] == "registered"
    cur = json.loads((proj / ".claude" / "state" / "current-trace.json").read_text(encoding="utf-8"))
    assert cur["trace_id"] == r["event_id"] and cur["rid"] == r["request_id"]
    tm = _load("trace_after_ledger", SCRIPTS / "lib" / "trace.py")
    evs = tm.events(r["request_id"])           # R 번호로도 조회
    assert evs and evs[0]["kind"] == "request" and evs[0]["status"] == "start"
    # 종료 기록 (request-ledger complete) → 같은 추적번호에 partial
    subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "request-ledger.py"), "complete", r["request_id"],
                    "--evidence", "시험", "--verification", "PARTIAL"], env=dict(os.environ), capture_output=True)
    assert [e["status"] for e in tm.events(r["event_id"])][-1] == "partial"


def test_hook_failure_cli_and_resume_section(proj, tm):
    tm.set_current("tid-5", "R5", "SAP 연결")
    inp = json.dumps({"tool_name": "Bash", "tool_input": {"command": "python sap_connect.py"}, "error": "RFC 연결 실패", "tool_use_id": "tu_1"})
    subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "lib" / "trace.py"), "hook-failure"], input=inp, text=True,
                   encoding="utf-8", env=dict(os.environ), check=True)
    tm.emit("tool", step="Bash", status="success")
    out = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "lib" / "trace.py"), "show", "tid-5"],
                         capture_output=True, text=True, encoding="utf-8", env=dict(os.environ)).stdout
    assert "RFC 연결 실패" in out and "실패 1회" in out
    rs = _load("resume_under_test", SCRIPTS / "resume-last-24h.py")
    sec = rs.section_current_trace()
    assert "tid-5" in sec and "대체 성공" in sec


@pytest.mark.parametrize("path,expect", [
    ("C:\\\\x\\\\.claude\\\\rules\\\\a.md", True),     # Windows 역슬래시 경로 (종전엔 재색인 안 됨)
    ("C:/x/.claude/rules/a.md", True),
    ("C:\\\\x\\\\guide.txt", False),
])
def test_index_rule_on_edit_windows_paths(tmp_path, path, expect):
    (tmp_path / ".claude" / "scripts").mkdir(parents=True)
    (tmp_path / ".claude" / "logs").mkdir(parents=True)
    marker = tmp_path / "rebuilt.txt"
    (tmp_path / ".claude" / "scripts" / "lookup-rule.py").write_text(
        "import pathlib,sys\npathlib.Path(%r).write_text('x')\n" % str(marker), encoding="utf-8")
    payload = '{"tool_name":"Edit","tool_input":{"file_path":"%s"}}' % path
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(tmp_path))
    env.pop("RULE_INDEX_ACTIVE", None)
    subprocess.run(["bash", str(HOOKS / "index-rule-on-edit.sh")], input=payload, text=True, env=env, timeout=60)
    import time
    for _ in range(50):
        if marker.exists():
            break
        time.sleep(0.1)
    assert marker.exists() == expect
