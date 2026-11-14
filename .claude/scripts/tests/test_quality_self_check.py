"""quality-self-check.py 판정 시험 (R253) — 가짜 대화 기록으로 PASS·FAIL·PARTIAL·미측정 경계 확인."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("qsc", ROOT / ".claude" / "scripts" / "quality-self-check.py")
qsc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qsc)


def _hook(ms, name="a.sh"):
    return {"type": "attachment", "attachment": {"hookName": "SessionStart:startup", "durationMs": ms,
                                                  "command": f'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/{name}"'}}


def _say(text):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


KO = ("이제 변경된 파일을 하나씩 확인하고 회귀 시험과 골든 시험을 다시 실행해서 "
      "통과 여부와 실패 원인을 모두 정리한 뒤 결과를 한 번에 보고하겠습니다. 범위 밖 파일은 손대지 않습니다.")
EN = ("Now let me check the changed files one by one and run the regression and golden tests again, "
      "then report the results and any failure causes in a single summary.")


def test_samples_are_long_enough_to_be_judged():
    std = qsc._std()
    assert std._hangul_ratio(KO)[1] >= std.LANG_MIN_LETTERS
    assert std._hangul_ratio(EN)[1] >= std.LANG_MIN_LETTERS


def test_startup_pass_fail_and_unmeasured():
    assert qsc.check_startup([_hook(1200, "a.sh"), _hook(4999, "b.sh")])["result"] == "PASS"
    r = qsc.check_startup([_hook(1200, "a.sh"), _hook(10988, "process-outbox.sh")])
    assert r["result"] == "FAIL" and r["slowest"] == "process-outbox.sh" and r["wait_ms"] == 10988
    assert qsc.check_startup([])["result"] == "미측정"     # compact·resume 시작은 판정하지 않음


def test_startup_boundary_exactly_limit_is_pass():
    assert qsc.check_startup([_hook(qsc.START_LIMIT_MS)])["result"] == "PASS"
    assert qsc.check_startup([_hook(qsc.START_LIMIT_MS + 1)])["result"] == "FAIL"


def test_korean_pass_needs_enough_reports():
    assert qsc.check_korean([_say(KO)] * (qsc.MIN_REPORTS - 1))["result"] == "미측정"
    assert qsc.check_korean([_say(KO)] * qsc.MIN_REPORTS)["result"] == "PASS"


def test_korean_one_english_or_one_correction_is_partial():
    r = qsc.check_korean([_say(KO)] * 12 + [_say(EN)])
    assert r["result"] == "PARTIAL" and r["english"] == 1
    corr = {"type": "system", "subtype": "stop_hook_summary", "hookInfos": [{"x": "[STD-KOREAN-001] 마지막 보고가 영어입니다"}]}
    r2 = qsc.check_korean([_say(KO)] * 12 + [corr])
    assert r2["result"] == "PARTIAL" and r2["corrections"] == 1


def test_korean_ignores_sidechain_and_api_error():
    side = dict(_say(EN), isSidechain=True)
    ev = [_say(KO)] * 10 + [side, _say("API Error: connection reset by peer while streaming response")]
    assert qsc.check_korean(ev)["result"] == "PASS"


def _resume_session(tmp_path, first_reply, used_tool=True, injected=True, monkeypatch=None):
    boot = 1_000_000.0
    monkeypatch.setattr(qsc, "_boot_epoch", lambda: boot)
    ts = "1970-01-12T14:00:00Z"   # 부팅(1970-01-12 13:46) 뒤
    inj = {"type": "attachment", "timestamp": ts, "x": "## ★ 이어서 할 일 — 바로 시작" if injected else "없음"}
    user = {"type": "user", "timestamp": ts, "message": {"content": "안녕"}}
    content = [{"type": "tool_use", "name": "Bash"}] if used_tool else []
    content.append({"type": "text", "text": first_reply})
    asst = {"type": "assistant", "timestamp": ts, "message": {"content": content}}
    tp = tmp_path / "s.jsonl"
    tp.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in (inj, user, asst)), encoding="utf-8")
    return qsc.check_resume([inj, user, asst], str(tp))


def test_resume_pass_only_when_injected_and_acted(tmp_path, monkeypatch):
    assert _resume_session(tmp_path, "남은 작업을 이어서 처리했습니다.", monkeypatch=monkeypatch)["result"] == "PASS"


def test_resume_asking_to_continue_is_partial(tmp_path, monkeypatch):
    # 11-13 실제 사례: 도구는 썼지만 지시를 기다리는 조건문으로 끝남 → PASS 아님
    r = _resume_session(tmp_path, '"진행해"라고 하시면 1~3번을 이어서 처리하겠습니다.', monkeypatch=monkeypatch)
    assert r["result"] == "PARTIAL" and r["asked_to_continue"]
    r2 = _resume_session(tmp_path, "1~3번도 이어서 처리할지 말씀해 주세요.", monkeypatch=monkeypatch)
    assert r2["result"] == "PARTIAL"


def test_resume_no_tool_or_no_injection(tmp_path, monkeypatch):
    assert _resume_session(tmp_path, "확인했습니다.", used_tool=False, monkeypatch=monkeypatch)["result"] == "PARTIAL"
    assert _resume_session(tmp_path, "처리했습니다.", injected=False, monkeypatch=monkeypatch)["result"] == "FAIL"


def test_resume_session_before_boot_not_applicable(tmp_path, monkeypatch):
    monkeypatch.setattr(qsc, "_boot_epoch", lambda: 9_999_999_999.0)
    ev = [{"type": "user", "timestamp": "2026-11-13T00:00:00Z", "message": {"content": "x"}}]
    tp = tmp_path / "s.jsonl"
    tp.write_text(json.dumps(ev[0]), encoding="utf-8")
    assert qsc.check_resume(ev, str(tp))["result"] == "해당 없음"


def test_main_withdraws_pass_on_same_session_recheck(tmp_path, monkeypatch):
    state = tmp_path / "q.json"
    monkeypatch.setattr(qsc, "STATE", state)
    monkeypatch.setattr(qsc, "LOG", tmp_path / "q.log")
    tp = tmp_path / "sess1.jsonl"
    tp.write_text("\n".join(json.dumps(_hook(900)) for _ in range(1)), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["x", "--transcript", str(tp)])
    qsc.main()
    assert json.loads(state.read_text(encoding="utf-8"))["last_pass"]["Q12_startup"]["session"] == "sess1"
    tp.write_text(json.dumps(_hook(9000)), encoding="utf-8")      # 같은 세션 재판정 FAIL → 이전 PASS 철회
    qsc.main()
    assert "Q12_startup" not in json.loads(state.read_text(encoding="utf-8"))["last_pass"]


def test_korean_counts_each_hook_event_once_not_quotes():
    # R253 재측정: 26 = 같은 사건 이중 기록 + 소스 읽기·요약 인용 → 실제 사건만 센다
    msg = "[STD-KOREAN-001] 새 보고 1건이 영어입니다"
    stop = {"type": "system", "subtype": "stop_hook_summary", "hookInfos": [{"x": msg}]}
    stop_dup = {"type": "user", "message": {"content": "Stop hook feedback:\n" + msg}}
    adv = {"type": "attachment", "attachment": {"type": "hook_additional_context", "content": [msg]}}
    adv_dup = {"type": "attachment", "attachment": {"type": "hook_success", "stdout": msg}}
    grep_result = {"type": "user", "message": {"content": [{"type": "tool_result", "content": 'if "[STD-KOREAN-001]" in s'}]}}
    file_quote = {"type": "attachment", "attachment": {"type": "file", "content": msg}}
    r = qsc.check_korean([_say(KO)] * 12 + [stop, stop_dup, adv, adv_dup, grep_result, file_quote])
    assert (r["stop_blocks"], r["advisories"], r["corrections"]) == (1, 1, 2)
    assert qsc.check_korean([_say(KO)] * 12 + [grep_result, file_quote, stop_dup])["result"] == "PASS"


def test_startup_cancelled_hook_is_fail_even_if_fast():
    ev = [_hook(900, "a.sh")]
    c = _hook(4000, "process-outbox.sh")
    c["attachment"]["type"] = "hook_cancelled"
    r = qsc.check_startup(ev + [c])
    assert r["result"] == "FAIL" and r["cancelled"] == ["process-outbox.sh"]


def test_process_outbox_archives_old_locks_and_logs(tmp_path):
    import os, shutil, subprocess, time
    bash = shutil.which("bash")
    if not bash:
        import pytest
        pytest.skip("bash 없음")
    proj = tmp_path / "p"
    (proj / "plugins").mkdir(parents=True)
    nd = proj / ".claude" / "state" / "notion-outbox"
    nd.mkdir(parents=True)
    old, new = nd / "old.md", nd / "new.md"
    old.write_text("x", encoding="utf-8"); new.write_text("y", encoding="utf-8")
    t = time.time() - 10 * 86400
    os.utime(old, (t, t))
    hook = ROOT / "plugins" / "exec_session_guard" / "hooks" / "process-outbox.sh"
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(proj))
    subprocess.run([bash, str(hook)], env=env, capture_output=True, timeout=60)
    assert (nd / "archive" / "old.md").exists() and new.exists() and not old.exists()
    log = (proj / ".claude" / "logs" / "process-outbox.log").read_text(encoding="utf-8")
    assert "done notion=1" in log and "archived=1" in log
    assert not (proj / ".claude" / "state" / "process-outbox.lock").exists()
    (proj / ".claude" / "state" / "process-outbox.lock").mkdir()       # 실행 중인 잠금 → 겹쳐 실행 안 함
    subprocess.run([bash, str(hook)], env=env, capture_output=True, timeout=60)
    assert "skip" in (proj / ".claude" / "logs" / "process-outbox.log").read_text(encoding="utf-8").splitlines()[-1]
