#!/usr/bin/env python
"""
resume-last-24h.py — 최근 24시간 작업 자동 복구 요약
SessionStart hook 가 호출 → stdout → systemMessage 로 주입

출력 포함:
- 최근 24h session_summary (어제·오늘)
- 미완료 task (.claude/tasks pending·in_progress)
- 최근 24h git commit
- 마지막 user 지시 3개 (대화 복원)
- session-snapshot.md 안 최종 상태

사용자 설명 요구 X · 재부팅·메모리 종료 복구 자동.
"""
from __future__ import annotations
import time
import os
# 협업 미처리는 세션 시작 때 원격을 직접 보지 않고 마지막 확인 결과(ai-collab-pending.json)만 읽는다.
#   11-26 바로잡기는 fetch+ls-remote 만 남은 시간 안에 넣었지만 그 뒤 응답 계약 확인(git·map 호출 ~30회)은 무제한이라
#   11-27 00:36 에 또 10.9초로 출력이 버려졌다(단독 4.3~5.6초 · 95% 가 pending_lines 의 네트워크·git).
#   결과가 _COLLAB_MAX_AGE_S 보다 오래됐으면 백그라운드 갱신만 띄운다(기다리지 않음 · OS 잠금으로 1개만).
_COLLAB_MAX_AGE_S = 900.0


def _collab_cached(ac, spawn=None) -> list:
    """마지막 확인 결과의 미처리 줄 + 확인 시점·실패 표시 (네트워크·git 호출 0)."""
    from datetime import datetime as _dt, timezone as _tz
    cache = ac._load(ac.PENDING_CACHE, {})
    cache = cache if isinstance(cache, dict) else {}
    lines = cache.get("lines") if isinstance(cache.get("lines"), list) else None
    try:
        age = (_dt.now(_tz.utc) - _dt.fromisoformat(cache.get("at", ""))).total_seconds()
    except (ValueError, TypeError, AttributeError):
        age = float("inf")
    if lines is None or age == float("inf") or age < -ac._FUTURE_SKEW:
        ac._spawn_refresh(spawn)
        return ["(협업 확인 기록 없음·손상 = 최신 여부 UNKNOWN · 백그라운드 확인 시작 · "
                "`python -X utf8 .claude/scripts/ai-collab-report.py pending` 로 직접 확인)"]
    notes = []
    if age > _COLLAB_MAX_AGE_S:
        ac._spawn_refresh(spawn)
        notes.append(f"({int(age // 60)}분 전 확인 결과 · 백그라운드 갱신 시작)")
    if not cache.get("ok", True):
        notes.append("(마지막 원격 확인 실패 = 최신 여부 UNKNOWN)")
    return (notes + lines) if (lines or not cache.get("ok", True)) else []
import json, os, re, sqlite3, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / ".claude" / "state" / "orca.db"
TASKS = ROOT / ".claude" / "tasks"
SNAPSHOT = ROOT / ".claude" / "context-cache" / "session-snapshot.md"

CUTOFF_HOURS = 24
MAX_CHARS = 3000  # systemMessage 폭주 방지

def _h(title: str) -> str:
    return f"\n## {title}\n"

def section_session_summary() -> str:
    if not DB.exists(): return ""
    cutoff = (datetime.now() - timedelta(hours=CUTOFF_HOURS)).isoformat()
    try:
        c = sqlite3.connect(DB)
        rows = c.execute(
            "SELECT session_id, ended_at, turns, summary, key_decisions "
            "FROM session_summary WHERE updated_at >= ? AND turns > 0 "
            "ORDER BY updated_at DESC LIMIT 5",
            (cutoff,)
        ).fetchall()
    except Exception:
        return ""
    if not rows: return ""
    out = [_h(f"최근 {CUTOFF_HOURS}h 세션 요약")]
    for sid, ended, turns, summ, dec in rows:
        s = (summ or "")[:400]
        d = (dec or "")[:200]
        out.append(f"- **[{sid[:8]}]** turns={turns} · ended={ended or '진행중'}")
        if s: out.append(f"  summary: {s}")
        if d: out.append(f"  decisions: {d}")
    return "\n".join(out)

def section_pending_tasks() -> str:
    if not TASKS.exists(): return ""
    pending = []
    for d in ("pending", "in_progress", "locks"):
        p = TASKS / d
        if p.is_dir():
            for f in sorted(p.glob("*.md"))[:5]:
                try:
                    first = f.read_text(encoding="utf-8", errors="replace").splitlines()[0][:80]
                except Exception:
                    first = "?"
                pending.append(f"  - [{d}] {f.name} — {first}")
    if not pending: return ""
    return _h(f"미완료 task") + "\n".join(pending)

def section_recent_commits() -> str:
    try:
        r = subprocess.run(
            ["git", "-C", str(ROOT), "log", f"--since={CUTOFF_HOURS} hours ago",
             "--oneline", "-10"],
            capture_output=True, text=True, encoding="utf-8", timeout=5
        )
        lines = (r.stdout or "").strip().splitlines()
    except Exception:
        return ""
    if not lines: return ""
    return _h(f"최근 {CUTOFF_HOURS}h commit") + "\n".join(f"  - {ln}" for ln in lines[:10])

def section_last_prompts() -> str:
    if not DB.exists(): return ""
    try:
        c = sqlite3.connect(DB)
        rows = c.execute(
            "SELECT content, ts FROM conversations WHERE role='user' "
            "ORDER BY ts DESC LIMIT 3"
        ).fetchall()
    except Exception:
        return ""
    if not rows: return ""
    out = [_h("마지막 사용자 지시 3개 (최신→과거)")]
    for txt, ts in rows:
        snip = (txt or "")[:150].replace("\n", " ")
        out.append(f"  - [{ts}] {snip}")
    return "\n".join(out)

def section_snapshot() -> str:
    if not SNAPSHOT.exists(): return ""
    try:
        txt = SNAPSHOT.read_text(encoding="utf-8", errors="replace")[:600]
    except Exception:
        return ""
    if not txt.strip(): return ""
    return _h("최종 세션 스냅샷") + txt

def _sanitize(s: str) -> str:
    """unpaired surrogate 제거 (orca.db 안 cp949↔utf-8 변환 잔재) — Claude API lone surrogate 400 방지"""
    if not isinstance(s, str): return s
    return s.encode("utf-8", "replace").decode("utf-8", "replace")

def section_current_trace() -> str:
    """§78 compact·재시작 뒤 진행 중 요청의 추적번호·최근 단계·실패를 복원 (기록에 없는 것은 만들지 않음)."""
    try:
        import importlib.util as _ilu
        sp = _ilu.spec_from_file_location("_resume_trace", Path(__file__).resolve().parent / "lib" / "trace.py")
        tm = _ilu.module_from_spec(sp)
        sp.loader.exec_module(tm)
        cur = tm.get_current()
        if not cur:
            return ""
        evs = tm.events(cur["trace_id"])
        lines = [f"- 추적번호 {cur['trace_id']} ({cur.get('rid', '')}) · {cur.get('desc', '')[:100]}",
                 f"- 조회: `python .claude/scripts/lib/trace.py show {cur['trace_id']}` · 이벤트 {len(evs)}건"]
        for e in [e for e in evs if e.get("status") not in ("success", "info")][-5:]:
            lines.append("- " + tm._fmt(e))
        for ch in tm.chains(evs)[-3:]:
            lines.append(f"- 실패 {len(ch['failures'])}회 → {'대체 성공' if ch['success'] else '아직 성공 기록 없음'} [{ch['kind']}:{ch['step']}]")
        if not any(e.get("kind") == "request" and e.get("status") not in ("start",) for e in evs):
            lines.append("- 종료 기록 없음 = 완료 여부 불명 (성공으로 보지 않음) · 아래 마지막 도구부터 상태 확인 후 이어서")
            risky = re.compile(r"git\s+push|git\s+commit|--apply|rm\s+-|Remove-Item|merge-to-target|DROP|DELETE", re.I)
            for e in [e for e in evs if e.get("kind") == "tool"][-3:]:
                mark = " ⚠ 비멱등 — 재실행 전 결과 확인 (git log·대상 상태)" if risky.search(e.get("detail") or "") else ""
                lines.append("- 마지막 도구: " + tm._fmt(e) + mark)
        return _h("진행 중 요청 추적 (§78)") + "\n".join(lines)
    except Exception:
        return ""


def main():
    parts = [
        section_current_trace(),
        section_session_summary(),
        section_pending_tasks(),
        section_recent_commits(),
        section_last_prompts(),
        section_snapshot(),
    ]
    body = "\n".join(p for p in parts if p).strip()
    # 2026-11-12 (R245): 이력이 비어 있으면(새 DB·다른 머신) next-actions 에 할 일이 있어도 아무것도 주입하지 않고
    #   끝났다 — 이어서 할 일이 있으면 본문이 없어도 진행한다.
    if not body and not (ROOT / ".claude" / "state" / "next-actions.md").is_file():
        return  # 복구할 거 없음
    body = _sanitize(body)[:MAX_CHARS]
    header = f"# 자동 복구 (최근 {CUTOFF_HOURS}h · resume-last-24h.py)\n"
    header += "재부팅·메모리 종료 전 작업 상태. 사용자 설명 요구 X · 바로 이어서.\n"
    # 2026-10-14 — compact·clear 직후 새 세션이 «무엇을 이어서 할지» 몰라 사용자에게 다시 물었다
    #   (요약은 최근 프롬프트 나열뿐). 세션이 남긴 «다음에 할 일» 을 맨 위에 «바로 시작» 으로 붙인다.
    # 2026-11-09: 정본 writer(auto-save-next-actions.py) 로 읽는다 — 수동 지시는 나이 무관 항상 ·
    #   자동 블록은 CUTOFF 안일 때만 · 인코딩이 섞여도 읽는다 (종전: strict utf-8 실패 → 조용히 주입 0)
    try:
        import importlib.util as _ilu
        _sp = _ilu.spec_from_file_location("_next_actions", Path(__file__).resolve().parent / "auto-save-next-actions.py")
        _nam = _ilu.module_from_spec(_sp)
        _sp.loader.exec_module(_nam)
        _txt = _nam.resume_text(CUTOFF_HOURS * 3600).strip()
        if _txt:
            header += ("\n## ★ 이어서 할 일 — 사용자 첫 메시지가 무엇이든 확인 질문 없이 이것부터 바로 시작\n"
                       + _txt[:4000] + "\n(끝낸 자동 항목은 갱신 시 사라진다 · 수동 지시는 사용자 지시가 있을 때만 "
                       "`python .claude/scripts/auto-save-next-actions.py manual-clear`)\n\n")
    except Exception as _e:
        header += f"\n## ★ 이어서 할 일 읽기 실패 — .claude/state/next-actions.md 직접 확인 ({type(_e).__name__})\n\n"
    # R372: 새 세션이 ChatGPT 리뷰(changes_requested)·새 지시·공식 변경 알림을 못 읽고 «할 일 없음» 으로 답하던 것 →
    #   협업 폴더 미처리(git 이력 워터마크 · 읽기 전용)와 changelog-new 를 맨 위에 붙인다 (실행 중 0 ≠ 미완료 0)
    top = ""
    try:
        _sp2 = _ilu.spec_from_file_location("_ai_collab", Path(__file__).resolve().parent / "ai-collab-report.py")
        _ac = _ilu.module_from_spec(_sp2)
        _sp2.loader.exec_module(_ac)
        _pend = _collab_cached(_ac)
        if _pend:
            top += "\n## ★ 협업 폴더 미처리 (ChatGPT 지시·리뷰) — 먼저 읽고 실행\n" + "\n".join(_pend[:20]) + "\n"
        # R375 후속 (2026-11-24 사용자 "loop 로 읽게 하지 않았어?"): 대기 루프(wait)는 Bash 백그라운드라 세션이 바뀌면 꺼진다 —
        #   이 문구가 붙는 시점(새 세션·compact 복구)마다 다시 켜도록 지시 (새 리뷰가 오면 셸이 Claude 를 한 번 깨움 · 대기 중 모델 호출 0)
        top += ("\n## ★ 협업 대기 루프 — 첫 동작으로 Bash 백그라운드(run_in_background) 시작: "
                "`python -X utf8 .claude/scripts/ai-collab-report.py wait --interval 300` · 끝나면(새 리뷰·지시 도착) 처리 후 다시 시작\n")
    except Exception as _e:
        top += f"\n## ★ 협업 폴더 확인 실패 ({type(_e).__name__}) — `python .claude/scripts/ai-collab-report.py pending` 직접 실행\n"
    if (ROOT / ".claude" / "state" / "changelog-new.md").is_file():
        top += ("\n## ★ 공식 변경 알림 미처리 — `.claude/state/changelog-new.md` 와 `changelog-cache/` 의 새 내용(.prev 대비)을 읽고 "
                "영향 있는 것만 반영 후 알림 파일 삭제\n")
    header = header.replace("\n## ★ 이어서 할 일", top + "\n## ★ 이어서 할 일", 1) if top and "\n## ★ 이어서 할 일" in header else header + top
    # 사용자 지시 '--json' 시 SessionStart hook JSON 직접 반환 (shell escape 우회)
    if "--json" in sys.argv:
        import json as _j
        print(_j.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": _sanitize(header + body)
            }
        }, ensure_ascii=True))
    else:
        print(header + body)

if __name__ == "__main__":
    try: main()
    except Exception as e: print(f"[ERR] {e}", file=sys.stderr); sys.exit(0)
