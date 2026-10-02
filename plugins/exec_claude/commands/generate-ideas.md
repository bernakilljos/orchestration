---
description: "브레인스토밍 — 주제·제약 조건 받아 다양한 아이디어 N개 생성"
allowed-tools: Read, Write
---

## Context
- 주제: $ARGUMENTS
- 과거 세션 (관련 있으면): `.claude/context-cache/session-snapshot.md`

## Your task

사용자가 준 주제에 대해 **다양한 각도의 아이디어 N개**를 생성한다.

### 입력 받을 수 있는 인자
- `--count <N>` — 생성 개수 (기본 10)
- `--angles <industry|user|tech|business|contrarian|future|cost|time>` — 각도
- `--format <bullet|table|cards>` — 출력 형식
- `--wild` — 상식 벗어난 아이디어 포함 (ENFP 모드)

### 흐름

1. **주제 명확화** — 1줄 재해석 ("즉 X 에 대한 Y 를 원함")
2. **각도 분해** — 지정 각도 (기본 5~8 개) 로 축 설정
3. **생성** — 각 축당 N/axes 개 아이디어 (중복 X)
4. **품질 필터** — fabrication·현실성 체크 (완전 황당은 `--wild` 때만)
5. **출력** — 표 또는 카드 (각 아이디어: 제목·1줄 설명·강점·약점·즉시 실험 가능 여부)

### 다각화 체크리스트
-  저비용 vs 고비용
-  단기 vs 장기
-  기술 vs 비기술
-  B2B vs B2C
-  확장형 vs 전문형
-  주류 vs contrarian
-  정량 vs 정성

### 스타일 (사용자 ENFP-ADHD 반영)
- 긴 essay X · 각 아이디어 3줄 이내
- 비유 환영 (일상·게임·요리)
- "spark 되는 거 짚어주세요" 로 마무리
- 결정 강요 X (고르는 건 사용자)

### 금지
- 뻔한 아이디어만 (ChatGPT 처럼) — 각도 다변화
- 같은 범주 아이디어 반복
- 깊이 분석 (이건 /critique 가 할 일)
- 결론 강요 ("가장 좋은 건 X")

## 참조
- plugins/exec_claude/commands/claude-thinking.md (복잡 추론은 이쪽)
- feedback_user_enfp_adhd_style.md
- feedback_industry_ml_transfer_style.md (산업 이식 패턴)
- .claude/agents/brainstorming-partner.md (심층 세션은 agent 로)
