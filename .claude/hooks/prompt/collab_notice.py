"""협업 폴더(.ai-collab) 미처리 지시·리뷰를 대기 루프가 꺼져 있을 때만 프롬프트에 알린다.

근거 R375 6차 검토 (2026-11-25) · 실측: 대기 루프(wait)가 메모리 부족으로 꺼진 뒤 새 세션·compact 가 없으면
확인이 아예 돌지 않아 리뷰 3건(20:11·23:51·11:21)을 놓쳤다 (세션 시작 훅만 있었고 프롬프트 경로 없음).
네트워크·git 호출 없음 — 파일 두 개(생존 표시·마지막 확인 결과)만 읽는다. 오래된 결과면 백그라운드 갱신 1개만 띄움.
판정·문구 정본: .claude/scripts/ai-collab-report.py prompt_notice (여기선 불러 쓰기만).
"""
from __future__ import annotations

import importlib.util

from _common import SCRIPTS_DIR


def run(ctx):
    p = SCRIPTS_DIR / "ai-collab-report.py"
    if not p.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_ai_collab_notice", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.prompt_notice() or None
