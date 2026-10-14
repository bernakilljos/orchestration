"""enforce-file-naming.sh 이식 - 편집 파일을 orca.db.file_audit 에 기록 + 명명 위반 경고 (출력은 전부 file-audit.log).

원본은 python 을 2번(경로 추출 · audit_file_write.py) 띄웠다. 여기서는 audit_file_write.py 를 in-process 로 호출한다.
원본이 `>>"$LOG" 2>&1` 로 stdout/stderr 를 로그에 모으던 것도 그대로 모은다.
"""
from __future__ import annotations

import contextlib
import io
import json

from _common import append_text, ensure_dir, load_script, root_path


def run(ctx):
    log_dir = root_path(".claude", "logs")
    ensure_dir(log_dir)
    log = root_path(".claude", "logs", "file-audit.log")
    path = ""
    try:
        open(log, "ab").close()  # 원본은 경로 추출 python 에 2>>"$LOG" 가 있어 로그 파일이 (비어 있어도) 생긴다
    except OSError:
        pass
    try:
        d = json.loads(ctx.raw)
        ti = d.get("tool_input") or {}
        path = (d.get("tool_input") or {}).get("file_path") or (d.get("tool_input") or {}).get("path") or ""
        del ti
    except Exception as e:
        append_text(log, f"[parse] {e}\n")
    path = path.rstrip("\n")  # $(...) 는 끝의 개행을 지운다
    if not path:
        return None
    buf_out, buf_err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            mod = load_script("audit_file_write")
            if mod is not None:
                mod.log_action("write", path, "PostToolUse")
                for w in mod.check_name(path):
                    print(w, file=buf_err)
    except Exception as e:  # 원본: python 예외도 || true 로 삼킨다 (traceback 은 로그로)
        buf_err.write(f"{type(e).__name__}: {e}\n")
    text = buf_out.getvalue() + buf_err.getvalue()
    if text:
        append_text(log, text)
    return None
