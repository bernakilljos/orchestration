# 화면·기능 검증 룰 (Smoke Test 의무)

> **근거**: CLAUDE.md § 7-24. 사용자 지적 (2026-06-10): "화면 검증·기능 검증은 너가 해, 난 최종만 할 거야".
> **이유**: NPE (NULL 컬럼 + null-unsafe Java) 같은 기본 에러는 smoke test 한 번이면 잡힘. AI 가 "다음부터는 검증할게요" 라고만 약속하고 또 같은 패턴 반복 = 농땡이.

## 절대 룰

**DB / API / 프론트 변경 후 사용자에게 "확인해 주세요" 금지.** 자동 smoke test → PASS 후 보고.

## 검증 매트릭스

| 변경 종류 | 자동 검증 | 도구 |
|---|---|---|
| **DB schema** (CREATE/ALTER/DROP TABLE) | 영향 endpoint grep → 각 endpoint curl → 응답 status·null·schema 검사 | `smoke-test-screen.sh --db <sql>` |
| **API controller** (.java/.py/.rb/.go 컨트롤러) | 해당 endpoint curl (세션 포함) → 응답 status·body·null 검사 | `smoke-test-screen.sh --api <file>` |
| **프론트** (.html/.jsx/.tsx/.vue) | Playwright headless 로드 → 페이지 렌더 + console.error 잡기 + DOM 핵심 selector 점검 | `smoke-test-screen.sh --ui <url>` |
| **마이그레이션 스크립트** | dry-run + rollback 가능 여부 점검 | DB tool dependent |

## NPE 패턴 자동 검출 (NULL 컬럼 + null-unsafe)

DB 컬럼이 NULL 가능 + Java/JS/Python 코드가 null check 안 함 = NPE 시한폭탄.

검출 패턴:
```bash
# 1. NULL 가능 컬럼 추출
grep -rE "ADD COLUMN \w+|NULL DEFAULT NULL" *.sql

# 2. 해당 컬럼 참조하는 코드 찾기
grep -rE "rs\.getString|getColumn|columns\['\w+'\]" src/

# 3. 매치되는 곳에 null check 있는지
# - Java: != null / Optional.ofNullable
# - Python: is None / .get(key, default)
# - JS: ?. / != null
```

매치 없음 + null check 없음 = WARN.

## 호출 흐름 (자동)

```bash
# PostToolUse hook (.claude/settings.json 등록됨)
# Edit/Write 가 .sql/.java/.py/.html/.tsx 파일 변경 시:
bash .claude/scripts/smoke-test-screen.sh <changed_file>

# 내부:
# 1. 파일 확장자 분류
# 2. .sql → schema 추출 → 영향 endpoint 식별 → curl
# 3. controller → endpoint 찾기 → curl + jq null check
# 4. 프론트 → Playwright → console error grep
# 5. PASS/FAIL 로그 + 사용자 보고
```

## "다음부터는" 약속 금지 (안티 패턴)

사용자가 NPE 발견 → AI: "다음부터는 smoke test 하겠습니다" = **농땡이 반복**.

올바른 행동:
1. 사용자 발견 즉시 → smoke test 룰 시스템에 박기 (이 문서 + skill + hook)
2. 같은 패턴 재발 = rule + hook 강화
3. 약속만 X, 코드/룰/hook 으로 강제

## 사용자 vs AI 역할 (명확화)

| 단계 | AI | 사용자 |
|---|---|---|
| 코드 수정 | ✅ | — |
| 기능 검증 (curl·smoke) | ✅ | — |
| 화면 검증 (Playwright render) | ✅ | — |
| 에러 발견 시 자동 재수정 | ✅ (max 3) | — |
| **최종 시각 확인** | — | ✅ |
| 비즈니스 로직 결정 | — | ✅ |

AI 가 사용자에게 "기능 검증해 주세요" 요청 = 룰 위반.

## 금지

1. **"확인해 주세요" 떠넘김** — AI 가 직접 curl·render·log 점검
2. **"다음부터는" 약속만** — 코드/룰/hook 으로 시스템화
3. **smoke test 결과 PASS 무시** — FAIL 이면 자동 재시도 (max 3회)
4. **null check 없는 코드 PASS** — NPE 패턴 grep 으로 사전 차단
5. **endpoint 영향 분석 skip** — DB 변경 시 모든 endpoint 추적

## 도구

- 스크립트: `.claude/scripts/smoke-test-screen.sh`
- skill: `plugins/exec_orch/skills/skill-smoke-test.md`
- hook: `.claude/settings.json` PostToolUse Edit/Write
- 로그: `.claude/logs/smoke-test.log`

## 참조

- `CLAUDE.md § 7-24` (절대 룰)
- `CLAUDE.md § 7-21` (수정·빌드 후 자동 검증) — 디자인 산출물 검증과 정합
- `.claude/rules/best-practices.md` § 검증 후 보고
- `.claude/rules/failure-mode.md` § 회피 안티패턴
- 메모리: `feedback_screen_verify_required.md`
