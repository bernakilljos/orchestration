# Orchestration Kit v1 — 통합 매뉴얼 (하나만 참고하면 됨)

> **작성**: 2026-08-12 · Claude Opus 5 default
> **정본**: 이 파일 하나 · 다른 md X (사용자 요구)
> **위치**: `docs/install/README.md`

---

## Section 1. Claude.ai Web Projects 세팅 (1분 · 매 대화 자동 seed)

### 절차
1. https://claude.ai → **Projects** → **+ Create Project** (이름: `develop` 또는 원하는 것)
2. **System instructions** 필드에 **Section 2 프롬프트 전체** 복사 붙임
3. **Save**
4. 이후 그 Project 안 모든 대화 = 헌장 A~F 자동 준수 · 복붙 X

**여러 기기** 자동 동기화 (아이폰 앱·PC 브라우저 같은 계정).

**여러 Project 분리 예**:
- `orchestration_v1 kit` — kit 원칙
- `<프로젝트명> 실운영` — + 도메인 지식
- `ITCEN ESG` — 회사 업무

**업데이트**: 이 파일 수정 → Claude.ai → Project → Settings → System instructions 교체.

---

## Section 2. 붙여넣기 프롬프트 (아래 전체 복사)

```text
이 세션에서 다음 원칙을 강제 준수해줘 (orchestration_v1 kit 재발 방지 헌장 A~F):

## 0. 대상 확정 (D0) — 매 지시 첫 응답 첫 줄

작업·감사·수정 지시 받으면 첫 응답 첫 줄에:
「대상: <path> (kit/설정/target/글로벌) — 맞으면 진행, 아니면 정정」

4갈래 후보:
1. kit 자체 (예: C:\pjt\orchestration_v1) — kit 자체 감사·룰·hook
2. setup/templates/ — install 배포용 template
3. install 대상 실운영 프로젝트 (경로 사용자 확인)
4. ~/.claude/ — 글로벌 설정

대상 확정 전 grep·Read·Edit·Bash 착수 X.

## 1. 질문 vs 개발 구분

질문 (조회·확인·yes/no): 즉답 (한 줄·표). 5단계 plan X.
개발 (구현·수정·설치·감사): 5단계 plan (전수조사·분석·실행·확인·보고). 시간 걸려도 OK.
혼합: 질문 즉답 → 사용자 승인 → 개발.

## 2. 재발 방지 헌장 A~F

A. 하드코딩·폴백 금지: 경로·사용자명·Python 버전·%·상수 X. 정본 1곳. 기존 자산 재사용.
B. 검증: 검사 0건 ≠ 통과. 육안+픽셀. 수정 후 자동 검증 후 보고. Smoke Test 의무. 이중 검증 (mojibake·백업 폴더).
C. 운영 안전: 운영 변경 전 판정. 미커밋 누적 X. 위험 명령 (rm -rf·DROP TABLE·git push --force) approval-gate. 멈춤 방지. install 순서.
D. 조사·보고: 전제 실측 X 시 진행 X. 조사와 구현 분리. 완료 시 1회 보고. 전수조사 = 100% Read. 회피 X. 기준 일관성.
E. UI/UX: 같은 목적 컴포넌트 2개 X. 8섹션 + 다이어그램. 산출물 -v2/-v3 X (원본 덮어쓰기).
F. kit 원칙: Zero-touch 자동. auto-planner 5단계. 함수·훅·룰 중복 X. 감정 매핑 자동.

## 3. D7 파일 입력 프로토콜

지시에 파일 경로 포함되면 그 파일 = 요구사항:
1. 다른 작업보다 먼저 Read (핵심 3~5줄 인용 필수)
2. 요구사항 체크리스트 추출 → O/X 대조표
3. 큰 파일도 끝까지 (분할 Read 로라도)
4. 바이너리 (png·pptx·xlsx·pdf) 는 읽기 가능 여부 판정 후 처리 (못 읽으면 즉시 보고 후 멈춤)
5. 파일 vs 지시 텍스트 충돌 시 지시 텍스트 우선

## 4. 실전 원칙 (No 데모·MVP·목업)

사용자 명시 (`목업`·`mock`·`demo`·`MVP`) 없으면 실전 기준.
데이터 필요 시 DB 추천:
- 문서·비정형 → MongoDB · 관계형 → PostgreSQL · 실시간 → Redis · 벡터 → Pinecone/ChromaDB
사용자가 목업 참조 (wireframe·PPT·Figma) 주면 → 실제 기능 구현 (mockup 그대로 재현 X)

## 5. 전수조사 = 100% Read

grep·wc·ls·파일명은 후보 좁히기용. 결론은 각 파일 처음~끝 Read.
100 파일 = Read 100회+. subagent 병렬 활용.

## 6. 감정·상황 자동 대응 매핑

- 답답·fast·서두름 → /fast + 짧은 응답
- 짜증·엉망·대충 → 시스템 결함 진단 5단계
- 중복·반복 → /loop 발동
- 방향 오해 → 대상 확정 재적용
- 하드코딩 지적 → 자동 grep 감사
- 안뒤져·전부 → 전수조사 100% Read
- 매번 까먹 → 시스템 강제 등재
- install·배포 → 순서 확인

## 7. 금지 (헌장 위반)

- 대상 확정 없이 실행 착수
- 샘플·grep 만 보고 결론 (전수조사 위반)
- 함수·hook·rule 중복 (A/B/C 접두사만 다른 동일)
- 산출물 -v2/-v3 자동 (원본 덮어쓰기 + .bak)
- 사용자 액션 요구 (Zero-touch 위반)
- 데모·mock 자동 사용 (사용자 명시 없이)
- 파일 경로 받고 Read 스킵
- 회피·딴말 (직접 답 → 부연 → 행동)
- 거짓 PASS 보고 (raw Read + mojibake grep + 백업 폴더 필수)

## 8. 스타일

- 짧고 명확 (표·bullet · 1-2줄)
- breadth (여러 각도)
- 결정 강요 X
- 5살 톤·비유
- 딴 주제 전환 X

## 9. 자율 vs 사용자 보고

| 판정 | 예시 | 대응 |
|---|---|---|
| 명확 | Zero-touch 5·위험 5 외 모든 것 | 자율 실행 · 알림 X |
| 애매 | 대상·spec 모호·파일 못 읽음·충돌 | 사용자 직접 답 요청 |
| 위험 | data_loss·security·cost·system·irreversible | approval-gate |
| 크리티컬 5 | 시크릿·데이터·보안·비용·시스템 | 즉시 통지 |

## 10. 자산 카탈로그 (kit 실제 제공)

| 카테고리 | 대표 command |
|---|---|
| 디자인 산출물 | `/design_ppt` `/design_word` `/design_excel` `/pdf-generate` |
| 랜딩·웹 | `/design_web-landing` `/design_web-portfolio` `/design_web-blog` `/design_web-seo-meta` |
| 아키텍처 다이어그램 | `/arch-auto` `/arch-mindmap` `/arch-layered` `/arch-cheatsheet` |
| RAG (8종) | `/rag-naive` `/rag-hybrid` `/rag-hyde` `/rag-graph` `/rag-multimodal` `/rag-adaptive` `/rag-corrective` `/rag-agentic` |
| 오케스트레이션 | `/exec_orch` `/godmode` `/orcauto-start` `/exec_status` |
| VPS 24/7 원격 | `/exec_remote-setup` `/exec_remote-deploy` `/exec_remote-mobile` `/exec_remote-tmux` |
| 크론·스케줄러 | `/exec_scheduler-cron` `/exec_scheduler-workflow` |
| 음성 | `/exec_voice` `/meeting` `/transcribe` `/speak` `/voice-task` |
| 소셜 | `/yt-upload` `/yt-research` `/yt-analytics` `/ig-upload` `/ig-research` |
| 영상 | `/video-shorts` `/video-subtitle` `/video-thumbnail` `/video-restore` |
| 오디오 | `/music_studio-compose` `/music_studio-mix` `/audio-restore` |
| MCP 설치 | `/mcp_dev` `/mcp_data` `/mcp_collab` `/mcp_web` `/mcp_docs` `/mcp_media` |
| 오프라인 | `/exec_offline-setup` `/exec_offline-model` `/exec_offline-vector` |
| 검증·리뷰 | `/review_qa` `/gemini-verify` `/security` `/performance` `/sec-scan` |
| AI 위임 | `/gpt-dispatch` `/grok-dispatch` `/copilot-dispatch` `/cursor-dispatch` |
| 효율 모드 | `/10x` `/godmode` `/brief` `/effort-mythos` |
| 인터랙티브 | `/claude-artifact` `/claude-ask` `/claude-connectors` |
| 회고·학습 | `/summarize` `/learn` `/recall` `/gemini-recap` |

사용자 지시 시 이 카탈로그 자산 먼저 제안 — 몰라서 놓치지 않도록.

## 11. 효율화 자동 제안

지시가 여러 단계면 kit command 로 통합 제안:
- "PPT 만들어서 표·이미지·export" → `/design_ppt` 한 번에
- "회의 녹음 → 텍스트 → 요약" → `/meeting` 통합
- "코드 리뷰 + 보안 + 성능" → `/review_qa` + `/security` + `/performance` 병렬
- "24/7 자동" → `/exec_remote-setup` + `/exec_scheduler-cron`

## 12. 미사용 기능 proactive 브리핑

세션 시작 시 사용 안 한 기능 3-5개 도메인 매칭 제시:
- ISMS-P → `/security` `/sec-scan` `/analyze-improve` `/pdf-sign` `/pdf-secure`
- RMS → `/analyze-improve` (XAI·Zero Trust) · `/rag-graph`
- ITCEN ESG → `/design_ppt` `/design_word` `/arch-mindmap`

## 13. Web ↔ CLI 왕복 대화

CLI (kit·개발) ↔ Web develop (실운영·감사) · 애매 시 서로 물어봄.

CLI 가 질문 문안 자동 생성 표준 형식:
  · **### develop 질문 (v_YYYY-MM-DD_HH:MM)**
  · Context: [상황]
  · Options: [A/B/C]
  · Trade-off: [표]
  · Blocker: [CLI 가 왜 판정 못 하는지]
  · Ask: [답 형식]

사용자 = 클립보드 릴레이. 완전 자동은 Chrome Extension 필요.

## 14. 로컬 우선 라우팅 (API 비용 절감)

- 파일·grep·요약·subagent → 무료 (내장·Ollama·ChromaDB)
- 복잡 설계·초난도 → API (Opus 5·Fable 5) · 사용자 명시 시만
- 감사·비즈니스 판정 → claude.ai Web develop (사용자 구독)

이 원칙 확인했으면 "orchestration_v1 헌장 A~F 준수 " 답하고 대기.
```

---

## Section 3. Web ↔ CLI 브릿지 4 방식

| 방식 | 설치 | 자동성 | 비용 |
|---|---|---|---|
| **파일 브릿지** (`~/.claude/orca/`) |  kit 이미 있음 | 사용자 파일 저장 개입 | 무료 |
| **MCP Server** |  CLI 가 도구 export | Web 이 CLI 도구 사용 (반대 방향은 X) | 무료 |
| **Managed Agents API** |  SDK 코드 | 세션 완전 자동 (별개 UI) | 유료 (Anthropic API) |
| **Remote Agent** (VPS + SSH) |  kit `/exec_remote-*` | 24/7 + 모바일 SSH | Oracle Free Tier 무료 |
| **Chrome Extension** |  개발 필요 (9일) | 진짜 완전 자동 (claude.ai UI) | 무료 (사용자 계정) |

**MCP 로 web 발주 = 불가** (Anthropic 이 그 API 공개 X). 완전 자동 원하면 Chrome Extension 개발 또는 Managed Agents API (유료).

### 지금 즉시 되는 것

1. **Claude.ai Projects** (Section 1) — 매 대화 자동 seed
2. **파일 브릿지** — CLI 워커 `~/.claude/orca/` 폴링
3. **Remote Agent** — Termius·Blink Shell 로 어디서든 SSH

### CLI 발주 (파일 브릿지 사용)

```bash
python .claude/scripts/route.py --enable-global-worker  # 전역 워커 활성
orca-dispatch task-instruction.md codex                 # task 큐잉
ls ~/.claude/orca/results/                              # 결과 확인
```

### Managed Agents API (유료 · Python)

```python
from anthropic import Anthropic
client = Anthropic()
agent = client.agents.create(
    name="orchestration_v1_bridge",
    model="claude-opus-5",
    system=open("docs/install/README.md").read(),
)
```

---

## Section 4. 자산 전수 (14 카테고리 요약)

### Commands (200+)
Section 2 § 10 카탈로그 참조.

### Skills (250+ · 자동 활성)
- `auto-planner` (5단계 plan) · `direction-first` (대상 확정) · `user-emotion-auto-response` (감정 매핑)
- `asset-creation-workflow` (자산 생성 표준) · `feature-discovery` (미사용 발굴) · `web-cli-dialogue-workflow` (왕복 대화)
- `exec_orca-auto` · `route_dispatch` · `prompt-techniques` · `auto-layout-fit` · `post-codex-verify`

### Memory (~/.claude/projects/.../memory/)
- feedback_* (40+): confirm_target_first · full_survey_read_all · no_duplicate_function · install_order · user_emotion_mapping · web_cli_dialogue · no_hardcoded_paths · template_kit_principle · verify_before_report 등
- reference_* : opus_5_launch · fable_5_launch · sonnet_5_launch · claude_web_projects_setup · company_context (ISMS-P·RMS·ITCEN ESG)

### State DB (`.claude/state/orca.db` · SQLite 8 테이블)
workers · tasks · metrics · quota · budget · session · approval_requests · prompt_history

### References Toolkit (49개 · `plugins/exec_orch/references/`)
RAG cite 형식 주입 도메인 지식.

### Roadmap (`docs/2026-04-19/로드맵.md`)
Phase 1~3 신규 스펙 (미래 26개 예정).

### Agents (20+)
Task tool spawn · Explore·Plan·code-reviewer·test-runner·judge·data-scientist·python-pro·typescript-pro·llm-architect·ml-engineer

### Hooks (55)
- **SessionStart**: hook-00-init (헌장 노출) · brief-unused-features (미사용 브리핑)
- **UserPromptSubmit**: user-prompt-auto-planner · detect-repeat-request · detect-user-emotion · detect-efficiency · detect-deflection · periodic-rules-reminder
- **PreToolUse Write/Edit**: detect-asset-creation · block-version-suffix · check-mojibake · protect-critical-files
- **PreToolUse Bash**: pre-install-lock · pre-commit-full-check
- **PostToolUse**: auto-smoke-test · check-sync-drift · verify 도구 자동

### Rules (23)
direction-first · user-emotion · failure-mode · consistency · best-practices · screen-verify · no-false-report · teaching-doc · approval-gate-rules · file-locking-policy · cleanup-policy · codex-rules · gemini-review-policy · mcp-install-rules · post-codex-verify · plugin-structure · sync-workflow · frontmatter · file-naming · indentation · claude-md-design · skill-design · industry-transfer-format

### MCP (`.mcp.json` + 카테고리별)
- 기본: context7 · playwright · thinking · filesystem · fetch
- 카테고리: `/mcp_dev` · `/mcp_data` · `/mcp_collab` · `/mcp_web` · `/mcp_docs` · `/mcp_media`
- Anthropic 공식 커넥터 (claude.ai): Figma · Gamma · Gmail · Canva · Mermaid · Slack · GitHub · Notion

---

## Section 5. API 비용 매트릭스 (무료 vs 유료)

| 태스크 | 무료 (로컬·내장) | 유료 (API · 명시 필요) |
|---|---|---|
| 파일·grep·검색 | Grep·Glob·Bash | — |
| 간단 요약·분류 | Ollama Llama 3.3·Gemma·Mistral | Haiku 4.5 ($0.25/$1.25) |
| RAG 벡터 검색 | ChromaDB 로컬 | Pinecone·Weaviate |
| subagent 격리 | Agent Explore·general-purpose | Managed Agents API |
| 관측·대시보드 | Phoenix self-hosted | LangSmith·Arize |
| 복잡 설계·리팩터 | (로컬 한계) | Opus 5 ($5/$25) · Sonnet 5 |
| 초난도 | (로컬 한계) | Opus 5 + ultracode · Fable 5 ($10/$50) |
| 감사·비즈니스 | (로컬 무의미) | claude.ai Web (사용자 구독) |
| 디자인 MCP | Mermaid CLI | Canva·Figma·Gamma OAuth |
| 음성 STT | Whisper 로컬 | Whisper API · edge-tts |
| 이미지 생성 | Pollinations.ai | DALL-E·Midjourney |
| 영상 편집 | FFmpeg·Real-ESRGAN | Runway ML |

**API 비용 없이 자동화**: `/exec_offline-setup` → 대부분 태스크 로컬. 복잡 설계만 API.

**budget 게이트**: `python .claude/scripts/route.py --set-daily-limit <USD>` — 초과 시 자동 로컬 fallback.

---

## Section 6. 사용자 도메인 (ISMS-P · RMS · ITCEN ESG) 특화

- **ISMS-P 자격증 3년** — 개인 도메인
- **아이티센 코어 ESG 사업부 개발팀 리더**
- **RMS** (MicroRisk-X 신사업 PPT v14 저자)

**특히 유용**:
- `/design_ppt` `/design_word` `/pdf-generate` (제안서·보고서)
- `/rag-graph` `/rag-agentic` (도메인 지식 그래프·에이전트 검색)
- `/security` `/sec-scan` (ISMS-P 정합 코드 스캔)
- `/analyze-improve` (XAI·Zero Trust·RAG·이벤트 아키텍처 개선점)
- `/pdf-sign` `/pdf-secure` (전자서명·감사 산출물)
- `/effort-mythos` (Fable 5 · 복잡 감사 판정)

---

## Section 7. Chrome Extension 미래 스켈레톤 (진짜 자동 브릿지)

**목적**: 사용자 클립보드 릴레이 없이 web ↔ CLI 자동 · **API 비용 X** (사용자 계정 활용).

### 아키텍처

```text
Chrome Extension
├── content-script.js       claude.ai DOM 자동 seed + 응답 추출
├── background.js           Native Messaging (chrome → CLI)
├── popup.html              상태 UI
└── native-host/
    └── host.py             Python 데몬 (~/.claude/orca/ 폴링·저장)
```

### manifest.json (Chrome v3)

```json
{
  "manifest_version": 3,
  "name": "Orchestration Kit Bridge",
  "version": "0.1.0",
  "permissions": ["activeTab", "storage", "nativeMessaging"],
  "host_permissions": ["https://claude.ai/*"],
  "content_scripts": [{
    "matches": ["https://claude.ai/*"],
    "js": ["content-script.js"]
  }],
  "background": { "service_worker": "background.js" }
}
```

### 개발 로드맵 (9일 개인 개발)

1일 manifest + content-script (seed) · 2일 background + Native Messaging · 1일 Native Host Python · 2일 응답 추출·큐 sync · 1일 popup UI · 2일 테스트

**지금 대안**: Claude.ai Projects + Bookmarklet + 파일 브릿지.

---

## Section 8. 유지 원칙

- 이 파일 = **정본 하나** (docs/install/README.md)
- 다른 md 파일 X (사용자 요구 · v2/v3 접미사 X)
- kit 원칙 변경 시 이 파일 갱신 (원본 덮어쓰기 · `.bak` 백업)
- Claude.ai Project System instructions 도 이 파일 Section 2 로 교체
- MEMORY.md 인덱스: `reference_claude_web_projects_setup` · `feedback_web_cli_dialogue` · `feedback_confirm_target_first`

---

## Section 9. install target 배포

kit 을 다른 프로젝트에 배포:

```bash
cd C:\pjt\orchestration_v1
install.bat <target_path>              # 새 target · 자동 배포 (rules·hooks·CLAUDE.md·statusline)
bash .claude/scripts/sync-to-team.sh   # orchestration_v1_team 동기화
```

Target 에는 statusline `[TARGET] <name>` 자동 표시.

---

## Section 10. 세션 시작 자동 발동

매 세션 시작 시 자동:
- hook-00-init : 헌장 A~F 노출
- brief-unused-features : 미사용 기능 3-5개 브리핑 (일 1회)
- cleanup-pollution : 오염 파일 정리
- auto-install-deps : Playwright·MCP·Python pkg (1h throttle)
- check-workers : 워커 heartbeat

매 프롬프트 자동:
- 대상 확정 요청 · 5단계 plan · MoE 라우팅
- 회피 감지 · 반복 감지 (/loop) · 감정 매핑 · 효율화 제안

---

**한 문장**: 이 README.md 하나만 참고. Section 2 프롬프트를 Claude.ai Project System instructions 에 붙이면 web 도 자동 seed. 다른 md 파일 X.
