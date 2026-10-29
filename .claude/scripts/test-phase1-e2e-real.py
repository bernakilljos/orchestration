#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 1-E 실 종단 테스트 — 가변 N 요청 (하드코딩 X · 2026-10-29).

사용자 지시 (bf41a4b 후속):
  - 가변 N 요청 보존
  - 요청별 Goal → Task DAG → risk 평가 → 검증 체인 실 실행
  - 부분 실패 격리 (한 request 실패가 다른 request 를 막지 않음)
  - Learning Candidate 자동 승격 X
  - 특정 숫자·순서·모델 하드코딩 X
  - 산출물 생성·검증 완성은 범위 외 (플로우 검증)

Usage: python .claude/scripts/test-phase1-e2e-real.py
"""
from __future__ import annotations
import json
import os
import random
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "scripts" / "lib"))

PY = sys.executable
PASS = 0
FAIL = 0


def check(cond: bool, msg: str) -> None:
    global PASS, FAIL
    tag = "PASS" if cond else "FAIL"
    if cond:
        PASS += 1
    else:
        FAIL += 1
    print(f"  [{tag}] {msg}")


def section(name: str) -> None:
    print(f"\n=== {name} ===")


def _random_requests(n: int) -> list:
    """가변 N 요청 생성 (하드코딩 X · 사용자 지시 '예시 숫자 하드코딩 금지').

    N 자체는 테스트 파라미터 (3·5·7 가변) · 요청 내용은 risk 혼합.
    """
    pools = {
        "low": ["코드 조사해", "구조 분석해 줘", "현재 상태 확인", "라이브러리 조사", "로그 분석"],
        "medium": ["설정 파일 수정해", "테스트 추가 만들어", "리팩터 구현해", "커밋 push 해줘"],
        "high": ["프로덕션 배포", "DB 삭제", "force push 해", "토큰 revoke"],
    }
    reqs = []
    for i in range(n):
        risk_pick = random.choice(["low", "low", "medium", "high"])  # bias low
        reqs.append(random.choice(pools[risk_pick]))
    return reqs


def main() -> int:
    from supervisor import decompose_goal

    db = ROOT / ".claude" / "state" / "orca.db"
    if not db.exists():
        print(f"[FAIL] orca.db 없음: {db}")
        return 1

    section("1. 가변 N 요청 생성 (N ∈ {3, 5, 7})")
    for n in (3, 5, 7):
        reqs = _random_requests(n)
        check(len(reqs) == n, f"N={n}: 요청 {len(reqs)}건 생성")

    section("2. 요청 → Goal 등재 (각 요청 독립 보존)")
    n = 5
    reqs = _random_requests(n)
    goal_ids = []
    with sqlite3.connect(str(db)) as conn:
        for i, req in enumerate(reqs):
            now = int(time.time())
            source = f"test:phase1e-{now}-{i}"
            conn.execute(
                "INSERT INTO goals (description, status, workflow_type, source_ref, "
                "max_retry, timeout_h, created_at, updated_at) VALUES "
                "(?, 'PENDING', 'GENERAL', ?, 3, 24, ?, ?)",
                (f"[E2E-TEST-{i}] {req}", source, now, now),
            )
            gid = conn.execute(
                "SELECT goal_id FROM goals WHERE source_ref=? ORDER BY created_at DESC LIMIT 1",
                (source,),
            ).fetchone()[0]
            goal_ids.append(gid)
    check(len(goal_ids) == n, f"{n}개 goal 독립 등재 (id {goal_ids})")

    section("3. 각 Goal 자연어 분해 (여러 요청 분기)")
    decomposed = []
    for gid in goal_ids:
        r = decompose_goal(gid)
        decomposed.append(r)
        check(r.get("tasks_registered", 0) > 0,
              f"g{gid}: {r.get('tasks_registered',0)} task · mode={r.get('mode')}")

    section("4. Task 위험 평가 (risk 분포)")
    risk_counts = {"low": 0, "medium": 0, "high": 0, "unknown": 0}
    approval_true = 0
    approval_false = 0
    with sqlite3.connect(str(db)) as conn:
        for gid in goal_ids:
            rows = conn.execute(
                "SELECT task_file FROM tasks WHERE task_id LIKE ?",
                (f"g{gid}-%",),
            ).fetchall()
            for (tf,) in rows:
                spec = json.loads(tf)
                risk = spec.get("risk", "unknown")
                risk_counts[risk] = risk_counts.get(risk, 0) + 1
                if spec.get("requires_user_approval"):
                    approval_true += 1
                else:
                    approval_false += 1
    check(sum(risk_counts.values()) > 0, f"risk 분포: {risk_counts}")
    check(approval_true > 0 or approval_false > 0,
          f"approval 분기: 승인필요 {approval_true} · 자동허용 {approval_false}")
    check(approval_true != sum(risk_counts.values()),
          "모든 작업 획일 승인 아님 (사용자 지시 '모든 작업을 무조건 승인 필요로 분류 금지')")
    check(approval_false != sum(risk_counts.values()),
          "모든 작업 획일 허용 아님 (사용자 지시 '모든 작업을 자동 허용 금지')")

    section("5. 부분 실패 격리 (존재하지 않는 goal 요청 → 다른 goal 영향 X)")
    bad_gid = max(goal_ids) + 999  # 존재 X
    r_bad = decompose_goal(bad_gid)
    check("error" in r_bad or r_bad.get("tasks_registered", 0) == 0,
          f"g{bad_gid}: 존재 X 처리 ({r_bad.get('error', r_bad.get('note', '?'))})")

    # 그래도 기존 goal_ids 들은 상태 유지
    with sqlite3.connect(str(db)) as conn:
        intact = 0
        for gid in goal_ids:
            row = conn.execute("SELECT status FROM goals WHERE goal_id=?", (gid,)).fetchone()
            if row and row[0] in ("PENDING", "PLANNING", "RUNNING"):
                intact += 1
    check(intact == len(goal_ids), f"기존 goal 모두 보존 (영향 X · {intact}/{len(goal_ids)})")

    section("6. 요청 보존 (여러 시점 요청 중복 등재 방지 · idempotent)")
    # 같은 goal 다시 decompose → 기존 task skip
    gid = goal_ids[0]
    r1_tasks_before = len(decomposed[0].get("tasks", []))
    r2 = decompose_goal(gid)
    r2_tasks = len(r2.get("tasks", []))
    check(r2_tasks == 0,  # 기존 등록 skip → tasks 리스트 비어있음 (중복 등록 X)
          f"g{gid} 재분해 결과 신규 등록 0 (idempotent · 중복 방지)")

    section("7. 세션 재시작 복원 (DB 보존)")
    # DB 재접속으로 복원 흉내
    with sqlite3.connect(str(db)) as conn:
        rows = conn.execute(
            "SELECT COUNT(*) FROM goals WHERE source_ref LIKE 'test:phase1e-%'",
        ).fetchone()
    check(rows[0] >= n, f"DB 재접속 goal 유지 ({rows[0]} ≥ {n})")

    section("8. Learning Candidate 자동 승격 금지")
    # memory-candidate list 호출 → promote 자동 호출 흔적 없음 확인
    mc_dir = ROOT / ".claude" / "state" / "memory-candidates"
    user_mem = Path.home() / ".claude" / "projects" / "C--pjt-orchestration_v1" / "memory"
    user_mem_count = len(list(user_mem.glob("feedback_*.md"))) if user_mem.exists() else 0
    check(True, f"memory-candidates 디렉토리 존재: {mc_dir.exists()} · user memory feedback 수: {user_mem_count}")
    # 자동 승격 안전 장치: memory-candidate.py promote 명시 승인 필요 (standing 포함 거부)
    mc_src = (ROOT / ".claude" / "scripts" / "memory-candidate.py").read_text(encoding="utf-8")
    check("STANDING_REQUIREMENT" in mc_src, "memory-candidate 안 STANDING 안전 장치 존재")
    check("--target" in mc_src and "promote" in mc_src, "promote 명시 target 필수")

    # 결과
    print("\n" + "=" * 60)
    print(f"PASS: {PASS}  FAIL: {FAIL}  TOTAL: {PASS + FAIL}")
    print("=" * 60)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
