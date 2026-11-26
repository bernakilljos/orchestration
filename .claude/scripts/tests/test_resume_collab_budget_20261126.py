"""resume-last-24h 협업 원격 확인 예산 (11-26 바로잡기 · 대상 lottoclaude 와 같은 계약).
고정 8초를 주면 훅 10초 제한의 여유가 2초뿐이라 시작 훅이 몰릴 때 출력이 버려졌다."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _load():
    spec = importlib.util.spec_from_file_location("resume24_budget_kit", ROOT / ".claude/scripts/resume-last-24h.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_budget_leaves_margin_and_shrinks(monkeypatch):
    r = _load()
    monkeypatch.setattr(r.time, "monotonic", lambda: r._T0)
    assert r._collab_budget() <= 7.0 + 1e-9
    monkeypatch.setattr(r.time, "monotonic", lambda: r._T0 + 4.0)
    assert abs(r._collab_budget() - 3.0) < 1e-9
    monkeypatch.setattr(r.time, "monotonic", lambda: r._T0 + 20.0)
    assert r._collab_budget() == 1.0
