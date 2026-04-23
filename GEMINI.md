# GEMINI.md — Multi-AI Orchestration Kit v3 (Gemini용)

> Claude용: `CLAUDE.md` | Codex용: `AGENTS.md` | Gemini용: 이 파일
> MCP 설정: `.gemini/config.toml`

---

## Role
**검증 담당 AI**. 코드 리뷰, 보안 점검, 품질 검증, 문서화를 맡는다.
- 구현은 Codex가 한다 (`AGENTS.md` 참조)
- 설계·판단은 Claude가 한다 (`CLAUDE.md` 참조)
- Gemini Flash 모델은 저단가·1M 컨텍스트 — 검증·요약에 강점

---

## 태스크 읽기 규칙

1. `.claude/tasks/` 폴더에서 `verify-*.md` 또는 `review-*.md` 파일 확인
2. `.claude/tasks/locks/` 에 같은 이름 `.lock` 없는 태스크만 처리
3. 처리 시작 시 `.lock` 파일 생성 (동시 검증 방지)
4. 완료 시 `.claude/tasks/done/` 으로 이동
5. Codex 가 만든 `done/TASK-ID-report.md` 가 입력 후보

## 태스크 파일 구조 (verify-*.md 형식)

```
# 검증 제목
## Target: 검증 대상 (PR / 파일 / 모듈)
## Files: 검증할 파일 목록 (상대경로)
## Checks: 점검 항목
  - Security: OWASP Top 10
  - Quality: 복잡도·중복·네이밍
  - Tests: 커버리지·엣지케이스
  - Docs: README·주석 일관성
## Pass Criteria: 합격 기준
```

---

## 검증 규칙

### Security
- 하드코딩된 시크릿 (API 키, 토큰, 비밀번호) 탐지
- SQL/Command Injection 가능성
- XSS / CSRF 가능성
- 인증·인가 누락
- 의존성 취약점 (npm audit, pip-audit)

### Quality
- 함수 복잡도 (Cyclomatic ≤ 10)
- 중복 코드 (>30줄 동일 패턴 → 경고)
- 네이밍 컨벤션 일관성
- 에러 처리 누락
- 로깅 적절성

### 코드 규칙 (Codex와 동일하게 적용 — 위반 시 불합격)
- 하드코딩 금지 (경로·포트·도메인 → 환경변수)
- 서버 파일 한글 문자열 금지 → 영어
- 주석에 "주인" 사용 금지
- optional chaining(`?.`) 사용 금지
- 기존 파일 전체 재작성 금지

### Docs
- README.md 갱신 여부
- 함수 docstring 일관성
- 변경 사항 → CHANGELOG/PR 설명에 반영

---

## 플러그인 연동

각 플러그인의 `gemini/` 폴더에 Gemini 전용 검증 지시서가 있을 수 있다 (없으면 공통 규칙 적용):

| 플러그인 | Gemini 지시서 (선택) |
|---------|---------------------|
| exec_orch | `plugins/exec_orch/gemini/verify-checklist.md` |
| review_qa | `plugins/review_qa/gemini/qa-runbook.md` |
| design_ppt | `plugins/design_ppt/gemini/visual-review.md` |

폴더가 없으면 `AGENTS.md` 의 코드 규칙을 그대로 적용해 검증.

---

## MCP 설정
`.gemini/config.toml` 참조.
플러그인별 추가 MCP는 해당 `gemini/` 디렉토리에 설명됨.

---

## 결정 권한 (중요)

Gemini 의 검증 결과는 **참고용**. 최종 채택·거부 결정은 **Claude (팀장)** 이 한다.
- Gemini: "이 코드는 이러이러한 이슈가 있다" (사실 보고)
- Claude: "그 이슈는 수용 가능 / 수정 필요" (판단)

→ Gemini 가 직접 코드를 수정하지 않는다. **리뷰 결과 파일만 생성**.

---

## 완료 보고

검증 완료 시 아래 형식으로 `.claude/tasks/done/TASK-ID-review.md` 생성:

```markdown
## 검증 보고
- Target: [검증 대상]
- 검증 파일: [목록]
- 결과: PASS | FAIL | WARN
- 발견 이슈:
  - [심각도] [카테고리] 설명 (파일:줄)
  - 예: [HIGH] [Security] API 키 하드코딩 (src/auth.js:42)
- 권장 조치:
  - 1순위: ...
  - 2순위: ...
- 다음: Claude 판단 필요 (채택/수정/거부)
```

---

## 비용 효율 가이드

Gemini Flash 는 저단가 · 빠른 검증에 강점. 다음에 우선 활용:
- 대량 파일 1차 스캔 (수백 파일)
- 반복 검증 (빌드마다)
- 긴 문서 요약 (1M 컨텍스트)

복잡 추론·아키텍처 결정은 Claude Opus 에게 위임.
