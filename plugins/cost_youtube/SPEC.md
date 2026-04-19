# cost_youtube — 상세 스펙 (Phase 1)

> **Status**: spec-only — 이 플러그인은 킷에 스펙만 있음. 실구현은 install 후 플랫폼에서.

## 목표

- YouTube 수익화 (Phase 1 축소판: research·upload·analytics 3개)

## 커맨드 스펙

### `/yt-research`

트렌드·키워드 리서치 (급상승·경쟁채널·검색량)

**시그니처 (예정)**:
```
/yt-research [args] [--flag]
```

### `/yt-upload`

YouTube Data API 업로드 (--dry-run 지원)

**시그니처 (예정)**:
```
/yt-upload [args] [--flag]
```

### `/yt-analytics`

수익·조회수·시청지속시간 리포트

**시그니처 (예정)**:
```
/yt-analytics [args] [--flag]
```

## 스킬 스펙

### `skill-yt-hook-writing`

첫 15초 훅 작성 (이탈률 최소화)

### `skill-yt-algorithm`

YouTube 알고리즘 (세션시간·외부트래픽·관련영상)

## 의존성

- **upstream (필수)**: exec_orch, mcp_social, exec_scheduler

## 구현 가이드라인 (install 후 플랫폼 참조용)

- [ ] 멱등성 보장
- [ ] `--dry-run` 옵션 지원
- [ ] Rate limit 대응 (지수백오프)
- [ ] 에러 복구 (state 파일 기반 재시작)
- [ ] 시크릿 관리 (환경변수·vault)
- [ ] 비용 관측 (토큰·API 호출 로깅)

## 참조

- 로드맵: `docs/2026-04-19/로드맵.md`
- 의존 플러그인: plugins/exec_orch, plugins/mcp_social, plugins/exec_scheduler
