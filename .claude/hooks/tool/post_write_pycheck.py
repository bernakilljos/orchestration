"""post_write_pycheck.py 이식 - .py 편집 직후 py_compile 검사 (systemMessage JSON · 항상 exit 0).

성공 경로는 in-process py_compile (원본은 python 하위 프로세스). 실패 시에는 원본과 같은 오류 문구를 위해
원본 방식(하위 프로세스) 으로 한 번 더 돌려 stderr 를 얻는다. 핵심 폴더면 tools/run_quick_tests.py 도 원본처럼 실행.
stdin 은 원본과 같은 방식(시스템 기본 인코딩) 으로 읽는다 - 한글이 든 경로면 원본은 깨진 경로로 compile 해 "FAIL" 이 된다
(_common.py 의 PY_STDIN_FIX 설명 참고). 출력은 원본처럼 utf-8 + errors=replace (깨진 글자는 ?).
"""
from __future__ import annotations

import json
import os
import py_compile
import sys

from _common import Result, py_child_encoding, py_stdin_text

_CODE = "import py_compile,sys; py_compile.compile(sys.argv[1], doraise=True); print('OK')"


def _run(cmd, cwd):
    import subprocess

    # 원본: subprocess.run(..., text=True) - 부모(원본 프로세스) 의 기본 인코딩으로 자식 출력을 읽는다
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, shell=False)
    enc = py_child_encoding()
    return (p.returncode, p.stdout.decode(enc, "replace").replace("\r\n", "\n").strip(),
            p.stderr.decode(enc, "replace").replace("\r\n", "\n").strip())


def _emit(obj) -> Result:
    text = json.dumps(obj, ensure_ascii=False)
    # 원본 sys.stdout.reconfigure(encoding="utf-8", errors="replace") - 깨진 글자(서로게이트) 는 ? 로
    return Result(0, text.encode("utf-8", "replace").decode("utf-8"), "")


def run(ctx):
    try:
        payload = json.loads(py_stdin_text(ctx))
    except Exception:
        return None
    try:
        ti = payload.get("tool_input", {}) or {}
        file_path = ti.get("file_path") or ""
        if not isinstance(file_path, str):
            return None
        if not file_path.endswith(".py"):
            return None
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        abs_path = file_path
        if not os.path.isabs(abs_path):
            abs_path = os.path.normpath(os.path.join(project_dir, file_path))

        lines = []
        err = ""
        try:
            py_compile.compile(abs_path, doraise=True)
            rc = 0
        except Exception:
            rc, _o, err = _run([sys.executable, "-c", _CODE, abs_path], cwd=project_dir)
            if rc == 0:
                err = ""
        if rc == 0:
            lines.append(f"[OK] py_compile OK: {file_path}")
        else:
            lines.append(f"[FAIL] py_compile FAIL: {file_path}")
            if err:
                lines.append(err)

        core_prefixes = ("engine" + os.sep, "storage" + os.sep, "web" + os.sep, "tools" + os.sep, "app" + os.sep)
        rel_norm = os.path.normpath(file_path)
        if rel_norm.startswith(core_prefixes):
            qt = os.path.join(project_dir, "tools", "run_quick_tests.py")
            if os.path.exists(qt):
                rc2, out2, err2 = _run([sys.executable, qt], cwd=project_dir)
                if rc2 == 0:
                    lines.append("[OK] quick_tests OK")
                else:
                    lines.append("[FAIL] quick_tests FAIL")
                    if out2:
                        lines.append(out2[-1200:])
                    if err2:
                        lines.append(err2[-1200:])
        return _emit({"systemMessage": "\n".join(lines).strip()})
    except Exception as e:
        return _emit({"systemMessage": f"Hook error: {e}"})
