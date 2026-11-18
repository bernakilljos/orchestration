"""R274·R275 (2026-11-16): 원장 미등록 분류 · 영향 의존 · 공통화 4항목 · 추측수정 · 디자인 검증(Golden Baseline·
Visual Quality Gate·Design Ownership Lock·Anti-Ping-Pong 연결). 위반 주입 → 탐지 · 정상 → 오탐 없음 · 기록 없음 → 미측정."""
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[3]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


SL = _load("sl_r275", KIT / ".claude/scripts/statusline_context.py")


def test_r274_do_first_messages_register_as_execute():
    m = _load("lar_r274", KIT / ".claude/hooks/prompt/ledger_auto_register.py")
    cases = {"이거 다하고 한번에 보고하라고 몇번이나 말해": "execute", "이어서할일 다 끝내고... 이것까지 해서 다시 보고해": "execute",
             "이것까지 하고 fifo로 해서 다 되면 다시 보고해": "execute", "다시 보고해줘 짤려서": "report_request",
             "다시보고해줘": "report_request", "지금 상태 어때": "status", "몇 건 남았어": "status", "왜 이래": "status"}
    for text, want in cases.items():
        assert m._classify(text) == want, text


def test_r275_impact_counts_real_references(tmp_path):
    s = tmp_path / ".claude" / "scripts"
    s.mkdir(parents=True)
    (s / "core_mod.py").write_text("X = 1\n", encoding="utf-8")
    (s / "user_a.py").write_text("import core_mod\n", encoding="utf-8")
    (s / "user_b.sh").write_text("python core_mod.py\n", encoding="utf-8")
    (s / "other.py").write_text("print('core_modx')\n", encoding="utf-8")   # 다른 이름 (경계) → 제외
    (tmp_path / ".claude" / "state").mkdir()
    assert SL._impact_compute(str(tmp_path), [".claude/scripts/core_mod.py"]) == 2
    assert SL._impact_dependents(str(tmp_path), [".claude/scripts/core_mod.py"]) == "의존 2"   # 캐시 경로
    assert SL._impact_dependents(str(tmp_path), ["docs/a.md"]) == "의존 해당없음"


def test_impact_cache_miss_returns_fast_and_spawns_once(tmp_path, monkeypatch):
    """2026-11-18: 캐시가 없으면 렌더 안에서 세지 않고 백그라운드 1개만 띄우고 «⏳» (종전: 렌더마다 1.5초 · 상태줄 1.8~2.0초)."""
    s = tmp_path / ".claude" / "scripts"
    s.mkdir(parents=True)
    (s / "core_mod.py").write_text("X = 1\n", encoding="utf-8")
    (tmp_path / ".claude" / "state").mkdir()
    calls = []
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: calls.append(a))
    t0 = time.time()
    r1 = SL._impact_dependents(str(tmp_path), [".claude/scripts/core_mod.py"])
    r2 = SL._impact_dependents(str(tmp_path), [".claude/scripts/core_mod.py"])   # 잠금 중 → 다시 안 띄움
    assert "⏳" in r1 and "⏳" in r2 and "의존" not in r1
    assert len(calls) == 1 and "--impact-worker" in calls[0][0]
    assert time.time() - t0 < 0.5


def test_r275_reuse_metrics_detect_reuse_bypass_dup_new(tmp_path, monkeypatch):
    (tmp_path / ".claude" / "state").mkdir(parents=True)
    comp = tmp_path / "src" / "components"
    comp.mkdir(parents=True)
    (comp / "Button.vue").write_text("<template/>", encoding="utf-8")
    pages = tmp_path / "src" / "pages"
    pages.mkdir()
    (pages / "Button.vue").write_text("<style>.a{color:red;margin:0 auto}</style>", encoding="utf-8")   # 공통과 같은 이름 = 우회
    (pages / "Home.vue").write_text("import B from '../components/Button.vue'\n<style>.b{margin:0 auto;color:red}</style>",
                                    encoding="utf-8")                                                  # 재사용 + 같은 선언 = 중복
    (comp / "Card.vue").write_text("<template/>", encoding="utf-8")
    monkeypatch.setattr(SL, "_git_new_files", lambda cwd: {"src/components/Card.vue"})
    files = ["src/pages/Button.vue", "src/pages/Home.vue", "src/components/Card.vue"]
    out = SL._reuse_metrics(str(tmp_path), files)
    assert "재사용 1" in out and "우회 1" in out and "CSS중복 1" in out and "신규공통 1" in out, out
    assert "UI 변경 없음" in SL._reuse_metrics(str(tmp_path), ["a.py"])
    assert "⏳" in SL._reuse_metrics(str(tmp_path), None)                     # git 실패 = 미측정 (0 아님)


def test_r275_guess_edits_counts_edits_without_prior_look():
    now = time.time()
    ev = lambda ts, step, inp: json.dumps({"kind": "tool", "ts": ts, "step": step, "detail": json.dumps({"input": inp})})
    lines = [ev(now - 100, "Read", "C:\\p\\a.py"), ev(now - 90, "Edit", "C:\\p\\a.py"),       # 읽고 수정 → 정상
             ev(now - 80, "Edit", "C:\\p\\b.py"),                                             # 안 보고 수정 → 추측
             ev(now - 70, "Bash", "grep -n x c.py"), ev(now - 60, "Edit", "C:\\p\\c.py"),     # 검색 후 수정 → 정상
             ev(now - 9000, "Read", "C:\\p\\d.py"), ev(now - 50, "Edit", "C:\\p\\d.py")]     # 2시간 넘은 읽기 → 추측
    assert SL._guess_edits(lines, now - 86400) == 2
    assert SL._guess_edits([], now - 86400) is None                                          # 기록 없음 = 미측정


def test_r275_control_line_shows_unauthorized_and_guess(tmp_path):
    logs = tmp_path / ".claude" / "logs"
    logs.mkdir(parents=True)
    t = time.strftime("%Y-%m-%d %H:%M:%S")
    (logs / "design-gate.log").write_text(f"[{t}] UNAUTHORIZED statusline · 1줄 왼쪽 라벨\n[{t}] PASS statusline · ok\n",
                                          encoding="utf-8")
    now = time.time()
    (logs / "trace-events.jsonl").write_text(json.dumps({"kind": "tool", "ts": now, "step": "Edit",
                                                         "detail": json.dumps({"input": "x.py"})}) + "\n", encoding="utf-8")
    line = SL._control_line(str(tmp_path))
    assert "임의변경 1" in line and "추측수정 1" in line
    empty = tmp_path / "e"
    (empty / ".claude").mkdir(parents=True)
    line2 = SL._control_line(str(empty))
    assert "임의변경 미측정" in line2 and "추측수정 미측정" in line2


@pytest.fixture()
def dg(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    m = _load("dg_r275", KIT / ".claude/scripts/design-gate.py")
    monkeypatch.setattr(m, "_ping_pong", lambda: "ok")
    return m


SAMPLE = ("  🧠️ 토큰    │ 50%\n  🎨️ 디자인  │ 기한 0 ▶   💻️ 개발    │ R1\n  🛑️ 통제    │ 승인차단 1 ▶   ✅️ 검증    │ test 1\n"
          "  🔐️ 증명    │ git 1\n  📡️ 인프라  │ MCP 8/8\n  🤖️ 서브    │ 없음\n")   # 5줄 미만 = 미측정 규칙 → 6줄


def test_r275_design_gate_lock_baseline_and_quality(dg):
    dg.BASE.mkdir(parents=True)
    (dg.BASE / "statusline.json").write_text(json.dumps({"columns": 250, **dg.signature(SAMPLE)}), encoding="utf-8")
    assert dg.cmd_check_statusline(SAMPLE.replace("50%", "99%")) == 0            # 값만 바뀜 → 구조 같음 PASS
    moved = SAMPLE.replace("  🛑️ 통제    │", "  🛑️ 통제   │")                    # │ 한 칸 이동 = 승인 구조 변경
    assert dg.cmd_check_statusline(moved) == 2                                    # 해제 없음 → UNAUTHORIZED (임의변경)
    assert dg.violations() == 1
    dg.cmd_unlock("statusline", "사용자 지시로 라벨 조정")
    assert dg.cmd_check_statusline(moved) == 1                                    # 해제 상태 → FAIL (임의변경 아님)
    assert dg.violations() == 1
    assert dg.cmd_check_statusline(SAMPLE + "  🔒️ 이력    │ x\n") == 1            # 줄 수 변경도 탐지


def test_r275_visual_quality_gate_image(dg, tmp_path):
    from PIL import Image
    a, b, c = tmp_path / "a.png", tmp_path / "b.png", tmp_path / "c.png"
    Image.new("RGB", (100, 100), "white").save(a)
    Image.new("RGB", (100, 100), "white").save(b)
    im = Image.new("RGB", (100, 100), "white")
    for x in range(30):
        for y in range(30):
            im.putpixel((x, y), (0, 0, 0))
    im.save(c)
    assert dg.cmd_image("home", str(b)) == 3                                      # 기준 없음 = 미측정
    dg.cmd_image_baseline("home", str(a))
    assert dg.cmd_image("home", str(b)) == 0                                      # 같은 화면 PASS
    assert dg.cmd_image("home", str(c)) == 2                                      # 9% 바뀜 → 해제 없이 = UNAUTHORIZED


def test_r275_real_statusline_matches_committed_baseline():
    """Design Ownership Lock 실제 적용 — 지금 상태줄 구조가 승인 기준(.claude/design-baseline/statusline.json)과 같아야 한다."""
    if not (KIT / ".claude" / "design-baseline" / "statusline.json").exists():
        pytest.skip("승인 기준 없음 (이 프로젝트는 상태줄 기준 미등록)")
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(KIT), PYTHONIOENCODING="utf-8")
    m = _load("dg_real", KIT / ".claude/scripts/design-gate.py")
    base = json.loads((KIT / ".claude/design-baseline/statusline.json").read_text(encoding="utf-8"))
    out = subprocess.run([sys.executable, "-X", "utf8", str(KIT / ".claude/scripts/statusline_context.py")], input=b"{}",
                         capture_output=True, env=dict(env, COLUMNS=str(base.get("columns", 250))), timeout=120, cwd=str(KIT))
    diffs = m.compare(base, m.signature(out.stdout.decode("utf-8", "replace")))
    assert not diffs, diffs


def test_r275_review_fixes_design_gate(dg):
    """독립 리뷰 반영: 렌더 실패 = 미측정 · 같은 위반 반복 검사 = 1건 · 기준 덮어쓰기는 해제 후에만."""
    dg.BASE.mkdir(parents=True)
    (dg.BASE / "statusline.json").write_text(json.dumps({"columns": 250, **dg.signature(SAMPLE)}), encoding="utf-8")
    assert dg.cmd_check_statusline("") == 3                                       # 빈 출력 → 미측정 (위반 기록 X)
    moved = SAMPLE.replace("  🛑️ 통제    │", "  🛑️ 통제   │")
    assert dg.cmd_check_statusline(moved) == 2 and dg.cmd_check_statusline(moved) == 2
    assert dg.violations() == 1                                                   # 두 번 검사해도 같은 위반 1건
    assert dg.cmd_baseline_statusline() == 2                                      # 해제 없이 기준 덮어쓰기 거부


def test_r275_review_fixes_classifier_and_guess(tmp_path):
    m = _load("lar_r275b", KIT / ".claude/hooks/prompt/ledger_auto_register.py")
    assert m._classify("다 하고 나면 어떻게 돼?") != "execute"
    assert m._classify("그거 하라고 했던 이유가 뭐야") != "execute"
    P = "git " + "push"
    for t in (P + " -uf origin main 해줘", P + " -d origin old 해줘", P + " --tags 해줘", P + " --prune origin 해줘"):
        assert m._needs_approval(t), t
    for t in ("push 했고 --all 확인해줘", "push 후 :) 끝", P + " -u origin feature 해줘"):
        assert not m._needs_approval(t), t
    now = time.time()
    ev = lambda ts, step, inp: json.dumps({"kind": "tool", "ts": ts, "step": step, "detail": json.dumps({"input": inp})})
    lines = [ev(now - 10, "Write", str(tmp_path / "new.py")),                     # 새 파일 생성 → 추측 아님
             ev(now - 9, "Bash", "grep x data.py"), ev(now - 8, "Edit", "C:/p/a.py")]   # data.py 검색 ≠ a.py 를 봄
    assert SL._guess_edits(lines, now - 86400) == 1


def test_r275_unchecked_design_shows_not_checked(tmp_path):
    logs = tmp_path / ".claude" / "logs"
    logs.mkdir(parents=True)
    (logs / "design-gate.log").write_text("[2026-11-16 10:00:00] BASELINE statusline · 10줄\n", encoding="utf-8")
    assert "임의변경 미검사" in SL._control_line(str(tmp_path))                     # 검사 기록 없음 = 0 아님
