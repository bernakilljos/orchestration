"""상태줄의 «[!] 오류 N · 경고 M» 을 세션이 스스로 처리하게 — 새 오류가 생기면 다음 프롬프트에 1회 주입.

근거 2026-10-16: 상태줄에 «오류 73 (orca-10min-loop.log) · 경고 71» 이 사흘간 떠 있었는데
아무 세션도 손대지 않았다 (사용자 «이렇게 나오면 확인하고 해결해줘야지»). 숫자는 상태줄에만 있고
세션 컨텍스트에는 없어서 Claude 가 볼 방법이 없었다.

규칙 (상태줄 recent_log_issues 와 같은 기준 · 시각 있는 줄만 · 최근 24h):
  - 오류: 새 종류(파일+메시지 지문)가 생기면 주입
  - 경고: 같은 종류가 24h 에 20건 넘게 반복되면 주입 (일회성 경고는 잡음)
  - 이미 알린 종류는 건수가 2배 이상 늘고 6시간 지났을 때만 다시 알린다
상태: .claude/state/log-errors-seen.json
해소 표시 (R354 4차 검토 P2): 같은 로그에서 나중에 «[RESOLVED] <문구>» 줄이 나오면, 그보다 앞서 기록된 «<문구>» 포함 오류는 주입하지 않는다.
  (복구가 끝난 오류를 다음 세션에 다시 알리던 문제 · 문구가 다른 오류와 해소 뒤 재발한 오류는 그대로 알림)
  R354 7차: 표시에 «(ref=<상관 ID>)» 가 있으면 같은 ID 오류만 해소 · ID 없는 옛 표시는 «[ERROR] <문구>» 로 시작하는 오류가 한 종류일 때만
  R354 8차: ref 는 완전 일치로 비교 · ref 가 다르면 (숫자만 달라도) 다른 오류로 센다
  R354 9차: ref 가 같아도 «[ERROR] <해소 문구>» 로 시작하는 오류만 해소 (같은 ref 를 공유한 다른 오류는 알림)
"""
from __future__ import annotations

import glob
import json
import os
import re
import time

from _common import is_loop_prompt_raw, project_path

SKIP = {"bash_commands.log", "lookup-history.log", "user-prompt-history.log", "conversation-save.log",
        "deflection-detect.log", "emotion-response.log", "mcp-health.log", "prompt-dispatch.log", "hook-trace.log",
        "tool-dispatch.log"}
TS_RE = re.compile(r"(20\d\d)-(\d\d)-(\d\d)[ T](\d\d):(\d\d):(\d\d)")
# 끝 경계 필수 (2026-11-10): 정리 기록의 파일 이름 "errors/error_2026….log" 가 ERROR 로 세어졌다 · FAILED·FAILURE 는 유지
ERR_RE = re.compile(r"(?<![A-Za-z0-9_])(ERROR|FAIL(?:ED|URE|S)?|Traceback|\[err\]|\[!!\])(?![A-Za-z0-9_])", re.I)
WARN_RE = re.compile(r"\b(WARN|\[skip\])", re.I)
RESOLVED_RE = re.compile(r"\[RESOLVED\]\s*(.+?)\s*(?:—|$)")
REF_RE = re.compile(r"\(ref=([\w-]{6,})\)")
WARN_REPEAT_MIN = 20       # BASIS: agreed(2026-10-16, 10분 주기 작업이 24h 에 144회 → 20회+ 반복이면 일회성이 아니다)
RENOTIFY_SEC = 6 * 3600    # BASIS: agreed(2026-10-16, 같은 오류를 매 프롬프트 넣으면 잡음 — 하루 4번 이내)


def _sig(line: str) -> str:
    """시각·숫자·경로 차이를 지운 메시지 지문 (같은 종류 오류를 한 줄로 묶는다)."""
    s = TS_RE.sub("", line)
    s = re.sub(r"\[[0-9T:.\-+ ]+\]", "", s)
    s = re.sub(r"\d+", "#", s)
    return " ".join(s.split())[:120]


def _tail_lines(path: str, n: int) -> list:
    """파일 끝 n 줄만 (R317 실측: 매 프롬프트 3.6MB·3.4MB 로그를 통째 readlines 해 스캔 85ms — 끝에서부터 블록을 늘려 읽는다).
    결과는 readlines()[-n:] 와 같다 (줄바꿈 포함 · 마지막 줄 줄바꿈 없어도 동일)."""
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        block = 64 * 1024
        while True:
            start = max(0, size - block)
            f.seek(start)
            data = f.read(size - start)
            if start == 0 or data.count(b"\n") > n:
                break
            block *= 4
    lines = data.decode("utf-8", errors="replace").splitlines(keepends=True)
    if start > 0:
        lines = lines[1:]          # 블록 첫 줄은 중간에서 잘린 줄
    return lines[-n:]


def _scan(log_dir: str):
    cutoff = time.time() - 86400
    found: dict[str, dict] = {}
    for lp in glob.glob(os.path.join(log_dir, "*.log")):
        name = os.path.basename(lp)
        if name in SKIP:
            continue
        try:
            if os.path.getmtime(lp) < cutoff:
                continue
            lines = _tail_lines(lp, 500)
        except OSError:
            continue
        resolved = []                      # (줄 순서, 해소 문구)
        last_at: dict = {}                 # 오류 key → 이 파일에서 마지막으로 나온 줄 순서
        for idx, ln in enumerate(lines):
            rm = RESOLVED_RE.search(ln)
            if rm:
                phrase = rm.group(1).strip()
                # R354 5차 검토 P2: 짧거나 오류 단어뿐인 문구(«[RESOLVED] ERROR»)는 다른 미해소 오류까지 숨긴다 → 무시
                if len(phrase) >= 8 and not ERR_RE.fullmatch(phrase):
                    resolved.append((idx, phrase))
                continue
            e, w = ERR_RE.search(ln), WARN_RE.search(ln)
            if not (e or w):
                continue
            m = TS_RE.search(ln)
            if not m or time.mktime(tuple(map(int, m.groups())) + (0, 0, -1)) < cutoff:
                continue
            # R354 8차 검토 P2: _sig 가 숫자를 지워 숫자만 다른 ref 오류가 한 key 로 합쳐졌다 → ref 를 key 에 넣어 따로 센다
            em = REF_RE.search(ln)
            eref = em.group(1) if em else ""
            key = name + " | " + _sig(ln) + (f" | ref={eref}" if eref else "")
            d = found.setdefault(key, {"kind": "ERROR" if e else "WARN", "n": 0, "file": name, "sample": "", "ref": eref})
            d["n"] += 1
            d["sample"] = ln.strip()[:200]
            last_at[key] = idx
        drop = set()
        for r_idx, phrase in resolved:
            ref = REF_RE.search(phrase)
            before = [k for k, idx in last_at.items() if idx < r_idx]
            if ref:
                # R354 7차 검토 P2: 상관 ID 가 있으면 그 ID 를 가진 오류만 (같은 접두어·다른 원인 오류는 그대로 알림)
                # R354 8차: 부분 문자열(aaaa1111 ⊂ aaaa1111-extra) 아니라 완전 일치
                # R354 9차: 같은 ref 를 공유한 다른 오류는 남긴다 → «[ERROR] <해소 문구>» 로 시작하는 것만
                head = re.compile(r"\[ERROR\]\s*" + re.escape(phrase), re.I)
                drop.update(k for k in before if found[k]["ref"] == ref.group(1) and head.search(found[k]["sample"]))
                continue
            # 옛 형식 (ID 없음): «[ERROR] <문구>» 로 시작하는 오류만 (R354 6차) · 그런 오류 종류가 둘 이상이면 어느 것인지 모르므로 숨기지 않음
            hits = [k for k in before if re.search(r"\[ERROR\]\s*" + re.escape(phrase), found[k]["sample"], re.I)]
            if len(hits) == 1:
                drop.update(hits)
        for key in drop:
            found.pop(key, None)
    return found


def run(ctx):
    if is_loop_prompt_raw(ctx.raw_stripped):
        return None
    log_dir = project_path(ctx, ".claude", "logs")
    if not os.path.isdir(log_dir):
        return None
    found = _scan(log_dir)
    if not found:
        return None
    seen_p = project_path(ctx, ".claude", "state", "log-errors-seen.json")
    try:
        with open(seen_p, "r", encoding="utf-8") as f:
            seen = json.load(f)
    except Exception:
        seen = {}
    now = time.time()
    hits = []
    for key, d in found.items():
        if d["kind"] == "WARN" and d["n"] < WARN_REPEAT_MIN:
            continue
        prev = seen.get(key)
        if prev and not (d["n"] >= 2 * prev.get("n", 1) and now - prev.get("t", 0) > RENOTIFY_SEC):
            continue
        hits.append((key, d))
    if not hits:
        return None
    for key, d in hits:
        seen[key] = {"n": d["n"], "t": now}
    try:
        os.makedirs(os.path.dirname(seen_p), exist_ok=True)
        with open(seen_p, "w", encoding="utf-8") as f:
            json.dump({k: v for k, v in seen.items() if now - v.get("t", 0) < 7 * 86400}, f, ensure_ascii=False)
    except OSError:
        pass
    hits.sort(key=lambda kd: (kd[1]["kind"] != "ERROR", -kd[1]["n"]))
    rows = [f"  - {d['kind']} ×{d['n']} ({d['file']}) {d['sample']}" for _, d in hits[:6]]
    more = f"\n  … 외 {len(hits) - 6}종" if len(hits) > 6 else ""
    return {"additionalContext": (
        "[로그 오류 자동 점검 — 상태줄 «오류/경고» 의 원인] 최근 24h 새로 생기거나 반복되는 문제:\n"
        + "\n".join(rows) + more
        + "\n★ 사용자 작업을 처리하면서 이것도 원인을 확인해 고친다 (사용자가 말하기 전에 · D6). "
          "로그만 지우는 것은 해결이 아니다 — 실행해서 재발 0 을 확인하고 보고에 1줄.")}
