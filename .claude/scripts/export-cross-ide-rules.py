"""
export-cross-ide-rules — .claude/rules -> Cursor/Windsurf/Copilot 자동 export
실행: python .claude/scripts/export-cross-ide-rules.py
근거: Task 42 - 크로스 IDE 룰 배포
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RULES = ROOT / ".claude" / "rules"


def read_rules(top_n: int = 15) -> str:
    """가장 중요한 rule 파일 top N 통합."""
    if not RULES.exists():
        return ""
    priority = [
        "direction-first.md",
        "failure-mode.md",
        "best-practices.md",
        "d8-no-stubborn.md",
        "consistency.md",
        "no-false-report.md",
        "screen-verify.md",
        "app-ui-standard.md",
        "language-standards.md",
        "production-file-management.md",
        "auto-optimization.md",
        "solution-reuse.md",
        "conversation-history.md",
        "hook-scope-separation.md",
        "subagent-delegation.md",
    ]
    parts = ["# Cross-IDE Rules - from orchestration_v1 kit", ""]
    for name in priority[:top_n]:
        f = RULES / name
        if f.exists():
            parts.append(f"\n## {name}")
            parts.append(f.read_text(encoding="utf-8", errors="replace")[:8000])
    return "\n".join(parts)


def export_cursor(content: str) -> None:
    (ROOT / ".cursorrules").write_text(content, encoding="utf-8")
    cursor_dir = ROOT / ".cursor" / "rules"
    cursor_dir.mkdir(parents=True, exist_ok=True)
    (cursor_dir / "kit-rules.mdc").write_text(
        f"---\ndescription: orchestration_v1 kit 룰 (자동 export)\nglobs:\n  - '**/*'\nalwaysApply: true\n---\n{content}",
        encoding="utf-8",
    )
    print("[ok] .cursorrules + .cursor/rules/kit-rules.mdc")


def export_windsurf(content: str) -> None:
    (ROOT / ".windsurfrules").write_text(content, encoding="utf-8")
    print("[ok] .windsurfrules")


def export_copilot(content: str) -> None:
    dst = ROOT / ".github" / "copilot-instructions.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8")
    print("[ok] .github/copilot-instructions.md")


def export_continue(content: str) -> None:
    dst = ROOT / ".continue" / "config.json"
    # Continue.dev uses JSON config with "rules" or "systemMessage"
    import json
    cfg = {"models": [], "systemMessage": content[:6000]}
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[ok] .continue/config.json")


def main() -> int:
    content = read_rules(top_n=15)
    if not content:
        print("[skip] .claude/rules 없음")
        return 1
    export_cursor(content)
    export_windsurf(content)
    export_copilot(content)
    export_continue(content)
    print(f"[done] 4 IDE export 완료 - {len(content)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
