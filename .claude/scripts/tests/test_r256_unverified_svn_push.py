"""R256 (2026-11-15) — 사용자 재검토 3건.

1) 검사기가 없어 못 본 변경 파일(unchecked) = 미검증 → 커밋 차단 (전에는 기록만 하고 pass)
   + 커밋 훅 확장자 목록 = 게이트 _CODE_EXT · CLI 종료 코드 (syntax_error 가 0 으로 나가던 것)
2) 문법 오류 → 차단 → 고침 → 통과 종단 간 (git 커밋 훅 · 실제 SVN 작업본의 svn commit 훅)
   IFRS 는 SVN 이라 git 커밋 훅이 한 번도 돌지 않았다 · java·xml·yml 은 검사 대상에도 없었다
3) 승인 게이트 push 오탐 — 실제 막힌 명령 3건(appr-7d5799dacb11 · appr-2b6e593318ef · appr-04a492249c3f) 재현 통과 +
   실행 경로(파이프·치환·인터프리터·훅 파일 쓰기·작업 위치 변경)는 그대로 차단
"""
from __future__ import annotations

import atexit
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[3]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


iv = _load("iv_r256", KIT / ".claude/scripts/lib/independent_verifier.py")
P = "gi" + "t pu" + "sh"          # 명령 글자 자체가 이 시험 파일을 실행하는 셸 명령에 나타나지 않게
PUSH = P + " origin main"


# ── 1) 미검증 차단 · 목록 일치 · 종료 코드 ─────────────────────────────────
def _repo(tmp_path):
    g = shutil.which("git")
    if not g:
        pytest.skip("git 없음")
    d = tmp_path / "repo"
    d.mkdir()
    for a in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"],
              ["config", "core.autocrlf", "false"]):
        subprocess.run([g, *a], cwd=d, check=True)
    (d / "base.txt").write_text("b", encoding="utf-8")
    subprocess.run([g, "add", "."], cwd=d, check=True)
    subprocess.run([g, "commit", "-qm", "base"], cwd=d, check=True)
    return d, g


def _no_tests(monkeypatch):
    monkeypatch.setattr(iv, "impact_selection", lambda cwd, staged: {"full": False, "why": "", "tests": []})


def test_unchecked_file_blocks_as_unverified(tmp_path, monkeypatch):
    d, g = _repo(tmp_path)
    (d / "run.bat").write_text("@echo off\r\necho hi\r\n", encoding="utf-8")
    subprocess.run([g, "add", "run.bat"], cwd=d, check=True)
    _no_tests(monkeypatch)
    res = iv.regression_gate(d, timeout=60)
    assert res["status"] == "unverified" and res["syntax_unchecked"] == ["run.bat (문법 검사기 없음)"]
    assert "자동 커밋하지 않음" in res["reason"]


def test_hook_extensions_match_gate_code_ext():
    sh = (KIT / ".claude/hooks/pre-commit-full-check.sh").read_text(encoding="utf-8")
    m = re.search(r"grep -qiE '\\\.\(([^)]*)\)\$'", sh)
    assert m, "훅의 확장자 정규식을 못 찾음"
    assert {"." + x for x in m.group(1).split("|")} == set(iv._CODE_EXT)


def test_cli_exit_codes_fail_on_syntax_error_and_unverified(tmp_path):
    d, g = _repo(tmp_path)
    (d / "src.py").write_text("print(\n", encoding="utf-8")
    subprocess.run([g, "add", "src.py"], cwd=d, check=True)
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(d), "PYTHONUTF8": "1"}
    r = subprocess.run([sys.executable, str(KIT / ".claude/scripts/lib/independent_verifier.py"), "regression-gate"],
                       env=env, capture_output=True, text=True, encoding="utf-8", timeout=300)
    assert r.returncode == 2 and '"syntax_error"' in r.stdout          # 전에는 0 (통과로 읽힘)
    (d / "src.py").write_text("x = 1\n", encoding="utf-8")
    (d / "go.bat").write_text("@echo off\n", encoding="utf-8")
    subprocess.run([g, "add", "src.py", "go.bat"], cwd=d, check=True)
    r = subprocess.run([sys.executable, str(KIT / ".claude/scripts/lib/independent_verifier.py"), "regression-gate"],
                       env=env, capture_output=True, text=True, encoding="utf-8", timeout=300)
    assert r.returncode == 1 and '"unverified"' in r.stdout


def test_new_checkers_catch_errors_and_pass_valid(tmp_path):
    files = {"ok.xml": "<a><b/></a>\n", "bad.xml": "<a><b></a>\n",
             "ok.yml": "a: 1\nb: !Ref x\n---\nc: [1, 2]\n", "bad.yml": "a: [1, 2\nb: 3\n",
             "tsconfig.json": '{ // 주석\n "a": "x//y", /* z */ "b": [1,2,],\n}\n', "bad.json": '{"a": 1,}'}
    for k, v in files.items():
        (tmp_path / k).write_text(v, encoding="utf-8")
    names = list(files)
    if shutil.which("powershell") or shutil.which("pwsh"):
        (tmp_path / "ok.ps1").write_text("Write-Host 'hi'\n", encoding="utf-8")
        (tmp_path / "bad.ps1").write_text("function f( {\n", encoding="utf-8")
        names += ["ok.ps1", "bad.ps1"]
    if shutil.which("javac"):
        (tmp_path / "Ok.java").write_text("package a;\nimport org.x.Y;\nclass Ok { Y y; void m(){ Z.q(); } }\n",
                                          encoding="utf-8")   # 해석 못 하는 import·심볼 = 문법 오류 아님
        (tmp_path / "Bad.java").write_text("package a;\nclass Bad { void m() { int x = ; } }\n", encoding="utf-8")
        names += ["Ok.java", "Bad.java"]
    r = iv.staged_syntax_check(tmp_path, names)
    bad = {e["file"] for e in r["errors"]}
    assert bad == {n for n in names if n.lower().startswith("bad")}, r
    assert set(r["checked"]) == {n for n in names if not n.lower().startswith("bad")}, r
    assert r["unchecked"] == []


# ── 2) 종단 간: git 커밋 훅 ────────────────────────────────────────────
def _hook(d: Path, cmd: str):
    return subprocess.run(["bash", str(d / ".claude/hooks/pre-commit-full-check.sh")],
                          input=json.dumps({"tool_input": {"command": cmd}}), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60, env={**os.environ, "CLAUDE_PROJECT_DIR": str(d)})


@pytest.mark.skipif(not shutil.which("bash"), reason="bash 없음")
def test_git_commit_hook_blocks_syntax_error_then_allows_after_fix(tmp_path, monkeypatch):
    d, g = _repo(tmp_path)
    (d / "plugins").mkdir()
    (d / ".claude/hooks").mkdir(parents=True)
    (d / ".claude/scripts/lib").mkdir(parents=True)
    shutil.copy(KIT / ".claude/hooks/pre-commit-full-check.sh", d / ".claude/hooks/")
    shutil.copy(KIT / ".claude/scripts/lib/independent_verifier.py", d / ".claude/scripts/lib/")
    (d / "src").mkdir()
    (d / "src/app.py").write_text("def f(:\n    return 1\n", encoding="utf-8")
    subprocess.run([g, "add", "src/app.py"], cwd=d, check=True)
    _no_tests(monkeypatch)
    assert iv.regression_gate(d, timeout=60)["status"] == "syntax_error"
    r = _hook(d, "git commit -m x")
    assert r.returncode == 2 and "문법 오류" in r.stderr                # ① 오류를 받는다 (stderr = Claude 에게 전달)
    (d / "src/app.py").write_text("def f():\n    return 1\n", encoding="utf-8")   # ② 고친다
    subprocess.run([g, "add", "src/app.py"], cwd=d, check=True)
    assert _hook(d, "git commit -m x").returncode == 2                   # 게이트를 다시 안 돌리면 여전히 차단 (기록 불일치)
    assert iv.regression_gate(d, timeout=60)["status"] == "pass"         # ③ 재검증
    assert _hook(d, "git commit -m x").returncode == 0                   # ④ 통과
    (d / "deploy.bat").write_text("@echo off\n", encoding="utf-8")
    subprocess.run([g, "add", "deploy.bat"], cwd=d, check=True)
    assert iv.regression_gate(d, timeout=60)["status"] == "unverified"
    r = _hook(d, "git commit -m x")
    assert r.returncode == 2 and "자동 커밋하지 않음" in r.stderr


# ── 2) 종단 간: 실제 SVN 작업본 svn commit 훅 ─────────────────────────────
sys.path.insert(0, str(KIT / ".claude/hooks/prompt"))   # _common (test_approval_gate_mentions 와 같은 방식)
pcc = _load("pcc_r256", KIT / ".claude/hooks/tool/pre_commit_full_check.py")


@pytest.mark.parametrize("cmd,hit", [
    ("svn commit -m x", True), ("svn ci -m x src/A.java", True), ("svn --non-interactive commit -m x", True),
    ("cd /c/IFRS_PJT && svn commit -m 'fix'", True), ("& svn.exe commit -m x", True),
    ("svn status -q", False), ("svn log -l 3", False), ('echo "svn commit -m x"', False),
    ("grep -n 'svn commit' notes.md", False), ("svn diff ci.txt", False),
])
def test_svn_commit_detection(cmd, hit):
    assert pcc.is_svn_commit_invocation(cmd) == hit


@pytest.mark.skipif(not (shutil.which("svn") and shutil.which("svnadmin")), reason="svn·svnadmin 없음")
def test_svn_commit_hook_blocks_syntax_error_then_allows_after_fix(tmp_path):
    repo, wc = tmp_path / "repo", tmp_path / "wc"
    subprocess.run(["svnadmin", "create", str(repo)], check=True)
    url = "file:///" + str(repo).replace("\\", "/").lstrip("/")
    subprocess.run(["svn", "checkout", "-q", "--non-interactive", url, str(wc)], check=True)
    (wc / ".claude/scripts/lib").mkdir(parents=True)          # 버전 관리 안 됨(?) — 수정 파일 목록에 안 잡힌다
    shutil.copy(KIT / ".claude/scripts/lib/independent_verifier.py", wc / ".claude/scripts/lib/")
    (wc / "src").mkdir()
    (wc / "src/app.py").write_text("print(\n", encoding="utf-8")
    subprocess.run(["svn", "add", "-q", str(wc / "src")], check=True)
    ctx = type("Ctx", (), {"project_dir": str(wc)})()
    r = pcc._svn_syntax_gate(ctx)
    assert r is not None and r.rc == 2 and "기록 없음" in r.err             # 게이트 안 돌림 = 차단
    assert iv.syntax_gate(wc)["status"] == "syntax_error"
    r = pcc._svn_syntax_gate(ctx)
    assert r.rc == 2 and "문법 오류" in r.err and "src/app.py" in r.err    # ① 오류 전달
    (wc / "src/app.py").write_text("print(1)\n", encoding="utf-8")       # ② 고침
    assert pcc._svn_syntax_gate(ctx).rc == 2                              # 기록 뒤 바뀐 파일 = 차단
    assert iv.syntax_gate(wc)["status"] == "pass"                          # ③ 재검증
    assert pcc._svn_syntax_gate(ctx) is None                               # ④ svn commit 통과
    (wc / "src/run.bat").write_text("@echo off\n", encoding="utf-8")
    subprocess.run(["svn", "add", "-q", str(wc / "src/run.bat")], check=True)
    assert iv.syntax_gate(wc)["status"] == "unverified"
    r = pcc._svn_syntax_gate(ctx)
    assert r.rc == 2 and "자동 커밋하지 않음" in r.err


def test_svn_gate_not_applied_outside_svn(tmp_path):
    ctx = type("Ctx", (), {"project_dir": str(tmp_path)})()
    assert pcc._svn_syntax_gate(ctx) is None


# ── 3) push 오탐 ───────────────────────────────────────────────────────
def _isolated_kit() -> Path:
    """기록 전용 스크립트 허용은 «kit HEAD 와 같은 내용» 일 때만 → 현재 작업본을 커밋한 격리 저장소에서 판정 (운영 kit 이력 불변)."""
    d = Path(tempfile.mkdtemp(prefix="r256-kit-"))
    atexit.register(shutil.rmtree, d, True)
    for rel in (".claude/hooks/tool", ".claude/hooks/prompt/_common.py", ".claude/scripts/lib",
                ".claude/scripts/approval-gate.py", ".claude/scripts/request-ledger.py",
                ".claude/scripts/auto-save-next-actions.py"):
        src, dst = KIT / rel, d / rel
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.db", "*.db-*", "*.sqlite*"))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
    g = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false"]
    for a in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "isolated"]):
        subprocess.run(g + a, cwd=d, check=True, capture_output=True)
    return d


_SYS = list(sys.path)
ROOT = _isolated_kit()
sys.path.insert(0, str(ROOT / ".claude/hooks/prompt"))
agd = _load("agd_r256", ROOT / ".claude/hooks/tool/approval_gate_detect.py")
gate = _load("gate_r256", ROOT / ".claude/scripts/approval-gate.py")
sys.path[:] = _SYS
assert Path(agd._KIT_ROOT).resolve() == ROOT.resolve()
CWD = str(ROOT).replace("\\", "/")


def flagged(cmd: str, cwd: str = "") -> bool:
    return gate.detect_risk(agd._strip_inert_text(agd._strip_git_commit_message(cmd), cwd)) is not None


def test_real_false_positive_grep_with_escaped_quote():      # appr-7d5799dacb11 원문 그대로
    cmd = ('grep -n "' + P + '\\b\\|\\"' + P + "\\|'" + P + '" .claude/scripts/tests/*.py | grep -v '
           '"force\\|--delete\\|-f \\|+main\\|:main\\|mirror" | head -30')
    assert not flagged(cmd)


def test_real_false_positive_python_data_heredoc():          # appr-2b6e593318ef 형태 (guide.txt 문장 수정)
    body = ("p='guide.txt'; t=open(p,encoding='utf-8').read()\n"
            "add=\"- 일반 push 자동: 단독 '" + P + "' / '" + PUSH + "' 는 승인 없이\"\n"
            "open(p,'w',encoding='utf-8').write(t+add)\n")
    assert not flagged("grep -n 'R249' guide.txt | head -1; python -X utf8 - <<'EOF'\n" + body + "EOF")
    assert not flagged('python -X utf8 - "$S/orig.py" <<\'EOF\'\nimport sys,re\nprint("' + PUSH + '")\nEOF\n')


def test_real_false_positive_ledger_evidence_relative_path():  # appr-04a492249c3f 원문 형태
    cmd = ('python -X utf8 .claude/scripts/request-ledger.py complete R255 --verification PARTIAL '
           '--evidence "52587c4 ' + PUSH + '(| tail 붙인 push 승인 없이 반영 실측) · 시험 25"')
    assert not flagged(cmd, CWD)                    # 세션 작업 위치 = kit · 작업 위치 변경 없음 · HEAD 와 같은 내용
    assert flagged(cmd)                             # 작업 위치를 모르면 그대로 차단 (기존 결정 유지)
    assert flagged("cd /tmp && " + cmd, CWD)        # 작업 위치를 바꾸면 기준 폴더 불확정 → 차단
    assert flagged(cmd.replace("request-ledger.py complete", "request-ledger.py gate"), CWD)   # 허용 하위 명령만
    assert flagged(cmd.replace("request-ledger.py", "other-script.py"), CWD)


def test_ledger_script_changed_after_commit_is_blocked():
    note = ROOT / ".claude/scripts/request-ledger.py"
    orig = note.read_bytes()
    cmd = 'python -X utf8 .claude/scripts/request-ledger.py complete R1 --verification PASS --evidence "' + PUSH + '"'
    try:
        note.write_bytes(orig + b"\nimport os; os.system(__import__('sys').argv[-1])\n")
        assert flagged(cmd, CWD)                    # 커밋 안 된 변경 = 무결성 불일치 → 차단
    finally:
        note.write_bytes(orig)


@pytest.mark.parametrize("cmd", [
    'grep "$(' + PUSH + ')" notes.md',                                   # 큰따옴표 안 치환은 실행 (전에는 가려짐)
    'grep -h "' + PUSH + '" notes.md | bash',                            # 검색 결과를 셸로
    'grep -h "' + PUSH + '" notes.md | xargs -I{} sh -c "{}"',
    "python - <<'EOF'\nimport subprocess; subprocess.run(['git','push'])\nEOF",
    "python - <<'EOF'\nimport sys; sys.modules['os'].system('" + PUSH + "')\nEOF",
    "python - <<'EOF'\nimport pathlib; pathlib.os.system('" + PUSH + "')\nEOF",
    "python - <<'EOF'\n__builtins__.__import__('os').system('" + PUSH + "')\nEOF",
    "python - <<'EOF'\nf=getattr\nf(1,'x')('" + PUSH + "')\nEOF",
    "python - <<'EOF'\nopen('.git/hooks/post-commit','w').write('" + PUSH + "')\nEOF",
    "python - <<EOF\nprint('" + PUSH + "')\nEOF",                         # 따옴표 없는 구분자 = 셸 확장 → 본문 판정 안 함
    "python - <<'EOF' | bash\nprint('" + PUSH + "')\nEOF",               # 출력을 셸로
    "python - <<'EOF' > run.sh\nprint('" + PUSH + "')\nEOF",
    "python - <<'EOF'\nprint('x')\nEOF\n" + PUSH + " --force",            # heredoc 뒤 실제 실행
    "cat > .git/hooks/pre-push <<'EOF'\n" + PUSH + " --force\nEOF",      # 훅 파일 = 나중에 git 이 실행 (전에는 가려짐)
    PUSH + " --force",
    "echo x && " + PUSH,
])
def test_execution_paths_still_blocked(cmd):
    assert flagged(cmd, CWD), cmd


def test_plain_push_still_allowed_and_detect_unchanged():
    assert not flagged(PUSH, CWD)                   # R250 사용자 위임 그대로
    assert flagged("cd /c/x && " + PUSH, CWD)        # HEAD 무결성 그대로
