# 9-Chain ↔ 8 Workflow YAML 매핑

> **근거**: 2026-10-27 사용자 지적 — "9개 체인 중 하나 누락? vs 하나의 YAML이 여러 체인 포함?"
> **결론**: **다른 축**. 9 체인 = **업무 도메인** · 8 YAML = **범용 workflow 단계**.

## 두 축

### 축 A — 9 체인 (업무 도메인별 · 외부 감사 보고서 B)

| # | 체인 | 담당 Agent / Skill (현재 산재) |
|---|---|---|
| 1 | 시장조사 | `explorer` + `tech_discovery.py` + `ig-research` |
| 2 | 고객분석 | `data-scientist` + `mcp_data` |
| 3 | 콘텐츠기획 | `pm` + `brainstorming-partner` |
| 4 | 카피/대본 | `design_ppt` · `design_word` · `design_excel` |
| 5 | 디자인 | `agent-06-designer` + `design_web` · `design_pdf` |
| 6 | 영상제작 | `design_video` + `design_pdf` |
| 7 | 채널운영 | `ig-upload` · `ig-analytics` + `yt-upload` |
| 8 | 광고개선 | `mcp_web` + `exec_orch` |
| 9 | 성과분석 | `agent-05-monitor` + `data-scientist` + `mcp_data` |

**현재 상태**: 전용 체인 **0건** · 자동 파이프라인 **0건** (수동 호출).

### 축 B — 8 Workflow YAML (범용 meta-workflow · 2026-10-27 신설)

| # | YAML | 역할 |
|---|---|---|
| 01 | `01-goal.yaml` | 사용자 목표 수신 → Supervisor goal 등록 |
| 02 | `02-discovery.yaml` | 미등록 기술·도메인 탐색 |
| 03 | `03-research.yaml` | WebSearch · 공식 docs |
| 04 | `04-plan.yaml` | Task 분해 + 라우팅 |
| 05 | `05-execute.yaml` | **Worker dispatch** (여기서 축 A 호출) |
| 06 | `06-verify.yaml` | test · build · smoke |
| 07 | `07-repair.yaml` | FAIL 격리 수정 (Anti-Ping-Pong 포함) |
| 08 | `08-learn.yaml` | solution 등재 · recurrence |

## 매핑 (축 A ↔ 축 B)

**축 A는 축 B의 05-execute 단계 안에서 호출**된다.

```text
사용자 목표 "인스타 광고 성과 분석"
    ↓
[01-goal]      goal 등록
    ↓
[02-discovery] 어떤 도메인? → "채널운영 + 성과분석" 매칭
    ↓
[03-research]  최신 Instagram Insights API 조사
    ↓
[04-plan]      Task 분해 → ["ig-analytics 호출", "data-scientist 분석"]
    ↓
[05-execute]
     ├── 축 A #7 채널운영 → ig-analytics (plugin 호출)
     └── 축 A #9 성과분석 → data-scientist agent 호출
    ↓
[06-verify]    수치 검증 · 샘플 하한
    ↓
[08-learn]     결과 솔루션 등재
```

## 누락 여부 (사용자 질문 "9 중 하나 누락?")

- **8 YAML ≠ 9 체인 - 1** · 다른 축
- **9 체인은 05-execute 안에서 전부 호출 가능** · 축 B 가 **8개로 충분** (goal → discovery → ... → learn 선형)
- 축 A 9 개 모두 커버되려면 **05-execute 가 N 개 Task 를 병렬·순차 dispatch** 가능해야 (현재 YAML 스펙상 가능 · 실제 엔진 `workflow-run.py` minimal 구현 2026-10-27)

## 다음 단계 (실제 CONNECTED)

| 작업 | 담당 YAML | 상태 |
|---|---|---|
| 05-execute step `dispatch` 에서 축 A 체인 호출 | 05-execute.yaml | **TODO** (현재 subagent/codex 매트릭스만 설계 · 축 A 직접 호출 X) |
| 각 축 A 체인별 skill 통합 skill-05-execute-<domain>.md 작성 | plugins/exec_orch/skills/ | **TODO** |
| workflow-run.py 가 05-execute 시 축 A 체인 선택 로직 | workflow-run.py | **minimal 구현** · 선택 로직 TODO |

## 관련

- `docs/ORCHESTRATION_AUDIT_1027.md § 보고서 B` (축 A 원본)
- `.claude/workflows/README.md` (축 B 설계)
- `.claude/scripts/workflow-run.py` (실행 엔진 minimal)
- `.claude/rules/execution-contract.md § 7` (상황 적응형 실행 매트릭스)
