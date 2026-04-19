# design_video — 상세 스펙 (Phase 2)

## 목표

- 영상 편집 — 자막·쇼츠·썸네일 (유튜브 수익화 직결)

## 커맨드 스펙

### `/video-edit`

영상 편집 (자르기·합치기·자막)

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

### `/video-subtitle`

자막 자동 생성 (Whisper + 번역)

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

### `/video-template`

유튜브 인트로·아웃트로 템플릿

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

### `/video-shorts`

롱폼 → 쇼츠 자동 추출

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

### `/video-thumbnail`

썸네일 A/B 3안 자동 생성

**공통**: `--dry-run` 지원, 구조화 로그, `data/<plugin>/<date>/` 저장

## 스킬 스펙

### `skill-video-remotion`

Remotion 프로그래매틱 영상 (design_ppt 에서 이관)

### `skill-video-retention`

시청지속률 높이는 편집 패턴

## 구현 체크리스트 (플랫폼)

- [ ] 멱등성
- [ ] `--dry-run` 실동작
- [ ] 입력 검증
- [ ] 에러 복구
- [ ] Rate limit (지수백오프)
- [ ] 시크릿 `.env` 로드
- [ ] JSON 구조화 로그

## 의존성

- upstream: exec_orch, mcp_media
- 공통 헬퍼: `scripts/common.sh`

## 참조

- `docs/architecture-patterns.md`
- `.claude/rules/file-naming.md`
