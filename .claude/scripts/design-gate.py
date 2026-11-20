#!/usr/bin/env python
"""design-gate.py — 디자인 검증 정본 (R275 · 2026-11-16 사용자 지시 "Design Ownership Lock · Golden Baseline ·
Visual Quality Gate · Anti-Ping-Pong 연결 · 서비스 UI 와 상태줄은 다른 검증 대상").

대상 두 종류 (섞지 않는다):
  statusline  — 상태줄의 «구조» (기준선 줄 수 · 2026-11-16 기준선 10줄 — 이 검사는 빈 입력 {} 으로 렌더해 세션 기록이 필요한 «비용» 줄이 빠진다 · 실제 VS Code 화면은 비용 포함 11줄 (R341 실측 · R336 의 «비용 줄 없음» 기록은 잘못된 경로 입력으로 생긴 오판이라 정정)) (줄 수 · 줄별 라벨 · 왼쪽/오른쪽 │ 칸 위치). 값은 비교하지 않는다.
  image:<이름> — 서비스 UI 화면 캡처 PNG. 승인된 기준 PNG 와 픽셀 차이 비율을 비교한다.

  Golden Baseline       baseline statusline | image-baseline <이름> <png>  → .claude/design-baseline/ (git 추적 · 승인 기준)
  Visual Quality Gate   check statusline     | image <이름> <현재 png> [--threshold 0.02]
  Design Ownership Lock 기준과 다르면 FAIL · 해제(unlock <대상> <사유>, 1시간) 없이 바뀐 것은 UNAUTHORIZED = «임의변경»
  Anti-Ping-Pong        check statusline 이 anti-ping-pong 의 statusline_context.py 반복 수정(5회+ block)도 함께 본다

기록: .claude/logs/design-gate.log (append · 시각 · 대상 · 판정) — 상태줄 통제 줄 «임의변경» 의 원천 (계측 시작 전 = 미측정).
종료 코드: 0 PASS · 1 FAIL(해제 상태의 변경 포함) · 2 UNAUTHORIZED · 3 기준 없음/실행 불가(미측정).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parent.parent.parent)
BASE = ROOT / ".claude" / "design-baseline"
LOG = ROOT / ".claude" / "logs" / "design-gate.log"
UNLOCK = ROOT / ".claude" / "state" / "design-unlock.json"
SL = ROOT / ".claude" / "scripts" / "statusline_context.py"
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
UNLOCK_SEC = 3600

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _cells(s: str) -> int:
    try:
        from wcwidth import wcwidth as _wc
    except Exception:
        def _wc(ch):
            return 2 if ord(ch) > 0x2E7F else 1
    return sum(max(_wc(ch), 0) for ch in s)


def signature(text: str) -> dict:
    """상태줄 출력 → 구조 서명 (값 제외). 줄마다 왼쪽 라벨·│ 위치, 오른쪽 쌍(▶ 뒤) 라벨·│ 위치."""
    rows = []
    for raw in [r for r in text.splitlines() if r.strip()]:
        cha = re.search(r"\x1b\[(\d+)G\s*│", raw)   # 동결 전제: 왼쪽 │ 는 CHA 로 칸 고정 (operational-freeze)
        ln = ANSI.sub("", raw)
        if "│" not in ln:
            rows.append({"label": ln.strip()[:12], "bar": None, "right": None, "rbar": None})
            continue
        left, rest = ln.split("│", 1)
        row = {"label": re.sub(r"\s+", "", left), "bar": _cells(left), "cha": int(cha.group(1)) if cha else None,
               "right": None, "rbar": None}
        if "▶" in rest and "│" in rest.split("▶", 1)[1]:
            pre, post = rest.split("▶", 1)
            rlab, _ = post.split("│", 1)
            row["right"] = re.sub(r"\s+", "", rlab)
            row["rbar"] = _cells(rlab)
        rows.append(row)
    return {"rows": len(rows), "items": rows}


def render_statusline(columns: int = 250) -> str:
    env = dict(os.environ, COLUMNS=str(columns), CLAUDE_PROJECT_DIR=str(ROOT), PYTHONIOENCODING="utf-8")
    env.pop("STATUSLINE_MAX_COLS", None)
    try:
        r = subprocess.run([sys.executable, "-X", "utf8", str(SL)], input=b"{}", capture_output=True, env=env, timeout=60,
                           cwd=str(ROOT))
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else ""


def compare(base: dict, cur: dict) -> list:
    diffs = []
    if base.get("rows") != cur.get("rows"):
        diffs.append(f"줄 수 {base.get('rows')} → {cur.get('rows')}")
    for i, (b, c) in enumerate(zip(base.get("items", []), cur.get("items", [])), 1):
        for k, name in (("label", "왼쪽 라벨"), ("bar", "왼쪽 │ 칸"), ("cha", "왼쪽 │ CHA 칸"), ("right", "오른쪽 라벨"),
                        ("rbar", "오른쪽 │ 폭")):
            if b.get(k) != c.get(k):
                diffs.append(f"{i}줄 {name} {b.get(k)!r} → {c.get(k)!r}")
    return diffs


def _unlocked(target: str) -> dict | None:
    try:
        u = json.loads(UNLOCK.read_text(encoding="utf-8")).get(target)
        if u and time.time() - float(u.get("ts", 0)) < UNLOCK_SEC:
            return u
    except (OSError, ValueError, TypeError):
        pass
    return None


def _dkey(diffs: list) -> str:
    """같은 위반(차이 내용이 같음)을 한 건으로 세기 위한 표지."""
    import hashlib
    return "#" + hashlib.sha1("|".join(sorted(diffs)).encode("utf-8")).hexdigest()[:10]


def _log(target: str, verdict: str, detail: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {verdict} {target} · {detail[:300]}\n")


def _ping_pong() -> str:
    """anti-ping-pong 연결 — statusline_context.py 반복 수정 상태 (block/warn/ok · 실패 = unknown)."""
    try:
        r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / ".claude" / "scripts" / "anti-ping-pong.py"), "check",
                            "--file", str(SL)], capture_output=True, timeout=20, cwd=str(ROOT))
        return json.loads(r.stdout.decode("utf-8", "replace") or "{}").get("status", "unknown")
    except Exception:
        return "unknown"


def cmd_baseline_statusline(columns: int = 250) -> int:
    if (BASE / "statusline.json").exists() and not _unlocked("statusline"):
        _log("statusline", "BASELINE-REFUSED", "해제 없이 승인 기준 덮어쓰기 시도")
        print("거부: 승인 기준이 이미 있음 — unlock statusline <사유> 후에만 다시 기준 저장 (Design Ownership Lock)")
        return 2
    sig = signature(render_statusline(columns))
    if sig["rows"] < 5:
        print(f"상태줄 출력이 {sig['rows']}줄 — 기준으로 저장하지 않음 (미측정)")
        return 3
    BASE.mkdir(parents=True, exist_ok=True)
    (BASE / "statusline.json").write_text(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "columns": columns, **sig},
                                                     ensure_ascii=False, indent=1), encoding="utf-8")
    _log("statusline", "BASELINE", f"{sig['rows']}줄 기준 저장")
    print(f"상태줄 기준 저장: {sig['rows']}줄 → {BASE / 'statusline.json'}")
    return 0


def cmd_check_statusline(text: str | None = None, record: bool = True) -> int:
    bp = BASE / "statusline.json"
    if not bp.exists():
        print("상태줄 기준 없음 — 미측정 (baseline statusline 먼저)")
        return 3
    base = json.loads(bp.read_text(encoding="utf-8"))
    cur = signature(text if text is not None else render_statusline(int(base.get("columns") or 250)))
    if cur["rows"] < 5:
        if record:
            _log("statusline", "UNMEASURED", f"상태줄 출력 {cur['rows']}줄 (렌더 실패·빈 출력)")
        print(f"미측정: 상태줄 출력 {cur['rows']}줄 — 렌더 실패는 위반으로 기록하지 않음")
        return 3
    diffs = compare(base, cur)
    pp = _ping_pong() if text is None else "skip"
    if pp == "block" and not diffs:
        if record:
            _log("statusline", "PINGPONG", "statusline_context.py 같은 수정 5회+ 반복 (DESIGN_CONFLICT · 임의변경과 별개)")
        print("FAIL anti-ping-pong: 같은 수정 5회+ 반복 — 구조는 일치하나 자동 수정 중단 (DESIGN_CONFLICT)")
        return 1
    if not diffs:
        if record:
            _log("statusline", "PASS", f"{cur['rows']}줄 구조 일치 · ping-pong {pp}")
        print(f"PASS 상태줄 구조 일치 ({cur['rows']}줄) · anti-ping-pong {pp if pp != 'unknown' else '미측정'}")
        return 0
    verdict, rc = ("FAIL", 1) if _unlocked("statusline") else ("UNAUTHORIZED", 2)
    if record:
        _log("statusline", verdict, _dkey(diffs) + " " + "; ".join(diffs))
    print(f"{verdict} 상태줄 승인 구조와 다름 ({len(diffs)}건)" + ("" if rc == 1 else " — 해제 없이 바뀜 = 임의변경"))
    for d in diffs[:20]:
        print("  - " + d)
    return rc


def cmd_image_baseline(name: str, png: str) -> int:
    from PIL import Image
    if (BASE / f"image-{name}.png").exists() and not _unlocked(f"image:{name}"):
        _log(f"image:{name}", "BASELINE-REFUSED", "해제 없이 승인 기준 덮어쓰기 시도")
        print(f"거부: image-{name} 승인 기준이 이미 있음 — unlock image:{name} <사유> 후에만")
        return 2
    with Image.open(png) as im:
        im.load()
        BASE.mkdir(parents=True, exist_ok=True)
        im.convert("RGB").save(BASE / f"image-{name}.png")
    _log(f"image:{name}", "BASELINE", png)
    print(f"서비스 UI 기준 저장: image-{name}.png")
    return 0


def image_diff_ratio(a: str, b: str) -> float:
    from PIL import Image, ImageChops
    with Image.open(a) as ia, Image.open(b) as ib:
        x, y = ia.convert("RGB"), ib.convert("RGB")
        if x.size != y.size:
            return 1.0
        d = ImageChops.difference(x, y).convert("L").point(lambda v: 255 if v > 24 else 0)
        hist = d.histogram()
        return hist[255] / float(x.size[0] * x.size[1])


def cmd_image(name: str, png: str, threshold: float = 0.02) -> int:
    bp = BASE / f"image-{name}.png"
    if not bp.exists():
        print(f"서비스 UI 기준 없음 (image-{name}) — 미측정")
        return 3
    ratio = image_diff_ratio(str(bp), png)
    if ratio <= threshold:
        _log(f"image:{name}", "PASS", f"차이 {ratio:.4f} ≤ {threshold}")
        print(f"PASS 화면 차이 {ratio:.2%} (기준 {threshold:.0%} 이하)")
        return 0
    verdict, rc = ("FAIL", 1) if _unlocked(f"image:{name}") else ("UNAUTHORIZED", 2)
    _log(f"image:{name}", verdict, f"차이 {ratio:.4f} > {threshold}")
    print(f"{verdict} 화면 차이 {ratio:.2%} (기준 {threshold:.0%} 초과)")
    return rc


def cmd_unlock(target: str, reason: str) -> int:
    UNLOCK.parent.mkdir(parents=True, exist_ok=True)
    try:
        cur = json.loads(UNLOCK.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cur = {}
    cur[target] = {"ts": time.time(), "reason": reason}
    UNLOCK.write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
    _log(target, "UNLOCK", reason)
    print(f"{target} 디자인 변경 허용 1시간 · 사유: {reason}")
    return 0


def violations(hours: float = 24) -> int | None:
    """최근 N시간 UNAUTHORIZED(임의변경) 수 · 기록 파일 없음 = None (미측정)."""
    if not LOG.exists():
        return None
    cut = time.time() - hours * 3600
    seen = set()
    for ln in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\] UNAUTHORIZED (\S+) · (#\w+|\S+)", ln)
        if m and time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")) >= cut:
            seen.add((m.group(2), m.group(3)))   # 같은 대상·같은 차이 = 1건 (검사를 여러 번 돌려도 부풀지 않음)
    return len(seen)


def main(argv: list) -> int:
    if len(argv) >= 2 and argv[:2] == ["baseline", "statusline"]:
        return cmd_baseline_statusline()
    if len(argv) >= 2 and argv[:2] == ["check", "statusline"]:
        return cmd_check_statusline()
    if len(argv) >= 3 and argv[0] == "image-baseline":
        return cmd_image_baseline(argv[1], argv[2])
    if len(argv) >= 3 and argv[0] == "image":
        try:
            th = float(argv[argv.index("--threshold") + 1]) if "--threshold" in argv else 0.02
        except (IndexError, ValueError):
            print("--threshold 값이 없거나 숫자가 아님")
            return 3
        return cmd_image(argv[1], argv[2], th)
    if len(argv) >= 3 and argv[0] == "unlock":
        return cmd_unlock(argv[1], " ".join(argv[2:]))
    if argv[:1] == ["violations"]:
        v = violations()
        print("미측정" if v is None else v)
        return 0
    print(__doc__)
    return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
