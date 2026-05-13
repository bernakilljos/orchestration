"""CHAPTERS list 재정렬 — Claude Code 먼저, AI 기초 나중.

build-arch-lecture-doc.py 의 CHAPTERS list 순서 변경 + title 번호 자동 갱신.
"""
import re
from pathlib import Path

LECT = Path(__file__).resolve().parent / "build-arch-lecture-doc.py"

# 새 순서 (이전 # → 새 #) — title prefix (번호 빼고) 매칭
NEW_ORDER = [
    # A 부 — Claude Code 도구 (1~9)
    (".claude 폴더",            18),
    ("CLAUDE.md 설계",          19),
    ("Claude Code 프로젝트",     17),
    ("에이전트 개발킷",          6),
    ("Claude Code 결정트리",     14),
    ("Claude Code 완전 가이드",  15),
    ("Claude Code 아키텍처",     16),
    ("8가지 프롬프트",           20),
    ("Claude 마스터",           13),
    # B 부 — AI 기초·RAG·프로토콜 (10~20)
    ("AI 3종 세트",             1),
    ("AI 에이전트의 8가지",      2),
    ("에이전트의 5가지",         3),
    ("9가지 숨은 함정",          4),
    ("AI 스택 5층",             5),
    ("제로비용 AI",             7),
    ("AI 빌더 도구",            8),
    ("RAG 입문",               9),
    ("RAG 8가지",              10),
    ("API 프로토콜",            11),
    ("MCP vs A2A",             12),
]


def reorder():
    src = LECT.read_text(encoding="utf-8")

    # 1) CHAPTERS list 시작·끝 찾기
    start_match = re.search(r"^CHAPTERS\s*=\s*\[", src, re.MULTILINE)
    if not start_match:
        return {"error": "CHAPTERS list not found"}
    start = start_match.end()

    # bracket 매칭으로 list 끝 찾기
    depth = 1
    pos = start
    while pos < len(src) and depth > 0:
        if src[pos] == '[': depth += 1
        elif src[pos] == ']': depth -= 1
        pos += 1
    end = pos - 1

    body = src[start:end]

    # 2) 각 챕터 dict 분리 (top-level { ... })
    chapters = []
    depth = 0
    cur_start = None
    for i, c in enumerate(body):
        if c == '{':
            if depth == 0:
                cur_start = i
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                chapters.append(body[cur_start:i + 1])
    # 3) 새 순서 — prefix 매칭으로 인덱싱
    reordered = []
    used = set()
    for new_idx, (prefix, old_num) in enumerate(NEW_ORDER, 1):
        match = None
        for j, c in enumerate(chapters):
            if j in used: continue
            # "title": "N. <prefix>..."
            m = re.search(r'"title":\s*"(\d+)\.\s*([^"]+)"', c)
            if m and prefix in m.group(2):
                match = (j, c, m.group(1), m.group(2))
                break
        if match is None:
            return {"error": f"챕터 매칭 실패: {prefix}"}
        j, c, old_n, name = match
        used.add(j)
        # title 번호 갱신: "N. <name>" → "<new_idx>. <name>"
        new_c = re.sub(r'"title":\s*"\d+\.\s*([^"]+)"',
                       f'"title": "{new_idx}. \\1"', c, count=1)
        reordered.append(new_c)

    new_body = ",\n    ".join(reordered) + ","
    new_src = src[:start] + "\n    " + new_body + "\n" + src[end:]
    LECT.write_text(new_src, encoding="utf-8")

    return {"reordered": len(reordered), "expected": len(NEW_ORDER)}


if __name__ == "__main__":
    import json
    r = reorder()
    print(json.dumps(r, ensure_ascii=False, indent=2))
