"""승인 게이트 P0·P1 회귀 (2026-11-08) — Ledger 가 놓쳐도 실행 단계에서 막히는가.

- 감지: 실제 hook 과 같은 경로 (_extract_cmd → strip → detect_risk) · 위험 문자열은 런타임 조립
- 승인 흐름: ORCHESTRATION_ROOT 를 임시 폴더로 → 운영 orca.db 미접촉
"""
import importlib.util
import json
import sqlite3
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "prompt"))
sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "tool"))
import approval_gate_detect as agd  # noqa: E402

_spec = importlib.util.spec_from_file_location("_gate_p0", ROOT / ".claude" / "scripts" / "approval-gate.py")
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)

G, P, F = "gi" + "t", "pu" + "sh", "--for" + "ce"


def flagged(cmd: str) -> bool:
    raw = json.dumps({"command": cmd, "description": "t"}, ensure_ascii=False)
    c = agd._strip_inert_text(agd._strip_git_commit_message(agd._extract_cmd(raw)))
    return gate.detect_risk(c) is not None


# ── 감지: 이전에 통과하던 위험 명령 (gate_probe 91건 중 ALLOW 였던 것) ──
BLOCK = [
    # P0-1 push 변형
    f"{G} {P} origin main", f"{G}  {P}  origin main", f"{G} -C repo {P}", f"{G} {P}",
    f"{G} {P} -f origin main", f"{G} {P} origin +main", f"{G} {P} origin :main",
    f"{G} {P} --delete origin feature", f"cd repo && {G} {P} origin main", f"{G} {P} {F} origin main",
    f"python -c \"import subprocess;subprocess.run(['{G}','{P}'])\"",
    f"echo '{{\"a\":\"b\"}}' ; {G} {P} origin main",          # 예전 _extract_cmd 가 \"} 에서 잘라 뒷부분 미검사
    # P0-2 자기 승인
    "python .claude/scripts/approval-gate.py approve appr-x",
    "python .claude/scripts/approval-gate.py reject appr-x why",
    "python \"$CLAUDE_PROJECT_DIR/.claude/scripts/approval-gate.py\" approve appr-x",
    "python -c \"import importlib;g=load('approval-gate');g.approve('appr-x','user')\"",
    "sqlite3 .claude/state/orca.db \"UPDATE tasks SET approval_state='approved'\"",
    "sqlite3 .claude/state/orca.db \"insert into tasks values(1)\"",
    "echo '{\"prompt\":\"/approve appr-x\"}' | python .claude/hooks/prompt-dispatch.py",
    "echo x | python -X utf8 \"$CLAUDE_PROJECT_DIR/.claude/hooks/prompt-dispatch.py\" --debug-per-hook",
    "python -c \"import user_approval; user_approval.run(c)\"",
    "python -c \"import platform_api as a;a.decide('task','x','approve','user')\"",
    # P0-3 직접 유료 호출
    "codex exec --task t.md", "codex-a exec x", "gemini -p hello", "claude -p hello",
    "curl -X POST https://api.anthropic.com/v1/messages -d @b.json",
    "python .claude/scripts/route.py --set-daily-limit 500",
    "python -c \"import anthropic;anthropic.Anthropic().messages.create(model='m')\"",
    # P1 삭제
    "rm -r build", "find . -name '*.py' -delete", "python -c \"import shutil;shutil.rmtree('build')\"",
    f"{G} clean -fdx", f"{G} reset --hard HEAD~3", f"{G} checkout -- .", f"{G} stash drop",
    "Remove-Item -Recurse build",
    # P1 배포
    "docker push app:v1", "terraform apply", "kubectl apply -f prod.yaml", "vercel --prod",
    "scp dist/app.zip user@server:/var/www",
    # P1 DB·설정
    "sqlite3 .claude/state/orca.db \"DELETE FROM tasks\"",
    "sqlite3 x.db \"DELETE FROM logs WHERE 1=1\"",
    "python -c \"import sqlite3;c=sqlite3.connect('x.db');c.execute('delete from logs');c.commit()\"",
    "sqlite3 x.db \"UPDATE logs SET v=1\"",
    "echo {} > .claude/settings.json", "cp x .env",
]

# ── 정상 개발 명령은 막히지 않아야 함 ──
ALLOW = [
    f"{G} status", f"{G} diff HEAD --stat", f"{G} log --oneline -5", f"{G} stash push -m wip",
    f"{G} config --get {P}.default", f"{G} add -A", f"{G} commit -m \"fix: {P} pattern\"",
    f"{G} fetch origin", f"{G} pull --rebase",
    "python -m pytest -q .claude/scripts/tests", "python .claude/scripts/approval-gate.py list",
    "python .claude/scripts/approval-gate.py status appr-x",
    "sqlite3 x.db \"select approval_state from tasks\"",
    "sqlite3 x.db \"DELETE FROM logs WHERE id=3\"", "sqlite3 x.db \"UPDATE logs SET v=1 WHERE id=2\"",
    "rm build/out.txt", "rm -f tmp.log", "codex --version", "claude mcp list", "gemini --version",
    "cp .claude/settings.json backup/settings.json.bak", "cat .env.example", "npm run build",
    f"grep -rn \"{G} {P}\" .claude/hooks",
    "python -m py_compile .claude/hooks/prompt/user_approval.py .claude/hooks/prompt-dispatch.py",   # 자기 오탐 사례
    "cat .claude/hooks/prompt-dispatch.py",
    f"{G} add .claude/scripts/approval-gate.py .claude/commands/approve.md .claude/commands/reject.md",   # 자기 오탐 사례
]


@pytest.mark.parametrize("cmd", BLOCK)
def test_previously_allowed_risk_now_blocked(cmd):
    assert flagged(cmd), cmd


@pytest.mark.parametrize("cmd", ALLOW)
def test_normal_dev_commands_not_blocked(cmd):
    assert not flagged(cmd), cmd


def test_cli_approve_disabled(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["approval-gate.py", "approve", "appr-x"])
    with pytest.raises(SystemExit) as e:
        gate.main()
    assert e.value.code == 3
    assert "비활성" in capsys.readouterr().out


# ── 승인 흐름: 임시 DB ──
@pytest.fixture
def tmp_root(tmp_path, monkeypatch):
    monkeypatch.setenv("ORCHESTRATION_ROOT", str(tmp_path))
    (tmp_path / ".claude" / "state").mkdir(parents=True)
    (tmp_path / "plugins").mkdir()
    (tmp_path / ".claude" / "scripts").mkdir()
    with sqlite3.connect(tmp_path / ".claude" / "state" / "orca.db") as c:
        c.execute("CREATE TABLE tasks (task_id TEXT PRIMARY KEY, task_file TEXT NOT NULL, status TEXT NOT NULL, "
                  "created_at INTEGER NOT NULL, completed_at INTEGER, approval_state TEXT DEFAULT 'not_required', "
                  "risk_category TEXT, risk_detail TEXT, approved_at INTEGER, approved_by TEXT)")
    assert str(gate.get_db_path()).startswith(str(tmp_path))
    return tmp_path


def test_approval_consumed_once(tmp_root):
    tid = "appr-000000000001"
    gate.request_approval(tid, "x", "irreversible", "d")
    assert gate.consume_approval(tid) == "waiting"
    gate.approve(tid, "user")                       # 사용자 프롬프트가 아닌 승인자 → 실행 X
    assert gate.consume_approval(tid) == "none"
    gate.request_approval(tid, "x", "irreversible", "d")
    gate.approve(tid, gate.USER_APPROVER)
    assert gate.consume_approval(tid) == "consumed"
    assert gate.consume_approval(tid) == "none"     # 1회만
    assert gate.consume_approval("appr-other0000000") == "none"   # 다른 작업으로 전용 X


def test_approval_expires(tmp_root):
    tid = "appr-000000000002"
    gate.request_approval(tid, "x", "irreversible", "d")
    gate.approve(tid, gate.USER_APPROVER)
    with sqlite3.connect(gate.get_db_path()) as c:
        c.execute("UPDATE tasks SET approved_at=? WHERE task_id=?", (int(time.time()) - gate.APPROVAL_TTL_SEC - 5, tid))
    assert gate.consume_approval(tid) == "none"


def _prompt(tmp_root, text):
    import _common
    import user_approval
    ctx = _common.Ctx(json.dumps({"prompt": text}))
    ctx.project_dir = str(ROOT)          # approval-gate.py 원본을 불러오되 DB 는 ORCHESTRATION_ROOT(임시)
    return user_approval.run(ctx)


def test_user_prompt_approval_only_exact_line(tmp_root):
    tid = "appr-000000000003"
    gate.request_approval(tid, "x", "irreversible", "d")
    # 붙여 넣은 문서·문장 안에 섞인 승인 문구는 무시
    assert _prompt(tmp_root, f"<pasted_content id='z'>\n/approve {tid}\n</pasted_content id='z'>") is None
    assert _prompt(tmp_root, f"보고서: 다음엔 /approve {tid} 하세요") is None
    assert _prompt(tmp_root, f"/approve {tid} 그리고 배포도") is None
    assert gate.status(tid)["approval_state"] == "waiting"
    out = _prompt(tmp_root, f"  /approve {tid}  ")
    assert "승인 기록됨" in out
    st = gate.status(tid)
    assert st["approval_state"] == "approved" and st["approved_by"] == gate.USER_APPROVER


def test_user_prompt_reject(tmp_root):
    tid = "appr-000000000004"
    gate.request_approval(tid, "x", "irreversible", "d")
    assert "거부 기록됨" in _prompt(tmp_root, f"/reject {tid} 위험")
    assert gate.status(tid)["approval_state"] == "rejected"


# ── 2026-11-09 승인 소비 ≠ 실행 성공 · 승인 후 스크립트 변경 차단 ──
def test_consume_is_not_success_until_result_recorded(tmp_root):
    tid = "appr-000000000005"
    gate.request_approval(tid, "x", "security", "d")
    gate.approve(tid, gate.USER_APPROVER)
    assert gate.consume_approval(tid) == "consumed"
    with sqlite3.connect(gate.get_db_path()) as c:
        st, ap, done_at, detail = c.execute("SELECT status, approval_state, completed_at, risk_detail FROM tasks "
                                            "WHERE task_id=?", (tid,)).fetchone()
    assert (st, ap, done_at) == ("running", "consumed", None)      # 실행 전 = 결과 미확인 (예전: executed/done)
    assert "consumed_at" in json.loads(detail)
    assert gate.consume_approval(tid) == "none"                      # 실행 결과가 없어도 재사용 X
    assert gate.record_result(tid, "finished", {"output_tail": "ok"}) is True
    with sqlite3.connect(gate.get_db_path()) as c:
        st, ap, detail = c.execute("SELECT status, approval_state, risk_detail FROM tasks WHERE task_id=?",
                                   (tid,)).fetchone()
    assert (st, ap) == ("done", "executed") and json.loads(detail)["result"]["outcome"] == "finished"
    assert gate.record_result(tid, "finished") is False              # 두 번 기록 X
    assert gate.consume_approval(tid) == "none"


def test_interrupted_result_is_failed(tmp_root):
    tid = "appr-000000000006"
    gate.request_approval(tid, "x", "security", "d")
    gate.approve(tid, gate.USER_APPROVER)
    gate.consume_approval(tid)
    gate.record_result(tid, "interrupted")
    assert gate.status(tid)["status"] == "failed"


def test_script_changed_after_approval_is_refused(tmp_root):
    tid = "appr-000000000007"
    gate.request_approval(tid, "x", "security", "d", artifacts={"c:/s.ps1": "a" * 64})
    gate.approve(tid, gate.USER_APPROVER)
    assert gate.consume_approval(tid, artifacts={"c:/s.ps1": "b" * 64}) == "changed"
    assert gate.status(tid)["approval_state"] == "expired"
    assert gate.consume_approval(tid, artifacts={"c:/s.ps1": "a" * 64}) == "none"   # 만료된 승인은 원래 내용으로도 X
    gate.request_approval(tid, "x", "security", "d", artifacts={"c:/s.ps1": "b" * 64})
    gate.approve(tid, gate.USER_APPROVER)
    assert gate.consume_approval(tid) == "changed"                   # 해시를 안 넘기면(옛 호출자) fail-closed
    gate.request_approval(tid, "x", "security", "d", artifacts={"c:/s.ps1": "b" * 64})
    gate.approve(tid, gate.USER_APPROVER)
    assert gate.consume_approval(tid, artifacts={"c:/s.ps1": "b" * 64}) == "consumed"


def _hook(cmd, cwd, resp=None):
    import _common
    payload = {"tool_name": "PowerShell", "tool_input": {"command": cmd}, "cwd": cwd}
    if resp is not None:
        payload["tool_response"] = resp
    ctx = _common.Ctx(json.dumps(payload, ensure_ascii=False))
    ctx.project_dir = str(ROOT)
    return ctx




# ── 2026-11-09 독립 리뷰 MUST/SHOULD 재발 방지 ──
def _risky_ps(extra):
    return "Start-Process powershell -Verb RunAs -Wait " + extra


def test_unc_script_refused_fast_without_request(tmp_root):
    t0 = time.time()
    bs = chr(92)
    unc = bs * 2 + "10.255.255.1" + bs + "s" + bs + "a.ps1"            # \\10.255.255.1\s\a.ps1 (닿지 않는 호스트)
    r = agd.run(_hook(_risky_ps("-ArgumentList '-File','%s'" % unc), str(tmp_root)))
    assert time.time() - t0 < 5, "UNC open 대기로 훅 시간 초과 → 디스패처 통과 (리뷰 MUST)"
    assert r is not None and r.rc == 2 and "확정할 수 없어" in r.err
    with sqlite3.connect(gate.get_db_path()) as c:
        assert c.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0     # 승인으로 풀 수 없는 차단 → 요청 X


def test_chdir_with_relative_script_refused(tmp_root):
    r = agd.run(_hook("cd sub; " + _risky_ps("-ArgumentList '-File','x.ps1'"), str(tmp_root)))
    assert r is not None and r.rc == 2 and "cd 등" in r.err


def test_too_many_scripts_refused(tmp_root):
    files = " ".join(f"'{tmp_root / ('d%02d.ps1' % i)}'" for i in range(agd._ART_MAX_FILES + 1))
    r = agd.run(_hook(_risky_ps("-ArgumentList " + files), str(tmp_root)))
    assert r is not None and r.rc == 2 and "상한" in r.err


def test_log_write_failure_still_blocks(tmp_root, monkeypatch):
    def boom(*a, **k):
        raise PermissionError("log is a directory")
    monkeypatch.setattr(agd, "append_text", boom)
    r = agd.run(_hook("cla" + "ude -p hello", str(tmp_root)))
    assert r is not None and r.rc == 2


def test_internal_error_fails_closed(tmp_root, monkeypatch):
    class Broken:
        def detect_risk(self, c):
            raise RuntimeError("x")
    monkeypatch.setattr(agd, "load_script", lambda name: Broken())
    r = agd.run(_hook("cla" + "ude -p hello", str(tmp_root)))
    assert r is not None and r.rc == 2 and "내부 오류" in r.err
    assert agd.run(_hook("echo hi", str(tmp_root))) is None                  # 위험 단어 없는 일반 명령은 그대로 통과


def test_request_does_not_clobber_running_row(tmp_root):
    tid = "appr-000000000008"
    gate.request_approval(tid, "x", "security", "d")
    gate.approve(tid, gate.USER_APPROVER)
    assert gate.consume_approval(tid) == "consumed"
    assert gate.request_approval(tid, "x", "security", "d")["state"] == "consumed"   # 실행 중 → 덮지 않음
    assert gate.status(tid)["approval_state"] == "consumed"
    with sqlite3.connect(gate.get_db_path()) as c:
        d = json.loads(c.execute("SELECT risk_detail FROM tasks WHERE task_id=?", (tid,)).fetchone()[0])
        d["consumed_at"] = int(time.time()) - gate.CONSUMED_RESULT_WAIT_SEC - 5
        c.execute("UPDATE tasks SET risk_detail=? WHERE task_id=?", (json.dumps(d), tid))
    gate.request_approval(tid, "x", "security", "d")                       # 결과 없이 오래 지남 → 다시 요청 가능
    assert gate.status(tid)["approval_state"] == "waiting"


def test_result_does_not_store_raw_output(tmp_root):
    tid = "appr-000000000009"
    gate.request_approval(tid, "x", "security", "d")
    gate.approve(tid, gate.USER_APPROVER)
    gate.consume_approval(tid)
    ctx = _hook("x", str(tmp_root), {"stdout": "TOKEN=abc123secret", "interrupted": False})
    gate.record_result(tid, "finished", {"output_sha256": "h", "output_chars": 18})
    with sqlite3.connect(gate.get_db_path()) as c:
        assert "abc123secret" not in c.execute("SELECT risk_detail FROM tasks WHERE task_id=?", (tid,)).fetchone()[0]
    src = (ROOT / ".claude" / "hooks" / "tool" / "approval_gate_detect.py").read_text(encoding="utf-8")
    assert "output_tail" not in src


# 2026-11-09: pre-commit 게이트는 실행 위치의 git commit 만 커밋으로 인정 (본문 언급 오인 차단)
import pre_commit_full_check as pcf  # noqa: E402

_C = "com" + "mit"


@pytest.mark.parametrize("cmd,expected", [
    (f'{G} {_C} -m "x"', True),
    (f"cd /c/pjt && {G} {_C} -m x", True),
    (f"{G} -C /c/pjt {_C} -m x", True),
    (f"{G} add -A; {G} {_C}", True),
    (f"GIT_EDITOR=true {G} {_C} --amend", True),
    (f"{G} status\n{G} {_C} -m y", True),
    (f'echo "{G} {_C} later"', False),
    (f'grep -n "{G} {_C}" file', False),
    (f'python x.py --msg "run {G} {_C}"', False),
    (f"{G} log --grep={_C}", False),
    (f"{G} {_C}-tree abc", False),
    (f"cat > f <<EOF\n{G} {_C} -m z\nEOF", False),
    ("echo 커밋 했음", False),
])
def test_pre_commit_gate_only_real_invocation(cmd, expected):
    assert pcf.is_git_commit_invocation(cmd) is expected


# ── 2026-11-09 push 승인은 올라갈 커밋(HEAD)에 묶인다 (승인 뒤 커밋이 늘면 재승인) ──
def _git_repo(path):
    import subprocess
    path.mkdir(parents=True, exist_ok=True)
    g = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run(g + ["init", "-q"], cwd=path, check=True)

    def commit(msg):
        (path / "f.txt").write_text(msg, encoding="utf-8")
        subprocess.run(g + ["add", "-A"], cwd=path, check=True)
        subprocess.run(g + ["commit", "-q", "-m", msg], cwd=path, check=True)
    commit("one")
    return commit






def test_push_with_repo_switch_refused(tmp_root):
    repo = tmp_root / "repo3"
    _git_repo(repo)
    for cmd in (f"cd {repo} && {G} {P}", f"{G} -C {repo} {P}", f"{G} --git-dir=x {P}"):
        r = agd.run(_hook(cmd, str(tmp_root)))
        assert r is not None and r.rc == 2 and "확정할 수 없" in r.err, cmd




def test_push_of_other_refs_bound_or_refused(tmp_root):            # HEAD 가 아닌 것을 올리는 push
    import re
    import subprocess
    repo = tmp_root / "repo5"
    commit = _git_repo(repo)
    g = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run(g + ["branch", "other"], cwd=repo, check=True)
    cmd = f"{G} {P} origin other:main"
    tid = re.search(r"appr-[0-9a-f]{12}", agd.run(_hook(cmd, str(repo))).err).group(0)
    gate.approve(tid, gate.USER_APPROVER)
    subprocess.run(g + ["checkout", "-q", "other"], cwd=repo, check=True)
    commit("on-other")                                                # HEAD 아닌 브랜치가 바뀜 → 재승인
    subprocess.run(g + ["checkout", "-q", "-"], cwd=repo, check=True)
    r = agd.run(_hook(cmd, str(repo)))
    assert r is not None and r.rc == 2 and "바뀌어" in r.err
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip()
    for c in (f"{G} {P} origin {head[:10]}:main", f"{G} {P} --all origin", f"{G} {P} --mirror origin"):
        r = agd.run(_hook(c, str(repo)))
        assert r is not None and r.rc == 2 and "확정할 수 없" in r.err, c


# ── 2026-11-09 승인 요청 불변성: 범위가 바뀌면 새 번호 · 기존 행은 상태 전이 외 수정 없음 ──
def _row(tid):
    with sqlite3.connect(gate.get_db_path()) as c:
        return c.execute("SELECT approval_state, status, risk_detail, approved_at FROM tasks WHERE task_id=?",
                         (tid,)).fetchone()


def _tid(r):
    import re
    return re.search(r"appr-[0-9a-f]{12}", r.err).group(0)


def test_hook_end_to_end_binds_script_content(tmp_root):
    s = tmp_root / "create.ps1"
    s.write_text("Write-Host 'approved'\n", encoding="utf-8")
    cmd = f"Start-Process powershell -Verb RunAs -Wait -ArgumentList '-File','{s}'"
    r = agd.run(_hook(cmd, str(tmp_root)))
    assert r is not None and r.rc == 2
    t1 = _tid(r)
    assert _tid(agd.run(_hook(cmd, str(tmp_root)))) == t1               # 같은 범위 대기 중 → 같은 번호 안내
    gate.approve(t1, gate.USER_APPROVER)
    before = _row(t1)
    s.write_text("Write-Host 'changed after approval'\n", encoding="utf-8")       # 승인 뒤 변경
    r = agd.run(_hook(cmd, str(tmp_root)))
    t2 = _tid(r)
    assert r.rc == 2 and t2 != t1 and "바뀌어" in r.err                  # 새 번호 · 이전 요청 미사용
    assert _row(t1) == before                                          # 이전 승인 행은 그대로 (수정 없음)
    gate.approve(t2, gate.USER_APPROVER)
    assert agd.run(_hook(cmd, str(tmp_root))) is None                 # 바뀐 내용 그대로면 1회 통과
    assert gate.status(t2)["status"] == "running"
    assert agd.run_action(_hook(cmd, str(tmp_root), {"stdout": "ok", "interrupted": False}), "post") is None
    done = _row(t2)
    assert (done[0], done[1]) == ("executed", "done")
    r = agd.run(_hook(cmd, str(tmp_root)))
    assert r is not None and r.rc == 2 and _tid(r) not in (t1, t2)    # 1회 사용 · 다음은 새 번호
    assert _row(t2) == done                                            # 실행 기록 덮어쓰기 없음


def test_push_approval_bound_to_head(tmp_root):
    repo = tmp_root / "repo"
    commit = _git_repo(repo)
    cmd = f"{G} {P} origin main"
    r = agd.run(_hook(cmd, str(repo)))
    assert r is not None and r.rc == 2 and "올라갈 HEAD" in r.err and "브랜치" in r.err
    t1 = _tid(r)
    art1 = json.loads(_row(t1)[2])["artifacts"]
    assert {"git:HEAD", "git:refs", "git:branch", "git:remotes"} <= set(art1)
    gate.approve(t1, gate.USER_APPROVER)
    before = _row(t1)
    commit("two")                                                     # 승인 뒤 커밋 추가 → 범위 바뀜
    r = agd.run(_hook(cmd, str(repo)))
    t2 = _tid(r)
    assert r.rc == 2 and t2 != t1 and "바뀌어" in r.err
    assert _row(t1) == before                                          # 승인된 옛 요청(옛 HEAD) 그대로
    assert json.loads(_row(t2)[2])["artifacts"]["git:HEAD"] != art1["git:HEAD"]
    gate.approve(t2, gate.USER_APPROVER)
    assert agd.run(_hook(cmd, str(repo))) is None                     # 새 HEAD 승인으로 1회 통과
    r = agd.run(_hook(cmd, str(repo)))
    assert r is not None and r.rc == 2                                # 1회성 유지


def test_old_push_approval_without_scope_not_used(tmp_root):
    repo = tmp_root / "repo2"
    _git_repo(repo)
    cmd = f"{G} {P} origin main"
    old = "appr-0000000000aa"                                         # 범위 지문 없는 옛 방식 승인 행
    gate.request_approval(old, cmd, "irreversible", "old", None)
    gate.approve(old, gate.USER_APPROVER)
    before = _row(old)
    r = agd.run(_hook(cmd, str(repo)))
    assert r is not None and r.rc == 2 and _tid(r) != old
    assert _row(old) == before


def test_waiting_request_never_modified_on_scope_change(tmp_root):
    repo = tmp_root / "repo4"
    commit = _git_repo(repo)
    cmd = f"{G} {P} origin main"
    t1 = _tid(agd.run(_hook(cmd, str(repo))))
    before = _row(t1)
    commit("two")                                                     # 대기 중에 커밋 추가
    t2 = _tid(agd.run(_hook(cmd, str(repo))))
    assert t2 != t1 and _row(t1) == before                             # 대기 요청 수정 없음 · 새 번호
    gate.approve(t1, gate.USER_APPROVER)                              # 옛 범위 승인은 지금 HEAD 에 못 씀
    r = agd.run(_hook(cmd, str(repo)))
    assert r is not None and r.rc == 2 and _tid(r) == t2
    gate.approve(t2, gate.USER_APPROVER)
    assert agd.run(_hook(cmd, str(repo))) is None


def test_waiting_request_expires_after_24h_without_modification(tmp_root):   # approval-gate-rules § 승인 만료
    repo = tmp_root / "repo6"
    _git_repo(repo)
    cmd = f"{G} {P} origin main"
    t1 = _tid(agd.run(_hook(cmd, str(repo))))
    with sqlite3.connect(gate.get_db_path()) as c:                     # 25시간 전 요청으로 만듦
        c.execute("UPDATE tasks SET created_at = created_at - ? WHERE task_id = ?", (gate.REQUEST_TTL_SEC + 3600, t1))
    before = _row(t1)
    res = gate.approve(t1, gate.USER_APPROVER)
    assert "만료" in res.get("error", "") and _row(t1) == before        # 승인 거부 · 기록 그대로
    t2 = _tid(agd.run(_hook(cmd, str(repo))))
    assert t2 != t1 and _row(t1) == before                             # 만료 요청 재안내 X · 새 번호
    gate.approve(t2, gate.USER_APPROVER)
    assert agd.run(_hook(cmd, str(repo))) is None


# ── 2026-11-10 §75: 스크립트 파일 안의 위험 동작 · 사용자 전역 Claude 설정 변경 ──
CL = "clau" + "de -p"


def _bash_hook(cmd, cwd):
    import _common
    ctx = _common.Ctx(json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": cwd}, ensure_ascii=False))
    ctx.project_dir = str(ROOT)
    return ctx


def _n_requests():
    with sqlite3.connect(gate.get_db_path()) as c:
        return c.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]


def test_risk_inside_shell_script_blocked(tmp_root):
    s = tmp_root / "새 폴더" / "probe.sh"
    s.parent.mkdir()
    s.write_text("#!/usr/bin/env bash\ncd /c/x && " + CL + " hi --model haiku\n", encoding="utf-8")
    r = agd.run(_bash_hook('bash "%s"' % s.as_posix(), str(tmp_root)))
    assert r is not None and r.rc == 2 and "probe.sh" in r.err and _n_requests() == 1


def test_risk_in_nested_script_blocked(tmp_root):
    inner = tmp_root / "inner.sh"
    inner.write_text(CL + " x\n", encoding="utf-8")
    outer = tmp_root / "outer.sh"
    outer.write_text('echo start\nbash "%s"\n' % inner.as_posix(), encoding="utf-8")
    r = agd.run(_bash_hook('bash "%s"' % outer.as_posix(), str(tmp_root)))
    assert r is not None and r.rc == 2 and "inner.sh" in r.err


def test_benign_shell_script_not_blocked(tmp_root):
    s = tmp_root / "ok.sh"
    s.write_text("echo hello\nls -la\n", encoding="utf-8")
    assert agd.run(_bash_hook('bash "%s"' % s.as_posix(), str(tmp_root))) is None
    assert _n_requests() == 0


def test_script_created_in_same_command_blocked(tmp_root):
    s = (tmp_root / "made.sh").as_posix()
    cmd = "cat > \"%s\" <<'EOF'\n%s hi\nEOF\nbash \"%s\"" % (s, CL, s)
    r = agd.run(_bash_hook(cmd, str(tmp_root)))
    assert r is not None and r.rc == 2


def test_heredoc_text_naming_scripts_not_blocked(tmp_root):
    """파일로만 쓰는 heredoc 안에 스크립트 이름·전역 경로가 글로 있어도 실행이 아니다 (§75 오탐 재발 방지)."""
    cmd = "cat >> notes.md <<'EOF'\nbash probe.sh 와 cp a ~/.claude/commands/ 는 예시\nEOF"
    assert agd.run(_bash_hook(cmd, str(tmp_root))) is None


@pytest.mark.parametrize("cmd", [
    'G="$HOME/.claude/commands"; cp a.md "$G/a.md"',
    "cp a.md ~/.claude/commands/a.md",
    r"Copy-Item a.md $env:USERPROFILE\.claude\skills\a\SKILL.md",
    "python -c \"import shutil,pathlib;shutil.copy('a', pathlib.Path.home()/'.claude'/'agents'/'a.md')\"",
])
def test_user_global_claude_write_flagged(cmd):
    assert flagged(cmd)


@pytest.mark.parametrize("cmd", [
    "ls ~/.claude/commands",
    "md5sum ~/.claude/commands/approve.md",
    "cp a.md .claude/commands/a.md",
])
def test_user_global_read_or_project_write_not_flagged(cmd):
    assert not flagged(cmd)


# ── §77 오탐: 스크립트를 지우거나 읽기만 하는 명령은 실행으로 보지 않는다 (막아야 할 것은 그대로) ──
def _risky_script(tmp_root):
    s = tmp_root / "risky.sh"
    s.write_text("#!/usr/bin/env bash\n" + CL + " hi --model haiku\n", encoding="utf-8")
    return s.as_posix()


@pytest.mark.parametrize("tpl", ['rm -f "{s}"', 'cat "{s}"', 'md5sum {s}', 'git add {s}', 'ls -la {s}',
                                 'git -C /c/x add {s}', 'git -c core.x=1 -C /c/x diff {s}'])
def test_script_operand_of_non_exec_command_not_blocked(tmp_root, tpl):
    s = _risky_script(tmp_root)
    r = agd.run(_bash_hook(tpl.format(s=s), str(tmp_root)))
    assert r is None or r.rc != 2, r.err if r else ""


@pytest.mark.parametrize("tpl", ['bash "{s}"', 'cat "{s}" | bash', 'eval "$(cat {s})"', 'cp "{s}" "{s}.bak.sh"',
                                 'rm -f /tmp/none.txt; bash "{s}"', 'sh {s}', '"{s}"'])
def test_script_execution_still_blocked(tmp_root, tpl):
    s = _risky_script(tmp_root)
    r = agd.run(_bash_hook(tpl.format(s=s), str(tmp_root)))
    assert r is not None and r.rc == 2, tpl
