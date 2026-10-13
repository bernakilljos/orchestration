#!/usr/bin/env python3
"""precommit-encoding-check — 커밋 직전 한글 깨짐·실행 불가 파일을 막는다.

2026-10-13 사고: 다른 PC 에이전트가 파일을 다시 저장하며 UTF-8 한글을 CP949 로 깨뜨려
(11c622f) 105개 파일이 커밋됐고 상태줄·프롬프트 hook 등 33개 python 이 실행 불가가 됐다.

검사 (staged 파일만 · staged 내용 기준):
  1. .py → ast.parse 실패면 차단
  2. 텍스트 파일 → CP949 오해석 흔적(아래 글자쌍) 이 HEAD 판보다 3개+ 늘면 차단
우회: 정말 의도한 경우만 `git commit --no-verify` (사용자 명시 시)
"""
import ast
import re
import subprocess
import sys

MOJI = re.compile(r"쨌|濡쒓|꾨줈|ъ슜|蹂묓빀|諛붿씠|罹먯떆|寃쎈줈|꾩삁|쒖쇅|ㅽ겕|좎씪")
TEXT_EXT = (".py", ".sh", ".md", ".txt", ".json", ".bat", ".yml", ".yaml", ".toml", ".ts", ".tsx", ".css", ".html")


def blob(spec: str) -> str | None:
    r = subprocess.run(["git", "show", spec], capture_output=True)
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None


def main() -> int:
    names = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "-z"],
                           capture_output=True).stdout.decode("utf-8", "replace").split("\0")
    bad = []
    for f in [n for n in names if n and n.endswith(TEXT_EXT)]:
        new = blob(f":{f}")
        if new is None:
            continue
        if f.endswith(".py"):
            try:
                ast.parse(new.lstrip("﻿"))
            except SyntaxError as e:
                bad.append(f"{f}: python 문법 오류 (줄 {e.lineno})")
                continue
        # 깨짐 검사 도구 자신은 패턴 글자를 담고 있어 흔적 비교에서 뺀다 (문법 검사는 받는다)
        if "mojibake" in f or f.endswith("precommit-encoding-check.py"):
            continue
        old = blob(f"HEAD:{f}") or ""
        grow = len(MOJI.findall(new)) - len(MOJI.findall(old))
        if grow >= 3:
            bad.append(f"{f}: 한글 깨짐 흔적 +{grow} (UTF-8 → CP949 오저장 의심)")
    if bad:
        print("[X] [git pre-commit] 깨진 파일 커밋 차단 — 원본 인코딩(UTF-8)으로 다시 저장하세요:")
        for b in bad[:30]:
            print("   -", b)
        if len(bad) > 30:
            print(f"   ... 외 {len(bad) - 30}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
