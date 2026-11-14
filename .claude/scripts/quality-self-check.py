"""남은 필수 품질 검증 3건 자동 판정 (2026-11-13 R253 · 사용자 지시 "자동으로 확인할 수 있는 것은 시스템이 직접").

사람이 기록을 열어 보지 않아도 매 세션 Stop 때 이 세션의 실제 기록으로 판정해 남긴다 (새 계측 X · 기존 기록만 읽음):
  Q12 시작 속도  — 이 세션 대화 기록의 SessionStart:startup 훅 durationMs (병렬 → 대기 = 가장 늦은 훅) ≤ 5000ms
  Q11 한국어     — 이 세션 메인 보고 전부를 기존 판정(standing-requirements._hangul_ratio · 같은 기준값)으로 ·
                   영어 0건 + 교정(STD-KOREAN-001 fail) 0건 + 보고 10건 이상일 때만 PASS
  Q1  재부팅 재개 — 이 세션이 Windows 부팅 뒤 첫 세션일 때만 판정: ① 재개 목록 주입 ② 첫 요청에서 확인 질문 없이 도구 실행
                   ③ 부팅 뒤 같은 제목 커밋 반복 0 — 셋 다 증거가 있어야 PASS · 주입만 = PARTIAL
결과: .claude/state/quality-self-check.json (최신 판정 · 항목별 마지막 PASS 증거 보존) + .claude/logs/quality-self-check.log (1줄씩)
사용: python quality-self-check.py [--transcript <jsonl>]   (Stop 훅 입력 JSON 을 stdin 으로 받아도 됨)
판정을 바꾸려고 값을 고치지 않는다 — 기록이 없으면 «미측정».
"""
from __future__ import annotations

import datetime as _dt
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
STATE = ROOT / ".claude" / "state" / "quality-self-check.json"
LOG = ROOT / ".claude" / "logs" / "quality-self-check.log"
START_LIMIT_MS = 5000
MIN_REPORTS = 10


def _std():
    spec = importlib.util.spec_from_file_location("std_req_qsc", ROOT / ".claude" / "scripts" / "standing-requirements.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load(transcript: str) -> list:
    out = []
    try:
        with open(transcript, encoding="utf-8", errors="replace") as f:
            for ln in f:
                try:
                    out.append(json.loads(ln))
                except ValueError:
                    pass
    except OSError:
        pass
    return out


def _walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from _walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from _walk(v)


def check_startup(events: list) -> dict:
    hooks = {}
    cancelled = []          # 시간 초과로 끊긴 훅 = 기능 실패 (11-13 process-outbox 11187ms hook_cancelled 실제 사례)
    for e in events:
        for d in _walk(e):
            if d.get("hookName") == "SessionStart:startup" and "durationMs" in d:
                cmd = str(d.get("command", ""))
                name = os.path.basename(cmd.split('"')[-2]) if '"' in cmd else cmd[-40:]
                hooks[name] = max(hooks.get(name, 0), int(d.get("durationMs") or 0))
                if d.get("type") == "hook_cancelled" and name not in cancelled:
                    cancelled.append(name)
    if not hooks:
        return {"result": "미측정", "why": "이 세션에 SessionStart:startup 기록 없음 (compact·resume 로 시작)"}
    slow = max(hooks, key=hooks.get)
    wait = hooks[slow]
    ok = wait <= START_LIMIT_MS and not cancelled
    why = f"가장 늦은 훅 {slow} {wait}ms (기준 {START_LIMIT_MS}ms)"
    if cancelled:
        why += f" · 시간 초과로 끊김 {', '.join(cancelled)}"
    return {"result": "PASS" if ok else "FAIL", "wait_ms": wait, "slowest": slow, "hooks": len(hooks),
            "cancelled": cancelled, "why": why}


def check_korean(events: list) -> dict:
    std = _std()
    reports = english = 0
    samples = []
    for e in events:
        if e.get("isSidechain") or e.get("type") != "assistant":
            continue
        for c in ((e.get("message") or {}).get("content") or []):
            if not (isinstance(c, dict) and c.get("type") == "text"):
                continue
            t = c.get("text", "")
            if t.startswith("API Error"):          # 시스템이 넣은 연결 오류 문구
                continue
            ratio, n = std._hangul_ratio(t)
            if n < std.LANG_MIN_LETTERS:
                continue
            reports += 1
            if ratio < std.LANG_MIN_HANGUL:
                english += 1
                if len(samples) < 3:
                    samples.append(t[:60].replace("\n", " "))
    # 교정은 훅이 실제로 낸 사건만 센다 (R253 재측정: 26 = 같은 사건 이중 기록 10 + 소스 읽기·grep·요약 인용 15 오탐)
    #   Stop 차단 = system/stop_hook_summary 1건 (같은 내용의 user "Stop hook feedback" 은 중복)
    #   도구 뒤 안내 = attachment/hook_additional_context 1건 (같은 내용의 hook_success 는 중복)
    def _has(e):
        return "[STD-KOREAN-001]" in json.dumps(e, ensure_ascii=False)
    stop_blocks = sum(1 for e in events if e.get("type") == "system" and e.get("subtype") == "stop_hook_summary"
                      and _has(e))
    advisories = sum(1 for e in events if e.get("type") == "attachment"
                     and (e.get("attachment") or {}).get("type") == "hook_additional_context" and _has(e))
    corrected = stop_blocks + advisories
    if reports < MIN_REPORTS:
        res = "미측정"
    elif english == 0 and corrected == 0:
        res = "PASS"
    else:
        res = "PARTIAL"
    return {"result": res, "reports": reports, "english": english, "corrections": corrected,
            "stop_blocks": stop_blocks, "advisories": advisories, "samples": samples,
            "why": f"보고 {reports} · 영어 {english} · Stop 차단 {stop_blocks} · 안내 {advisories}"
                   f" (PASS = 영어 0·교정 0·보고 {MIN_REPORTS}+)"}


def _boot_epoch() -> float | None:
    try:
        import psutil  # noqa: PLC0415
        return float(psutil.boot_time())
    except Exception:  # noqa: BLE001
        return None


def _ts(e) -> float | None:
    t = e.get("timestamp")
    if not t:
        return None
    try:
        return _dt.datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def check_resume(events: list, transcript: str) -> dict:
    boot = _boot_epoch()
    times = [t for t in (_ts(e) for e in events) if t]
    if boot is None or not times:
        return {"result": "미측정", "why": "부팅 시각 또는 세션 시각을 못 읽음"}
    start = min(times)
    proj = Path(transcript).parent
    others = [p for p in proj.glob("*.jsonl") if p != Path(transcript)]
    earlier_after_boot = [p for p in others if boot < p.stat().st_mtime < start and p.stat().st_ctime > boot]
    if start < boot:
        return {"result": "해당 없음", "why": "부팅 전에 시작한 세션 (재부팅 뒤 첫 세션 아님)"}
    if earlier_after_boot:
        return {"result": "해당 없음", "why": "부팅 뒤 이미 다른 세션이 있었음 (첫 세션 아님)"}
    blob = json.dumps(events[:80], ensure_ascii=False)
    injected = "이어서 할 일" in blob
    # 첫 사람 입력 뒤 첫 assistant 턴에서 도구를 썼는가 (확인 질문만 하고 멈추지 않았는가)
    #   도구를 썼어도 마지막 보고가 «진행할지·할까요·말씀해 주세요» 로 끝나면 확인 질문 = PASS 아님
    #   (11-12 재부팅 첫 세션: 상태 조회 도구는 썼지만 "1~3번도 이어서 처리할지 말씀해 주세요" 로 멈춘 실제 사례)
    used_tool = False
    last_text = ""
    seen_user = False
    for e in events:
        if e.get("isSidechain"):
            continue
        if e.get("type") == "user":
            parts = (e.get("message") or {}).get("content")
            if isinstance(parts, str) or any(isinstance(c, dict) and c.get("type") == "text" for c in (parts or [])):
                if seen_user:
                    break
                seen_user = True
            continue
        if seen_user and e.get("type") == "assistant":
            for c in ((e.get("message") or {}).get("content") or []):
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    used_tool = True
                elif isinstance(c, dict) and c.get("type") == "text" and c.get("text", "").strip():
                    last_text = c["text"]
    tail = last_text.strip()[-200:]
    asked = bool(re.search(r"(진행할지|처리할지|할까요|말씀해 ?주세요|알려 ?주세요|어떻게 할지|선택해 ?주세요)\s*[.?!]?\s*$", tail)
                 # 실제 사례 문장: '"진행해"라고 하시면 … 이어서 처리하겠습니다.' (지시를 기다리는 조건문)
                 or re.search(r"(하시면|주시면|원하시면|지시하시면)[^\n]{0,150}(하겠습니다|드리겠습니다|진행합니다|처리합니다)", tail))
    acted = used_tool and not asked
    try:
        subj = subprocess.run(["git", "log", f"--since=@{int(boot)}", "--format=%s"], cwd=ROOT, capture_output=True,
                              text=True, encoding="utf-8", timeout=10).stdout.splitlines()
    except Exception:  # noqa: BLE001
        subj = []
    dup = len(subj) - len(set(subj))
    ok = injected and acted and dup == 0
    res = "PASS" if ok else ("PARTIAL" if injected else "FAIL")
    return {"result": res, "injected": injected, "acted_without_asking": acted, "asked_to_continue": asked,
            "duplicate_commits": dup,
            "boot": _dt.datetime.fromtimestamp(boot).strftime("%m-%d %H:%M"),
            "why": f"재개 주입 {injected} · 첫 요청에서 바로 실행 {acted} · 부팅 뒤 중복 커밋 {dup}"}


def main() -> int:
    transcript = ""
    if "--transcript" in sys.argv:
        transcript = sys.argv[sys.argv.index("--transcript") + 1]
    elif not sys.stdin.isatty():
        try:
            transcript = (json.loads(sys.stdin.read() or "{}") or {}).get("transcript_path", "")
        except ValueError:
            transcript = ""
    if not transcript or not os.path.isfile(transcript):
        print("quality-self-check: 대화 기록 경로 없음 — 미측정")
        return 0
    ev = _load(transcript)
    sid = Path(transcript).stem
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    res = {"Q12_startup": check_startup(ev), "Q11_korean": check_korean(ev), "Q1_reboot_resume": check_resume(ev, transcript)}
    try:
        prev = json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        prev = {}
    last_pass = prev.get("last_pass", {})
    for k, v in res.items():
        if v["result"] == "PASS":
            last_pass[k] = {"session": sid, "at": now, **v}
        elif last_pass.get(k, {}).get("session") == sid:   # 같은 세션을 다시 판정해 PASS 가 아니면 이전 PASS 증거 철회
            last_pass.pop(k)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"checked_at": now, "session": sid, "latest": res, "last_pass": last_pass},
                                ensure_ascii=False, indent=1), encoding="utf-8")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f"{now} {sid[:8]} " + " · ".join(f"{k}={v['result']}" for k, v in res.items())
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    for k, v in res.items():
        print(f"{k}: {v['result']} — {v['why']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
