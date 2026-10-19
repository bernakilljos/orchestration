#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
inject-experience — 사용자 프롬프트에 관련된 top 3 검증 경험 자동 주입 (A1).

원칙 (사용자 2026-10-19):
  - "저장된 대화 1,000건보다 교훈 3개 정확히 불러오는 게 유용"
  - 매번 전부 주입 X · 현재 작업과 관련된 검증된 경험 3~5건만

흐름:
  1. 사용자 프롬프트 (stdin JSON) 받음
  2. problem_solutions WHERE verified=1 OR reusable_score>=8 중 키워드 매치 top 3
  3. hit_count·last_hit_ts 업데이트 (활용 추적)
  4. systemMessage 로 출력 (prompt-dispatch 가 자동 수집)

사용:
  echo '{"prompt":"...."}' | python inject-experience.py
  python inject-experience.py --test "공통 CSS 우회"   # 수동 테스트
"""
from __future__ import annotations
import json, os, sqlite3, sys, re
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
)
DB = os.path.join(ROOT, ".claude", "state", "orca.db")


def _extract_keywords(text: str, top_n: int = 5) -> list:
    """프롬프트에서 명사·동사 핵심어 추출 (간단 heuristic)."""
    # 한글 2+ 글자 + 영문 3+ 글자 추출 · 흔한 조사·접속사 제외
    words = re.findall(r"[가-힣]{2,}|[A-Za-z]{3,}", text)
    stop = {"있는", "없는", "이것", "저것", "그것", "되는", "하는", "해줘", "주세요",
            "입니다", "the", "and", "for", "with", "from", "that", "this"}
    words = [w.lower() for w in words if w not in stop]
    # 빈도 · unique 유지 순서
    seen = {}
    for w in words:
        seen[w] = seen.get(w, 0) + 1
    sorted_w = sorted(seen.items(), key=lambda x: -x[1])
    return [w for w, _ in sorted_w[:top_n]]


def _find_experiences(keywords: list, top: int = 3) -> list:
    """verified=1 OR score>=8 solutions 중 키워드 매치 top-K."""
    if not keywords or not os.path.exists(DB):
        return []
    with sqlite3.connect(DB) as c:
        rows = c.execute(
            "SELECT id, problem, solution, category, reusable_score, verified, hit_count "
            "FROM problem_solutions "
            "WHERE verified=1 OR reusable_score >= 8"
        ).fetchall()
    # 각 row 와 키워드 일치 점수
    scored = []
    for r in rows:
        text = ((r[1] or "") + " " + (r[2] or "") + " " + (r[3] or "")).lower()
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scored.append((score, r))
    scored.sort(key=lambda x: (-x[0], -(x[1][4] or 0), -(x[1][6] or 0)))
    return [r for _, r in scored[:top]]


def _update_hits(ids: list) -> None:
    if not ids:
        return
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB) as c:
        for i in ids:
            c.execute(
                "UPDATE problem_solutions SET hit_count = COALESCE(hit_count, 0) + 1, last_hit_ts = ? WHERE id = ?",
                (now, i)
            )


def _render(experiences: list) -> str:
    """systemMessage markdown."""
    if not experiences:
        return ""
    L = ["## 📚 관련 검증 경험 (자동 주입 · verified 또는 score≥8 중 top 3)"]
    for i, (eid, problem, solution, category, score, verified, hits) in enumerate(experiences, 1):
        vcheck = "✅" if verified else "⭐"
        p_short = (problem or "")[:80]
        s_short = (solution or "")[:120]
        L.append(f"{i}. {vcheck} [{category or '?'}] score={score} hits={hits}: {p_short}")
        L.append(f"   → {s_short}")
    L.append("")
    L.append("*이 경험을 참고 · 적용 가능 시 재사용 · 부적합 시 무시*")
    return "\n".join(L)


def main():
    if "--test" in sys.argv:
        idx = sys.argv.index("--test")
        prompt = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""
    else:
        try:
            data = json.load(sys.stdin) if not sys.stdin.isatty() else {}
            prompt = data.get("prompt", "") or data.get("user_prompt", "")
        except Exception:
            prompt = ""
    if not prompt:
        return
    kws = _extract_keywords(prompt)
    exps = _find_experiences(kws, top=3)
    if exps:
        _update_hits([e[0] for e in exps])
    msg = _render(exps)
    if msg:
        # prompt-dispatch 가 수집하는 포맷
        print(json.dumps({"systemMessage": msg}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # 실패 시 침묵 (프롬프트 처리 영향 X)
