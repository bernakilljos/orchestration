"""UserPromptSubmit 훅 모듈 — 관련 검증 경험 top 3 자동 주입 (A1 · 2026-10-19).

이 모듈은 .claude/scripts/inject-experience.py 와 같은 로직 (성능 위해 직접 수행).
결과: dict {"systemMessage": "..."} · prompt-dispatch 가 수집·병합.
"""
from __future__ import annotations
import re
import sqlite3
from datetime import datetime

from _common import Ctx, ROOT


DB = ROOT / ".claude" / "state" / "orca.db"


def _extract_keywords(text, top_n=5):
    words = re.findall(r"[가-힣]{2,}|[A-Za-z]{3,}", text or "")
    stop = {"있는", "없는", "이것", "저것", "그것", "되는", "하는", "해줘", "주세요",
            "입니다", "the", "and", "for", "with", "from", "that", "this"}
    words = [w.lower() for w in words if w not in stop]
    seen = {}
    for w in words:
        seen[w] = seen.get(w, 0) + 1
    sorted_w = sorted(seen.items(), key=lambda x: -x[1])
    return [w for w, _ in sorted_w[:top_n]]


def _find_experiences(keywords, top=3, current_project=None):
    """프로젝트 격리 (2026-10-19 #4):
       - PROMOTED/CORE 는 전역 공유
       - 그 외 verified+score≥8 은 current_project 와 연관된 것만 (session_id 접두 매칭)
    """
    if not keywords or not DB.exists():
        return []
    try:
        with sqlite3.connect(str(DB)) as c:
            rows = c.execute(
                "SELECT id, problem, solution, category, reusable_score, verified, hit_count, session_id, experience_type "
                "FROM problem_solutions "
                "WHERE (verified=1 OR reusable_score >= 8) "
                "AND (experience_type IS NULL OR experience_type NOT IN ('ARCHIVED','STALE'))"
            ).fetchall()
    except Exception:
        return []
    # 프로젝트 격리 (defect #2 fix 2026-10-26 · 사용자 명시 "소속 불명 통과 방지"):
    #   PROMOTED/CORE = 전역 공유 (CORE 승격 전 적합성 전제)
    #   verified=1 = 전역 공유 (검증된 지식 교차 재사용)
    #   verified=0 + 소속 불명 (session_id 비어있음) = SKIP
    #   verified=0 + 다른 프로젝트 marker 포함 = SKIP
    #   verified=0 + 소속 현재 프로젝트 = PASS
    other_project_markers = set()
    cp_lower = (str(current_project) if current_project else "").lower()
    if "ifrs" in cp_lower:
        other_project_markers = {"icmai", "icm", "orchestration"}
        own_markers = {"ifrs"}
    elif "icmai" in cp_lower or "/icm" in cp_lower:
        other_project_markers = {"ifrs", "orchestration"}
        own_markers = {"icmai", "icm"}
    elif "orchestration" in cp_lower:
        other_project_markers = {"ifrs", "icmai", "icm"}
        own_markers = {"orchestration"}
    else:
        own_markers = set()
    scored = []
    for r in rows:
        text = ((r[1] or "") + " " + (r[2] or "") + " " + (r[3] or "")).lower()
        s = sum(1 for kw in keywords if kw in text)
        if s == 0:
            continue
        exp_type = r[8] or ""
        session = (r[7] or "").lower()
        verified_flag = r[5] or 0
        is_core = exp_type in ("PROMOTED", "CORE")
        if is_core:
            # CORE 승격 적합성 전제 (승격 자체가 공유 승인)
            scored.append((s, r))
            continue
        if verified_flag == 1:
            # 검증된 지식은 전역 (단 명시된 다른 프로젝트 marker 는 제외)
            if any(m in session or m in text for m in other_project_markers):
                continue
            scored.append((s, r))
            continue
        # verified=0 : strict project match 필요
        if not current_project:
            # current_project 모름 → verified 아닌 경험 skip (안전)
            continue
        if any(m in session or m in text for m in other_project_markers):
            continue
        # 자기 프로젝트 marker 포함 or kit (orchestration) 공통일 때만 통과
        if own_markers and any(m in session or m in text for m in own_markers):
            scored.append((s, r))
            continue
        # 소속 불명 (own_markers 매치 X · other 매치 X) → skip (defect #2 fix)
        continue
    scored.sort(key=lambda x: (-x[0], -(x[1][4] or 0), -(x[1][6] or 0)))
    return [r for _, r in scored[:top]]


def _update_hits(ids):
    if not ids:
        return
    now = datetime.now().isoformat(timespec="seconds")
    try:
        with sqlite3.connect(str(DB)) as c:
            for i in ids:
                c.execute(
                    "UPDATE problem_solutions SET hit_count = COALESCE(hit_count, 0) + 1, "
                    "last_hit_ts = ? WHERE id = ?", (now, i)
                )
    except Exception:
        pass


def run(ctx: Ctx):
    prompt = ctx.payload.get("prompt", "") or ctx.payload.get("user_prompt", "")
    if not prompt or len(prompt) < 10:
        return None
    kws = _extract_keywords(prompt)
    # 프로젝트 격리: 현재 project_dir 전달
    exps = _find_experiences(kws, top=3, current_project=ctx.project_dir)
    if not exps:
        return None
    _update_hits([e[0] for e in exps])
    # defect #3 fix 2026-10-26 — 검증 전 vs 검증된 경험 명시 구분
    L = ["## 📚 관련 경험 (A1 자동 주입 · [검증완료]/[후보] 명시 · 프로젝트 격리 적용)"]
    for i, row in enumerate(exps, 1):
        eid, problem, solution, category, score, verified, hits = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
        exp_type = row[8] if len(row) > 8 else None
        if exp_type in ("PROMOTED", "CORE"):
            status_tag = "[CORE 승격]"
        elif verified:
            status_tag = "[검증완료 ✅]"
        else:
            status_tag = "[후보 ⭐ 미검증]"
        p_short = (problem or "")[:80].replace("\n", " ")
        s_short = (solution or "")[:120].replace("\n", " ")
        L.append(f"{i}. {status_tag} [{category or '?'}] score={score} hits={hits}: {p_short}")
        if s_short.strip():
            L.append(f"   → {s_short}")
    L.append("")
    L.append("*적용 시 `python .claude/scripts/mark-applied.py <id>` · 후보 는 참고만 · 검증완료만 적극 재사용*")
    return "\n".join(L)
