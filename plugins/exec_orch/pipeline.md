# exec_orch 파이프라인 — Hook → Planner → Executor → Validator → State → Retry

## 표준 실행 순서

```
1. Hook       사전 확인
2. Planner    구조 설계
3. Executor   구현 실행
4. Validator  검증
5. State      상태 저장
6. Retry      실패 처리
```

---

## 1. Hook (사전 확인)

파일: `hooks/hook-01-pre-task.md`

```
실행 항목:
  ✅ .claude/tasks/task-instruction.md 존재 여부
  ✅ 대상 파일 잠금 확인 (.claude/tasks/locks/)
  ✅ 동시 수정 충돌 방지 (Writer=1 규칙)
  ✅ MCP 필요 여부 확인
  ✅ orca-workers-config.json 워커 수 확인

실패 시: 작업 중단 + 원인 보고
```

---

## 2. Planner (구조 설계) — Claude 담당

```
실행 항목:
  - 요청 분석 및 설계
  - task-instruction.md 작성
    → Goal, Files, Rules, Steps, Expected Output
  - 태스크 규모 판단 (LARGE/SMALL/VERIFY)
  - route_dispatch 호출 → AI 자동 배분

출력: .claude/tasks/task-instruction.md
```

---

## 3. Executor (구현) — Codex 담당

```
실행 항목:
  - task-instruction.md 읽기
  - .lock 파일 생성
  - Files 섹션 파일만 수정
  - Rules 준수
  - 완료 보고서 작성

실행 방법:
  ▸ 글로벌 (기본, 여러 프로젝트 공유):
      orca-dispatch .claude/tasks/task-instruction.md codex
      codex-auto-global                    ← 전역 상한까지 spawn
  ▸ 로컬 (단일 프로젝트만 작업할 때):
      codex-auto 4                          ← 4개 병렬 워커

완료:
  ▸ 글로벌: ~/.claude/orca/done/ 로 이동
  ▸ 로컬:   .claude/tasks/done/ 로 이동
```

---

## 4. Validator (검증) — Gemini + review_qa 담당

```
실행 순서:
  4-1. 테스트 자동 실행 (/validate)
       → npm test / pytest / mvn test
       → 결과: docs/YYYY-MM-DD/validation/test-result.txt

  4-2. 스크린샷 캡처 (/screenshot)
       → Playwright MCP로 로컬 서버 캡처
       → 결과: docs/YYYY-MM-DD/validation/screenshots/*.png
       → Playwright 없으면 PowerShell 화면 캡처

  4-3. 보안 검사 (/security)
       → npm audit / pip-audit
       → 시크릿 노출 패턴 검색
       → 결과: docs/YYYY-MM-DD/validation/security-report.md

  4-4. 성능 검사 (/performance)
       → 응답시간 10회 측정
       → 번들 크기 확인
       → 결과: docs/YYYY-MM-DD/validation/performance-report.md

  4-5. Gemini 코드 리뷰
       → 구현 결과 vs task-instruction.md 비교
       → OWASP 기준 취약점 검토
       → 코드 품질·가독성·유지보수성

실행 방법:
  ▸ 글로벌: orca-dispatch <task> gemini && gemini-auto-global
  ▸ 로컬:   gemini-auto 2   ← 2개 워커

출력 형식:
  MUST:     [반드시 적용]
  SHOULD:   [권장]
  COULD:    [선택]
  SECURITY: [보안 이슈]

→ Claude가 채택 여부 결정 (자동 적용 금지)
```

---

## 5. State (상태 저장) — 자동

```
저장 시점:
  - 파이프라인 단계 완료마다
  - 컨텍스트 80% 도달 시
  - 사용자 요청 시

저장 위치:
  .claude/context-cache/session-snapshot.md

저장 내용:
  - 현재 태스크·목표·상태
  - 완료된 단계 체크리스트
  - 다음 실행 명령
  - 수정된 파일 목록
  - 주요 결정 사항

학습 저장 (/learn):
  .claude/learning/failure-patterns.json
  .claude/learning/optimization-rules.json
```

---

## 6. Retry (실패 처리)

```
재시도 조건:
  - Codex 실행 실패
  - Gemini 검증 MUST 항목 존재
  - 테스트 실패

재시도 규칙:
  - 최대 3회
  - 매 재시도마다 .claude/state/retry-count.json 업데이트
  - 3회 실패 시 → Claude 직접 처리로 에스컬레이션
  - 에스컬레이션 내용 failure-patterns.json 저장

재시도 방법:
  codex-auto 4   ← 동일 태스크 재실행
```

---

## 빠른 참조

| 단계 | 담당 | 파일 |
|------|------|------|
| Hook | 자동 | `hooks/hook-01-pre-task.md` |
| Planner | Claude | `skills/route_dispatch.md` |
| Executor | Codex | `codex-auto.bat` (4개) |
| Validator | Gemini | `commands/gemini-verify.md` |
| State | 자동 | `skills/state_session.md` |
| Retry | 자동→Claude | `.claude/state/retry-count.json` |
