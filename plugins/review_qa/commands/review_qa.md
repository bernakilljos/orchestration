---
description: "코드 리뷰·보안·품질·테스트 검증"
---

# /review_qa — 리뷰·품질 허브

## 포함 커맨드
- `/check` — 종합 품질 체크 (**기본 액션**)
- `/security` — 보안 취약점 스캔
- `/performance` — 성능 분석
- `/screenshot` — UI 스크린샷 기반 검증
- `/validate` — 요구사항 대비 검증

## 기본 실행
`/check` — 린트·타입·테스트 일괄 실행.
보안 집중이면 `/security`, UI 회귀면 `/screenshot`.
