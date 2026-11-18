"""R308 재발 감지는 사용자가 직접 쓴 글만 — 붙여 넣은 검토·지시 글과 harness 알림은 재발로 세지 않는다."""
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "prompt"))


class _Ctx:
    def __init__(self, prompt, root):
        self.raw = json.dumps({"prompt": prompt, "session_id": "r308"})
        self._p = prompt
        self.root = root

    def has_plugins(self):
        return True

    def prompt_jq(self):
        return self._p

    def field(self, *names):
        return "r308"


def _detect(prompt, monkeypatch, tmp_path):
    rt = importlib.import_module("recurrence_tracker")
    seen = []
    real_exec = importlib.util.spec_from_file_location

    def fake_spec(name, path):  # recurrence-tracker.py 의 record 만 가로채 실제 DB 에 쓰지 않음
        spec = real_exec(name, path)
        orig = spec.loader.exec_module

        def exec_module(mod):
            orig(mod)
            mod.record = lambda rid, cat, snip, sid: seen.append(rid) or {"promoted_level": 0}
        spec.loader.exec_module = exec_module
        return spec
    monkeypatch.setattr(rt.importlib.util, "spec_from_file_location", fake_spec)
    rt.run(_Ctx(prompt, ROOT))
    return seen


def test_own_complaint_counts(monkeypatch, tmp_path):
    assert "전수조사skip" in _detect("넌 속도개선을 대충하는구나", monkeypatch, tmp_path)


def test_pasted_review_does_not_count(monkeypatch, tmp_path):
    p = '<pasted_content id="ab12">\n이미지 기반 테스트와 설치 과정이 영향을 받지 않는지 검증해야 합니다. 대충 넘기면 안 됩니다.\n</pasted_content id="ab12">'
    assert _detect(p, monkeypatch, tmp_path) == []


def test_own_text_with_paste_counts_only_own(monkeypatch, tmp_path):
    p = '<pasted_content id="cd34">\n검증해야 합니다. 하드코딩 금지.\n</pasted_content id="cd34">\n\n이거 반영 안 됐잖아'
    assert _detect(p, monkeypatch, tmp_path) == ["미반영"]


def test_harness_notification_does_not_count(monkeypatch, tmp_path):
    p = "<task-notification>\n<summary>시험 검증해 완료 · 대충</summary>\n</task-notification>"
    assert _detect(p, monkeypatch, tmp_path) == []
