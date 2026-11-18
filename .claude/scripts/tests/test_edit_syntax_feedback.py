"""코드 수정 직후 문법 검사 결과가 Claude 에게 실제로 되돌아가는지 (2026-11-13 · R249).

결함: 검사는 오류를 찾았지만 Claude 가 받을 수 있는 형식이 아니었다 (공식 hooks 문서 기준).
  - 파이썬: systemMessage 만 → "Warning message shown to the user" (Claude 미전달)
  - JS·TS: 오류 원문을 JSON 에 그대로 끼워 파싱 실패 → "Non-blocking error" (Claude 미전달)
  - TS: '| head -5' 뒤 $? = head 종료 코드 → 오류가 한 번도 보고되지 않음
  - post-impl-verify: 실패 문구를 stdout + exit 2 → exit 2 에서 Claude 가 받는 건 stderr 뿐
Claude 가 받는 형식 = PostToolUse 의 {"decision":"block","reason":...} 또는 exit 2 + stderr.
실제 디스패처·실제 셸 스크립트를 임시 폴더 파일로 실행한다 (운영 파일 불변).
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
BASH = os.environ.get("BASH_EXE") or (
    r"C:\Program Files\Git\bin\bash.exe" if os.name == "nt" and Path(r"C:\Program Files\Git\bin\bash.exe").exists() else "bash")


def _payload(path: Path) -> bytes:
    return json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(path)}}).encode("utf-8")


def _dispatch_post(path: Path) -> str:
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(ROOT), PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / ".claude" / "hooks" / "tool-dispatch.py"), "post"],
                       input=_payload(path), capture_output=True, env=env, timeout=120)
    return p.stdout.decode("utf-8", "replace")


def _json_objects(text: str) -> list:
    out = []
    for ln in text.splitlines():
        ln = ln.strip()
        if ln.startswith("{"):
            try:
                out.append(json.loads(ln))
            except ValueError:
                pass
    if not out and text.strip().startswith("{"):
        out.append(json.loads(text))   # 여러 줄 JSON — 파싱 실패면 여기서 예외 (= Claude 미전달)
    return out


def _run_js_hook(path: Path, project_dir: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(project_dir))
    return subprocess.run([BASH, str(ROOT / ".claude" / "hooks" / "check-js-syntax.sh")], input=_payload(path),
                          capture_output=True, env=env, timeout=120)


# ---------- 파이썬 ----------
def test_python_syntax_error_reaches_claude(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("def f(:\n    return 1\n", encoding="utf-8")
    objs = [o for o in _json_objects(_dispatch_post(bad)) if "py_compile" in json.dumps(o, ensure_ascii=False)]
    assert objs, "파이썬 검사 출력 없음"
    o = objs[0]
    assert o.get("decision") == "block" and "py_compile FAIL" in o.get("reason", "")   # Claude 가 받는 필드


def test_python_valid_file_does_not_block(tmp_path):
    ok = tmp_path / "ok.py"
    ok.write_text("def f():\n    return 1\n", encoding="utf-8")
    objs = [o for o in _json_objects(_dispatch_post(ok)) if "py_compile" in json.dumps(o, ensure_ascii=False)]
    assert objs and all(o.get("decision") != "block" for o in objs)


# ---------- JS ----------
@pytest.mark.skipif(shutil.which("node") is None, reason="node 없음")
def test_js_syntax_error_is_valid_json_block(tmp_path):
    bad = tmp_path / "bad.js"
    bad.write_text('function f( {\n  return "x";\n}\n', encoding="utf-8")   # 줄바꿈·따옴표·Windows 경로가 오류에 들어감
    p = _run_js_hook(bad, ROOT)
    out = p.stdout.decode("utf-8", "replace")
    o = json.loads(out)                    # 예전: Invalid \escape 로 실패 → Claude 미전달
    assert o["decision"] == "block" and "SyntaxError" in o["reason"] and "bad.js" in o["reason"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node 없음")
def test_js_valid_file_silent(tmp_path):
    ok = tmp_path / "ok.js"
    ok.write_text("function f() { return 'x'; }\n", encoding="utf-8")
    p = _run_js_hook(ok, ROOT)
    assert p.returncode == 0 and p.stdout.strip() == b""


# ---------- TS (프로젝트 node_modules/.bin/tsc · 종료 코드) ----------
def test_ts_error_reported_via_project_tsc_exit_code(tmp_path):
    if shutil.which("tsc"):
        pytest.skip("전역 tsc 가 있으면 가짜 tsc 를 쓰지 않음")
    proj = tmp_path / "proj"
    (proj / "node_modules" / ".bin").mkdir(parents=True)
    (proj / ".claude" / "state").mkdir(parents=True)
    fake = proj / "node_modules" / ".bin" / "tsc"
    fake.write_text('#!/usr/bin/env bash\necho "x.ts(1,17): error TS1109: Expression expected."\nexit 2\n',
                    encoding="utf-8", newline="\n")
    os.chmod(fake, 0o755)
    bad = proj / "x.ts"
    bad.write_text("let x: number = ;\n", encoding="utf-8")
    p = _run_js_hook(bad, proj)
    o = json.loads(p.stdout.decode("utf-8", "replace"))   # 예전: head 종료 코드 0 → 출력 없음
    assert o["decision"] == "block" and "TS1109" in o["reason"]


# ---------- 완료 전 검증 (exit 2 의 메시지 = stderr) ----------
def test_post_impl_verify_failure_text_goes_to_stderr(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    g = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, check=True)  # noqa: E731
    g("init", "-q")
    g("config", "user.email", "t@t")
    g("config", "user.name", "t")
    (repo / "a.txt").write_text("a", encoding="utf-8")
    g("add", "-A")
    g("commit", "-qm", "base")
    (repo / "bad.py").write_text("def f(:\n", encoding="utf-8")
    g("add", "-A")
    g("commit", "-qm", "bad")
    for script in (ROOT / "plugins" / "review_qa" / "hooks" / "post-impl-verify.sh",
                   ROOT / ".claude" / "hooks" / "post-impl-verify.sh"):
        p = subprocess.run([BASH, str(script)], cwd=repo, capture_output=True, timeout=120,
                           env=dict(os.environ, PROJECT_ROOT=str(repo)))
        assert p.returncode == 2, script
        assert b"Python syntax error" in p.stderr and p.stdout.strip() == b"", script   # 예전: stdout 에만


# ---------- Vue (프로젝트에 이미 있는 vue/compiler-sfc · 가짜 모듈로 배선만 검증 — 실제 IFRS 285개 오탐 0 은 §91 기록) ----------
_FAKE_V3 = """exports.parse=(src,o)=>{if(typeof src!=='string')return{descriptor:{}};
 return {descriptor:{template:{content:src},script:null,scriptSetup:null},errors:[]}};
exports.compileTemplate=(o)=>({errors:o.source.includes('BROKEN')?[{message:'invalid expression: BROKEN'}]:[]});
"""
# Vue 2.7 형: parse(source, opts) 로 부르면 빈 descriptor · parse({source}) 만 동작 · 구조 단계 errors 는 경고
_FAKE_V2 = """exports.parse=(a,o)=>{if(typeof a==='string')return {template:null,script:null,scriptSetup:null,errors:[]};
 return {template:{content:a.source},script:null,scriptSetup:null,errors:['tag <br> has no matching end tag.']}};
exports.compileTemplate=(o)=>({errors:o.source.includes('BROKEN')?['invalid expression: BROKEN']:[]});
"""


def _vue_project(tmp_path, fake: str) -> Path:
    proj = tmp_path / "vproj"
    mod = proj / "node_modules" / "vue" / "compiler-sfc"
    mod.mkdir(parents=True)
    (mod / "index.js").write_text(fake, encoding="utf-8")
    (mod / "package.json").write_text('{"name":"vue-compiler-sfc-fake","main":"index.js"}', encoding="utf-8")
    return proj


@pytest.mark.skipif(shutil.which("node") is None, reason="node 없음")
@pytest.mark.parametrize("fake", [_FAKE_V3, _FAKE_V2], ids=["vue3", "vue2"])
def test_vue_template_error_blocks(tmp_path, fake):
    proj = _vue_project(tmp_path, fake)
    bad = proj / "Bad.vue"
    bad.write_text("<template>\n  <div v-if=\"BROKEN\"></div>\n</template>\n", encoding="utf-8")
    o = json.loads(_run_js_hook(bad, proj).stdout.decode("utf-8", "replace"))
    assert o["decision"] == "block" and "BROKEN" in o["reason"]   # vue2: 예전엔 빈 descriptor → 검사 0 → 통과


@pytest.mark.skipif(shutil.which("node") is None, reason="node 없음")
def test_vue2_structure_warning_does_not_block(tmp_path):
    proj = _vue_project(tmp_path, _FAKE_V2)
    ok = proj / "Ok.vue"
    ok.write_text("<template>\n  <div><br></div>\n</template>\n", encoding="utf-8")
    p = _run_js_hook(ok, proj)
    assert p.returncode == 0 and b"decision" not in p.stdout   # 실제 IFRS: <br>·<input> 경고 10건 오탐이었음


def test_vue_checker_is_separate_file_not_multiline_node_e():
    """Git Bash → Windows node 에 여러 줄 `node -e` 인자는 첫 줄만 전달된다 → 검사 본문은 파일이어야 한다."""
    sh = (ROOT / ".claude" / "hooks" / "check-js-syntax.sh").read_text(encoding="utf-8")
    assert "vue-sfc-check.js" in sh and "node -e '\n" not in sh
    assert (ROOT / ".claude" / "hooks" / "vue-sfc-check.js").is_file()

