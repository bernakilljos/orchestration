"""suggest-skills.sh 이식 — 프롬프트 -> 관련 skill·command·rule 자동 추천.

주의 (원본 동일): 프롬프트가 아니라 stdin JSON 원문(소문자화) 에서 매칭하고,
로그 .claude/logs/suggest-skills.log 에도 원문 앞 80자가 남는다.
"""
from __future__ import annotations

import os

from _common import append_text, search, ts_iso_tz

HEAD = "[SUGGEST] 관련 skill/tool 참고 (R337 · 자동 실행 아님):"
TAIL = "\n\n(관련 있을 때만 적용 · 단어 일치만으로 실행·위임하지 않음 — execution-contract §7 · R337 · 종전 '지금 즉시 반영-실행')"
TABLE = [
    ("ppt|슬라이드|프레젠테이션|발표자료|deck", False, "\n  - /ppt-make - plugins/design_ppt/ (기업 PPT 자동)"),
    ("docx|워드|word|보고서|리포트|report", False, "\n  - plugins/design_web/ - docx 빌더 스킬"),
    ("엑셀|excel|xlsx|스프레드시트", False, "\n  - plugins/data_excel/ - xlsx 스킬"),
    ("감사|audit|조서|증적|점검", False, "\n  - plugins/audit_* - auto-planner skill"),
    ("신사업|kpi|사업기획|사업안|비즈니스", False, "\n  - docs/kpi-*.docx 참조 - 8 track 산업 매트릭스"),
    ("계산기|화면|ui|디자인|만들어줘|앱", False, "\n  - .claude/rules/app-ui-standard.md (shadcn/AntD/MUI 강제)"),
    ("최신|신기능|changelog|릴리스|업데이트|가격|응시료", False, "\n  - WebSearch 자동 (auto-websearch.md rule)"),
    ("배포|deploy|install|setup|배치", False, "\n  - setup/setup.bat - install 순서 (kit->commit->sync->install->검증)"),
    ("커밋|commit|push|git", False, "\n  - guide.txt + CLAUDE.md + settings.json 3-set 준수"),
    ("답답|짜증|짱나|엉망|대충|장난", False, "\n  - fast mode - 시스템 결함 진단 5단계 (user-emotion.md)"),
    # R337: 종전 패턴 "전수조사|모든|다|전부|100" 은 «다»(합니다·했다) 때문에 실제 요청 120건 중 75건에 붙었다 (위임 권고 과잉)
    (r"전수\s*조사|100%\s*read|모든\s*파일", False, "\n  - 넓은 읽기 조사면 위임 검토 (execution-contract §7 · 수십 파일 이하는 Grep·Read 직접)"),
    ("검증|smoke|테스트|test|확인", False, "\n  - smoke-test-screen.sh - verify-*.py (screen-verify.md)"),
    ("(^|[^a-z0-9_])db([^a-z0-9_]|$)|데이터베이스|sqlite|테이블|orca", False, "\n  - .claude/state/orca.db - kit-stats.py db"),
    ("통계|시각|dashboard|현황|상태|보여", False, "\n  - kit-stats.py all - kit-view.bat - dashboard.html"),
    ("재사용|이력|기억|이전|저장|어떻게 했", False, "\n  - save_solution.py search - problem_solutions DB - lookup-rule.py"),
    ("파일 정리|이름|명명|중복|백업|삭제", False, "\n  - production-file-management.md - file-naming.md - cleanup-pollution.sh"),
    ("파인튜닝|fine-tune|lora|qlora|학습|train", False, "\n  - .claude/skills/ai-finetune-pipeline.md"),
]


def run(ctx):
    if not ctx.has_plugins():
        return None
    raw = ctx.raw_stripped
    lower = raw.lower()

    matches = "".join(txt for rx, _ic, txt in TABLE if search(rx, lower))

    # 로그 (matches 줄 중 '-' 포함 줄 수)
    n_match = sum(1 for ln in matches.rstrip("\n").split("\n") if "-" in ln)
    append_text(
        os.path.join(ctx.project_dir, ".claude", "logs", "suggest-skills.log"),
        f"[{ts_iso_tz()}] matches={n_match} prompt={raw[:80]}\n",
    )

    if not matches:
        return None
    # 원본: here-string 으로 json.dumps 에 넘겨 끝에 개행이 하나 붙는다
    return HEAD + matches + TAIL + "\n"
