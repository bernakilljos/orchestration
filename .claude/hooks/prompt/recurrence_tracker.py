"""recurrence_tracker — UserPromptSubmit 시 사용자 프롬프트에서 재발 패턴 매치 → record.

사용자 지시 (2026-10-16): "재발률 = 이미 지시한 rule 중 다시 등장한 비율".
매 사용자 프롬프트에서 아래 pattern 매치 → recurrence-tracker.record() 호출.
자동 승격 (2회=warn, 3회=CLAUDE.md 후보, 5회=hook 후보) 은 record() 내부에서 수행.
"""
from __future__ import annotations
import importlib.util
import os
import re
import sys
from pathlib import Path

from _common import is_loop_prompt_raw

_STATUSLINE_LINE = re.compile(r"[│▒█]")

# 재발 패턴 (디자인·개발·인프라)
PATTERNS = {
    "design": {
        "이모지":          r'이모지|이모티콘|emoji',
        "여백불일치":      r'여백|빈 공간|비어|밋밋|밋밋해|gap\s*불일치|padding\s*다름',
        "버전접미":        r'-v2|-v3|_v2|_v3|final_final|버전\s*접미|v2\s*(만들|파일)',
        "산출물기한":      r'OVERDUE|산출물.*기한|freshness|오래\s*됐|낡은',
        "공통우회디자인":  r'공통\s*컴포넌트|공통\s*CSS|design\s*token.*우회|shadcn.*안\s*씀|antd.*무시',
    },
    "dev": {
        "증명지시":        r'증명해|확인해 봐|검증\s*(했|해)|실측해',
        "미반영":          r'안\s*되었|안\s*됐|안\s*되어있|적용\s*안|효과\s*없|작동\s*안|반영\s*안',
        "전수조사skip":    r'농땡이|대충|장난|제대로.*해|전수조사|다\s*(보지|보시)',
        # R318: «중복 구현» 은 뒤에 금지·회피 말이 붙으면 지시문의 금지 조항이지 재발 지적이 아님
        #   (실측: 지금 필터로도 잡히는 13건이 13/13 "중복 구현 금지·하지 않는다·피했다·최소화·탐지" → REPAIR goal 37·44 를 만듦)
        "공통우회개발":    r'공통\s*(함수|유틸|lib|라이브러리).*우회|기존.*있는데.*새'
                           r'|중복\s*구현(?!\S{0,3}\s*(?:금지|하지|않|말|마|피|최소|탐지|검사|방지|없))',
        "하드코딩":        r'하드\s*코딩|하드코딩|박아|%USERPROFILE%.*안\s*씀',
        "검증생략":        r'검증\s*(안\s*함|skip|생략|없이)|smoke\s*test\s*안',
    },
    "infra": {
        "install순서":     r'install\s*(순서|먼저)|배포\s*전\s*commit',
        "mcp연결":         r'MCP\s*(연결|끊어|실패|재등록)',
    },
}


def _snippet(txt: str, pat: re.Pattern, window: int = 60) -> str:
    m = pat.search(txt)
    if not m:
        return ""
    s = max(0, m.start() - window // 2)
    e = min(len(txt), m.end() + window // 2)
    return txt[s:e].replace("\n", " ")


def run(ctx):
    if not ctx.has_plugins():
        return None
    if is_loop_prompt_raw(ctx.raw):
        return None
    prompt = ctx.prompt_jq()
    if not prompt or len(prompt) < 3:
        return None
    # 2026-11-18 R308: 재발은 «사용자가 직접 쓴 글» 에서만 센다 — 붙여 넣은 검토·지시 글 안의 "검증해야 합니다"·"대충" 과
    #   harness 알림까지 증명지시·전수조사skip 재발로 기록돼 지표가 부풀었다 (실측: ChatGPT 평가문 붙여 넣기 1회 = 증명지시 +1).
    #   정본 = ledger_auto_register 의 붙여 넣은 글 구분 (같은 기준 재사용 · 새 판정 X)
    try:
        import ledger_auto_register as _lar
        if _lar._is_system_notification(prompt):
            return None
        prompt = _lar._split_pasted(prompt)[0]
    except Exception:  # noqa: BLE001 — 구분 실패 시 원래대로 전체를 본다
        pass
    # R309: 복사해 붙인 상태줄 줄은 제외 — 상태줄이 "이모지 33 · 여백 15" 를 보여 주고 그 줄을 붙이면 이모지·여백 재발이 +1 되는
    #   자기 증폭 (소급 실측: 재발 312건 중 68건 · 이모지 18/39 · 여백 18/31 이 상태줄 문구). 구분 문자 │ · 게이지 ▒█ 가 든 줄 = 상태줄
    prompt = "\n".join(ln for ln in prompt.splitlines() if not _STATUSLINE_LINE.search(ln))
    if not prompt or len(prompt) < 3:
        return None
    session_id = ctx.field("session_id", "sessionId", "id")

    # recurrence-tracker.py 동적 import
    scripts_dir = ctx.root / ".claude" / "scripts"
    spec = importlib.util.spec_from_file_location(
        "_recurrence_tracker_cli", scripts_dir / "recurrence-tracker.py"
    )
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception:
        return None

    detected = []
    for category, pats in PATTERNS.items():
        for rule_id, pat_src in pats.items():
            pat = re.compile(pat_src, re.IGNORECASE)
            if pat.search(prompt):
                snip = _snippet(prompt, pat)
                try:
                    res = mod.record(rule_id, category, snip, session_id)
                    detected.append((rule_id, category, res))
                except Exception:
                    pass

    # 아무 패턴도 매치 안되면 조용
    if not detected:
        return None

    # 승격된 것 (promoted_level >= 2 = CLAUDE.md 후보) 만 systemMessage 로 알림
    promoted = [d for d in detected if d[2].get("promoted_level", 0) >= 2]
    # R310 근본 원인 기록 연결: 같은 유형 2회+ 재발 = 원인 미해결 신호 → 이번 이벤트 번호로 원인 기록을 요구 (증상과 원인 분리)
    repeated = [d for d in detected if (d[2].get("total") or 0) >= 2 and d[2].get("event_id")]
    if not promoted and not repeated:
        return None

    lines = []
    if promoted:
        lines.append("[recurrence] 3회+ 재발 감지 — CLAUDE.md 규칙 승격 후보 자동 추가:")
        for rid, cat, res in promoted:
            lines.append(f"  - [{cat}] {rid} · {res.get('total')}회 · level={res.get('promoted_level')}")
        lines.append("  → .claude/state/rule-promotion-candidates.md 참고")
    if repeated:
        lines.append("[recurrence] 재발 — 이번 작업에서 원인을 찾으면 기록 (증상 ≠ 원인 · 증거 없으면 suspected):")
        for rid, cat, res in repeated:
            lines.append(f"  - {rid} {res.get('total')}회 → python .claude/scripts/recurrence-tracker.py root-cause "
                         f"{res['event_id']} --cause \"…\" --evidence \"파일:줄·로그·실행 출력\" --status confirmed --fix \"해결·회귀 시험\"")
        lines.append("  · 해결 검증 뒤: recurrence-tracker.py fix-result <번호> passed --test 파일.py::시험 --evidence \"…\" (시험을 지금 실행 · 실패하면 FIX_FAILED) 또는 failed")
    return {"systemMessage": "\n".join(lines)}
