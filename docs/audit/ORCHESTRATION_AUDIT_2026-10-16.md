# Orchestration Kit Audit — 2026-10-16

## 결론

현재 문제는 기능 부족보다 **규칙 중복·상충 + 라우팅 불일치 + 종료 게이트 부재**가 크다.

### 실측
- ZIP 해제 크기: 약 343MB
- `.claude/hooks`: 217 files (실행 디스패처 기준 prompt 16 + PreTool 23 + PostTool 13 외 다수 보관/동기 파일)
- `.claude/skills`: 137 files
- `.claude/rules`: 51 files
- `.claude/agents`: 19 files
- SessionStart 등록 command가 매우 많아 세션 시작 오버헤드와 상태 드리프트 가능성이 큼.

## 핵심 결함

1. **Scope 충돌**
   - operating-principles: 요청 밖 인접 시스템 수정 금지
   - 기존 auto-planner: "사용자 명시 안 한 인접 시스템도 포함"
   - 결과: Claude가 범위를 자기 판단으로 넓힐 근거가 존재.

2. **중간보고 충돌**
   - complete-output: 끝까지 하고 1회 보고
   - 기존 auto-planner: 각 turn 시작 plan 출력 + Step5 A/B 선택 요구
   - 결과: 실행보다 설명/선택 요청으로 빠지기 쉬움.

3. **Codex가 로그인돼도 안 쓰이는 구조**
   - route_dispatch: Codex가 사실상 800k+ 또는 quota fallback
   - CLAUDE.md: 500줄+도 Claude general-purpose subagent가 1순위
   - classify-task: Codex 트리거가 매우 좁음
   - auto-dispatch: task 파일 enqueue 중심이며 실제 실행은 worker 존재에 의존
   - agent-02 문서: 사용자가 터미널에서 직접 실행한다고 명시
   - 결과: "Codex 사용" 의도와 실제 런타임이 불일치.

4. **다중요청 원장 없음**
   - 요청 1/2/3을 immutable ledger로 고정하는 단일 SoT가 없었음.
   - 완료조건은 많지만 "처음 받은 요구사항 수 대비 완료 수"를 강제하지 못함.

5. **고객용 UI와 내부 구현 설명의 경계가 없음**
   - 기술적으로 맞는 설명을 화면에 많이 넣는 경향을 제어할 규칙이 부족.
   - 고객 화면은 업무 흐름 중심, 파서/OCR/라이브러리 세부는 상세로 내려야 함.

6. **용량/배포 불필요 파일**
   - `claude-talk-to-figma-mcp/node_modules`: 약 126MB
   - `.codex/mcp/node_modules`: 약 70MB
   - `.claude/state`: 약 53MB
   - 이 세 개만 약 249MB. 배포 ZIP에는 의존성 재설치/런타임 state 제외 권장.

## 이번 패치

- `execution-contract.md` 신설: Request Ledger, n/n 완료, 중간보고 금지, Web/Codex 교차검증, 고객용 화면 규칙.
- auto-planner 재작성: 인접 범위 자동 확장 제거, A/B 선택 제거, 최종 1회 보고.
- classify-task 강화: Codex 명시/다중 파일/공통화/대량 변경을 Codex로 분류.
- prompt dispatcher 주입 문구를 Complete-First 방식으로 교정.
- Codex implementer 문서에서 "사용자가 직접 실행" 제거 → orchestrator 자동 호출 원칙.
- CLAUDE.md에 실행 계약 SoT 연결.

## 다음 권장 (2차 패치)

1. SessionStart 20+ command를 dispatcher 1개로 묶기.
2. 실제 사용하지 않는 hook 파일을 `archive/`로 이동해 탐색 노이즈 축소.
3. `.claude/skills`는 generated mirror임을 명확히 하고 plugin SoT만 직접 편집하도록 lint.
4. Stop hook에 Request Ledger 완료 게이트를 붙여 n/n이 아니면 종료를 deterministic하게 차단.
5. Codex worker heartbeat가 없을 때 auto-dispatch가 worker를 자동 spawn하거나 동기 fallback하도록 개선.
6. 고객용 UI reviewer를 별도 agent로 두기보다 기존 reviewer에 `customer-facing` 체크리스트를 추가해 agent 수 증가 방지.
