#!/usr/bin/env python3
"""UserPromptSubmit hook 방식 전환 — merged(prompt-dispatch.py 1개) ↔ separate(옛 .sh 13개).

2026-10-12 사용자 지시: "분리된 건 별도로 가지고 있고 · 합쳐서 push · 혹시 모르잖아".
합친 판에 문제가 생기면 이 한 줄로 되돌린다 (옛 .sh 는 지우지 않고 그대로 둔다).

사용: python .claude/scripts/switch-prompt-hooks.py merged|separate|status
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = ROOT / ".claude" / "settings.json"
PRESETS = ROOT / ".claude" / "scripts" / "prompt-hooks-presets.json"


def names(groups):
    return [h["command"].split("/")[-1].strip('"') for m in groups for h in m.get("hooks", [])]


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    sj = json.loads(SETTINGS.read_text(encoding="utf-8-sig"))
    cur = sj.get("hooks", {}).get("UserPromptSubmit", [])
    if mode == "status":
        print("현재:", "merged" if names(cur) == ["prompt-dispatch.py"] else "separate", names(cur))
        return 0
    presets = json.loads(PRESETS.read_text(encoding="utf-8"))
    if mode not in ("merged", "separate"):
        print(__doc__)
        return 2
    sj.setdefault("hooks", {})["UserPromptSubmit"] = presets[mode]
    # 2026-10-14: 도구 hook(PreToolUse·PostToolUse) 도 같이 전환 (tool-dispatch.py ↔ 옛 .sh 들)
    tool = presets.get("tool_" + mode)
    if tool:
        for ev, groups in tool.items():
            sj["hooks"][ev] = groups
    SETTINGS.write_text(json.dumps(sj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"전환 → {mode}: {names(presets[mode])}")
    print("※ 열려 있는 세션은 다음 프롬프트부터 적용")
    return 0


if __name__ == "__main__":
    sys.exit(main())
