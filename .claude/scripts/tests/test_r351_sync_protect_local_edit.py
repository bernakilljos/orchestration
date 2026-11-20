"""R351 F3 — sync-plugins.py 가 커밋 안 된 .claude/ 수정본을 조용히 덮어쓰던 것 (격리 저장소 · 운영 저장소 변경 없음).

종전: 기본 sync 모드는 drift 검사를 --check·--verbose 때만 하고 shutil.copy2 로 덮어씀 → .claude/commands 를 직접 고친 뒤
커밋 전에 sync 하면 그 수정이 흔적 없이 사라짐. 이제 커밋 안 된 수정이 있는 대상은 건너뛰고 drift(rc 2) 로 알림 · --force 로만 덮어씀.
mtime 비교는 git checkout 뒤 순서가 섞여 믿을 수 없어 쓰지 않음 (커밋된 내용은 git 이력으로 복구 가능).
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SYNC = ROOT / ".claude" / "scripts" / "sync-plugins.py"


def _git(cwd, *a):
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=str(cwd), check=True, capture_output=True)


def _repo(tmp_path):
    r = tmp_path / "repo"
    (r / ".claude" / "scripts").mkdir(parents=True)
    shutil.copy(SYNC, r / ".claude" / "scripts" / SYNC.name)
    (r / "plugins" / "p1" / "commands").mkdir(parents=True)
    (r / "plugins" / "p1" / "commands" / "a.md").write_text("원본 1\n", encoding="utf-8")
    (r / ".claude" / "commands").mkdir(parents=True)
    (r / ".claude" / "commands" / "a.md").write_text("원본 1\n", encoding="utf-8")
    _git(r, "init", "-q")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "init")
    return r


def _sync(r, *a):
    p = subprocess.run([sys.executable, "-X", "utf8", str(r / ".claude" / "scripts" / SYNC.name), *a],
                       cwd=str(r), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    return p.returncode, p.stdout


def test_normal_plugin_edit_still_copied(tmp_path):
    r = _repo(tmp_path)
    (r / "plugins" / "p1" / "commands" / "a.md").write_text("원본 2\n", encoding="utf-8")
    rc, out = _sync(r)
    assert rc == 0 and (r / ".claude" / "commands" / "a.md").read_text(encoding="utf-8") == "원본 2\n", out


def test_uncommitted_local_edit_not_overwritten(tmp_path):
    r = _repo(tmp_path)
    (r / ".claude" / "commands" / "a.md").write_text("직접 고친 내용\n", encoding="utf-8")
    (r / "plugins" / "p1" / "commands" / "a.md").write_text("원본 2\n", encoding="utf-8")
    rc, out = _sync(r)
    assert rc == 2 and "커밋 안 된" in out and ".claude/commands/a.md" in out, out
    assert (r / ".claude" / "commands" / "a.md").read_text(encoding="utf-8") == "직접 고친 내용\n"   # 수정본 보존


def test_staged_local_edit_also_protected_and_force_overwrites(tmp_path):
    r = _repo(tmp_path)
    (r / ".claude" / "commands" / "a.md").write_text("스테이징한 수정\n", encoding="utf-8")
    _git(r, "add", ".claude/commands/a.md")
    (r / "plugins" / "p1" / "commands" / "a.md").write_text("원본 3\n", encoding="utf-8")
    assert _sync(r)[0] == 2
    assert (r / ".claude" / "commands" / "a.md").read_text(encoding="utf-8") == "스테이징한 수정\n"
    rc, out = _sync(r, "--force")
    assert rc == 0 and (r / ".claude" / "commands" / "a.md").read_text(encoding="utf-8") == "원본 3\n", out


# ── R351 F1: 중복 커밋 훅 정리 — infra-check 가 막는 모든 경우를 full-check 가 막는지 (등록 제거의 안전 근거) ──
import json as _json
import os as _os

_HOOKS = ROOT / ".claude" / "hooks"


def _hook_rc(r, name):
    bash = shutil.which("bash")
    p = subprocess.run([bash, str(_HOOKS / name)], input=_json.dumps({"tool_input": {"command": "git commit -m x"}}),
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**_os.environ, "CLAUDE_PROJECT_DIR": str(r), "PRECOMMIT_PREFLIGHT": "1"}, cwd=str(r))
    return p.returncode


def test_full_check_covers_every_infra_block(tmp_path):
    if not shutil.which("bash"):
        return
    import itertools
    r = tmp_path / "hk"
    (r / "plugins").mkdir(parents=True)
    _git(r, "init", "-q")
    (r / "seed.txt").write_text("s\n", encoding="utf-8")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "init")
    infra = ["plugins/p/x.md", ".claude/hooks/h.md", "setup/m.md", "notes.md"]
    docs = ["guide.txt", "CLAUDE.md", "setup/BUILD.md"]
    blocked = 0
    for n in range(1, 3):
        for combo in itertools.combinations(infra + docs, n):
            _git(r, "rm", "-rq", "--cached", "--ignore-unmatch", ".")
            for f in combo:
                (r / f).parent.mkdir(parents=True, exist_ok=True)
                (r / f).write_text(f"{combo}\n", encoding="utf-8")
                _git(r, "add", f)
            if _hook_rc(r, "pre-commit-infra-check.sh") == 2:
                blocked += 1
                assert _hook_rc(r, "pre-commit-full-check.sh") == 2, combo
    assert blocked >= 3                                   # 빈 검사 방지: infra-check 가 실제로 막은 조합이 있어야 함


def test_dispatcher_runs_full_check_only():
    src = (ROOT / ".claude" / "hooks" / "tool-dispatch.py").read_text(encoding="utf-8")
    assert '("pre-commit-full-check", "pre_commit_full_check"' in src
    assert '("pre-commit-infra-check", "pre_commit_infra_check"' not in src


# ── R351 F2: 커밋 검사는 CLAUDE.md 를 고치지 않는다 (갱신은 사전 준비 단계에서만) ──
def _stats_repo(tmp_path):
    r = tmp_path / "st"
    (r / ".claude" / "hooks").mkdir(parents=True)
    (r / ".claude" / "scripts").mkdir(parents=True)
    shutil.copy(_HOOKS / "pre-commit-full-check.sh", r / ".claude" / "hooks" / "pre-commit-full-check.sh")
    shutil.copy(ROOT / ".claude" / "scripts" / "auto-update-stats.sh", r / ".claude" / "scripts" / "auto-update-stats.sh")
    (r / "plugins" / "p").mkdir(parents=True)
    (r / "plugins" / "p" / "x.md").write_text("a\n", encoding="utf-8")
    (r / "CLAUDE.md").write_text("# t\n<!-- AUTO-STATS -->\n> old stats\n<!-- AUTO-STATS -->\n", encoding="utf-8")
    (r / "guide.txt").write_text("g\n", encoding="utf-8")
    _git(r, "init", "-q")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "init")
    (r / "plugins" / "p" / "x.md").write_text("b\n", encoding="utf-8")
    (r / "guide.txt").write_text("g\nfix\n", encoding="utf-8")
    _git(r, "add", "-A")
    return r


def _run_full(r, preflight):
    env = {**_os.environ, "CLAUDE_PROJECT_DIR": str(r)}
    env.pop("PRECOMMIT_PREFLIGHT", None)
    if preflight:
        env["PRECOMMIT_PREFLIGHT"] = "1"
    p = subprocess.run([shutil.which("bash"), str(r / ".claude" / "hooks" / "pre-commit-full-check.sh")],
                       input=_json.dumps({"tool_input": {"command": "git commit -m x"}}), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, cwd=str(r))
    return p.returncode, p.stderr


def test_commit_check_is_read_only_and_preflight_updates(tmp_path):
    if not shutil.which("bash"):
        return
    r = _stats_repo(tmp_path)
    before = (r / "CLAUDE.md").read_bytes()
    rc, err = _run_full(r, preflight=False)
    assert rc == 2 and "CLAUDE.md" in err and "고치지 않음" in err, err
    assert (r / "CLAUDE.md").read_bytes() == before                      # 커밋 검사는 파일을 쓰지 않는다
    rc, err = _run_full(r, preflight=True)
    assert "CLAUDE.md" in err and "old stats" not in (r / "CLAUDE.md").read_text(encoding="utf-8")   # 사전 준비에서 갱신
    _git(r, "add", "CLAUDE.md")
    rc, err = _run_full(r, preflight=False)
    assert "CLAUDE.md" not in err, err                                     # 갱신본 stage 뒤엔 요구 없음
