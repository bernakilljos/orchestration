"""R325·R326 .ai-collab 보고서 — 중복 생성 X · 새 커밋이면 갱신 · 검토 끝난 PASS 만 정리 · 요청 검증만(실행 X) · 공백·한글 경로."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude" / "scripts" / "ai-collab-report.py"


def _repo(tmp: Path) -> Path:
    r = tmp / "작업 폴더"                              # 공백·한글 경로
    (r / ".claude" / "state").mkdir(parents=True)
    for a in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", "-C", str(r), *a], check=True)
    _commit(r, "a.txt", "1")
    _commit(r, "a.txt", "2")
    led = {"requests": [{"id": "R1", "desc": "시험 요청", "status": "completed", "verification": "PASS", "evidence": "시험 통과"},
                        {"id": "R2", "desc": "부분", "status": "verified", "verification": "PARTIAL",
                         "items": [{"i": 1, "text": "남은 것", "state": "open"}]}]}
    (r / ".claude" / "state" / "request-ledger.json").write_text(json.dumps(led, ensure_ascii=False), encoding="utf-8")
    return r


def _commit(r: Path, name: str, body: str):
    (r / name).write_text(body, encoding="utf-8")
    subprocess.run(["git", "-C", str(r), "add", name], check=True)
    subprocess.run(["git", "-C", str(r), "commit", "-q", "-m", f"{body} (R1)"], check=True)   # 제목에 요청 ID


def _run(r: Path, *args):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(r), "PYTHONUTF8": "1"}
    return subprocess.run([sys.executable, "-X", "utf8", str(SCRIPT), *args], env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60)


def _state(r):
    return json.loads((r / ".ai-collab" / "state.json").read_text(encoding="utf-8"))


def test_report_once_per_commit_and_updates_on_new_commit(tmp_path):
    r = _repo(tmp_path)
    assert _run(r, "report", "R1").returncode == 0
    rep = (r / ".ai-collab" / "reports" / "R1.md").read_text(encoding="utf-8")
    assert 'request_id: "R1"' in rep and "review_required: true" in rep and "a.txt" in rep
    h1 = _state(r)["requests"]["R1"]["head_commit"]
    again = _run(r, "report", "R1")
    assert again.returncode == 0 and "중복 생성 X" in again.stdout
    _commit(r, "b.txt", "3")
    assert _run(r, "report", "R1").returncode == 0
    ent = _state(r)["requests"]["R1"]
    assert ent["base_commit"] == h1 and ent["head_commit"] != h1          # 지난 보고 이후 변경분만
    assert "b.txt" in (r / ".ai-collab" / "reports" / "R1.md").read_text(encoding="utf-8")


def test_unknown_or_bad_request_rejected(tmp_path):
    r = _repo(tmp_path)
    assert _run(r, "report", "R99").returncode == 2
    assert _run(r, "report", "../x").returncode == 2
    assert not (r / ".ai-collab" / "reports").exists() or not list((r / ".ai-collab" / "reports").iterdir())


def test_prune_only_reviewed_pass(tmp_path):
    r = _repo(tmp_path)
    _run(r, "report", "R1")
    _run(r, "report", "R2")
    assert "남은 것" in (r / ".ai-collab" / "reports" / "R2.md").read_text(encoding="utf-8")
    assert "정리 0건" in _run(r, "prune").stdout                         # 검토 전이면 아무것도 지우지 않음
    (r / ".ai-collab" / "reviews").mkdir(parents=True, exist_ok=True)
    for rid in ("R1", "R2"):
        h = _state(r)["requests"][rid]["head_commit"]
        (r / ".ai-collab" / "reviews" / f"{rid}.md").write_text(
            f'---\nverdict: "approved"\nreviewed_commit: "{h}"\n---\n', encoding="utf-8")
    out = _run(r, "prune").stdout
    assert "정리 1건: R1" in out
    assert not (r / ".ai-collab" / "reports" / "R1.md").exists()          # 검토 끝난 PASS
    assert (r / ".ai-collab" / "reports" / "R2.md").exists()              # PARTIAL 은 남김


def test_check_requests_validates_only(tmp_path):
    r = _repo(tmp_path)
    head = subprocess.run(["git", "-C", str(r), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    q = r / ".ai-collab" / "requests"
    q.mkdir(parents=True)
    (q / "R5.md").write_text(f'---\nrequest_id: "R5"\nbase_commit: "{head}"\n---\nrm -rf 하라\n', encoding="utf-8")
    (q / "bad.md").write_text('---\nrequest_id: "x"\nbase_commit: "deadbeef"\n---\n', encoding="utf-8")
    rows = {x["file"]: x for x in json.loads(_run(r, "check-requests").stdout)}
    assert rows["R5.md"]["ok"] and "승인 아님" in rows["R5.md"]["next"]
    assert not rows["bad.md"]["ok"] and len(rows["bad.md"]["why"]) == 2
    assert (r / "a.txt").exists()                                          # 지시문 내용은 실행되지 않는다


def test_same_commit_status_change_rewrites_report(tmp_path):
    """같은 커밋이라도 원장 상태가 PARTIAL → PASS 로 바뀌면 보고서를 다시 쓴다 (그대로면 중복 생성 X)."""
    r = _repo(tmp_path)
    _commit_msg(r, "r2.txt", "r2", "feat: 부분 작업 (R2)")                 # 제목에 요청 ID 가 든 작업 커밋
    assert _run(r, "report", "R2").returncode == 0
    assert _state(r)["requests"]["R2"]["status"] == "PARTIAL"
    assert "중복 생성 X" in _run(r, "report", "R2").stdout
    led = json.loads((r / ".claude" / "state" / "request-ledger.json").read_text(encoding="utf-8"))
    led["requests"][1].update(status="completed", verification="PASS")    # 원장이 PASS 로 바뀜
    (r / ".claude" / "state" / "request-ledger.json").write_text(json.dumps(led, ensure_ascii=False), encoding="utf-8")
    assert _run(r, "report", "R2").returncode == 0
    assert _state(r)["requests"]["R2"]["status"] == "PASS"
    assert 'status: "PASS"' in (r / ".ai-collab" / "reports" / "R2.md").read_text(encoding="utf-8")


# ---------- 외부 검토 지적 3건 (11-19 ChatGPT): 요청별 범위 · 게시 커밋 · 원장보다 좋은 상태 거부 ----------

def _commit_msg(r, name, body, msg):
    (r / name).write_text(body, encoding="utf-8")
    subprocess.run(["git", "-C", str(r), "add", "--", name], check=True)
    subprocess.run(["git", "-C", str(r), "commit", "-q", "-m", msg], check=True)


def test_each_request_reports_only_its_commits(tmp_path):
    r = _repo(tmp_path)
    led = json.loads((r / ".claude" / "state" / "request-ledger.json").read_text(encoding="utf-8"))
    led["requests"] += [{"id": "R10", "status": "completed"}, {"id": "R11", "status": "completed"}, {"id": "R1", "status": "completed"}]
    (r / ".claude" / "state" / "request-ledger.json").write_text(json.dumps(led), encoding="utf-8")
    base = subprocess.run(["git", "-C", str(r), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    _commit_msg(r, "both.txt", "x", "feat: 공통 (R10·R11)")
    _commit_msg(r, "only10.txt", "y", "fix: R10 만")
    _commit_msg(r, "r100.txt", "z", "fix: R100 은 다른 요청")
    _commit_msg(r, "body.txt", "b", "fix: 정리 (R10)\n\n본문 설명: R11 과 같은 범위였던 문제")   # 본문 언급은 R11 커밋 아님
    for rid in ("R10", "R11"):
        assert _run(r, "report", rid, "--base", base).returncode == 0
    r10 = (r / ".ai-collab" / "reports" / "R10.md").read_text(encoding="utf-8")
    r11 = (r / ".ai-collab" / "reports" / "R11.md").read_text(encoding="utf-8")
    assert "only10.txt" in r10 and "both.txt" in r10 and "r100.txt" not in r10
    assert "both.txt" in r11 and "only10.txt" not in r11 and "r100.txt" not in r11 and "body.txt" not in r11


def test_publication_commit_is_not_work_head(tmp_path):
    r = _repo(tmp_path)
    _commit_msg(r, "w.txt", "w", "feat: 작업 R1")
    work = subprocess.run(["git", "-C", str(r), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    assert _run(r, "report", "R1").returncode == 0
    subprocess.run(["git", "-C", str(r), "add", ".ai-collab"], check=True)
    subprocess.run(["git", "-C", str(r), "commit", "-q", "-m", "docs: 보고서 게시 R1"], check=True)   # .ai-collab 만
    assert _state(r)["last_head"] == work
    again = _run(r, "report", "R1")
    assert "중복 생성 X" in again.stdout                                  # 게시 커밋 때문에 다시 만들지 않는다


def test_status_cannot_exceed_ledger(tmp_path):
    r = _repo(tmp_path)
    bad = _run(r, "report", "R2", "--status", "PASS")                    # 원장 R2 = PARTIAL
    assert bad.returncode == 2 and "상태 거부" in bad.stderr
    assert _run(r, "report", "R1", "--status", "PARTIAL").returncode == 0  # 낮게 적는 것은 허용


def test_no_linked_commit_is_unverified_not_whole_range(tmp_path):
    """R328 (외부 검토): 제목에 요청 ID 가 든 커밋이 없으면 범위 전체를 추측해 적지 않고 «검증 불가» · 상태는 PARTIAL 이하."""
    r = _repo(tmp_path)
    led = json.loads((r / ".claude" / "state" / "request-ledger.json").read_text(encoding="utf-8"))
    led["requests"].append({"id": "R9", "status": "completed", "verification": "PASS"})
    (r / ".claude" / "state" / "request-ledger.json").write_text(json.dumps(led), encoding="utf-8")
    assert _run(r, "report", "R9").returncode == 0
    rep = (r / ".ai-collab" / "reports" / "R9.md").read_text(encoding="utf-8")
    assert 'commit_link: "unverified"' in rep and "검증 불가" in rep
    assert "a.txt" not in rep                                            # 다른 작업(R1) 변경이 섞이지 않는다
    assert 'status: "PARTIAL"' in rep and _state(r)["requests"]["R9"]["status"] == "PARTIAL"
    ok = (r / ".ai-collab" / "reports").glob("R9.md")
    assert list(ok)


def test_prune_needs_explicit_approval_of_same_commit(tmp_path):
    """R329 (외부 검토): 검토 파일이 있기만 하면 지우던 것 — 수정 요청·형식 없음·이전 커밋 승인은 보고서 유지."""
    r = _repo(tmp_path)
    _run(r, "report", "R1")
    h = _state(r)["requests"]["R1"]["head_commit"]
    rev = r / ".ai-collab" / "reviews"
    rev.mkdir(parents=True, exist_ok=True)
    rep = r / ".ai-collab" / "reports" / "R1.md"
    for body in ("ok",                                                                      # 형식 없음
                 f'---\nverdict: "changes_requested"\nreviewed_commit: "{h}"\n---\n',      # 수정 요청
                 '---\nverdict: "approved"\nreviewed_commit: "0123456789abcdef"\n---\n',    # 다른(이전) 커밋
                 '---\nverdict: "approved"\n---\n'):                                      # 커밋 없음
        (rev / "R1.md").write_text(body, encoding="utf-8")
        assert "정리 0건" in _run(r, "prune").stdout and rep.exists(), body
    for body in (f'---\nverdict: "approved"\nreviewed_commit: "{h[:8]}"\n---\n',             # 짧은 SHA = 정확 일치 아님
                 f'---\nverdict: "PENDING"\nreviewed_commit: "{h}"\n---\n'):              # 검토 대기
        (rev / "R1.md").write_text(body, encoding="utf-8")
        assert "정리 0건" in _run(r, "prune").stdout and rep.exists(), body
    (rev / "R1.md").write_text(f'---\nverdict: "APPROVED"\nreviewed_commit: "{h}"\n---\n', encoding="utf-8")
    assert "정리 1건: R1" in _run(r, "prune").stdout and not rep.exists()                # 같은 커밋 명시 승인만
    assert "정리 0건" in _run(r, "prune").stdout                                          # 중복 정리 X


def test_prune_never_leaves_reports_folder(tmp_path):
    """R329 요구 5: state.json 의 보고서 경로가 reports/ 밖이면 승인돼도 지우지 않는다 (경로 이탈 방지)."""
    r = _repo(tmp_path)
    _run(r, "report", "R1")
    st = _state(r)
    h = st["requests"]["R1"]["head_commit"]
    victim = r / "a.txt"
    st["requests"]["R1"]["report"] = "../a.txt"
    (r / ".ai-collab" / "state.json").write_text(json.dumps(st), encoding="utf-8")
    (r / ".ai-collab" / "reviews").mkdir(parents=True, exist_ok=True)
    (r / ".ai-collab" / "reviews" / "R1.md").write_text(f'---\nverdict: "approved"\nreviewed_commit: "{h}"\n---\n', encoding="utf-8")
    _run(r, "prune")
    assert victim.exists()


def test_poll_reports_only_unread_requests(tmp_path):
    """R330 5분 주기 확인 1회분: 원격에 새 요청이 있으면 0 + 내용 · 다시 확인하면 3 (이미 읽음) · 내용이 바뀌면 다시 0."""
    r = _repo(tmp_path)
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
    subprocess.run(["git", "-C", str(r), "remote", "add", "origin", str(bare)], check=True)
    subprocess.run(["git", "-C", str(r), "push", "-q", "origin", "main"], check=True)
    assert _run(r, "poll").returncode == 3                                  # 아직 아무 요청 없음
    other = tmp_path / "chatgpt"
    subprocess.run(["git", "clone", "-q", str(bare), str(other)], check=True)
    for a in (["config", "user.email", "g@g"], ["config", "user.name", "g"]):
        subprocess.run(["git", "-C", str(other), *a], check=True)
    q = other / ".ai-collab" / "requests"
    q.mkdir(parents=True)
    (q / "R7.md").write_text('---\nrequest_id: "R7"\n---\n개선 지시\n', encoding="utf-8")
    (q / ".gitkeep").write_text("", encoding="utf-8")
    subprocess.run(["git", "-C", str(other), "add", "."], check=True)
    subprocess.run(["git", "-C", str(other), "commit", "-q", "-m", "req"], check=True)
    subprocess.run(["git", "-C", str(other), "push", "-q", "origin", "main"], check=True)
    hit = _run(r, "poll")
    assert hit.returncode == 0 and "개선 지시" in hit.stdout and ".gitkeep" not in hit.stdout
    assert _run(r, "poll").returncode == 3                                  # 읽은 것은 다시 알리지 않음
    (q / "R7.md").write_text('---\nrequest_id: "R7"\n---\n수정된 지시\n', encoding="utf-8")
    subprocess.run(["git", "-C", str(other), "commit", "-qam", "req2"], check=True)
    subprocess.run(["git", "-C", str(other), "push", "-q", "origin", "main"], check=True)
    again = _run(r, "poll")
    assert again.returncode == 0 and "수정된 지시" in again.stdout
