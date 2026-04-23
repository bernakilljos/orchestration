---
description: "구조화된 질문 폼 생성 — 자유텍스트 대신 선택지·라벨로 사용자 입력 수집"
allowed-tools: Write
---

## Context
- 주제: `$ARGUMENTS`
- 출력 디렉토리: `outputs/asks/`

## Your task

`skill-claude-ask` 활성화 후, 주어진 주제에 대해 사용자에게 물을 질문을 **구조화된 폼**으로 설계한다.

### 왜 이게 필요한가
- 자유텍스트 질문 → 사용자가 길게 쓰거나·놓치거나·모호하게 답변
- 구조화 폼 → 선택지/라벨/예시로 빠르고 정확

### Step 1 — 질문 항목 추출

`$ARGUMENTS` 의 주제에서 결정해야 할 항목 3~7개 식별:

```json
{
  "topic": "<주제>",
  "fields": [
    {
      "id": "scope",
      "label": "범위는?",
      "type": "single_choice",
      "options": ["전체", "일부", "신규"],
      "default": "일부",
      "required": true
    },
    {
      "id": "deadline",
      "label": "데드라인 (YYYY-MM-DD)",
      "type": "date",
      "required": false
    },
    {
      "id": "notes",
      "label": "추가 메모",
      "type": "text",
      "max_length": 200
    }
  ]
}
```

### Step 2 — 폼 출력 (대화창 표시)

JSON 을 사용자가 답하기 쉬운 마크다운 표로 변환:

```
📋 <주제>

1. 범위는? [필수]
   ( ) 전체   (•) 일부   ( ) 신규     ← 기본: 일부
   답:

2. 데드라인 (YYYY-MM-DD) [선택]
   답:

3. 추가 메모 [선택, 200자 이하]
   답:

→ 답변을 한 줄씩 적어주세요. 또는 "기본값으로" 라고 답하면 default 사용.
```

### Step 3 — 답변 수집 + 저장

사용자가 답하면:
1. 검증 (required 채워짐? max_length 초과 안 함?)
2. 저장: `outputs/asks/<slug(topic)>-<YYYY-MM-DD-HHmm>.json`
3. 결과 보고:
```
✅ 입력 수집 완료
- 저장: outputs/asks/<file>.json
- 다음 단계: <answers 기반 후속 행동 제안>
```

### Step 4 — 다음 행동 제안

수집된 답을 바탕으로 적절한 후속 커맨드 제안:
- "구현해" → `task-instruction.md` 작성 → `codex-auto` 위임
- "분석해" → 직접 답변
- "그림으로" → `/arch-auto` 호출

## 안티패턴
- ❌ 7개 초과 질문 (피로) → 그룹화하거나 2단계로 나눔
- ❌ 자유텍스트만 (구조화 의미 없음)
- ❌ default 없이 모든 항목 필수 (이탈 ↑)
