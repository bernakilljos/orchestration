"""CLAUDE.md 자동 업데이트 — 새 plugin/rule/skill 추가 시 § 4 핵심 경로 표 갱신.

PostToolUse hook 트리거: new plugin.json 생성·rule 추가 시 자동.
"""
import sys
import json
from pathlib import Path
from datetime import date

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"


def collect_stats():
    stats = {
        "plugins_stable": 0,
        "plugins_spec": 0,
        "rules": 0,
        "skills": 0,
        "hooks": 0,
        "scripts": 0,
    }
    for p in (PROJECT_ROOT / "plugins").iterdir():
        if p.is_dir() and not p.name.startswith("_"):
            pj = p / "plugin.json"
            if pj.exists():
                try:
                    data = json.loads(pj.read_text(encoding="utf-8"))
                    if data.get("status") == "stable":
                        stats["plugins_stable"] += 1
                    elif data.get("status") == "spec-only":
                        stats["plugins_spec"] += 1
                except Exception:
                    pass
    stats["rules"] = len(list((PROJECT_ROOT / ".claude" / "rules").glob("*.md")))
    stats["hooks"] = len(list((PROJECT_ROOT / ".claude" / "hooks").glob("*.sh"))) + \
                    len(list((PROJECT_ROOT / ".claude" / "hooks").glob("*.py")))
    stats["scripts"] = len(list((PROJECT_ROOT / ".claude" / "scripts").glob("*.py"))) + \
                       len(list((PROJECT_ROOT / ".claude" / "scripts").glob("*.sh")))
    return stats


def update():
    if not CLAUDE_MD.exists():
        return {"updated": False, "error": "CLAUDE.md not found"}
    stats = collect_stats()
    content = CLAUDE_MD.read_text(encoding="utf-8")
    today = date.today().isoformat()

    # § 1 WHAT 안 stats 줄 자동 갱신 (있으면 교체, 없으면 추가)
    marker = "<!-- AUTO-STATS -->"
    stats_block = f"""{marker}
> **현재 상태** ({today}): plugins {stats['plugins_stable']} stable + {stats['plugins_spec']} spec-only · rules {stats['rules']} · hooks {stats['hooks']} · scripts {stats['scripts']}
{marker}"""

    if marker in content:
        # 기존 marker 블록 교체
        import re
        content = re.sub(
            f"{marker}.*?{marker}",
            stats_block,
            content,
            count=1,
            flags=re.DOTALL,
        )
    else:
        # § 1 WHAT 다음에 삽입
        idx = content.find("## 1. WHAT")
        if idx >= 0:
            next_section = content.find("\n## ", idx + 5)
            insert_pos = next_section if next_section > 0 else len(content)
            content = content[:insert_pos] + f"\n\n{stats_block}\n" + content[insert_pos:]

    CLAUDE_MD.write_text(content, encoding="utf-8")
    return {"updated": True, "stats": stats, "date": today}


if __name__ == "__main__":
    result = update()
    print(json.dumps(result, ensure_ascii=False, indent=2))
