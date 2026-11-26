"""resume-last-24h 협업 미처리 읽기 (11-27 바로잡기 · kit·대상 같은 계약).
11-26 은 fetch+ls-remote 만 남은 시간 안에 넣었지만 그 뒤 git·map 호출이 무제한이라 11-27 00:36 에 또 10.9초로
훅 출력이 버려졌다 → 세션 시작 훅은 원격을 보지 않고 마지막 확인 결과(ai-collab-pending.json)만 읽는다."""
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _setup(tmp_path, monkeypatch, cache):
    r = _load("resume24_cache", ".claude/scripts/resume-last-24h.py")
    ac = _load("ai_collab_cache", ".claude/scripts/ai-collab-report.py")
    pc = tmp_path / "pending.json"
    if cache is not None:
        pc.write_text(cache if isinstance(cache, str) else json.dumps(cache), encoding="utf-8")
    monkeypatch.setattr(ac, "PENDING_CACHE", pc)
    calls = []

    def no_net(*a, **k):
        raise AssertionError("세션 시작 경로에서 원격·git 호출")
    monkeypatch.setattr(ac, "pending_lines", no_net)
    monkeypatch.setattr(ac.subprocess, "run", no_net)
    monkeypatch.setattr(ac, "_spawn_refresh", lambda spawn=None: calls.append(1) or True)
    return r, ac, calls


def _at(sec_ago):
    return (datetime.now(timezone.utc) - timedelta(seconds=sec_ago)).isoformat(timespec="seconds")


def test_fresh_cache_no_network_no_refresh(tmp_path, monkeypatch):
    r, ac, calls = _setup(tmp_path, monkeypatch, {"at": _at(60), "ok": True, "lines": ["- 리뷰 R1: x"]})
    assert r._collab_cached(ac) == ["- 리뷰 R1: x"]
    assert calls == []


def test_fresh_empty_cache_is_empty(tmp_path, monkeypatch):
    r, ac, calls = _setup(tmp_path, monkeypatch, {"at": _at(60), "ok": True, "lines": []})
    assert r._collab_cached(ac) == [] and calls == []


def test_stale_cache_spawns_refresh_and_says_age(tmp_path, monkeypatch):
    r, ac, calls = _setup(tmp_path, monkeypatch, {"at": _at(3600), "ok": True, "lines": ["- 지시 R2: 미처리"]})
    out = r._collab_cached(ac)
    assert calls == [1]
    assert out[-1] == "- 지시 R2: 미처리" and "60분 전" in out[0]


def test_missing_or_broken_cache_is_unknown_not_empty(tmp_path, monkeypatch):
    for cache in (None, "{broken", {"at": _at(10), "ok": True}):
        r, ac, calls = _setup(tmp_path, monkeypatch, cache)
        out = r._collab_cached(ac)
        assert out and "UNKNOWN" in out[0], cache
        assert calls == [1]


def test_failed_remote_check_is_unknown(tmp_path, monkeypatch):
    r, ac, calls = _setup(tmp_path, monkeypatch, {"at": _at(60), "ok": False, "lines": []})
    out = r._collab_cached(ac)
    assert any("UNKNOWN" in x for x in out)
