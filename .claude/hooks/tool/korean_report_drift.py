"""PostToolUse '.*' — 턴 중간 영어 보고를 다음 보고 전에 바로잡는다 (STD-KOREAN-001 · §83).

실측 (2026-11-11): 설정 language=Korean 이후에도 메인 보고 21건 중 13건이 영어였고 전부 «도구 결과 직후» 의
중간 진행 보고였다 (사용자 입력·Stop 지적 직후는 0건). Stop 훅은 턴 끝에만 보므로 이미 나간 영어를 못 막는다.
→ 도구 실행 직후, 이번 턴의 가장 최근 보고가 영어면 한 줄 안내를 넣는다 (같은 보고엔 1회만 · 한국어면 출력 없음).
판정 함수는 standing-requirements.py 정본(_hangul_ratio·_turn_assistant_texts)을 재사용한다.
"""
from __future__ import annotations

import importlib.util
import json
import os

from _common import Result

_MOD = None


def _std():
    global _MOD
    if _MOD is None:
        root = os.environ.get("CLAUDE_PROJECT_DIR", "")
        spec = importlib.util.spec_from_file_location(
            "_std_req_drift", os.path.join(root, ".claude", "scripts", "standing-requirements.py"))
        _MOD = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_MOD)
    return _MOD


def run(ctx):
    try:
        data = json.loads(ctx.raw or "{}")
    except Exception:
        return None
    tp = data.get("transcript_path") or ""
    if not tp:
        return None
    m = _std()
    items = m._turn_assistant_texts(tp)
    if not items:
        return None
    last = items[-1]
    ratio, n = m._hangul_ratio(last["text"])
    if n < m.LANG_MIN_LETTERS or ratio >= m.LANG_MIN_HANGUL:
        return None
    root = os.environ.get("CLAUDE_PROJECT_DIR", "")
    sf = os.path.join(root, ".claude", "state", "lang-drift.json")
    sid = str(data.get("session_id") or "nosession")
    try:
        with open(sf, "r", encoding="utf-8") as f:
            st = json.load(f)
    except Exception:
        st = {}
    if last.get("uuid") and st.get(sid) == last["uuid"]:
        return None                                   # 같은 보고에는 1회만
    st[sid] = last.get("uuid")
    try:
        with open(sf, "w", encoding="utf-8") as f:
            json.dump(st, f)
    except Exception:
        pass
    msg = (f"[STD-KOREAN-001] 방금 보고가 영어였습니다 (한글 비율 {ratio:.0%}). 다음 보고부터 진행 보고·표·짧은 한 줄까지 "
           "한국어로 쓰세요. 도구 출력·코드가 영어여도 사용자 보고는 한국어 (식별자·명령·경로·원문 오류만 원문).")
    return Result(0, json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}},
                                ensure_ascii=False), "")
