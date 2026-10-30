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
