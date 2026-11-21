"""R354 PARTIAL 정체 복구 — 보고 뒤 남은 일이 원장 하위 항목(owner)으로 남고, 큐가 next-actions collab 블록으로 재개에 주입된다.

수정 전 실패 (재현):
- 원장에 하위 항목을 추가하는 명령이 없어 등록 원문에 번호 줄이 없던 PARTIAL 은 남은 일이 보고서 본문에만 있었다 (18/19 건 items 0개).
- R346 후속 9 이후 보고된 PARTIAL 은 poll 이 다시 깨우지 않는데, 남은 일을 담는 큐가 없어 세션이 닫히면 조용히 정체했다.
- 재개 주입(resume_text)은 자동 블록을 24시간 안일 때만 넣어, 며칠 닫혀 있던 세션은 남은 일을 받지 못한다.
"""
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_r325_ai_collab import _origin, _push_file, _repo, _run, _state  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
LEDGER = ROOT / ".claude" / "scripts" / "request-ledger.py"
NEXT = ROOT / ".claude" / "scripts" / "auto-save-next-actions.py"


def _ledger(r: Path, *args):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(r), "PYTHONUTF8": "1"}
    return subprocess.run([sys.executable, "-X", "utf8", str(LEDGER), *args], env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60, cwd=str(r))


def _items(r: Path, rid: str) -> list:
    led = json.loads((r / ".claude" / "state" / "request-ledger.json").read_text(encoding="utf-8"))
    return next(x for x in led["requests"] if x["id"] == rid).get("items") or []


def _na(r: Path) -> str:
    p = r / ".claude" / "state" / "next-actions.md"
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def _resume(r: Path, max_age: float = 86400.0) -> str:
    spec = importlib.util.spec_from_file_location("_na_r354", NEXT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.OUT = r / ".claude" / "state" / "next-actions.md"
    m.LOCK = m.OUT.with_suffix(".md.lock") if hasattr(m, "LOCK") else None
    return m.resume_text(max_age)


def _unlisted_partial(r: Path):
    led_p = r / ".claude" / "state" / "request-ledger.json"
    led = json.loads(led_p.read_text(encoding="utf-8"))
    led["requests"].append({"id": "R3", "desc": "항목 없는 부분", "status": "verified", "verification": "PARTIAL"})
    led_p.write_text(json.dumps(led, ensure_ascii=False), encoding="utf-8")


def test_item_add_owner_and_duplicates(tmp_path):
    r = _repo(tmp_path)
    assert _ledger(r, "item-add", "R2", "사용자 화면 캡처로 2줄 가림 판정", "--owner", "external").returncode == 0
    assert _ledger(r, "item-add", "R2", "공식 문서 본문 대조").returncode == 0
    again = _ledger(r, "item-add", "R2", "공식 문서 본문 대조")
    assert again.returncode == 0 and "추가 X" in again.stdout              # 같은 글은 다시 넣지 않음
    assert _ledger(r, "item-add", "R2", "x", "--owner", "someone").returncode == 2
    assert _ledger(r, "item-add", "R2", "   ").returncode == 2
    assert _ledger(r, "item-add", "R99", "없는 요청").returncode == 2
    it = _items(r, "R2")
    assert [x["i"] for x in it] == [1, 2, 3] and it[1]["owner"] == "external" and it[2]["owner"] == "claude"
    # PASS 는 열린 항목이 있으면 거부 (R261 계약 그대로)
    assert _ledger(r, "complete", "R2", "--evidence", "e", "--verification", "PASS").returncode != 0


def test_queue_lists_open_items_and_unlisted_partial(tmp_path):
    r = _repo(tmp_path)
    _unlisted_partial(r)
    assert _run(r, "report", "R2", "--status", "PARTIAL").returncode == 0
    assert _run(r, "report", "R3", "--status", "PARTIAL").returncode == 0
    rep3 = (r / ".ai-collab" / "reports" / "R3.md").read_text(encoding="utf-8")
    assert "남은 일 미정리" in rep3                                            # 빈 «남은 문제» 제목만 두지 않음
    _ledger(r, "item-add", "R2", "캡처 판정", "--owner", "external")
    q = _run(r, "queue")
    assert q.returncode == 0
    assert "R2#1 [claude] 남은 것" in q.stdout and "R2#2 [external] 캡처 판정" in q.stdout
    assert "R3 (PARTIAL) — 남은 일 미정리" in q.stdout                       # 조용히 빠지지 않음
    assert "실행 가능 [claude] 1 · 외부 증거 필요 [external] 1 · 미정리 1" in q.stdout
    na = _na(r)
    assert "<!-- AUTO:collab BEGIN -->" in na and "R2#2 [external]" in na
    assert "R1" not in q.stdout.split("\n", 1)[1]                              # 완료(PASS) 요청은 큐에 없음


def test_queue_drains_when_items_done(tmp_path):
    r = _repo(tmp_path)
    assert _run(r, "report", "R2", "--status", "PARTIAL").returncode == 0
    assert "R2#1" in _run(r, "queue").stdout
    assert _ledger(r, "item", "R2", "1", "done", "--evidence", "시험 통과").returncode == 0
    assert _ledger(r, "complete", "R2", "--evidence", "모든 항목 끝", "--verification", "PASS").returncode == 0
    q = _run(r, "queue")
    assert "남은 협업 요청 없음" in q.stdout
    assert "AUTO:collab" not in _na(r)                                          # 끝나면 블록 제거 (수동 지시는 그대로)


def test_resume_injects_collab_even_when_old(tmp_path):
    """며칠 닫혀 있던 세션도 남은 일을 받는다 (answer·goals 블록은 종전대로 24시간 조건)."""
    r = _repo(tmp_path)
    assert _run(r, "report", "R2", "--status", "PARTIAL").returncode == 0
    assert _run(r, "queue").returncode == 0
    p = r / ".claude" / "state" / "next-actions.md"
    old = time.time() - 5 * 86400
    os.utime(p, (old, old))
    txt = _resume(r)
    assert "보고는 했지만 끝나지 않은 협업 요청" in txt and "R2#1 [claude]" in txt
    assert "[external] 항목은 실행하지 말고" in txt


def test_poll_keeps_quiet_but_refreshes_queue(tmp_path):
    """보고된 PARTIAL 은 다시 깨우지 않되(R346 후속 9 유지) 남은 일은 collab 큐에 남는다 (같은 요청 두 번 소비 X)."""
    r = _repo(tmp_path)
    other = _origin(tmp_path, r)
    _push_file(other, ".ai-collab/requests/R2.md", '---\nrequest_id: "R2"\n---\n지시 B\n')
    time.sleep(1.1)
    assert _run(r, "poll").returncode == 0
    assert _run(r, "report", "R2", "--status", "PARTIAL").returncode == 0
    p = r / ".claude" / "state" / "next-actions.md"
    p.unlink(missing_ok=True)                                                  # 큐 사본이 사라진 상태(재시작 등)
    st = _state(r)
    for v in st.get("inflight", {}).values():
        v["at"] = "2000-01-01T00:00:00+00:00"                                  # 임대 만료
    (r / ".ai-collab" / "state.json").write_text(json.dumps(st), encoding="utf-8")
    quiet = _run(r, "poll")
    assert quiet.returncode == 3, quiet.stdout                                 # 다시 깨우지 않음
    assert "남은 실행 가능 항목 1" in quiet.stdout
    assert "R2#1 [claude]" in _na(r)                                           # 큐는 다시 채워짐
    assert _run(r, "poll").returncode == 3                                     # 두 번째도 조용 (중복 소비 X)


def test_fault_github_unreachable_then_recover_exactly_once(tmp_path):
    """R346 P1 장애 실험 (격리 저장소): 원격 접속 실패 → poll 2·상태 무변경 · wait 는 연속 3회 실패에서만 2 (무한 재시도 X) ·
    원격 복구 뒤 새 요청을 한 번만 전달 (임대 안 중복 X) · 복구 시간 측정."""
    import shutil as _sh
    r = _repo(tmp_path)
    other = _origin(tmp_path, r)
    _push_file(other, ".ai-collab/requests/R2.md", '---\nrequest_id: "R2"\n---\n지시 C\n')
    bare = tmp_path / "origin.git"
    moved = tmp_path / "origin-offline.git"
    bare.rename(moved)                                                         # 원격 접속 불가 흉내
    st_before = (r / ".ai-collab" / "state.json").read_text(encoding="utf-8") if (r / ".ai-collab" / "state.json").exists() else ""
    bad = _run(r, "poll")
    assert bad.returncode == 2 and "fetch 실패" in bad.stderr
    st_after = (r / ".ai-collab" / "state.json").read_text(encoding="utf-8") if (r / ".ai-collab" / "state.json").exists() else ""
    assert st_after == st_before                                               # 실패가 상태를 바꾸지 않음
    t0 = time.time()
    w = _run(r, "wait", "--interval", "0.2", "--max-sec", "30")
    assert w.returncode == 2 and time.time() - t0 < 25                         # 연속 3회 실패에서 끝남 (재시도 상한)
    moved.rename(bare)                                                         # 복구
    t1 = time.time()
    hit = _run(r, "poll")
    rto = time.time() - t1
    assert hit.returncode == 0 and "지시 C" in hit.stdout and rto < 30
    assert _run(r, "poll").returncode == 3                                     # 임대 안 = 다시 전달 안 함 (중복 0)


def test_fault_crash_before_state_replace_keeps_original(tmp_path):
    """저장 도중 끊김 흉내: 쓰다 만 state.tmp 가 남아도 원본 state.json 은 그대로 읽히고 다음 저장이 덮어써 정리된다."""
    r = _repo(tmp_path)
    assert _run(r, "report", "R2", "--status", "PARTIAL").returncode == 0
    good = _state(r)
    (r / ".ai-collab" / "state.tmp").write_text('{"requests": {"R2": ', encoding="utf-8")   # 깨진 반쪽 파일
    assert _state(r) == good                                                   # 원본 보존
    q = _run(r, "queue", "--no-write")
    assert q.returncode == 0 and "R2#1" in q.stdout
    assert _run(r, "report", "R1").returncode == 0                             # 다음 저장 정상
    assert not (r / ".ai-collab" / "state.tmp").exists() and "R1" in _state(r)["requests"]


def test_report_refreshes_when_items_change_and_keeps_human_sections(tmp_path):
    """R354: head·상태가 같아도 남은 일(하위 항목)이 바뀌면 보고서 갱신 · 다시 만들 때 사람이 쓴 절은 그대로 · 자동 절은 한 번만."""
    r = _repo(tmp_path)
    assert _run(r, "report", "R2", "--status", "PARTIAL").returncode == 0
    p = r / ".ai-collab" / "reports" / "R2.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n## 판정 근거 (사람이 씀)\n\n- 상세 분석 표 A\n", encoding="utf-8")
    _ledger(r, "item-add", "R2", "새로 찾은 남은 일", "--owner", "external")
    again = _run(r, "report", "R2", "--status", "PARTIAL")
    assert again.returncode == 0 and "변경 없음" not in again.stdout, again.stdout   # 항목 변화 = 갱신
    t = p.read_text(encoding="utf-8")
    assert "새로 찾은 남은 일" in t and "외부 증거 필요" in t
    assert "## 판정 근거 (사람이 씀)" in t and "상세 분석 표 A" in t                  # 사람이 쓴 절 보존
    assert t.count("## 남은 문제") == 1 and t.count("## 커밋") == 1                 # 자동 절 중복 X
    same = _run(r, "report", "R2", "--status", "PARTIAL")
    assert "변경 없음" in same.stdout                                               # 아무것도 안 바뀌면 그대로 건너뜀


def test_queue_write_failure_is_visible_and_recovers(tmp_path):
    """R354 검토 P1: next-actions 기록이 실패해도(자식 exit 1 · 기록 불가) queue 가 성공처럼 끝나던 것 →
    queue rc 1 + stderr 원인 · report·poll 은 본 작업은 끝내되 경고와 state.json queue_error 로 관찰 가능 ·
    원인 해소 뒤 다음 queue 가 복구하고 재개 주입까지 이어짐 (무한 재시도 X · 기존 상태 보존)."""
    r = _repo(tmp_path)
    assert _run(r, "report", "R2", "--status", "PARTIAL").returncode == 0
    na = r / ".claude" / "state" / "next-actions.md"
    na.unlink(missing_ok=True)
    na.mkdir(parents=True)                                                     # 파일 자리에 폴더 = 기록 불가 주입
    q = _run(r, "queue")
    assert q.returncode == 1 and "collab 큐 기록 실패" in q.stderr, (q.returncode, q.stderr)
    _ledger(r, "item-add", "R2", "기록 실패 중 새 항목")                         # 보고서를 다시 만들 변화
    rep = _run(r, "report", "R2", "--status", "PARTIAL")
    assert rep.returncode == 0 and "collab 큐 기록 실패" in rep.stderr, rep.stderr   # 보고는 끝내되 경고
    st = _state(r)
    assert st.get("queue_error", {}).get("rc") not in (None, 0)                 # 관찰 가능한 기록
    assert (r / ".ai-collab" / "reports" / "R2.md").is_file()                   # 본 작업(보고서) 보존
    na.rmdir()                                                                  # 원인 해소
    ok = _run(r, "queue")
    assert ok.returncode == 0 and "R2#1" in ok.stdout
    assert "queue_error" not in _state(r)                                       # 복구되면 오류 기록 해제
    assert "R2#1 [claude]" in _resume(r)                                        # 다음 세션 재개까지 이어짐


def test_queue_error_record_failure_keeps_original_error_and_state(tmp_path):
    """R354 2차 검토 P1: queue_error 를 적는 state 저장 자체가 실패(원자 교체 전 임시 파일 쓰기 실패)하면
    예외가 원래 오류(next-actions 기록 실패)를 덮었다 → 두 실패를 모두 stderr 에 · queue rc 1 · 기존 state.json 보존 ·
    원인 해소 뒤 다음 queue 가 복구 (무한 재시도·원장 삭제 X)."""
    r = _repo(tmp_path)
    assert _run(r, "report", "R2", "--status", "PARTIAL").returncode == 0
    st_path = r / ".ai-collab" / "state.json"
    before = st_path.read_bytes()
    na = r / ".claude" / "state" / "next-actions.md"
    na.unlink(missing_ok=True); na.mkdir()                                     # 원래 오류: 재개 큐 기록 불가
    (r / ".ai-collab" / "state.tmp").mkdir()                                   # 2차 오류: state 저장 불가
    q = _run(r, "queue")
    assert q.returncode == 1, (q.returncode, q.stderr)
    assert "collab 큐 기록 실패" in q.stderr and "queue_error 기록 실패" in q.stderr, q.stderr   # 원래 오류가 덮이지 않음
    assert "Traceback" not in q.stderr
    assert st_path.read_bytes() == before                                       # 기존 state 보존
    (r / ".ai-collab" / "state.tmp").rmdir(); na.rmdir()                        # 원인 해소
    ok = _run(r, "queue")
    assert ok.returncode == 0 and "queue_error" not in _state(r) and "R2#1 [claude]" in _resume(r)


def test_double_failure_surfaces_in_next_session_via_log_scanner(tmp_path):
    """R354 3차 검토 P2: 재개 큐 기록 실패 + queue_error 저장 실패면 stderr 에만 남아 다음 세션이 놓쳤다 →
    .claude/logs/ai-collab.log 에 시각 있는 ERROR 1줄 · 기존 «로그 오류 자동 점검»(surface_log_errors._scan) 이 실제로 찾아냄."""
    r = _repo(tmp_path)
    assert _run(r, "report", "R2", "--status", "PARTIAL").returncode == 0
    na = r / ".claude" / "state" / "next-actions.md"
    na.unlink(missing_ok=True); na.mkdir()
    (r / ".ai-collab" / "state.tmp").mkdir()
    assert _run(r, "queue").returncode == 1
    log = r / ".claude" / "logs" / "ai-collab.log"
    line = log.read_text(encoding="utf-8").strip().splitlines()[-1]
    assert "[ERROR]" in line and "state.json queue_error 기록도 실패" in line, line
    sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "prompt"))
    spec = importlib.util.spec_from_file_location("_sle_r354", ROOT / ".claude" / "hooks" / "prompt" / "surface_log_errors.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    found = m._scan(str(log.parent))
    hit = [d for d in found.values() if d["file"] == "ai-collab.log" and d["kind"] == "ERROR"]
    assert hit and "재개 큐 기록 실패" in hit[0]["sample"]                     # 다음 세션 주입 경로가 실제로 잡음


def _dispatch_scan_only(r: Path) -> str:
    """실제 UserPromptSubmit 분배기(prompt-dispatch.py main)를 로그 스캐너 1개로만 돌려 additionalContext 를 얻는다.
    분배기의 로그·요청 추적·세션 중복 제거는 kit 운영 폴더에 쓰므로 막는다 (시험 입력이 운영 기록에 남지 않게)."""
    runner = (
        "import importlib.util,io,sys,_common\n"
        f"spec=importlib.util.spec_from_file_location('pd',{str(ROOT / '.claude' / 'hooks' / 'prompt-dispatch.py')!r})\n"
        "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)\n"
        "m.HOOKS=[('surface-log-errors','surface_log_errors')];m._write_log=lambda lines:None\n"
        "_common.trace_emit=lambda *a,**k:None\n"
        "sys.stdin=io.TextIOWrapper(io.BytesIO('{\"prompt\":\"상태 확인\"}'.encode()),encoding='utf-8')\n"
        "m.main([])\n")
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(r), "PYTHONUTF8": "1", "PROMPT_INJECT_DEDUPE": "0",
           "PYTHONPATH": str(ROOT / ".claude" / "hooks" / "prompt")}
    p = subprocess.run([sys.executable, "-X", "utf8", "-c", runner], env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60, cwd=str(r))
    assert p.returncode == 0, p.stderr
    if not p.stdout.strip():
        return ""
    return json.loads(p.stdout)["hookSpecificOutput"]["additionalContext"]


def test_triple_failure_stderr_only_no_crash_then_recover(tmp_path):
    """R354 4차 검토 P2: 재개 큐 · state.json · 운영 로그 셋 다 못 쓰는 삼중 장애 →
    예외 없이 queue rc 1 · 세 실패가 모두 stderr 에 · 기존 state.json 보존 · 원인 해소 뒤 다음 queue 가 복구."""
    r = _repo(tmp_path)
    assert _run(r, "report", "R2", "--status", "PARTIAL").returncode == 0
    st_path = r / ".ai-collab" / "state.json"
    before = st_path.read_bytes()
    na = r / ".claude" / "state" / "next-actions.md"
    na.unlink(missing_ok=True); na.mkdir()
    (r / ".ai-collab" / "state.tmp").mkdir()
    log = r / ".claude" / "logs" / "ai-collab.log"
    log.unlink(missing_ok=True); log.mkdir(parents=True)                        # 운영 로그 자리에 폴더 = 기록 불가
    q = _run(r, "queue")
    assert q.returncode == 1 and "Traceback" not in q.stderr, q.stderr
    for msg in ("collab 큐 기록 실패", "queue_error 기록 실패", "운영 로그 기록도 실패"):
        assert msg in q.stderr, (msg, q.stderr)
    assert st_path.read_bytes() == before
    log.rmdir(); (r / ".ai-collab" / "state.tmp").rmdir(); na.rmdir()
    ok = _run(r, "queue")
    assert ok.returncode == 0 and "R2#1 [claude]" in _resume(r)
    assert not log.exists() or "[ERROR]" not in log.read_text(encoding="utf-8")  # 기록 못 한 오류를 지어내지 않음


def test_log_error_reaches_real_prompt_then_resolved_not_repeated(tmp_path):
    """R354 4차 검토 P2: 이중 장애 ERROR 가 실제 프롬프트 분배기 출력(additionalContext)에 들어가고,
    복구 뒤에는 해소 표시로 같은 ERROR 가 다시 주입되지 않으며 재개 큐가 재생성된다. 해소 뒤 재발은 다시 알림."""
    r = _repo(tmp_path)
    assert _run(r, "report", "R2", "--status", "PARTIAL").returncode == 0
    na = r / ".claude" / "state" / "next-actions.md"
    na.unlink(missing_ok=True); na.mkdir()
    (r / ".ai-collab" / "state.tmp").mkdir()
    assert _run(r, "queue").returncode == 1
    ctx1 = _dispatch_scan_only(r)
    assert "로그 오류 자동 점검" in ctx1 and "재개 큐 기록 실패" in ctx1, ctx1   # 다음 프롬프트에 실제 주입
    (r / ".ai-collab" / "state.tmp").rmdir(); na.rmdir()
    assert _run(r, "queue").returncode == 0                                     # 복구 → 해소 표시
    log = r / ".claude" / "logs" / "ai-collab.log"
    tail = log.read_text(encoding="utf-8").strip().splitlines()
    assert tail[-1].count("[RESOLVED]") == 1 and "R2#1 [claude]" in _resume(r)
    assert _run(r, "queue").returncode == 0                                     # 이미 해소됐으면 해소 줄 중복 X
    assert log.read_text(encoding="utf-8").count("[RESOLVED]") == 1
    (r / ".claude" / "state" / "log-errors-seen.json").unlink(missing_ok=True)  # 새 PC·seen 없는 새 세션 가정
    assert "재개 큐 기록 실패" not in _dispatch_scan_only(r)                  # 해소된 오류는 다시 안 알림
    na.unlink(missing_ok=True); na.mkdir()                                      # 해소 뒤 재발
    assert _run(r, "queue").returncode == 1
    (r / ".claude" / "state" / "log-errors-seen.json").unlink(missing_ok=True)
    assert "재개 큐 기록 실패" in _dispatch_scan_only(r)                      # 재발은 다시 알림


def _scanner():
    sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "prompt"))
    spec = importlib.util.spec_from_file_location("_sle_r354b", ROOT / ".claude" / "hooks" / "prompt" / "surface_log_errors.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _ts(sec_ago: int = 60) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - sec_ago))


def test_resolved_marker_hides_only_its_own_earlier_errors(tmp_path):
    """R354 5차 검토 P2: 같은 로그에 다른 오류·해소 표시가 섞여도 해소 표시는 자기 문구의 앞선 오류만 숨긴다 ·
    표시 뒤 재발은 다시 알림 · 짧거나 오류 단어뿐인 표시는 무시 (다른 미해소 오류를 숨기지 않음)."""
    m = _scanner()
    d = tmp_path / "logs"; d.mkdir()
    (d / "mix.log").write_text("\n".join([
        f"[{_ts(500)}] [ERROR] collab 재개 큐 기록 실패 — rc=1 a",
        f"[{_ts(400)}] [ERROR] DB 연결 실패 db_timeout",                    # 다른 오류 (해소 안 됨)
        f"[{_ts(300)}] [RESOLVED] collab 재개 큐 기록 실패 — 복구됨",
        f"[{_ts(200)}] [ERROR] 다른 작업 실패 job_x",                       # 표시 뒤 다른 오류
        f"[{_ts(150)}] [RESOLVED] ERROR",                                    # 너무 넓은 표시 = 무시
        f"[{_ts(140)}] [RESOLVED] 실패",                                     # 8자 미만 = 무시
    ]) + "\n", encoding="utf-8")
    samples = [v["sample"] for v in m._scan(str(d)).values() if v["kind"] == "ERROR"]
    assert not any("재개 큐" in s for s in samples)
    assert any("db_timeout" in s for s in samples) and any("job_x" in s for s in samples), samples
    with (d / "mix.log").open("a", encoding="utf-8") as f:                   # 해소 뒤 재발
        f.write(f"[{_ts(60)}] [ERROR] collab 재개 큐 기록 실패 — rc=1 b\n")
    assert any("재개 큐" in v["sample"] for v in m._scan(str(d)).values())


def test_resolved_marker_tail_boundary_and_unreadable_logs(tmp_path):
    """500줄 끝 범위 경계: 범위 밖 오류는 원래 안 셈 · 범위 안 오류는 범위 안 해소 표시로만 숨겨짐 ·
    읽을 수 없는 로그(폴더)·seen 기록 실패가 다른 로그의 알림을 막지 않음."""
    m = _scanner()
    d = tmp_path / "logs"; d.mkdir()
    lines = [f"[{_ts(900)}] [ERROR] collab 재개 큐 기록 실패 — 범위 밖"]
    lines += [f"[{_ts(800)}] [INFO] filler {i}" for i in range(520)]          # 끝 500줄 밖으로 밀어냄
    lines += [f"[{_ts(100)}] [ERROR] collab 재개 큐 기록 실패 — 범위 안"]
    (d / "tail.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    hit = [v for v in m._scan(str(d)).values() if v["kind"] == "ERROR"]
    assert len(hit) == 1 and hit[0]["n"] == 1 and "범위 안" in hit[0]["sample"]
    with (d / "tail.log").open("a", encoding="utf-8") as f:
        f.write(f"[{_ts(50)}] [RESOLVED] collab 재개 큐 기록 실패 — 복구됨\n")
    assert not [v for v in m._scan(str(d)).values() if v["kind"] == "ERROR"]
    (d / "broken.log").mkdir()                                               # 읽기 실패 로그
    (d / "other.log").write_text(f"[{_ts(30)}] [ERROR] 독립 오류 indep\n", encoding="utf-8")
    assert any("indep" in v["sample"] for v in m._scan(str(d)).values())
    proj = tmp_path / "proj"; (proj / ".claude").mkdir(parents=True)
    os.replace(str(d), str(proj / ".claude" / "logs"))
    (proj / ".claude" / "state").mkdir()
    (proj / ".claude" / "state" / "log-errors-seen.json").mkdir()            # seen 읽기·쓰기 실패
    ctx = type("C", (), {"raw_stripped": "확인", "project_dir": str(proj)})()
    out = m.run(ctx)
    assert out and "indep" in out["additionalContext"]                       # 기록 실패가 알림을 막지 않음


def test_resolved_marker_does_not_suppress_partial_matches_or_other_files(tmp_path):
    """R354 6차 검토 P2: 8자 이상 일반 문구도 다른 오류와 부분 일치하면 과도하게 숨겼다 →
    «[ERROR] <문구>» 로 시작하는 같은 파일의 앞선 오류만 숨김 · 문구가 메시지 중간에 든 다른 오류 · 다른 파일 · 해소 뒤 재발은 알림."""
    m = _scanner()
    d = tmp_path / "logs"; d.mkdir()
    (d / "a.log").write_text("\n".join([
        f"[{_ts(500)}] [ERROR] 백업 작업 실패 — disk full",
        f"[{_ts(450)}] [ERROR] 야간 배치: 백업 작업 실패 원인 추적 중 nightly",   # 같은 단어가 중간에 든 다른 오류
        f"[{_ts(440)}] [ERROR] 업로드 실패 (백업 작업 실패 이후) upl",            # 같은 단어 · 다른 원인
        f"[{_ts(300)}] [RESOLVED] 백업 작업 실패 — 복구됨",
    ]) + "\n", encoding="utf-8")
    (d / "b.log").write_text(f"[{_ts(400)}] [ERROR] 백업 작업 실패 — 다른 파일 bfile\n", encoding="utf-8")
    samples = [v["sample"] for v in m._scan(str(d)).values() if v["kind"] == "ERROR"]
    assert not any("disk full" in s for s in samples)                         # 자기 오류만 숨김
    for mark in ("nightly", "upl", "bfile"):
        assert any(mark in s for s in samples), (mark, samples)
    with (d / "a.log").open("a", encoding="utf-8") as f:
        f.write(f"[{_ts(60)}] [ERROR] 백업 작업 실패 — disk full again\n")
    assert any("again" in v["sample"] for v in m._scan(str(d)).values())     # 해소 뒤 재발


def test_resolved_marker_same_prefix_different_cause(tmp_path):
    """R354 7차 검토 P2: 같은 접두어·다른 원인 오류 2건(disk full · permission denied)을 해소 표시 하나가 둘 다 숨길 수 있었다 →
    상관 ID(ref) 가 있으면 같은 ID 오류만 해소 · ID 없는 옛 표시는 같은 접두어 오류 종류가 둘 이상이면 아무것도 숨기지 않음 ·
    해소 뒤 재발은 다시 알림."""
    m = _scanner()
    d = tmp_path / "logs"; d.mkdir()
    log = d / "a.log"
    log.write_text("\n".join([
        f"[{_ts(500)}] [ERROR] 백업 작업 실패 — disk full",
        f"[{_ts(450)}] [ERROR] 백업 작업 실패 — permission denied",
        f"[{_ts(300)}] [RESOLVED] 백업 작업 실패 — 복구됨",                    # 옛 형식 · 어느 것인지 모름
    ]) + "\n", encoding="utf-8")
    s = [v["sample"] for v in m._scan(str(d)).values() if v["kind"] == "ERROR"]
    assert any("disk full" in x for x in s) and any("permission denied" in x for x in s), s
    log.write_text("\n".join([
        f"[{_ts(500)}] [ERROR] 백업 작업 실패 (ref=aaaa1111) — disk full",
        f"[{_ts(450)}] [ERROR] 백업 작업 실패 (ref=bbbb2222) — permission denied",
        f"[{_ts(300)}] [RESOLVED] 백업 작업 실패 (ref=aaaa1111) — 복구됨",
    ]) + "\n", encoding="utf-8")
    s = [v["sample"] for v in m._scan(str(d)).values() if v["kind"] == "ERROR"]
    assert not any("disk full" in x for x in s) and any("permission denied" in x for x in s), s
    with log.open("a", encoding="utf-8") as f:
        f.write(f"[{_ts(60)}] [ERROR] 백업 작업 실패 (ref=aaaa1111) — disk full again\n")
    assert any("again" in v["sample"] for v in m._scan(str(d)).values())     # 해소 뒤 같은 ID 재발도 알림


def test_queue_error_lines_carry_one_ref_per_episode(tmp_path):
    """재개 큐 기록 실패가 이어지면 같은 상관 ID · 복구 표시도 그 ID · 다음 장애는 새 ID (실제 ai-collab-report 경로)."""
    import re as _re
    r = _repo(tmp_path)
    assert _run(r, "report", "R2", "--status", "PARTIAL").returncode == 0
    na = r / ".claude" / "state" / "next-actions.md"
    na.unlink(missing_ok=True); na.mkdir()
    assert _run(r, "queue").returncode == 1 and _run(r, "queue").returncode == 1
    na.rmdir()
    assert _run(r, "queue").returncode == 0
    na.unlink(missing_ok=True); na.mkdir()
    assert _run(r, "queue").returncode == 1
    lines = (r / ".claude" / "logs" / "ai-collab.log").read_text(encoding="utf-8").strip().splitlines()
    refs = [_re.search(r"\(ref=(\w+)\)", ln).group(1) for ln in lines]
    assert len(lines) == 4 and "[RESOLVED]" in lines[2]
    assert refs[0] == refs[1] == refs[2] and refs[3] != refs[0], lines
    m = _scanner()
    s = [v["sample"] for v in m._scan(str(r / ".claude" / "logs")).values() if v["kind"] == "ERROR"]
    assert len(s) == 1 and refs[3] in s[0]                                    # 해소된 장애는 숨기고 새 장애만


def test_resolved_ref_must_match_exactly_and_not_merge_by_digits(tmp_path):
    """R354 8차 검토 P2: ① 해소 ref 가 다른 오류 ref 의 접두어일 때(aaaa1111 ⊂ aaaa1111-extra) 그 오류까지 숨겼다 (부분 문자열 비교)
    ② _sig 가 숫자를 # 로 지워 숫자만 다른 ref 두 오류가 한 key 로 합쳐져 하나만 해소해도 둘 다 사라졌다 →
    ref 는 완전 일치 · ref 가 다르면 별도 오류로 센다 · 같은 ID 재발과 옛 형식은 그대로."""
    m = _scanner()
    d = tmp_path / "logs"; d.mkdir()
    log = d / "a.log"
    log.write_text("\n".join([
        f"[{_ts(500)}] [ERROR] 백업 작업 실패 (ref=aaaa1111-extra) — disk full",
        f"[{_ts(490)}] [ERROR] 백업 작업 실패 (ref=aaaa1111) — disk full",
        f"[{_ts(480)}] [ERROR] 큐 기록 실패 (ref=abc1234567) — rc=1",
        f"[{_ts(470)}] [ERROR] 큐 기록 실패 (ref=abc7654321) — rc=1",           # 같은 메시지 · 숫자만 다른 ID
        f"[{_ts(300)}] [RESOLVED] 백업 작업 실패 (ref=aaaa1111) — 복구됨",
        f"[{_ts(290)}] [RESOLVED] 큐 기록 실패 (ref=abc7654321) — 복구됨",
    ]) + "\n", encoding="utf-8")
    s = [v["sample"] for v in m._scan(str(d)).values() if v["kind"] == "ERROR"]
    assert any("aaaa1111-extra" in x for x in s), s                          # 접두어 관계 ID 는 남음
    assert not any("(ref=aaaa1111)" in x for x in s), s
    assert any("abc1234567" in x for x in s), s                              # 숫자만 다른 ID 는 남음
    assert not any("abc7654321" in x for x in s), s
    with log.open("a", encoding="utf-8") as f:
        f.write(f"[{_ts(60)}] [ERROR] 큐 기록 실패 (ref=abc7654321) — rc=1 again\n")
    s = [v["sample"] for v in m._scan(str(d)).values() if v["kind"] == "ERROR"]
    assert any("abc7654321" in x and "again" in x for x in s), s             # 해소 뒤 같은 ID 재발은 다시 알림


def test_shared_ref_different_messages_and_boundaries_reach_real_prompt(tmp_path):
    """R354 9차 검토 P2: ① 서로 다른 오류가 같은 ref 를 공유할 때 «[RESOLVED] A (ref=X)» 가 B 까지 숨겼다 (ref 만 비교) →
    ref 일치 + «[ERROR] <해소 문구>» 로 시작하는 오류만 · ② ID 없는 옛 줄 · ③ 해소 표시가 끝 500줄 밖이면 숨기지 않음 ·
    ④ 실제 프롬프트 분배기 주입에서 미해소 오류만 보임."""
    r = _repo(tmp_path)
    d = r / ".claude" / "logs"; d.mkdir(parents=True, exist_ok=True)
    (d / "s.log").write_text("\n".join([
        f"[{_ts(500)}] [ERROR] 백업 작업 실패 (ref=shared01) — disk full",
        f"[{_ts(490)}] [ERROR] 업로드 실패 (ref=shared01) — timeout upl",           # 같은 ref · 다른 오류
        f"[{_ts(480)}] [ERROR] 정리 작업 실패 — 옛 형식 cln",                       # ID 없는 옛 줄 (해소 표시 없음)
        f"[{_ts(300)}] [RESOLVED] 백업 작업 실패 (ref=shared01) — 복구됨",
    ]) + "\n", encoding="utf-8")
    lines = [f"[{_ts(900)}] [ERROR] 배치 실패 (ref=tail0001) — 범위 안 bat"]
    lines += [f"[{_ts(800)}] [INFO] filler {i}" for i in range(520)]
    lines += [f"[{_ts(100)}] [ERROR] 배치 실패 (ref=tail0002) — 범위 안 bat2"]
    (d / "t.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (d / "t.log").open("a", encoding="utf-8") as f:
        f.write(f"[{_ts(50)}] [RESOLVED] 배치 실패 (ref=tail0001) — 복구됨\n")      # 대상 오류가 500줄 밖 → 숨길 것 없음
    s = [v["sample"] for v in _scanner()._scan(str(d)).values() if v["kind"] == "ERROR"]
    assert not any("disk full" in x for x in s), s
    assert any("timeout upl" in x for x in s), s                                # 같은 ref 다른 오류는 남음
    assert any("cln" in x for x in s) and any("bat2" in x for x in s), s
    ctx = _dispatch_scan_only(r)
    assert "timeout upl" in ctx and "bat2" in ctx and "disk full" not in ctx, ctx


def test_resolved_phrase_must_equal_error_head_not_prefix(tmp_path):
    """R354 10차 검토 P2: «[RESOLVED] 백업 실패 (ref=X)» 가 같은 ref 의 «[ERROR] 백업 실패 (ref=X) - 추가 장애» 까지 숨겼다
    (해소 문구를 앞부분만 비교) → 오류 머리(«[ERROR]» 뒤 ~ «—» 앞, 해소 표시와 같은 경계)가 해소 문구와 완전히 같을 때만 ·
    머리는 200자로 잘린 표본이 아니라 원래 줄에서 뽑는다 · 서로 다른 ref·같은 메시지 · 해소 뒤 재발 · 500줄 경계 · 실제 주입."""
    r = _repo(tmp_path)
    d = r / ".claude" / "logs"; d.mkdir(parents=True, exist_ok=True)
    long_a = "가" * 230 + " 끝A"
    long_b = "가" * 230 + " 끝B"                                                # 200자 안에서는 같은 두 오류
    lines = [
        f"[{_ts(600)}] [ERROR] 백업 실패 (ref=pfx00001) — disk full",
        f"[{_ts(590)}] [ERROR] 백업 실패 (ref=pfx00001) - 추가 장애 extra",         # 같은 ref · 공통 접두어 · 다른 원인
        f"[{_ts(580)}] [ERROR] 동기화 실패 (ref=dif00001) — x",
        f"[{_ts(570)}] [ERROR] 동기화 실패 (ref=dif00002) — y sync2",               # 같은 메시지 · 다른 ref
        f"[{_ts(560)}] [ERROR] {long_a} (ref=lng00001) — la",
        f"[{_ts(550)}] [ERROR] {long_b} (ref=lng00001) — lb",
        f"[{_ts(400)}] [RESOLVED] 백업 실패 (ref=pfx00001) — 복구됨",
        f"[{_ts(390)}] [RESOLVED] 동기화 실패 (ref=dif00001) — 복구됨",
        f"[{_ts(380)}] [RESOLVED] {long_a} (ref=lng00001) — 복구됨",
    ]
    lines += [f"[{_ts(300)}] [INFO] filler {i}" for i in range(480)]            # 위 오류·표시가 끝 500줄 안에 남는 범위
    (d / "p.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    found = [v for v in _scanner()._scan(str(d)).values() if v["kind"] == "ERROR"]
    s = [v["sample"] for v in found]
    assert not any("disk full" in x for x in s), s
    assert any("extra" in x for x in s), s                                     # 공통 접두어 다른 원인은 남음
    assert any("sync2" in x for x in s) and not any("dif00001" in x for x in s), s
    lng = [v.get("head", "") for v in found if v.get("ref") == "lng00001"]     # 표본은 200자로 잘려 끝이 안 보임
    assert len(lng) == 1 and lng[0].endswith("끝b (ref=lng00001)"), lng       # 긴 머리 A 만 해소 · 200자 안에서 같은 B 는 남음
    with (d / "p.log").open("a", encoding="utf-8") as f:
        f.write(f"[{_ts(60)}] [ERROR] 백업 실패 (ref=pfx00001) — disk full again\n")
    ctx = _dispatch_scan_only(r)
    assert "again" in ctx and "extra" in ctx and "sync2" in ctx, ctx           # 실제 주입: 재발·미해소만


def test_ref_is_one_failure_episode_and_resolved_only_when_fully_clean(tmp_path):
    """R354 11차 검토 P2: 같은 ref·같은 머리·다른 상세 원인. ref 를 만드는 곳은 ai-collab-report._log_queue_error 하나뿐 (전수 조사) —
    해소 안 된 장애가 이어지는 동안만 같은 ID → 같은 ID = 한 장애 에피소드 (상세 원인이 달라도) · 해소 표시는 그 에피소드 전체 복구.
    단 해소 표시를 남긴 뒤 state.json queue_error 해제가 실패하면 «다 복구» 가 아니었는데 해소로 보였다 → 해제 성공 뒤에만 표시.
    서로 다른 장애는 서로 다른 ID 라서 하나만 해소해도 다른 것은 남는다."""
    import re as _re
    r = _repo(tmp_path)
    assert _run(r, "report", "R2", "--status", "PARTIAL").returncode == 0
    na = r / ".claude" / "state" / "next-actions.md"
    tmp = r / ".ai-collab" / "state.tmp"
    log = r / ".claude" / "logs" / "ai-collab.log"
    logs = r / ".claude" / "logs"
    na.unlink(missing_ok=True); na.mkdir()
    assert _run(r, "queue").returncode == 1                                     # 원인 1: 재개 큐 기록 실패
    tmp.mkdir()
    assert _run(r, "queue").returncode == 1                                     # 원인 2 추가: state 기록도 실패 (상세 다름)
    tmp.rmdir()
    na.rmdir(); tmp.mkdir()
    assert _run(r, "queue").returncode == 1                                     # 큐는 복구 · queue_error 해제 실패 = 아직 안 끝남
    text = log.read_text(encoding="utf-8")
    refs = _re.findall(r"\(ref=(\w+)\)", text)
    assert len(set(refs)) == 1 and text.count("[ERROR]") == 2, text            # 상세가 달라도 같은 에피소드 = 같은 ID
    assert "[RESOLVED]" not in text, text                                       # 해제 실패 중에는 해소 표시 없음
    assert "재개 큐 기록 실패" in _dispatch_scan_only(r)                        # 그래서 다음 세션에 계속 알림
    tmp.rmdir()
    assert _run(r, "queue").returncode == 0
    text = log.read_text(encoding="utf-8")
    assert text.count("[RESOLVED]") == 1 and f"(ref={refs[0]})" in text.splitlines()[-1], text
    (r / ".claude" / "state" / "log-errors-seen.json").unlink(missing_ok=True)
    assert "재개 큐 기록 실패" not in _dispatch_scan_only(r)                    # 에피소드 전체 해소 (두 상세 모두)
    # 스캐너 규칙: 서로 다른 장애에 서로 다른 ID → 하나만 해소해도 다른 것은 남음 (같은 머리·다른 상세)
    (logs / "z.log").write_text("\n".join([
        f"[{_ts(500)}] [ERROR] 백업 실패 (ref=ep000001) — disk full",
        f"[{_ts(490)}] [ERROR] 백업 실패 (ref=ep000002) — permission denied",
        f"[{_ts(300)}] [RESOLVED] 백업 실패 (ref=ep000001) — disk full 복구",
    ]) + "\n", encoding="utf-8")
    s = [v["sample"] for v in _scanner()._scan(str(logs)).values() if v["kind"] == "ERROR"]
    assert any("permission denied" in x for x in s) and not any("disk full" in x for x in s), s


def _c(r: Path, name: str, body: str, msg: str):
    (r / name).parent.mkdir(parents=True, exist_ok=True)
    (r / name).write_text(body, encoding="utf-8")
    subprocess.run(["git", "-C", str(r), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(r), "commit", "-q", "-m", msg], check=True)
    return subprocess.run(["git", "-C", str(r), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def test_report_head_override_for_followup_fix_without_id(tmp_path):
    """R354 15차 P1: 후속 수정 커밋(0cf9163f)이 메시지에 요청 ID 를 안 적어 head_commit 이 CI 실패한 앞 SHA(5f9e90d9)에 남았다.
    --head 로 최신 실제 코드 SHA 를 지정 — base..tip 안·게시 전용 아님·자동 선택보다 최신일 때만 허용."""
    r = _repo(tmp_path)
    base = subprocess.run(["git", "-C", str(r), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    impl = _c(r, "x.py", "1", "fix: 구현 (R2)")
    follow = _c(r, "tests/t.py", "2", "fix(test): CI 환경 의존 단언 제거")     # ID 없음
    pub = _c(r, ".ai-collab/reports/R2.md", "r", "docs(collab): 게시")
    assert _run(r, "report", "R2", "--base", base).returncode == 0
    assert _state(r)["requests"]["R2"]["head_commit"] == impl                     # 수정 전 동작 그대로 (재현)
    bad = _run(r, "report", "R2", "--base", base, "--head", pub, "--reason", "ID 없는 후속 수정 반영")                  # 게시 전용 커밋 거부
    assert bad.returncode == 2 and "게시" in bad.stderr, bad.stderr
    assert _run(r, "report", "R2", "--base", base, "--head", base, "--reason", "ID 없는 후속 수정 반영").returncode == 2   # 범위 밖(기준 자신) 거부
    assert _run(r, "report", "R2", "--base", base, "--head", "deadbeef" * 5, "--reason", "ID 없는 후속 수정 반영").returncode == 2
    ok = _run(r, "report", "R2", "--base", base, "--head", follow, "--reason", "ID 없는 후속 수정 반영")
    assert ok.returncode == 0, ok.stderr
    ent = _state(r)["requests"]["R2"]
    assert ent["head_commit"] == follow and ent.get("head_override")             # 지정 사실을 기록
    rep = (r / ".ai-collab" / "reports" / "R2.md").read_text(encoding="utf-8")
    assert f'head_commit: "{follow}"' in rep
    old = _run(r, "report", "R2", "--base", base, "--head", impl, "--reason", "ID 없는 후속 수정 반영")                 # 자동 선택과 같거나 옛 SHA 로 되돌리기 X
    assert old.returncode == 2


def test_report_head_override_survives_later_report_without_flag(tmp_path):
    """R354 16차 P1: --head 로 맞춘 뒤 다음 report(또는 큐 갱신 뒤 보고)에서 --head 를 생략하면 자동 선택이
    예전 ID 포함 커밋으로 되돌아갔다 → 지정 head 가 아직 범위 안이고 자동 선택보다 최신이면 유지 ·
    ID 를 적은 더 새 작업 커밋이 생기면 자동 선택으로 돌아가고 지정 표식은 지움."""
    r = _repo(tmp_path)
    base = subprocess.run(["git", "-C", str(r), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    _c(r, "x.py", "1", "fix: 구현 (R2)")
    follow = _c(r, "tests/t.py", "2", "fix(test): ID 없는 후속 수정")
    assert _run(r, "report", "R2", "--base", base, "--head", follow, "--reason", "ID 없는 후속 수정 반영").returncode == 0
    _ledger(r, "item-add", "R2", "남은 일 하나 더")                                   # 항목이 바뀌어 보고서가 다시 써지는 경우
    again = _run(r, "report", "R2", "--base", base)
    assert again.returncode == 0, again.stderr
    ent = _state(r)["requests"]["R2"]
    assert ent["head_commit"] == follow and ent.get("head_override"), ent           # 되돌아가지 않음
    newer = _c(r, "y.py", "3", "fix: 다음 구현 (R2)")
    assert _run(r, "report", "R2", "--base", base).returncode == 0
    ent = _state(r)["requests"]["R2"]
    assert ent["head_commit"] == newer and not ent.get("head_override"), ent        # 더 새 ID 커밋이면 자동 선택


def test_report_head_override_edges_do_not_keep_stale_base(tmp_path):
    """R354 17차 P2: --head 유지가 범위 변경·직계 아닌 커밋·재보고·ID 없는 추가 후속에서 오래된 기준을 붙잡지 않는지."""
    r = _repo(tmp_path)
    g = lambda *a: subprocess.run(["git", "-C", str(r), *a], capture_output=True, text=True, check=True).stdout.strip()
    base = g("rev-parse", "HEAD")
    impl = _c(r, "x.py", "1", "fix: 구현 (R2)")
    f1 = _c(r, "t1.py", "1", "fix(test): ID 없는 후속 1")
    assert _run(r, "report", "R2", "--base", base, "--head", f1, "--reason", "ID 없는 후속 수정 반영").returncode == 0
    # 1) 재보고(같은 상태) — 지정 유지·중복 생성 X
    same = _run(r, "report", "R2", "--base", base)
    assert same.returncode == 0 and _state(r)["requests"]["R2"]["head_commit"] == f1
    # 2) ID 없는 후속이 하나 더 — 자동 선택(impl)보다 최신인 f1 유지 · 더 새 f2 로 다시 지정 가능
    f2 = _c(r, "t2.py", "2", "fix(test): ID 없는 후속 2")
    assert _run(r, "report", "R2", "--base", base).returncode == 0
    assert _state(r)["requests"]["R2"]["head_commit"] == f1                      # 몰래 f2 로 옮기지 않음 (지정한 것만)
    assert _run(r, "report", "R2", "--base", base, "--head", f2, "--reason", "ID 없는 후속 수정 반영").returncode == 0
    assert _state(r)["requests"]["R2"]["head_commit"] == f2
    # 3) 직계가 아닌 커밋(다른 가지) 지정 거부
    side = g("commit-tree", impl + "^{tree}", "-p", impl, "-m", "fix: 옆 가지 (R2)")   # main 이력에 없는 커밋 (작업 트리 무변경)
    bad = _run(r, "report", "R2", "--base", base, "--head", side, "--reason", "ID 없는 후속 수정 반영")
    assert bad.returncode == 2 and "범위 밖" in bad.stderr, bad.stderr
    assert _state(r)["requests"]["R2"]["head_commit"] == f2                      # 거부 뒤 기존 값 그대로
    # 4) 범위 변경 — 기준을 지정 head 뒤로 옮기면 그 head 는 범위 밖 → 유지하지 않고 새 범위의 자동 선택
    new_impl = _c(r, "z.py", "3", "fix: 새 범위 구현 (R2)")
    assert _run(r, "report", "R2", "--base", f2).returncode == 0
    ent = _state(r)["requests"]["R2"]
    assert ent["head_commit"] == new_impl and not ent.get("head_override") and ent["base_commit"] == f2, ent


def test_report_head_requires_reason_and_keeps_it(tmp_path):
    """R354 18차 P2: 기준 SHA 를 수동 지정할 때 근거를 남기지 않았다 → --head 는 --reason(8자 이상) 필수 ·
    state 의 head_override_reason 과 보고서 머리 head_override 줄에 남고 · 지정 유지(재보고) 때도 그대로."""
    r = _repo(tmp_path)
    base = subprocess.run(["git", "-C", str(r), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    _c(r, "x.py", "1", "fix: 구현 (R2)")
    follow = _c(r, "t.py", "2", "fix(test): ID 없는 후속")
    no = _run(r, "report", "R2", "--base", base, "--head", follow)
    assert no.returncode == 2 and "--reason" in no.stderr, no.stderr
    short = _run(r, "report", "R2", "--base", base, "--head", follow, "--reason", "짧음")
    assert short.returncode == 2
    why = "후속 시험 수정 0cf9163f 가 ID 를 빠뜨림 · CI 초록 SHA"
    assert _run(r, "report", "R2", "--base", base, "--head", follow, "--reason", why).returncode == 0
    ent = _state(r)["requests"]["R2"]
    assert ent["head_override_reason"] == why
    rep = (r / ".ai-collab" / "reports" / "R2.md").read_text(encoding="utf-8")
    assert "head_override:" in rep.split("---")[1] and why in rep.split("---")[1]
    _ledger(r, "item-add", "R2", "다시 보고되게 항목 추가")
    assert _run(r, "report", "R2", "--base", base).returncode == 0                 # 지정 유지 재보고
    ent = _state(r)["requests"]["R2"]
    assert ent["head_commit"] == follow and ent["head_override_reason"] == why
    assert why in (r / ".ai-collab" / "reports" / "R2.md").read_text(encoding="utf-8").split("---")[1]
