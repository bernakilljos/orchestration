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
    subprocess.run(["git", "-C", str(r), "commit", "-q", "-m", body], check=True)


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
        (r / ".ai-collab" / "reviews" / f"{rid}.md").write_text("ok", encoding="utf-8")
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
