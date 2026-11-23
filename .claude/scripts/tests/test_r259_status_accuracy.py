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
    assert "승인차단 1" in line and "검증skip 2" in line and "범위 lock꺼짐" in line and "임의변경 미측정" in line and "추측수정 미측정" in line   # R275 개별 계측
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


def test_r273_queue_running_only_while_processing():
    """R273: 최신 요청 ≠ 실행 중. 처리 중(pending·implemented)만 실행 · PARTIAL·BLOCKED·승인대기로 끝나면 «최근» · 미완료 수는 그대로."""
    rl = _load("rl_r273", KIT / ".claude/scripts/request-ledger.py")
    mk = lambda rid, st, ver="": {"id": rid, "session_id": "s", "status": st, "verification": ver}
    base = [mk("R1", "approval_required"), mk("R2", "pending")]
    cases = [  # (현재 요청 상태, 검증, 기대 실행, 기대 최근)
        ("pending", "", "R9", ""),                       # 요청 실행 중
        ("implemented", "", "R9", ""),                   # 수정·시험·push·해시 확인 중 (아직 종료 기록 전)
        ("verified", "PARTIAL", "", "R9부분"),           # 대상 격리 시험 미검증 → PARTIAL 로 보고 종료
        ("verified", "BLOCKED", "", "R9차단"),
        ("approval_required", "", "", "R9확인필요"),
    ]
    for st, ver, run, last in cases:
        cur = mk("R9", st, ver)
        q = rl.queue_view(base + [cur], cur)
        assert q["running"] == run and q["last"] == last, (st, ver, q)
        assert q["remaining"] == 3                        # 끝난 현재 요청도 미완료로 남음 (숨기지 않음)
    done = mk("R9", "completed", "PASS")                  # 모든 실행 종료 · 미완료만 남음
    q = rl.queue_view(base + [done], done)
    assert q["running"] == "" and q["last"] == "R9완료" and q["remaining"] == 2 and q["next"] == ["R2"]
    s = rl.summarize(base + [mk("R9", "verified", "PARTIAL")], "R9")
    assert s["current_verification"] == "PARTIAL"


def test_r273_dev_line_eta_only_while_processing():
    """R273: 개발 줄 남은 시간은 처리 중일 때만 · PARTIAL 은 «부분완료» (소스 계약)."""
    src = (KIT / ".claude/scripts/statusline_context.py").read_text(encoding="utf-8")
    assert 'if _cs in ("pending", "implemented"):' in src and '"PARTIAL": "부분완료"' in src and "최근{_q['last']}" in src


def test_r355_debug_lines_are_not_errors(tmp_path):
    """R355: 'DEBUG: Search for 'error: 숫자' ...' 처럼 검색어에 error 글자가 든 DEBUG 기록이 상태줄 «error 1»·
    프롬프트 오류 알림으로 세지던 것 (11-23 실측 common.log) → 수준이 DEBUG 인 줄은 오류·경고 판정에서 뺀다 · 실제 ERROR 는 그대로."""
    import sys as _s
    import time as _t
    sl = _load("sl_r355", KIT / ".claude/scripts/statusline_context.py")
    logs = tmp_path / ".claude" / "logs"
    logs.mkdir(parents=True)
    now = _t.strftime("%Y-%m-%d %H:%M:%S", _t.localtime())
    (logs / "common.log").write_text(
        f"[{now}] DEBUG: Search for 'error: \\d+' in 1 files: 2 matches\n"
        f"[{now}] DEBUG: retry after FAILED fetch (warn)\n", encoding="utf-8")
    c, e, w, rpt, top = sl.recent_log_issues(str(tmp_path))
    assert (c, e, w) == (0, 0, 0)
    _s.path.insert(0, str(KIT / ".claude" / "hooks" / "prompt"))
    m = _load("sle_r355", KIT / ".claude/hooks/prompt/surface_log_errors.py")
    assert m._scan(str(logs)) == {}
    (logs / "common.log").write_text(f"[{now}] ERROR: real failure in x.py\n", encoding="utf-8")
    assert sl.recent_log_issues(str(tmp_path))[1] == 1                  # 실제 ERROR 는 그대로 센다
    assert any(d["kind"] == "ERROR" for d in m._scan(str(logs)).values())


def test_r355_mcp_refresh_retries_transient_failure(tmp_path):
    """R355: 일시 연결 시간 초과가 실패로 굳던 것 → 실패가 보이면 재확인 1번 · 결과·시작을 mcp-health.log 에 남김."""
    import os as _o
    import subprocess as _sp
    import sys as _s
    root = tmp_path / "kit"
    (root / ".claude" / "scripts").mkdir(parents=True)
    src = (KIT / ".claude/scripts/refresh-mcp-status.sh").read_text(encoding="utf-8")
    (root / ".claude/scripts/refresh-mcp-status.sh").write_text(src, encoding="utf-8", newline="\n")
    fake = tmp_path / "bin"
    fake.mkdir()
    cnt = tmp_path / "n"
    (fake / "claude").write_text(                                  # 첫 호출 = 1개 실패 · 두 번째 = 모두 연결
        f'#!/usr/bin/env bash\nn=$(cat "{cnt.as_posix()}" 2>/dev/null || echo 0); echo $((n+1)) > "{cnt.as_posix()}"\n'
        'echo "a: x - ✔ Connected"\nif [ "$n" = 0 ]; then echo "b: y - ✗ Failed to connect"; else echo "b: y - ✔ Connected"; fi\n',
        encoding="utf-8", newline="\n")
    _s.path.insert(0, str(KIT / ".claude" / "hooks" / "prompt"))
    from _common import bash_exe
    env = {**_o.environ, "MCP_REFRESH_RETRY_SEC": "0"}
    r = _sp.run([bash_exe(), "-c", f'export PATH="$(cygpath -u "{fake}" 2>/dev/null || echo "{fake.as_posix()}"):$PATH"; chmod +x "$(dirname "$0")/../../bin/claude" 2>/dev/null; bash "$0"',
                 str(root / ".claude/scripts/refresh-mcp-status.sh")], env=env, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 0, r.stderr
    st = json.loads((root / ".claude/state/mcp-status.json").read_text(encoding="utf-8"))
    assert (st["connected"], st["failed"]) == (2, 0)              # 재확인 결과가 기록됨
    log = (root / ".claude/logs/mcp-health.log").read_text(encoding="utf-8")
    assert "start" in log and "재확인" in log and "connected=2 failed=0" in log


def test_r355_spawn_refresh_falls_back_without_breakaway(monkeypatch):
    """R355: 작업 묶음 밖 실행(BREAKAWAY)이 막힌 환경이면 종전 플래그로 한 번 더 띄운다."""
    import subprocess as _sp
    sl = _load("sl_r355s", KIT / ".claude/scripts/statusline_context.py")
    seen = []

    def fake(args, **kw):
        seen.append(kw.get("creationflags", 0))
        if len(seen) == 1 and sl.os.name == "nt":
            raise OSError("access denied")
        return None
    monkeypatch.setattr(_sp, "Popen", fake)
    sl._spawn_refresh("x.sh")
    if sl.os.name == "nt":
        assert seen[0] & 0x01000000 and not (seen[1] & 0x01000000) and len(seen) == 2
    else:
        assert len(seen) == 1


def test_r355_drift_baseline_follows_gated_commit(tmp_path):
    """R355: 핵심 파일 기준선이 수동 'baseline' 에만 의존해 회귀 게이트를 통과해 커밋된 승인 변경까지 'frozen ⚠ 위반' 으로
    영구 표시되던 것 (11-23 실측: 11-18 기준선 · 핵심 4개 모두 커밋됨) → 핵심·규칙·훅·agent 에 미커밋 변경이 없고
    회귀 게이트 기록(status pass·tree = HEAD tree)이 있을 때만 기준선을 자동 갱신 · 미커밋 핵심 수정은 계속 위반."""
    import os as _o
    import subprocess as _sp
    import sys as _s
    r = tmp_path / "kit"
    (r / ".claude" / "rules").mkdir(parents=True)
    (r / ".claude" / "scripts").mkdir()
    (r / ".claude" / "state").mkdir()
    (r / ".claude/scripts/drift-detect.py").write_bytes((KIT / ".claude/scripts/drift-detect.py").read_bytes())
    for p in ("CLAUDE.md", ".claude/rules/operational-freeze.md"):
        (r / p).write_text("v1\n", encoding="utf-8")

    def git(*a):
        return _sp.run(["git", "-C", str(r), *a], capture_output=True, text=True, check=True).stdout.strip()
    for a in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        git(*a)
    git("add", "-A"); git("commit", "-qm", "v1")
    env = {**_o.environ, "CLAUDE_PROJECT_DIR": str(r)}

    def status():
        return _sp.run([_s.executable, "-X", "utf8", str(r / ".claude/scripts/drift-detect.py"), "status"], env=env,
                       capture_output=True, text=True, encoding="utf-8").stdout

    def stamp(tree, st="pass"):
        (r / ".claude/state/regression-gate.json").write_text(json.dumps({"tree": tree, "status": st}), encoding="utf-8")
    assert "✅" in status()                                                  # 첫 실행 = 기준선 저장
    (r / "CLAUDE.md").write_text("v2\n", encoding="utf-8")
    assert "위반" in status()                                                # 미커밋 핵심 수정 = 위반
    git("add", "-A"); git("commit", "-qm", "v2")
    stamp("0" * 40)
    assert "위반" in status()                                                # 게이트 기록이 이 커밋 tree 가 아님 = 위반 유지
    stamp(git("rev-parse", "HEAD^{tree}"), "regression")
    assert "위반" in status()                                                # 게이트 실패 기록 = 위반 유지
    stamp(git("rev-parse", "HEAD^{tree}"))
    assert "✅" in status()                                                  # 게이트 통과 커밋 = 기준선 자동 갱신
    assert "✅" in status()


def test_r355_health_orphan_and_duplicate_use_real_checks(monkeypatch, tmp_path):
    """R355: HEALTH 'orphan 37' 은 sync 가 이름을 바꿔 복사한 명령(mcp_dev-install.md 등)까지 원본 없음으로 셌고
    (sync 점검 실측 5 → 원본 이동 뒤 0), '중복 8' 은 이름 앞부분(check-*·detect-*) 묶음 수였다 (내용 동일 파일 실측 0)
    → orphan = sync-plugins --check 의 수 (SoT) · 중복 = 규칙·훅 중 내용이 완전히 같은 파일 수."""
    hc = _load("hc_r355", KIT / ".claude/scripts/health-check.py")
    monkeypatch.setattr(hc, "_run_py", lambda s, a: (2, "  orphan: 3\n  (check mode)") if s == "sync-plugins.py" else (1, ""))
    o = hc.check_orphan()
    assert (o["ok"], o["value"]) == (False, 3)
    monkeypatch.setattr(hc, "_run_py", lambda s, a: (0, "  orphan: 0\n"))
    assert (hc.check_orphan()["ok"], hc.check_orphan()["value"]) == (True, 0)
    monkeypatch.setattr(hc, "_run_py", lambda s, a: (1, ""))
    assert hc.check_orphan()["ok"] is False and hc.check_orphan()["value"] == "?"     # 점검 실패 = 미측정 (0 아님)
    r = tmp_path / "kit"
    (r / ".claude" / "rules").mkdir(parents=True)
    (r / ".claude" / "hooks").mkdir()
    for n in ("check-a.sh", "check-b.sh", "check-c.sh", "check-d.sh", "check-e.sh"):    # 이름만 비슷 · 내용 다름
        (r / ".claude/hooks" / n).write_text(n, encoding="utf-8")
    monkeypatch.setattr(hc, "ROOT", str(r))
    assert (hc.check_duplicates()["ok"], hc.check_duplicates()["value"]) == (True, 0)
    (r / ".claude/rules/x.md").write_text("same", encoding="utf-8")
    (r / ".claude/rules/y.md").write_text("same", encoding="utf-8")
    d = hc.check_duplicates()
    assert (d["ok"], d["value"]) == (False, 1) and sorted(d["detail"][0]) == [".claude/rules/x.md", ".claude/rules/y.md"]


def test_r356_req_progress_incremental_equals_full(tmp_path, monkeypatch):
    """R356: 상태줄이 렌더마다 trace-events.jsonl(11-23 실측 5MB·9,524줄)을 처음부터 읽어 진행률 계산에 0.12초 →
    같은 요청이면 지난번 읽은 위치부터 늘어난 줄만 읽음 · 결과는 전체 재계산과 같아야 함 · 요청 변경·파일 축소 = 처음부터."""
    import json as _j
    import shutil
    sl = _load("sl_r356", KIT / ".claude/scripts/statusline_context.py")
    r = tmp_path / "kit"
    (r / ".claude/scripts/lib").mkdir(parents=True)
    (r / ".claude/state").mkdir()
    (r / ".claude/logs").mkdir()
    (r / "plugins/exec_orch").mkdir(parents=True)                                  # kit 표지 = 6단계 고정
    (r / ".claude-plugin").mkdir()
    (r / ".claude-plugin/plugin.json").write_text("{}", encoding="utf-8")
    shutil.copy(KIT / ".claude/scripts/lib/trace.py", r / ".claude/scripts/lib/trace.py")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(r))
    log = r / ".claude/logs/trace-events.jsonl"

    def cur(tid, rid):
        (r / ".claude/state/current-trace.json").write_text(_j.dumps({"trace_id": tid, "rid": rid}), encoding="utf-8")

    def add(tid, step, inp, ts, status="success", kind="tool"):
        with open(log, "a", encoding="utf-8") as f:
            f.write(_j.dumps({"trace_id": tid, "kind": kind, "status": status, "step": step, "ts": ts,
                              "detail": _j.dumps({"input": inp})}, ensure_ascii=False) + "\n")
    cache = r / ".claude/state/req-progress-cache.json"

    def full():
        cache.unlink(missing_ok=True)
        return sl._req_progress(str(r))
    cur("t1", "R1")
    add("t1", "", "", 1.0, status="start", kind="request")
    add("t1", "Edit", "a.py", 2.0)
    add("t2", "Bash", "git commit -m x", 2.5)                                       # 다른 요청 = 무시
    first = sl._req_progress(str(r))
    assert first[:4] == ("R1", 1, 6, "수정") and cache.exists()
    add("t1", "Bash", "python -m pytest -q", 3.0)
    with open(log, "a", encoding="utf-8") as f:
        f.write('{"trace_id": "t1", "kind": "tool", "sta')                         # 쓰는 중인 반쪽 줄
    inc = sl._req_progress(str(r))
    assert inc[:4] == ("R1", 2, 6, "시험")
    with open(log, "a", encoding="utf-8") as f:
        f.write('tus": "success", "step": "Bash", "ts": 4.0, "detail": "{\\"input\\": \\"git commit -m y\\"}"}\n')
    inc = sl._req_progress(str(r))
    assert inc == full() and inc[:4] == ("R1", 3, 6, "커밋")                       # 반쪽 줄을 이어 읽음 · 전체 재계산과 같음
    cur("t2", "R2")
    assert sl._req_progress(str(r))[:4] == ("R2", 1, 6, "커밋")                     # 요청 변경 = 처음부터
    log.write_text("", encoding="utf-8")
    add("t2", "Edit", "b.py", 5.0)
    assert sl._req_progress(str(r))[:4] == ("R2", 1, 6, "수정")                     # 파일 축소(교체) = 처음부터
