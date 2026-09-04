# Hook 08: AI Handoff Enforcement

## 목적
멀티AI 인수인계 프로토콜을 강제한다.
각 단계에서 필수 산출물이 없으면 진행을 차단.

## 트리거 시점

### 1. task-instruction.md 작성 후 (Claude → Codex)
```
검증 항목:
   .claude/tasks/task-instruction.md 존재
   handoff-log.md에 from:claude, to:codex 기록
   context 섹션에 설계 결정 사유 포함
   expected_output 명시
   constraints (수정 금지 파일, 코딩 규칙) 명시

실패 시:
  → "[HANDOFF]  인수인계 불완전 — handoff-log.md 보완 필요"
  → task-instruction.md 옆에 handoff-log.md 자동 생성 (빈 템플릿)
```

### 2. Codex 완료 후 (Codex → Claude)
```
검증 항목:
   docs/implementation-report.md 존재
   변경 파일 목록 포함
   테스트 결과 포함 (PASS/FAIL)
   Claude 보완 요청 사항 (있으면)

실패 시:
  → "[HANDOFF]  Codex 보고서 불완전 — done/ 이동 보류"
  → lock 파일 유지 (task 완료 처리 안 함)
```

### 3. Claude 보완 후 (Claude → Gemini)
```
검증 항목:
   검증 지시 파일 존재 (verify-*.md 또는 task-instruction.md 업데이트)
   handoff-log.md에 from:claude, to:gemini 기록
   검증 포인트 목록 명시

실패 시:
  → "[HANDOFF]  검증 지시 불완전 — Gemini에 넘기기 전에 보완"
```

### 4. Gemini 완료 후 (Gemini → Claude)
```
검증 항목:
   docs/review-result.md 존재
   합격/불합격/조건부합격 판정 포함
   이슈 발견 시 파일:줄번호 포함
   보안 점검 결과 포함

실패 시:
  → "[HANDOFF]  Gemini 리뷰 불완전 — 재실행 필요"
```

## 자동 handoff-log.md 관리

### 엔트리 추가 (자동)
```markdown
## [2026-04-12 11:00] Claude → Codex
- **Task**: task-instruction.md (login page 구현)
- **Context**: [프로젝트 스택], API는 /api/auth/login
- **Constraints**: 프로젝트 CLAUDE.md 규칙 준수
- **Expected**: src/pages/Login.vue, src/store/auth.js

## [2026-04-12 11:30] Codex → Claude
- **Result**: 구현 완료 (2 files, 180 lines)
- **Issues**: API 에러 핸들링 미구현
- **Request**: 에러 핸들링 + 로딩 상태 추가 요청

## [2026-04-12 11:45] Claude → Gemini
- **Task**: verify-login.md
- **Focus**: 기능 정상 동작, XSS 방어, API 에러 처리

## [2026-04-12 12:00] Gemini → Claude
- **Verdict**: 조건부 합격
- **Issues**: CSRF 토큰 미적용 (src/api/auth.js:15)
- **Fix**: axios interceptor에 CSRF 헤더 추가 필요
```

## 스크립트 연동

### codex-auto.bat에 hook 추가
```
Codex 완료 시 자동 검증:
  1. implementation-report.md 존재 확인
  2. 없으면 Claude -p 로 자동 생성 요청
  3. handoff-log.md에 Codex→Claude 엔트리 추가
```

### gemini-auto.bat에 hook 추가
```
Gemini 완료 시 자동 검증:
  1. review-result.md 존재 확인
  2. 합격/불합격 키워드 확인
  3. handoff-log.md에 Gemini→Claude 엔트리 추가
```

## Claude 자동 동작
```
Claude 세션에서 자동 체크:
  1. handoff-log.md 마지막 엔트리 확인
  2. Codex→Claude 엔트리 있으면 → 보완 작업 시작
  3. Gemini→Claude 엔트리 있으면 → 채택/수정 결정
  4. 미처리 handoff 있으면 세션 시작 시 알림
```
