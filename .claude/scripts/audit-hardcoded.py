#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""audit-hardcoded — CLAUDE.md § 7-A1 (하드 경로·시크릿·Python 버전 금지) 자동 감사.
결과: .claude/state/hardcoded-audit.json
"""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / ".claude" / "state" / "hardcoded-audit.json"

PATTERNS = [
    ("users_path_win", re.compile(r"C:\\Users\\[a-z0-9_]+", re.IGNORECASE), "Windows 사용자 경로"),
    ("users_path_unix", re.compile(r"/home/[a-z0-9_]+"), "Linux 사용자 경로"),
    ("python_version", re.compile(r"Python3(10|11|12|13|14|15)\\python\.exe"), "Python 버전 박음"),
    ("desktop_hostname", re.compile(r"DESKTOP-[A-Z0-9]+"), "특정 호스트명"),
    ("ip_192", re.compile(r"192\.168\.\d+\.\d+"), "고정 사설 IP"),
    ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key"),
    ("openai_key", re.compile(r"sk-[a-zA-Z0-9]{40,}"), "OpenAI/Anthropic API key"),
    ("github_pat", re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub PAT"),
]

# ★★★1002 — 문서(.md)에서 **경로·버전·호스트·IP 만** 면제한다.
#   왜: 실측 1002 에 남은 22건이 전부 **룰·가이드가 「이렇게 쓰지 마라」고 인용한
#   금지 예시**였다(`best-practices.md` 의 사용자 경로 예시 4건 등). 규칙 문서가
#   자기가 금지하는 패턴을 적었다고 위반으로 세면, 고치는 길은 **예시를 지우는
#   것**뿐이고 그러면 룰이 뜻을 잃는다.
#   ★★단, **시크릿 3종(aws_key·openai_key·github_pat)은 문서에서도 계속 잡는다** —
#     「.md 는 전부 면제」로 넓히면 문서에 박힌 진짜 키를 영원히 못 본다.
#     면제는 «오탐이 구조적인 패턴»에만 걸고, «나면 사고인 패턴»에는 안 건다.
#   ★이것은 「규칙이 틀렸으면 규칙을 고친다」 갈래다(코드를 비틀지 않는다).
DOC_EXEMPT_KEYS = {"users_path_win", "users_path_unix",
                   "python_version", "desktop_hostname", "ip_192"}

# ★★★1002 — 두 갈래로 나눴다. 종전엔 한 집합에 섞여 있었고, 그래서
#   «.claude/state» 류 **경로형 3개가 한 번도 걸러진 적이 없었다**:
#   비교가 `any(p in SKIP_DIRS for p in rel.split("/"))` 라 한 칸(.claude 또는
#   state)하고만 맞춰 보는데, 집합에는 두 칸짜리 문자열이 들어 있었다.
#   ★그 결과 감사기가 **자기 결과 파일(.claude/state/hardcoded-audit.json)을
#     다시 스캔**했다 — 검출한 위반이 캐시에 적히고, 다음 실행이 그걸 또 센다.
#     실측 1002: 전체 115건 중 **38건이 이 자기참조**였다(출처 1위).
#     숫자가 실행마다 출렁이던 것도, 고치지 않아도 늘던 것도 이 때문이다.
#   ★「방어가 있다고 믿는 것이 없는 것보다 위험하다」(A4)·「측정 도구는 자기를
#     세지 않는다」(A12)가 한 자리에서 같이 났다.
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
             # ★`archive` 만 적혀 있어 이 저장소의 실제 이름 `_archive` 가 안 걸렸다
             #   (과거 스냅샷 = 작업 대상 아님 · 루트 CLAUDE.md § 3 이 그렇게 말한다).
             "archive", "_archive", "outputs", "local_data",
             # ★런타임 로그 — 사설 IP 가 찍히는 건 그 서버가 실제로 그 주소였다는
             #   **기록**이지 소스의 하드코딩이 아니다. 지우면 기록이 사라진다(A15).
             "logs",
             # ★RPA 수집 산출물 — 고객 사이트에서 긁어온 **데이터**이지 우리 소스가
             #   아니다. 수집할 때마다 늘어서 숫자가 작업과 무관하게 흔들리고,
             #   받아온 텍스트에 토큰 비슷한 문자열이 있으면 CRITICAL 오탐이 난다.
             "download", "evidence", "highlight",
             # ★벤더가 배포한 런타임(네이버 WASM 바인딩 등) — 고칠 수 없는 코드.
             "rpa_profiles"}

# 경로형 제외(두 칸 이상) — 위 집합과 비교 방식이 다르므로 따로 둔다.
SKIP_PREFIXES = (".claude/state", ".claude/logs", ".claude/context-cache")
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".docx", ".pptx",
            ".xlsx", ".zip", ".tar", ".gz", ".mp4", ".mp3", ".wav", ".sqlite",
            ".db", ".bak", ".pyc", ".pyo", ".ico",
            # ★로그는 «일어난 일»의 기록이다 — `logs/` 밖에 떨어진 것도 있어
            #   확장자로도 막는다(실측 1002: 루트 `test_mock_err.log`).
            ".log", ".err"}


def scan():
    hits = {k: [] for k, _, _ in PATTERNS}
    scanned = 0
    for base, dirs, files in os.walk(ROOT):
        rel = Path(base).relative_to(ROOT).as_posix()
        # skip
        parts = rel.split("/")
        if any(p in SKIP_DIRS for p in parts) or \
                any(rel == p or rel.startswith(p + "/") for p in SKIP_PREFIXES):
            dirs[:] = []
            continue
        for name in files:
            ext = Path(name).suffix.lower()
            if ext in SKIP_EXT:
                continue
            fp = Path(base) / name
            try:
                if fp.stat().st_size > 500_000:
                    continue
                txt = fp.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            scanned += 1
            _is_doc = (ext == ".md")
            for key, pat, _ in PATTERNS:
                # ★문서의 금지 예시 면제 — 단 시크릿 3종은 면제하지 않는다(위 주석).
                if _is_doc and key in DOC_EXEMPT_KEYS:
                    continue
                for m in pat.finditer(txt):
                    lineno = txt.count("\n", 0, m.start()) + 1
                    hits[key].append({
                        "file": fp.relative_to(ROOT).as_posix(),
                        "line": lineno,
                        "match": m.group(0)[:80],
                    })
                    if len(hits[key]) >= 100:
                        break
    return hits, scanned


def main():
    hits, scanned = scan()
    counts = {k: len(v) for k, v in hits.items()}
    total = sum(counts.values())
    critical = counts.get("aws_key", 0) + counts.get("openai_key", 0) + counts.get("github_pat", 0)
    status = "PASS" if total == 0 else ("CRITICAL" if critical else "WARN")
    result = {
        "ts": datetime.now().isoformat(),
        "scanned_files": scanned,
        "status": status,
        "total_hits": total,
        "counts": counts,
        "hits": {k: v[:20] for k, v in hits.items()},  # top 20 per pattern
        "patterns": {k: desc for k, _, desc in PATTERNS},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[audit-hardcoded] {status} - scanned {scanned} - total {total} - critical {critical}")
    print(f"  cache: {OUT.relative_to(ROOT)}")
    for k, n in counts.items():
        if n:
            print(f"  {k}: {n}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[audit-hardcoded] err: {e}", file=sys.stderr)
        sys.exit(1)
