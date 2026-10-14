"""markdown_formatter.py 이식 - .md/.mdx 편집 후 코드펜스 언어 태그 · 연속 빈 줄 정리 (파일을 직접 고친다).

stdin 은 원본과 같은 방식(시스템 기본 인코딩) 으로 읽는다 - 한글이 든 경로면 원본은 파일을 못 찾아 아무것도 안 한다
(_common.py 의 PY_STDIN_FIX 설명 참고).
원본은 완료 메시지에 체크 문자(U+2713) 를 print 한다. 한국어 Windows 의 기본 콘솔 인코딩(cp949) 으로는
인코딩할 수 없어 UnicodeEncodeError -> "Error formatting markdown" + exit 1 이 된다 (파일은 이미 저장된 뒤).
같은 결과가 나오도록 원본 프로세스의 stdout 인코딩으로 인코딩을 시도해 그대로 재현한다.
"""
from __future__ import annotations

import json
import os
import re

from _common import Result, py_child_encoding, py_stdin_text


def detect_language(code):
    s = code.strip()
    if re.search(r"^\s*[{\[]", s):
        try:
            json.loads(s)
            return "json"
        except Exception:
            pass
    if re.search(r"^\s*def\s+\w+\s*\(", s, re.M) or re.search(r"^\s*(import|from)\s+\w+", s, re.M):
        return "python"
    if re.search(r"\b(function\s+\w+\s*\(|const\s+\w+\s*=)", s) or re.search(r"=>|console\.(log|error)", s):
        return "javascript"
    if re.search(r"^#!.*\b(bash|sh)\b", s, re.M) or re.search(r"\b(if|then|fi|for|in|do|done)\b", s):
        return "bash"
    if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE)\s+", s, re.I):
        return "sql"
    return "text"


def format_markdown(content):
    def add_lang_to_fence(match):
        indent, info, body, closing = match.groups()
        if not info.strip():
            lang = detect_language(body)
            return f"{indent}```{lang}\n{body}{closing}\n"
        return match.group(0)

    fence_pattern = r"(?ms)^([ \t]{0,3})```([^\n]*)\n(.*?)(\n\1```)\s*$"
    content = re.sub(fence_pattern, add_lang_to_fence, content)
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.rstrip() + "\n"


def run(ctx):
    try:
        input_data = json.loads(py_stdin_text(ctx))
        file_path = input_data.get("tool_input", {}).get("file_path", "")
        if not file_path.endswith((".md", ".mdx")):
            return None
        out = ""
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            formatted = format_markdown(content)
            if formatted != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(formatted)
                out = f"✓ Fixed markdown formatting in {file_path}\n"
                out.encode(py_child_encoding())  # 원본 print 의 인코딩 실패 재현
        return Result(0, out, "") if out else None
    except Exception as e:
        return Result(1, "", f"Error formatting markdown: {e}\n")
