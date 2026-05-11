# CLAUDE.md — Multi-AI Orchestration Kit v1

> **목적**: Claude Code 가 이 프로젝트에서 **어떻게 일해야 하는지** 정의.
> **대상**: AI 에이전트 (Claude 우선). 사람용 가이드는 `guide.txt`.
> **유지 원칙**: 500줄 이하 · WHAT/WHY/HOW 프레임 · 참조 중심 (내용 중복 금지).

---

## 1. WHAT — 이 프로젝트는 무엇인가

**멀티AI 오케스트레이션 킷** (Claude + Codex + Gemini).
- **핵심**: `exec_orch` 엔진 + 26개 플러그인 (16 stable + 10 spec-only, `_template` 제외)
- **경계**: 이 저장소 = **킷**. 실구현·비즈니스 로직은 **install 후 각 플랫폼**에서.
- 전체 플러그인 목록: `docs/2026-04-19/플러그인.txt`
- 로드맵 (미래 26개): `docs/2026-04-19/로드맵.md`
- 최신 추가: `exec_remote` (4주차 VPS 24/7 원격 운영, 2026-05-07)

---

## 2. WHY — 왜 이 구조인가

- **다AI 협업**: 단일 모델 한계 극복 (Claude 설계 → Codex 구현 → Gemini 검증)
- **SoT 규칙**: `plugins/` 원본 → `.claude/` sync 결과물 (드리프트 방지)
- **스코프 분리**: 킷은 인프라만, 응용은 플랫폼에서 (스코프 폭주 방지)
- **비용 관측**: plugin.json `precedence` + `token_estimate` (세션 로드 우선순위)

상세 원칙: `docs/architecture-patterns.md` (9개 패턴)

---

## 3. HOW — 어떻게 작업하는가

### 3.1 Session Start (순서 고정)
1. **Orca Auto** — `.claude/skills/exec_orca-auto.md` 실행 (워커 spawn)
2. **First-Run** — `docs/CLAUDE_SETUP_GUIDE.md` 있으면 처리 후 삭제
3. **Resume** — `.claude/context-cache/session-snapshot.md` 있으면 복구 제안

### 3.2 AI 역할 (규모·특성 기반, 4.7 우선)
| 태스크 | AI | 방법 |
|--------|-----|------|
| 설계·복잡추론 | Claude Opus 4.7 | Extended Thinking (1M context) |
| 단순구현 <200줄 | Claude Sonnet 4.6 | 직접 (저비용) |
| 코드 500줄+ | Codex (×4 병렬) | `task-instruction.md` → `codex-auto` |
| 검증 (기본) | Haiku 4.5 (×2 병렬) | `haiku-auto` (Prompt caching 90% 절감) |
| 검증 (초장문/멀티모달) | Gemini Flash | >500k 토큰만 `gemini-auto` |
| PPT·디자인 | Claude + MCP | Gamma/Canva/Figma |

라우팅 로직: `plugins/exec_orch/skills/route_dispatch.md` (AI 단가·특성·quota 매트릭스)

### 3.3 API 한도 + Budget Fallback
SQLite 기반 quota·budget 관리 → 자동 fallback + 지수 backoff.
- 감지: `.claude/state/orca.db` (quota·budget 테이블)
- Quota 초과: 10m→20m→40m→2h 지수 backoff
- Budget 초과: 일일 상한 (기본 무제한, `route.py --set-daily-limit` 설정 가능)
- **절대 금지**: 빈 task 를 `done/` 으로 이동 (위장 완료)

### 3.4 Orca Auto 규칙
- 활성: `.claude/orca-enabled` 있고 `.claude/orca-stopped` 없음
- 로컬 워커 수: `.claude/orca-workers-config.json`
- 전역 상한: `~/.claude/orca/workers-config.json` `max_workers`
- 종료: `/orcauto-stop` 또는 Claude 종료 후 5분

상세: `.claude/skills/exec_orca-auto.md`

### 3.5 전역 오케스트레이션 (멀티 프로젝트)
- 진입: `orca-dispatch <task_file> [codex|gemini|claude]`
- 워커: `codex-auto-global`, `gemini-auto-global` (`~/.claude/orca/` 폴링)
- 중단: `touch ~/.claude/orca/stop`

상세: `plugins/exec_orch/skills/route_dispatch.md § Step 4`

### 3.6 MCP 설치 규칙
1. **실제 npm 존재 확인**: `npm view <package>` 로 검증 후만 커맨드에 기록 (404 방지)
2. **Windows npx 래퍼**: `cmd /c npx <package>` 필수 (shell 교차호환성)
3. **OAuth/인증도구**: 실제 값은 환경변수만, 개발자 콘솔 URL + 변수 이름 명시
4. **각 plug_<category> 준수**: design·dev·data·web·collab·docs·media 모두 위 규칙 따름

상세: `guide.txt` § 8 · `docs/upgrade-notes-2026-04-23.md`

### 3.7 24/7 자동화 필수 설정
1. **SQLite 초기화**: `python .claude/scripts/init-state-db.py` (`.claude/state/orca.db` 생성)
2. **Watchdog 백그라운드**: `.claude/scripts/watchdog-start.bat` (워커 heartbeat 체크)
3. **예산 상한** (선택): `python .claude/scripts/route.py --set-daily-limit 50` (USD)

상세: `guide.txt` § 7 · `docs/routing-policy.md` · `docs/caching-strategy.md` · `docs/metrics-guide.md`

---

## 4. 핵심 경로 (참조 전용 — 내용은 해당 파일에)

| 경로 | 용도 | 편집 |
|------|------|------|
| `plugins/` | **원본** (14 stable + 7 spec-only + `_template`) | ✅ 여기만 |
| `.claude/commands,skills/` | sync 결과물 | ❌ 자동 생성 |
| `.claude/rules/` | 공유 규칙 (plugin-structure·frontmatter·file-naming·sync·indentation) | ✅ |
| `.claude/scripts/` | sync·validate·install·orca-status·worker-health·route·watchdog·metrics 등 | ✅ |
| `.claude/scripts/lib/` | state_db·router·pricing·prompt_cache·watchdog_helpers (10개) | ✅ |
| `.claude/hooks/` | PreToolUse·PostToolUse·SessionEnd 훅 스크립트 | ✅ |
| `.claude/state/orca.db` | **SQLite 통합 상태** (workers·tasks·metrics·quota·budget·session) | 자동 |
| `.claude/tasks/` | task-instruction.md, locks/, done/ | 자동 |
| `~/.claude/orca/` | **전역 큐** (멀티 프로젝트) | 자동 |
| `.claude-plugin/` | plugin.json + schema + marketplace.json | ✅ |
| `docs/architecture-patterns.md` | 설계 원칙 9가지 | ✅ |
| `docs/caching-strategy.md` | Prompt caching TTL 전략 | ✅ |
| `docs/routing-policy.md` | 4.7 라우팅 결정 트리 상세 | ✅ |
| `docs/metrics-guide.md` | Metrics DB 스키마·쿼리 | ✅ |
| `docs/2026-04-19/로드맵.md` | Phase 1~3 스펙 (미래 26개) | ✅ |
| `guide.txt` | 사람용 전체 가이드 (섹션 1~14) | ✅ |
| `.env` / `.env.example` | 환경변수 (하드코딩 금지) | .env 는 gitignore |

---

## 5. 5 Rules (Brij Kishore Pandey, 2026)

이 CLAUDE.md 가 **실제로 작동하려면**:

1. **`/init` 먼저** — 새 환경 세팅 시 `bash .claude/scripts/install.sh` (scaffold 검증·sync·env 초기화)
2. **500줄 이하 유지** — 길면 무시됨. 세부는 참조 파일로 분리.
3. **Hooks 사용** — 자동 실행 필요한 건 메모리·프롬프트 X, `.claude/settings.json hooks` ✓
4. **월간 업데이트** — 구조 변경 시 이 파일도 갱신. 고정 문서 아님.
5. **참조만, 중복 금지** — `guide.txt`, `docs/architecture-patterns.md`, `.claude/rules/*` 에 있는 건 여기서 반복 X

---

## 6. 3 Scopes (우선순위: Folder > Project > Global, Last wins)

- **Global**: `~/.claude/CLAUDE.md` — 모든 프로젝트 공통 (코딩 스타일·개인 선호)
- **Project**: 이 파일 (`./CLAUDE.md`) — 프로젝트 규칙
- **Folder**: `./src/CLAUDE.md` 등 — 모듈 국소 규칙 (필요 시)

같은 규칙 충돌 시 **Folder가 이긴다**.

---

## 7. 금지 사항

1. task-instruction.md 없이 Codex 호출
2. Gemini 리뷰 자동 채택 (Claude가 결정)
3. 같은 파일 동시 수정 (Writer=1)
4. 하드코딩 (API 키·경로·시크릿·사용자명·OS 절대경로·Python 버전) — `.env` + 런타임 동적 검색 (`where`/`tempfile`/`%USERPROFILE%`). Task Scheduler 같은 곳도 wrapper 거쳐 동적화. 상세: `.claude/rules/best-practices.md` § 하드 경로 금지
5. optional chaining (`?.`) 사용
6. 코드 주석에 "owner(주인)" 사용
7. `.claude/` 직접 편집 (sync가 덮어씀)
8. 빈 task `done/` 이동 (위장 완료)
9. 거짓 npm 패키지명 커맨드 (실측 없이) — `npm view` 검증 필수
10. **농땡이 (=일부 샘플로 단정)** — 사용자 지시는 무조건 전수조사. 파일명만 보고 중복/필요없다 판정 X, spec md 만 보고 .sh/.py 안 본 채 판정 X. 상세: `.claude/rules/failure-mode.md` § 농땡이 안티패턴
11. **사용자 액션 요구** — "이 .bat 한 번만 실행해주세요" 류 금지. 셋업·등록·시작은 SessionStart hook 으로 자동. 알림은 크리티컬 5가지(시크릿 노출/데이터 손실/보안 위협/비용 폭증/시스템 손상) 만. 상세: `.claude/rules/best-practices.md` § Zero-touch 자동화
12. **`~/.claude/` 직접 수정 / 다른 프로젝트 폴더 직접 수정** — orchestration_v1 은 **install/setup 으로 다른 폴더에 배포되는 공통 kit**. 글로벌·다른 프로젝트는 `setup/templates/` + `setup/modules/` 거쳐 자동 배포. 상세: `.claude/rules/best-practices.md` § Template kit 원칙
13. **교재/강의 doc 작성 시 8섹션 누락 + 다이어그램 품질 위반** — 8섹션 필수 (핵심·표·흐름·강점·약점·강추·우리매핑·점검). 외국어 이미지는 한글로 **대체** (영어+한글 같이 X). 다이어그램 = SVG/HTML + 화살표 + 흐름 필수, 단순 박스/표는 위반. 도구 우선순위: HTML/CSS+SVG (Playwright) > Mermaid > matplotlib. 5살 청자 톤. 상세: `.claude/rules/teaching-doc.md`
14. **산출물 자동 -v2/-v3 폴백 금지** — docx·pptx·pdf 빌드 시 잠금 폴백으로 버전 접미사 X. `.bak` 백업 후 원본 자리에 덮어쓰기. 원본 잠겨있으면 사용자에게 알림 (자동 -v2 X). 버전은 사용자 명시 요청 시만. 상세: `.claude/rules/teaching-doc.md` § 산출물 명명
15. **산출물 페이지 fit 사전검증 (docx · pptx · pdf 전체)** — 이미지 임베드 전 PIL 로 PNG 비율 측정 → 산출물별 페이지 비율 (docx portrait 1.46 / docx landscape 0.69 / pptx 16:9 0.54 / pptx 4:3 0.71 / pdf portrait 1.41 / pdf landscape 0.71) 과 비교 → 잘림·빈공간 자동 조정. PNG 빌드 시 viewport 비율 = 페이지 비율 강제 (full_page=False + clip). 사용자가 "짤린다" 한 후에야 fix = 농땡이. 자동 검증: `verify-image-fit.py` + hook-09 (build/generate/render-*-(ppt/doc/diagrams/pdf/html).py 트리거). 상세: `.claude/rules/teaching-doc.md` § 페이지 fit 검증
16. **멈춤 방지 — 사용자 액션 요구 X** — 파일 잠금·네트워크·권한 fail 시 즉시 sys.exit X. 60초 폴링·지수 backoff·대안 도구 자동 시도. "Word 닫고 재시도" 같은 노동 떠넘김 = 위반. 폴링 시작·완료는 stdout 만, 사용자 호출은 크리티컬 5가지 (시크릿/데이터손실/보안/비용/시스템손상) 만. 상세: `.claude/rules/best-practices.md` § 멈춤 방지
17. **페이지 전체 콘텐츠 fit (H1+callout+이미지+표 합산)** — 이미지 비율 검증만 X. H1·callout·캡션·이미지·표 모든 요소 height 합산 후 페이지 한계 내. 빈 여백·짤림·글씨 작음 = 같은 문제 다른 증상. PageLayoutTracker 의무 (skill: `auto-layout-fit`). 빌더 IMG 호출 시 자동 max_height 계산. 상세: `.claude/rules/teaching-doc.md` § 페이지 콘텐츠 fit
18. **사용자 요청 받으면 auto-planner skill 자동 활성** — "X 해줘"·"X 고쳐줘"·결함 지적 받자마자 5단계 plan (전수조사·분석·실행·확인·보고) + 30+ rule 자가 점검 + 막히면 codex/gemini 위임. 매번 사용자가 지시 기다림 X = Generative→Agentic 약점 보완. skill: `plugins/exec_orch/skills/auto-planner.md`

---

## 8. 플러그인 편집 → 배포 플로우

```bash
vim plugins/exec_orch/commands/godmode.md      # 1. 원본 편집
bash .claude/scripts/sync-plugins.sh --dry     # 2. 미리보기
bash .claude/scripts/sync-plugins.sh           # 3. 실제 sync
python .claude/scripts/validate-plugin-schema.py  # 4. 검증
git add plugins/ .claude/ && git commit -m "..."  # 5. 커밋
```

---

## 9. 참조 (상세는 각 파일에)

- 사람용 가이드: `guide.txt`
- 설계 원칙 9가지: `docs/architecture-patterns.md`
- 로드맵 (Phase 1~3): `docs/2026-04-19/로드맵.md`
- 공유 규칙: `.claude/rules/*.md`
- plugin.json 스키마: `.claude-plugin/plugin-schema.json`
- 업그레이드 노트: `docs/upgrade-analysis-2026-04-19.md`
