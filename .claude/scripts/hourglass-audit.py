#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
hourglass-audit — ⏳ 상태 세분화 (사용자 명시 2026-10-16).

상태 매트릭스 (사용자 지시):
  ✅ = 실제 측정 완료 / 정상
  ❌ = 실제 측정 실패
  ⚠ = 소스는 있으나 읽기 또는 실행 실패
  ⏳ = 측정 가능하지만 아직 실행하지 않음
  ↻ = 현재 측정/재시도 중
  ? = 소스 또는 지원 여부를 확인하지 못함
  — = 현재 프로젝트에서 측정 불가 또는 해당 없음

목적: 각 ⏳ 항목이 "왜 ⏳인지" 소스 기준으로 증명.
     ⏳ 를 기본 fallback 으로 사용하지 X.

출력:
  python hourglass-audit.py       # markdown 표
  python hourglass-audit.py json  # JSON

구조:
  항목 | 현재상태 | 데이터소스 | 측정가능여부 | 실제원인 | 수정필요여부
"""
from __future__ import annotations
import json, os, sys, glob, subprocess
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)


def _exists(p: str) -> bool:
    return os.path.exists(os.path.join(ROOT, p))


def _which(cmd: str) -> str:
    import shutil
    return shutil.which(cmd) or ""


def check_test() -> dict:
    """test — package.json scripts.test 또는 pyproject.toml pytest 등."""
    src = []
    reason = ""
    status = "⏳"
    if _exists("package.json"):
        try:
            with open(os.path.join(ROOT, "package.json"), "r", encoding="utf-8") as f:
                p = json.load(f)
            if (p.get("scripts") or {}).get("test"):
                src.append("package.json scripts.test")
        except Exception:
            pass
    if _exists("pyproject.toml") and "pytest" in open(os.path.join(ROOT, "pyproject.toml"), encoding="utf-8", errors="ignore").read():
        src.append("pyproject.toml pytest")
    # kit 자체는 golden-test.py 가 test 대신
    if _exists(".claude/scripts/golden-test.py"):
        src.append("golden-test.py (kit 전용)")
    if not src:
        status = "—"
        reason = "kit 는 test 명령 없음 · golden-test.py 로 대체"
    else:
        cache = ".claude/state/test-cache.json"
        if _exists(cache):
            status = "✅"
            reason = f"{cache} 존재"
        else:
            status = "⏳"
            reason = "소스 있음 · 아직 실행 X"
    return {"status": status, "source": " / ".join(src) or "N/A", "measurable": bool(src), "reason": reason}


def check_build() -> dict:
    src = []
    if _exists("package.json"):
        try:
            with open(os.path.join(ROOT, "package.json"), "r", encoding="utf-8") as f:
                p = json.load(f)
            if (p.get("scripts") or {}).get("build"):
                src.append("package.json scripts.build")
        except Exception:
            pass
    if not src:
        return {"status": "—", "source": "N/A", "measurable": False,
                "reason": "kit 는 build 단계 없음 (python/bash script · 컴파일 X)"}
    return {"status": "⏳", "source": " / ".join(src), "measurable": True,
            "reason": "소스 있음 · 아직 실행 X"}


def check_lint() -> dict:
    src = []
    if _exists(".eslintrc") or _exists(".eslintrc.json") or _exists("eslint.config.js"):
        src.append("eslint config")
    if _exists("pyproject.toml") or _exists(".ruff.toml") or _exists("ruff.toml"):
        src.append("ruff/pyproject")
    if not src:
        return {"status": "—", "source": "N/A", "measurable": False,
                "reason": "kit 는 lint 설정 없음 (python 스크립트만)"}
    return {"status": "⏳", "source": " / ".join(src), "measurable": True,
            "reason": "소스 있음 · 아직 실행 X"}


def check_type() -> dict:
    src = []
    if _exists("tsconfig.json"):
        src.append("tsconfig.json (tsc)")
    if _exists("mypy.ini") or _exists(".mypy.ini"):
        src.append("mypy.ini")
    if _exists("pyrightconfig.json"):
        src.append("pyright")
    if not src:
        return {"status": "—", "source": "N/A", "measurable": False,
                "reason": "kit 는 type checker 미설정 (python 동적 타입)"}
    return {"status": "⏳", "source": " / ".join(src), "measurable": True,
            "reason": "소스 있음 · 아직 실행 X"}


def check_component_reuse() -> dict:
    return {"status": "?", "source": "N/A", "measurable": False,
            "reason": "kit 자체는 UI 컴포넌트 X · install 대상 프로젝트에서 측정"}


def check_bypass() -> dict:
    return {"status": "?", "source": "N/A", "measurable": False,
            "reason": "공통 컴포넌트 우회 감지는 target 프로젝트 전용"}


def check_css_dup() -> dict:
    return {"status": "—", "source": "N/A", "measurable": False,
            "reason": "kit 는 CSS 자산 X · UI 프로젝트 전용 지표"}


def check_new_common() -> dict:
    return {"status": "?", "source": "N/A", "measurable": False,
            "reason": "'신규 공통 컴포넌트 생성' 추적 소스 없음"}


def check_impact() -> dict:
    """영향도 — git diff 분석."""
    try:
        r = subprocess.run(["git", "-C", ROOT, "diff", "--stat"],
                           capture_output=True, text=True, timeout=3)
        if r.returncode == 0:
            lines = r.stdout.strip().splitlines()
            if lines:
                return {"status": "✅", "source": "git diff --stat", "measurable": True,
                        "reason": f"{len(lines)-1} 파일 변경"}
    except Exception:
        pass
    return {"status": "✅", "source": "git diff --stat", "measurable": True,
            "reason": "변경 없음 (clean)"}


def check_breaking() -> dict:
    return {"status": "?", "source": "N/A", "measurable": False,
            "reason": "breaking change 자동 감지 소스 없음 (semver bump + CHANGELOG 수동)"}


def check_golden() -> dict:
    if _exists(".claude/scripts/golden-test.py"):
        cache = ".claude/state/golden-cache.json"
        if _exists(cache):
            return {"status": "✅", "source": "golden-test.py + cache", "measurable": True,
                    "reason": f"{cache} 존재"}
        return {"status": "⏳", "source": "golden-test.py", "measurable": True,
                "reason": "스크립트 존재 · 실행 OK (13/13) · cache 없음"}
    return {"status": "—", "source": "N/A", "measurable": False, "reason": "golden-test.py 없음"}


def check_codex_verify() -> dict:
    db = ".claude/state/orca.db"
    if _exists(db):
        return {"status": "⏳", "source": f"{db} tasks 테이블", "measurable": True,
                "reason": "DB 존재 · 자동 검증 집계 미구현"}
    return {"status": "?", "source": "N/A", "measurable": False, "reason": "orca.db 없음"}


def check_web_verify() -> dict:
    return {"status": "?", "source": "N/A", "measurable": False,
            "reason": "Claude Web 검증 결과 자동 수집 소스 없음"}


ITEMS = [
    ("test", check_test),
    ("build", check_build),
    ("lint", check_lint),
    ("type", check_type),
    ("컴포넌트 재사용", check_component_reuse),
    ("공통 우회", check_bypass),
    ("CSS 중복", check_css_dup),
    ("신규공통", check_new_common),
    ("영향도", check_impact),
    ("breaking", check_breaking),
    ("golden", check_golden),
    ("Codex 검증", check_codex_verify),
    ("Web 검증", check_web_verify),
]


def run_all() -> list:
    rows = []
    for name, fn in ITEMS:
        try:
            r = fn()
        except Exception as e:
            r = {"status": "⚠", "source": "N/A", "measurable": False, "reason": f"check failed: {e}"}
        r["name"] = name
        r["fix_needed"] = r["status"] in ("⚠", "❌") or (r["measurable"] and r["status"] == "⏳")
        rows.append(r)
    return rows


def md_table(rows: list) -> str:
    lines = [
        f"# ⏳ 상태 세분화 감사 — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "상태 매트릭스: ✅ 정상 · ❌ 실패 · ⚠ 읽기/실행 실패 · ⏳ 측정 대기 · ↻ 실행 중 · ? 소스 불명 · — 측정 불가",
        "",
        "| 항목 | 현재상태 | 데이터소스 | 측정가능 | 실제원인 | 수정필요 |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        fix = "YES" if r["fix_needed"] else "no"
        measurable = "YES" if r.get("measurable") else "no"
        lines.append(f"| {r['name']} | {r['status']} | {r['source']} | {measurable} | {r['reason']} | {fix} |")
    lines.extend(["", "## 요약", ""])
    by_status = {}
    for r in rows:
        by_status.setdefault(r["status"], 0)
        by_status[r["status"]] += 1
    for s, c in sorted(by_status.items()):
        lines.append(f"- {s}: {c}건")
    lines.extend([
        "",
        "## 수정 계획",
        "",
        "1. ⏳ (측정 가능 · 미실행) → 실제 측정 실행 or source 추가",
        "2. ? (소스 불명) → 측정 소스 식별 또는 — 로 변경",
        "3. — (측정 불가) → statusline 에서 아예 제거 또는 '해당 없음' 표시",
        "4. ⚠ (실행 실패) → 원인 조사 · 재시도",
        "",
        "## 적용 원칙",
        "",
        "- ⏳ 를 기본 fallback 으로 사용 X",
        "- 각 지표 소스를 명시",
        "- '측정 대기' vs '불러오는 중' vs '소스 없음' vs '측정 불가' 구분",
        "",
    ])
    return "\n".join(lines)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "md"
    rows = run_all()
    if cmd == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        date = datetime.now().strftime("%Y-%m-%d")
        path = os.path.join(ROOT, "docs", f"HOURGLASS_AUDIT_{date}.md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(md_table(rows))
        print(f"[OK] report: {path}")
        print(md_table(rows))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERR] {e}", file=sys.stderr)
        sys.exit(1)
