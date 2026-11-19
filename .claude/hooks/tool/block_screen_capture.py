"""화면 전체 캡처 차단 (2026-11-05) — 자동 검증이 승인되지 않은 업무 화면을 수집하지 않게 한다.

사례: Statusline 확인용 캡처에 사용자 Excel 업무 문서가 찍혔다. 화면에 무엇이 떠 있는지는 찍기 전에 알 수 없다.
Bash·PowerShell 명령 안의 화면 캡처 호출을 막는다. Playwright 페이지 캡처는 대상이 정해져 있어 해당 없음.
우회: 사용자가 대상 창을 지정해 승인한 경우에만 명령에 ALLOW_SCREEN_CAPTURE=1 (screen-verify.md).

2026-11-19 R320 사용자 결정: "개발하는데 너무 불편해 · 이거 나만 쓸 건데" → 기본은 허용 (개인 PC 1대 전용 · project_personal_use_scope).
다시 막으려면 .claude/state/screen-capture.block 파일을 만든다 (golden-test.block-on-fail 과 같은 켜기 방식) — 그때만 아래 차단이 동작.
"""
from __future__ import annotations

import os
import re

from _common import Result, project_path, tool_input

_CAPTURE = re.compile(
    r"CopyFromScreen|ImageGrab\.grab|pyautogui\.screenshot|mss\.mss\(|\bmss\(\)\.|savescreenshot|\bscreencapture\b",
    re.I,
)
_READ_ONLY = re.compile(r"\s*(grep|rg|git|cat|sed|head|tail|ls|Select-String)\b", re.I)


def run(ctx):
    if not os.path.isfile(project_path(ctx, ".claude", "state", "screen-capture.block")):
        return None                       # 기본 허용 (R320) — 켜기 파일이 있을 때만 차단
    cmd = str(tool_input(ctx).get("command") or "")
    if "ALLOW_SCREEN_CAPTURE=1" in cmd or _READ_ONLY.match(cmd) or not _CAPTURE.search(cmd):
        return None
    return Result(2, "", "BLOCKED(화면 캡처): 승인되지 않은 화면 수집 금지 — 다른 업무 화면이 찍힐 수 있다.\n"
                         "  → 창 하나만 캡처 (R322 · 겹친 다른 창 안 섞임): powershell -NoProfile -ExecutionPolicy Bypass -File "
                         ".claude\\scripts\\capture-window.ps1 -Title \"Visual Studio Code\" -Out <경로.png>\n"
                         "  → 웹 화면은 Playwright 페이지 캡처 · 그 외는 사용자에게 대상 창 지정·승인을 받는다\n"
                         "  → 다른 업무 화면이 찍히면 분석하지 말고 즉시 삭제 (screen-verify.md)\n")
