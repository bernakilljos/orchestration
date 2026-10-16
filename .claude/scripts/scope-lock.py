#!/usr/bin/env python
"""
scope-lock.py — 요청 범위 lock CLI.

사용:
  python scope-lock.py activate <glob1> [glob2 ...]  # 활성화
  python scope-lock.py deactivate                    # 비활성화
  python scope-lock.py status                        # 현재 상태
  python scope-lock.py check <file_path>             # 매치 여부 (exit 0=OK, 1=OUT)
  python scope-lock.py mode warn|deny                # 모드 변경

상태 파일: .claude/state/scope-lock.json
자동 만료: 24h (set_at 기준) · 만료 시 inactive 로 간주

왜 opt-in · WARN:
- auto 추출 (사용자 프롬프트에서 "범위 어휘" 자동 뽑기) 는 regex 가 틀리면 cascade (lib·import·sibling) 다 block.
- 1주 WARN 로그 보고 B안 (auto) 로 고도화.
"""
from __future__ import annotations
import fnmatch
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
STATE = ROOT / ".claude" / "state" / "scope-lock.json"
TTL_HOURS = 24


def _load() -> dict:
    if not STATE.exists():
        return {}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(cfg: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def _expired(cfg: dict) -> bool:
    sa = cfg.get("set_at")
    if not sa:
        return False
    try:
        dt = datetime.fromisoformat(sa)
        return (datetime.now() - dt) > timedelta(hours=TTL_HOURS)
    except Exception:
        return False


def _normalize(p: str) -> str:
    try:
        rel = os.path.relpath(p, ROOT)
    except Exception:
        rel = p
    return rel.replace("\\", "/")


def is_active(cfg: dict | None = None) -> bool:
    cfg = cfg if cfg is not None else _load()
    return bool(cfg.get("active") and cfg.get("paths") and not _expired(cfg))


def check(file_path: str) -> tuple[bool, dict]:
    """Return (allowed, cfg). If scope inactive -> allowed=True."""
    cfg = _load()
    if not is_active(cfg):
        return True, cfg
    rel = _normalize(file_path)
    for p in cfg.get("paths", []):
        if fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(rel, p.lstrip("./")):
            return True, cfg
    return False, cfg


def cmd_activate(paths: list[str]) -> int:
    if not paths:
        print("[scope-lock] usage: activate <glob1> [glob2 ...]", file=sys.stderr)
        return 2
    cfg = {
        "active": True,
        "paths": [p.replace("\\", "/") for p in paths],
        "mode": _load().get("mode", "warn"),
        "set_at": datetime.now().isoformat(timespec="seconds"),
        "ttl_hours": TTL_HOURS,
    }
    _save(cfg)
    print(f"[scope-lock] activated · mode={cfg['mode']} · paths={cfg['paths']} · ttl={TTL_HOURS}h")
    return 0


def cmd_deactivate() -> int:
    cfg = _load()
    cfg["active"] = False
    _save(cfg)
    print("[scope-lock] deactivated")
    return 0


def cmd_status() -> int:
    cfg = _load()
    if not cfg:
        print("[scope-lock] no state file")
        return 0
    cfg["_expired"] = _expired(cfg)
    cfg["_active_effective"] = is_active(cfg)
    print(json.dumps(cfg, ensure_ascii=False, indent=2))
    return 0


def cmd_check(file_path: str) -> int:
    allowed, cfg = check(file_path)
    rel = _normalize(file_path)
    if allowed:
        print(f"[scope-lock] OK · {rel}")
        return 0
    print(f"[scope-lock] OUT-OF-SCOPE · {rel} · allowed={cfg.get('paths')}")
    return 1


def cmd_mode(mode: str) -> int:
    if mode not in ("warn", "deny"):
        print("[scope-lock] mode must be warn or deny", file=sys.stderr)
        return 2
    cfg = _load()
    cfg["mode"] = mode
    _save(cfg)
    print(f"[scope-lock] mode={mode}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 0
    op = argv[1]
    rest = argv[2:]
    if op == "activate":
        return cmd_activate(rest)
    if op == "deactivate":
        return cmd_deactivate()
    if op == "status":
        return cmd_status()
    if op == "check":
        if not rest:
            print("[scope-lock] usage: check <file_path>", file=sys.stderr)
            return 2
        return cmd_check(rest[0])
    if op == "mode":
        if not rest:
            print("[scope-lock] usage: mode warn|deny", file=sys.stderr)
            return 2
        return cmd_mode(rest[0])
    print(f"[scope-lock] unknown op: {op}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print(f"[scope-lock] fatal: {e}", file=sys.stderr)
        sys.exit(0)
