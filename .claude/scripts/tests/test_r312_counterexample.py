"""R312 반례·근본 원인 실제 연결 — 안내문이 아니라 원장 항목 · PASS 때 연결 시험 재실행 · 해결 통과는 시험 실행으로만 (모두 임시 폴더)."""
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEDGER_PY = ROOT / ".claude" / "scripts" / "request-ledger.py"
RT = ROOT / ".claude" / "scripts" / "recurrence-tracker.py"
sys.path.insert(0, str(ROOT / ".claude" / "scripts"))


def _env(tmp):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp), "PYTHONUTF8": "1"}
    env.pop("ORCA_TEST_MODE", None)
    return env


def _run(tmp, script, *args):
    (tmp / ".claude" / "state").mkdir(parents=True, exist_ok=True)
    return subprocess.run([sys.executable, "-X", "utf8", str(script), *args], env=_env(tmp), capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=300)


def _mod():
    import importlib.util
    sp = importlib.util.spec_from_file_location("rl312", LEDGER_PY)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


ITEMS = ["원장 동시 저장 시 손실 방지", "손상 파일 복구", "승인 우회 차단", "상태줄 표시 유지"]


def _seed(tmp, items=ITEMS):
    m = _mod()
    its = [{"i": i + 1, "n": i + 1, "text": t, "state": "done", "evidence": "시험"} for i, t in enumerate(items)]
    r = {"id": "R1", "desc": "x", "status": "pending", "session_id": "s", "items": its,
         "counterexamples": m.extract_counterexamples(its)}
    p = tmp / ".claude" / "state" / "request-ledger.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"session_id": "s", "requests": [r]}, ensure_ascii=False), encoding="utf-8")
    return r


def _ledger(tmp):
    return json.loads((tmp / ".claude" / "state" / "request-ledger.json").read_text(encoding="utf-8"))["requests"][0]


def test_extract_skips_simple_and_dedupes():
    m = _mod()
    assert m.extract_counterexamples([{"i": 1, "text": "동시 저장"}, {"i": 2, "text": "삭제"}]) == []   # 간단한 작업 비용 0
    cx = m.extract_counterexamples([{"i": i + 1, "text": t} for i, t in enumerate(ITEMS + ["여러 세션 동시 실행"])])
    texts = [x["text"] for x in cx]
    assert len(texts) == len(set(texts))                        # 중복 없음
    conc = next(x for x in cx if x["text"].startswith("동시 실행"))
    assert conc["items"] == [1, 5]                              # 같은 반례는 요구 두 개를 한 번에 묶음
    assert any(x["text"].startswith("우회 시도") for x in cx)


def test_open_counterexample_blocks_pass_and_links_are_checked(tmp_path):
    _seed(tmp_path)
    r = _run(tmp_path, LEDGER_PY, "complete", "R1", "--evidence", "증거", "--verification", "PASS")
    assert r.returncode == 2 and "반례" in r.stderr
    assert _ledger(tmp_path)["status"] == "pending"
    # 없는 시험·형식 틀림·짧은 사유는 연결 거부 (관련 없는 증거로 닫지 못하게)
    assert _run(tmp_path, LEDGER_PY, "cx", "R1", "1", "tested", "--test", "nope.py::test_x").returncode == 2
    assert _run(tmp_path, LEDGER_PY, "cx", "R1", "1", "tested", "--test", "그냥 확인함").returncode == 2
    assert _run(tmp_path, LEDGER_PY, "cx", "R1", "1", "na", "--evidence", "없음").returncode == 2
    # PARTIAL 은 사실대로 기록 가능
    assert _run(tmp_path, LEDGER_PY, "complete", "R1", "--evidence", "일부", "--verification", "PARTIAL").returncode == 1


def test_linked_test_reruns_at_pass(tmp_path):
    (tmp_path / "t_cx.py").write_text("def test_ok():\n    assert True\n\ndef test_bad():\n    assert False\n", encoding="utf-8")
    r = _seed(tmp_path)
    n = len(r["counterexamples"])
    assert _run(tmp_path, LEDGER_PY, "cx", "R1", "1", "tested", "--test", "t_cx.py::test_bad").returncode == 0
    for c in range(2, n + 1):
        assert _run(tmp_path, LEDGER_PY, "cx", "R1", str(c), "na", "--evidence", "이 변경과 무관한 경계라 해당 없음").returncode == 0
    bad = _run(tmp_path, LEDGER_PY, "complete", "R1", "--evidence", "증거", "--verification", "PASS")
    assert bad.returncode == 2 and "시험 실패" in bad.stderr          # 실패를 숨기고 완료 X
    rec = _ledger(tmp_path)
    assert rec["status"] == "pending" and rec["counterexamples"][0]["last_run"]["ok"] is False
    # 시험을 고치면(다른 시험 연결) 지금 다시 실행해 통과해야 PASS
    assert _run(tmp_path, LEDGER_PY, "cx", "R1", "1", "tested", "--test", "t_cx.py::test_ok").returncode == 0
    ok = _run(tmp_path, LEDGER_PY, "complete", "R1", "--evidence", "증거", "--verification", "PASS")
    assert ok.returncode == 0, ok.stderr
    rec = _ledger(tmp_path)
    assert rec["status"] == "completed" and rec["counterexamples"][0]["last_run"]["ok"] is True


def test_cx_without_run_is_not_pass(tmp_path):
    """잠금 밖 사전 실행 결과 없이 cmd_complete 를 직접 부르면 연결 시험 = 미실행 → PASS 아님 (옛 결과 불인정)."""
    (tmp_path / "t_cx.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    r = _seed(tmp_path)
    _run(tmp_path, LEDGER_PY, "cx", "R1", "1", "tested", "--test", "t_cx.py::test_ok")
    for c in range(2, len(r["counterexamples"]) + 1):
        _run(tmp_path, LEDGER_PY, "cx", "R1", str(c), "na", "--evidence", "이 변경과 무관한 경계라 해당 없음")
    code = ("import importlib.util,sys;sp=importlib.util.spec_from_file_location('m',sys.argv[1]);m=importlib.util.module_from_spec(sp);"
            "sp.loader.exec_module(m);sys.exit(m.cmd_complete('R1','증거','PASS'))")
    p = subprocess.run([sys.executable, "-X", "utf8", "-c", code, str(LEDGER_PY)], env=_env(tmp_path),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    assert p.returncode == 2 and "실행 안 됨" in p.stderr


def test_fix_passed_requires_running_test_and_recurrence_reopens(tmp_path):
    (tmp_path / "t_fix.py").write_text("def test_ok():\n    assert True\n\ndef test_bad():\n    assert False\n", encoding="utf-8")
    ev = json.loads(_run(tmp_path, RT, "record", "미반영", "dev", "반영 안 됐잖아").stdout)["event_id"]
    assert _run(tmp_path, RT, "root-cause", str(ev), "--cause", "캐시 무효화 누락", "--evidence", "cache.py:42 무효화 호출 없음",
                "--status", "confirmed").returncode == 0
    assert _run(tmp_path, RT, "fix-result", str(ev), "passed", "--evidence", "cache.py:42 무효화 호출 추가").returncode == 2   # 시험 없음
    r = _run(tmp_path, RT, "fix-result", str(ev), "passed", "--evidence", "cache.py:42 무효화 호출 추가", "--test", "t_fix.py::test_bad")
    assert r.returncode == 2 and json.loads(r.stdout)["result"] == "failed"
    db = sqlite3.connect(tmp_path / ".claude" / "state" / "orca.db")
    assert db.execute("SELECT status FROM recurrence_improvements").fetchone()[0] == "FIX_FAILED"
    assert _run(tmp_path, RT, "fix-result", str(ev), "passed", "--evidence", "cache.py:42 무효화 호출 추가",
                "--test", "t_fix.py::test_ok").returncode == 0
    assert db.execute("SELECT status, verified FROM recurrence_improvements").fetchone() == ("VERIFIED", 1)
    # 같은 원인 재발 → 검증 표시 해제 · 기존 해결책 재검증 안내
    ev2 = json.loads(_run(tmp_path, RT, "record", "미반영", "dev", "또 반영 안 됐잖아").stdout)["event_id"]
    out = json.loads(_run(tmp_path, RT, "root-cause", str(ev2), "--cause", "캐시 무효화 누락", "--evidence",
                          "cache.py:42 다시 빠짐", "--status", "confirmed").stdout)
    assert out["reused"] and out["prior_fix"]["status"] == "VERIFIED"
    assert db.execute("SELECT status, verified FROM recurrence_improvements").fetchone() == ("REOPENED", 0)


def test_git_directives_register_and_questions_do_not():
    """R312 실측 미등록 2건 ("이거하고 git push해야지" · "이것도 하고 push해") → 실행 · 같은 낱말의 질문은 질문으로 (양방향)."""
    import importlib.util
    sp = importlib.util.spec_from_file_location("lar312", ROOT / ".claude" / "hooks" / "prompt" / "ledger_auto_register.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    for p in ("이거하고 git push해야지", "이것도 하고 push해 이미지같은건 다른곳에서도 서야지", "push해", "다하고 git push하고",
              "이건 꼭 제대로 보고해주고 git push하도록", "정리하도록", "결과 확인해주고 커밋"):   # R315 실측 미등록 + 같은 어미 변형
        assert m._classify(p) == "execute", p
    for p in ("push했어?", "커밋했어?", "이거하고 나면 어떻게 돼?", "push하도록 돼 있어?", "보고해주고 나면 뭐해?"):
        assert m._classify(p) == "question", p


def test_raw_log_keeps_long_prompt(tmp_path, monkeypatch):
    """R314: 원본 기록이 800자에서 잘려 R313 하위 요구 2개만 복구되던 것 → 긴 지시문도 보존 (비밀 가림은 그대로)."""
    import importlib.util
    sp = importlib.util.spec_from_file_location("lar314", ROOT / ".claude" / "hooks" / "prompt" / "ledger_auto_register.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    body = "\n".join(f"{i}. 요구사항 {i} 처리하고 검증해" for i in range(1, 200))
    m._append_raw(body + "\n끝줄 확인", "s", "execute", "registered")
    rec = json.loads((tmp_path / ".claude" / "logs" / "ledger-raw.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert len(body) > 800 and rec["prompt"].endswith("끝줄 확인")
    m._append_raw("가" * (m.RAW_PROMPT_MAX + 50), "s", "execute", "registered")
    rec = json.loads((tmp_path / ".claude" / "logs" / "ledger-raw.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert len(rec["prompt"]) == m.RAW_PROMPT_MAX          # 상한은 유지 (기록 폭주 방지)
