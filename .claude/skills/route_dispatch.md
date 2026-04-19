# route_dispatch — AI 라우팅 · 판단

> **분류:** `route_` (라우팅/판단 계열)
> **통합 레거시:** (`vibe-loop` command — 2026-04-19 삭제), CLAUDE.md `Multi-Agent Auto-Detection`
> **참조 plugin:** `.claude-plugin/plugin.json` → `entry_points.task_route`

## 목적
태스크 규모와 가용 AI 도구를 자동 감지해 최적 실행 경로를 결정한다.
사용자에게 묻지 않고 자동으로 결정한다.

---

## Step 1: 가용 AI 감지

```
1. codex-auto / codex-auto-global 가용 확인:
     where codex-auto 2>nul && echo YES || echo NO       (로컬 워커)
     where codex-auto-global 2>nul && echo YES || echo NO (글로벌 워커)
     CODEX_AVAILABLE        = true / false
     CODEX_GLOBAL_AVAILABLE = true / false

2. gemini-auto / gemini-auto-global 가용 확인:
     where gemini-auto 2>nul && echo YES || echo NO
     where gemini-auto-global 2>nul && echo YES || echo NO
     GEMINI_AVAILABLE        = true / false
     GEMINI_GLOBAL_AVAILABLE = true / false
```

---

## Step 2: 태스크 규모 판단

| 규모 | 판단 기준 |
|------|---------|
| `LARGE`  | 예상 코드 500줄+, CRUD 전체, 새 기능 |
| `VERIFY` | 검증·문서·다이어그램·리서치 요청 |
| `SMALL`  | 500줄 미만 구현, 버그 수정, 단순 수정 |

### Step 2.5: AI별 특성·단가 매트릭스 (v2 정교화)

| AI | 강점 영역 | 상대 단가 | 컨텍스트 | 우선 선택 |
|----|----------|-----------|----------|----------|
| **Claude** (Opus) | 설계·판단·리팩토링·복잡한 추론 | 높음 | 200K/1M | LARGE 설계, 승인, 복잡 판단 |
| **Claude** (Sonnet/Haiku) | 일반 구현·문서·요약 | 중간/낮음 | 200K | SMALL 구현, 보완 |
| **Codex** (GPT-4 계열) | 대량 코드 작성·API 연동 | 중간 | 128K | LARGE 구현 (500줄+) |
| **Gemini** (2.0 Flash) | 검증·리뷰·리서치·멀티모달 | 낮음 | 1M+ | VERIFY, 문서 읽기, 스크린샷 |

**선택 규칙 (우선순위 순)**:
1. **설계·판단** → Claude (Opus 우선)
2. **대량 코드 구현** (500줄+) → Codex (병렬 4대)
3. **검증·리뷰·문서 탐색** → Gemini (비용 효율)
4. **음성·이미지·멀티모달** → Gemini (네이티브 지원)
5. **소규모 수정** (<200줄) → Claude 직접 (라우팅 오버헤드 제거)

**비용 절감 전략**:
- 프롬프트 캐싱 활용 (반복 질의 90% 절감)
- 검증 단계는 Gemini Flash (저단가) 우선
- Claude Opus 는 결정·설계에만 (자주 호출 X)

### Step 2.6: 8 AI 아키텍처 인지 (LLM 외)

**출처**: IG Reel `DUrAxgmDa9p` — "LLMs are AI models, but not all AI models are LLMs"

작업 특성이 순수 텍스트 추론이 아니면 **다른 아키텍처** 고려:

| 아키텍처 | 용도 | 대표 모델 |
|---|---|---|
| **LLM** | 텍스트 추론 (기본) | Claude · GPT · Gemini |
| **VLM** | 이미지+텍스트 멀티모달 | GPT-4o · Gemini Vision · Claude Vision |
| **SLM** | 엣지·로컬·비용 최적 | Llama 3.3 70B · Mistral Small · Gemma 4 |
| **MoE** | 선택적 전문가 활성화 | Mixtral · DeepSeek V3 |
| **MLM** | 양방향 컨텍스트 (임베딩) | BERT · RoBERTa |
| **LAM** | 시스템·도구 조작 | 장래형 (에이전트) |
| **SAM** | 픽셀 세그먼트 | Meta SAM 2 |
| **LCM** | 문장/개념 단위 | Meta SONAR |

**라우팅 확장 규칙**:
- 이미지 포함 요청 → VLM (Claude Vision 또는 Gemini)
- 로컬 처리·비용 0 → SLM (`exec_offline` 플러그인 위임)
- 임베딩·RAG → MLM 또는 전용 모델 (`ai_rag` 플러그인)
- 비디오/이미지 세그먼트 → SAM (`mcp_media` 위임)

---

## Step 3: 라우팅 결정표

| CODEX | GEMINI | 태스크 | 실행 경로 |
|-------|--------|--------|---------|
| ✅ | ✅ | LARGE  | `task-instruction.md` → `codex-auto` → Claude 보완 → `gemini-auto` |
| ✅ | ✅ | VERIFY | `task-instruction.md` → `gemini-auto --verify` |
| ✅ | ✅ | SMALL  | Claude 직접 구현 → `gemini-auto --verify` |
| ✅ | ❌ | LARGE  | `task-instruction.md` → `codex-auto` → Claude 검증 |
| ✅ | ❌ | SMALL  | Claude 직접 구현 (codex-auto 필요 시 선택) |
| ❌ | ✅ | VERIFY | `task-instruction.md` → `gemini-auto` |
| ❌ | ❌ | ANY    | Claude 직접 구현 + 검증 (`task-instruction.md` 불필요) |

---

## 자동 시작 모드 (CODEX + GEMINI 모두 가용)

```
전제: .claude/tasks/stop 파일 없음

1. stop 파일 제거:
     del .claude\tasks\stop 2>nul
     del %USERPROFILE%\.claude\orca\stop 2>nul

2. 워커 spawn (인자 없음 — config의 수치 자동 적용):
   ▸ 글로벌 우선 (codex-auto-global 있으면):
       start /min cmd /c "codex-auto-global"        ← ~/.claude/orca/workers-config.json 의 max_workers.codex 까지 채움
       start /min cmd /c "gemini-auto-global"
   ▸ 없으면 로컬:
       start /min cmd /c "codex-auto"                ← .claude/orca-workers-config.json 의 workers.codex 개수 spawn
       start /min cmd /c "gemini-auto"

   ⚠️ 절대 `codex-auto 1` 처럼 1을 명시적으로 주지 말 것 — config의 4/2 가 무시됨.
      인자 생략 = config값 사용.

3. 상태 확인 (10초 후):
   tasklist | findstr /i "cmd.exe codex" → 프로세스 수 확인
   또는 /check-agents 로 보고

4. 중단: /loop-stop 또는 .claude/tasks/stop 생성 (로컬) / ~/.claude/orca/stop (글로벌)
```

---

## 단독 모드 (CODEX만 가용)

```
- codex-auto 1  ← 단일 워커 실행
- Claude가 gemini 역할 대행 (검증 + 문서화)
```

---

## 직접 모드 (둘 다 없음)

```
- Claude가 구현 + 검증 모두 직접 처리
- task-instruction.md 작성 불필요
- 즉시 구현 시작
```

---

## Quota Fallback (Codex/Gemini API 한도 초과 시)

**트리거**: codex 또는 gemini 호출에서 "usage limit / rate limit / quota exceed / 429" 감지

**플래그 파일**:
- Codex: `.claude/state/codex-quota-exceeded` (JSON, expire_epoch 포함)
- Gemini: `.claude/state/gemini-quota-exceeded`

**자동 감지 스크립트**:
```bash
# bat 러너 내부에서 실패 후:
bash plugins/exec_orch/scripts/codex-quota-check.sh --check-error "$STDERR_LOG"
# → "usage limit" 감지 시 플래그 생성 + exit 2

# 세션 시작 시 (exec_orca-auto):
bash plugins/exec_orch/scripts/codex-quota-check.sh --status
# → 플래그 있고 TTL 안 지났으면 exit 2
```

**플래그 존재 시 라우팅 변경**:

| 원래 경로 | 한도 시 대체 |
|----------|-------------|
| LARGE → codex 4대 병렬 | **Claude 직접 구현** (용량 분할 필요 시 2~3회 split) |
| VERIFY → gemini 2대 | **Claude 자체 검증** 또는 다른 AI (Codex 쪽이 가용하면) |
| SMALL → 그대로 | 변경 없음 |

**사용자 고지 (필수)**:
한도 감지 시 **항상 명시**:
```
⚠️ Codex API 한도 초과 — Claude 직접 모드로 fallback
  만료 예정: 2026-04-19 13:35 (플래그 TTL 3h)
  수동 해제: bash plugins/exec_orch/scripts/codex-quota-check.sh --clear
```

**금지**:
- 한도 상황에서 task-N.md 를 done/ 으로 이동 (빈 완료 위장) — 절대 금지
- 사용자에게 "어느 AI 쓸까요?" 재질문 — 자동 fallback 수행 후 보고

---

## task-instruction.md 작성 조건

| 조건 | task-instruction.md 필요 여부 |
|------|---------------------------|
| CODEX_AVAILABLE AND LARGE | ✅ 필요 |
| GEMINI_AVAILABLE AND VERIFY | ✅ 필요 |
| Claude 직접 (SMALL 또는 둘 다 없음) | ❌ 불필요 |

---

## 금지 사항

- 사용자에게 "어떤 AI 사용할까요?" 묻지 않는다
- codex-auto 없이 task-instruction.md만 작성하지 않는다
- gemini 리뷰 의견을 Claude 승인 없이 자동 적용하지 않는다

---

## Step 4: 스코프 결정 (로컬 vs 글로벌)

여러 프로젝트에서 동시에 `/exec_orch` 를 쓰면 프로젝트마다 워커 N개 spawn → 총 N×프로젝트수 → 메모리 과부하.
이를 막기 위해 `/exec_orch` 플로우는 **글로벌 큐**를 기본으로 사용한다.

```
IF CODEX_GLOBAL_AVAILABLE (codex-auto-global 설치됨):
    스코프 = 글로벌
    →  orca-dispatch .claude/tasks/task-instruction.md codex
       (태스크를 ~/.claude/orca/tasks/ 로 복사, frontmatter에 project_root 자동 삽입)
    →  codex-auto-global  (빈자리만큼 워커 spawn, max_workers.codex 상한 엄수)
ELSE:
    스코프 = 로컬 (기존 동작)
    →  codex-auto N  (프로젝트 로컬 워커)
```

Validator 단계도 동일:
```
IF GEMINI_GLOBAL_AVAILABLE:
    orca-dispatch .claude/tasks/task-instruction.md gemini
    gemini-auto-global
ELSE:
    gemini-auto N
```

### 글로벌 태스크 포맷

`orca-dispatch` 헬퍼가 아래 frontmatter를 자동 삽입한다:

```yaml
---
task_id: 20260419-123045-projA-a1b2
project_root: C:\work\projectA
project_id: projectA
agent: codex        # 또는 gemini, claude
source: <원본 task-instruction.md 절대경로>
created_at: 2026-04-19T12:30:45
---
```

워커는 `project_root` 로 cd → `codex-a --auto <task>` 호출 → 완료 시 `~/.claude/orca/done/` 로 이동.

### 글로벌 상한 관리

`~/.claude/orca/workers-config.json` 의 `max_workers.codex`/`.gemini`/`.claude` 값이 전역 상한.
워커는 spawn 전 `~/.claude/orca/workers/*.hb` (2분 이내 갱신된 것만) 를 센 뒤 빈자리만큼만 생성.

### 언제 로컬?

- 단일 프로젝트에서 수동으로 `.claude/tasks/task-*.md` 편집 후 `codex-auto` 직접 실행할 때
- 프로젝트 고유 경로/워크스페이스에 강하게 결합된 태스크 (예: 특정 venv에서만 빌드 가능)
