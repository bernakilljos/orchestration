"""R255 (2026-11-14) — 커밋 게이트 보완 시험.

1) 변경 소스 자체 문법 검사 (회귀 시험 통과와 별개) · 오류 표본을 넣으면 반드시 잡고 커밋 차단
2) pytest 종료 코드 5 (시험 0건 수집) 는 통과 아님
3) 일반 push 에 붙은 cd 접두·출력 파이프 때문에 생기던 불필요한 승인 요청 제거 (강제·삭제·연결은 그대로 차단)
4) 24시간 넘은 대기 승인 요청은 expired 로 자동 변경
"""
from __future__ import annotations

import importlib.util
import shutil
import sqlite3
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


iv = _load("iv_r255", ".claude/scripts/lib/independent_verifier.py")
ag = _load("ag_r255", ".claude/scripts/approval-gate.py")


# ── 3) 일반 push ─────────────────────────────────────────────
@pytest.mark.parametrize("cmd", [
    "git push origin main 2>&1 | tail -2",          # appr-b4baf8033922 실제 명령
    "git push origin main 2>&1 | tail -8",
    "git push origin main | head -n 5",
    "git push -q 2>&1",
    "git push",
])
def test_plain_push_variants_need_no_approval(cmd):
    assert ag.is_plain_push(cmd)
    assert ag.detect_risk(cmd) is None


@pytest.mark.parametrize("cmd", [
    "git push --force origin main 2>&1 | tail -2",
    "git push -f origin main | tail -2",
    "git push origin :main 2>&1",
    "git push origin +main | tail -1",
    "git push origin main; rm -rf build",
    "git push origin main | sh",
    "cd $(echo /tmp) && git push origin main",
    "cd x && git push --mirror",
    "cd /c/pjt/orchestration_v1 && git push origin main",   # 저장소·HEAD 확정 불가 → 그대로 차단 (HEAD 무결성)
    'cd "C:\\pjt\\orchestration_v1"; git push -q',
    "git push upstream main | tail -2",
    "git commit -m x && git push origin main",
])
def test_dangerous_or_chained_push_still_gated(cmd):
    assert not ag.is_plain_push(cmd)


# ── 4) 만료 ────────────────────────────────────────────────
def test_expire_stale_marks_only_old_waiting(tmp_path, monkeypatch):
    db = tmp_path / "orca.db"
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE tasks (task_id TEXT PRIMARY KEY, approval_state TEXT, status TEXT, "
              "risk_category TEXT, risk_detail TEXT, created_at INTEGER)")
    now = int(time.time())
    c.executemany("INSERT INTO tasks VALUES (?,?,?,?,?,?)", [
        ("old", "waiting", "pending", "irreversible", "{}", now - 90000),
        ("new", "waiting", "pending", "irreversible", "{}", now - 60),
        ("appr", "approved", "pending", "irreversible", "{}", now - 90000),
    ])
    c.commit(); c.close()
    monkeypatch.setattr(ag, "get_db_path", lambda: db)
    assert ag.expire_stale(now) == 1
    rows = dict(sqlite3.connect(db).execute("SELECT task_id, approval_state FROM tasks").fetchall())
    assert rows == {"old": "expired", "new": "waiting", "appr": "approved"}
    assert [x["task_id"] for x in ag.list_waiting()] == ["new"]


# ── 1) 변경 소스 문법 검사 ───────────────────────────────────
def test_syntax_check_catches_injected_errors(tmp_path):
    (tmp_path / "ok.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "bad.py").write_text("def f(:\n    pass\n", encoding="utf-8")
    (tmp_path / "bad.json").write_text('{"a": 1,}', encoding="utf-8")
    (tmp_path / "tsconfig.json").write_text('{ // 주석\n "a": 1 }', encoding="utf-8")
    (tmp_path / "x.ps1").write_text("Write-Host 1", encoding="utf-8")
    files = ["ok.py", "bad.py", "bad.json", "tsconfig.json", "x.ps1"]
    if shutil.which("bash"):
        (tmp_path / "bad.sh").write_text("if [ 1 ; then\n", encoding="utf-8")
        files.append("bad.sh")
    r = iv.staged_syntax_check(tmp_path, files)
    bad = {e["file"] for e in r["errors"]}
    assert {"bad.py", "bad.json"} <= bad and "ok.py" in r["checked"]
    assert "ok.py" not in bad
    if shutil.which("bash"):
        assert "bad.sh" in bad
    assert any(u.startswith("tsconfig.json") for u in r["unchecked"])   # 못 본 것은 통과로 세지 않음
    assert any(u.startswith("x.ps1") for u in r["unchecked"])


@pytest.mark.skipif(not (shutil.which("node") and shutil.which("bash")), reason="node·bash 없음")
def test_syntax_check_js_uses_existing_hook(tmp_path):
    (tmp_path / "bad.js").write_text("function (\n", encoding="utf-8")
    (tmp_path / "ok.js").write_text("const a = 1;\n", encoding="utf-8")
    r = iv.staged_syntax_check(tmp_path, ["bad.js", "ok.js"])
    assert [e["file"] for e in r["errors"]] == ["bad.js"] and r["checked"] == ["ok.js"]


# ── 게이트 연결 (실제 git 저장소) ─────────────────────────────
def _repo(tmp_path):
    g = shutil.which("git")
    if not g:
        pytest.skip("git 없음")
    d = tmp_path / "repo"
    d.mkdir()
    for a in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run([g, *a], cwd=d, check=True)
    (d / "base.txt").write_text("b", encoding="utf-8")
    subprocess.run([g, "add", "."], cwd=d, check=True)
    subprocess.run([g, "commit", "-qm", "base"], cwd=d, check=True)
    return d, g


def test_gate_blocks_commit_on_syntax_error_even_without_tests(tmp_path, monkeypatch):
    d, g = _repo(tmp_path)
    (d / "src.py").write_text("print(\n", encoding="utf-8")
    subprocess.run([g, "add", "src.py"], cwd=d, check=True)
    monkeypatch.setattr(iv, "impact_selection", lambda cwd, staged: {"full": False, "why": "", "tests": []})
    res = iv.regression_gate(d, timeout=60)
    assert res["status"] == "syntax_error" and res["syntax_errors"][0]["file"] == "src.py"


def test_gate_vue_only_change_is_no_longer_skip(tmp_path, monkeypatch):
    d, g = _repo(tmp_path)
    (d / "A.vue").write_text("<template><div></div></template>\n", encoding="utf-8")
    subprocess.run([g, "add", "A.vue"], cwd=d, check=True)
    monkeypatch.setattr(iv, "impact_selection", lambda cwd, staged: {"full": False, "why": "", "tests": []})
    res = iv.regression_gate(d, timeout=60)
    assert res["status"] != "skip" and res["changed_code"] == ["A.vue"]
    assert res["syntax_checked"] == ["A.vue"] or res["syntax_unchecked"]   # 검사했거나 못 본 사유를 남김


def test_gate_pytest_exit5_is_not_pass(tmp_path, monkeypatch):
    d, g = _repo(tmp_path)
    (d / "src.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run([g, "add", "src.py"], cwd=d, check=True)
    monkeypatch.setattr(iv, "impact_selection",
                        lambda cwd, staged: {"full": False, "why": "", "tests": ["tests/test_x.py"]})
    monkeypatch.setattr(iv, "_pytest_failures", lambda cwd, tests, timeout: (set(), "no tests ran in 0.01s", 5))
    res = iv.regression_gate(d, timeout=60)
    assert res["status"] == "blocked" and "수집되지 않음" in res["reason"]


def test_failed_line_with_spaces_in_param_id_is_parsed():
    # 실제 사례: 매개변수 id 안 공백 때문에 실패 0건으로 집계 → 신규 회귀 판정 불가
    win = r".claude\scripts\tests\test_a.py::test_x[cd /c/x; run main-True]"
    out = "FAILED " + win + "\nFAILED tests/test_b.py::test_y - AssertionError: boom\n2 failed, 5 passed"
    assert set(iv._RX_FAILED.findall(out)) == {win, "tests/test_b.py::test_y"}


def test_syntax_check_treats_invalid_escape_warning_as_error(tmp_path):
    (tmp_path / "w.py").write_text('p = "C:' + chr(92) + 'scripts"\n', encoding="utf-8")   # "\s" 잘못된 이스케이프
    r = iv.staged_syntax_check(tmp_path, ["w.py"])
    assert [e["file"] for e in r["errors"]] == ["w.py"]
