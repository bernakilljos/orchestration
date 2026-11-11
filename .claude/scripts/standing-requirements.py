#!/usr/bin/env python
"""
standing-requirements.py — Persistent Requirement Registry (SoT).

근거: 2026-10-16 사용자 지적 "저장 ≠ 재주입" — conversation 저장만으로는 다음 세션 반영 X.

구조:
- 지속 요구사항 (STANDING_REQUIREMENT): 앞으로 매 세션 자동 적용 (statusline 라인·디자인 규칙 등)
- 일회성 (CURRENT_TASK): 이번 요청만 (Request Ledger 로 관리)

CLI:
  python standing-requirements.py add <id> <type> <rule>   # 등록
  python standing-requirements.py list [--active]           # 조회
  python standing-requirements.py replay                    # SessionStart 용 systemMessage (JSON)
  python standing-requirements.py gate                      # Stop hook — ACTIVE 반영 여부 체크
  python standing-requirements.py resolve <id>              # ACTIVE → RESOLVED
  python standing-requirements.py disable <id>              # 임시 비활성

저장:
  .claude/state/standing-requirements.json
  {
    "UX-STATUS-007": {
      "type": "STANDING_REQUIREMENT",
      "status": "ACTIVE",
      "source": "USER_EXPLICIT",
      "rule": "품질추세 라인을 statusline 에 유지",
      "verify_pattern": "품질추세",
      "verify_target": ".claude/scripts/statusline_context.py",
      "created_at": "...",
      "last_verified_at": "..."
    }
  }
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
STORE = ROOT / ".claude" / "state" / "standing-requirements.json"


# 2026-11-09: 확정 개발 기준의 정본 = git 추적 파일 (이 스크립트 옆) — .claude/state 는 git·전파에서 빠져
#   다른 노트북·새 설치 프로젝트에 기준이 하나도 안 따라갔다. 기준은 로컬 기록에 없을 때 여기서 채운다
#   (로컬 status 변경은 유지 · 승인·예산 DB(orca.db)와 분리).
SEED = Path(__file__).resolve().parent / "standing-requirements.seed.json"


def _load() -> dict:
    data: dict = {}
    if STORE.exists():
        try:
            data = json.loads(STORE.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    try:
        seed = json.loads(SEED.read_text(encoding="utf-8")) if SEED.exists() else {}
    except Exception:
        seed = {}
    for rid, r in (seed.get("requirements") or {}).items():
        cur = data.get(rid)
        if cur is None or str(cur.get("version", "")) < str(r.get("version", "")):
            merged = dict(r)
            if cur is not None and cur.get("status") in ("RESOLVED", "DISABLED"):
                merged["status"] = cur["status"]    # 로컬에서 끈 기준은 유지 (새 버전이어도 임의 재활성 X)
            merged.setdefault("status", "ACTIVE")
            merged["source"] = "KIT_SEED v%s" % seed.get("version", "?")
            data[rid] = merged
    return data


def _save(data: dict) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_add(rid: str, rtype: str, rule: str, verify_pattern: str = "", verify_target: str = "") -> int:
    data = _load()
    data[rid] = {
        "type": rtype,
        "status": "ACTIVE",
        "source": "USER_EXPLICIT",
        "rule": rule,
        "verify_pattern": verify_pattern,
        "verify_target": verify_target,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "last_verified_at": None,
    }
    _save(data)
    print(f"[req] + {rid} [{rtype}] ACTIVE: {rule[:80]}")
    return 0


def cmd_list(active_only: bool = False) -> int:
    data = _load()
    if not data:
        print("[req] empty")
        return 0
    for rid, r in data.items():
        if active_only and r.get("status") != "ACTIVE":
            continue
        print(f"  [{r['status']}] {rid} ({r['type']}): {r['rule'][:100]}")
    return 0


def _effective_setting(key: str):
    """§84 Claude Code 공식 설정 우선순위로 실제 적용 값 — .claude/settings.local.json > .claude/settings.json >
    ~/.claude/settings.json (code.claude.com/docs/en/settings.md · Settings precedence). (값, 파일) · 없으면 (None, None)."""
    for p in (ROOT / ".claude" / "settings.local.json", ROOT / ".claude" / "settings.json",
              Path.home() / ".claude" / "settings.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict) and key in d:
            return d[key], str(p)
    return None, None


def _effective_setting_ok(r: dict) -> str:
    val, _src = _effective_setting(r.get("setting_key", ""))
    want = str(r.get("expect", ""))
    return "PASS" if val is not None and str(val).strip().lower() == want.strip().lower() else "FAIL"


def _verify(r: dict) -> "str":
    """verify_pattern 이 verify_target 안에 존재하는지.

    P0a-C: 2026-10-28 CRITICAL #3 fix.
    기존 verify_pattern 없으면 True 자동 반환 — gate 무력화 결함.
    이제 3-state 반환: 'PASS' / 'FAIL' / 'UNKNOWN'.
    UNKNOWN 은 gate 에서 PASS 로 간주 X · 수동 검증 요구 flag 로 처리.
    """
    if r.get("judge") == "human":
        return "HUMAN"
    if r.get("verify_kind") == "effective_setting":
        return _effective_setting_ok(r)    # 사람·독립 검토가 판단하는 기준 (2026-11-09) — 자동 PASS 로 세지 않고 차단 사유로도 쓰지 않는다
    tgt = r.get("verify_target", "")
    pat = r.get("verify_pattern", "")
    if not tgt or not pat:
        return "UNKNOWN"  # 검증 패턴 미제공 — 자동 True X · gate 가 수동 확인 요구
    p = ROOT / tgt
    if not p.exists():
        return "FAIL"
    try:
        return "PASS" if pat in p.read_text(encoding="utf-8", errors="ignore") else "FAIL"
    except Exception:
        return "FAIL"


def cmd_replay() -> int:
    """SessionStart hook 용. ACTIVE requirements 를 systemMessage JSON 으로 출력."""
    data = _load()
    active = [(rid, r) for rid, r in data.items() if r.get("status") == "ACTIVE"]
    if not active:
        return 0
    lines = ["# ACTIVE Standing Requirements (매 세션 재주입 · 작업 전 대조)"]
    lines.append("")
    for rid, r in active:
        tag = " · ".join(x for x in (r.get("grade"), ("v" + r["version"]) if r.get("version") else "",
                                     r.get("confirmed"), "사람 판단" if r.get("judge") == "human" else "") if x)
        lines.append(f"- **{rid}** ({r['type']}{' · ' + tag if tag else ''}): {r['rule']}")
    lines.append("")
    lines.append("**금지**: 이 중 하나라도 생략한 채 작업 완료 보고 X. Stop gate 가 재검사.")
    msg = "\n".join(lines)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": msg,
        }
    }, ensure_ascii=False))
    return 0


def _stop_hook_active() -> bool:
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return False
        raw = sys.stdin.read()
        return bool(json.loads(raw).get("stop_hook_active")) if raw.strip() else False
    except Exception:
        return False


def cmd_gate() -> int:
    """Stop hook 용. ACTIVE requirements 중 verify FAIL 있으면 exit 2."""
    data = _load()
    active = [(rid, r) for rid, r in data.items() if r.get("status") == "ACTIVE"]
    if not active:
        return 0
    failed = []
    unknown = []
    for rid, r in active:
        result = _verify(r)
        if result == "PASS":
            r["last_verified_at"] = datetime.now().isoformat(timespec="seconds")
        elif result == "FAIL":
            failed.append((rid, r))
        elif result == "HUMAN":
            continue
        else:  # UNKNOWN — verify_pattern 미제공 (P0a-C fix: 자동 True X)
            unknown.append((rid, r))
    _save(data)
    if not failed and not unknown:
        return 0
    msg = f"[standing-req] {len(active)-len(failed)-len(unknown)}/{len(active)} 유지"
    if failed:
        msg += f" · 누락 {len(failed)}건"
    if unknown:
        msg += f" · 미검증 {len(unknown)}건 (verify_pattern 미제공 · 수동 확인 요구)"
    msg += ":\n"
    for rid, r in failed[:5]:
        msg += f"  ✗ {rid}: {r['rule'][:80]}\n"
    for rid, r in unknown[:3]:
        msg += f"  ⏳ {rid} (UNKNOWN · verify_pattern 추가 필요): {r['rule'][:70]}\n"
    # 2026-11-05 재진입: 공식 문서 — stop_hook_active 를 확인해 풀리지 않는 조건으로 계속 막지 말 것.
    # 한 번은 막아 알리고, 이어서 또 멈출 때는 미해결인 채 종료를 허용한다 (요구사항 상태는 그대로).
    if _stop_hook_active():
        print(msg + "→ 이미 한 번 차단함 · 미해결 유지 · 이번 Stop 허용", file=sys.stderr)
        return 0
    msg += "→ ACTIVE standing requirement 복원 후 완료 (Stop 차단)"
    print(msg, file=sys.stderr)
    # FAIL 이 있거나 UNKNOWN 이 있어도 exit 2 (fail-closed)
    return 2


def cmd_resolve(rid: str) -> int:
    data = _load()
    if rid not in data:
        print(f"[req] {rid} not found", file=sys.stderr)
        return 2
    data[rid]["status"] = "RESOLVED"
    data[rid]["resolved_at"] = datetime.now().isoformat(timespec="seconds")
    _save(data)
    print(f"[req] ✓ {rid} RESOLVED")
    return 0


def cmd_disable(rid: str) -> int:
    data = _load()
    if rid not in data:
        print(f"[req] {rid} not found", file=sys.stderr)
        return 2
    data[rid]["status"] = "DISABLED"
    _save(data)
    print(f"[req] - {rid} DISABLED")
    return 0


def cmd_stats() -> dict:
    """§81 (2026-11-11): 종전엔 `not _verify(r)` 로 실패를 셌는데 _verify 는 'PASS'/'FAIL'/'UNKNOWN'/'HUMAN'
    문자열을 돌려줘 늘 참 → failed 0 · ok == active (항상 만점). 결과별로 따로 센다.
    ok = 자동 검증 PASS 만 · human = 사람 판단 기준(자동 PASS 아님) · unknown = 검증 패턴 없음."""
    data = _load()
    total = len(data)
    res = [_verify(r) for r in data.values() if r.get("status") == "ACTIVE"]
    return {"total": total, "active": len(res), "ok": res.count("PASS"), "failed": res.count("FAIL"),
            "unknown": res.count("UNKNOWN"), "human": res.count("HUMAN")}


LANG_LOG = ROOT / ".claude" / "logs" / "language-violations.log"
LANG_MIN_LETTERS = 60      # 짧은 한 줄(명령·경로만 있는 답)은 판정하지 않는다
LANG_MIN_HANGUL = 0.30     # 글자(한글+영문) 중 한글 비율이 이보다 낮으면 영어 보고로 본다


def _hangul_ratio(text: str) -> "tuple[float, int]":
    import re as _re
    body = _re.sub(r"```.*?```", " ", text or "", flags=_re.S)          # 코드 블록 제외
    body = _re.sub(r"`[^`]*`", " ", body)                              # 인라인 식별자 제외
    body = _re.sub(r"(https?://|[A-Za-z]:\\|/)[^\s]*", " ", body)      # URL·경로 제외
    ko = len(_re.findall(r"[\uac00-\ud7a3]", body))
    en = len(_re.findall(r"[A-Za-z]", body))
    n = ko + en
    return ((ko / n) if n else 1.0), n


def _turn_assistant_texts(transcript: str) -> list:
    """이번 턴(마지막 사람 입력·Stop 지적 이후) 메인 스레드 보고 [{uuid, text}] — 중간 진행 보고 포함 · 서브에이전트 제외."""
    try:
        p = Path(transcript)
        with open(p, "rb") as f:
            f.seek(max(0, p.stat().st_size - 1048576))
            lines = f.read().decode("utf-8", "replace").splitlines()
    except Exception:
        return []
    out = []
    for ln in reversed(lines):
        try:
            e = json.loads(ln)
        except Exception:
            continue
        if e.get("isSidechain"):
            continue
        parts = (e.get("message") or {}).get("content")
        if e.get("type") == "user":
            if isinstance(parts, str) or any(isinstance(c, dict) and c.get("type") == "text" for c in (parts or [])):
                break                                  # 사람 입력 또는 Stop 훅 지적 = 이번 턴 시작
            continue                                   # tool_result 는 건너뜀
        if e.get("type") == "assistant":
            txt = "\n".join(c.get("text", "") for c in (parts or []) if isinstance(c, dict) and c.get("type") == "text")
            if txt.strip():
                out.append({"uuid": e.get("uuid"), "text": txt})
    return list(reversed(out))


LANG_STATE = ROOT / ".claude" / "state" / "lang-check.json"


def _lang_trace(status: str, error: str = "", evidence: str = "", detail=None) -> str:
    """§82 위반·정정 기록 = 기존 요청 추적(trace) · 현재 요청이 없으면 옛 로그 파일에 덧붙임 (지우지 않음)."""
    try:
        import importlib.util as _ilu
        _sp = _ilu.spec_from_file_location("_lang_trace_mod", str(Path(__file__).resolve().parent / "lib" / "trace.py"))
        _m = _ilu.module_from_spec(_sp)
        _sp.loader.exec_module(_m)
        where = _m.emit("policy", step="STD-KOREAN-001", status=status, error=error or None,
                        evidence=evidence or None, detail=detail)
        if where != "none":
            return where
    except Exception:
        pass
    try:
        LANG_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LANG_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"), "rule": "STD-KOREAN-001",
                                "status": status, "error": error, "evidence": evidence, "detail": detail},
                               ensure_ascii=False) + "\n")
        return "log"
    except Exception:
        return "none"


def cmd_lang_check() -> int:
    """§81·§82 Stop 훅: 사용자에게 보인 보고 중 «아직 검사하지 않은 것»(증분)만 검사.
    영어가 있으면 1회 차단(한국어로 다시 보고) · stop_hook_active 면 기록만 · 이미 검사한 보고는 다시 세지 않음 ·
    차단 뒤 새 보고가 한국어면 «정정됨» 기록. 기록 = 요청 추적(trace) · 위반 이력은 지우지 않는다."""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        payload = {}
    sid = str(payload.get("session_id") or "nosession")
    try:
        state = json.loads(LANG_STATE.read_text(encoding="utf-8"))
    except Exception:
        state = {}
    mine = state.get(sid) or {}
    items = _turn_assistant_texts(payload.get("transcript_path") or "")
    seen = mine.get("last_uuid")
    if seen:
        pos = next((k for k, it in enumerate(items) if it.get("uuid") == seen), None)
        if pos is not None:
            items = items[pos + 1:]                    # 이미 검사한 보고는 건너뜀 (증분)
    if not items and payload.get("last_assistant_message") and not payload.get("transcript_path"):
        items = [{"uuid": None, "text": payload["last_assistant_message"]}]
    bad = []
    for it in items:
        ratio, n = _hangul_ratio(it["text"])
        if n >= LANG_MIN_LETTERS and ratio < LANG_MIN_HANGUL:
            bad.append((it, ratio, n))
    was_pending = bool(mine.get("pending"))
    if items and items[-1].get("uuid"):
        mine["last_uuid"] = items[-1]["uuid"]
    if items:                                          # 새 보고가 없으면 미정정 상태를 그대로 둔다
        mine["pending"] = bool(bad)
    mine["checked_at"] = datetime.now().isoformat(timespec="seconds")
    state[sid] = mine
    try:
        LANG_STATE.parent.mkdir(parents=True, exist_ok=True)
        LANG_STATE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    if not bad:
        if was_pending and items:
            _lang_trace("success", evidence=f"차단 뒤 보고 {len(items)}건 한국어로 정정됨")
        return 0
    it, ratio, n = bad[-1]
    _lang_trace("fail", error=f"영어 보고 {len(bad)}건 (마지막 한글 비율 {ratio:.0%})",
                detail={"session": sid, "letters": n, "head": it["text"].strip()[:120],
                        "blocked": not payload.get("stop_hook_active")})
    if payload.get("stop_hook_active"):
        return 0
    print(f"[STD-KOREAN-001] 새 보고 {len(bad)}건이 영어입니다 (마지막 한글 비율 {ratio:.0%}) — 같은 내용을 한국어로 다시 보고하세요 "
          "(식별자·명령·경로·원문 오류만 원문 유지 · 백그라운드 Agent 결과도 한국어로 옮겨 보고).", file=sys.stderr)
    return 2


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="op")
    p_add = sub.add_parser("add")
    p_add.add_argument("rid")
    p_add.add_argument("rtype", choices=["STANDING_REQUIREMENT", "CURRENT_TASK", "PREFERENCE"])
    p_add.add_argument("rule")
    p_add.add_argument("--verify-pattern", default="")
    p_add.add_argument("--verify-target", default="")
    p_list = sub.add_parser("list")
    p_list.add_argument("--active", action="store_true")
    sub.add_parser("replay")
    sub.add_parser("gate")
    sub.add_parser("stats")
    sub.add_parser("lang-check")
    p_res = sub.add_parser("resolve")
    p_res.add_argument("rid")
    p_dis = sub.add_parser("disable")
    p_dis.add_argument("rid")
    args = ap.parse_args()
    if args.op == "add":
        return cmd_add(args.rid, args.rtype, args.rule, args.verify_pattern, args.verify_target)
    if args.op == "list":
        return cmd_list(args.active)
    if args.op == "replay":
        return cmd_replay()
    if args.op == "gate":
        return cmd_gate()
    if args.op == "lang-check":
        return cmd_lang_check()
    if args.op == "stats":
        print(json.dumps(cmd_stats(), ensure_ascii=False))
        return 0
    if args.op == "resolve":
        return cmd_resolve(args.rid)
    if args.op == "disable":
        return cmd_disable(args.rid)
    ap.print_help()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[standing-req] fatal: {e}", file=sys.stderr)
        sys.exit(0)
