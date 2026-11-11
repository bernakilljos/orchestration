"""대상 솔루션 시험을 격리 사본에서만 실행 — 운영 기록이 바뀌면 FAIL (1111 · §76).

§73 사고: 대상 시험을 실제 IFRS·ICMAI 폴더에서 돌려 orca.db file_audit·sessions.db 가 바뀌었다.
이 스크립트는
  1) 실행 전 보호 대상 해시를 찍는다 (대상 .claude/state 전체 · 대상 settings · 사용자 전역 ~/.claude 명령·설정)
  2) 대상을 임시 격리 사본으로 복사하고 CLAUDE_PROJECT_DIR·ORCHESTRATION_ROOT 를 사본으로 둔 채 pytest 실행
  3) 실행 후 해시를 다시 찍어 하나라도 바뀌면 시험 결과와 무관하게 FAIL (종료 코드 2)
  4) 격리 사본(대상 DB 사본 포함)은 끝나면 삭제한다.

읽기만 한다: 원본은 바이트 복사로 읽고 SQLite 로 열지 않는다 (읽기 전용 연결도 -shm 을 만든다 · §73 정정).
다른 세션이 같은 대상에서 동시에 기록해도 FAIL 로 본다 (보수적 판정 · 바뀐 파일 이름을 보고).

사용: python target-test-isolated.py <대상 폴더> [<대상 폴더> ...] [-- <pytest 인자>]
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

COPY_DIRS = (".claude", "plugins")
COPY_FILES = ("CLAUDE.md", "guide.txt", "pytest.ini")
IGNORE = shutil.ignore_patterns("backups", "logs", "__pycache__", ".pytest_cache", "node_modules", "worktrees")
GLOBAL_ITEMS = ("commands", "skills", "agents", "CLAUDE.md", "settings.json")


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _walk(root: Path):
    if root.is_file():
        yield root
    elif root.is_dir():
        for p in sorted(root.rglob("*")):
            if p.is_file():
                yield p


def protected_roots(target: Path, home: Path) -> list[Path]:
    roots = [target / ".claude" / "state", target / ".claude" / "settings.json",
             target / ".claude" / "settings.local.json"]
    roots += [home / ".claude" / n for n in GLOBAL_ITEMS]
    return roots


def snapshot(roots: list[Path]) -> dict[str, str]:
    snap: dict[str, str] = {}
    for r in roots:
        for p in _walk(r):
            try:
                snap[str(p)] = _sha(p)
            except OSError as e:
                snap[str(p)] = f"읽기 실패:{e.__class__.__name__}"
    return snap


def diff(before: dict[str, str], after: dict[str, str]) -> list[str]:
    out = []
    for k in sorted(set(before) | set(after)):
        if k not in after:
            out.append(f"삭제됨 {k}")
        elif k not in before:
            out.append(f"새로 생김 {k}")
        elif before[k] != after[k]:
            out.append(f"내용 바뀜 {k}")
    return out


def make_copy(target: Path, dst: Path) -> None:
    for d in COPY_DIRS:
        if (target / d).is_dir():
            shutil.copytree(target / d, dst / d, ignore=IGNORE)
    for f in COPY_FILES:
        if (target / f).is_file():
            shutil.copy2(target / f, dst / f)


def _force_writable(func, path, _exc):
    """Windows 읽기 전용 파일(.git pack 등)은 rmtree 가 못 지운다 — 속성을 풀고 한 번 더 (1111 §76 잔여 사본)."""
    try:
        os.chmod(path, 0o700)
        func(path)
    except OSError:
        pass


def remove_copy(work: Path) -> bool:
    """격리 사본 삭제 · 남은 것이 있으면 False (조용히 넘기지 않는다)."""
    kw = {"onexc": _force_writable} if sys.version_info >= (3, 12) else {"onerror": _force_writable}
    for _ in range(2):
        if work.exists():
            shutil.rmtree(work, **kw)
    return not work.exists()


def run_one(target: Path, pytest_args: list[str], home: Path) -> int:
    roots = protected_roots(target, home)
    before = snapshot(roots)
    work = Path(tempfile.mkdtemp(prefix="tgt-iso-"))
    try:
        dst = work / target.name
        make_copy(target, dst)
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(dst), ORCHESTRATION_ROOT=str(dst), PYTHONUTF8="1")
        r = subprocess.run([sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                            "-o", "addopts=", *pytest_args], cwd=dst, env=env, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=1800)
        lines = r.stdout.strip().splitlines()
        tail = lines[-1] if lines else r.stderr.strip()[-300:]
        fails = sorted(l.split("::")[-1][:100] for l in lines if l.startswith("FAILED"))
    finally:
        removed = remove_copy(work)
    changed = diff(before, snapshot(roots))
    print(f"== {target} (격리 사본) → {tail}")
    if not removed:
        print(f"   경고: 격리 사본 일부를 지우지 못함 — {work} (대상 사본이 남아 있음 · 수동 확인)")
    for x in fails:
        print("   실패:", x)
    if changed:
        print(f"   FAIL 운영 기록 변경 {len(changed)}건 — 이 검증은 무효:")
        for c in changed[:50]:
            print("     ", c)
        return 2
    print(f"   보호 대상 {len(before)}개 파일 해시 불변")
    return r.returncode


def main(argv: list[str]) -> int:
    if "--" in argv:
        i = argv.index("--")
        targets, pytest_args = argv[:i], argv[i + 1:]
    else:
        targets, pytest_args = argv, []
    if not targets:
        print(__doc__)
        return 64
    home = Path(os.environ.get("TGT_ISO_HOME") or Path.home())
    worst = 0
    for t in targets:
        p = Path(t).resolve()
        if not (p / ".claude").is_dir():
            print(f"== {p} → 대상 아님 (.claude 없음) · BLOCKED")
            worst = max(worst, 3)
            continue
        rc = run_one(p, pytest_args, home)
        worst = 2 if rc == 2 or worst == 2 else max(worst, rc)
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
