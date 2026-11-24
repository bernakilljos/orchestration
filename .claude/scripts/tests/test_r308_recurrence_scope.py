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


def test_copied_statusline_lines_do_not_count(monkeypatch, tmp_path):
    """R309 상태줄을 복사해 붙인 줄의 라벨(이모지·여백·하드코딩)은 재발이 아님 · 같은 메시지의 직접 쓴 불만은 그대로 셈."""
    p = ("  🎨 디자인  │ 기한 17 · 이모지 33 · 여백 15 · 버전 2 · 재발 48%\n"
         "  📡 인프라  │ cache 98% · [!] 하드코딩 17\n"
         "이거 또 이모지 넣었네")
    assert _detect(p, monkeypatch, tmp_path) == ["이모지"]
    assert _detect("  🎨 디자인  │ 이모지 33 · 여백 15", monkeypatch, tmp_path) == []


def test_r371_d7_same_notice_once_per_session(monkeypatch, tmp_path):
    """R364 D7: 같은 재발은 기록은 매번 · 알림은 세션·규칙·승격 단계별 1번만 (단계가 오르면 다시 알림)."""
    import shutil
    (tmp_path / ".claude" / "scripts").mkdir(parents=True)
    shutil.copy(ROOT / ".claude" / "scripts" / "recurrence-tracker.py", tmp_path / ".claude" / "scripts")
    rt = importlib.import_module("recurrence_tracker")
    level = {"v": 1}
    calls = []
    real_exec = importlib.util.spec_from_file_location

    def fake_spec(name, path):
        spec = real_exec(name, path)
        orig = spec.loader.exec_module

        def exec_module(mod):
            orig(mod)
            mod.record = lambda rid, cat, snip, sid: calls.append(rid) or {
                "promoted_level": level["v"], "total": 5, "event_id": 7}
        spec.loader.exec_module = exec_module
        return spec
    monkeypatch.setattr(rt.importlib.util, "spec_from_file_location", fake_spec)
    msg = "넌 속도개선을 대충하는구나"
    assert rt.run(_Ctx(msg, tmp_path))                 # 첫 알림
    assert rt.run(_Ctx(msg, tmp_path)) is None         # 같은 세션 같은 단계 → 알림 X
    assert len(calls) == 2                             # 기록은 두 번 다
    level["v"] = 2
    assert rt.run(_Ctx(msg, tmp_path))                 # 승격 단계 상승 → 다시 알림
