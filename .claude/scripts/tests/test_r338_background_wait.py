"""R338 성능·자동화 — 백그라운드 명령 결과를 기다리는 동안 Stop 원장 게이트가 매 턴 막아 '대기 중' 답만 반복하던 낭비.

2026-11-20 실측: R334 수신 뒤 게이트 차단 피드백 턴 18회 (회귀 게이트·측정이 백그라운드로 도는 동안).
이 세션이 띄운 Bash 백그라운드 명령이 아직 끝나지 않았으면 Stop 허용 (완료 처리 아님 · 끝나면 하네스 알림으로 이어짐).
Monitor·대화 본문 인용·완료된 작업·오래된 작업은 해당 없음 → 종전대로 막는다."""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_r314_e2e_scenarios import LEDGER_PY, _cli, _prompt  # noqa: E402

SID = "s338"


def _ts(sec_ago=0):
    return datetime.fromtimestamp(time.time() - sec_ago, timezone.utc).isoformat().replace("+00:00", "Z")


def _tool_result(text, sec_ago=0):
    return {"type": "user", "timestamp": _ts(sec_ago),
            "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t", "content": text}]}}


def _notice(tid):
    return {"type": "user", "timestamp": _ts(),
            "message": {"role": "user", "content": f"<task-notification>\n<task-id>{tid}</task-id>\n<status>completed</status>"}}


def _write(tmp, rows):
    p = tmp / "transcript.jsonl"
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    return str(p)


def _gate(tmp, transcript):
    return _cli(tmp, LEDGER_PY, "gate", stdin=json.dumps({"session_id": SID, "transcript_path": transcript}))


def test_running_background_allows_stop_without_completing(tmp_path):
    _prompt(tmp_path, "로그인 버그 고쳐줘", SID)
    tr = _write(tmp_path, [_tool_result("Command running in background with ID: bk1abc2. Output is being written to: x")])
    g = _gate(tmp_path, tr)
    assert g.returncode == 0 and "bk1abc2" in g.stderr and "Stop 허용" in g.stderr
    led = json.loads((tmp_path / ".claude" / "state" / "request-ledger.json").read_text(encoding="utf-8"))
    assert led["requests"][-1]["status"] == "pending"                 # 완료로 바뀌지 않음


def _gate_payload(tmp, payload):
    return _cli(tmp, LEDGER_PY, "gate", stdin=json.dumps({"session_id": SID, **payload}))


def test_official_background_tasks_field_preferred(tmp_path):
    """공식 Stop 입력 background_tasks (hooks 문서 Stop input) — 있으면 그것만 본다 (대화 기록보다 우선)."""
    _prompt(tmp_path, "로그인 버그 고쳐줘", SID)
    running = [{"id": "task-001", "type": "shell", "status": "running", "command": "pytest"}]
    g = _gate_payload(tmp_path, {"background_tasks": running})
    assert g.returncode == 0 and "task-001" in g.stderr
    assert _gate_payload(tmp_path, {"background_tasks": [{"id": "m1", "type": "monitor", "status": "running"}]}).returncode == 2
    assert _gate_payload(tmp_path, {"background_tasks": []}).returncode == 2          # 진행 중 없음
    # 필드가 빈 배열이면 대화 기록에 시작 흔적이 있어도 공식 값을 따른다 (이미 끝난 것으로 봄)
    tr = _write(tmp_path, [_tool_result("Command running in background with ID: bk1abc2. Output")])
    assert _gate_payload(tmp_path, {"background_tasks": [], "transcript_path": tr}).returncode == 2


def test_finished_quoted_monitor_old_or_missing_keep_blocking(tmp_path):
    _prompt(tmp_path, "로그인 버그 고쳐줘", SID)
    cases = {
        "완료 알림 있음": [_tool_result("Command running in background with ID: bk1abc2. Output"), _notice("bk1abc2")],
        "대화 본문 인용": [{"type": "assistant", "timestamp": _ts(), "message": {"role": "assistant", "content": [
            {"type": "text", "text": "Command running in background with ID: X 라는 문장"}]}}],
        "Monitor 만": [_tool_result("Monitor started (task mon1abc, expires in 20m)")],
        "90분 넘음": [_tool_result("Command running in background with ID: old1abc. Output", sec_ago=91 * 60)],
    }
    for name, rows in cases.items():
        assert _gate(tmp_path, _write(tmp_path, rows)).returncode == 2, name
    assert _gate(tmp_path, "").returncode == 2                          # 기록 경로 없음 = 종전대로
