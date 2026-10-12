"""detect-deflection.sh 이식 — 회피·반복 지적 신호 (농땡이/짤려/안 보여/또) 감지 + 반복 누적 경고.

상태: .claude/logs/user-prompt-history.log (최근 30줄) · deflection-detect.log
"""
from __future__ import annotations

import os

from _common import append_text, bash_strip, read_lines, search, ts_local, write_text

MSG_WARN = "[WARN] 회피-반복 위반 패턴 감지: @MATCHED@ (최근 10 prompt 중 @COUNT@ 회). failure-mode.md § 회피 안티패턴 / feedback_nongttaengi_means_full_survey.md 점검. 사용자 직답 -> 부연 -> 행동 순서로. 5단계 전수조사 필수."
MSG_SIGNAL = "[SIGNAL] 사용자 신호 감지: @MATCHED@. 룰 위반 가능성. 단순 응답 X, 원인 점검 후 행동."
SIGNALS_DECL = [
    ("overflow_jal", "짤려|짤린|잘림|넘쳐|넘치"),
    ("text_too_small", "작은데|글씨.*안 ?보여|작아|크게"),
    ("whitespace", "빈 ?여백|공간.*많|허전"),
    ("repeat", "다시|또|반복|왜 자꾸|계속|왜이리"),
    ("nongttaengi", "농땡이|정신.*차|안되니|왜 안"),
    ("rule_violation", "룰.*위반|규칙.*어겨|전수조사|체크리스트"),
    ("wrong", "틀렸|잘못|아니야|아닌데|왜 그래"),
    ("no_show", "안 ?보여|안 ?나와|안 ?돼"),
]

# bash 연관배열 `${!SIGNALS[@]}` 순회 순서 (해시 순서 · 이 PC bash 5.2.37 실측).
# 출력 문구의 카테고리 나열 순서가 이 순서에 따라 달라지므로 그대로 고정한다.
ITER_ORDER = [
    "overflow_jal",
    "repeat",
    "rule_violation",
    "text_too_small",
    "wrong",
    "no_show",
    "nongttaengi",
    "whitespace",
]


def run(ctx):
    if not ctx.has_plugins():
        return None
    log_dir = os.path.join(ctx.project_dir, ".claude", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log = os.path.join(log_dir, "deflection-detect.log")
    history = os.path.join(log_dir, "user-prompt-history.log")

    if not ctx.raw_stripped:
        return None

    # 원본 (jq 경로): .prompt // .user_message // empty
    msg = ctx.payload.get("prompt") or ctx.payload.get("user_message") or ""
    if not isinstance(msg, str):
        msg = str(msg)
    msg = bash_strip(msg)
    if not msg:
        return None

    # 누적 prompt 기록 (30줄 회전) — 메시지에 개행이 있으면 여러 줄이 된다 (원본 동일)
    append_text(history, f"[{ts_local('%Y-%m-%d_%H:%M:%S')}] {msg}\n")
    lines = read_lines(history)
    if len(lines) > 30:
        write_text(history, "\n".join(lines[-30:]) + "\n")

    signals = dict(SIGNALS_DECL)
    matched = [c for c in ITER_ORDER if search(signals[c], msg)]
    if not matched:
        return None
    matched_s = "".join(" " + c for c in matched)  # 원본: 앞에 공백 붙여 이어붙임

    # 최근 10줄에서 같은 카테고리 반복 카운트
    recent = read_lines(history)[-10:]
    count = 0
    for c in matched:
        pat = signals[c]
        for ln in recent:
            if search(pat, ln):
                count += 1

    append_text(log, f"[{ts_local('%Y-%m-%d_%H:%M:%S')}] MATCHED:{matched_s} | recent_count={count} | msg={msg}\n")

    if count >= 3:
        return MSG_WARN.replace("@MATCHED@", matched_s).replace("@COUNT@", str(count))
    return MSG_SIGNAL.replace("@MATCHED@", matched_s)
