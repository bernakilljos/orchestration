# _template — 상세 스펙

> status=spec-only 인 동안 이 파일이 실구현의 기준. 구현 완료되면 README.md로 내용 이동.

## 목표 (Goal)

- 구체적으로 달성하고자 하는 것 (정량)
- 성공 기준 (예: "30분 내 YouTube 영상 업로드 자동화 완료")

## 비목표 (Non-goal)

- 명시적으로 **하지 않을 것** (스코프 폭주 방지)

## 인터페이스

### 커맨드 시그니처

```
/cmd-1 <required_arg> [--option=default]
/cmd-2 <target> [--dry-run]
```

### 입출력

| 커맨드 | 입력 | 출력 | 부작용 |
|---|---|---|---|
| `/cmd-1` | 파일 경로 | stdout JSON | 없음 (read-only) |
| `/cmd-2` | URL + 플래그 | 파일 생성 | `data/template/<date>/` 저장 |

## 동작 규칙

1. **멱등성**: 재실행해도 안전. 동일 입력 → 동일 출력.
2. **드라이런**: `--dry-run` 옵션 필수 (실제 호출 전 시뮬레이션).
3. **에러 복구**: 중간 실패 시 state 파일로 재시작 지점 저장.
4. **Rate limit**: 외부 API 호출은 지수백오프 재시도 (최대 5회).

## 의존성 해결

- **upstream**: 이 플러그인이 동작하려면 먼저 필요한 것
- **downstream**: 이 플러그인을 참조하는 다른 플러그인

## 데이터 저장 경로

- 중간 결과: `data/<plugin>/<yyyy-mm-dd>/`
- 로그: `.claude/state/<plugin>/log.jsonl`
- 상태: `.claude/state/<plugin>/state.json`

## 관측·로깅

- 메트릭: `command_name, duration_ms, tokens_used, api_cost_usd`
- 로그 레벨: DEBUG/INFO/WARN/ERROR

## 보안·시크릿

- API 키는 `.env` 또는 환경변수만. 절대 커밋 금지.
- 민감 데이터 로깅 금지 (PII, 토큰, 키).

## 테스트 전략

- 단위: 각 커맨드 input/output
- 통합: 의존 플러그인과의 연결
- 스모크: 드라이런 모드로 매 배포 전 검증

## 미해결 질문

- [ ] TBD 항목 1
- [ ] TBD 항목 2
