"""R364 (2026-11-23) — 상태 변화 없이 같은 경고를 매 프롬프트 반복 주입하던 결함 회귀.

compact 경고(inject_compact_reminder): 구간(60·75·90%)이 바뀔 때만 주입 · 같은 구간이면 조용히.
운영 상태·기록 접촉 0 (임시 USERPROFILE · 임시 프로젝트).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "prompt"))
import inject_compact_reminder as icr  # noqa: E402


class _Ctx:
    def __init__(self, root, payload):
        self.root = Path(root)
        self.payload = payload


def _setup(tmp_path, monkeypatch, tokens):
    home, proj = tmp_path / "home", tmp_path / "proj"
    (proj / "plugins").mkdir(parents=True)
    (proj / ".claude" / "state").mkdir(parents=True)
    (proj / ".claude" / "state" / "context-limit.json").write_text('{"limit": 1000000}', encoding="utf-8")
    pdir = home / ".claude" / "projects" / re.sub(r"[^a-zA-Z0-9]", "-", str(proj))
    pdir.mkdir(parents=True)
    tr = pdir / "s.jsonl"
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(proj))
    monkeypatch.setattr(icr, "_safe_to_clear", lambda root: (None, "시험"))
    _write(tr, tokens)
    return proj, tr


def _write(tr, tokens):
    rec = {"type": "assistant", "message": {"model": "m", "usage": {"input_tokens": tokens}}}
    tr.write_text(json.dumps(rec) + "\n", encoding="utf-8")


def test_compact_notice_only_on_band_change(tmp_path, monkeypatch):
    proj, tr = _setup(tmp_path, monkeypatch, 650_000)
    ctx = _Ctx(proj, {"transcript_path": str(tr), "session_id": "sess-1"})
    assert icr.run(ctx) and "65%" in icr.run(_Ctx(proj, {"transcript_path": str(tr), "session_id": "sess-2"}))
    assert icr.run(ctx) is None                         # 같은 세션·같은 구간 → 반복 주입 X
    _write(tr, 800_000)
    out = icr.run(ctx)
    assert out and "80%" in out                         # 구간 상승 (60→75) → 1회 주입
    assert icr.run(ctx) is None
    _write(tr, 100_000)
    assert icr.run(ctx) is None                         # 60% 미만은 원래 주입 없음
    _write(tr, 650_000)
    assert icr.run(ctx)                                 # 내려갔다 다시 올라오면 다시 1회
