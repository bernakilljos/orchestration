# Orchestration Kit v1 — 자산 카탈로그 (전수)

> **용도**: kit 이 실제 제공하는 **모든 자산** 을 카테고리별로 훑기. 사용자가 "이거 있어?" 물을 때 즉답 가능.
> **작성**: 2026-08-12

---

## 1. Commands (200+) — 사용자가 슬래시로 호출

### 디자인 산출물
| Command | 용도 |
|---|---|
| `/design_ppt` `/make-ppt` | PPT 자동 생성 (HTML/CSS → Playwright → PPTX) |
| `/design_word` `/word-make` | Word (python-docx + Mermaid + PDF) |
| `/design_excel` `/excel-make` | Excel (openpyxl + 차트 + Google Sheets) |
| `/pdf-generate` `/pdf-fill` `/pdf-sign` `/pdf-secure` | PDF 생성·양식 채우기·서명·암호화 |
| `/ai-system-stages` | AI 시스템 6단계 PPT |

### 랜딩·웹
`/design_web-landing` · `/design_web-portfolio` · `/design_web-blog` · `/design_web-seo-meta`

### 아키텍처 다이어그램
`/arch-auto` · `/arch-mindmap` · `/arch-layered` · `/arch-cheatsheet`

### RAG 8종
`/rag-naive` · `/rag-hybrid` · `/rag-hyde` · `/rag-graph` · `/rag-multimodal` · `/rag-adaptive` · `/rag-corrective` · `/rag-agentic`

### 오케스트레이션
`/exec_orch` · `/godmode` · `/orcauto-start` · `/orcauto-stop` · `/exec_status` · `/loop-stop` · `/vibe-loop`

### VPS 24/7 원격
`/exec_remote-setup` · `/exec_remote-deploy` · `/exec_remote-ssh` · `/exec_remote-tmux` · `/exec_remote-status` · `/exec_remote-mobile`

### 크론·스케줄러
`/exec_scheduler-cron` · `/exec_scheduler-workflow` · `/exec_scheduler-run-now` · `/exec_scheduler-status` · `/exec_scheduler-history` · `/exec_scheduler-retry`

### 음성·회의
`/exec_voice` · `/meeting` · `/transcribe` · `/speak` · `/voice-task` · `/voice-status`

### 소셜
`/yt-upload` · `/yt-research` · `/yt-analytics` · `/ig-upload` · `/ig-research` · `/ig-analytics`

### 영상·오디오
`/video-shorts` · `/video-subtitle` · `/video-thumbnail` · `/video-restore` · `/video-edit` · `/video-template`
`/music_studio-compose` · `/music_studio-mix` · `/music_studio-master` · `/audio-restore` · `/image-restore` · `/image-generate`

### MCP 설치
`/mcp_dev` · `/mcp_data` · `/mcp_collab` · `/mcp_web` · `/mcp_docs` · `/mcp_media` · `/mcp_queue` · `/mcp_social` · `/install-mcp` · `/plug_all` · `/plug_design` · `/plug_dev` · `/plug_data` · `/plug_collab` · `/plug_web` · `/plug_docs` · `/plug_media`

### 오프라인·로컬
`/exec_offline-setup` · `/exec_offline-model` · `/exec_offline-vector` · `/exec_offline-observe` · `/exec_offline-route`

### 검증·리뷰
`/review_qa` · `/gemini-verify` · `/security` · `/performance` · `/sec-scan` · `/test-gen` · `/screenshot` · `/verify` · `/validate` · `/check` · `/check-agents` · `/check-services`

### AI 위임
`/gpt-dispatch` · `/grok-dispatch` · `/copilot-dispatch` · `/cursor-dispatch` · `/gemini-recap` · `/gemini-verify`

### 효율 모드
`/10x` · `/godmode` · `/brief` · `/effort-mythos` · `/fast` (built-in) · `/loop`

### 인터랙티브·아티팩트
`/claude-artifact` · `/claude-ask` · `/claude-connectors` · `/artifacts` · `/claude-thinking` · `/claude-status`

### 회고·학습
`/summarize` · `/learn` · `/recall` · `/gemini-recap` · `/score-task` · `/token-stats`

### HITL 승인
`/approve` · `/reject` · `/approvals`

### 설치·배포
`/install-to <target>` · `/sync-team` · `/anthropic-skill <name>` · `/copilot-dispatch`

### 기타
`/ooda` · `/scout` · `/critique` · `/devil` · `/teacher` · `/explainlikeim5` · `/ghost` · `/pitch` · `/compare` · `/analyze-improve` · `/cleanup` · `/guard-save` · `/help`

---

## 2. Skills (250+) — 사용자 지시 매칭 시 **자동 활성**

Command 는 슬래시로 호출, Skill 은 **description 매칭 자동 발동**.

주요 SKill 카테고리:
- **auto-planner** — 사용자 지시 받자마자 5단계 plan (자동)
- **direction-first** 관련 — 대상 확정 자동
- **user-emotion-auto-response** — 감정·상황 12 매핑 자동
- **asset-creation-workflow** — 새 자산 생성 시 유형별 표준
- **exec_orca-auto** — 워커 spawn 자동
- **route_dispatch** — AI 라우팅 결정
- **prompt-techniques** — 12 프롬프트 강화 기법 (Role·Negative·CoT·Self-consistency·ToT·ReAct·RAG 등)
- **auto-layout-fit** — 페이지 콘텐츠 fit 자동
- **post-codex-verify** — Codex hallucination 사후 검증

전체: `.claude/skills/*.md` + `plugins/*/skills/*.md`

---

## 3. Memory (재발 방지 학습) — `~/.claude/projects/C--pjt-orchestration-v1/memory/`

세션 간 지속 · Claude 가 자동 recall (`recall-memory.py` + RAG 인덱스).

### feedback_* (사용자 학습, 40+)
- `confirm_target_first` · `full_survey_read_all` · `no_duplicate_function` · `install_order` · `user_emotion_mapping`
- `zero_touch_automation` · `no_hardcoded_paths` · `template_kit_principle` · `no_version_suffix`
- `page_fit_verification` · `full_page_content_fit` · `png_builder_universal`
- `auto_planner_required` · `no_deflection` · `verify_before_report` · `no_false_pass_report`
- `screen_verify_required` · `auto_install_no_ask` · `official_features_auto_check`
- `industry_ml_transfer_style` · `insight_explain_simple` · `no_whitespace_design`
- `user_enfp_adhd_style` · `common_kit_not_domain` · `install_guide_on_every_change`
- `claude_bypass_permissions` · `secret_commit_consent` · `no_delete_template` · `no_delete_without_justification`

### reference_* (외부 참조 인덱스)
- `opus_5_launch` · `opus_4_8_launch` · `fable_5_launch` · `sonnet_5_launch`
- `audit_tokens` · `design_screens_folder` · `image_sources_pngtree`
- `company_context` · `claude_web_projects_setup`

### project_* (프로젝트 상태)
- `fable_5_usage_strategy` · `next_session_tasks`

**활용**: 사용자 지시 시 자동 recall (`.claude/hooks/user-prompt-auto-planner.sh` 안 memory recall) — top 3 kw + top 2 rag.

---

## 4. Context Cache — `.claude/context-cache/`

세션 스냅샷 · 자동 복구.

- `session-snapshot.md` — 이전 세션 종료 스냅샷 (다음 세션 시작 시 복구 제안)
- `auto-compact-recommended` — 컨텍스트 임계치 도달 시 다음 turn 자동 `/compact`
- `guard.log` — 세션 guard 로그

Skill: `exec_session_guard` · `guard-save`

---

## 5. State DB — `.claude/state/orca.db` (SQLite, 8 테이블)

원자적 상태 관리:
- **workers** — 워커 heartbeat·상태
- **tasks** — task-instruction 큐·진행·완료
- **metrics** — 성능·비용·quota
- **quota** — API 한도 관리 (10m→20m→40m→2h 지수 backoff)
- **budget** — 일일 예산 (`route.py --set-daily-limit`)
- **session** — 세션 통합 상태
- **approval_requests** — HITL 승인 큐 (v2 schema)
- **prompt_history** — 최근 프롬프트 (반복 감지용)

---

## 6. References Toolkit (49개) — `plugins/exec_orch/references/`

RAG cite 형식 주입용 도메인 지식:
- academic-research · accessibility · api-gateway · audio-speech
- blockchain-web3 · caching-performance · cloud-infrastructure
- cms-content · communication-messaging · workflow-automation 등 49 toolkit
- 사용: prompt-techniques.md § RAG (#12) 로 자동 인용

---

## 7. Roadmap (예정 26개) — `docs/2026-04-19/로드맵.md`

Phase 1~3 스펙 · 미래 신규 플러그인.

**Phase 1 (완료 · Spec-only → stable)**:
- ai_rag · exec_offline · exec_scheduler · design_web · design_pdf · cost_youtube · mcp_social · design_video · mcp_queue · music_studio (10개)

**Phase 2/3 (예정)**: 26개 신규 스펙 (상세는 로드맵.md)

---

## 8. Agents (20+) — subagent 격리 실행

Task tool 로 spawn:
- **claude** (catch-all) · **general-purpose**
- **Explore** — 코드베이스 탐색 (breadth quick/medium/thorough)
- **Plan** — 구현 계획 설계
- **code-reviewer** · **test-runner** · **judge** (Haiku 채점)
- **explorer** · **data-scientist** · **python-pro** · **typescript-pro**
- **llm-architect** · **ml-engineer** · **claude-code-guide**

메인 컨텍스트 격리 · 결과만 요약 반환.

---

## 9. Hooks (55) — 이벤트 자동 발동

주요:
- **SessionStart** — hook-00-init (헌장 A~F 노출) · auto-install-deps · cleanup-pollution · check-workers
- **UserPromptSubmit** — user-prompt-auto-planner (5단계) · detect-deflection · detect-repeat-request · detect-user-emotion · periodic-rules-reminder
- **PreToolUse Write/Edit** — detect-asset-creation · block-version-suffix · check-mojibake · protect-critical-files
- **PreToolUse Bash** — pre-install-lock (install 순서 강제) · pre-commit-full-check
- **PostToolUse** — auto-smoke-test · check-sync-drift · verify 도구 자동 발동
- **Stop / SessionEnd** — stop-snapshot · stop-doc-summary · hook-gemini-recap

전체: `.claude/hooks/*` + `plugins/*/hooks/*`

---

## 10. Rules (23) — `.claude/rules/*.md` · SoT

`direction-first` · `user-emotion` · `failure-mode` · `consistency` · `best-practices` · `screen-verify` · `no-false-report` · `teaching-doc` · `approval-gate-rules` · `file-locking-policy` · `cleanup-policy` · `codex-rules` · `gemini-review-policy` · `mcp-install-rules` · `post-codex-verify` · `plugin-structure` · `sync-workflow` · `frontmatter` · `file-naming` · `indentation` · `claude-md-design` · `skill-design` · `industry-transfer-format`

---

## 11. Setup Modules (11단계) — `setup/modules/`

01 core · 02 defender · 03 settings · 04 commands · 05 services · 06 prereqs · 07 github · 08 plugins · 09 finalize · 10 video-restore · 11 media-enhance

---

## 12. MCP Servers — `.mcp.json` 및 카테고리별 설치

- **기본**: context7, playwright, thinking, filesystem, sequentialthinking, fetch
- **디자인** (`/mcp_dev`): Canva · Figma · Gamma · Mermaid · PowerPoint · Google Slides
- **개발** (`/mcp_dev`): GitHub · GitLab · Docker · K8s · AWS · Firebase · Supabase · Vercel · Netlify
- **데이터** (`/mcp_data`): PostgreSQL · MongoDB · BigQuery · Snowflake · Sheets · Airtable
- **협업** (`/mcp_collab`): Slack · Notion · Jira · Trello · Gmail · Google Calendar · Telegram
- **웹** (`/mcp_web`): Playwright · Puppeteer
- **문서** (`/mcp_docs`): PDF · DOCX · OCR (Tesseract)
- **미디어** (`/mcp_media`): Whisper (STT) · edge-tts (TTS) · FFmpeg

Anthropic 공식 커넥터 (claude.ai 자동): Figma · Gamma · Gmail · Canva · Mermaid · Slack · GitHub · Notion

---

## 12.5 API 비용 매트릭스 (무료 vs 유료)

| 카테고리 | 무료 (로컬·내장) | 유료 (API) |
|---|---|---|
| **파일·grep·검색** | Grep·Glob·Bash 도구 | — |
| **간단 요약·분류** | Ollama Llama 3.3·Gemma·Mistral | Haiku 4.5 ($0.25/$1.25) |
| **RAG 벡터 검색** | ChromaDB 로컬 | Pinecone·Weaviate |
| **subagent 격리** | Agent Explore·general-purpose | Managed Agents API |
| **관측·대시보드** | Phoenix self-hosted | LangSmith·Arize |
| **복잡 설계·리팩터** | (로컬 한계) | Opus 5 ($5/$25) · Sonnet 5 |
| **초난도** | (로컬 한계) | Opus 5 + ultracode · Fable 5 ($10/$50) |
| **감사·비즈니스** | (로컬 무의미) | claude.ai Web develop (사용자 구독 · 브라우저) |
| **디자인 MCP** | Mermaid CLI (로컬) | Canva·Figma·Gamma OAuth |
| **음성 STT** | Whisper 로컬 (base·small) | Whisper API · edge-tts |
| **이미지 생성** | Pollinations.ai (무료 익명) | DALL-E·Midjourney API |
| **영상 편집** | FFmpeg·Real-ESRGAN 로컬 | Runway ML API |

**API 비용 없이 자동화**: `/exec_offline-setup` (Ollama + ChromaDB + Phoenix) → 대부분 태스크 로컬. 복잡 설계·초난도만 API.

**budget 게이트**: `route.py --set-daily-limit <USD>` — 상한 초과 시 로컬 fallback 자동.

## 13. 사용자 도메인 (ISMS-P · RMS · ITCEN ESG) 특화

memory `reference_company_context.md`:
- ISMS-P 자격증 3년 (개인 도메인)
- 아이티센 코어 ESG 사업부 개발팀 리더
- RMS (MicroRisk-X 신사업 PPT v14 저자)

특히 유용한 command:
- `/design_ppt` · `/design_word` · `/pdf-generate` (제안서·보고서)
- `/rag-*` (RAG 8종 · 도메인 지식 기반 검색)
- `/security` · `/sec-scan` (ISMS-P 정합)
- `/analyze-improve` (프로젝트 개선점 추천 — XAI · Zero Trust · RAG · 이벤트)

---

## 14. 참조

- **CLAUDE.md § 7** — 재발 방지 헌장 A~F
- **guide.txt** — 사람용 상세 가이드 (§ 1~19)
- **outputs/install/**:
  - `orchestration-kit-total-guide.md` — 총망라
  - `session-bootstrap-prompt.md` — Claude.ai Projects 붙임용
  - `web-cli-bridge.md` — Web ↔ CLI 4방식
  - `claude-web-projects-setup.md` — Projects 세팅
  - `kit-catalog.md` — 이 파일
- **docs/architecture-patterns.md** — 설계 원칙 9가지
- **docs/2026-04-19/로드맵.md** — Phase 1~3 예정
- **~/.claude/projects/.../memory/MEMORY.md** — memory 인덱스

---

**한 문장**: kit 은 commands + skills + memory + context + state DB + references + 로드맵 + agents + hooks + rules + setup + MCP 전방위 자산. 사용자 지시 시 이 카탈로그 참고해서 알맞은 command·skill·자산을 먼저 제안.
