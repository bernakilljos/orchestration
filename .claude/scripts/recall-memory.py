"""Memory 자동 검색·로드 — 사용자 메시지 → 관련 feedback memory 추출.

UserPromptSubmit hook 에 통합:
1. 사용자 메시지 키워드 추출
2. ~/.claude/projects/<proj>/memory/feedback_*.md 검색
3. 매칭 memory description 추출 → systemMessage 주입

목적: Memory 가 있어도 Claude 가 잊는 문제 해결 (5 핵심 부품 중 #4 Memory 보완).
"""
import sys
import re
import json
from pathlib import Path

# project memory dir 자동 감지
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_NAME = PROJECT_ROOT.name  # "orchestration_v1"
# Claude Code 의 project memory 경로 — C:--pjt-orchestration-v1 형식
# Claude Code project memory 경로 자동 검색 — `_` ↔ `-` 변환
def _candidate_memory_dirs():
    # `orchestration_v1` → `orchestration-v1` 변환 (Claude Code 의 path → dir 정규화)
    proj_normalized = PROJECT_NAME.replace("_", "-")
    base = Path.home() / ".claude" / "projects"
    if base.exists():
        for sub in base.iterdir():
            if sub.is_dir() and proj_normalized in sub.name:
                mem = sub / "memory"
                if mem.exists():
                    yield mem

MEMORY_DIR_CANDIDATES = list(_candidate_memory_dirs()) or [
    Path.home() / ".claude" / "memory",
]


def find_memory_dir() -> Path:
    for d in MEMORY_DIR_CANDIDATES:
        if d.exists():
            return d
    return None


def parse_frontmatter(content: str) -> dict:
    """YAML frontmatter 추출."""
    m = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def extract_keywords(message: str) -> set:
    """사용자 메시지 → 핵심 키워드 추출."""
    # 한글 2글자+, 영어 3글자+ 단어 추출
    words = set()
    words.update(re.findall(r"[가-힣]{2,}", message))
    words.update(w.lower() for w in re.findall(r"[a-zA-Z]{3,}", message))
    return words


def score_memory(mem_content: str, keywords: set) -> int:
    """memory 내용 vs 키워드 매칭 점수."""
    fm = parse_frontmatter(mem_content)
    desc = fm.get("description", "") + " " + fm.get("name", "")
    desc_lower = desc.lower()
    score = 0
    for kw in keywords:
        if kw.lower() in desc_lower:
            score += 3  # description 매칭은 더 가중
        elif kw.lower() in mem_content.lower():
            score += 1
    return score


def recall(message: str, top_n: int = 3) -> list:
    """사용자 메시지 → 관련 memory top N."""
    mem_dir = find_memory_dir()
    if mem_dir is None:
        return []
    keywords = extract_keywords(message)
    if not keywords:
        return []
    matches = []
    for mf in mem_dir.glob("feedback_*.md"):
        try:
            content = mf.read_text(encoding="utf-8")
        except Exception:
            continue
        score = score_memory(content, keywords)
        if score > 0:
            fm = parse_frontmatter(content)
            matches.append({
                "file": mf.name,
                "name": fm.get("name", mf.stem),
                "description": fm.get("description", "")[:200],
                "score": score,
            })
    matches.sort(key=lambda x: -x["score"])
    return matches[:top_n]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        if not sys.stdin.isatty():
            msg = sys.stdin.read().strip()
        else:
            print("usage: recall-memory.py '<사용자 메시지>'")
            sys.exit(2)
    else:
        msg = " ".join(sys.argv[1:])
    results = recall(msg)
    print(json.dumps(results, ensure_ascii=False, indent=2))
