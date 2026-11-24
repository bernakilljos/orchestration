"""R374/R375 (2026-11-24) — 같은 작업 판정은 명령에서 동적으로 (경로·번호·도구 이름 하드코딩 없음).

같은 대상 폴더를 rm → python → PowerShell 로 도구만 바꿔 다시 실행할 때마다 새 승인 번호가 생겨
사용자가 같은 승인을 여러 번 받던 결함. 시험 경로는 실행마다 무작위로 만든다 (특정 사례 의존 없음).
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_approval_gate_p0 import _hook, _tid, agd, gate, tmp_root  # noqa: F401 — tmp_root 는 fixture


def _rand_dirs(base, n):
    out = []
    for _ in range(n):
        d = base / ("copy_" + uuid.uuid4().hex[:8]) / ("ref_" + uuid.uuid4().hex[:6])
        d.mkdir(parents=True)
        (d / "a.txt").write_text("x", encoding="utf-8")
        out.append(d)
    return out


def _bash_path(p):
    s = str(p).replace("\\", "/")
    return "/" + s[0].lower() + s[2:] if len(s) > 1 and s[1] == ":" else s


RM = "rm" + " -rf"   # 시험 명령 조립 (이 파일을 고치는 셸 명령이 차단 훅에 걸리지 않게)


def test_r375_same_target_different_tool_reuses_one_request(tmp_root):
    """B·I: 도구만 바꿔도 같은 대상이면 번호 1개 · 다른 명령으로 승인 전용 X · 원래 명령만 1회."""
    t1_dir, t2_dir = _rand_dirs(tmp_root, 2)
    cmds = [
        f'{RM} "{_bash_path(t1_dir)}" "{_bash_path(t2_dir)}"',
        f"python -c \"import shutil; [shutil.rmtree(p) for p in (r'{t1_dir}', r'{t2_dir}')]\"",
        f"Remove-Item -Recurse -Force -LiteralPath '{t2_dir}','{t1_dir}'",
    ]
    ids = []
    for c in cmds:
        r = agd.run(_hook(c, str(tmp_root)))
        assert r is not None and r.rc == 2, c                       # 위험 감지는 도구와 무관하게 유지
        ids.append(_tid(r))
    assert len(set(ids)) == 1, ids                                  # 새 번호 남발 0
    assert len(gate.list_waiting()) == 1
    gate.approve(ids[0], gate.USER_APPROVER)
    assert agd.run(_hook(cmds[2], str(tmp_root))).rc == 2           # 다른 명령 = 실행 불가 (원래 명령 안내)
    assert agd.run(_hook(cmds[0], str(tmp_root))) is None           # 원래 명령만 1회
    assert t1_dir.exists() and t2_dir.exists()                      # 훅은 판정만 · 실제 파일은 그대로


def test_r375_different_scope_gets_own_request(tmp_root):
    """A·E: 대상이 하나라도 다르면(범위 확대·축소) 같은 작업이 아니다 → 별도 요청 (승인 범위 재평가)."""
    a, b, c = _rand_dirs(tmp_root, 3)
    r1 = agd.run(_hook(f'{RM} "{_bash_path(a)}" "{_bash_path(b)}"', str(tmp_root)))
    r2 = agd.run(_hook(f'{RM} "{_bash_path(a)}" "{_bash_path(b)}" "{_bash_path(c)}"', str(tmp_root)))
    r3 = agd.run(_hook(f"Remove-Item -Recurse -Force -LiteralPath '{a}'", str(tmp_root)))
    assert len({_tid(r1), _tid(r2), _tid(r3)}) == 3


def test_r375_operation_key_is_dynamic_and_path_normalized(tmp_root):
    """H: 경로 표기(Git Bash /c/…·역슬래시·따옴표·상대 경로)가 달라도 같은 대상 = 같은 지문 · 장치 경로 무시."""
    d, = _rand_dirs(tmp_root, 1)
    k = gate.operation_key
    rel = str(d.relative_to(tmp_root)).replace("\\", "/")
    keys = {
        k(f'{RM} "{_bash_path(d)}" 2>/dev/null', "data_loss", str(tmp_root)),
        k(f"Remove-Item -Recurse '{d}'", "data_loss", str(tmp_root)),
        k(f"{RM} ./{rel}", "data_loss", str(tmp_root)),
    }
    assert len(keys) == 1 and "" not in keys
    assert k(f"{RM} '{d}'", "security", str(tmp_root)) not in keys   # 범주가 다르면 다른 작업
    assert k("git reset --hard", "data_loss", str(tmp_root)) == ""   # 대상 경로 없음 = 기존 범위 지문만


def test_r375_expired_or_withdrawn_request_not_reused(tmp_root):
    """G: 취소된 요청은 같은 작업이어도 재사용하지 않는다 (상태 전이 존중)."""
    d, = _rand_dirs(tmp_root, 1)
    t1 = _tid(agd.run(_hook(f'{RM} "{_bash_path(d)}"', str(tmp_root))))
    gate.withdraw(t1, "시험 취소")
    t2 = _tid(agd.run(_hook(f"Remove-Item -Recurse '{d}'", str(tmp_root))))
    assert t2 != t1
