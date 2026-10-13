#!/usr/bin/env python3
"""
verify-hook-scope.py ??Hook ?ㅼ퐫??遺꾨━ 寃利?1. ~/.claude/settings.json ??kit hook ?좎텧 媛먯?
2. kit hook script ??[ -d plugins ] guard 議댁옱 ?뺤씤
3. 臾몄젣 ??寃쎄퀬

洹쇨굅: .claude/rules/hook-scope-separation.md
"""
from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

# ?섍꼍 蹂??湲곕컲 ?숈쟻 寃쎈줈
ROOT = Path(__file__).resolve().parent.parent.parent
LOGS = ROOT / ".claude" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

# 濡쒓퉭
LOG_FILE = LOGS / "verify-hook-scope.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Kit hook ?⑦꽩 (?꾨줈?앺듃 ?꾩슜 = plugins/ 愿??
KIT_HOOK_PATTERNS = [
    "exec_orch",
    "detect-user-emotion",
    "ensure-state",
    "load-recent-conversations",
    "save-session-summary",
    "mcp-autostart",
    "websearch-trigger",
    "changelog-check",
    "post-codex-verify",
    "hook-profile",
    "check-mcp-health",
    "verify-hook-scope",
    "cleanup-pollution",
    "pre-install-lock",
    "enforce-file-naming",
    "save-solution",
    "lookup-history",
]


def is_kit_hook(hook_name: str) -> bool:
    """Hook ?대쫫??kit ?꾩슜?몄? ?먯젙."""
    for pattern in KIT_HOOK_PATTERNS:
        if pattern.lower() in hook_name.lower():
            return True
    return False


def check_global_settings() -> list:
    """湲濡쒕쾶 ~/.claude/settings.json ?먯꽌 kit hook ?좎텧 媛먯?."""
    issues = []

    global_settings = Path.home() / ".claude" / "settings.json"
    if not global_settings.exists():
        logger.info("global settings not found (expected for project-only setup)")
        return issues

    try:
        with global_settings.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        logger.error(f"failed to parse global settings: {e}")
        return issues

    # hooks ?뱀뀡 ?뺤씤
    hooks = data.get("hooks", {})
    for event, hook_list in hooks.items():
        if not isinstance(hook_list, list):
            hook_list = [hook_list]

        for hook in hook_list:
            if isinstance(hook, dict):
                hook_name = hook.get("name", hook.get("command", ""))
            else:
                hook_name = str(hook)

            if is_kit_hook(hook_name):
                issues.append(
                    f"[GLOBAL_HOOK_LEAK] {event}: {hook_name} found in ~/.claude/settings.json"
                )
                logger.warning(f"kit hook leaked to global scope: {hook_name}")

    return issues


def check_kit_guard(hook_script: Path) -> bool:
    """kit hook script ??[ -d plugins ] guard 議댁옱 ?뺤씤."""
    if not hook_script.exists() or not hook_script.is_file():
        return True  # ?뚯씪 ?놁쑝硫?臾몄젣 ?꾨떂

    try:
        content = hook_script.read_text(encoding="utf-8")
    except (OSError, IOError, ValueError, KeyError, TypeError, json.JSONDecodeError, AttributeError, FileNotFoundError) as e:
        logger.warning(f"failed to read {hook_script}: {e}")
        return False

    # Guard ?⑦꽩 寃??    guard_patterns = [
        r'\[\s*-d\s+.*plugins\s*\]',  # [ -d plugins ]
        r'\[\s*-d\s+"\${.*}/plugins"\s*\]',  # [ -d "${...}/plugins" ]
        r'plugins_dir.*exit\s+0',  # guard via variable
    ]

    for pattern in guard_patterns:
        if re.search(pattern, content):
            return True

    return False


def scan_kit_hooks() -> list:
    """kit hook script ???꾩닔議곗궗."""
    issues = []

    kit_hook_dir = ROOT / ".claude" / "hooks"
    if not kit_hook_dir.exists():
        logger.info("kit hooks directory not found")
        return issues

    for script in kit_hook_dir.glob("*.sh"):
        # ?ㅽ겕由쏀듃 ?대쫫??kit hook ?몄? ?뺤씤
        if is_kit_hook(script.name):
            if not check_kit_guard(script):
                issues.append(
                    f"[MISSING_GUARD] {script.name} missing [ -d plugins ] guard"
                )
                logger.warning(f"missing guard in {script.name}")

    return issues


def main(verbose: bool = False) -> int:
    """寃利??ㅽ뻾."""
    logger.info("=== verify-hook-scope start ===")

    all_issues = []

    # 1. 湲濡쒕쾶 ?ㅼ젙 ?뺤씤
    logger.info("checking global settings...")
    all_issues.extend(check_global_settings())

    # 2. kit hook guard ?뺤씤
    logger.info("checking kit hooks...")
    all_issues.extend(scan_kit_hooks())

    # 寃곌낵
    if all_issues:
        logger.error(f"found {len(all_issues)} issues:")
        for issue in all_issues:
            logger.error(f"  - {issue}")
            print(f"  - {issue}")
        logger.info("=== done (FAILED) ===")
        return 1
    else:
        logger.info("hook scopes OK (no leaks, all guards present)")
        logger.info("=== done ===")
        return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Verify hook scope separation")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    sys.exit(main(verbose=args.verbose))

