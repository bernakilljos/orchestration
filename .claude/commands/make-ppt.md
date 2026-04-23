---
description: "PPT 자동 생성 — Claude 설계 → python-pptx 구현 (로컬) + 선택 MCP 연동"
allowed-tools: Bash(python:*), Bash(npm:*)
---

## Context
- 설치된 생성 스크립트: !`ls -1 .claude/scripts/generate-*ppt*.py 2>/dev/null | head -3`
- Mermaid MCP: !`claude mcp list 2>/dev/null | grep -i mermaid && echo "OK" || echo "없음"`
- Figma MCP: !`claude mcp list 2>/dev/null | grep -i figma && echo "OK" || echo "없음"`

## 워크플로우

### Step 1 — Claude 설계 (자동)

주제 또는 기본값 사용:
- 입력: 슬라이드 주제 (예: "최신 기술 동향") 또는 비어있음 → 기본값 "Orchestration Kit"
- 출력: 슬라이드 목차 구조 (텍스트 또는 JSON)

### Step 2 — python-pptx 로 PPT 생성 (즉시 실행 가능)

```bash
# 기본 제공 v3/v4/v5 중 하나 실행:
python .claude/scripts/generate-premium-ppt-v5.py

# 결과: outputs/ppt/orchestration-v1-premium-2026-04-23-v5-cyberpunk.pptx
```

각 버전 특징:
- **v3 (Bloomberg)**: 데이터 밀도 높음, 차트·표 강조
- **v4 (Luxury)**: 우아함, 크림 배경, 골드 액센트
- **v5 (Cyberpunk)**: 다크 네온, 터미널 로그, 미래식

### Step 3 — Mermaid 다이어그램 (선택)

PPT 내 일부 슬라이드에 추가 다이어그램 필요 시:
```bash
# Mermaid MCP 설치 확인 후 호출
claude mcp list | grep mermaid
```

mermaid-mcp-server가 활성이면, 상세 다이어그램 추가 가능.

### Step 4 — Figma 디자인 동기화 (선택, PAT 토큰 필요)

Figma PAT 토큰 설정 후:
```bash
export FIGMA_TOKEN="your_token"
# 기존 Figma 파일 가져오기 → PPT 스타일 적용
```

### Step 5 — 최종 생성 및 검증

```bash
# 파일 확인
ls -lh outputs/ppt/*.pptx

# 슬라이드 수 확인 (매우 대략적)
unzip -l outputs/ppt/*.pptx | grep -c "slide"
```

결과:
| 항목 | 값 |
|------|-----|
| 생성 도구 | python-pptx (v3/v4/v5 선택) |
| 형식 | .pptx (PowerPoint 2010+) |
| 슬라이드 수 | 18~25장 (선택 버전마다 다름) |
| 저장 경로 | `outputs/ppt/` |
| 재생성 명령 | `python .claude/scripts/generate-premium-ppt-v{N}.py` |

## 제한사항

- **Gamma**: npm 패키지 없음 (claude.ai 웹 전용 → Python 코드로 대체)
- **Canva**: OAuth 필요 → 로그인 후 수동 연동 가능
- **Google Slides**: 공동편집 가능하지만 PPT 생성 후 수동 업로드 필요

## 추천

1. 빠른 PPT 생성 → **v5 (Cyberpunk)** 실행
2. 전문 디자인 필요 → v3/v4 중 선택 후 Figma 추가 디자인 고려
3. 클라우드 공유 필요 → 생성 후 Google Slides 로 변환
