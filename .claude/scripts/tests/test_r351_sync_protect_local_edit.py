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
