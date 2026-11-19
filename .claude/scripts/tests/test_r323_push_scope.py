"""R323 다른 프로젝트 push 차단 — IFRS(SVN)·ICMAI 사본 재현에서 남은 결함: svn commit 메시지 안의 «git push» 언급이
push 실행으로 판정돼 «승인으로도 실행하지 않음» 차단. 메시지 걷어 내기를 svn commit·ci 에도 적용 (양방향).
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
P = "pu" + "sh"


def _m():
    sys.path.insert(0, str(ROOT / ".claude" / "hooks" / "prompt"))
    sp = importlib.util.spec_from_file_location("agd323", ROOT / ".claude" / "hooks" / "tool" / "approval_gate_detect.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def test_svn_commit_message_mention_is_not_execution():
    m = _m()
    for cmd in ('svn commit -m "git ' + P + ' 정책 문서" --non-interactive',
                "svn ci -m 'force " + P + " 금지 규칙 정리'",
                'git commit -q -m "fix: git ' + P + ' 판정"'):
        assert P not in m._strip_git_commit_message(cmd), cmd


def test_svn_commit_real_execution_still_visible():
    m = _m()
    # 메시지 밖에 이어 붙인 push · 메시지 안 $( ) 는 셸이 실행하므로 그대로 판정 대상에 남는다
    for cmd in ('svn commit -m "x" --non-interactive && git ' + P + ' --force origin main',
                'svn commit -m "$(git ' + P + ' origin main)" --non-interactive'):
        assert P in m._strip_git_commit_message(cmd), cmd


def test_non_commit_commands_untouched():
    m = _m()
    cmd = 'svn update && echo "git ' + P + '"'
    assert m._strip_git_commit_message(cmd) == cmd


# ---------- R323 python heredoc 본문의 '\r\n' 표기가 줄바꿈으로 깨져 push 언급이 실행으로 남던 것 ----------

def _doc_cmd(extra=""):
    body = ("p='guide.txt'\ns=open(p,'rb').read().decode('utf-8'); nl='\\r\\n'\n"
            "line='- 기록: git " + P + " 차단 실측'\n" + extra + "open(p,'wb').write((s+line+nl).encode('utf-8'))")
    return "python -X utf8 - <<'EOF'\n" + body + "\nEOF"


def test_doc_edit_heredoc_with_crlf_literal_is_inert():
    m = _m()
    out = m._strip_inert_text(_doc_cmd(), str(ROOT))
    assert P not in out


def test_heredoc_that_can_execute_push_still_visible():
    m = _m()
    out = m._strip_inert_text(_doc_cmd("import subprocess\nsubprocess.run(['git', '" + P + "'])\n"), str(ROOT))
    assert P in out


def test_single_line_escaped_heredoc_still_recognized():
    m = _m()
    one = "python -X utf8 - <<'EOF'\\nline='git " + P + " 언급'\\nprint(line)\\nEOF"   # 실제 줄바꿈 없이 이스케이프만
    assert P not in m._strip_inert_text(one, str(ROOT))
