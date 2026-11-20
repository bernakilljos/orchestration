"""R337 위임 권고 과잉 제거 — 프롬프트 훅이 흔한 글자(«다»·«전체»·«모든») 만 보고 Explore 병렬 위임을 «즉시 실행» 으로 권하던 것.

실측(2026-11-20): 실제 요청 120건 중 suggest_skills 'Explore agent 병렬 dispatch' 권고 75건(63%) · auto-explore 14건 ·
classify-task Codex 권고 0건. 판단 정본은 execution-contract.md § 7 하나 — 훅은 «검토» 힌트만 준다."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROMPT = ROOT / ".claude" / "hooks" / "prompt"


def _load(name, path):
    sys.path.insert(0, str(PROMPT))
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ORDINARY = ["R334 처리했습니다 다음 진행해", "전체 작업을 모두 끝내고 보고해", "버그 다 고쳐줘", "전부 커밋하고 push 해",
            "모든 요청 처리해"]
SURVEY = ["kit 전수조사 해줘", "모든 파일 100% read 로 확인", "전수 조사로 훅 목록 정리"]


def _explore_hint(m, text):
    common = _load("_common_r337", PROMPT / "_common.py")
    return [txt for rx, _ic, txt in m.TABLE if "위임" in txt and common.search(rx, text.lower())]


def test_suggest_skills_no_delegation_hint_on_ordinary_sentences():
    m = _load("suggest_skills_r337", PROMPT / "suggest_skills.py")
    assert all(not _explore_hint(m, t) for t in ORDINARY), [t for t in ORDINARY if _explore_hint(m, t)]
    assert all(_explore_hint(m, t) for t in SURVEY), [t for t in SURVEY if not _explore_hint(m, t)]
    assert "즉시 반영-실행" not in m.TAIL.split("종전")[0] and "자동 실행 아님" in m.HEAD
    assert not any("병렬 dispatch" in txt for _rx, _ic, txt in m.TABLE)


def test_auto_explore_triggers_only_explicit_survey_and_no_speed_claim():
    m = _load("auto_explore_r337", ROOT / ".claude" / "scripts" / "auto-explore-on-task.py")
    assert not any(m.detect_explore_trigger(t) for t in ORDINARY)
    assert all(m.detect_explore_trigger(t) for t in SURVEY)
    msg = m.generate_system_message_injection()
    assert "3-5x" not in msg and "자동 위임 아님" in msg and "§ 7" in msg


def test_policy_docs_have_no_fixed_number_delegation_triggers():
    sub = (ROOT / ".claude" / "rules" / "subagent-delegation.md").read_text(encoding="utf-8")
    ec = (ROOT / ".claude" / "rules" / "execution-contract.md").read_text(encoding="utf-8")
    for bad in ("= 3배 속도", "general-purpose ×4 병렬", "codex-auto 대체 1순위", "→ Explore 병렬"):
        assert bad not in sub, bad
    assert "**3+ 파일** 동시 수정 필요" not in ec and "**300줄+ 예상** 구현" not in ec
    assert "고려 신호" in ec and "사용자가 \"Codex\" 를 명시하면 위임" in ec
