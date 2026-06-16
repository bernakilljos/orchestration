# 기준 일관성 룰 (Standards Drift Prevention)

> **근거**: 2026-06-16 사용자 지적 — "개발이랑 기준자체가 개발할대마다 흔들리면 안돼".
> **이유**: 매 turn 마다 적용 잣대 (자율/승인·코드 스타일·라우팅·검증·보고 형식) 바뀌면 사용자가 시스템 신뢰 못 함. 룰 추가만 늘고 적용은 isnpired-of-the-moment = drift.

## 절대 룰

**같은 카테고리 작업은 매번 같은 기준 적용. "이번엔 예외" 자기 판단 금지.** 기준 변경 시 명시 사유 + 룰 파일 갱신 + commit message 에 기록.

## 적용 영역 (drift 점검 카테고리)

| 카테고리 | 기준 (SoT) | drift 예시 |
|---|---|---|
| **들여쓰기·코드 스타일** | `.claude/rules/indentation.md` | 어제 4 스페이스, 오늘 2 스페이스 |
| **파일 명명** | `.claude/rules/file-naming.md` | kebab-case → snake_case 임의 변경 |
| **자율 vs 승인** | `feedback_approve_before_apply.md` + `feedback_official_features_auto_check.md` | 자율 영역인데 갑자기 승인 요청, 승인 영역인데 자율 진행 |
| **라우팅 정책** | CLAUDE.md § 3.2 + `route_dispatch.md` | 같은 특성 task 인데 모델 임의 선택 |
| **검증 의무** | `feedback_verify_before_report.md` + `screen-verify.md` + `no-false-report.md` | 어떤 작업은 검증, 어떤 작업은 skip |
| **산출물 명명** | `feedback_no_version_suffix.md` | -v2/-v3 임의 추가 |
| **5단계 plan** | `auto-planner.md` (전수조사·분석·실행·확인·보고) | 작업마다 단계 누락 다름 |
| **보고 형식** | `brief.md` / `auto-planner.md` 출력 형식 | turn 마다 다른 표·다른 길이 |
| **commit message 형식** | `feat/fix/refactor/docs/chore` 접두사 + Co-Authored-By | 어떤 commit 은 접두사 빠짐 |
| **MCP 설치 규칙** | `.claude/rules/mcp-install-rules.md` | npm view 검증 skip |

## drift 발생 패턴 (안티)

| 패턴 | 위반 |
|---|---|
| "이번 task 만 예외" 자기 판단 | drift |
| 룰 추가 후 다음 turn 적용 안 함 | drift |
| 사용자 룰 깜빡 — 매번 다르게 적용 | drift |
| 룰 충돌 시 그때그때 한 쪽 선택 | drift |
| commit/PR 마다 다른 형식 | drift |
| "더 좋은 방법 찾아서 바꿈" 사용자 보고 없이 | drift |

## 룰 변경 절차 (drift X)

```text
1. 사유 명시: 어떤 결함·신기능·외부 변화로 룰 변경 필요
2. SoT 파일 갱신 (.claude/rules/<file>.md 또는 CLAUDE.md § 7)
3. memory 갱신 (feedback_*.md or reference_*.md)
4. CHANGELOG/commit message 에 "RULE CHANGE: <before> → <after> (사유)"
5. 다음 turn 부터 모든 작업 새 기준 적용 (예외 X)
```

## 자가 점검 (auto-planner Step 1 에 통합)

작업 시작 전:
- [ ] 적용 룰 명시 (지난 turn 과 같은가?)
- [ ] 들여쓰기·명명·라우팅·검증·보고 모두 SoT 따름?
- [ ] 이번 turn 에 룰 변경 의도 있나? Yes → 절차 따름

## 5중 박기 (잊지 못하도록)

1. 이 파일 (`.claude/rules/consistency.md`)
2. CLAUDE.md § 7-26 (금지)
3. memory `feedback_no_standard_drift.md` (repo 외부)
4. `auto-planner.md` Step 1 자가 점검 항목
5. `plugins/exec_orch/hooks/hook-00-init.sh` 매 세션 출력

## 참조

- `.claude/rules/best-practices.md` § 검증 후 보고
- `.claude/rules/failure-mode.md` § 회피·confidence
- `feedback_approve_before_apply.md` (자율 vs 승인)
- `feedback_official_features_auto_check.md` (예외: ⭐⭐ 자율 적용 영역)
