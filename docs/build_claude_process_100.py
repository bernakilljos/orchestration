"""Claude 과정 전체 100 토픽 교재 빌더 — jobescape.me 인포그래픽 기반 + 우리 kit 매핑.

출력: docs/claude-process-100.docx
근거: KakaoTalk_20261002_140508472.jpg + CLAUDE.md § 3.2 (2026-10-02 Opus 5.5)
준수: .claude/rules/teaching-doc.md 8섹션 · landscape A4
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENTATION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "claude-process-100.docx"

STAGES = [
    {
        "no": 1,
        "name": "기본 사항",
        "range": "1-10",
        "core": "Claude 의 핵심 기능과 UI 를 숙지한다. 모든 심화의 출발점.",
        "topics": [
            "1. Claude 란?", "2. 모델 선택 (Opus 5.5·Sonnet 5·Haiku 4.5)",
            "3. 대화 기본", "4. 컨텍스트 window (1M)",
            "5. 이미지 첨부", "6. 파일 업로드",
            "7. 검색 기능", "8. 음성 입력",
            "9. 설정 관리", "10. 요금제·사용량",
        ],
        "kit_map": [
            ("3. 대화 기본", "모든 플러그인 공통"),
            ("2. 모델 선택", "CLAUDE.md § 3.2 모델 매트릭스 + route_dispatch.md"),
            ("4. 컨텍스트 window", "Opus 5.5 1M 기본 + Headroom proxy 60~95% 압축"),
            ("5. 이미지 첨부", "docs/screens/* + .claude/scripts/verify-image-*.py"),
        ],
        "strength": "진입 장벽 낮음. 5분 안에 첫 응답.",
        "weakness": "모델별 특성·가격 모르면 비싼 호출 폭주.",
        "when": "완전 처음 사용자 · 팀 온보딩 · 모델 승격 결정 전.",
        "check": "Opus 5.5 와 Sonnet 5 차이 1 줄로 설명할 수 있는가?",
    },
    {
        "no": 2,
        "name": "프롬프트",
        "range": "11-20",
        "core": "효과적인 프롬프트 공식 — 역할·맥락·과제·제약·형식.",
        "topics": [
            "11. 프롬프트 구조", "12. Role prompting",
            "13. Context priming", "14. Few-shot 예시",
            "15. CoT (Chain of Thought)", "16. ReAct",
            "17. Self-consistency", "18. ToT (Tree of Thoughts)",
            "19. Prompt chaining", "20. Meta-prompting",
        ],
        "kit_map": [
            ("전체 10개", "plugins/exec_orch/skills/prompt-techniques.md (12 기법 완비)"),
            ("Role·Context·Few-shot·CoT", "codex task-instruction-template.md § 1-10"),
            ("Meta-prompting", "plugins/exec_orch/skills/meta-prompting.md"),
            ("ToT", "plugins/exec_orch/skills/tot-prompting.md"),
            ("Self-critique", "plugins/exec_orch/skills/self-critique-loop.md"),
        ],
        "strength": "같은 모델도 프롬프트 엔지니어링으로 2~5x 품질 향상.",
        "weakness": "과도한 기법 조합은 혼란 유발. 1 task 1 기법 원칙.",
        "when": "동일 질문 반복 시 템플릿화 · codex/gemini 위임 전.",
        "check": "task-instruction.md 안에 role·negative·context·few-shot 모두 들어가는가?",
    },
    {
        "no": 3,
        "name": "아티팩트",
        "range": "21-30",
        "core": "대용량 산출물을 Claude 가 바로 생성 — HTML·코드·문서.",
        "topics": [
            "21. Artifact 란", "22. 코드 블록",
            "23. 스프레드시트 생성", "24. 프레젠테이션",
            "25. 다이어그램 (Mermaid)", "26. HTML/CSS",
            "27. React 컴포넌트", "28. SVG",
            "29. Dashboard", "30. 복합 artifact",
        ],
        "kit_map": [
            ("23. Excel 생성", "plugins/design_excel/ (openpyxl + Google Sheets)"),
            ("24. PPT", "plugins/design_ppt/ (Playwright HTML→PNG→PPTX 잘림 방지)"),
            ("25. Mermaid", "install-mcp · plug_design · mermaid 네이티브"),
            ("26-28. HTML/React/SVG", "plugins/design_web/ (landing·portfolio·blog) + /claude-artifact"),
            ("29. Dashboard", "plugins/exec_claude/commands/claude-artifact.md"),
            ("22. 코드", "plugins/exec_orch/codex/ (×4 병렬 · task-instruction)"),
        ],
        "strength": "결과물 즉시 실행 가능 · PDF/Word/HTML 교차 호환.",
        "weakness": "복잡 레이아웃은 렌더링 사후 검증 필수 (verify-image-fit).",
        "when": "보고서·대시보드·강의 자료·랜딩 페이지 · 1 shot 생성 필요 시.",
        "check": "산출물 자동 검증 hook (hook-09) 가 PASS 로 끝났는가?",
    },
    {
        "no": 4,
        "name": "스킬",
        "range": "31-40",
        "core": "역할·워크플로우·예시·출력 형식 — Skill 패키징으로 재사용.",
        "topics": [
            "31. Skill 개념", "32. SKILL.md frontmatter",
            "33. kebab-case 이름", "34. description 트리거",
            "35. 3단계 점진 공개", "36. scripts/references/assets",
            "37. 조합 가능성", "38. 테스트 (트리거·기능·성능)",
            "39. skill-creator", "40. GitHub-hosted skills (9/22)",
        ],
        "kit_map": [
            ("31-38. Skill 전체", ".claude/rules/skill-design.md (Anthropic 공식 표준 14 항목)"),
            ("우리 skills 100+", "plugins/*/skills/ · .claude/skills/"),
            ("36. scripts", ".claude/scripts/* (134 스크립트)"),
            ("36. references", "plugins/exec_orch/references/ (49 toolkit)"),
            ("40. GitHub-hosted", "install.bat 자동 discovery · GA 2026-09-22"),
            ("38. 테스트", "feedback_verify_before_report.md · 자동 검증 hook"),
        ],
        "strength": "토큰 절감 (점진 공개) + 이식성 (claude.ai·Code·API 공통).",
        "weakness": "동시 활성 50+ 시 혼란 · SKILL.md 5000 단어 상한.",
        "when": "반복 작업 자동화 · 팀 공유 · 외부 배포.",
        "check": "SKILL.md 가 kebab-case 이름 + 트리거 포함 description 인가?",
    },
    {
        "no": 5,
        "name": "툴 (Tools)",
        "range": "41-50",
        "core": "Claude 를 외부 세계와 연결 — WebSearch·Python 실행·MCP.",
        "topics": [
            "41. WebSearch", "42. WebFetch",
            "43. Python 실행 (code interpreter)", "44. File I/O",
            "45. Bash 실행", "46. MCP 연결",
            "47. Tool use 패턴", "48. Error handling",
            "49. Retry 정책", "50. Observability",
        ],
        "kit_map": [
            ("41-42. WebSearch/Fetch", ".claude/rules/auto-websearch.md (트리거 매트릭스)"),
            ("45. Bash", "모든 플러그인 공통"),
            ("46. MCP", "mcp_* 플러그인 10+ (dev·data·web·collab·docs·media·image·queue·social)"),
            ("47. Tool use", "plugins/exec_claude/commands/claude-thinking.md"),
            ("49. Retry", ".claude/rules/best-practices.md § 멈춤 방지"),
            ("50. Observability", "orca.db metrics · claude-mem 자동 관측"),
        ],
        "strength": "실시간 데이터 접근 · 로컬 파일·DB·API 통합.",
        "weakness": "MCP 과다 활성 시 token 폭증 · OAuth 토큰 관리 중요.",
        "when": "최신 정보 필요 · 외부 시스템 조작 · 실측 검증.",
        "check": "최신 정보 질문에 WebSearch 가 자동 발동되는가?",
    },
    {
        "no": 6,
        "name": "연장 (Agent)",
        "range": "51-60",
        "core": "외부 도구 조립 — subagent·멀티 AI·동료 모드.",
        "topics": [
            "51. Agent 란", "52. subagent (Explore·Plan·Judge)",
            "53. 동료 모드 (coach·pm·brainstorming·code-reviewer·data-scientist)",
            "54. 병렬 dispatch", "55. Fork + nesting (depth 3)",
            "56. Advisor tool (mid-turn 상담)", "57. Memory 공유",
            "58. 결과 집계", "59. Governance",
            "60. Agent Skills (9/22 GA)",
        ],
        "kit_map": [
            ("52. subagent", ".claude/rules/subagent-delegation.md (매트릭스)"),
            ("53. 동료 모드 5역할", ".claude/agents/ (coach·pm·brainstorming-partner·code-reviewer·data-scientist 완비 2026-10-02)"),
            ("54. 병렬", "v2.1.232 subagent fork · depth 3 default"),
            ("55. nesting", "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH env"),
            ("56. Advisor", "anthropic-api-features.md § Advisor"),
            ("57. Memory", "~/.claude/projects/<proj>/memory/ + claude-mem"),
            ("60. Agent Skills GA", "install·sync-plugins 자동 discovery"),
        ],
        "strength": "복잡 태스크 분할 · 컨텍스트 격리 · 역할 전문화.",
        "weakness": "nesting 깊으면 디버그 어려움 · 동료 모드 역할 선택 중요.",
        "when": "대량 리서치 · 코드 리뷰 · 1:1 코칭 · 프로젝트 계획.",
        "check": "task 유형별로 맞는 agent 가 자동 선택되는가?",
    },
    {
        "no": 7,
        "name": "자동화",
        "range": "61-76",
        "core": "정형 워크플로우 구축 — 트리거→조치→결과 보관.",
        "topics": [
            "61. Hook (SessionStart·PostToolUse·Stop)", "62. 자동 트리거",
            "63. 조건부 실행", "64. 상태 머신",
            "65. Task Scheduler / cron", "66. Watchdog",
            "67. Retry + backoff", "68. 알림 정책 (크리티컬 5)",
            "69. 로그·audit trail", "70. 롤백",
            "71. Batch API (50% 할인)", "72. Semantic caching",
            "73. 야간 최적화", "74. 주간 감사",
            "75. 자동 문서 갱신", "76. Zero-touch 원칙",
        ],
        "kit_map": [
            ("61. Hook", "plugins/*/hooks/ (31 hook) + .claude/settings.json"),
            ("65. Task Scheduler", "setup/modules/18-daily-artifact-refresh.bat 등"),
            ("66. Watchdog", ".claude/scripts/watchdog-start.bat"),
            ("68. 알림 5", ".claude/rules/approval-gate-rules.md"),
            ("69. Audit", "orca.db.file_audit · production-file-management.md"),
            ("71. Batch", ".claude/rules/batch-api-nightly.md"),
            ("72. Semantic cache", ".claude/rules/semantic-caching.md"),
            ("76. Zero-touch", "CLAUDE.md 글로벌 § ② 전역 원칙"),
        ],
        "strength": "반복 작업 100% 자동화 · 사용자 액션 0.",
        "weakness": "비용 폭증·보안 사고 방지 위해 알림 5 카테고리 필수.",
        "when": "24/7 운영 · 매일/매주 반복 · 조건부 실행.",
        "check": "모든 자동 실행이 로그·audit 에 기록되는가?",
    },
    {
        "no": 8,
        "name": "Claude 코드",
        "range": "77-80",
        "core": "고급 시나리오에 적용 — 터미널 기반 코딩 AI.",
        "topics": [
            "77. Claude Code 설치", "78. CLI vs IDE",
            "79. Hook·Slash·MCP·Skill·Plugin 조합", "80. Mods (TypeScript, 10/1 v2.1.287)",
        ],
        "kit_map": [
            ("전체", "C:\\pjt\\orchestration_v1 kit 자체 = Claude Code 활용 극대화 예시"),
            ("77. 설치", "setup/install.bat"),
            ("79. 조합", "CLAUDE.md § 4 핵심 경로 매트릭스"),
            ("80. Mods (NEW)", "v2.1.287 Claude Mods — built-in /diff 가 mod · TypeScript 로 custom behavior · plugin ship · directory 공유"),
        ],
        "strength": "로컬 파일 접근 · git 통합 · 1M context · bypass permissions.",
        "weakness": "10/1 Mods 출시로 기존 built-in 도 off/replace 가능 — 테스트 필요.",
        "when": "실무 코딩·DevOps·CLI 자동화·멀티 세션 격리.",
        "check": "v2.1.287 설치 시 built-in /diff 가 mod 로 교체 가능한가?",
    },
    {
        "no": 9,
        "name": "사용 사례",
        "range": "81-90",
        "core": "실제 시나리오별 적용 — 산업·역할·규모별.",
        "topics": [
            "81. 감사 (IFRS·개보법)", "82. 코드 리뷰",
            "83. 교재·강의 자동 생성", "84. 번역·요약·확장 (/translate /summarize /expand)",
            "85. 데이터 분석", "86. 리서치·브레인스토밍 (/generate-ideas)",
            "87. 고객 지원 (Zendesk MCP)", "88. 프로젝트 관리 (pm agent)",
            "89. 1:1 코칭 (coach agent)", "90. 산업 ML 이식",
        ],
        "kit_map": [
            ("81. 감사", "다른 프로젝트 (IFRS·ICM·RMS) install 로 배포"),
            ("82. 코드 리뷰", ".claude/agents/code-reviewer.md"),
            ("83. 교재", "plugins/design_word + teaching-doc.md 8섹션 룰"),
            ("84. 번역·요약·확장", "/translate /summarize /expand (2026-10-02 신설)"),
            ("85. 데이터", ".claude/agents/data-scientist.md"),
            ("86. 리서치·아이디어", "/generate-ideas + brainstorming-partner agent (2026-10-02 신설)"),
            ("87. 고객 지원", "mcp_collab Zendesk MCP (2026-10-02 신설)"),
            ("88. PM", ".claude/agents/pm.md (2026-10-02 신설)"),
            ("89. 코칭", ".claude/agents/coach.md (2026-10-02 신설)"),
            ("90. 산업 ML 이식", "industry-transfer-format.md"),
        ],
        "strength": "하나의 kit 로 10 가지 역할 커버 · 모듈 조합 자유.",
        "weakness": "역할마다 적정 agent·skill·command 매핑 숙지 필요.",
        "when": "조직 적용 · 다중 부서 지원 · 영업 데모.",
        "check": "각 사용 사례에 맞는 /command 또는 agent 가 즉시 호출되는가?",
    },
    {
        "no": 10,
        "name": "고급 사용자",
        "range": "91-100",
        "core": "출력물·안전·확장을 역·인덴티티로 익힌다.",
        "topics": [
            "91. Fable 5.1 / Mythos 5.1 (초난도)", "92. Adaptive thinking (always-on 5.5)",
            "93. On-demand conversation compaction (9/22 API)", "94. Prompt cache 1h TTL (75% 저렴)",
            "95. 비용 최적화 (Headroom + semantic cache + Batch)", "96. Observability (claude-mem + orca.db)",
            "97. 보안 (approval-gate · sec_scan · security-guidance)", "98. 다중 세션 (worktree + ASCII 경로)",
            "99. Commerce agents blueprint (9/22)", "100. Claude Mods (10/1)",
        ],
        "kit_map": [
            ("91. Fable 5.1", "route.py `/effort mythos` · Terminal-Bench 55.8% · GDPval 1853"),
            ("92. Adaptive thinking", "Opus 5.5 default · thinking disable 불가"),
            ("93. Conversation compaction", "anthropic-api-features.md § On-demand compaction"),
            ("94. Cache 1h TTL", "Fable 5.1 cache reads 75% 저렴 · 극한 절감"),
            ("95. 비용 최적화", "auto-optimization.md 6 축 + batch-api-nightly.md"),
            ("96. Observability", "claude-mem (자동) + orca.db (명시) · 서로 다른 축"),
            ("97. 보안", "approval-gate.py + sec_scan + security-guidance plugin"),
            ("98. 다중 세션", "multi-session-isolation.md · worktree + ASCII"),
            ("99. Commerce", "retail·travel·telecom·ticketing reference (API blueprint)"),
            ("100. Mods", "v2.1.287 TypeScript custom behavior"),
        ],
        "strength": "최신 신기능 전부 활용 · 운영 grade · 조직 배포 가능.",
        "weakness": "모델·feature·plugin 신기능 추적 지속 필요 (매주 changelog).",
        "when": "조직 전사 적용 · SaaS 제품화 · 교육 과정 운영.",
        "check": "매주 changelog-new.md 알림이 autom 자율 반영되는가 ( feedback_official_features_auto_check.md)?",
    },
]


def _set_landscape(section) -> None:
    section.orientation = WD_ORIENTATION.LANDSCAPE
    section.page_width = Cm(29.7)
    section.page_height = Cm(21.0)
    section.left_margin = Cm(1.8)
    section.right_margin = Cm(1.8)
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)


def _h1(doc: Document, text: str, color: str = "1F4E79") -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(22)
    run.font.color.rgb = RGBColor.from_string(color)


def _h2(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor.from_string("2E5984")


def _p(doc: Document, text: str, size: int = 11) -> None:
    p = doc.add_paragraph(text)
    for run in p.runs:
        run.font.size = Pt(size)


def _callout(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(f"  {text}")
    run.italic = True
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor.from_string("4472C4")


def _topic_table(doc: Document, topics: list[str]) -> None:
    cols = 5
    rows = (len(topics) + cols - 1) // cols
    tbl = doc.add_table(rows=rows, cols=cols)
    tbl.style = "Light Grid Accent 1"
    for i, topic in enumerate(topics):
        r, c = divmod(i, cols)
        cell = tbl.rows[r].cells[c]
        cell.text = topic
        for p in cell.paragraphs:
            for run in p.runs:
                run.font.size = Pt(10)


def _kit_map_table(doc: Document, mapping: list[tuple[str, str]]) -> None:
    tbl = doc.add_table(rows=1 + len(mapping), cols=2)
    tbl.style = "Light Grid Accent 1"
    tbl.rows[0].cells[0].text = "이미지 토픽"
    tbl.rows[0].cells[1].text = "우리 kit 매핑"
    for p in tbl.rows[0].cells[0].paragraphs + tbl.rows[0].cells[1].paragraphs:
        for run in p.runs:
            run.bold = True
            run.font.size = Pt(11)
    for i, (topic, path) in enumerate(mapping, start=1):
        tbl.rows[i].cells[0].text = topic
        tbl.rows[i].cells[1].text = path
        for cell in tbl.rows[i].cells:
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(10)


def _page_break(doc: Document) -> None:
    doc.add_page_break()


def build(out_path: Path = OUT) -> Path:
    doc = Document()
    _set_landscape(doc.sections[0])

    # Cover
    _h1(doc, "Claude 과정 전체 — 10 단계 100 토픽", color="1F4E79")
    _callout(
        doc,
        f"2026-10-02 작성 · jobescape.me 인포그래픽 기반 + orchestration_v1 kit 매핑. "
        f"CLAUDE.md § 3.2 (Opus 5.5 default) 반영."
    )
    _p(doc, "")
    _p(doc, "이 교재는 사용자가 보내준 'Claude 과정 전체' 인포그래픽 (10 단계 100 토픽) 을 ")
    _p(doc, "orchestration_v1 공통 kit 과 1:1 매핑한 결과물입니다. 각 챕터는 teaching-doc.md ")
    _p(doc, "8 섹션 규칙 (핵심·토픽·우리 kit 매핑·강점·약점·강추·점검) 을 따릅니다.")
    _p(doc, "")

    _h2(doc, "범용 요약")
    tbl = doc.add_table(rows=1 + len(STAGES), cols=3)
    tbl.style = "Light Grid Accent 1"
    tbl.rows[0].cells[0].text = "단계"
    tbl.rows[0].cells[1].text = "토픽 범위"
    tbl.rows[0].cells[2].text = "핵심 한 줄"
    for p in tbl.rows[0].cells[0].paragraphs + tbl.rows[0].cells[1].paragraphs + tbl.rows[0].cells[2].paragraphs:
        for run in p.runs:
            run.bold = True
    for i, s in enumerate(STAGES, start=1):
        tbl.rows[i].cells[0].text = f"{s['no']}. {s['name']}"
        tbl.rows[i].cells[1].text = s["range"]
        tbl.rows[i].cells[2].text = s["core"]
        for cell in tbl.rows[i].cells:
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(10)

    _page_break(doc)

    # Per-stage chapters
    for stage in STAGES:
        _h1(doc, f"단계 {stage['no']}. {stage['name']} ({stage['range']})")
        _callout(doc, stage["core"])
        _p(doc, "")

        _h2(doc, "토픽 10 개")
        _topic_table(doc, stage["topics"])
        _p(doc, "")

        _h2(doc, "우리 kit 매핑")
        _kit_map_table(doc, stage["kit_map"])
        _p(doc, "")

        _h2(doc, "강점")
        _p(doc, f"  {stage['strength']}")

        _h2(doc, "약점·주의")
        _p(doc, f"  {stage['weakness']}")

        _h2(doc, "강추 시점")
        _p(doc, f"  {stage['when']}")

        _h2(doc, "점검 1 줄")
        _p(doc, f"  {stage['check']}")

        _page_break(doc)

    # Appendix: 2026-10-02 신기능 요약
    _h1(doc, "부록 A. 2026-10-02 신기능 요약 (이 교재 반영분)")
    _h2(doc, "모델")
    _p(doc, "  Claude Opus 5.5 (9/22) — default · $4/$20 · 1M context · adaptive thinking always-on")
    _p(doc, "  Claude Fable 5.1 / Mythos 5.1 (9/01) — Terminal-Bench 55.8%/60.9% · cache 75% 저렴")

    _h2(doc, "Claude Code 릴리스")
    _p(doc, "  v2.1.260 (9/4) — Fullscreen diff panel")
    _p(doc, "  v2.1.280 (9/22) — Opus 5.5 default 승격 · list 마우스 지원")
    _p(doc, "  v2.1.285 (9/29) — MCP WebSocket · plugin fixes · claude --desktop · WebFetch kill switch")
    _p(doc, "  v2.1.287 (10/1) — Claude Mods 공식 출시 (TypeScript · built-in /diff 가 mod)")

    _h2(doc, "API 신규")
    _p(doc, "  On-demand conversation compaction (9/22) — signed compaction block 재사용")
    _p(doc, "  thinking_mismatch_allowed (9/22) — preserved thinking history edit 전 감지")
    _p(doc, "  Agent Skills GA (9/22) — GitHub-hosted auto-discovery")
    _p(doc, "  Commerce agents blueprint (9/22) — retail·travel·telecom·ticketing")
    _p(doc, "  Mid-conversation inline tools (beta, 9/22) — Opus 5.5 only")

    _h2(doc, "kit 신규 추가 (2026-10-02)")
    _p(doc, "  Commands 5 종 — /rewrite /translate /expand /format-as /generate-ideas")
    _p(doc, "  Agents 3 종 — coach · pm · brainstorming-partner (동료 모드)")
    _p(doc, "  MCP 1 종 — Zendesk (@fruggr/zendesk-mcp-server v3.0.1)")

    _p(doc, "")
    _callout(doc, f"출처: KakaoTalk_20261002_140508472.jpg (jobescape.me) · Anthropic 공식 changelog 9/01~10/01 · 우리 kit 2026-10-02 상태")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    return out_path


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    out = build(target)
    print(f"[OK] built {out}")
