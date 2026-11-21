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
