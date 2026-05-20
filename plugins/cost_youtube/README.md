# cost_youtube — YouTube 수익화 (Phase 1 축소판: research·upload·analytics 3개)

> **Status**: spec-only (Phase 1) | **Prefix**: `cost_` | **버전**: 0.1

## ⚠️ 현재 상태

이 플러그인은 **스펙만** 있고 실구현은 없습니다. `install 후 플랫폼`에서 구현.
상세 스펙: [`SPEC.md`](SPEC.md)

## 📋 커맨드 (예정)

- `/yt-research` — 트렌드·키워드 리서치 (급상승·경쟁채널·검색량)
- `/yt-upload` — YouTube Data API 업로드 (--dry-run 지원)
- `/yt-analytics` — 수익·조회수·시청지속시간 리포트

## 🔗 의존성

- **플러그인**: exec_orch, mcp_social, exec_scheduler

## 상세 스펙

### 목표

- YouTube 수익화 (Phase 1 축소판: research·upload·analytics 3개)

### 스킬 스펙

#### `skill-yt-hook-writing`

첫 15초 훅 작성 (이탈률 최소화)

#### `skill-yt-algorithm`

YouTube 알고리즘 (세션시간·외부트래픽·관련영상)

### 구현 가이드라인 (install 후 플랫폼 참조용)

- [ ] 멱등성 보장
- [ ] `--dry-run` 옵션 지원
- [ ] Rate limit 대응 (지수백오프)
- [ ] 에러 복구 (state 파일 기반 재시작)
- [ ] 시크릿 관리 (환경변수·vault)
- [ ] 비용 관측 (토큰·API 호출 로깅)

### 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 커맨드 인식 안 됨 | sync 미실행 | `bash .claude/scripts/sync-plugins.sh` |
| 환경변수 누락 | `.env` 미설정 | `.env.example` 복사 후 값 입력 |
| API 호출 실패 | 쿼터·네트워크·토큰 | `scripts/common.sh` 의 retry 로직 확인 |
| 한글 깨짐 | 인코딩 | `.claude/hooks/check-mojibake.sh` 가 차단. UTF-8 로 재저장 |
| 드라이런 실패 | 인자 미지원 | `is_dry_run "$@"` 헬퍼 검사 |

## 📝 로드맵

- `docs/2026-04-19/로드맵.md` § Phase 1
- `.claude/rules/skill-design.md` (Anthropic 가이드 적용)
- `.claude/rules/plugin-structure.md`
