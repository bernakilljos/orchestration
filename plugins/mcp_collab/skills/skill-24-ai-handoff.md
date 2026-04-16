# Skill 24: AI Handoff (멀티AI 강제 연동)

## 목적
Claude ↔ Codex ↔ Gemini 간 작업 인수인계를 강제화한다.
각 AI가 독립적으로 일하지 않고, 반드시 결과를 다음 AI에게 전달하도록 보장.

## 핵심 원칙
```
1. 혼자 끝내지 마라 — 반드시 다음 AI에게 넘겨라
2. 받았으면 확인해라 — 이전 AI 결과물을 반드시 읽어라
3. 기록을 남겨라 — handoff-log.md에 인수인계 내용 작성
```

## 트리거
- task-instruction.md 작성 완료 시 (자동)
- codex-auto/gemini-auto 완료 시 (자동)
- "인수인계", "handoff", "넘겨" 언급 시

## Handoff Protocol

### Phase 1: Claude → Codex (구현 위임)
```
[Claude 작성 필수 항목]
1. .claude/tasks/task-instruction.md — 구현 지시서
2. .claude/tasks/handoff-log.md — 인수인계 로그

handoff-log.md 형식:
---
from: claude
to: codex
timestamp: 2026-04-12T11:00:00Z
task: task-instruction.md
context:
  - 설계 결정 사항 (왜 이 방식을 선택했는지)
  - 주의할 파일 목록
  - 기존 코드와의 관계
  - 테스트 우선순위
constraints:
  - 수정 금지 파일
  - 코딩 규칙 (대상 프로젝트 CLAUDE.md에 정의된 금지 패턴)
expected_output:
  - 구현 파일 목록
  - 테스트 파일
  - implementation-report.md
---
```

### Phase 2: Codex → Claude (보완 요청)
```
[Codex 완료 시 자동 생성]
.claude/tasks/done/{task-name}.md  — 완료 마킹
docs/implementation-report.md     — 구현 보고서

implementation-report.md 필수 항목:
  - 구현한 파일 목록 + 변경 내역
  - 설계 지시서와 다른 점 (있으면)
  - 미완성 항목 (있으면)
  - 테스트 결과
  - Claude에게 보완 요청 사항
```

### Phase 3: Claude → Gemini (검증 위임)
```
[Claude 보완 완료 후 자동 트리거]
1. .claude/tasks/task-instruction.md 에 검증 지시 추가
   또는 새 파일: .claude/tasks/verify-{task-name}.md
2. handoff-log.md 업데이트:
---
from: claude
to: gemini
task: verify-{task-name}.md
context:
  - Codex 구현 + Claude 보완 완료
  - 검증 포인트 (기능, 성능, 보안)
  - 참조할 테스트 파일
expected_output:
  - review-result.md (합격/불합격 + 상세)
  - 수정 필요 시 구체적 위치 + 코드
---
```

### Phase 4: Gemini → Claude (검증 결과 보고)
```
[Gemini 완료 시 자동 생성]
docs/review-result.md — 검증 결과

review-result.md 필수 항목:
  - 합격 / 불합격 / 조건부 합격
  - 발견된 이슈 목록 (파일:줄번호)
  - 수정 코드 제안
  - 보안 점검 결과
  - 성능 점검 결과

→ Claude가 최종 채택/수정 결정
```

## 강제 규칙 (HOOK에서 검증)

### hook-post-task-write (task-instruction.md 작성 후)
```
검증:
  1. handoff-log.md가 함께 생성되었는가?
  2. context 섹션이 비어있지 않은가?
  3. expected_output이 명시되어 있는가?
→ 미충족 시 경고 + 보완 요청
```

### hook-post-codex (codex-auto 완료 후)
```
검증:
  1. implementation-report.md가 생성되었는가?
  2. 변경 파일 목록이 있는가?
  3. 테스트 결과가 포함되어 있는가?
→ 미충족 시 done/ 이동 차단
```

### hook-post-gemini (gemini-auto 완료 후)
```
검증:
  1. review-result.md가 생성되었는가?
  2. 합격/불합격 판정이 있는가?
  3. 이슈 목록이 구체적인가 (파일:줄번호)?
→ 미충족 시 재실행 요청
```

## Handoff Dashboard 연동
```
status-push가 handoff-log.md를 읽어서 대시보드에 표시:
  [Claude] → task-instruction.md → [Codex] → impl-report → [Claude] → verify → [Gemini] → review → [Claude 채택]
  
각 단계별 상태: ⏳대기 / 🔄진행중 / ✅완료 / ❌실패
```

## 출력
- `.claude/tasks/handoff-log.md` — 인수인계 로그 (누적)
- `docs/implementation-report.md` — Codex 구현 보고
- `docs/review-result.md` — Gemini 검증 결과
