"""next-actions.md 작업 기억 영속성 회귀 (2026-11-09).

결함: 자동 갱신이 파일을 통째로 다시 써서 수동 작업 지시가 사라지고, supervisor 출력이 cp949 로 섞여
재개 주입이 조용히 실패했다. 운영 파일·orca.db 는 건드리지 않는다 (모두 tmp_path).
"""
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude" / "scripts" / "auto-save-next-actions.py"
BASH = os.environ.get("BASH_EXE") or (
    r"C:\Program Files\Git\bin\bash.exe" if os.name == "nt" and Path(r"C:\Program Files\Git\bin\bash.exe").exists() else "bash")


def _load(tmp_path):
    spec = importlib.util.spec_from_file_location(f"_na_{tmp_path.name}", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.OUT = tmp_path / ".claude" / "state" / "next-actions.md"
    m.DB = tmp_path / ".claude" / "state" / "orca.db"
    m.OUT.parent.mkdir(parents=True, exist_ok=True)
    return m


def _utf8(p: Path) -> str:
    return p.read_bytes().decode("utf-8")   # UTF-8 아니면 여기서 실패


def test_manual_survives_auto_updates(tmp_path):
    m = _load(tmp_path)
    m.OUT.write_text("# 내 작업 지시\n1. 회귀 게이트 확인 후 커밋\n2. push 승인\n", encoding="utf-8")
    m.cmd_goals(json.dumps([{"goal_id": 1, "description": "한글 목표"}], ensure_ascii=False))
    m.set_block("answer", "## 다음 세션\n- 보고서 작성")
    m.cmd_goals(json.dumps([{"goal_id": 2, "description": "두번째"}], ensure_ascii=False))
    m.set_block("answer", None)            # «완료» 처리 — 자동 블록만 비움
    m.cmd_goals("[]")                      # goal 0건
    t = _utf8(m.OUT)
    assert "회귀 게이트 확인 후 커밋" in t and "push 승인" in t
    assert "한글 목표" not in t and "보고서 작성" not in t


def test_legacy_mixed_encoding_file_recovered(tmp_path):
    m = _load(tmp_path)
    legacy = ("# 수동 메모\n- 반드시 이어서 push\n\n"
              "# 이어서 할 일 — 자동 재기록 (old)\n\n옛 목표\n\n---\n\n").encode("utf-8")
    legacy += "깨진 설명".encode("cp949")      # 종전 stop 훅이 섞어 넣은 cp949 바이트
    m.OUT.write_bytes(legacy)
    m.cmd_goals(json.dumps([{"goal_id": 3, "description": "새 목표"}], ensure_ascii=False))
    t = _utf8(m.OUT)
    assert "반드시 이어서 push" in t and "새 목표" in t and "옛 목표" not in t


def test_resume_text_manual_kept_even_when_old(tmp_path):
    m = _load(tmp_path)
    m.OUT.write_text("일주일 전 확정한 지시: 기존 소스 재사용\n", encoding="utf-8")
    m.set_block("answer", "## 다음 세션\n- 오래된 자동 항목")
    old = time.time() - 7 * 86400
    os.utime(m.OUT, (old, old))
    r = m.resume_text(24 * 3600)
    assert "기존 소스 재사용" in r and "오래된 자동 항목" not in r
    os.utime(m.OUT, None)
    assert "오래된 자동 항목" in m.resume_text(24 * 3600)


def test_external_write_during_update_is_merged(tmp_path):
    m = _load(tmp_path)
    m.OUT.write_text("원래 지시\n", encoding="utf-8")
    calls = {"n": 0}

    def mutate(manual, blocks):
        calls["n"] += 1
        if calls["n"] == 1:   # 잠금을 무시한 외부 편집이 끼어듦
            m.OUT.write_text("원래 지시\n다른 세션이 추가한 지시\n", encoding="utf-8")
        blocks["answer"] = "## 다음 세션\n- 자동"
        return manual, blocks
    assert m.update(mutate)
    t = _utf8(m.OUT)
    assert "다른 세션이 추가한 지시" in t and "- 자동" in t and calls["n"] >= 2


def test_concurrent_sessions_no_lost_update(tmp_path):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(tmp_path), PYTHONIOENCODING="utf-8")
    (tmp_path / ".claude" / "state").mkdir(parents=True)
    procs = [subprocess.Popen([sys.executable, "-X", "utf8", str(SCRIPT), "manual-add", f"세션{i} 지시"], env=env)
             for i in range(8)]
    procs.append(subprocess.Popen([sys.executable, "-X", "utf8", str(SCRIPT), "goals"], env=env, stdin=subprocess.PIPE))
    procs[-1].communicate(json.dumps([{"goal_id": 9, "description": "동시 목표"}], ensure_ascii=False).encode("utf-8"))
    for p in procs:
        p.wait(timeout=60)
    t = _utf8(tmp_path / ".claude" / "state" / "next-actions.md")
    assert all(f"세션{i} 지시" in t for i in range(8)) and "동시 목표" in t
    assert not (tmp_path / ".claude" / "state" / "next-actions.md.lock").exists()


def test_stop_hook_end_to_end_keeps_manual_and_utf8(tmp_path):
    (tmp_path / "plugins").mkdir()
    lib = tmp_path / ".claude" / "scripts" / "lib"
    lib.mkdir(parents=True)
    (tmp_path / ".claude" / "hooks").mkdir()
    (tmp_path / ".claude" / "state").mkdir()
    (lib / "supervisor.py").write_text(
        "import json\nprint(json.dumps([{'goal_id':1,'description':'한글 목표 설명'}], ensure_ascii=False))\n",
        encoding="utf-8")
    (tmp_path / ".claude" / "scripts" / "auto-save-next-actions.py").write_bytes(SCRIPT.read_bytes())
    hook = tmp_path / ".claude" / "hooks" / "stop-active-goals-resume.sh"
    hook.write_bytes((ROOT / ".claude" / "hooks" / "stop-active-goals-resume.sh").read_bytes())
    na = tmp_path / ".claude" / "state" / "next-actions.md"
    na.write_text("# 수동 지시\n1. 회귀 게이트 확인 후 커밋\n\n# 이어서 할 일 — 자동 재기록 (old)\n\nold\n\n---\n\n",
                  encoding="utf-8")
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(tmp_path))
    for _ in range(2):
        subprocess.run([BASH, str(hook)], env=env, timeout=60, check=False)
    t = _utf8(na)
    assert "회귀 게이트 확인 후 커밋" in t and "한글 목표 설명" in t
    assert t.count("<!-- AUTO:goals BEGIN -->") == 1 and "\n\n\n\n" not in t


def test_state_not_propagated_to_targets():
    src = (ROOT / ".claude" / "scripts" / "merge-to-target.py").read_text(encoding="utf-8")
    assert '"state"' in src.split("SKIP_PARTS", 1)[1].split("\n", 1)[0]
