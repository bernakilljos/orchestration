"""hook-09-ocr-verify.sh 이식 - 산출물 빌드/렌더 스크립트 실행 후 OCR/fit/여백 자동 검증 (systemMessage).

빌드 명령이 아니면 즉시 통과 (대부분의 Bash 호출). 해당될 때만 (검증 스크립트 다수 실행) 원본에 위임한다.
"""
from __future__ import annotations

import re

from _common import Spawn, bash_field, bash_read

_BUILD = re.compile(
    r"(build|generate|render)-[a-z-]+-(ppt|pptx|doc|diagrams|pdf|html)\.py|build-[a-z-]+-doc\.py|render-[a-z-]+\.py")


def run(ctx):
    inp = bash_read(ctx.raw)
    if "build-" not in inp and "generate-" not in inp and "render-" not in inp:
        return None
    cmd = bash_field(inp, "command")
    if not _BUILD.search(cmd):
        return None
    return Spawn(".claude/hooks/hook-09-ocr-verify.sh")
