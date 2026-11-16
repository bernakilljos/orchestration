"""R259 (2026-11-16) — 상태줄 표시 정확성: 실제 재현된 계산·갱신 결함만.

1) 개발 단계: 도구 기록 입력을 200자로 잘라 앞이 긴 명령의 뒤쪽 git commit·merge-to-target --apply 가 사라짐
   → R257·R258 이 실제로 커밋·전파했는데 4/6 로 표시
2) HEALTH: «30일 지나면 자동 점검» 인데 monthly 를 부르는 곳이 없어 10/16 점수가 한 달 넘게 남음 ·
   같은 검사(중복)를 두 번 세어 10축 문서와 달리 11축
(같은 판정을 Stop 마다 다시 적어 READY 를 0 으로 끌어내리던 것은 test_quality_self_check 에서)
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

KIT = Path(__file__).resolve().parents[3]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _stage_hits(sl, cmd):
    return [n for n, ok in sl._STAGES if ok("Bash", cmd)]


def test_tool_trace_keeps_long_command_tail():
    src = (KIT / ".claude/hooks/tool-dispatch.py").read_text(encoding="utf-8")
    m = re.search(r'detail=\{"input": str\(brief\)\[:(\d+)\]', src)
    assert m and int(m.group(1)) >= 1500, "도구 기록 입력이 짧게 잘리면 뒤쪽 단계 명령이 사라진다"
    sl = _load("sl_r259", KIT / ".claude/scripts/statusline_context.py")
    # R258 실제 형태: 앞에 게이트 결과 확인(약 300자) 뒤 커밋 · 파일 목록 반복문 뒤 전파
    commit_cmd = ("cd /c/pjt/orchestration_v1 && tail -1 \"" + "C:/x/" * 40 + "gate3.log\"; python -X utf8 -c \"print(1)\"; "
                  "git commit -q -F - <<'EOF'\nfeat: x\nEOF")
    merge_cmd = ("O=\"\"; for f in " + " ".join(f".claude/scripts/f{i}.py" for i in range(12)) +
                 "; do O=\"$O --only $f\"; done; for T in C:/IFRS_PJT; do python -X utf8 .claude/scripts/merge-to-target.py \"$T\" $O --apply; done")
    assert len(commit_cmd) > 200 and len(merge_cmd) > 200
    assert "커밋" in _stage_hits(sl, commit_cmd[:int(m.group(1))])
    assert "전파" in _stage_hits(sl, merge_cmd[:int(m.group(1))])
    assert "커밋" not in _stage_hits(sl, commit_cmd[:200])          # 수정 전 상한(200)이면 사라지던 것 = 재현


def test_health_axes_counted_once():
    hc = _load("hc_r259", KIT / ".claude/scripts/health-check.py")
    calls = []
    for name in ("check_duplicates", "check_orphan", "check_drift", "check_golden", "check_request_ledger", "check_codex",
                 "check_stop_gate", "check_propagation", "check_recurrence", "check_standing"):
        setattr(hc, name, (lambda n: (lambda: calls.append(n) or {"ok": True}))(name))
    checks = hc.run_all_checks()
    assert len(checks) == 10 and calls.count("check_duplicates") == 1     # 10축 · 같은 검사 한 번


def test_health_monthly_is_wired_to_async_session_start():
    hook = (KIT / ".claude/hooks/detect-artifact-staleness.sh").read_text(encoding="utf-8")
    assert "health-check.py\" monthly" in hook
    # throttle(1시간 exit) 보다 앞이어야 매 시작 확인
    assert hook.index("health-check.py\" monthly") < hook.index("THROTTLE_FILE=")
    s = json.loads((KIT / ".claude/settings.json").read_text(encoding="utf-8"))
    hooks = [h for g in s["hooks"]["SessionStart"] for h in g["hooks"] if "detect-artifact-staleness" in h["command"]]
    assert hooks and hooks[0].get("async") is True                       # 시작을 기다리게 하지 않음


def test_health_status_marks_overdue_and_fresh(tmp_path, monkeypatch):
    hc = _load("hc_r259b", KIT / ".claude/scripts/health-check.py")
    from datetime import datetime, timedelta
    st = tmp_path / "h.json"
    monkeypatch.setattr(hc, "STATE_FILE", str(st))
    st.write_text(json.dumps({"last_check": (datetime.now() - timedelta(days=31)).isoformat(), "last_score": 45}), encoding="utf-8")
    assert "점검 필요" in hc.status_line()
    st.write_text(json.dumps({"last_check": datetime.now().isoformat(), "last_score": 40}), encoding="utf-8")
    assert "점검 필요" not in hc.status_line() and "40/100" in re.sub(r"\x1b\[[0-9;]*m", "", hc.status_line())


# ── R261 요구사항 부분 반영·거짓 완료 ───────────────────────────────────
SIX = ("지시\n\n1. 임시 파일 정리\n설명\n2. 승인 요청 취소\n3. 오탐 재발 방지\n- 하위 글머리\n"
       "4. 자동 실행\n```\n5. 코드 블록 안 번호는 제외\n```\n5. 검증\n6. 보고\n")


def _ledger(tmp_path, monkeypatch, items_text=SIX):
    L = _load("L_r261", KIT / ".claude/scripts/request-ledger.py")
    monkeypatch.setattr(L, "LEDGER", tmp_path / "ledger.json")
    L._save({"session_id": "s", "requests": [{"id": "R1", "desc": "x", "status": "pending",
                                                  "items": L.extract_items(items_text)}]})
    return L


def test_r261_extract_numbered_items_skips_code_fence():
    L = _load("L_r261a", KIT / ".claude/scripts/request-ledger.py")
    its = L.extract_items(SIX)
    assert [x["text"] for x in its] == ["임시 파일 정리", "승인 요청 취소", "오탐 재발 방지", "자동 실행", "검증", "보고"]
    assert all(x["state"] == "open" for x in its) and [x["i"] for x in its] == [1, 2, 3, 4, 5, 6]


def test_r261_two_of_six_done_blocks_pass(tmp_path, monkeypatch):
    L = _ledger(tmp_path, monkeypatch)
    assert L.cmd_item("R1", "1-2", "done", "증거") == 0
    assert L.cmd_complete("R1", "일부 구현", "PASS") == 2                       # 2/6 → 전체 완료 거부
    r = L._load()["requests"][0]
    assert r["status"] == "pending" and L.item_counts(r) == (2, 6)
    assert L.cmd_complete("R1", "일부 구현", "PARTIAL") == 1                    # 사실대로 PARTIAL 은 기록됨
    assert L._load()["requests"][0]["status"] == "verified"
    assert L.summarize(L._load()["requests"], "R1")["current_items"] == (2, 6)


def test_r261_done_and_na_need_evidence_then_pass_allowed(tmp_path, monkeypatch):
    L = _ledger(tmp_path, monkeypatch)
    assert L.cmd_item("R1", "1", "done", "") == 2                                # 근거 없는 done 거부
    assert L.cmd_item("R1", "6", "na", "  ") == 2                                # 사유 없는 해당 없음 거부
    assert L.cmd_item("R1", "1,2,3", "done", "e") == 0
    assert L.cmd_item("R1", "4", "partial", "e") == 0
    assert L.cmd_item("R1", "5", "done", "e") == 0 and L.cmd_item("R1", "6", "na", "보고 형식 절") == 0
    assert L.cmd_complete("R1", "e", "PASS") == 2                                # partial 1개 남음
    assert L.cmd_item("R1", "4", "done", "e") == 0
    assert L.cmd_complete("R1", "e", "PASS") == 0 and L._load()["requests"][0]["status"] == "completed"


def test_r261_no_items_keeps_old_behavior(tmp_path, monkeypatch):
    L = _ledger(tmp_path, monkeypatch, items_text="번호 없는 짧은 지시")
    assert L.cmd_complete("R1", "e", "PASS") == 0


def test_r261_auto_register_stores_items(tmp_path, monkeypatch):
    import sys as _s
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    (tmp_path / ".claude" / "state").mkdir(parents=True)
    _s.path.insert(0, str(KIT / ".claude/hooks/prompt"))
    R = _load("R_r261", KIT / ".claude/hooks/prompt/ledger_auto_register.py")
    res = R._append_ledger_entry(SIX, "sess", "execute")
    e = json.loads((tmp_path / ".claude/state/request-ledger.json").read_text(encoding="utf-8"))["requests"][-1]
    assert res["status"] == "registered" and len(e["items"]) == 6 and e["items"][0]["state"] == "open"


def test_r261_eta_only_from_measured_stages():
    sl = _load("sl_r261", KIT / ".claude/scripts/statusline_context.py")
    assert sl._eta_min(None, {"수정": 100.0, "시험": 200.0}, 6) is None             # 시작 시각 없음
    assert sl._eta_min(0.0, {"수정": 60.0}, 6) is None                               # 끝난 단계 1개 = 근거 부족
    assert sl._eta_min(0.0, {"수정": 60.0, "시험": 240.0}, 6) == 8                  # 단계당 120초 × 남은 4 = 8분
    assert sl._eta_min(0.0, {n: 60.0 * i for i, n in enumerate("abcdef", 1)}, 6) == 0
    src = (KIT / ".claude/scripts/statusline_context.py").read_text(encoding="utf-8")
    assert '(산정중)' in src and '(≈{_eta}분)' in src and "요구{_it[0]}/{_it[1]}" in src   # R269 표기: 상태 뒤 괄호


def test_r262_scan_cache_tmp_removed_on_failure_and_stale_swept(tmp_path, monkeypatch):
    """R262: os.replace 실패(다른 렌더가 읽는 중) 때 임시 파일이 남아 99개 누적 — 실패 시 제거 · 10분 넘은 잔여물 정리."""
    import os as _os
    import time as _t
    sl = _load("sl_r262", KIT / ".claude/scripts/statusline_context.py")
    cache = tmp_path / "jsonl-scan-cache.json"
    monkeypatch.setattr(sl, "_SCAN_PATH", str(cache))
    old = tmp_path / "jsonl-scan-cache.json.1234.tmp"
    old.write_text("{}", encoding="utf-8")
    _os.utime(old, (_t.time() - 3600, _t.time() - 3600))
    new = tmp_path / "jsonl-scan-cache.json.5678.tmp"
    new.write_text("{}", encoding="utf-8")                            # 다른 렌더가 지금 쓰는 중일 수 있음 → 보존
    other = tmp_path / "jsonl-scan-cache.json.abc.tmp"
    other.write_text("{}", encoding="utf-8")
    _os.utime(other, (_t.time() - 3600, _t.time() - 3600))            # 이름 규칙이 다른 파일은 손대지 않음
    monkeypatch.setattr(sl, "_SCAN", {"k": 1})
    monkeypatch.setattr(sl, "_SCAN_DIRTY", True)
    monkeypatch.setattr(sl.os, "replace", lambda a, b: (_ for _ in ()).throw(PermissionError("in use")))
    sl._scan_save()
    assert not (tmp_path / f"jsonl-scan-cache.json.{_os.getpid()}.tmp").exists()   # 실패한 자기 임시 파일 제거
    assert not old.exists() and new.exists() and other.exists()


# ── R264 상태줄 작업 현황 (원장 동적 · FIFO 와 실행 구분) ─────────────────
def _q(L, reqs, cur_id):
    return L.summarize(reqs, cur_id)["queue"]


def test_r264_queue_oldest_waiting_later_running_and_counts_change():
    L = _load("L_r264", KIT / ".claude/scripts/request-ledger.py")
    S = "sess-a"
    reqs = [{"id": "R1", "session_id": S, "status": "approval_required"},            # 가장 오래된 = 실환경·승인 대기
            {"id": "R2", "session_id": S, "status": "verified", "verification": "PARTIAL",
             "items": [{"i": 1, "state": "done"}, {"i": 2, "state": "open"}]},       # 게이트 통과 후 커밋·전파 대기 = 부분
            {"id": "R3", "session_id": S, "status": "pending"},                          # 실제 실행 중
            {"id": "R4", "session_id": "other", "status": "pending"},                    # 다른 세션 = 제외
            {"id": "R5", "session_id": S, "status": "completed"}]                        # 완료 = 남은 수 제외
    q = _q(L, reqs, "R3")
    assert q["remaining"] == 3 and q["running"] == "R3" and q["oldest"] == "R1"
    assert q["waiting"] == ["R1 확인필요"] and q["next"] == ["R2(1/2)부분"]        # 앞의 대기 때문에 뒤가 막혀 보이지 않음
    reqs[1]["status"], reqs[1]["verification"] = "completed", "PASS"                  # R2 완료 → 남은 수 감소
    q = _q(L, reqs, "R3")
    assert q["remaining"] == 2 and q["next"] == []
    reqs.append({"id": "R6", "session_id": S, "status": "verified", "verification": "BLOCKED"})
    assert "R6 차단" in _q(L, reqs, "R3")["waiting"]
    assert _q(L, reqs, "R9")["remaining"] == 0                                        # 원장에 없는 현재 요청 = 표시 안 함


def test_r264_statusline_request_line_shows_queue_first():
    src = (KIT / ".claude/scripts/statusline_context.py").read_text(encoding="utf-8")
    i = src.index('_qp = [f"남은{_q[\'remaining\']}"')
    assert i > 0 and 'f"대기{len(_q[\'waiting\'])}' in src and '"다음" + "→".join(_nx[:2])' in src


def test_r264_plain_declarative_directive_is_registered_but_report_is_not():
    """11-16 «전체 요구사항 복원» 지시(평서형 '~확인한다.')가 pasted_report 로 분류돼 미등록되던 것."""
    import sys as _s
    _s.path.insert(0, str(KIT / ".claude/hooks/prompt"))
    R = _load("R_r264", KIT / ".claude/hooks/prompt/ledger_auto_register.py")
    spec = ("<pasted_content id=\"1\">\n# 작업\n\n## 1. 대조\n원문을 시간순으로 조사한다.\n추측하지 않는다.\n"
            "## 2. 검증\n변경 파일이 실제 검증됐는지 확인한다.\n모든 보고는 한국어로 작성한다.\n</pasted_content id=\"1\">")
    assert R._intent_text(spec)[1] == "pasted_directive"
    report = ("<pasted_content id=\"2\">\n이번 작업은 완료됐습니다.\n시험 640건이 통과했습니다.\n전파도 끝났습니다.\n"
              "다음 실행 때 측정된다.\n</pasted_content id=\"2\">")                    # 보고 문장이 더 많음 → 보고
    assert R._intent_text(report)[1] == "pasted_report"
    two = "<pasted_content id=\"3\">\n결과를 확인한다.\n기록을 남긴다.\n</pasted_content id=\"3\">"   # 평서 2줄 = 약한 표지 부족
    assert R._intent_text(two)[1] == "pasted_report"


def test_r268_ready_penalty_counts_unique_errors(tmp_path):
    """R268: 같은 오류가 시각만 바뀌어 10줄 기록돼도 READY 감점은 고유 1건 · 다른 오류는 따로 센다 · 표시 건수는 그대로."""
    import time as _t
    sl = _load("sl_r268", KIT / ".claude/scripts/statusline_context.py")
    logs = tmp_path / ".claude" / "logs"
    logs.mkdir(parents=True)
    now = _t.strftime("%Y-%m-%d %H:%M:", _t.localtime())
    rows = [f"{now}{i:02d} 740899f3 Q12_startup=FAIL · Q11=PARTIAL" for i in range(10)]
    rows.append(f"{now}30 abcdef12 other.py: Traceback boom")
    (logs / "q.log").write_text("\n".join(rows) + "\n", encoding="utf-8")
    c, e, w, rpt, top = sl.recent_log_issues(str(tmp_path))
    assert e == 11 and sl._LOG_UNIQUE_ERRS == 2


def test_r270_control_line_counts_existing_records(tmp_path):
    """R270 통제 줄: 승인 차단·검증 미완료를 기존 기록에서 센다 · 시험 임시 폴더 명령은 제외 · 기록 없는 항목은 «미계측»(0 아님)."""
    import json as _j
    import time as _t
    sl = _load("sl_r270", KIT / ".claude/scripts/statusline_context.py")
    logs = tmp_path / ".claude" / "logs"
    logs.mkdir(parents=True)
    now = _t.strftime("%Y-%m-%d_%H:%M:%S")
    old = _t.strftime("%Y-%m-%d_%H:%M:%S", _t.localtime(_t.time() - 3 * 86400))
    (logs / "approval-gate.log").write_text("\n".join([
        f"[{now}] BLOCK: irreversible | task_id=a1 | cmd=git push --force origin main",          # 실제 차단
        f"[{now}] BLOCK: cost | task_id=a2 | cmd=sh C:/x/Temp/pytest-of-u/pytest-1/t/risky.sh",  # 시험 명령 → 제외
        f"[{old}] BLOCK: data_loss | task_id=a3 | cmd=rm -rf x",                                  # 24시간 지남 → 제외
        f"[{now}] REQUEST: cost | task_id=a4"]) + "\n", encoding="utf-8")
    ev = lambda st, ts: _j.dumps({"kind": "test", "step": "regression-gate", "status": st, "ts": ts})
    (logs / "trace-events.jsonl").write_text("\n".join([
        ev("blocked", _t.time()), ev("unknown", _t.time()), ev("success", _t.time()), ev("blocked", _t.time() - 3 * 86400)]) + "\n",
        encoding="utf-8")
    line = sl._control_line(str(tmp_path))
    assert "승인차단 1" in line and "검증skip 2" in line and "범위 lock꺼짐" in line and "임의변경·추측수정 미계측" in line
    empty = tmp_path / "none"
    (empty / ".claude").mkdir(parents=True)
    line2 = sl._control_line(str(empty))
    assert "승인차단 미측정" in line2 and "검증skip 미측정" in line2   # 기록 파일 없음 = 0 이 아니라 미측정


def test_r270_merge_apply_records_deploy_log(tmp_path, monkeypatch):
    """R270: 전파 반영 1회 = kit 로그 1줄 (READY «배포» 원천) · 기록 위치는 kit (시험은 임시 폴더로 돌림)."""
    mt = _load("mt_r270", KIT / ".claude/scripts/merge-to-target.py")
    monkeypatch.setattr(mt, "KIT", tmp_path)
    mt._record_apply(tmp_path / "T", "--only 2개 · 판정 정상")
    t = (tmp_path / ".claude" / "logs" / "merge-to-target.log").read_text(encoding="utf-8")
    assert "APPLY" in t and "--only 2개" in t and t.count("\n") == 1
