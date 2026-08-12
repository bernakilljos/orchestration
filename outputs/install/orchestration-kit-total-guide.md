# Orchestration Kit v1 — 총망라 가이드 (Total Guide)

> **목적**: 이 md 하나로 kit 전체 이해. install 안 해도 참고만으로 kit 이해·활용 가능.
> **대상**: 다른 프로젝트 개발자·다른 Claude 세션·사람 리뷰어.
> **작성일**: 2026-08-12 (Opus 5 default · Claude Code v2.1.226)
> **kit 상태**: plugins 36 · rules 22 · hooks 40+ · scripts 115

---

## 1. Kit 은 무엇인가

**멀티 AI 오케스트레이션 kit** (Claude + Codex + Gemini + Haiku + GPT-5.2 + Grok).

- **kit 자체 경로**: `<KIT_ROOT>\`
- **배포 방식**: `install.bat <target>` 또는 `sync-to-team.sh`
- **install target 예**: `C:\pjt\calc`·`C:\pjt\llm`·`<KIT_ROOT>_team`·`C:\pjt\teamclaude`
- **글로벌 설정**: `~/.claude/` (Windows: `%USERPROFILE%\.claude\`)

### 배포 자동 대상 (`setup/modules/01-core.bat`)
- `.claude/` 전체 (rules/hooks/skills/commands/agents/scripts/statusline)
- `CLAUDE.md`
- `plugins/` (SoT) → `.claude/{commands,skills,agents,hooks}` fanout
- `.claude-plugin/` (manifest)
- `AGENTS.md`·`GEMINI.md`·`guide.txt`
- `setup/`·`install*.bat`

---

## 2. 재발 방지 헌장 (§ 7) — A / B / C / D / E / F

**원칙**: 재발 방지 조항을 6 카테고리로 통합. 각 조항 = 규칙 + 근거.

### A. 하드코딩·폴백 금지
- **A1** — API 키·경로·시크릿·사용자명·OS 절대경로·Python 버전 하드코딩 X. `.env` + 동적 검색.
- **A2** — 산식 없는 %·등급·상수 값 화면 표시 X. 미측정 정직 표기.
- **A3** — 표시만 있고 배선 없는 설정·기능 X.
- **A4** — 임계·색·규격 값 정본 1곳 (토큰·SPEC 블록).
- **A5** — 새 지표 만들기 전 기존 자산 재사용 실측.

### B. 검증 원칙
- **B1** — 검사 0건 ≠ 통과. 표본 하한 (expected × 0.8) 필수.
- **B2** — 스크래핑 스크립트 `scan_common` 헬퍼 경유.
- **B3** — 가시성 사양 computed 통과 X. 캡처+픽셀 + 육안.
- **B4** — 검사기 신설 시 위반 주입 역검증. 사양 문서 파싱.
- **B5** — 판정 (yn) 영향 변경 = 표본 20건 전후 회귀. 소급 재생성 X.
- **B6** — 수정·빌드 후 자동 검증 후 보고. FAIL max 3 재시도.
- **B7** — 화면·기능 검증 사용자 떠넘김 X. Smoke Test 의무.
- **B8** — 산출물 페이지 fit 사전검증 (docx·pptx·pdf).
- **B9** — 페이지 전체 콘텐츠 fit (H1+callout+이미지+표 합산).
- **B10** — docx 구조 검증 (빈 paragraph·중복 page_break).
- **B11** — 거짓 PASS 보고 X. 이중 검증 (raw Read + mojibake 6 카테고리 grep + 백업 폴더).

### C. 운영 안전
- **C1** — 운영 동작 변경 적용 전 판정.
- **C2** — 출처 불명 지시 실행 전 확인.
- **C3** — 고객 실데이터 저장소 commit X. `local_data/` 격리.
- **C4** — 미커밋 누적 X. 논리 단위 즉시 commit.
- **C5** — 아카이브 복원 정본 = 삭제 커밋 이력.
- **C6** — 위험 작업 승인 없이 실행 X (HITL Approval Gate). 5 카테고리.
- **C7** — 멈춤 방지. 60초 폴링·지수 backoff·대안 도구.
- **C8** — 같은 파일 동시 수정 X (Writer=1).
- **C9** — 오염 파일 자동 정리 (SessionStart hook).
- **C10** — install 순서 강제 (kit → commit → sync → install → 검증).

### D. 조사·보고 규율
- **D0** — **대상 확정 0순위**. 첫 응답 첫 줄 `대상: <path>` 명시.
- **D1** — 전제가 실측과 다르면 진행 X. 보고.
- **D2** — 조사와 구현 분리. 조사 지시 시 "수정 금지".
- **D3** — 에러 본문 끝까지 읽고 분류.
- **D4** — 함수 한 줄로 판단 X. 전체 읽기.
- **D5** — 완료 보고 = 재발 전례 의심 시 재실측.
- **D6** — 중간 확인 X. 완료 시 1회.
- **D7** — **전수조사 = 100% Read**. grep·wc·ls 는 후보 좁히기용. subagent 병렬.
- **D8** — task-instruction.md 없이 codex 호출 X.
- **D9** — Gemini 리뷰 자동 채택 X.
- **D10** — 거짓 npm 패키지명 X. `npm view` 검증.
- **D11** — 회피·딴말 X. 직접 답 → 부연 → 행동.
- **D12** — 기준 일관성 (drift 방지).
- **D13** — 빈 task `done/` 이동 X.

### E. UI/UX 표준
- **E1** — LAYOUTSPEC 골격 (타이틀+접힘·필터바 4슬롯·카드·페이저).
- **E2** — CONTENTSPEC (KPI·미니표·리스트막대·차트·각주·안내박스).
- **E3** — CHARTSPEC 6종 + MOTIONSPEC (진입 1회·hover·reduced-motion).
- **E4** — 같은 목적 컴포넌트 2개 X. 만들기 전 grep.
- **E5** — 교재/강의 doc = 8섹션 + 다이어그램 (SVG/HTML + 화살표).
- **E6** — 산출물 `-v2`/`-v3` X. `.bak` 백업 후 원본 덮어쓰기.

### F. kit 고유
- **F1** — `.claude/` 직접 편집 X. `plugins/` 원본만.
- **F2** — `~/.claude/` 직접 수정 X. `setup/templates/` 거쳐 install 배포.
- **F3** — 사용자 액션 요구 X (Zero-touch). 알림 크리티컬 5가지만.
- **F4** — 누락 의존성 자동 install.
- **F5** — auto-planner 5단계 자동 발동.
- **F6** — **함수·훅·룰·skill·command 중복 X**. A/B/C 접두사·`_v2` 접미사 X.
- **F7** — **감정·상황 자동 대응 매핑** (답답→fast·짜증→진단·반복→loop·design→command 수정 등).
- **F8** — 자산 생성 감지 (유사 파일 grep · 자매 파일 검사).
- **F9** — 반복 요청 감지 → `/loop` 발동.
- **F10** — optional chaining `?.` X · 코드 주석 "owner" X.

---

## 3. Rules 목록 (`.claude/rules/*.md`)

| 파일 | 목적 | 헌장 매핑 |
|---|---|---|
| **direction-first.md** | 대상 확정 0순위 (kit/설정/target/글로벌 4갈래) | D0 |
| **user-emotion.md** | 감정·상황 자동 대응 매핑 | F7 |
| **failure-mode.md** | 확신 없으면 거절 · 전수조사 위반 · 100% Read · 회피 | D1·D7·D11 |
| **consistency.md** | 기준 일관성 · 함수·훅·룰 중복 금지 | D12·F6 |
| **best-practices.md** | Zero-touch·Template kit·하드 경로·검증 후 보고·멈춤 방지·FIFO 큐·install 순서 | A1·B6·C7·C10·F3·F4 |
| **screen-verify.md** | Smoke Test 의무·End-to-End 완결성 (DB→join→화면)·참조 페이지 100% 반영 | B7 |
| **no-false-report.md** | 이중 검증 (raw Read + mojibake grep + 백업 폴더) | B11 |
| **teaching-doc.md** | 8섹션·다이어그램·페이지 fit·산출물 명명 | B8·B9·E5·E6 |
| **approval-gate-rules.md** | HITL 5 카테고리 위험 명령 | C6 |
| **file-locking-policy.md** | Writer=1 · 다중 워커 lock | C8 |
| **cleanup-policy.md** | 오염 파일 정리 (nul·bak·nested `.claude/`) | C9 |
| **codex-rules.md** | task-instruction.md 의무 | D8 |
| **gemini-review-policy.md** | Gemini 리뷰 Claude 결정 | D9 |
| **mcp-install-rules.md** | `npm view` 검증·Windows npx 래퍼 | D10 |
| **post-codex-verify.md** | Codex hallucination 사후 검증 | D13 |
| **plugin-structure.md** | 플러그인 폴더 구조 | F1 |
| **sync-workflow.md** | plugins/ → .claude/ sync | F1 |
| **frontmatter.md** | plugin.json·md frontmatter 표준 | F1 |
| **file-naming.md** | 파일 명명 규칙 | F1 |
| **indentation.md** | 들여쓰기 (JSON 2·Python 4·Bash 2) | F10 |
| **claude-md-design.md** | CLAUDE.md 설계 (500줄 이하·참조 중심) | - |
| **skill-design.md** | Anthropic 공식 skill 표준 | - |
| **industry-transfer-format.md** | 산업 ML 이식 답변 형식 (표 + 한 줄) | - |

---

## 4. Hooks 목록 (`.claude/hooks/*` + `plugins/*/hooks/*`)

### SessionStart (매 세션)
- **hook-00-init.sh** — 폴더 초기화 + 재발 방지 헌장 A~F 노출 + 대상 확정 0순위 + 전수조사 5단계 + Zero-touch·Template kit·8섹션·-v2 금지·검증·회피·docx 구조 리마인드
- **deploy-vscode-settings.sh** — VS Code settings 배포
- **auto-install-deps.sh** — Playwright·MCP·Python pkg 자동 install (1h throttle)
- **force-restart-stale-watchdog.sh**
- **install-external-watchdog.sh**
- **cleanup-pollution.sh** — 오염 파일 정리
- **check-workers.sh**

### UserPromptSubmit (매 프롬프트)
- **user-prompt-auto-planner.sh** — 5단계 plan + MoE 분류 + Memory recall + 대상 확정 REQUIRED 주입
- **detect-deflection.sh** — 회피 안티패턴 감지
- **detect-repeat-request.sh** — 최근 5 프롬프트 유사도 3+ → `/loop` 안내
- **detect-user-emotion.sh** — 감정·상황 12 카테고리 자동 매핑 (F7)
- **periodic-rules-reminder.sh** — 10턴마다 룰 리마인드 (0. 대상 확정 우선)

### PreToolUse (Write·Edit)
- **detect-asset-creation.sh** — 새 rule/hook/skill/command/agent/memory 생성 시 유사 파일 grep + 자매 파일 검사
- **protect-critical-files.sh**
- **block-version-suffix.sh** — 산출물 `-v2`/`-v3` X (docx/pptx/pdf/xlsx/md/txt/html/rst/adoc/ipynb)
- **check-mojibake.sh** — mojibake 6 카테고리 grep
- **check-hardcoded-paths.sh**
- **check-indentation.sh**
- **block-korean-removal.sh** — 한글 제거 시도 차단
- **block-tricks.sh**
- **block-file-deletion.sh**
- **block-visible-windows.sh**
- **check-html-balance.sh**
- **check-js-syntax.sh**
- **check-korean-only.sh**
- **check-claude-md-size.sh** — 500줄 초과 warn

### PreToolUse (Bash)
- **pre-install-lock.sh** — install/sync-to-team 감지 시 uncommitted block
- **block_dangerous_bash.py**
- **log_bash_command.py**

### PostToolUse
- **check-sync-drift.sh**
- **check-infra-sync.sh**
- **auto-smoke-test.sh** — DB/API/frontend 변경 시 smoke test
- **check-mcp-health.sh**
- **hook-09-ocr-verify.sh** — 산출물 PNG 검증

### Stop / SessionEnd
- **stop-snapshot.sh**
- **stop-doc-summary.sh**
- **hook-gemini-recap.sh**
- **memory_guard.sh**

---

## 5. Commands (핵심)

- `/godmode` — 최대 워커·직통 라우팅
- `/check` — 서비스·테스트·스크린샷 종합 체크
- `/design_ppt`·`/design_word`·`/design_excel`·`/pdf-generate`
- `/exec_orch` — 오케스트레이션 진입
- `/exec_remote-*` — VPS 24/7 운영
- `/exec_scheduler-*` — cron 잡
- `/rag-*` — 7 RAG 패턴 (naive·hybrid·hyde·graph·multimodal·adaptive·corrective·agentic)
- `/approve`·`/reject`·`/approvals` — HITL 승인 큐
- `/loop` — 반복 작업 자동화
- `/sync-team` — orchestration_v1_team 동기화
- `/install-to <path>` — 다른 프로젝트 배포

전체 목록: `.claude/commands/` (~200 개)

---

## 6. Skills (핵심)

- **direction-first** 관련 (rule 참조)
- **asset-creation-workflow** — 자산 생성 유형별 표준 세트 (F8 정합)
- **user-emotion-auto-response** — 감정·상황 자동 대응 매핑 SoT (F7 정합)
- **auto-planner** — 5단계 plan 자동 (F5)
- **route_dispatch** — AI 라우팅 매트릭스
- **prompt-techniques** — 12 프롬프트 강화 기법
- **post-codex-verify** — Codex hallucination 검출

---

## 7. 감정·상황 자동 대응 매핑 (F7)

| 트리거 어휘 | 자동 대응 | 관련 자산 |
|---|---|---|
| 답답·빠름·fast·서두름 | `/fast` mode + 짧은 응답 | Claude Code built-in |
| 짜증·짱나·엉망·대충·장난 | 시스템 결함 진단 5단계 | detect-user-emotion.sh |
| 중복·또 요청·반복 | `/loop` 자동 발동 | detect-repeat-request.sh |
| design 별로·UI 이상 | 관련 command md 자동 수정 | plugins/design_*/commands/ |
| 방향 오해·target 아니 | direction-first 재적용 + statusline | direction-first.md |
| 하드코딩·박아 | 자동 grep 감사 | best-practices.md § 하드 경로 |
| 안뒤져·전부·모든·다 | 전수조사 100% Read | failure-mode.md § 전수조사 |
| 매번 까먹·기억 못 | hook·rule·memory 강제 등재 | consistency.md |
| install·배포·deploy | install 순서 확인 | pre-install-lock.sh |
| 회피·딴말 | 직접 답 강제 | detect-deflection.sh |
| 비용·budget·quota | budget·quota fallback 재확인 | route.py --check |
| 성능·느림 | 캐싱·병렬·subagent Explore | prompt cache |

---

## 8. 대상 확정 4갈래 (D0)

| # | 경로 | 언제 |
|---|---|---|
| 1 | `<KIT_ROOT>\` | kit 자체 감사·룰·hook 축약 |
| 2 | `<KIT_ROOT>\setup\templates\` | install 배포용 template |
| 3 | install 대상 실운영 프로젝트 (경로 확인) | "실운영"·"하드코딩 실측"·"재발 방지 헌장"·비즈니스 지표 |
| 4 | `~/.claude/` (`%USERPROFILE%\.claude\`) | 글로벌 설정 |

**자동 판정 힌트** (`user-prompt-auto-planner.sh`):
- "install a/b"·"배포"·"공통 kit"·"template" → 후보 2
- "실운영"·"하드코딩 실측"·"헌장"·비즈니스 지표 → 후보 3
- "룰 21개"·"hook 40개"·"플러그인"·"kit 자체" → 후보 1
- "settings"·"글로벌"·"~/.claude" → 후보 4

**첫 응답 첫 줄 형식**: `대상: <path> (kit/설정/target/글로벌) — 맞으면 진행, 아니면 정정`

---

## 9. statusline (매 turn 표시)

`.claude/statusline.sh` — 매 turn 상태바에 4갈래 판정 + turn 번호 + 폴더명.

**예**:
- `[KIT] orchestration_v1 (감사·리팩터) · turn#367 · orchestration_v1`
- `[TARGET] install 대상 실운영: calc · turn#12 · calc`
- `[GLOBAL] ~/.claude · turn#3 · .claude`

**Override**: `.claude/state/current-target` 파일에 임의 문자열 쓰면 그것으로 표시.

---

## 10. 자산 생성 워크플로우 (F8)

새 자산 만들기 전 공통 절차:

1. **유사 파일 grep** — `grep -rln "<purpose>" .claude/ plugins/`
2. **정본 위치 확인** — SoT 표
3. **자매 파일 유형** — bash `.sh` → PowerShell `.ps1` (Windows) 사매
4. **작성** — frontmatter + 근거·이유·How to apply
5. **인덱스 갱신** — MEMORY.md·CLAUDE.md § 7

### 정본 위치 (SoT)

| 자산 | 정본 |
|---|---|
| 공통 유틸 | `.claude/scripts/lib/` |
| 스킬 로직 | `plugins/exec_orch/skills/` |
| Hook | `plugins/*/hooks/` (SoT) → `.claude/hooks/` sync |
| Rule | `.claude/rules/<name>.md` 하나 |
| Command | `plugins/*/commands/<name>.md` 하나 |
| Memory feedback | `~/.claude/projects/<proj>/memory/feedback_<slug>.md` 하나 |

---

## 11. AI 라우팅 (2026-08-12 기준)

| 태스크 | AI | 방법 |
|---|---|---|
| **설계·복잡추론 (default)** | Claude Opus 5 | `claude-opus-5` · 1M context 기본+최대 · 128k 출력 · thinking on-by-default · $5/$25 |
| 설계·복잡추론 fallback | Claude Opus 4.8 | thinking disable 자유 · $5/$25 |
| 초난도·다각 검증 | Opus 5 + ultracode | Dynamic Workflows · subagent nesting 3 depth |
| Mythos-class | Claude Fable 5 | RESTORED 2026-07-01 · $10/$50 · 30일 retention |
| 균형형 | Claude Sonnet 5 | Opus 4.7 tokenizer (30% 더 많은 토큰) |
| 단순구현 <200줄 | Claude Sonnet 4.6 | 저비용 |
| 코드 500줄+ | Codex ×4 병렬 | `task-instruction.md` 의무 |
| 검증 기본 | Haiku 4.5 ×2 병렬 | Prompt caching 90% 절감 |
| 초장문/멀티모달 | Gemini Flash | >500k 토큰만 |
| 가벼운 대량 | Grok | route.py --check grok |
| 초장기 recall | GPT-5.2 | 2M+ 컨텍스트 |

---

## 12. install 절차 (C10 순서)

```text
[Phase 1] kit 편집 (rules·hooks·CLAUDE.md·memory)
      ↓
[Phase 2] git commit (kit 상태 스냅샷)
      ↓
[Phase 3] sync-plugins (plugins → .claude fanout)
      bash .claude/scripts/sync-plugins.sh
      ↓
[Phase 4] install / sync-team (target 배포)
      install.bat <target>              # 새 target
      bash .claude/scripts/sync-to-team.sh  # orchestration_v1_team
      ↓
[Phase 5] 검증 (target 에서 statusline·CLAUDE.md 반영 확인)
```

**감지 hook** `pre-install-lock.sh`: Phase 1~3 미완 (uncommitted 또는 `kit-edit-lock` 파일 존재) 시 `install.bat`·`sync-to-team.sh` block.

---

## 13. 최신 상태 (2026-08-12)

### Claude Code v2.1.226
- Opus 5 default 승격 (7/24)
- subagent nested spawn depth 3 (7/24)
- `sandbox.network.strictAllowlist`
- `/code-review` non-interactive 강제
- WebSearch 세션 상한 200 (`CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION`)
- subagent 세션 상한 200 (`CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION`)

### API 신규
- Claude Opus 5 launched (7/24) · 1M context 기본+최대
- Mid-conversation tool changes beta (7/24)
- Server-side fallback beta (7/24)
- MCP tool 100k+ char auto-spill (7/24)
- Managed Agents session thread event streams (7/22)
- Managed Agents webhooks (7/22)

---

## 14. 참조

- **CLAUDE.md** (프로젝트 루트) — 헌장 A~F 원본
- **guide.txt** — 사람용 상세 가이드
- **docs/architecture-patterns.md** — 설계 원칙 9가지
- **docs/routing-policy.md** — AI 라우팅 결정 트리
- **docs/caching-strategy.md** — Prompt caching TTL
- **docs/metrics-guide.md** — Metrics DB 스키마
- **plugins/exec_orch/skills/** — 오케스트레이션 skill
- **plugins/exec_orch/references/** — 49 toolkit 참조 자료

---

## 15. 다른 프로젝트에서 이 kit 활용 방법

### 옵션 A: install 배포 (권장)
```bash
cd <KIT_ROOT>
install.bat C:\pjt\<target_project>
```
결과: target 에 `.claude/`·`plugins/`·`CLAUDE.md` 배포 → 그 프로젝트에서 Claude Code 세션 시 자동 적용.

### 옵션 B: 이 md 만 참고
이 파일 하나 읽으면 kit 핵심 파악 가능. 다른 프로젝트에서 install 안 해도:
- 헌장 A~F 를 그 프로젝트 CLAUDE.md § 7 로 복붙
- Hook 스크립트 필요한 것만 복사
- Rule 카테고리별 필요한 것만 복사

### 옵션 C: sync-team (팀 협업 폴더)
```bash
bash .claude/scripts/sync-to-team.sh [/path/to/team_copy]
```
`orchestration_v1_team` 기본 대상 (다른 경로 지정 가능).

---

## 16. 이 문서 유지 원칙

- **변경 트리거**: kit 에 rule/hook/skill/command/agent 추가·삭제 시 즉시 갱신
- **위치**: `outputs/install/orchestration-kit-total-guide.md` (git 관리 X — outputs 는 gitignore 가능)
- **버전**: `-v2` 접미사 X (E6 정합) — 원본 덮어쓰기 + `.bak` 백업
- **정본**: CLAUDE.md § 7 · rules/*.md · hooks · skills 가 SoT. 이 md 는 요약 스냅샷.

---

**작성**: Claude Opus 5 · 2026-08-12 세션
**세션 학습**: `~/.claude/projects/C--pjt-orchestration-v1/memory/feedback_user_enfp_adhd_style.md § 2026-08-12 확장`
