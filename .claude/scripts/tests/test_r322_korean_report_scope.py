"""R322 한국어 보고 검사(STD-KOREAN-001) 범위 — 한국어 보고 안의 도구 원문은 통과 · 실제 영어 보고는 계속 차단 (양방향).

실측 오탐 3종 (수정 전): 백틱 없이 붙인 오류 원문 줄 27% · > 인용 출력 16% · 영문 시험명 표 22% → 한국어 보고인데 Stop 차단.
정본 판정 함수 standing-requirements._hangul_ratio 하나를 Stop 검사·턴 중간 검사·품질 자가 점검이 함께 쓴다.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _m():
    sp = importlib.util.spec_from_file_location("sr322", ROOT / ".claude" / "scripts" / "standing-requirements.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _blocked(m, text):
    r, n = m._hangul_ratio(text)
    return n >= m.LANG_MIN_LETTERS and r < m.LANG_MIN_HANGUL


KOREAN_WITH_RAW = {
    "오류 원문 줄": "시험이 실패했습니다. 원인을 보니 상태 전이 주기가 부족했습니다.\n"
                 "E   AssertionError: assert 'RUNNING' == 'VERIFIED' expected status VERIFIED but got RUNNING after two supervisor cycles\n"
                 "주기를 4로 늘렸습니다.",
    "인용 출력": "푸시 결과입니다.\n> To https x main -> main remote: Resolving deltas: 100% (5/5), completed with 4 local objects. "
             "Writing objects done\n원격 차이는 0입니다.",
    "영문 시험명 표": "| 시험 | 결과 |\n|---|---|\n| test_remote_agent_capture_event_gated_r266 | 통과 |\n"
                "| test_screen_capture_allowed_by_default_r320 | 통과 |\n두 시험 모두 통과했습니다.",
}
ENGLISH_REPORTS = {
    "영어 문장": "Deletion blocked by the gate — I withdraw my own request and proceed with a new folder name, without deleting anything.",
    "영어 + 화살표": "Pushed main -> main and propagated to both targets. All tests pass now and the gate is green, nothing left to do here.",
    "영어 + 표": "| item | result |\n|---|---|\n| gate | passed all tests without failures today |\n"
              "Everything is done and pushed to the remote repository already.",
    "한국어 한 줄 + 영어 문장": "회귀 시험을 돌렸습니다. All regression tests passed and the commit was pushed to the remote branch successfully today.",
}


def test_korean_report_with_raw_tool_output_passes():
    m = _m()
    bad = [k for k, t in KOREAN_WITH_RAW.items() if _blocked(m, t)]
    assert bad == [], bad


def test_english_reports_still_blocked():
    m = _m()
    missed = [k for k, t in ENGLISH_REPORTS.items() if not _blocked(m, t)]
    assert missed == [], missed


# ---------- R322 창 하나만 캡처 (겹친 다른 업무 창이 섞이지 않게) ----------

def _capture_pre(tmp_path, command):
    import json, os, subprocess, sys
    (tmp_path / "plugins").mkdir(exist_ok=True)
    (tmp_path / ".claude" / "state").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".claude" / "state" / "screen-capture.block").write_text("", encoding="utf-8")   # 차단 켠 상태
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "session_id": "t"})
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path), "PYTHONUTF8": "1"}
    return subprocess.run([sys.executable, "-X", "utf8", str(ROOT / ".claude" / "hooks" / "tool-dispatch.py"), "pre"],
                          input=payload, capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)


def test_capture_window_script_draws_only_that_window():
    src = (ROOT / ".claude" / "scripts" / "capture-window.ps1").read_text(encoding="utf-8-sig")
    t = "\n".join(ln for ln in src.splitlines() if not ln.lstrip().startswith("#"))   # 설명 주석 제외 · 실제 코드만
    assert "PrintWindow($w.Handle, $hdc, 2)" in t                    # 창이 그린 내용만 (PW_RENDERFULLCONTENT)
    assert "CopyFromScreen" not in t and "AllScreens" not in t     # 화면 좌표·모니터 전체 캡처 없음
    assert "IsIconic" in t                                         # 최소화 창은 빈 이미지를 성공으로 내지 않음


def test_window_capture_allowed_even_when_block_on(tmp_path):
    ok = _capture_pre(tmp_path, r'powershell -NoProfile -ExecutionPolicy Bypass -File .claude\scripts\capture-window.ps1 '
                                '-Title "Visual Studio Code" -Out x.png')
    assert ok.returncode == 0, ok.stderr
    full = _capture_pre(tmp_path, "$g.Copy" + "FromScreen($b.Location, $p, $b.Size)")
    assert full.returncode == 2 and "capture-window.ps1" in full.stderr   # 화면 전체는 막고 창 캡처 명령을 바로 안내
