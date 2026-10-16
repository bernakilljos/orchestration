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
        "공통우회개발":    r'공통\s*(함수|유틸|lib|라이브러리).*우회|기존.*있는데.*새|중복\s*구현',
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
    if not promoted:
        return None

    lines = ["[recurrence] 3회+ 재발 감지 — CLAUDE.md 규칙 승격 후보 자동 추가:"]
    for rid, cat, res in promoted:
        lines.append(f"  - [{cat}] {rid} · {res.get('total')}회 · level={res.get('promoted_level')}")
    lines.append("  → .claude/state/rule-promotion-candidates.md 참고")
    return {"systemMessage": "\n".join(lines)}
