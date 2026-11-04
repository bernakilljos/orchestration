"""Phase 20 회귀 (2026-11-04 · a3d88b7 독립 코드 감사 V1.0 결함) — 임시 폴더·가짜 프로세스만 · 실 DB·유료 API X.

1. cleanup-pollution: 3일 지난 미완료 task 는 보존 · lock 은 기록된 pid 가 죽었을 때만 삭제
2. supervisor advance-all: --dry-run = --dry (상태 변경 X) · 모르는 옵션은 실행 전 거부
3. promote-solutions: 같은 로그 재실행 시 중복 집계 X · 조회 횟수로 verified 를 바꾸지 않음
4. load_requirements: 정책 길이 초과 문서는 잘라서 넘기지 않고 실패
5. reap_stuck_orphans: 소유 흔적 없는 프로세스·CPU 를 쓰는 프로세스는 종료하지 않음
"""
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / ".claude" / "scripts"
sys.path.insert(0, str(SCRIPTS / "lib"))
import real_repair_chain as rc  # noqa: E402


def _bash():
    import shutil
    return shutil.which("bash") or "bash"


# ---------- 1. cleanup-pollution ----------

def _old(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    t = time.time() - 5 * 86400
    os.utime(p, (t, t))


def test_cleanup_keeps_unfinished_tasks_and_live_locks(tmp_path):
    sc = tmp_path / ".claude" / "scripts" / "cleanup-pollution.sh"
    sc.parent.mkdir(parents=True)
    sc.write_bytes((SCRIPTS / "cleanup-pollution.sh").read_bytes())
    (tmp_path / ".claude" / "state").mkdir()
    tasks = tmp_path / ".claude" / "tasks"
    _old(tasks / "pending" / "t1.md", "pending task")
    _old(tasks / "in_progress" / "t2.md", "running task")
    _old(tasks / "locks" / "alive.lock", json.dumps({"pid": os.getpid()}))
    _old(tasks / "locks" / "dead.lock", json.dumps({"pid": 999999}))
    _old(tasks / "locks" / "nopid.lock", "{}")
    r = subprocess.run([_bash(), str(sc)], env={**os.environ, "HOME": str(tmp_path)},
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    assert r.returncode == 0, r.stderr
    assert (tasks / "pending" / "t1.md").exists() and (tasks / "in_progress" / "t2.md").exists()
    assert (tasks / "locks" / "alive.lock").exists() and (tasks / "locks" / "nopid.lock").exists()
    assert not (tasks / "locks" / "dead.lock").exists()
    summary = next((tmp_path / ".claude" / "state").glob("cleanup-summary-*.md")).read_text(encoding="utf-8")
    assert "자동 삭제 안 함" in summary and "pid 999999 종료됨" in summary


# ---------- 2. supervisor CLI ----------

def _sup(tmp_path, *args):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path), "ORCHESTRATION_ROOT": str(tmp_path), "PYTHONUTF8": "1"}
    return subprocess.run([sys.executable, str(SCRIPTS / "lib" / "supervisor.py"), "advance-all", *args], env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=120)


def test_advance_all_unknown_option_rejected_before_running(tmp_path):
    for args in (["--dryrun"], ["--trigger"], ["--trigger", "--dry"], ["dry-run"], ["--dry", "extra"]):
        r = _sup(tmp_path, *args)
        assert r.returncode == 2 and '"executed": false' in r.stdout, args


def test_advance_all_dry_run_alias_changes_nothing(monkeypatch):
    import supervisor
    calls = {}
    monkeypatch.setattr(supervisor, "advance_all_pending",
                        lambda dry_run=False, trigger_source="": calls.update(dry=dry_run) or {"ok": True})
    for flag in ("--dry-run", "--dry"):
        assert supervisor.main(["supervisor.py", "advance-all", flag]) == 0
        assert calls["dry"] is True
    assert supervisor.main(["supervisor.py", "advance-all", "--trigger", "scheduler"]) == 0
    assert calls["dry"] is False


# ---------- 3. promote-solutions ----------

def _promote(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("promote_p20", SCRIPTS / "promote-solutions.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setattr(m, "DB", tmp_path / "orca.db")
    monkeypatch.setattr(m, "LOG", tmp_path / "lookup-history.log")
    return m


def test_promote_is_idempotent_and_never_sets_verified(tmp_path, monkeypatch):
    m = _promote(tmp_path, monkeypatch)
    with sqlite3.connect(str(tmp_path / "orca.db")) as c:
        c.execute("CREATE TABLE problem_solutions (id INTEGER PRIMARY KEY, problem_hash TEXT, hit_count INT,"
                  " reusable_score INT, verified INT)")
        c.execute("INSERT INTO problem_solutions VALUES (1, 'aaaa1111', 0, 5, 0)")    # 미검증
        c.execute("INSERT INTO problem_solutions VALUES (2, 'bbbb2222', 0, 8, 1)")    # 수동 검증
    log = tmp_path / "lookup-history.log"
    log.write_text("head\n", encoding="utf-8")
    m.main()                                                   # 첫 실행: 위치만 기록
    log.write_text("head\n" + "solution #1\n" * 5, encoding="utf-8")
    m.main()
    m.main()                                                   # 같은 로그 재실행
    with sqlite3.connect(str(tmp_path / "orca.db")) as c:
        rows = dict((r[0], r[1:]) for r in c.execute("SELECT id, hit_count, verified FROM problem_solutions"))
    assert rows[1] == (5, 0)                                   # 5회 1번만 · 조회만으로 verified X
    assert rows[2] == (0, 1)                                   # 수동 검증 행은 그대로


def test_promote_short_log_appends_counted_once_each(tmp_path, monkeypatch):
    """감사 재현: 짧은 로그에 1줄씩 붙이면 1·3·6 으로 집계되던 것 → 1·2·3 · 쓰는 중인 줄은 다음 실행에 · 교체된 로그는 처음부터."""
    m = _promote(tmp_path, monkeypatch)
    with sqlite3.connect(str(tmp_path / "orca.db")) as c:
        c.execute("CREATE TABLE problem_solutions (id INTEGER PRIMARY KEY, problem_hash TEXT, hit_count INT,"
                  " reusable_score INT, verified INT)")
        c.execute("INSERT INTO problem_solutions VALUES (1, 'aaaa1111', 0, 5, 0)")
    log = tmp_path / "lookup-history.log"
    log.write_bytes(b"")
    m.main()

    def hits():
        with sqlite3.connect(str(tmp_path / "orca.db")) as c:
            return c.execute("SELECT hit_count FROM problem_solutions").fetchone()[0]
    seen = []
    for _ in range(3):
        with open(log, "ab") as fh:
            fh.write(b"solution #1\n")
        m.main()
        seen.append(hits())
    assert seen == [1, 2, 3]
    with open(log, "ab") as fh:
        fh.write(b"solution #1")                  # 줄바꿈 없는 쓰는 중인 줄
    m.main()
    assert hits() == 3
    with open(log, "ab") as fh:
        fh.write(b"\n")
    m.main()
    assert hits() == 4
    log.write_bytes(b"new file\nsolution #1\n")   # 로그 교체 (정리 후 새 파일)
    m.main()
    assert hits() == 5


def test_promote_failure_before_commit_does_not_double_count(tmp_path, monkeypatch):
    m = _promote(tmp_path, monkeypatch)
    with sqlite3.connect(str(tmp_path / "orca.db")) as c:
        c.execute("CREATE TABLE problem_solutions (id INTEGER PRIMARY KEY, problem_hash TEXT, hit_count INT,"
                  " reusable_score INT, verified INT)")
        c.execute("INSERT INTO problem_solutions VALUES (1, 'aaaa1111', 0, 5, 0)")
    log = tmp_path / "lookup-history.log"
    log.write_bytes(b"x\n")
    m.main()
    log.write_bytes(b"x\nsolution #1\nsolution #1\n")
    real = m.score_from_hits
    monkeypatch.setattr(m, "score_from_hits", lambda n: (_ for _ in ()).throw(RuntimeError("중간 실패")))
    try:
        m.main()
    except RuntimeError:
        pass
    monkeypatch.setattr(m, "score_from_hits", real)
    m.main()
    with sqlite3.connect(str(tmp_path / "orca.db")) as c:
        assert c.execute("SELECT hit_count FROM problem_solutions").fetchone()[0] == 2


# ---------- 4. requirements 길이 ----------

def test_long_requirements_fail_instead_of_truncating(tmp_path):
    body = "".join(f"R{i}. 요구사항 {i} " + "x" * 200 + "\n" for i in range(1, 60))
    (tmp_path / "REQ.md").write_bytes(body.encode("utf-8"))
    r = rc.load_requirements(str(tmp_path), "REQ.md", max_chars=6000)
    assert not r["ok"] and "too long" in r["error"]
    ok = rc.load_requirements(str(tmp_path), "REQ.md", max_chars=len(body) + 10)
    assert ok["ok"] and ok["text"] == body and "R59" in ok["ids"]
    pol = json.loads((ROOT / ".claude/config/sandbox-policy.json").read_text(encoding="utf-8"))
    assert pol["requirements_max_chars"] > 0                   # 상한은 정책 1곳


# ---------- 5. reap_stuck_orphans ----------

class _P:
    def __init__(self, pid, name, cmd, cpu):
        self.info = {"pid": pid, "ppid": 0, "name": name, "cmdline": cmd.split(), "create_time": time.time() - 7200}
        self._cpu = cpu
        self.killed = False

    def cpu_times(self):
        return SimpleNamespace(user=self._cpu, system=0.0)

    def children(self, recursive=False):
        return []

    def kill(self):
        self.killed = True


def test_reaper_only_kills_owned_stuck_processes(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("orca_loop_p20", SCRIPTS / "orca-10min-loop.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setattr(m, "LOG_FILE", tmp_path / "loop.log")
    own = str(m.PROJECT_ROOT.resolve()).replace("\\", "/") + "/.claude/hooks/x.py"
    procs = {
        "owned_stuck": _P(11, "python.exe", f"python {own}", 0.1),
        "owned_busy": _P(12, "python.exe", f"python {own}", 50.0),
        "other_project": _P(13, "python.exe", "python D:/other/.claude/hooks/y.py", 0.1),
        "user_grep_busy": _P(14, "grep.exe", "grep -r foo .", 80.0),
        "user_server": _P(15, "python.exe", "python run.py", 0.1),
        "generic_dash_c": _P(16, "python.exe", "python -c import time;time.sleep(9999)", 0.1),
        "generic_version": _P(17, "python.exe", "python --version", 0.0),
    }
    monkeypatch.setattr(m.psutil, "pids", lambda: [])
    monkeypatch.setattr(m.psutil, "process_iter", lambda attrs=None: list(procs.values()))
    assert m.reap_stuck_orphans() == 1
    assert procs["owned_stuck"].killed
    assert not any(p.killed for k, p in procs.items() if k != "owned_stuck")
    log = (tmp_path / "loop.log").read_text(encoding="utf-8")
    assert "CPU 사용 중" in log and "소유 미확인" in log


# ---------- V1.1 F. Statusline 요청 줄 (레이아웃·색상 FROZEN · 문구 정리·폭만) ----------

def test_ledger_label_strips_control_and_fits_cells():
    sys.path.insert(0, str(SCRIPTS))
    import statusline_context as sl
    from wcwidth import wcswidth
    long_paste = '<pasted_content id="efcd">\n좋습니다. 이번에는 Claude Code가 V1.0의 발견된 결함을 수정하고, V1.1에 오늘까지'
    for d in (long_paste, "abc\x1b[31mred\x1b[0m\tx\r\ny", "가" * 80, "A" * 100):
        out = sl._ledger_label(d)
        assert "\n" not in out and "\r" not in out and "\x1b" not in out and "pasted_content" not in out
        assert wcswidth(out) <= sl.LEDGER_LABEL_CELLS
    assert sl._ledger_label("짧은 요청 (부연)") == "짧은 요청"


def test_statusline_rows_fit_terminal_and_keep_ansi(monkeypatch):
    sys.path.insert(0, str(SCRIPTS))
    import statusline_context as sl
    from wcwidth import wcswidth
    row = "  \x1b[1;35m📊️ 품질추세\x1b[0m\x1b[90m│\x1b[0m " + "가" * 60 + " \x1b[36m▶\x1b[0m   요청 " + "B" * 50
    out = sl._fit_cells(row, 99)
    assert wcswidth(sl.re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", out)) <= 99 and out.endswith("…\x1b[0m")
    assert "\x1b[1;35m" in out                               # 색 코드는 잘리지 않음
    assert sl._fit_cells("짧은 줄", 99) == "짧은 줄"           # 폭 안이면 그대로
    monkeypatch.setenv("STATUSLINE_COLUMNS", "130")
    assert sl._terminal_cols() == 130


# ---------- bde283b 재감사: 정리·프로세스·토큰 ----------

def test_cleanup_keeps_evidence_and_task_files_by_extension(tmp_path):
    sc = tmp_path / ".claude" / "scripts" / "cleanup-pollution.sh"
    sc.parent.mkdir(parents=True)
    sc.write_bytes((SCRIPTS / "cleanup-pollution.sh").read_bytes())
    (tmp_path / ".claude" / "state").mkdir()
    keep = [tmp_path / ".repair-sandbox" / "g1" / "a.bak", tmp_path / ".claude" / "tasks" / "pending" / "t.tmp",
            tmp_path / ".claude" / "state" / "integrity-baseline" / "m.orig"]
    drop = tmp_path / "docs" / "old.tmp"
    for p in keep + [drop]:
        _old(p, "x")
    r = subprocess.run([_bash(), str(sc)], env={**os.environ, "HOME": str(tmp_path)},
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    assert r.returncode == 0, r.stderr
    assert all(p.exists() for p in keep) and not drop.exists()


def test_orphan_hook_and_daily_cleanup_do_not_kill_or_delete():
    for rel in ("plugins/exec_session_guard/hooks/cleanup-orphans.sh", ".claude/hooks/cleanup-orphans.sh"):
        t = (ROOT / rel).read_text(encoding="utf-8")
        assert "Stop-Process" not in t                       # heartbeat 만으로 종료 X
        assert 'rm -f "$bak"' not in t                       # 확장자만으로 백업 삭제 X
    bat = (SCRIPTS / "daily-cleanup.bat").read_bytes()
    assert b"del /q \"%%F\" >nul 2>&1\r\n  echo [%date% %time%] Removed" not in bat
    assert b"\r\n" in bat                                     # cmd 는 LF bat 을 잘못 읽음 (.gitattributes eol=crlf)


def test_status_push_never_puts_token_in_git_url():
    import re
    for rel in ("status-push.ps1", "status-push.bat"):
        t = (ROOT / rel).read_text(encoding="utf-8-sig")
        assert not re.search(r"https://[^\s\"']*:\$\w+@", t), rel
        assert "credential.helper" in t and "ORCH_GH_PAT" in t
    assert "'!PAT!'" not in (ROOT / "status-push.bat").read_text(encoding="utf-8")   # 생성 스크립트에 토큰 원문 X


def test_remote_commands_gated_and_dashboard_token_free():
    import re
    for rel in ("status-push.ps1", "remote-agent.ps1"):
        t = (ROOT / rel).read_text(encoding="utf-8-sig")
        assert "function Test-RemoteCommand" in t and "ORCH_REMOTE_CMD_SECRET" in t, rel
        assert "Get-Process -Name 'codex','gemini','claude'" not in t, rel   # 이름 전체 종료 X
    sp = (ROOT / "status-push.ps1").read_text(encoding="utf-8-sig")
    assert "Disable-ScheduledTask -TaskName 'OrchestrationStatusPush'" not in sp   # 실제 실행 구조(Run 키)와 불일치
    assert "Stop-OwnedWorkers" in sp
    ra = (ROOT / "remote-agent.ps1").read_text(encoding="utf-8-sig")
    assert ra.index("Test-RemoteCommand $cmd") < ra.index("switch ($cmd.action)")   # 실행 전에 검증
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    assert not re.search(r"https://x:\{pat\}@", dash) and "GIT_CONFIG_PARAMETERS" in dash
