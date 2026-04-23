# Orchestration Kit v1.0 — Multi-AI Automation Framework

Claude Opus 4.7 (Team Lead) + Codex (Implementation) + Haiku 4.5 (Review) — Plugin-Centric 멀티AI 오케스트레이션

---

## 24/7 자동화 (v1.0+)

- **SQLite 상태머신**: 원자적 워커·태스크·quota 관리 (`.claude/state/orca.db`, 8 테이블)
- **Watchdog + 자동부활**: 죽은 워커 복구, quota-aware 지수 backoff (10m→20m→40m→2h)
- **Budget ceiling**: 일일 비용 상한 초과 시 자동 breaker (신규 태스크 차단)
- **Haiku 4.5 검증**: Gemini 대체 기본 검증자 (Prompt caching, 90% 비용 절감, 2개 병렬)
- **4.7 라우팅**: Claude Opus 4.7 + Extended Thinking 우선, Codex/Gemini는 fallback (route.py)
- **통합 메트릭**: SQLite 기반 성능·비용·quota 대시보드 (metrics-report.py)

설정: `python .claude/scripts/init-state-db.py` → `.claude/scripts/watchdog-start.bat`  
상태: `python .claude/scripts/route.py --status`  
상세: [guide.txt](guide.txt) 섹션 7

---

## Quick Start

### 방법 1: setup.exe (추천)
[Releases](https://github.com/bernakilljos/orchestration/releases) 에서 **OrchestrationKit-Setup.exe** 다운로드 → 더블클릭 → 경로 선택 → 설치 끝

### 방법 2: git clone
```bat
git clone https://github.com/bernakilljos/orchestration.git
cd orchestration
setup\setup.bat C:\work\myproject
```

### 방법 3: 사일런트 설치
```bat
OrchestrationKit-Setup.exe /VERYSILENT /DIR="C:\work\myproject"
```

### 설치 후
Claude Code 실행 → 자동으로 환경 구성 완료  
추가 MCP 필요 시: `/plug_dev`, `/plug_data` 등 슬래시 커맨드 실행

---

## 포함 항목

| 카테고리 | 수량 | 내용 |
|---------|------|------|
| Skills | 38개 + 3개 | skill-01~38 (레거시) + exec_orca-auto, state_session, route_dispatch |
| Hooks | 9개 명세 + 9개 스크립트 | hook-00~08 + Python/Shell 실행 스크립트 |
| Agents | 6개 | team-lead, implementer, reviewer, architect, monitor, designer |
| Plugins | 13개 | exec_orch, exec_voice, exec_learning, design_ppt/excel/word, review_qa, mcp_dev/data/collab/web/docs/media |
| Commands | 20개 | loop-stop, plug_*, check-*, godmode, 10x, brief 등 |
| Codex 연동 | AGENTS.md + .codex/ | Codex용 지시서 + MCP config.toml |

---

## AI 역할 분담

| AI | 역할 | 명령어 |
|----|------|--------|
| Claude | 팀장: 설계·판단·승인·보완 | 대화에서 직접 |
| Codex | 구현: 500줄+ 1차 구현 | `codex-a --auto` (단일) / `codex-auto 4` (병렬) |
| Gemini | 검증: 리뷰·보안·문서화 | `gemini-a --verify` (단일) / `gemini-auto 2` (병렬) |

### 명칭 정리
```
codex-a     = 단일 태스크 실행
codex-auto  = 병렬 구현 워커 (기본 4개)
gemini-a    = 단일 검증 실행
gemini-auto = 병렬 검증 워커 (기본 2개)
claude-auto = Claude 병렬 워커 (기본 3개)
```

---

## 파이프라인

```
Hook → Planner → Executor → Validator → State → Retry
  ↓        ↓          ↓           ↓         ↓       ↓
사전확인  Claude    Codex 4개   Gemini 2개  스냅샷  3회재시도
         설계      구현        검증        저장    →에스컬레이션
```

### 디자인 파이프라인
```
PPT:   Claude → Canva → Mermaid → Figma
Excel: Claude → openpyxl → 차트 → Google Sheets
Word:  Claude → python-docx → Mermaid → PDF
```

---

## 플러그인 구조 (plugins/)

```
exec_orch      오케스트레이션 핵심 (pipeline.md)
exec_voice     음성 STT·TTS·회의록·음성명령
exec_learning  세션학습·패턴저장·요약
design_ppt     PPT 자동생성
design_excel   Excel 자동생성
design_word    Word 자동생성
review_qa      코드리뷰·보안·품질
mcp_dev        개발 MCP (GitHub·Docker·AWS)
mcp_data       데이터 MCP (MySQL·MongoDB·BigQuery)
mcp_collab     협업 MCP (Slack·Notion·Jira)
mcp_web        웹자동화 MCP (Playwright·Puppeteer)
mcp_docs       문서처리 MCP (PDF·DOCX·OCR)
mcp_media      미디어 (Whisper·TTS·FFmpeg)
```

각 플러그인: `commands/` + `skills/` + `agents/` + `hooks/` + `codex/` + `rules.md`

---

## Setup Modules (11단계)

| # | Module | 내용 |
|---|--------|------|
| 01 | core | .claude 폴더 + 설정 복사 |
| 02 | defender | Windows Defender 예외 |
| 03 | settings | Claude 글로벌 설정, PS UTF-8 |
| 04 | commands | codex-a, gemini-a 등 글로벌 설치 |
| 05 | services | status-push, remote-agent |
| 06 | prereqs | Node.js, Claude Code, Cloudflared |
| 07 | github | Git 초기화, GitHub repo 연동 |
| 08 | plugins | install-plugins.ps1 (TTY 없이 안정 설치) |
| 09 | finalize | exec_voice 도구 설치, 로컬LLM 감지, Claude 실행 |
| 10 | video-restore | CodeFormer + Real-ESRGAN |
| 11 | media-enhance | 오디오/PDF/PPT 의존성 |

---

## MCP 추가 설치

기본 설치됨: `context7`, `playwright`, `thinking`  
자동 연결 (claude.ai): Figma, Gamma, Gmail, Canva, Mermaid

추가 설치 — Claude에서 실행:
```
/plug_dev      GitHub, Docker, AWS, Vercel...
/plug_data     MySQL, MongoDB, BigQuery...
/plug_design   Canva, Figma, Gamma, PowerPoint...
/plug_collab   Slack, Notion, Jira, Gmail...
/plug_media    Whisper, TTS, FFmpeg
/plug_all      전체 한번에
```

---

## Codex 연동 (.codex/)

```toml
# .codex/config.toml
[mcp_servers.filesystem]  # 파일 처리
[mcp_servers.github]      # GitHub
[mcp_servers.playwright]  # 웹 자동화
[mcp_servers.figma]       # 디자인
[mcp_servers.canva]       # 디자인
[mcp_servers.mermaid]     # 다이어그램
```

`AGENTS.md` = Codex용 루트 지시서 (`CLAUDE.md` 대응)

---

## 확장

```
새 플러그인:  plugins/내이름/commands/커맨드명.md
새 스킬:     .claude/skills/exec_이름.md
새 에이전트: .claude/agents/agent-07-name.md
새 훅:       .claude/hooks/hook-09-name.md
```
