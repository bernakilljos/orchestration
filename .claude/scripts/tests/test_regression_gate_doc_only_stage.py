"""회귀 게이트 — 문서만 더 stage 하면 다시 돌리지 않는다 (11-16 바로잡기).

전체 회귀(7분 15초) 통과 직후 커밋 훅이 CLAUDE.md AUTO-STATS 날짜 한 줄 stage 를 요구 → 트리 해시가 바뀌어 stale
→ 재실행 중 dev 회차 61분 시간 초과(11-16 21:40). 이제 기록의 code_tree(코드 파일만의 지문)가 같으면 통과.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / ".claude" / "hooks" / "pre-commit-full-check.sh"
sys.path.insert(0, str(ROOT / ".claude" / "scripts" / "lib"))
import independent_verifier as iv  # noqa: E402

BASH = shutil.which("bash")


def _git(cwd, *a):
    subprocess.run(["git", *a], cwd=str(cwd), check=True, capture_output=True)


def _repo(tmp_path):
    r = tmp_path / "repo"
    (r / "plugins").mkdir(parents=True)
    (r / "engine").mkdir()
    (r / ".claude" / "scripts" / "lib").mkdir(parents=True)
    (r / ".claude" / "scripts" / "lib" / "independent_verifier.py").write_text("# placeholder\n", encoding="utf-8")
    (r / "engine" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (r / "notes.md").write_text("one\n", encoding="utf-8")
    _git(r, "init", "-q")
    _git(r, "-c", "user.email=t@t", "-c", "user.name=t", "add", "-A")
    _git(r, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    return r


def _stamp(r, **kw):
    p = r / ".claude" / "state" / "regression-gate.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(kw), encoding="utf-8")


def _run_hook(r):
    inp = json.dumps({"tool_input": {"command": "git commit -m x"}})
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(r)}
    p = subprocess.run([BASH, str(HOOK)], input=inp, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env, cwd=str(r))
    return p.returncode, p.stderr


def test_code_ext_lists_match():
    src = HOOK.read_text(encoding="utf-8")
    assert "ext=" + repr(iv._CODE_EXT).replace(" ", "") in src.replace(" ", "")


def test_doc_only_extra_stage_keeps_gate(tmp_path):
    if not BASH:
        return
    r = _repo(tmp_path)
    (r / "engine" / "a.py").write_text("x = 2\n", encoding="utf-8")
    _git(r, "add", "engine/a.py")
    tree = subprocess.run(["git", "write-tree"], cwd=str(r), capture_output=True, text=True).stdout.strip()
    _stamp(r, tree=tree, code_tree=iv.code_fingerprint(r), status="pass")
    assert _run_hook(r)[0] == 0
    # 문서만 더 stage → 트리는 바뀌지만 통과
    (r / "notes.md").write_text("two\n", encoding="utf-8")
    _git(r, "add", "notes.md")
    rc, err = _run_hook(r)
    assert rc == 0, err
    # 코드를 더 바꾸면 stale
    (r / "engine" / "a.py").write_text("x = 3\n", encoding="utf-8")
    _git(r, "add", "engine/a.py")
    rc, err = _run_hook(r)
    assert rc == 2 and "stale" in err


def test_old_stamp_without_code_tree_is_stale(tmp_path):
    if not BASH:
        return
    r = _repo(tmp_path)
    (r / "engine" / "a.py").write_text("x = 2\n", encoding="utf-8")
    _git(r, "add", "engine/a.py")
    _stamp(r, tree="0" * 40, status="pass")
    rc, err = _run_hook(r)
    assert rc == 2 and "stale" in err
