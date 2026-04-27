---
description: "PPT·디자인 생성 허브 — Claude→HTML→Playwright→PPTX (잘림 방지 + OCR 검증 워크플로우)"
---

# /design_ppt — PPT 생성 허브

> **2026-04-27 업데이트**: 27→40장 작업 학습으로 잘림 방지·OCR 검증·페이지번호 자동화 강화.

## 포함 커맨드

- `/make-ppt` — PPT 파일 생성 (**기본 액션**) ⭐
- `/ai-system-stages` — AI 시스템 6단계 PPT (Prompt→Agent→…→Platform)
- `/arch-auto` — 아키텍처 다이어그램 (자동 형식 판단)
- `/arch-mindmap` — 마인드맵 다이어그램
- `/ppt-install` — Playwright + python-pptx 의존성 설치
- `/install-mcp` — Canva·Figma·Gamma MCP 연결

## 자동 활성 스킬

- `skill-ppt-pitfalls` ⭐ — 13가지 함정 체크리스트 (잘림·정렬·페이지번호·OCR)
- `skill-08-design` — Canva·DALL-E·Figma 자산 생성
- `skill-14-auto-detail` — 짧은 요청 자동 확장
- `skill-15-theme-factory` — 테마 자동 생성

## 기본 실행

`/make-ppt` — 주제 + 분량 지정해 슬라이드 자동 생성.
- 특수 템플릿 원하면 `/ai-system-stages`
- 다이어그램만 원하면 `/arch-auto`

## 핵심 워크플로우 (5단계 + 검증 루프)

```
[1] 구조 설계 → [2] HTML 작성 → [3] 렌더링 → [4] OCR 검증 → [5] 수정·재렌더
                                                         ↓ (잘림 0건)
                                                    [완료] git commit
```

### 잘림 방지 — 절대 룰 3가지
1. `.slide-NN { height: 1080px; overflow: hidden }`
2. flex/grid 자식에 `min-height: 0`
3. 코드 박스는 `flex: 0 0 auto` (절대 `flex: 1` X)

### OCR 검증 — 위임하지 마라
사용자가 OCR 캡처 보내면 **그것이 진실**. Sub-Agent "27/27 PASS" 보고 신뢰 X.
메인 Claude 가 Read tool 로 PNG 직접 본다.

### 새 슬라이드 추가 시
```bash
# 1. HTML 작성 (알파벳 정렬 위치)
vim outputs/ppt/html-source/slides/slide-NNa.html

# 2. 페이지번호 일괄 갱신
python .claude/scripts/update-ppt-page-numbers.py

# 3. 재렌더
python .claude/scripts/generate-final-ppt.py
```

## 출력 위치

- HTML 소스: `outputs/ppt/html-source/slides/`
- PNG 결과: `outputs/ppt/html-source/png-output/`
- 최종 PPTX: `outputs/ppt/orchestration-v1-FINAL.pptx`

## 자세히

- 워크플로우 상세: `commands/make-ppt.md`
- 함정 13개: `skills/skill-ppt-pitfalls.md`
- 디자인 시스템 5색: `outputs/ppt/html-source/styles/design-system.css`
