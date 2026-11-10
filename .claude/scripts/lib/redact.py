"""비밀정보 가림 정본 (2026-11-10 · §64).

종전에는 Ledger 훅(hooks/prompt/ledger_auto_register.py) 안에만 있어서, 대화 기록(orca.db conversations)·
세션 DB(sessions.db prompts·tool_calls)·bash 명령 로그는 토큰을 그대로 저장했다 (kit 안 토큰 사본 6파일 · §63).
같은 정규식을 여기 한 곳에 두고 네 기록 경로가 함께 쓴다. 해시·판정은 호출자가 가리기 전 원문으로 한다.
"""
from __future__ import annotations

import re

MASK = "[MASKED]"

# secret-scan.sh · tool/block_tricks.py 와 같은 계열 (키=값 은 줄 끝까지)
SECRET_RE = re.compile(r"(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|glpat-[A-Za-z0-9_-]{16,}"
                       r"|AIza[0-9A-Za-z_-]{30,}|npm_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|xox[abpr]-[A-Za-z0-9-]{10,}"
                       r"|eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*|(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}"
                       r"|[a-z][a-z0-9+.-]*://[^\s:/@]+:[^\s@]+@"
                       r"|sk_(?:live|test)_[A-Za-z0-9]{16,}|[rp]k_live_[A-Za-z0-9]{16,}|gh[soru]_[A-Za-z0-9]{20,}"
                       r"|(?:bearer|basic|token)\s+[A-Za-z0-9._~+/=-]{8,}|xox[a-z]-[A-Za-z0-9-]{10,}|ya29\.[A-Za-z0-9._-]{10,}"
                       r"|hf_[A-Za-z0-9]{20,}|pypi-[A-Za-z0-9_-]{20,}|dckr_pat_[A-Za-z0-9_-]{16,}|shpat_[A-Za-z0-9]{16,}"
                       r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
                       r"|[\"']?(?:password|passwd|passphrase|pwd|pw|token|secret|api[_-]?key|apikey|key|credential|auth"
                       r"|authorization|aws_secret_access_key|비밀번호|비번|암호)[\"']?\s*[:=：＝]\s*\S.*"
                       r"|--(?:password|passwd|token|api-key)[\s=]+\S+"
                       r"|(?<![A-Za-z])(?:passphrase|apikey|비밀번호|비번)\s+\S.*)", re.I)


def mask(text):
    """문자열의 비밀정보를 [MASKED] 로 바꾼다. 문자열이 아니면 그대로 돌려준다 (None 포함)."""
    if not isinstance(text, str):
        return text
    return SECRET_RE.sub(MASK, text)
