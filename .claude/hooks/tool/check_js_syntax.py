"""check-js-syntax.sh 이식 - JS/TS 편집 후 문법 검사 (node --check / esbuild / tsc 외부 도구 필요).

대상 확장자 파일이 아니면 즉시 통과. 해당될 때만 원본 스크립트에 위임한다.
"""
from __future__ import annotations

import os

from _common import Spawn, bash_cat, glob_any, grep_key_value_a, has_jq

REL = ".claude/hooks/check-js-syntax.sh"


def run(ctx):
    if has_jq():
        return Spawn(REL)
    fp = grep_key_value_a(bash_cat(ctx.raw), "file_path")
    if not os.path.isfile(fp):
        return None
    if glob_any(fp, "*.js", "*.mjs", "*.cjs", "*.jsx", "*.ts", "*.tsx"):
        return Spawn(REL)
    return None
