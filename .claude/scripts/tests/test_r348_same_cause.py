"""R348#1 의미 기반 동일 원인 후보 — 줄 전체 일치(same_pattern_candidates)는 언어가 다른 짝 파일·조건 줄·호출하는 곳을 못 찾았다
(보고서 R348: R337 suggest_skills.py ↔ suggest-skills.sh · R344 조건 줄 · R341 호출 경로). 격리 git 저장소에서 확인."""
import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("iv_r348", ROOT / ".claude" / "scripts" / "lib" / "independent_verifier.py")
iv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iv)


def _git(cwd, *a):
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=str(cwd), capture_output=True,
                          text=True, encoding="utf-8", check=True).stdout


def _repo(tmp_path):
    r = tmp_path / "repo"
    (r / "hooks").mkdir(parents=True)
    (r / "scripts").mkdir()
    (r / "hooks" / "suggest_skills.py").write_text(
        'import re\n\ndef should_delegate(p):\n    return re.search(r"(전부|모두|다)\\s*해", p) is not None\n', encoding="utf-8")
    (r / "hooks" / "suggest-skills.sh").write_text(
        '#!/bin/bash\nif echo "$1" | grep -qE "(전부|모두|다)\\s*해"; then echo delegate; fi\n', encoding="utf-8")
    (r / "scripts" / "router.py").write_text(
        "from hooks.suggest_skills import should_delegate\n\ndef route(p):\n    return 'explore' if should_delegate(p) else 'main'\n",
        encoding="utf-8")
    (r / "scripts" / "unrelated.py").write_text("def other():\n    return 42\n", encoding="utf-8")
    _git(r, "init", "-q")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "base")
    return r


def _fix(r):
    p = r / "hooks" / "suggest_skills.py"
    p.write_text(p.read_text(encoding="utf-8").replace('(전부|모두|다)\\s*해', '(전부|모두)\\s*해줘'), encoding="utf-8")


def test_line_only_misses_sibling_and_caller(tmp_path):
    r = _repo(tmp_path)
    _fix(r)
    assert iv.same_pattern_candidates(r) == []                   # 수정 전 방식: 아무것도 못 찾음 (재현)
    old = {c["path"] for c in iv.semantic_same_cause(r, methods=("line",))}
    assert old == set()


def test_semantic_finds_cross_language_sibling_and_caller(tmp_path):
    r = _repo(tmp_path)
    _fix(r)
    got = {c["path"]: c["reasons"] for c in iv.semantic_same_cause(r)}
    assert "hooks/suggest-skills.sh" in got and {"literal", "sibling"} <= set(got["hooks/suggest-skills.sh"]), got
    assert "caller" in got.get("scripts/router.py", []), got
    assert "scripts/unrelated.py" not in got and "hooks/suggest_skills.py" not in got   # 무관·자기 자신 제외


def test_rev_mode_reads_past_tree_without_touching_worktree(tmp_path):
    r = _repo(tmp_path)
    _fix(r)
    _git(r, "commit", "-qam", "fix")
    (r / "hooks" / "suggest-skills.sh").unlink()                 # 작업본에서 지워도 과거 시점 트리에서 찾음
    diff = _git(r, "diff", "-U0", "HEAD^", "HEAD")
    got = {c["path"] for c in iv.semantic_same_cause(r, diff=diff, rev="HEAD^")}
    assert "hooks/suggest-skills.sh" in got and "scripts/router.py" in got, got


def test_generic_literal_over_threshold_is_ignored(tmp_path):
    r = _repo(tmp_path)
    for i in range(25):                                          # 25곳에 같은 문구 = 일반 구문 → 신호로 안 씀
        (r / "scripts" / f"m{i}.py").write_text('print("loading configuration")\n', encoding="utf-8")
    (r / "scripts" / "a_target.py").write_text('print("loading configuration")\n', encoding="utf-8")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "many")
    (r / "scripts" / "a_target.py").write_text('print("loading settings")\n', encoding="utf-8")
    got = {c["path"] for c in iv.semantic_same_cause(r, methods=("literal",))}
    assert not any(p.startswith("scripts/m") for p in got), got
