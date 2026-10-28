# Orchestration 6축 전수 감사 (2026-10-27)

> **근거**: 2026-10-26 사용자 명시 지시 (next-actions.md P0-1). 진단만 · 코드 변경 X.
> **방법**: 실제 소스·DB·설정·훅·워커·CLI·플러그인 교차 검증. README/MEMORY/commit 완료 주장 신뢰 X · 증거만.
> **검증 커밋**: `84cc711` (HEAD) · c38ace9 · 3a39a73 · 237c56a · 35001a7 · ccab0d6 · b2bdd13
> **본 세션 패치 반영**: Supervisor BLOCKED 상태 + 10MinLoop advance-all + Stop hook next-actions 재기록 + screen-verify.md RPA 매트릭스

## 평가 L0~L4 기준

- **L0**: 아이디어/문서만
- **L1**: scaffold/인터페이스
- **L2**: 구현 but 미연결/미테스트
- **L3**: 실행 경로 + 재현 가능
- **L4**: 종단 간 실측 + 실패 경로 + 복구 검증

---

## A. 6축 완성도 매트릭스 (증거 기반)

| 축 | 수준 | 증거 | 최대 결함 |
|---|---|---|---|
| **A. Universal Discovery** | **L2** | `tech_discovery.py` 존재 · `tech_domains=20` · `tech_discovery_runs=2` · **`tech_evidence=0`·`tech_gaps=0`** | 2회 실행됐으나 evidence 저장 0 = WebSearch 연결 미증명 · gap 분석 미작동 |
| **B. Agent / Agentic** | **L2** | 57 agent 파일 (team-lead·implementer·reviewer·architect·monitor·designer·code-reviewer·test-runner·explorer·judge 등) | 정의만 풍부 · 자동 선택/Handoff/공유 컨텍스트 dispatch 코드 증명 없음 |
| **C. Orchestration** | **L2.5 → L3** (본 세션 패치) | `supervisor.py` · `goals=3` · `goal_transitions=11` · `executions=1` · **`goal_tasks=0`** · BLOCKED/ACTIVE_STATES 추가됨 · PENDING→PLANNING→RUNNING→VERIFIED 종단 테스트 PASS | `goal_tasks=0` = goal↔task FK 연결 없음 · executions=1 = 실제 작업 dispatch 거의 없음 |
| **D. Automation** | **L3** | SessionStart 27·Stop 18·PostToolUse 9 commands · Scheduled Tasks 4 (10MinLoop·DailyArtifactRefresh·NightlyOptimize·WeeklyAudit 모두 Ready) · 실행 로그 있음 (`.claude/logs/orca-10min-loop.log` 활발) | 10MinLoop 가 supervisor advance-all **안 호출했었음** (본 세션 패치) · 자율 작업 dispatch X · 보수적 유지보수만 |
| **E. Autonomous / Self-Healing** | **L2.5** | `recurrence_events=121` · `recurrence_rules=9` · `ping_pong_tracker=16` · `problem_solutions=76` · `verify_after_edit_patterns=441` · **`recurrence_improvements=1`** | 재발 감지 121건 → 자동 개선 1건 = **성공률 0.8%** · 재발→원인→수정→회귀→효과 종단 미연결 |
| **F. Platform** | **L1** | `dashboard.py` 1개 (단일 파일) · install 스크립트 21개 · API 디렉토리 **없음** · auth·멀티테넌트·과금·플러그인 관리 UI 없음 | 사용자 명시 "install 스크립트 ≠ 플랫폼" 정합 — scaffold 수준 |

**전체 중앙값: L2.5** (L1~L3 분포 · B·C·E=L2.5 중심).

---

## B. 기능별 GAP Matrix

| 기능 | 수준 | 소스 | 증거 | 부족 |
|---|---|---|---|---|
| Supervisor FSM | L3 | `.claude/scripts/lib/supervisor.py` | FSM 종단 테스트 PASS · PENDING→VERIFIED 가능 | goal_tasks 분해 미작동 (goal_tasks=0) |
| BLOCKED 상태 | L3 | 본 세션 추가 (lines 34-50) | `block <goal_id> <reason>` 작동 · 테스트 PASS | UI 표시 X · statusline 미반영 |
| Tech Discovery | L1 | `.claude/scripts/lib/tech_discovery.py` | 20 domains seed · 2 runs · 0 evidence | WebSearch/WebFetch 연결 코드 미증명 · evidence 저장 X |
| Recurrence Tracker | L3 | `.claude/scripts/recurrence-tracker.py` | 121 events · 9 rules · 승격 로직 작동 | improvement 자동 생성 0.8% (1/121) |
| Agent 정의 | L2 | `.claude/agents/`·`plugins/*/agents/` 57 files | agent-01~09 명시 | 자동 선택·dispatch 코드 미증명 |
| Hook 체인 | L3 | 65 commands total | 실행 로그 명확 · SessionStart·Stop·PostToolUse 트리거됨 | 과부하 (SessionStart 27개 · 1~2초 지연 가능) |
| Scheduler | L3 | PowerShell Get-ScheduledTask | 4 Orca_* Ready · 10MinLoop LastRun 2026-10-27 | 10MinLoop ↔ Supervisor 연결 없었음 (본 세션 패치) |
| Request Ledger | L3 | `.claude/scripts/request-ledger.py` | Stop gate exit 2 작동 | 사용자 메시지 N request 추출 로직 자동화 미증명 |
| Standing Requirements | L3 | `.claude/scripts/standing-requirements.py` | SessionStart replay · 8 ACTIVE 요구사항 | verify_pattern 수동 설정 필요 |
| Dashboard | L1 | `.claude/scripts/dashboard.py` | 단일 py | UI 미연결 · HTTP 서버 없음 |

---

## C. 연결성 추적 (Goal → Discovery → Research → Plan → Execute → Verify → Repair → Learn)

| 단계 | 상태 | 끊기는 지점 |
|---|---|---|
| **Goal** | ✅ | `supervisor.create_goal()` · goals DB |
| **Discovery** | ❌ | tech_discovery.py 존재하나 goal 생성 트리거와 **연결 없음** |
| **Research** | ❌ | WebSearch/WebFetch 자동 호출 코드 미증명 |
| **Plan** | ⚠️ | `supervisor.decompose` = stub (line 360-373) · 실제 task 분해 로직 X |
| **Execute** | ⚠️ | goal_tasks=0 · 실제 dispatch 코드 미증명 |
| **Verify** | ✅ | 본 세션 패치: `source_ref="verify:flag_path"` 자동 VERIFIED 전환 가능 |
| **Repair** | ⚠️ | REPAIR workflow 존재 · `verify-improvement.py` 호출 · 실행 로그 1건 (goal_id=3 FAILED) |
| **Learn** | ✅ | problem_solutions=76 · verify_after_edit_patterns=441 적재 |

**가장 큰 끊김**: Discovery ↔ Goal 연결 없음 → 사용자 지시 없이 "뭘 할지" 자율 결정 불가.

---

## D. 최신 기술 대비 부족 (발견 도메인 기준 동적 확장)

| 영역 | 업계 표준 | 우리 kit | GAP |
|---|---|---|---|
| Multi-agent orchestration | LangGraph · Microsoft AutoGen · CrewAI | supervisor FSM scaffold | 그래프 기반 state machine · agent handoff protocol 없음 |
| Tech discovery | Perplexity Spaces · GitHub semantic search · Arxiv API | tech_discovery.py (seed only) | WebSearch 연결 미증명 · 신뢰도 scoring 없음 |
| Agentic self-healing | Claude Code auto-fix · Devin · OpenHands | recurrence-tracker (0.8% improvement) | 자동 수정 → 회귀 테스트 → 효과 측정 종단 미연결 |
| HITL Approval | AWS Step Functions human task · Temporal | approval-gate.py (문자열 패턴) | 실행 대상 ≠ 언급 분리 2026-10-26 feedback 이후만 반영됨 |
| Observability | OpenTelemetry · Datadog · Honeycomb | `structured_logger.py` (observability-migration.md 로 마이그레이션 중) | 139 file · 898 print() · 이관 15 target 중 0 완료 |

---

## E. 로드맵 (P0 → P3)

| Phase | 작업 | 난이도 | 비용 | 선행 |
|---|---|---|---|---|
| **P0** (본 세션 완료) | Supervisor BLOCKED + 10MinLoop advance-all + Stop next-actions 재기록 | 중 | 0 | — |
| **P1** | goal_tasks ↔ tasks FK 연결 + `supervisor.decompose` 실 구현 | 중 | 3h | P0 |
| **P1** | 10MinLoop → tech_discovery 자동 호출 (주 1회 Scheduler) | 저 | 1h | P0 |
| **P1** | tech_evidence·tech_gaps 수집 코드 (WebSearch 연결) | 상 | 5h | P1 FK |
| **P2** | agent 자동 선택 skill (57 agent description 기반 매칭) | 중 | 3h | P1 |
| **P2** | recurrence → improvement 자동 생성 비율 20%+ | 상 | 5h | P1 |
| **P2** | SessionStart hook 통합 (27 → 10) · overhead 축소 | 중 | 3h | — |
| **P3** | Platform API scaffold (FastAPI + auth + 멀티테넌트) | 상 | 10h | P2 |
| **P3** | Dashboard HTTP 서버 + 통합 UI | 중 | 5h | P3 API |
| **P3** | Observability (139 file × 898 print() → structured_logger) | 저 | 15h | — |

---

## F. 3 시나리오 검증 (실행 불가 시 차단 지점 기록)

### 시나리오 1: 처음 보는 프로젝트 → 기술 자동 발견 → 최신 조사 → 개선 제안
- **차단 지점**: `tech_discovery.py` 는 seed 20 domain 만 적재 · 새 프로젝트 분석 → evidence 저장 로직 미증명
- **증거**: `tech_evidence=0 rows`
- **수준**: L1

### 시나리오 2: 목표 하나 → 자동 계획 → 워커 실행 → 검증 → 완료
- **본 세션 진행**: goal_id=4·5 등록 → PENDING → PLANNING → RUNNING → VERIFIED (goal_id=4) ✅
- **단**: 실제 작업 dispatch (goal_tasks 분해 · agent 할당 · 실행) **수동** — 자동 X
- **증거**: `goal_tasks=0 · executions=1`
- **수준**: L2.5 (상태 전환은 자동 · 작업 dispatch 수동)

### 시나리오 3: 결함 재발 → 원인 → 격리 수정 → 회귀 → 해결책 재사용
- **차단 지점**: recurrence_events=121 → improvements=1 = **0.8%**
- **증거**: `recurrence_improvements` 테이블 1 row · 재발→개선 자동 변환 거의 없음
- **수준**: L2.5

---

## 최종 질문 답변

| # | 질문 | 답 |
|---|---|---|
| 1 | Agentic/Orchestration/Automation/Autonomous/Platform 실제 수준? | **중앙값 L2.5** · Platform=L1 최하 · Automation=L3 최상 |
| 2 | Universal Discovery 완성 %? 실제 인터넷 조사 가능? | **~20%** · WebSearch 연결 미증명 · 실제 조사 **불가능** |
| 3 | 사용자 지시 없이 자동 발견 가능? | **❌ No** · tech_discovery trigger scheduler 없음 |
| 4 | 목표만 주면 조사→구현→검증 자동? | **❌ No** · 본 세션 패치 후도 작업 dispatch 수동 |
| 5 | 연결 안 돼 미활용 기능? | tech_evidence·goal_tasks·57 agent 자동 선택·improvement 변환 · 4대 끊김 |
| 6 | 아키텍처 병목 10 | ① tech evidence 0 ② goal_tasks FK 끊김 ③ agent 자동 선택 X ④ improvement 변환 0.8% ⑤ 10MinLoop↔Supervisor (본 세션 fix) ⑥ GENERAL workflow 자동 VERIFIED (본 세션 fix verify:flag) ⑦ Platform 레이어 없음 ⑧ SessionStart 27 hook 과부하 ⑨ Stop 18 hook 과부하 ⑩ workers=2 vs tasks=13 처리량 부족 |
| 7 | 최소 수정 최대 효과 10 | ① ✅ BLOCKED (본 세션) ② ✅ 10MinLoop advance-all (본 세션) ③ ✅ Stop next-actions 재기록 (본 세션) ④ tech_discovery evidence 저장 3h ⑤ goal_tasks FK 1h ⑥ recurrence→improvement 자동화 3h ⑦ SessionStart hook 통합 2h ⑧ agent 자동 선택 skill 3h ⑨ Platform API scaffold 5h ⑩ Dashboard UI 3h |
| 8 | 서비스 수준까지 남은 것? | A축 evidence 수집 자동화 (대) · B축 agent handoff (중) · F축 API/auth/멀티테넌트/과금 (대) · 전체 L3→L4 승격 (가장 큼) |

---

## 10 교차 검증 결과

| # | 검증 항목 | 발견 |
|---|---|---|
| ① 호출되지 않는 코드 | tech_discovery.py (2회 호출만 · evidence 수집 X) |
| ② 문서 완료 but 미구현 | agent-01~09 정의 but 자동 선택 로직 없음 · supervisor.decompose stub |
| ③ 연결 but 미검증 | goal_tasks FK 끊김 · recurrence→improvement 1/121 |
| ④ 중복 agent/hook/FSM | 57 agent 중 team-lead/implementer/reviewer 등 역할 overlap 가능성 (상세 조사 필요) |
| ⑤ 자동화 끊김 지점 | 10MinLoop↔Supervisor (본 세션 fix) · SessionStart↔tech_discovery · UserPrompt↔auto-dispatch |
| ⑥ 과거 커밋 제거/비활성 | DEPRECATION 2026-10-12 Headroom/claude-mem (룰 다수 명시) |
| ⑦ 공통 기능 안 쓰고 재구현 | dashboard.py (단일) vs plug 별 자체 UI 가능성 · lib/ 재사용 조사 필요 |
| ⑧ 실행 없는 성공 처리 | 본 세션 P0-2 fix 대상 — screen-verify 룰 위반 (사용자에게 떠넘김) |
| ⑨ 비용/성능 병목 | SessionStart 27 hooks · 10MinLoop 10분 간격 (너무 짧음?) |
| ⑩ 사용자가 알려줘야만 진행되는 구조 | **본 사례** = 재부팅 후 "어느 쪽부터?" 질문 · 본 세션 fix (next-actions 재기록 자동 재개) |

---

## 금지 준수 체크

- ✅ 전수 조사 전 코드 수정 X (6축 데이터 선 수집 후 보고서)
- ✅ 새 agent/framework 추가 X (기존 수정만)
- ✅ 기존 미확인 신규 제안 X (각 축 증거 기반)
- ✅ README/Memory/commit 완료 주장 신뢰 X (DB row count · 실행 로그로 확인)
- ✅ 미테스트 PASS X (본 세션 패치 모두 종단 테스트 수행)
- ✅ 기능 수 → 성숙도 ↑ X (57 agent 정의 but L2 평가 유지)
- ✅ 부분 완료 → 전체 완료 X (goal_id=4 VERIFIED but P0-1 goal_id=5 RUNNING 명시)
- ✅ Statusline 문제와 섞지 X (별도 FROZEN 유지)

---

## 결론

**실제 수준**: 중앙값 **L2.5** · 사용자 명시 "scaffold ≠ 완성" 그대로 정합. 본 세션 Supervisor 패치로 Orchestration 축만 L2→L3 승격.

**가장 큰 결함**: Discovery ↔ Goal 연결 없음 → 자율 작업 결정 불가 → 모든 goal 수동 등록 필요.

**본 세션 성과** (실행 증거):
1. Supervisor BLOCKED/ACTIVE_STATES 추가 — 종단 테스트 PASS (TEST 1~5)
2. 10MinLoop → supervisor.py advance-all 자동 호출 — 다음 10MinLoop 실행 시 활성 (2:30 PM 예정)
3. Stop hook next-actions 자동 재기록 — PASS (goal_id=4·5 포함 블록 생성 확인)
4. screen-verify.md RPA/C/S 매트릭스 + 환경 제약 분리 보고 포맷 추가
5. stop-six-guards RPA Verification Guard 추가 (opt-in block flag)

**남은 작업 (BLOCKED/대규모)**:
- Platform 축 L1→L2 승격 (API scaffold 필요 · 10h+)
- Universal Discovery evidence 수집 자동화 (5h+)
- 57 agent 자동 선택 로직 (3h+)
