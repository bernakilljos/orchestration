---
description: "/design_ppt 의 호환 alias — 동일 동작 (PPT 자동 생성)"
allowed-tools: Bash(python:*), Bash(playwright:*), Read, Write, Edit, Grep, Glob
---

# /make-ppt — `/design_ppt` 호환 alias

> **이 명령은 `/design_ppt` 와 동일하게 동작합니다.** 새 작업은 `/design_ppt` 사용 권장.

## 사용

```
/make-ppt "주제" 40
```
→ 내부적으로 `/design_ppt "주제" 40` 과 동일한 워크플로우 실행.

## 워크플로우 상세

전체 가이드: `commands/design_ppt.md`

핵심:
- HTML/CSS → Playwright → PPTX 파이프라인
- 잘림(overflow) 방지 10 계명
- OCR 검증 필수
- 페이지번호 일괄 갱신 (`update-ppt-page-numbers.py`)

함정 13개 체크리스트: `skills/skill-ppt-pitfalls.md`

## 왜 alias 인가

기존에 `/make-ppt` 를 사용한 사용자·문서·workflow 호환을 위해 유지.
신규 작업은 `/design_ppt` 사용 — 플러그인 이름과 명령 이름이 일치해 헷갈림 X.
