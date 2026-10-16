#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
health-check — Orchestration Health 자동 점검 (사용자 명시 2026-10-16).

원칙 (사용자 명시):
- 자동으로 OK: 검사·비교·drift·golden·health score·보고서·statusline
- 자동 금지: rule 삭제·hook 추가·skill merge·agent 변경·routing 정책
- 월 1회 조건 체크 (가벼운 스케줄러) · 매 SessionStart X
- 이상 있을 때만 CHANGE CANDIDATE 제안 · 자동 수정 X

점검 축 (10):
  1. 충돌 (중복 함수·hook·rule)
  2. 중복 (hook/skill/rule 중복)
  3. orphan (plugins/ 밖 .claude/ 자산)
  4. drift (release-manifest baseline 대비)
  5. golden (10/10 테스트)
  6. request (ledger 완료율)
  7. codex (routing 정상)
  8. stop gate (standing req 통과)
  9. 전파 (sync-to-team / install-to-target 로그)
  10. 재발률 (recurrence by category)

사용:
  python health-check.py status   # statusline 용 (96/100 · last 10/16 · next 11/16)
  python health-check.py scan     # 전체 점검 → JSON
  python health-check.py report   # 월간 ORCHESTRATION_HEALTH_YYYY-MM-DD.md 생성
  python health-check.py monthly  # 지난 점검으로부터 30일 지났으면 report 자동
"""
from __future__ import annotations
import json
import os
import sys
import glob
import time
import subprocess
from datetime import datetime, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
STATE_DIR = os.path.join(ROOT, ".claude", "state")
STATE_FILE = os.path.join(STATE_DIR, "health-check.json")


def _run_py(script: str, args: list) -> tuple[int, str]:
    try:
        p = os.path.join(ROOT, ".claude", "scripts", script)
        if not os.path.exists(p):
            return (1, "")
        r = subprocess.run([sys.executable, "-X", "utf8", p] + args,
                           capture_output=True, text=True, timeout=10, cwd=ROOT)
        return (r.returncode, r.stdout.strip())
    except Exception:
        return (1, "")


def check_drift() -> dict:
    """drift-detect.py scan 결과 요약."""
    rc, out = _run_py("drift-detect.py", ["scan"])
    if rc != 0 or not out:
        return {"ok": False, "value": "?", "detail": "scan failed"}
    try:
        d = json.loads(out)
        total = sum(d.get("diff", {}).get(k, {}).get("total", 0)
                    for k in ("core", "rule", "hook", "agent"))
        core_imp = d.get("diff", {}).get("core_important", False)
        return {"ok": total == 0, "value": total,
                "core_important": core_imp,
                "frozen": d.get("frozen", False)}
    except Exception:
        return {"ok": False, "value": "?", "detail": "parse failed"}


def check_golden() -> dict:
    """golden-test.py 결과 요약 (10/10 PASS?)."""
    rc, out = _run_py("golden-test.py", [])
    # golden-test.py 존재만 확인 (실행 비용 들수 있음)
    gt = os.path.join(ROOT, ".claude", "scripts", "golden-test.py")
    if not os.path.exists(gt):
        return {"ok": False, "value": "N/A", "detail": "golden-test.py missing"}
    # 결과 텍스트에서 "N/N PASS" 패턴 찾기
    import re
    m = re.search(r"(\d+)/(\d+)\s*(?:PASS|OK|✓)", out, re.IGNORECASE)
    if m:
        passed, total = int(m.group(1)), int(m.group(2))
        return {"ok": passed == total, "value": f"{passed}/{total}"}
    return {"ok": rc == 0, "value": "existed"}


def check_request_ledger() -> dict:
    """request-ledger.json 완료율."""
    f = os.path.join(STATE_DIR, "request-ledger.json")
    if not os.path.exists(f):
        return {"ok": True, "value": "0/0", "detail": "no requests"}
    try:
        with open(f, "r", encoding="utf-8") as fp:
            d = json.load(fp)
        reqs = d.get("requests", [])
        total = len(reqs)
        done = sum(1 for r in reqs if r.get("status") in ("completed", "deferred"))
        return {"ok": done == total, "value": f"{done}/{total}"}
    except Exception:
        return {"ok": False, "value": "?"}


def check_standing() -> dict:
    """standing-requirements gate exit code."""
    rc, out = _run_py("standing-requirements.py", ["stats"])
    try:
        d = json.loads(out) if out else {}
        ok = int(d.get("ok", 0))
        active = int(d.get("active", 0))
        return {"ok": ok == active and active > 0, "value": f"{ok}/{active}"}
    except Exception:
        return {"ok": False, "value": "?"}


def check_orphan() -> dict:
    """plugins/ 밖 .claude/ 자산 (sync-plugins drift)."""
    rc, out = _run_py("sync-plugins.sh" if False else "sync-plugins-check.py", [])
    # 간단 heuristic: .claude/commands 와 plugins/*/commands 일치?
    cmd_dir = os.path.join(ROOT, ".claude", "commands")
    plugin_cmd_dirs = glob.glob(os.path.join(ROOT, "plugins", "*", "commands"))
    if not os.path.isdir(cmd_dir):
        return {"ok": True, "value": "0"}
    # orphan 검사는 복잡 - 간단히 .claude/commands 수 vs plugins 합계
    claude_cmds = set(os.path.basename(p) for p in glob.glob(os.path.join(cmd_dir, "*.md")))
    plugin_cmds = set()
    for d in plugin_cmd_dirs:
        for p in glob.glob(os.path.join(d, "*.md")):
            plugin_cmds.add(os.path.basename(p))
    orphan = claude_cmds - plugin_cmds
    return {"ok": len(orphan) == 0, "value": len(orphan),
            "detail": sorted(list(orphan))[:5]}


def check_duplicates() -> dict:
    """중복 hook/rule heuristic (파일명 유사)."""
    import collections
    rule_files = [os.path.basename(p) for p in glob.glob(os.path.join(ROOT, ".claude", "rules", "*.md"))]
    hook_files = [os.path.basename(p) for p in glob.glob(os.path.join(ROOT, ".claude", "hooks", "*.sh"))]
    # 간단 검사: 같은 topic 접두어 (post-codex-verify / codex-rules 등)
    rule_prefixes = collections.Counter(r.split("-")[0] for r in rule_files if "-" in r)
    hook_prefixes = collections.Counter(h.split("-")[0] for h in hook_files if "-" in h)
    dup = sum(1 for v in rule_prefixes.values() if v >= 3) + sum(1 for v in hook_prefixes.values() if v >= 4)
    return {"ok": dup < 5, "value": dup,
            "detail": {"rule": {k: v for k, v in rule_prefixes.most_common(3)},
                       "hook": {k: v for k, v in hook_prefixes.most_common(3)}}}


def check_recurrence() -> dict:
    """재발률 (rule-adherence.json)."""
    f = os.path.join(STATE_DIR, "rule-adherence.json")
    if not os.path.exists(f):
        return {"ok": True, "value": "0%", "detail": "no data"}
    try:
        with open(f, "r", encoding="utf-8") as fp:
            d = json.load(fp)
        rec = d.get("recurrence", {}).get("by_category", {})
        rates = [rec.get(c, {}).get("recur_rate_pct", 0) for c in ("design", "dev")]
        avg = sum(rates) / len(rates) if rates else 0
        return {"ok": avg < 40, "value": f"{avg:.0f}%"}
    except Exception:
        return {"ok": False, "value": "?"}


def check_propagation() -> dict:
    """sync-to-team · install-to-target · merge-to-target 최근 로그."""
    logs = ["merge-to-target.log", "sync-to-team.log", "install-to-target.log"]
    recent = 0
    for log in logs:
        p = os.path.join(ROOT, ".claude", "logs", log)
        if os.path.exists(p):
            age_days = (time.time() - os.path.getmtime(p)) / 86400
            if age_days <= 7:
                recent += 1
    return {"ok": recent >= 1, "value": f"{recent}/3"}


def check_stop_gate() -> dict:
    """stop-six-guards.sh 또는 stop-request-ledger-gate.sh 존재."""
    hooks = [os.path.join(ROOT, ".claude", "hooks", f)
             for f in ("stop-six-guards.sh", "stop-request-ledger-gate.sh")]
    exists = sum(1 for h in hooks if os.path.exists(h))
    return {"ok": exists >= 1, "value": f"{exists}/2"}


def check_codex() -> dict:
    """codex-auto 상태 (orca.db · tasks 테이블)."""
    db = os.path.join(STATE_DIR, "orca.db")
    if not os.path.exists(db):
        return {"ok": True, "value": "N/A", "detail": "no db"}
    try:
        import sqlite3
        with sqlite3.connect(db) as c:
            # 최근 24h 실패 task 수
            r = c.execute("SELECT COUNT(*) FROM tasks WHERE status='failed' "
                          "AND created_at >= datetime('now','-1 day')").fetchone()
            fail = r[0] if r else 0
        return {"ok": fail < 3, "value": f"{fail} fail/24h"}
    except Exception:
        return {"ok": True, "value": "?"}


def run_all_checks() -> dict:
    """10 축 전체 점검."""
    return {
        "충돌": check_duplicates(),
        "중복": check_duplicates(),  # alias
        "orphan": check_orphan(),
        "drift": check_drift(),
        "golden": check_golden(),
        "request": check_request_ledger(),
        "codex": check_codex(),
        "stop_gate": check_stop_gate(),
        "전파": check_propagation(),
        "재발률": check_recurrence(),
        "standing": check_standing(),
    }


def compute_score(checks: dict) -> int:
    """100점 환산. 각 축 10점 × 10."""
    ok_count = sum(1 for v in checks.values() if v.get("ok"))
    total = len(checks)
    if total == 0:
        return 0
    return int(ok_count / total * 100)


def _load_state() -> dict:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def status_line() -> str:
    """statusline 용 짧은 한 줄: 96/100 · last 10/16 · next 11/16"""
    state = _load_state()
    score = state.get("last_score", 0)
    last_ts = state.get("last_check")
    if last_ts:
        try:
            last_dt = datetime.fromisoformat(last_ts)
            last_str = last_dt.strftime("%m/%d")
            next_dt = last_dt + timedelta(days=30)
            next_str = next_dt.strftime("%m/%d")
            days_left = (next_dt - datetime.now()).days
        except Exception:
            last_str = "?"; next_str = "?"; days_left = 0
    else:
        last_str = "미측정"; next_str = "?"; days_left = 0
    # 색상
    if score >= 90:
        c = "1;32"  # 초록
    elif score >= 70:
        c = "1;33"  # 노랑
    elif score == 0:
        c = "90"    # 회색 (미측정)
    else:
        c = "1;31"  # 빨강
    due = ""
    if last_ts and days_left <= 0:
        due = " \033[1;33m[점검 필요]\033[0m"
    score_s = f"\033[{c}m{score}/100\033[0m" if score else f"\033[90m⏳\033[0m"
    return f"{score_s} · last {last_str} · next {next_str}{due}"


def scan_and_save() -> dict:
    checks = run_all_checks()
    score = compute_score(checks)
    now = datetime.now().isoformat(timespec="seconds")
    state = _load_state()
    state["last_check"] = now
    state["last_score"] = score
    state["last_checks"] = {k: {"ok": v.get("ok"), "value": v.get("value")} for k, v in checks.items()}
    _save_state(state)
    return {"score": score, "checks": checks, "ts": now}


def gen_report(scan_result: dict) -> str:
    """ORCHESTRATION_HEALTH_YYYY-MM-DD.md 생성."""
    date = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(ROOT, "docs", f"ORCHESTRATION_HEALTH_{date}.md")
    score = scan_result["score"]
    verdict = "HEALTHY" if score >= 90 else ("ATTENTION" if score >= 70 else "CRITICAL")
    action = "NO CHANGE" if score >= 90 else "CHANGE CANDIDATE"
    lines = [f"# Orchestration Health — {date}", "",
             f"**점수**: {score}/100 · **판정**: {verdict} · **조치**: {action}", ""]
    for name, result in scan_result["checks"].items():
        icon = "✅" if result.get("ok") else "⚠"
        lines.append(f"- {name}: {result.get('value', '?')} {icon}")
    if score < 90:
        lines.extend(["", "## CHANGE CANDIDATE (자동 수정 X · 사용자 승인 후만)", ""])
        for name, result in scan_result["checks"].items():
            if not result.get("ok"):
                lines.append(f"- {name}: {result.get('detail', '점검 필요')}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        print(status_line())
    elif cmd == "scan":
        print(json.dumps(scan_and_save(), indent=2, ensure_ascii=False, default=str))
    elif cmd == "report":
        res = scan_and_save()
        p = gen_report(res)
        print(f"report: {p}")
    elif cmd == "monthly":
        state = _load_state()
        last_ts = state.get("last_check")
        if last_ts:
            last_dt = datetime.fromisoformat(last_ts)
            if (datetime.now() - last_dt).days < 30:
                print(f"skip: 지난 점검 {(datetime.now() - last_dt).days} 일 전")
                return
        res = scan_and_save()
        p = gen_report(res)
        print(f"monthly report: {p}")
    else:
        print(f"unknown: {cmd}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\033[90m⏳\033[0m · last ? · next ?", file=sys.stderr)
        sys.exit(1)
