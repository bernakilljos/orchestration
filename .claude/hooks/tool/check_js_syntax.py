"""check-js-syntax.sh 이식 - JS/TS 편집 후 문법 검사 (node --check / esbuild / tsc 외부 도구 필요).

대상 확장자 파일이 아니면 즉시 통과. 해당될 때만 원본 스크립트에 위임한다.
"""
from __future__ import annotations

import os

from _common import Spawn, bash_cat, glob_any, grep_key_value_a, has_jq

REL = ".claude/hooks/check-js-syntax.sh"


#: 2026-11-15 (R256): 편집 직후 검사가 py(post_write_pycheck)·js/ts/vue(이 훅) 뿐이라 실제 개발 프로젝트(IFRS)에서 가장 많이
#:   바뀌는 Java 와 xml·yml·json·ps1·sh 는 문법 오류를 편집 때 돌려받지 못했다. 새 훅을 만들지 않고 커밋 게이트와 같은 검사기
#:   (independent_verifier.staged_syntax_check) 를 그대로 불러 오류면 decision block 으로 Claude 에게 되돌린다.
_OTHER = ("*.java", "*.xml", "*.yml", "*.yaml", "*.json", "*.ps1", "*.psm1", "*.sh", "*.go")


def _other_syntax(ctx, fp: str):
    import importlib.util
    import json
    from pathlib import Path

    from _common import Result
    proj = Path(ctx.project_dir)
    try:
        rel = os.path.relpath(fp, str(proj))
        base = proj if not rel.startswith("..") else Path(fp).parent
        rel = rel if base == proj else os.path.basename(fp)
        spec = importlib.util.spec_from_file_location(
            "_iv_edit_syntax", str(proj / ".claude" / "scripts" / "lib" / "independent_verifier.py"))
        iv = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(iv)
        r = iv.staged_syntax_check(base, [rel.replace("\\", "/")])
    except Exception:  # noqa: BLE001 — 검사기 문제로 편집을 막지 않는다 (커밋 게이트가 다시 검사)
        return None
    if not r["errors"]:
        return None
    msg = "[FAIL] 문법 오류: %s\n%s" % (rel, "\n".join(e["error"] for e in r["errors"])[:2500])
    return Result(0, json.dumps({"decision": "block", "systemMessage": msg,
                                 "reason": msg + "\n\n이 파일을 고친 뒤 같은 검사를 다시 통과시키고 나서 완료로 보고한다."},
                                ensure_ascii=False), "")


def run(ctx):
    fp0 = grep_key_value_a(bash_cat(ctx.raw), "file_path")
    if fp0 and glob_any(fp0, *_OTHER) and os.path.isfile(fp0):
        return _other_syntax(ctx, fp0)
    if has_jq():
        return Spawn(REL)
    fp = grep_key_value_a(bash_cat(ctx.raw), "file_path")
    if not os.path.isfile(fp):
        return None
    if glob_any(fp, "*.js", "*.mjs", "*.cjs", "*.jsx", "*.ts", "*.tsx", "*.vue"):   # .vue 2026-11-13 R249
        return Spawn(REL)
    return None
