"""CLAUDE.md ?먮룞 ?낅뜲?댄듃 ????plugin/rule/skill 異붽? ??짠 4 ?듭떖 寃쎈줈 ??媛깆떊.

PostToolUse hook ?몃━嫄? new plugin.json ?앹꽦-rule 異붽? ???먮룞.
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
                except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError):
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

    # 짠 1 WHAT ??stats 以??먮룞 媛깆떊 (?덉쑝硫?援먯껜, ?놁쑝硫?異붽?)
    marker = "<!-- AUTO-STATS -->"
    stats_block = f"""{marker}
> **?꾩옱 ?곹깭** ({today}): plugins {stats['plugins_stable']} stable + {stats['plugins_spec']} spec-only - rules {stats['rules']} - hooks {stats['hooks']} - scripts {stats['scripts']}
{marker}"""

    if marker in content:
        # 湲곗〈 marker 釉붾줉 援먯껜
        import re
        content = re.sub(
            f"{marker}.*?{marker}",
            stats_block,
            content,
            count=1,
            flags=re.DOTALL,
        )
    else:
        # 짠 1 WHAT ?ㅼ쓬???쎌엯
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

