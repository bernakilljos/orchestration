"""신규 기록 비밀정보 가림 (2026-11-10 · §64) — 대화(orca.db)·세션 DB(sessions.db)·bash 로그·Ledger 가 같은 정본을 쓴다."""
import hashlib
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
HOOKS = SCRIPTS.parent / "hooks"
TOKEN = "ghp_" + "Ab1" * 12            # 형태만 토큰 (실제 값 아님 · 파일에 원문 패턴을 두지 않음)
TEXT = f"push 해줘 토큰은 {TOKEN} 이야"


def _load(path, name, extra_path=None):
    if extra_path:
        sys.path.insert(0, str(extra_path))
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    finally:
        if extra_path:
            sys.path.remove(str(extra_path))


def test_single_source_of_truth():
    sm = _load(SCRIPTS / "lib" / "redact.py", "sm_t")
    assert TOKEN not in sm.mask(TEXT) and "[MASKED]" in sm.mask(TEXT) and sm.mask(None) is None
    led = _load(HOOKS / "prompt" / "ledger_auto_register.py", "led_t", HOOKS / "prompt")
    assert led._SECRET_RE.pattern == sm.SECRET_RE.pattern                 # Ledger 는 정본을 그대로 씀 (복제 없음)
    assert TOKEN not in led._mask(TEXT)


def test_conversation_logger_masks_but_keeps_original_hash(tmp_path, monkeypatch):
    cl = _load(SCRIPTS / "lib" / "conversation_logger.py", "cl_t")
    monkeypatch.setattr(cl, "DB_PATH", tmp_path / "orca.db")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "s1")
    cl.save_turn("user", TEXT)
    content, ch = sqlite3.connect(tmp_path / "orca.db").execute("SELECT content, content_hash FROM conversations").fetchone()
    assert TOKEN not in content and "[MASKED]" in content
    assert ch == hashlib.sha256(TEXT.encode()).hexdigest()[:16]           # Ledger prompt_sha256 대조는 원문 해시


def test_session_history_brief_masks():
    sh = _load(SCRIPTS / "session-history-db.py", "sh_t")
    assert TOKEN not in sh.brief(TEXT) and TOKEN not in sh.brief({"command": TEXT})


def test_bash_command_log_masks(tmp_path, monkeypatch):
    lb = _load(HOOKS / "tool" / "log_bash_command.py", "lb_t", HOOKS / "tool")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setattr(lb, "py_stdin_text",
                        lambda ctx: json.dumps({"tool_input": {"command": f"curl -H 'Authorization: token {TOKEN}'",
                                                               "description": TEXT}}))
    lb.run(None)
    log = (tmp_path / ".claude" / "logs" / "bash_commands.log").read_text(encoding="utf-8")
    assert TOKEN not in log and "[MASKED]" in log


def test_fail_closed_when_mask_module_missing(tmp_path, monkeypatch):
    lib = tmp_path / "lib"
    lib.mkdir()
    (lib / "conversation_logger.py").write_text((SCRIPTS / "lib" / "conversation_logger.py").read_text(encoding="utf-8"),
                                                encoding="utf-8")         # redact.py 없이 복사
    monkeypatch.setattr(sys, "path", [p for p in sys.path if Path(p).resolve() != (SCRIPTS / "lib").resolve()])
    sys.modules.pop("redact", None)
    cl = _load(lib / "conversation_logger.py", "cl_nomask")
    monkeypatch.setattr(cl, "DB_PATH", tmp_path / "orca.db")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "s2")
    cl.save_turn("user", TEXT)
    content = sqlite3.connect(tmp_path / "orca.db").execute("SELECT content FROM conversations").fetchone()[0]
    assert content == "[MASKED]"                                         # 가림 모듈이 없으면 원문 저장 안 함
