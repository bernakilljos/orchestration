# MEDIUM 4건 재분류 결과 (2026-10-29)

> **근거**: 사용자 지시 "결함이 아닌 의도된 설계는 NOT_A_DEFECT로 분류하고 근거를 남긴다" · "검증되지 않은 작업을 완료로 선언하지 않는다"
> **원칙**: 소스 전수조사 + 실제 호출 경로 + 재현 가능성 분석 후 판정. 결함 가정 없이 수정 금지.

## 결과 요약

| # | 결함 (원 지적) | 판정 | 근거 |
|---|---|---|---|
| **#8** | Agent 분산 (19 global + plugin · 중앙 registry 없음) | **NOT_A_DEFECT** | Claude Code 자동 탐색 + dedupe-agent.py SoT 관리 |
| **#6** | workflow 8 YAML (문서는 9-chain 주장) | **NOT_A_DEFECT** | 축 2개가 다름 (YAML=실행 파이프라인 · docs=업무 도메인) |
| **#4** | STALE_SEC = 6h 고정 | **NOT_A_DEFECT** | BASIS 2026-10-16 명시 합의 + 한계·대안 문서화 |
| **#2** | 60/200자 분류 경계 (다국어 미흡) | **NOT_A_DEFECT** | 글자수 임계값 상수 자체 소스에 없음 · 정규식 패턴 (언어 중립) |

**4건 모두 결함 아님** · 코드 변경 **0건** · 커밋 생성 **X** (지시 10 준수).

---

## #8 Agent Registry — NOT_A_DEFECT

### 전수조사

- `.claude/agents/*.md`: **19개** (SoT · Claude Code 자동 로드)
- `plugins/*/agents/*.md`: **29개** (대부분 `.claude/agents/` 와 md5 동일 · sync 결과물)
- 중앙 Registry 파일 (`.claude/config/agent-registry.*`): **없음**

### 실제 호출 경로

```bash
grep -rE "agent.*select|choose_agent|dispatch_agent|agent_for" .claude/scripts/
# → 매치 0건
```

**Agent 선택 메커니즘**:
- Claude Code 플랫폼이 사용자 메시지 분석 → `.claude/agents/*.md` description 매칭 → 자동 로드
- `Agent(subagent_type="...")` tool 호출 시 플랫폼이 enum 참조
- 외부 orchestrator (supervisor·workflow) 가 agent 를 **런타임 선택** 하는 코드 **없음**

### SoT 관리

`.claude/scripts/dedupe-agent.py` 결과 (2026-10-29 실행):
- 유지 (SoT): 16 · REMOVE: 0 · 다른 해시: 0
- SoT 우선순위: `.claude/agents` > `plugins/exec_orch/agents` > 알파벳

### 판정 근거

- Claude Code 자동 탐색이 **플랫폼 메커니즘** · 중앙 Registry 파일 불필요
- `dedupe-agent.py` 가 SoT 일원화 유지
- 중앙 Registry 가 필요한 것은 외부 orchestrator **런타임** 선택 시 (현재 kit 엔 그 호출 경로 없음)

**통합 Registry 필요 조건** (해제 조건):
- workflow·supervisor 가 agent 를 런타임 선택하는 feature 가 추가되면 그때 신설
- 지금은 scaffold 조차 불필요

---

## #6 Workflow Drift — NOT_A_DEFECT

### 전수조사

**실제 workflow YAML (`.claude/workflows/`)**:
```text
01-goal.yaml · 02-discovery.yaml · 03-research.yaml · 04-plan.yaml
05-execute.yaml · 06-verify.yaml · 07-repair.yaml · 08-learn.yaml
```

→ **8개 · 실행 단계 파이프라인** (orchestration meta pipeline)

**docs 9개 체인 (`ORCHESTRATION_AUDIT_1027.md § 보고서 B`)**:
```text
1. 시장조사 · 2. 고객분석 · 3. 콘텐츠기획 · 4. 카피/대본 · 5. 디자인
6. 영상제작 · 7. 채널운영 · 8. 광고개선 · 9. 성과분석
```

→ **9개 · 업무 도메인 체인** (business domain chain)

### 판정 근거

두 축이 다른 축. workflow YAML 8 = **메타 실행 파이프라인** · docs 9 = **업무 종류** (SNS 광고 운영 등). drift 아님.

### 실행 상태 vs 기록 상태 비교 (사용자 지시 특별 주의)

**supervisor goals (`orca.db`)** 통계:
- Total: 42 · BLOCKED: 1 · FAILED: **25** · RUNNING: 1 · VERIFIED: 15

**workflow-run.log (2026-10-27)**:
- `07-repair FAIL at isolate_sandbox`
- `01-goal FAIL at parse_requests`

**별도 발견 (범위 밖 · 보고만)**:
- 25/42 (59%) goals FAILED — workflow 실행 로직 결함 가능성
- 이것은 **#6 범위 아님** (docs/YAML 축 불일치가 아니라 **런타임 실패**)
- 다음 세션 안건: workflow-run.log 25건 FAILED 원인 분석 (별도 결함)

사용자 지시 9 "범위 밖의 항목은 VERIFIED로 승격하지 않는다" 준수 — 발견만 기록.

---

## #4 STALE_SEC = 6h 고정 — NOT_A_DEFECT

### 전수조사

실제 사용처 (2곳):

1. `request-ledger.py:189` — `STALE_SEC = 6 * 3600`
   - 역할: Stop gate 가 6시간 넘게 안 바뀐 ledger (지난 작업) 는 **통과** (영원히 블록 방지)
   - 코드 안 BASIS 명시: `agreed(2026-10-16, 한 세션의 요청 묶음은 몇 시간 안에 끝난다 — 6시간 넘게 안 바뀐 ledger 는 지난 작업. 한계: 6시간 넘게 이어지는 긴 작업의 미완은 놓친다. 그때는 시각이 아니라 세션 id 대조로 바꾼다.)`

2. `surface_log_errors.py:30` — `RENOTIFY_SEC = 6 * 3600`
   - 역할: 같은 오류 매 프롬프트 반복 X · 하루 4번 이내
   - BASIS 명시: `agreed(2026-10-16, 같은 오류를 매 프롬프트 넣으면 잡음)`

### 다른 축 상수 (혼동 금지)

- `worker-health.sh:23` STALE_SEC=300 (5분) — worker heartbeat
- `ensure-state.sh:36` 21600 (6h) — audit 재생성 주기 (별도 축)
- `recurrence-tracker.py:41` STALE_DAYS=60 — rule archive (별도 축)

### 판정 근거

- 두 사용처 모두 **명시적 합의 (BASIS 2026-10-16)** · 근거·한계·대안 코드 안 문서화됨
- **artifact-freshness-check.md 유통기한 매트릭스와는 다른 축**:
  - STALE_SEC = **운영 안전 상한** (Stop gate 영원 블록 방지 · 오류 알림 과포화 방지)
  - artifact 유통기한 = **산출물 신선도** (산출물이 outdated 됐나)
- 통합 시 축 혼재 · 부적절

**경계값 테스트** 불필요: 로직 명확 (`session_id == 'test' OR time - mtime > STALE_SEC → pass`) · BASIS 로 한계 문서화됨.

---

## #2 다국어 분류 (60/200자 경계) — NOT_A_DEFECT

### 전수조사 결과

`.claude/scripts/classify-task.py` 전체 (103 라인) 안:
- **글자수 비교 로직 없음** (`len(message)` 매치 0건)
- `len()` 사용은 `len(sys.argv) < 2:` (CLI arg 체크 · 분류와 무관)
- **60·200 상수 없음** (grep 결과)

### 실제 분류 로직

정규식 패턴 매칭만 사용:
```python
# code_implementation 트리거 패턴 (대표)
r"(\d{3,}|300\+|500\+|대량|batch)\s*(줄|line|file|파일)"
r"(refactor|리팩토링|마이그레이션|migration)"
r"(전체|모든|all)\s*(파일|file|폴더|directory).*(?:수정|편집|edit|update)"
```

### 다국어 상태

- 한글 조사 (`로|으로|에게|한테|시켜|써`) — 명시 대응 (R13 결함 수정 2026-10-16)
- 영어 (`refactor|migration|batch|multiple|long context`) — OK
- 패턴 자체 언어 중립 (단어 매칭)
- 글자수·토큰수 임계값 **없음**

### 판정 근거

보고서가 지적한 **"60/200자 분류 경계"** 상수 자체가 소스에 **없음**. 이전 H5 재감사와 유사 패턴 — 보고서가 추정한 결함이 실재 X.

**이전 commit 18ff2b0 H5 재감사와 동일 패턴**:
- regex `\d{3,}|300\+|500\+` 는 사용자 자연어 메시지 안 숫자 매칭 (예: "300줄 코드 만들어줘")
- 로직 임계값 비교 X · 지적된 "경계값" 자체가 없음

---

## 회귀 테스트 결과

| 테스트 | 결과 |
|---|---|
| test-h1-h2-h4-e2e.py | **68/68 PASS** |
| golden-test.py | **13/13 PASS** |

MEDIUM 재분류 작업 중 **코드 변경 0건** · 회귀 테스트 영향 없음.

---

## 결론

### 공식 판정

| # | 판정 | 사용자 조건 (지시 6 "문서/설정만 변경하고 완료 처리하지 않는다") |
|---|---|---|
| #8 | NOT_A_DEFECT | 플랫폼 메커니즘 · 코드 변경 불필요 |
| #6 | NOT_A_DEFECT | 축 2개 분리 설명만 · 코드 변경 불필요 |
| #4 | NOT_A_DEFECT | BASIS 명시 · 코드 변경 불필요 |
| #2 | NOT_A_DEFECT | 결함 자체 소스에 없음 · 수정 대상 없음 |

### 남은 위험 (범위 밖 · 다음 세션 안건)

| 발견 | 상태 | 다음 세션 처리 |
|---|---|---|
| supervisor goals 25/42 (59%) FAILED | **별도 결함** | workflow-run.log 25건 FAILED 원인 분석 |
| workflow 07-repair isolate_sandbox FAIL | **별도 결함** | repair 체인 재현 |
| workflow 01-goal parse_requests FAIL | **별도 결함** | goal 체인 재현 |
| grok · gpt-5.2 실 API 검증 | **BLOCKED** | xAI · OpenAI API key 필요 |
| AiChoice enum 완전 제거 | **SCAFFOLD** | 사용자 명시 승인 필요 |

### Operating Principles 준수

- Statusline FROZEN · 승인 정책 X · 계정 전환 X
- Change Budget: NEW 1 (이 문서) · CHANGE 0 · REMOVE 0
- 지시 6·9·10 준수 (문서만 변경 완료 X · 범위 밖 승격 X · 불필요 커밋 X)

### 다음 단계 진입 조건

MEDIUM 4건 NOT_A_DEFECT 판정 → **MEDIUM 작업 종결**.

다음 세션 안건 우선순위 (사용자 로드맵):
1. **workflow-run.log 25 FAILED 원인 분석** (이번 세션 발견 · 범위 밖 승격 X · 다음 세션 R? 로 등재)
2. P1 다중 지시 동적 종단 (Request Ledger → Goal → Task → Runner → Verification 체인 실측)
3. 실제 Self-Healing (오류 진단 → 격리 Worktree → 테스트 → 재검증)
4. Universal Technology Discovery
5. 다중 Agent 능력 기반 DAG 실행

## 관련

- `docs/P0B_STATUS_MATRIX_2026-10-29.md` (P0b 종료 매트릭스)
- `docs/HARDCODING_AUDIT_2026-10-28.md` (원 감사)
- `.claude/scripts/classify-task.py` (#2 소스)
- `.claude/scripts/request-ledger.py:189` (#4 BASIS 명시)
- `.claude/scripts/dedupe-agent.py` (#8 SoT 관리)
- `.claude/workflows/*.yaml` (#6 실행 파이프라인)
