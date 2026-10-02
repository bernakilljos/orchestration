# 수정 후 증명 체인 강제 룰 (Verify-After-Edit)

> **근거**: 2026-10-02 사용자 지적 — "A 수정해줘 → 보고 → 사용자 확인 → 안 되어 있음 → 왜 안 됐는지 증명하고 수정해 재지시 반복".
> **이유**: `Edit` 성공 ≠ 실제 작동. 파일 변경 됐어도 캐시·cascade·재시작·엉뚱한 파일 때문에 효과 X. 사용자가 매번 재검증 지시 = 시스템 결함.

## 절대 룰

**사용자 "A 수정해줘" 지시 받으면 수정 → 즉시 증명 → 보고 3단계 체인 강제.** 수정만 하고 보고 X.

## 증명 체인 (5단계)

| # | 단계 | 도구 | 생략 조건 |
|---|---|---|---|
| 1 | **pre-snapshot** | 수정 전 상태 캡처 (md5·cat·sqlite SELECT·curl 등) | 없음 (필수) |
| 2 | **수정 실행** | Edit·Write·Bash | 없음 (필수) |
| 3 | **post-snapshot** | 수정 후 상태 재캡처 | 없음 (필수) |
| 4 | **diff + 작동 테스트** | diff·re-read·실행·API 호출·UI 캡처 | 설정 파일 (실행 불가) 면 Read 재확인만 |
| 5 | **보고 (증거 첨부)** | diff 요약 + 작동 결과 | 없음 (필수) |

## 영역별 증명 매트릭스

| 수정 대상 | pre | post | 작동 테스트 |
|---|---|---|---|
| settings.json·CLAUDE.md 등 설정 | `md5` + Read | md5 + Read | 설정 적용되는 다음 세션에서만 확인 가능 → 명시 보고 |
| Python·JS 코드 | Read line | Read line | `python -X utf8 script.py` 또는 `node script.js` 실행 |
| Shell script (.sh) | Read | Read | `bash -n script.sh` syntax + `bash script.sh` 실행 |
| DB (sqlite) | `SELECT COUNT`·row | SELECT 재실행 | 변경량 == 보고량 |
| API endpoint | `curl` 전 | curl 후 | HTTP status + response body 일치 |
| UI (프론트) | 스크린샷 전 | 스크린샷 후 (Playwright) | 변경 요소 가시 확인 |
| Hook 등록 | `.claude/settings.json` grep | 재grep | 다음 세션 발동 확인 (명시 보고) |
| Rule 추가 | 파일 존재 X | 존재 O | 참조 룰 수 재확인 |

## "왜 안 됐어" 트리거 (사용자 재지시 감지 시 자가 진단)

사용자가 **"왜 안 됐어"·"수정했다며 안 됨"·"적용 안 됨"·"효과 X"** 재지시 시:

### 자가 진단 5단계

1. **파일 확인**: 수정한 파일 Read 재확인 (실제 new_string 있는지)
2. **cascade 확인**: 같은 설정이 다른 곳에서 override 되는지 (글로벌 vs 프로젝트 등)
3. **캐시 확인**: 재시작·cache invalidate 필요한지 (restart·clear cache)
4. **다른 파일 확인**: 엉뚱한 파일 수정했는지 (경로 확인)
5. **실행 테스트**: 실제 작동 재확인 (실행·curl·UI)

### 보고 포맷
```text
[자가 진단]
① 파일: /path/to/file — new_string {있음|없음}
② cascade: {글로벌 override|프로젝트 override|none}
③ 캐시: {재시작 필요|clear cache 필요|무관}
④ 다른 파일: {엉뚱한 경로 수정|정확}
⑤ 실행: {작동 OK|FAIL — <reason>}

[원인]: <한 줄>
[수정]: <코드 변경 요약>
[재검증]: <실행 결과>
```

## 금지

1. 수정 후 "완료" 만 보고 (증명 체인 skip)
2. post-snapshot 안 찍고 보고
3. 작동 테스트 없이 "성공" 단정
4. 사용자가 "안 됐어" 지적한 후에야 증명 (전수조사 위반)
5. cascade·캐시·엉뚱한 파일 가능성 안 짚고 "이상하다"
6. 설정 파일 수정 후 "다음 세션 반영" 명시 X

## 관련

- `.claude/rules/best-practices.md § 검증 후 보고` (기존)
- `.claude/rules/no-false-report.md` (기존 — 거짓 PASS 차단)
- `.claude/rules/screen-verify.md` (화면 검증)
- `.claude/rules/post-codex-verify.md` (외부 AI 결과 검증 패턴 재사용)
- `.claude/rules/user-emotion.md` ("왜 안 됐어" 트리거 매핑)
- memory: [[feedback_verify_before_report]]
