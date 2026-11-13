"""승인 게이트: '언급' 오탐 회귀 + 실제 위험 명령 차단 유지 (2026-10-30 appr-7195ea9e0833 · appr-4cb62e15545a 사례)."""
import importlib.util
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KIT / ".claude" / "hooks" / "prompt"))   # _common
sys.path.insert(0, str(KIT / ".claude" / "hooks" / "tool"))


def _isolated_kit() -> Path:
    """2026-11-12 (R245): 기록 전용 스크립트 허용은 «kit HEAD 와 같은 내용» 일 때만이라, kit 작업본을 고친 채
    커밋 전 회귀를 돌리면 허용 시험이 늘 실패했다 (커밋해야 통과 · 통과해야 커밋 = 순환).
    무결성 검사는 그대로 두고, 현재 작업본을 커밋한 격리 git 저장소를 만들어 그 사본의 게이트로 시험한다.
    운영 kit 의 git 이력·승인 기록은 건드리지 않는다."""
    import atexit
    import shutil
    import subprocess
    import tempfile
    d = Path(tempfile.mkdtemp(prefix="agd-kit-"))
    atexit.register(shutil.rmtree, d, True)
    for rel in (".claude/hooks/tool", ".claude/scripts/lib", ".claude/scripts/auto-save-next-actions.py",
                ".claude/scripts/approval-gate.py"):
        src, dst = KIT / rel, d / rel
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.db", "*.db-*", "*.sqlite*"))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
    g = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false"]
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "isolated kit"]):
        subprocess.run(g + args, cwd=d, check=True, capture_output=True)
    return d


ROOT = _isolated_kit()
_SYS_PATH = list(sys.path)   # 격리 사본이 자기 scripts/lib 를 sys.path 에 남기면 다른 시험이 그 모듈을 찾는다 → 아래에서 복원
_spec_agd = importlib.util.spec_from_file_location("agd_isolated", ROOT / ".claude" / "hooks" / "tool" / "approval_gate_detect.py")
agd = importlib.util.module_from_spec(_spec_agd)
_spec_agd.loader.exec_module(agd)
assert Path(agd._KIT_ROOT).resolve() == ROOT.resolve()   # 격리 저장소 기준으로 판정

_spec = importlib.util.spec_from_file_location("_gate", ROOT / ".claude" / "scripts" / "approval-gate.py")
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)
sys.path[:] = _SYS_PATH   # 격리 사본의 lib 경로 제거 (test_redact_writers fail-closed 시험 간섭 · R245 실측)
DANGER = "git branch -D old-feature"


def flagged(cmd: str) -> bool:
    """실제 hook 과 같은 경로: tool input JSON → _extract_cmd → strip → detect_risk."""
    import json
    raw = json.dumps({"command": cmd, "description": "t"}, ensure_ascii=False)
    c = agd._strip_inert_text(agd._strip_git_commit_message(agd._extract_cmd(raw)))
    return gate.detect_risk(c) is not None


def test_document_write_mention_not_flagged():          # appr-7195ea9e0833 재현
    assert not flagged(f"cat >> docs/review.md <<'EOF'\n- 삭제 방식: {DANGER} 대신 -d\nEOF")
    assert not flagged(f"cat > notes.txt <<EOF\n{DANGER}\nEOF\necho done")


def test_search_pattern_mention_not_flagged():          # appr-4cb62e15545a 재현
    assert not flagged(f'grep -rn "{DANGER}" .claude/hooks')
    assert not flagged(f"rg '{DANGER}' scripts | head")


def test_real_danger_still_blocked():
    assert flagged(DANGER)
    assert flagged(f"cd repo && {DANGER}")
    assert flagged(f'grep -rn "x" file; {DANGER}')                         # 같은 줄 다른 세그먼트
    assert flagged(f"cat <<'EOF' | bash\n{DANGER}\nEOF")                  # 셸로 넘기는 heredoc
    assert flagged(f"bash <<'EOF'\n{DANGER}\nEOF")
    assert flagged(f"python - <<'EOF'\nimport os; os.system('{DANGER}')\nEOF")
    assert flagged(f"cat >> f.md <<'EOF'\nx\nEOF\n{DANGER}")               # heredoc 뒤 실제 명령
    assert flagged("rm -rf /var/data")                                     # 다른 패턴도 그대로 (원 규칙: 절대경로)
    assert flagged("rm -rf build/") == (gate.detect_risk("rm -rf build/") is not None)   # 원 게이트 판정과 동일


# ---------- 2026-11-09: 따옴표 안 '언급' (실행하지 않는 인자) 오탐 + 우회 경로 차단 유지 ----------
_P = "gi" + "t pu" + "sh origin main"
_NOTE = str(ROOT / ".claude" / "scripts" / "auto-save-next-actions.py").replace("\\", "/")


def test_quoted_mention_in_inert_argument_not_flagged():      # 2026-11-09 manual-add 오탐 재현
    assert not flagged(f'python -X utf8 {_NOTE} manual-add "1. {_P} 승인 대기"')
    assert not flagged(f'echo "다음: {_P}"')
    assert not flagged(f"printf '%s' '{_P} 대기'")
    assert not flagged(f'Write-Host "{_P} 예정"')


def test_quoted_push_bypass_paths_still_blocked():
    assert not flagged(_P)                                      # 2026-11-13 R250: origin 일반 push 단독 = 사용자 위임으로 허용
    assert flagged(f'"{_P}"')                                   # 따옴표로 감싼 형태는 단독이어도 계속 판정
    assert flagged(f'echo "x" && {_P}')                         # 다른 세그먼트의 실제 실행
    assert flagged(f'echo "{_P}" | bash')                       # 셸로 넘김
    assert flagged(f'echo "{_P}" | sh -s')
    assert flagged(f'echo "{_P}" > run.sh; bash run.sh')       # 파일로 써서 실행
    assert flagged(f'echo "$({_P})"')                           # 명령 치환은 실행됨
    assert flagged(f'echo "`{_P}`"')
    assert flagged(f'bash -c "{_P}"')                           # 셸 래퍼
    assert flagged(f'sh -c "{_P}"')
    assert flagged(f'eval "{_P}"')
    assert flagged(f'powershell -Command "{_P}"')
    assert flagged(f'cmd /c "{_P}"')
    assert flagged(f'python -c "import os; os.system(\'{_P}\')"')  # 인터프리터 직접 실행
    assert flagged(f'xargs -I{{}} sh -c "{_P}"')
    assert flagged(f'python -X utf8 {_NOTE} manual-add "$({_P})"')   # 허용 스크립트라도 치환은 실행
    assert flagged(f'python -X utf8 {_NOTE} manual-add "x" && {_P}')
    assert flagged(f'python other_script.py "{_P}"')             # 허용 목록 밖 스크립트 인자 = 실행될 수 있음
    assert flagged(f'Write-Host "$({_P})"')                      # PowerShell 하위 식


def test_review_bypasses_stay_blocked(tmp_path):   # 2026-11-09 독립 리뷰 재현 명령 (MUST 1·2·3 · SHOULD 4·5·6)
    assert flagged(f'echo \\" & {_P} ""')                      # \" 는 셸에서 글자 → & 뒤 실행
    assert flagged(f"echo \' & {_P} ''")
    assert flagged(f"echo $'\'' & {_P} & echo $'\''")
    assert flagged(f'echo ^" & {_P} ^"')                       # cmd.exe ^ 이스케이프
    assert flagged('echo hi & "gi' + 't" pu' + 'sh origin main')   # & + 따옴표 친 명령어 (이전에도 차단)
    assert flagged('"gi"t pu' + 'sh origin main')                   # 따옴표로 쪼갠 명령어 (기존 우회 · 같이 수정)
    assert flagged("g'i't pu" + "sh origin main")
    assert flagged("gi''t pu" + "sh origin main")
    assert flagged('g' + chr(92) + 'it pu' + 'sh origin main')
    assert flagged('^gi^t pu' + 'sh origin main')
    assert flagged(f'echo "x" & {_P}')
    evil = tmp_path / "evil" / ".claude" / "scripts" / "auto-save-next-actions.py"   # 다른 저장소의 같은 이름 (커밋됨)
    evil.parent.mkdir(parents=True)
    evil.write_text("import os, sys; os.system(sys.argv[2])\n", encoding="utf-8")
    import subprocess
    g = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run(g + ["init", "-q"], cwd=tmp_path / "evil", check=True)
    subprocess.run(g + ["add", "-A"], cwd=tmp_path / "evil", check=True)
    subprocess.run(g + ["commit", "-q", "-m", "x"], cwd=tmp_path / "evil", check=True)
    ev = str(evil).replace("\\", "/")
    assert flagged(f'python {ev} manual-add "{_P}"')
    assert flagged(f"python -Xutf8 -I {ev} manual-add '{_P}'")
    assert flagged(f'PYTHONPATH=/tmp/evil python {_NOTE} manual-add "{_P}"')      # 환경 변수 접두
    assert flagged(f'python --check-hash-based-pycs always {_NOTE} manual-add "{_P}"')   # 허용 외 옵션
    assert flagged(f'python .claude/scripts/auto-save-next-actions.py manual-add "{_P}"')   # 상대 경로
    assert not flagged(f'python -X utf8 {_NOTE} manual-add "{_P} 대기"')          # 정상 사용은 통과 유지
    assert not flagged(f'python -Xutf8 -u {_NOTE} manual-add "{_P} 대기"')


def test_reattack_bypasses_stay_blocked():          # 2026-11-09 독립 리뷰 재공격 (MUST \' · SHOULD 경로 붙은 echo)
    assert flagged(f"echo \\' & {_P} & \\'")
    assert flagged(f"printf \\' & {_P} & \\'")
    assert flagged(f"Write-Host \\' & {_P} & \\'")
    assert flagged(f'./echo "{_P}"')
    assert flagged(f'/tmp/x/echo "{_P}"')
    assert flagged(f'./python {_NOTE} manual-add "{_P}"')
    assert not flagged(f'echo "{_P} 대기"')                     # 정상 언급은 통과 유지


def test_commit_message_heredoc_mention_and_substitution():   # 2026-11-09 커밋 메시지 언급 vs 실행
    C = "gi" + "t com" + "mit"
    assert not flagged(f"{C} -q -F - <<'EOF'\n- 설명: {_P} 는 승인 필요\nEOF")      # -F - 따옴표 heredoc = 메시지
    assert not flagged(f'{C} -m "$(cat <<\'EOF\'\n{_P} 설명\nEOF\n)"')
    assert not flagged(f'{C} -m "fix: {_P} 오탐"')
    assert flagged(f'{C} -m "$({_P})"')                                            # 큰따옴표 안 치환은 실행됨
    assert flagged(f'{C} -m "`{_P}`"')
    assert flagged(f"{C} -F - <<EOF\n$({_P})\nEOF")                                  # 따옴표 없는 heredoc 은 확장됨
    assert flagged(f'{C} -m "$(cat <<EOF\n$({_P})\nEOF\n)"')
    assert flagged(f"{C} -F - <<'EOF'\nmsg\nEOF\n{_P}")                              # heredoc 뒤 실제 실행


# ── §84 cd <절대 경로> + 상대 경로 기록 스크립트 · 끝 출력 다듬기 — 정상 기록 허용 · 우회 차단 유지 ──
import pytest as _pt84

_S84 = ".claude/scripts/auto-save-next-actions.py"
_K84 = "/" + str(ROOT)[0].lower() + str(ROOT)[2:].replace(chr(92), "/")


@_pt84.mark.parametrize("cmd,blocked", [
    (f'cd {_K84}; python -X utf8 {_S84} manual-add "Git 상태 · 원격 반영(push)은 하지 않음" 2>&1 | tail -1', False),
    (f'cd {_K84} && python -X utf8 {_S84} manual-add "git push 는 하지 않음"', False),
    (f'cd {_K84}; git push origin main', True),
    (f'cd {_K84}; python -X utf8 {_S84} manual-add "$(git push origin main)"', True),
    (f'cd {_K84}; cd /; python {_S84} manual-add "git push origin main"', True),
    (f'cd {_K84}; python {_S84} manual-add "메모"; git push origin main', True),
    (f'python -X utf8 {_K84}/{_S84} manual-add "git push origin main" | bash', True),
    (f'python {_K84}/{_S84} manual-add "git push x" | tail -1 | sh', True),
])
def test_cd_relative_record_script_inert_but_bypass_blocked(cmd, blocked):
    risk = gate.detect_risk(agd._strip_inert_text(agd._strip_git_commit_message(cmd)))
    assert (risk is not None) == blocked, cmd


def test_non_git_target_uses_propagation_manifest(tmp_path):
    """§84 전파 대상(IFRS·ICMAI)은 git 저장소가 아니라 «kit HEAD 와 같은 내용» 조건이 늘 실패 → 정상 기록 명령도 늘 차단.
    git 이 아니면 전파 매니페스트 해시로 확인 · 스크립트가 바뀌면 다시 차단."""
    import hashlib
    import json as _j
    import shutil
    t = tmp_path / "tgt"
    for rel in (".claude/hooks/tool/approval_gate_detect.py", ".claude/scripts/auto-save-next-actions.py"):
        (t / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, t / rel)
    note = t / ".claude/scripts/auto-save-next-actions.py"
    h = hashlib.md5(note.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    (t / ".claude/state").mkdir(parents=True)
    (t / ".claude/state/kit-merge-manifest.json").write_text(_j.dumps({".claude/scripts/auto-save-next-actions.py": h}),
                                                             encoding="utf-8")
    spec = importlib.util.spec_from_file_location("agd_tgt", t / ".claude/hooks/tool/approval_gate_detect.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    p = "gi" + "t pu" + "sh origin main"
    cmd = f'python -X utf8 {str(note).replace(chr(92), "/")} manual-add "{p} 하지 않음"'

    def flagged(c):
        return gate.detect_risk(m._strip_inert_text(m._strip_git_commit_message(c))) is not None
    assert not flagged(cmd)                                     # 매니페스트와 같은 kit 사본 = 글로 판정
    note.write_text(note.read_text(encoding="utf-8") + "\n# 변조\n", encoding="utf-8")
    assert flagged(cmd)                                         # 내용이 바뀌면 다시 차단
    (t / ".claude/state/kit-merge-manifest.json").unlink()
    assert flagged(cmd)                                         # 매니페스트 없음 = 확인 불가 = 차단


# ---------- 2026-11-12 (R245): 검색어 자리표시자의 '>' 가 리다이렉트로 읽혀 설정 파일 조회가 차단됨 ----------
_SJ = ".claude/" + "settings.json"


def test_search_on_settings_file_not_flagged():          # appr-ffee00945d69 · appr-2bf916ac4b7a 재현
    assert not flagged(f'grep -n "auto-save-next-actions" {_SJ} .claude/hooks/*.sh | head')
    assert not flagged(f'sed -n 1,5p a.py; grep -n "PYTHONIOENCODING" /c/x/{_SJ} /c/y/.claude/settings.local.json 2>/dev/null | head')
    assert not flagged(f"rg 'x' {_SJ}")


def test_settings_overwrite_still_blocked():
    assert flagged(f"echo x > {_SJ}")
    assert flagged(f"cp a.json {_SJ}")
    assert flagged(f"cat a.json | tee {_SJ}")
    assert flagged(f'grep -n "x" a.txt > {_SJ}')                           # 검색 결과로 덮어쓰기는 차단 유지


def test_uncommitted_record_script_is_blocked_until_committed():
    """R245 순환 의존 분리 — ① 커밋 전(작업본 ≠ HEAD) 은 기록 전용으로 인정하지 않고 차단 ② 커밋하면 허용.
    격리 저장소에서만 커밋한다 (운영 kit 이력 불변)."""
    import subprocess
    note = ROOT / ".claude" / "scripts" / "auto-save-next-actions.py"
    cmd = f'python -X utf8 {str(note).replace(chr(92), "/")} manual-add "{_P} 하지 않음"'
    orig = note.read_bytes()
    g = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false"]
    try:
        assert not flagged(cmd)                                   # 커밋된 그대로 = 글로 판정
        note.write_bytes(orig + b"\n# uncommitted change\n")
        assert flagged(cmd)                                       # 커밋 전 수정본 = 차단 (무결성 검사 유지)
        subprocess.run(g + ["commit", "-q", "-am", "edit"], cwd=ROOT, check=True, capture_output=True)
        assert not flagged(cmd)                                   # 커밋 후 = 다시 허용
    finally:
        note.write_bytes(orig)
        subprocess.run(g + ["commit", "-q", "-am", "restore"], cwd=ROOT, capture_output=True)
