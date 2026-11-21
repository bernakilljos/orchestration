"""R354 14차 P2: post-impl-verify 가 `git diff --name-only HEAD~1` (직전 커밋 1개) 만 보고 `for f in $(...)` 로 공백에서
파일명을 쪼갰다 → 한 작업의 앞 커밋에만 든 산출물·공백 든 파일명이 검증에서 빠졌다 (검증 안 된 것을 통과로 보임).
변경 집합 = 커밋 안 한 변경 + 새 파일 + 원격에 아직 안 올린 커밋 전체 (원격 추적 없으면 직전 커밋) · NUL 구분."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / "plugins" / "review_qa" / "hooks" / "post-impl-verify.sh"
VOP = ROOT / ".claude" / "scripts" / "verify-office-package.py"
BASH = shutil.which("bash")
pytestmark = pytest.mark.skipif(not BASH, reason="bash 없음")


def _git(cwd, *a):
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=str(cwd), check=True,
                   capture_output=True, text=True)


def _repo(tmp_path, upstream=True):
    r = tmp_path / "w"
    (r / ".claude" / "scripts").mkdir(parents=True)
    shutil.copy(VOP, r / ".claude" / "scripts" / VOP.name)
    _git(tmp_path, "init", "-q", "w")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "base")
    if upstream:
        _git(tmp_path, "init", "-q", "--bare", "remote.git")
        _git(r, "remote", "add", "origin", str(tmp_path / "remote.git"))
        _git(r, "push", "-q", "-u", "origin", "HEAD")
    return r


def _run(r):
    env = dict(os.environ, PROJECT_ROOT=str(r))
    p = subprocess.run([BASH, str(HOOK)], cwd=str(r), env=env, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=120)
    return p.returncode, p.stdout + p.stderr


def test_earlier_unpushed_commit_artifact_is_verified(tmp_path):
    r = _repo(tmp_path)
    (r / "bad.xlsx").write_bytes(b"not a zip")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "산출물")
    (r / "note.txt").write_text("다음 커밋", encoding="utf-8")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "후속")                     # 산출물은 직전 커밋이 아니라 그 앞 커밋에만 있음
    rc, out = _run(r)
    assert rc == 2 and "office package: bad.xlsx" in out, out


def test_filename_with_space_is_not_split(tmp_path):
    r = _repo(tmp_path)
    (r / "월간 보고.xlsx").write_bytes(b"not a zip")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "공백 이름")
    rc, out = _run(r)
    assert rc == 2 and "office package: 월간 보고.xlsx" in out, out


def test_uncommitted_and_untracked_artifacts_are_verified(tmp_path):
    r = _repo(tmp_path)
    (r / "new.hwpx").write_bytes(b"not a zip")                 # 아직 add 도 안 한 새 파일
    rc, out = _run(r)
    assert rc == 2 and "office package: new.hwpx" in out, out
    (r / "깨진 모듈.py").write_text("def f(:\n", encoding="utf-8")   # 같은 변경 집합을 쓰는 1절(py 문법)도 공백 이름 그대로
    rc, out = _run(r)
    assert rc == 2 and "Python syntax error: 깨진 모듈.py" in out, out


def test_no_upstream_falls_back_to_last_commit_and_clean_tree_passes(tmp_path):
    r = _repo(tmp_path, upstream=False)
    rc, out = _run(r)
    assert rc == 0 and "office package" not in out, out        # 직전 커밋에 산출물 없음 = 검사할 것 없음
    (r / "x y.pptx").write_bytes(b"not a zip")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "c")
    rc, out = _run(r)
    assert rc == 2 and "office package: x y.pptx" in out, out


def _verify_stub(r):
    """PNG 절은 verify-image-whitespace.py 가 있을 때만 돈다 — 받은 폴더를 기록하고 항상 WARN 을 내는 대역."""
    p = r / ".claude" / "scripts" / "verify-image-whitespace.py"
    p.write_text("import sys\nopen(sys.argv[1] + '/.seen', 'w').write('1')\nprint('WARN x')\n", encoding="utf-8")


def test_png_dirs_space_and_newline_names(tmp_path):
    """R354 15차 P2: PNG 경로는 NUL 을 줄바꿈으로 바꾼 뒤 줄 단위로 폴더를 구해 줄바꿈 든 파일명이 폴더를 잘못 나눴다."""
    r = _repo(tmp_path)
    _verify_stub(r)
    (r / "docs" / "월간 화면").mkdir(parents=True)
    (r / "docs" / "월간 화면" / "a b.png").write_bytes(b"x")
    rc, out = _run(r)
    assert "PNG whitespace in docs/월간 화면 " in out, out                   # 공백 폴더 1개로 인식
    try:
        (r / "docs" / "줄\n바꿈").mkdir()
        (r / "docs" / "줄\n바꿈" / "p.png").write_bytes(b"x")
    except OSError:
        pytest.skip("이 파일 시스템은 파일명에 줄바꿈 불가 (Windows NTFS) — Linux CI 에서 확인")
    rc, out = _run(r)
    assert (r / "docs" / "줄\n바꿈" / ".seen").exists(), out                   # 줄바꿈 폴더를 그대로 받아 검사함
    assert not (r / "docs" / "줄").exists() and "PNG whitespace in 바꿈" not in out
