#!/usr/bin/env python3
"""
Generate 25-slide Claude Code Architecture Reference PPT
Standard structure (DK.method inspired)
"""

import os
import json
from pathlib import Path

SLIDES_DIR = Path("C:/pjt/orchestration_v1/outputs/ppt/html-source/slides").resolve()

# Define all 25 slides
SLIDES_DATA = [
    {
        "num": 1,
        "title": "Claude Code",
        "type": "cover",  # Special cover slide, already manually edited
        "skip": True
    },
    {
        "num": 2,
        "eyebrow": "PART 01 · INTRODUCTION",
        "title": "Claude Code",
        "subtitle": "터미널에 들어온 AI 페어 프로그래머",
        "part": "part-1",
        "bg": "bg-subtle",
        "body_lead": "Claude Code는 터미널에서 돌아가는 AI 에이전트. 파일 읽고·쓰고·실행하고·git 조작하고·MCP 서버 호출한다. 웹 UI가 아니라 <strong>프로젝트 폴더 자체가 작업 공간</strong>이다.",
        "body_paragraphs": [
            "핵심은 <strong>.claude/ 폴더</strong>. 여기 안에 Claude가 이 프로젝트에서 어떻게 일해야 하는지 모든 규칙·명령·훅·스킬이 담긴다. 새 세션을 시작해도 자동으로 로드되고, 팀원이 같은 리포를 쓰면 동일한 규칙이 적용된다.",
            "새 프로젝트에서 <strong>/init을 실행</strong>하면 Claude가 코드베이스를 스캔해서 .claude/ 와 CLAUDE.md를 자동 생성한다. 이게 시작점. 초안을 큐레이션한 후 git commit 하면 끝."
        ],
        "sidebar_title": "◆ 핵심 특징",
        "sidebar_bullets": [
            "터미널 CLI 기반",
            "프로젝트 폴더 = 작업공간",
            ".claude/ 에 모든 맥락",
            "/init 으로 자동 세팅",
            "MCP·훅·플러그인 지원",
            "Multi-AI 오케스트레이션"
        ],
        "sidebar_footer": "폴더가 곧 컨텍스트<br>매번 지시하지 말고<br>한 번 설정해서 영원히",
        "footnote": "시작: claude code --help 또는 docs.claude.com"
    },
    {
        "num": 3,
        "eyebrow": "PART 01 · WHY INIT",
        "title": "/init 의 이유",
        "subtitle": "왜 매번 설명하지 말고, 한 번 세팅해서 영원히",
        "part": "part-1",
        "bg": "bg-subtle",
        "body_lead": "매 대화마다 'Python 3.11 쓰고', 'snake_case 로', 'pytest 통과 후 커밋해야 돼' 를 다시 말하는 건 낭비. Claude가 <strong>항상 알고 있어야 할 규칙</strong>은 CLAUDE.md 에 한 번 쓰면 이후 자동 로드.",
        "body_paragraphs": [
            "/init 은 이걸 자동화한다. 실행 순간 Claude가 프로젝트를 스캔해서 언어·프레임워크·빌드 도구·테스트 방식·디렉토리 구조를 파악하고 초안 CLAUDE.md 를 생성. 유저는 <strong>큐레이션만</strong> 하면 됨.",
            "한번 세팅하면: (1) 새 세션 시작해도 맥락 유지, (2) 팀원이 같은 리포 쓰면 동일 규칙, (3) Claude 실수 줄어들고 품질 일관, (4) 반복 지시 불필요."
        ],
        "sidebar_title": "◆ /init 이 해결하는 것",
        "sidebar_bullets": [
            "반복 지시 제거",
            "팀원 간 규칙 통일",
            "새 세션도 맥락 유지",
            "품질 일관성",
            "자동 스캔 → 초안 생성"
        ],
        "sidebar_footer": "설정 한 번, 효과 영원",
        "footnote": "참조: CLAUDE.md 설계 원칙"
    },
    {
        "num": 4,
        "eyebrow": "PART 01 · WHAT INIT DOES",
        "title": "init 실행 시 순서",
        "subtitle": "자동 스캔 + 초안 생성 + 큐레이션",
        "part": "part-1",
        "bg": "bg-subtle",
        "body_lead": "<strong>Step 1: 코드베이스 분석</strong> — 패키지 매니저(package.json/requirements.txt/go.mod), 빌드 도구, 테스트 프레임워크, 디렉토리 구조, 주요 엔트리 포인트 식별.",
        "body_paragraphs": [
            "<strong>Step 2: CLAUDE.md 초안 작성</strong> — WHAT (프로젝트 소개) / WHY (원칙) / HOW (빌드·테스트·배포 명령) 구조로 자동 채움.",
            "<strong>Step 3: 유저 큐레이션</strong> — Claude가 놓친 팀 컨벤션, 안티패턴, 보안 주의사항을 유저가 직접 편집해서 최종본 만듦."
        ],
        "sidebar_title": "◆ 스캔 대상",
        "sidebar_bullets": [
            "package.json / requirements.txt",
            "빌드·테스트 설정",
            "디렉토리 구조",
            "README.md",
            "Git history (최근 커밋)"
        ],
        "sidebar_footer": "자동화 → 수동 검증<br>품질 담보",
        "footnote": "참조: .claude/scripts/init.py",
        "mermaid": True,
        "mermaid_code": """graph LR
  I[/init 실행] --> S[코드베이스 스캔]
  S --> G["CLAUDE.md 초안<br>생성"]
  G --> C["유저<br>큐레이션"]
  C --> R["✓ Ready"]"""
    },
    {
        "num": 5,
        "eyebrow": "PART 01 · PROJECT ROOT",
        "title": "/init 후 생기는 것",
        "subtitle": "프로젝트 최상위 — 4개 핵심 요소",
        "part": "part-1",
        "bg": "bg-subtle",
        "body_code": """your-project/
├── CLAUDE.md           ◆ 팀 공유 기억         [commit]
├── CLAUDE.local.md     ◆ 나만의 기억          [gitignore]
├── .claude/            ◆ 런타임 설정 폴더
│   └── ...             (다음 슬라이드에서 해부)
└── .mcp.json           ◆ MCP 서버 정의         [commit]""",
        "sidebar_title": "◆ 3 가지 구분",
        "sidebar_bullets": [
            "CLAUDE.md — 공유 (커밋)",
            "CLAUDE.local.md — 개인 (gitignore)",
            ".claude/ — 전체 설정",
            ".mcp.json — 외부 서비스 연결"
        ],
        "sidebar_footer": "용도 명확히 분리",
        "footnote": "참조: CLAUDE.md vs CLAUDE.local.md"
    },
    {
        "num": 6,
        "eyebrow": "PART 01 · MEMORY SYSTEM",
        "title": "기억의 3 단계",
        "subtitle": "Global → Project → Folder (마지막이 이김)",
        "part": "part-1",
        "bg": "bg-subtle",
        "body_lead": "Claude는 세 단계의 Memory를 읽어서 컨텍스트 구성. <strong>Global</strong> (~/.claude/CLAUDE.md) 은 모든 프로젝트 공통 — 개인 코딩 스타일·선호도. <strong>Project</strong> (./CLAUDE.md) 는 이 프로젝트 규칙 — 빌드·테스트·팀 컨벤션. <strong>Folder</strong> (./src/CLAUDE.md) 는 국소 규칙 — 특정 모듈·컴포넌트 주의사항.",
        "body_paragraphs": [
            "충돌 발생 시 <strong>가까운 것이 이긴다</strong> (Folder > Project > Global). 즉 ./src/CLAUDE.md 에 'TypeScript strict 모드' 있고 ./CLAUDE.md 에 'JavaScript OK' 있으면 src/ 안에서는 strict 적용.",
            "CLAUDE.local.md 는 같은 위치의 일반 CLAUDE.md 와 병합되지만 git ignore — 개인 비밀·PR 전 TODO 메모 등."
        ],
        "sidebar_title": "◆ 우선순위 (가까운 순)",
        "sidebar_bullets": [
            "Folder (모듈)",
            "Project (리포)",
            "Global (개인)"
        ],
        "sidebar_footer": "같은 레벨 .local.md<br>는 병합·gitignore",
        "footnote": "참조: .claude/rules/claude-md-design.md",
        "mermaid": True,
        "mermaid_code": """graph TD
  G["Global<br>~/.claude/CLAUDE.md"] --> P
  P["Project<br>./CLAUDE.md"] --> F
  F["Folder<br>./src/CLAUDE.md"]
  F --> A["가장 가까운<br>규칙 적용"]"""
    },
    {
        "num": 7,
        "eyebrow": "PART 02 · .CLAUDE FOLDER",
        "title": ".claude/ 폴더",
        "subtitle": "Claude Code 의 모든 설정이 여기에",
        "part": "part-2",
        "bg": "bg-tech",
        "body_code": """.claude/
├── settings.json       ◆ 팀 공유 권한·훅       [commit]
├── settings.local.json ◆ 개인 오버라이드        [gitignore]
├── commands/           ◆ 슬래시 명령 (/<cmd>)
├── skills/             ◆ 자동 활성 스킬
├── rules/              ◆ 항상 적용 규칙
├── agents/             ◆ 서브에이전트
├── hooks/              ◆ 이벤트 훅 스크립트
├── output-styles/      ◆ 응답 스타일 커스터마이징
└── status-line/        ◆ 커스텀 상태바""",
        "sidebar_title": "◆ 9 하위 요소",
        "sidebar_bullets": [
            "settings · commands · skills",
            "rules · agents · hooks",
            "output-styles · status-line",
            "state/ · scripts/ (자동)"
        ],
        "sidebar_footer": "DK.method + 공식 확장",
        "footnote": "참조: .claude/ 구조 상세"
    },
    {
        "num": 8,
        "eyebrow": "PART 02 · SETTINGS",
        "title": "settings.json",
        "subtitle": "권한 · 훅 · MCP · 플러그인",
        "part": "part-2",
        "bg": "bg-tech",
        "body_lead": "settings.json 은 <strong>권한 관리</strong> (allow/deny/ask 배열), <strong>훅 정의</strong> (이벤트 → 명령), <strong>MCP 서버 활성화</strong>, <strong>플러그인 설정</strong> 을 한 곳에서 처리. 팀 공유 (git commit).",
        "body_paragraphs": [
            "defaultMode 로 전체 권한 수준 결정: 'default' (매번 물음), 'acceptEdits' (에디터 명령 자동 승인), 'plan' (계획만), 'bypassPermissions' (관리자 모드).",
            "env 섹션 으로 환경변수 정의. enabledMcpjsonServers, enabledPlugins 로 활성화할 MCP/플러그인 목록 관리."
        ],
        "sidebar_title": "◆ 주요 필드",
        "sidebar_bullets": [
            "permissions (allow/deny/ask)",
            "hooks (이벤트 훅)",
            "enabledMcpjsonServers",
            "enabledPlugins",
            "env (환경변수)"
        ],
        "sidebar_footer": "팀 설정 = 공유<br>개인 설정 = .local.json",
        "footnote": "참조: settings.json 스키마"
    },
    {
        "num": 9,
        "eyebrow": "PART 02 · COMMANDS",
        "title": "commands/ 슬래시 명령",
        "subtitle": "나만의 /report, /deploy 등 정의",
        "part": "part-2",
        "bg": "bg-tech",
        "body_lead": "파일명 = 명령어. <strong>report.md</strong> → <strong>/report</strong>. frontmatter 로 description, allowed-tools 등 명시. $ARGUMENTS 로 인자 받기. ! 접두 로 Bash 실행, @ 로 파일 참조.",
        "body_paragraphs": [
            "예시: report.md 에 '오늘 커밋 요약' 이라 쓰면 claude /report 하면 git log --since=yesterday 돌려서 결과 출력.",
            "명령은 description 을 읽고 트리거 → 본문 실행 → 결과 반환. 도구 제한 (allowed-tools) 으로 보안 확보. 팀 표준 명령을 여기에 모아두면 새 팀원도 쉽게 따라갈 수 있음."
        ],
        "sidebar_title": "◆ Command 구성",
        "sidebar_bullets": [
            "파일명 = 슬래시명",
            "YAML frontmatter",
            "Bash 실행: ! 접두",
            "파일 참조: @<path>",
            "인자: $ARGUMENTS"
        ],
        "sidebar_footer": "/mycommand --flag arg",
        "footnote": "참조: commands/ 사례"
    },
    {
        "num": 10,
        "eyebrow": "PART 02 · SKILLS",
        "title": "skills/ 자동 활성 스킬",
        "subtitle": "SKILL.md — YAML + 본문",
        "part": "part-2",
        "bg": "bg-tech",
        "body_lead": "스킬은 description 의 트리거 문구로 <strong>자동 활성</strong>. kebab-case 폴더명 필수, SKILL.md 정확히. 점진적 공개: 단계별 로드 (frontmatter → 본문 → scripts/references/assets).",
        "body_paragraphs": [
            "예시 description: '사용자가 PR 리뷰를 요청하면 자동 코드 리뷰 수행' — 이 문구를 보면 Claude 가 이 스킬을 자동으로 활성화.",
            "본문 5,000 단어 이하 권장. 더 크면 references/ 폴더에 세부 분리. Anthropic 공식 스킬 표준 따름 (Skill Design 규칙 참조)."
        ],
        "sidebar_title": "◆ Skill 원칙",
        "sidebar_bullets": [
            "kebab-case 폴더명",
            "SKILL.md 정확히",
            "description ≤ 1024자",
            "본문 ≤ 5,000단어",
            "트리거 문구 구체적"
        ],
        "sidebar_footer": "자동화로 효율성",
        "footnote": "참조: skill-design.md (Anthropic 표준)"
    },
    {
        "num": 11,
        "eyebrow": "PART 02 · RULES",
        "title": "rules/ 공통 규칙",
        "subtitle": "프로젝트 전체에 항상 적용",
        "part": "part-2",
        "bg": "bg-tech",
        "body_lead": "code-style.md, naming.md, testing.md 등 주제별 규칙. CLAUDE.md 에서 [참조] 로 연결 → 본문 중복 방지. rules/ 는 Claude가 항상 참조 가능한 공유 지식 풀.",
        "body_paragraphs": [
            "예: code-style.md 에 'camelCase 변수, PascalCase 클래스' 하면 CLAUDE.md 에는 '[코드 스타일은 rules/code-style.md 참조]' 만 적음. 수정할 때도 한 곳만 건드림.",
            "rules/ 로 분리하면 CLAUDE.md 를 500줄 이하로 유지 쉬움. 또한 같은 규칙을 여러 프로젝트에서 재사용 가능 (공통 rules.zip 공유)."
        ],
        "sidebar_title": "◆ rules/ 장점",
        "sidebar_bullets": [
            "주제별 분리",
            "CLAUDE.md 가볍게 유지",
            "참조 재사용",
            "팀 공유 규칙"
        ],
        "sidebar_footer": "파일명 예:<br>code-style.md<br>naming.md<br>testing.md",
        "footnote": "참조: .claude/rules/ 구조"
    },
    {
        "num": 12,
        "eyebrow": "PART 02 · AGENTS",
        "title": "agents/ 서브에이전트",
        "subtitle": "역할별 Claude 분리 실행",
        "part": "part-2",
        "bg": "bg-tech",
        "body_lead": "메인 Claude가 특정 작업을 서브에이전트에 위임. 각 agent.md 는 YAML frontmatter 로 model, tools, prompt 정의. 예: reviewer.md (코드 리뷰 전문), researcher.md (리서치 전문).",
        "body_paragraphs": [
            "토큰 격리: 메인 대화 토큰 절약 가능. 각 agent 는 독립 세션에서 실행.",
            "model 선택: 코드 리뷰 는 Opus, 빠른 사실 확인 은 Haiku 지정 가능. tools 제한으로 보안 확보 (예: reviewer 는 Read/Bash 만, 파일 쓰기 금지)."
        ],
        "sidebar_title": "◆ 서브에이전트 효과",
        "sidebar_bullets": [
            "토큰 격리 (메인 대화 절약)",
            "역할별 model 선택 가능",
            "도구 제한으로 안전성",
            "병렬 실행 가능"
        ],
        "sidebar_footer": "메인 Claude + N개<br>전문 서브에이전트",
        "footnote": "참조: agents/ 사례"
    },
    {
        "num": 13,
        "eyebrow": "PART 02 · HOOKS",
        "title": "hooks/ 이벤트 훅",
        "subtitle": "자동 실행되는 스크립트",
        "part": "part-2",
        "bg": "bg-tech",
        "body_lead": "훅은 <strong>특정 이벤트</strong>에서 자동 실행. 메모리·프롬프트보다 강력 (100% 실행 보장). settings.json 에 등록, .sh/.py 스크립트 연결.",
        "body_paragraphs": [
            "주요 이벤트: PreToolUse (툴 실행 직전, 차단 가능) · PostToolUse (툴 실행 후) · Stop (세션 종료) · SessionStart (세션 시작) · PreCompact (컨텍스트 압축 전).",
            "예: Edit/Write 후 자동 prettier --write $FILE 실행. 또는 rm -rf 명령 차단. 또는 세션 시작 시 상태 DB 검증. 이 모든 게 settings.json 설정 1줄로 100% 강제됨."
        ],
        "sidebar_title": "◆ 훅 이벤트 8+",
        "sidebar_bullets": [
            "PreToolUse · PostToolUse",
            "Stop · SessionStart",
            "PreCompact · PostCompact",
            "UserPromptSubmit",
            "+ 커스텀 이벤트"
        ],
        "sidebar_footer": "100% 실행 · 차단 가능<br>메모리보다 강력",
        "footnote": "참조: hooks/ 사례"
    },
    {
        "num": 14,
        "eyebrow": "PART 03 · ECOSYSTEM",
        "title": "출력 스타일 + 상태바",
        "subtitle": "Claude 응답 톤·형식 커스터마이징",
        "part": "part-3",
        "bg": "bg-subtle",
        "body_lead": "<strong>output-styles/</strong> — 응답 포맷 정의 (예: 한국어·영어 분기, 기술적/대화적 톤). <strong>status-line/</strong> — 터미널 하단에 커스텀 상태 표시 (세션 토큰·비용·브랜치 등). 팀 브랜딩·일관성에 도움.",
        "body_paragraphs": [
            "output-style 예: 'technical-kr' (한글 본문 + 영어 코드 주석 + 3줄 이내 요약). 또는 'management-brief' (임원진 보고용 한 장 요약).",
            "status-line 예: '[Session: 45K/100K · Branch: feat/xyz · Status: 🟢 Active]' 같은 정보를 터미널 하단에 계속 표시."
        ],
        "sidebar_title": "◆ 활용 예",
        "sidebar_bullets": [
            "공식 문서 톤",
            "팀 브리핑 형식",
            "커스텀 상태 모니터",
            "개인 선호 반영"
        ],
        "sidebar_footer": "일관성 강화",
        "footnote": "참조: output-styles/, status-line/"
    },
    {
        "num": 15,
        "eyebrow": "PART 03 · MCP SERVERS",
        "title": "MCP 서버 연결",
        "subtitle": "외부 서비스 = Claude 의 도구",
        "part": "part-3",
        "bg": "bg-subtle",
        "body_lead": "<strong>MCP (Model Context Protocol)</strong> — 외부 서비스를 Claude가 도구로 쓰게 하는 표준. 프로젝트 루트 .mcp.json 또는 유저 ~/.claude.json 에 정의. 서버 예: GitHub, Playwright, PostgreSQL, Slack 등.",
        "body_paragraphs": [
            "표준 프로토콜: stdio / http / sse 지원. 공식 서버 (Anthropic) + 커뮤니티 서버 다수 존재.",
            "Windows 주의: cmd /c 필수. 예: ['cmd', '/c', 'npx', '-y', '@modelcontextprotocol/server-github']"
        ],
        "sidebar_title": "◆ MCP 특징",
        "sidebar_bullets": [
            "표준 프로토콜",
            "stdio / http / sse",
            "공식 + 커뮤니티 서버",
            "Windows: cmd /c 필수",
            ".mcp.json 또는 ~/.claude.json"
        ],
        "sidebar_footer": "외부 API 직접 접근",
        "footnote": "참조: .mcp.json 스키마"
    },
    {
        "num": 16,
        "eyebrow": "PART 03 · PLUGINS",
        "title": "플러그인 시스템",
        "subtitle": ".claude-plugin/ + plugin.json",
        "part": "part-3",
        "bg": "bg-subtle",
        "body_lead": "<strong>플러그인 = commands/skills/hooks/agents를 묶은 배포 단위.</strong> plugin.json 에 이름·버전·의존성. marketplace.json 으로 여러 플러그인 번들 공유. 설치: claude plugin install <name> 또는 git clone.",
        "body_paragraphs": [
            "필수 필드: name, display, version, status (stable/experimental/spec-only), commands.",
            "선택 필드: skills, agents, hooks, dependencies.plugins (의존성), entry_points.default_command."
        ],
        "sidebar_title": "◆ 플러그인 장점",
        "sidebar_bullets": [
            "공유·재사용",
            "버전 관리",
            "팀 표준 배포",
            "공개 마켓플레이스"
        ],
        "sidebar_footer": "재사용 가능한<br>단위로 번들링",
        "footnote": "참조: .claude-plugin/ 구조"
    },
    {
        "num": 17,
        "eyebrow": "PART 03 · OFFICIAL PLUGINS",
        "title": "official plugins",
        "subtitle": "바로 쓸 수 있는 공식 도구",
        "part": "part-3",
        "bg": "bg-subtle",
        "body_lead": "Anthropic 에서 제공하는 공식 플러그인들. 설치: claude plugin install <name>@claude-plugins-official",
        "body_paragraphs": [
            "claude-md-management — CLAUDE.md 감사·개선",
            "code-review — PR 리뷰 자동화",
            "commit-commands — /commit, /commit-push-pr",
            "superpowers — 테스트·디버깅·플랜 스킬 번들"
        ],
        "sidebar_title": "◆ 설치 명령",
        "sidebar_bullets": [
            "claude-md-management",
            "code-review",
            "commit-commands",
            "superpowers"
        ],
        "sidebar_footer": "공식 표준 확장",
        "footnote": "참조: github.com/anthropics/plugins"
    },
    {
        "num": 18,
        "eyebrow": "PART 04 · PRINCIPLES",
        "title": "CLAUDE.md 프레임",
        "subtitle": "WHAT + WHY + HOW",
        "part": "part-4",
        "bg": "bg-tech",
        "body_lead": "<strong>WHAT</strong> — 컨텍스트 제공 (프로젝트 이름, 기술 스택, 의존성, 환경변수). <strong>WHY</strong> — 원칙 세팅 (아키텍처, 코드 스타일, 안티패턴). <strong>HOW</strong> — 워크플로우 (build, test, commit, deploy).",
        "body_paragraphs": [
            "500줄 이하 유지. 길면 .claude/rules/ 로 분리.",
            "5 Rules (Brij Kishore Pandey): (1) /init 먼저 (2) 500줄 이하 (3) Hooks 활용 (4) 월간 업데이트 (5) 참조 중심 (중복 금지)"
        ],
        "sidebar_title": "◆ 5 Rules",
        "sidebar_bullets": [
            "/init 먼저",
            "500 줄 이하",
            "Hooks 활용",
            "월간 업데이트",
            "참조 중심 (중복 금지)"
        ],
        "sidebar_footer": "WHAT/WHY/HOW<br>프레임 고수",
        "footnote": "참조: CLAUDE.md, guide.txt, docs/architecture-patterns.md"
    },
    {
        "num": 19,
        "eyebrow": "PART 04 · BE SPECIFIC",
        "title": "구체적으로 써라",
        "subtitle": "CLAUDE.md 모호성 ↔ 정확성",
        "part": "part-4",
        "bg": "bg-tech",
        "body_lead": "모호한 규칙은 AI가 기억 못 함. 구체적으로 써야 실행된다.",
        "body_paragraphs": [
            "❌ Vague: '깨끗한 코드' → ✅ Precise: 'camelCase 변수, PascalCase 컴포넌트'",
            "❌ Vague: '테스트 해' → ✅ Precise: 'npm test --watch, utils/ 커버리지 80%+'",
            "❌ Vague: '안전하게' → ✅ Precise: '에러는 try/catch, 로그에 PII 금지'"
        ],
        "sidebar_title": "◆ 구체화 체크리스트",
        "sidebar_bullets": [
            "수량 명시 (몇 %, 몇 줄)",
            "도구명 명시 (npm, pytest)",
            "파일/폴더 명시 (src/, utils/)",
            "명령어 전체 기재",
            "예외 케이스 명시"
        ],
        "sidebar_footer": "Precise = Followed",
        "footnote": "참조: best-practices.md"
    },
    {
        "num": 20,
        "eyebrow": "PART 04 · 3 SCOPES",
        "title": "3 스코프 · 같은 규칙 충돌 시",
        "subtitle": "Folder > Project > Global",
        "part": "part-4",
        "bg": "bg-tech",
        "body_lead": "세 단계 Memory 중 가장 가까운 곳의 규칙이 이김. Global CLAUDE.md 에 'tab 4 space', Project 에 'tab 2 space', Folder 에 'tab 8 space' 있으면 그 Folder 안에서는 8 space 적용.",
        "body_paragraphs": [
            "Global (~/.claude/CLAUDE.md): 모든 프로젝트 공통 (개인 선호)",
            "Project (./CLAUDE.md): 이 리포 규칙 (팀 컨벤션)",
            "Folder (./src/CLAUDE.md): 모듈 국소 규칙 (필요 시)"
        ],
        "sidebar_title": "◆ 우선순위",
        "sidebar_bullets": [
            "1. Folder (가장 가까움)",
            "2. Project",
            "3. Global (가장 멀음)",
            "Last wins on conflicts"
        ],
        "sidebar_footer": "가까운 규칙이<br>먼 규칙을 이김",
        "footnote": "참조: claude-md-design.md",
        "mermaid": True,
        "mermaid_code": """graph TD
  G["Global<br>~/.claude/CLAUDE.md"] --> P
  P["Project<br>./CLAUDE.md"] --> F
  F["Folder<br>./src/CLAUDE.md"]
  F --> W["워킹 디렉토리"]
  style W fill:#fff9e6"""
    },
    {
        "num": 21,
        "eyebrow": "PART 04 · HOOKS ENFORCEMENT",
        "title": "메모리 말고 Hook 으로",
        "subtitle": "70~80% 지킴 → 100% 실행",
        "part": "part-4",
        "bg": "bg-tech",
        "body_lead": "CLAUDE.md 의 규칙은 <strong>AI 가 '기억'</strong> 해야 적용 — 놓칠 수 있음. 훅은 <strong>시스템이 강제 실행</strong> — 100% 작동.",
        "body_paragraphs": [
            "예: '모든 Python 파일 저장 시 black 실행' → PostToolUse 훅으로 settings.json 에 등록. Edit/Write 이벤트마다 자동 실행 (메모리 전혀 안 쓰임).",
            "또는 '커밋 전 테스트 필수' → PreToolUse 훅으로 git commit 차단. hooks/pre-commit.sh 에서 npm test 돌려서 실패하면 차단. Claude 가 아무리 바빠도 강제됨."
        ],
        "sidebar_title": "◆ Hook 활용 사례",
        "sidebar_bullets": [
            "포매터 자동 실행",
            "커밋 전 검증",
            "위험 명령 차단",
            "보안 스캔",
            "자동 로깅"
        ],
        "sidebar_footer": "메모리: 70~80%<br>Hook: 100%",
        "footnote": "참조: hooks/, settings.json hooks"
    },
    {
        "num": 22,
        "eyebrow": "PART 05 · IN PRACTICE",
        "title": "시작하기",
        "subtitle": "Claude Code 새 프로젝트 10 분",
        "part": "part-5",
        "bg": "bg-subtle",
        "body_code": """□ claude code CLI 설치
□ cd project-root
□ claude 실행
□ /init — CLAUDE.md 초안 생성
□ CLAUDE.md 큐레이션 (WHAT/WHY/HOW)
□ .claude/rules/ 분리 (긴 규칙)
□ .claude/commands/ 추가 (자주 쓰는 명령)
□ settings.json 권한 설정
□ hooks 등록 (자동화)
□ .mcp.json 외부 서비스 연결
□ git commit .claude/ CLAUDE.md""",
        "sidebar_title": "◆ 첫 주 팁",
        "sidebar_bullets": [
            "작게 시작",
            "반복 시 규칙화",
            "주 1회 CLAUDE.md 갱신",
            "팀 공유 후 피드백"
        ],
        "sidebar_footer": "설정 완성도<br>= 팀 생산성",
        "footnote": "참조: CLAUDE_SETUP_GUIDE.md"
    },
    {
        "num": 23,
        "eyebrow": "PART 05 · TROUBLESHOOTING",
        "title": "흔한 실수",
        "subtitle": "이것만 피하면",
        "part": "part-5",
        "bg": "bg-subtle",
        "body_lead": "가장 흔한 실수 5가지와 해결책:",
        "body_table": [
            ("SKILL.md 철자 오류", "스킬 안 열림", "SKILL.md 정확히 (대소문자)"),
            ("YAML frontmatter '---' 누락", "잘못된 frontmatter 에러", "앞뒤 '---' 구분자 추가"),
            ("description 모호", "트리거 안 됨 또는 과잉", "구체 키워드·트리거 문구"),
            ("CLAUDE.md 500줄 초과", "무시됨", "rules/ 로 분리"),
            (".claude/ 직접 편집 (sync 있을 때)", "덮어씀 (원본이 SoT)", "plugins/ 원본 수정 후 sync")
        ],
        "sidebar_title": "◆ 피해야 할 것",
        "sidebar_bullets": [
            "파일 직접 편집 (.claude/ 안)",
            "500줄 초과 CLAUDE.md",
            "하드코딩된 API 키",
            "순환 의존성 (plugins)",
            "빈 task 를 done/ 이동"
        ],
        "sidebar_footer": "예방이 치료",
        "footnote": "참조: troubleshooting 가이드"
    },
    {
        "num": 24,
        "eyebrow": "PART 05 · EXPANSION",
        "title": "다음 단계",
        "subtitle": "팀 → 조직 → 커뮤니티",
        "part": "part-5",
        "bg": "bg-subtle",
        "body_lead": "개인 프로젝트에서 시작한 Claude Code 설정을 팀, 조직, 공개 커뮤니티로 확장하는 방법:",
        "body_paragraphs": [
            "개인 → 팀: .claude/ 와 CLAUDE.md 를 git 으로 공유. 또는 .claude-plugin/ 으로 플러그인 패키지화.",
            "팀 → 조직: 플러그인 마켓플레이스 운영. 조직 표준 규칙을 plugin.json 에 등록 후 배포.",
            "조직 → 공개: github.com/anthropics/plugins 에 기여 또는 독립 marketplace 운영."
        ],
        "sidebar_title": "◆ 배포 전략",
        "sidebar_bullets": [
            "개인: Git repo 공유",
            "팀: .claude-plugin/ 패키지",
            "조직: 마켓플레이스",
            "공개: GitHub · NPM"
        ],
        "sidebar_footer": "표준화 → 재사용",
        "footnote": "참조: marketplace.json"
    },
    {
        "num": 25,
        "eyebrow": "CLOSING",
        "title": "Learn More",
        "subtitle": "공식 문서 + 커뮤니티 리소스",
        "type": "closing",
        "part": "part-5",
        "bg": "bg-hero",
        "links": [
            ("docs.claude.com/claude-code", "공식 가이드"),
            ("github.com/anthropics/claude-code", "공식 리포"),
            ("github.com/anthropics/skills", "스킬 라이브러리"),
            ("DK.method by Brij Kishore Pandey", "CLAUDE.md 설계 프레임")
        ],
        "footer_text": "Created with Claude Code · Architecture Reference v1.0",
        "footnote": "감사: Brij Kishore Pandey 의 CLAUDE.md 설계 프레임"
    }
]

def generate_standard_slide(data):
    """Generate standard slide HTML"""
    num = data['num']
    title = data.get('title', '')
    subtitle = data.get('subtitle', '')
    eyebrow = data.get('eyebrow', '')
    part = data.get('part', 'part-1')
    bg = data.get('bg', 'bg-subtle')

    body_lead = data.get('body_lead', '')
    body_paragraphs = data.get('body_paragraphs', [])
    body_code = data.get('body_code', '')
    body_table = data.get('body_table', [])

    sidebar_title = data.get('sidebar_title', '')
    sidebar_bullets = data.get('sidebar_bullets', [])
    sidebar_footer = data.get('sidebar_footer', '')
    footnote = data.get('footnote', '')

    mermaid = data.get('mermaid', False)
    mermaid_code = data.get('mermaid_code', '')

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.css" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <link href="../styles/design-system.css" rel="stylesheet">
  <script src="https://code.iconify.design/iconify-icon/1.0.8/iconify-icon.min.js"></script>
'''

    if mermaid:
        html += '  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>\n'
        html += '  <script>mermaid.initialize({ startOnLoad: true, theme: "light" });</script>\n'

    html += f'''  <style>
    .mermaid-wrapper {{
      background: rgba(255, 255, 255, 0.6);
      border: 0.5px solid var(--fog);
      border-radius: 12px;
      padding: 24px;
      backdrop-filter: blur(10px);
      margin-top: 24px;
      display: flex;
      justify-content: center;
    }}
    .code-block {{
      background: rgba(26, 29, 36, 0.05);
      border: 0.5px solid var(--fog);
      border-radius: 8px;
      padding: 24px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 14px;
      line-height: 1.6;
      color: var(--ink);
      overflow-x: auto;
      margin-top: 24px;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    .table-wrapper {{
      width: 100%;
      margin-top: 24px;
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      padding: 12px;
      text-align: left;
      border-bottom: 0.5px solid var(--fog);
    }}
    th {{
      font-weight: 700;
      background: rgba(255, 255, 255, 0.4);
      color: var(--ink);
    }}
    td {{
      color: var(--stone);
    }}
  </style>
</head>
<body>
  <div class="slide {bg} {part}">
    <div class="slide-header">
      <span class="eyebrow">{eyebrow}</span>
      <span class="mono caption">{num:02d} / 25</span>
    </div>

    <div class="main-content">
      <h1 class="heading-1">{title}</h1>
      <p class="heading-2 text-stone" style="font-weight: 400;">{subtitle}</p>
'''

    if body_lead:
        html += f'      <p class="body-lead" style="margin-top: 28px;">{body_lead}</p>\n'

    if body_code:
        html += f'      <div class="code-block">{body_code}</div>\n'

    if body_table:
        html += '      <div class="table-wrapper"><table><thead><tr><th>실수</th><th>증상</th><th>해결</th></tr></thead><tbody>\n'
        for mistake, symptom, solution in body_table:
            html += f'      <tr><td>{mistake}</td><td>{symptom}</td><td>{solution}</td></tr>\n'
        html += '      </tbody></table></div>\n'

    for para in body_paragraphs:
        html += f'      <p class="body" style="margin-top: 24px;">{para}</p>\n'

    if mermaid and mermaid_code:
        html += f'      <div class="mermaid-wrapper"><div class="mermaid">{mermaid_code}</div></div>\n'

    html += '''
    </div>

    <div class="side-panel">
      <div class="bullet-box">
'''

    if sidebar_title:
        html += f'        <h3>{sidebar_title}</h3>\n'

    if sidebar_bullets:
        html += '        <ul>\n'
        for bullet in sidebar_bullets:
            html += f'          <li>{bullet}</li>\n'
        html += '        </ul>\n'

    if sidebar_footer:
        html += f'''        <hr>
        <div style="margin-top: 16px; font-size: 12px; color: var(--stone);">
          {sidebar_footer}
        </div>
'''

    html += '''      </div>
    </div>

    <div class="footer-border">
      <span class="footnote">'''
    html += footnote
    html += '''</span>
    </div>
  </div>
</body>
</html>
'''
    return html

def generate_closing_slide(data):
    """Generate closing slide"""
    num = data['num']
    title = data.get('title', '')
    subtitle = data.get('subtitle', '')
    links = data.get('links', [])
    footer_text = data.get('footer_text', '')
    footnote = data.get('footnote', '')

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.css" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&display=swap" rel="stylesheet">
  <link href="../styles/design-system.css" rel="stylesheet">
  <style>
    .closing {{
      width: 1920px;
      height: 1080px;
      background: linear-gradient(180deg, #F7F2EA 0%, #EDE4D3 100%);
      position: relative;
      overflow: hidden;
      padding: 100px 120px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .closing-title {{
      font-family: 'Fraunces', serif;
      font-size: 160px;
      font-weight: 600;
      line-height: 0.92;
      color: #1A1D24;
      margin-bottom: 24px;
    }}
    .closing-sub {{
      font-size: 32px;
      color: #6E685C;
      margin-bottom: 64px;
    }}
    .links-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 32px;
      margin-bottom: 64px;
    }}
    .link-item {{
      padding: 24px;
      background: rgba(255, 255, 255, 0.6);
      border: 0.5px solid var(--fog);
      border-radius: 12px;
    }}
    .link-item a {{
      font-size: 18px;
      color: #B8864E;
      text-decoration: none;
      font-weight: 600;
    }}
    .link-item a:hover {{
      text-decoration: underline;
    }}
    .link-desc {{
      font-size: 14px;
      color: #6E685C;
      margin-top: 8px;
    }}
    .closing-footer {{
      font-size: 14px;
      color: #6E685C;
      border-top: 0.5px solid var(--fog);
      padding-top: 24px;
    }}
  </style>
</head>
<body>
  <div class="closing">
    <div>
      <h1 class="closing-title">{title}</h1>
      <p class="closing-sub">{subtitle}</p>

      <div class="links-grid">
'''

    for link, desc in links:
        html += f'''        <div class="link-item">
          <a href="#">{link}</a>
          <div class="link-desc">{desc}</div>
        </div>
'''

    html += f'''      </div>
    </div>

    <div class="closing-footer">
      {footer_text}<br>
      <span style="color: #B8864E; font-weight: 600;">{footnote}</span>
    </div>
  </div>
</body>
</html>
'''
    return html

def main():
    """Generate all 25 slides"""
    for slide_data in SLIDES_DATA:
        if slide_data.get('skip'):
            continue

        num = slide_data['num']
        slide_type = slide_data.get('type', 'standard')

        if slide_type == 'closing':
            html = generate_closing_slide(slide_data)
        else:
            html = generate_standard_slide(slide_data)

        output_file = SLIDES_DIR / f"slide-{num:02d}.html"
        output_file.write_text(html, encoding='utf-8')
        print(f"[OK] Generated slide-{num:02d}.html")

if __name__ == '__main__':
    main()
    print(f"\n[DONE] Generated 24 slides (slide-01 manually edited)")
