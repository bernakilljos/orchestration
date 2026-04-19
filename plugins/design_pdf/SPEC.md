# design_pdf — 상세 스펙 (Phase 2)

## 목표

- PDF 생성·양식·서명·암호화 (mcp_docs 는 파싱만)

## 커맨드 스펙

### `/pdf-generate`

HTML·Markdown → PDF 변환

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

### `/pdf-fill`

양식(form) 자동 채우기

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

### `/pdf-sign`

전자서명·직인 삽입

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

### `/pdf-secure`

암호화·워터마크

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

## 스킬 스펙

### `skill-pdf-form`

PDF 양식 필드 매핑·검증

### `skill-pdf-compliance`

전자서명 법적 요건 (전자서명법)

## 구현 체크리스트 (플랫폼)

- [ ] 멱등성
- [ ] `--dry-run` 실동작
- [ ] 입력 검증
- [ ] 에러 복구
- [ ] Rate limit (지수백오프)
- [ ] 시크릿 `.env` 로드
- [ ] JSON 구조화 로그

## 의존성

- upstream: exec_orch
- 공통 헬퍼: `scripts/common.sh`

## 참조

- `docs/architecture-patterns.md`
- `.claude/rules/file-naming.md`

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 커맨드 인식 안 됨 | sync 미실행 | `bash .claude/scripts/sync-plugins.sh` |
| 환경변수 누락 | `.env` 미설정 | `.env.example` 복사 후 값 입력 |
| API 호출 실패 | 쿼터·네트워크·토큰 | `scripts/common.sh` 의 retry 로직 확인 |
| 한글 깨짐 | 인코딩 | `.claude/hooks/check-mojibake.sh` 가 차단. UTF-8 로 재저장 |
| 드라이런 실패 | 인자 미지원 | `is_dry_run "$@"` 헬퍼 검사 |

## 참조

- `.claude/rules/skill-design.md` (Anthropic 가이드 적용)
- `.claude/rules/plugin-structure.md`
