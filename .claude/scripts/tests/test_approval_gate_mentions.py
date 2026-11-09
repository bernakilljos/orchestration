"""승인 게이트: '언급' 오탐 회귀 + 실제 위험 명령 차단 유지 (2026-10-30 appr-7195ea9e0833 · appr-4cb62e15545a 사례)."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "prompt"))   # _common
sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "tool"))
import approval_gate_detect as agd  # noqa: E402

_spec = importlib.util.spec_from_file_location("_gate", ROOT / ".claude" / "scripts" / "approval-gate.py")
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)
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
    assert flagged(_P)
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
