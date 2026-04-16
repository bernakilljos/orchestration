---
description: "God Mode — 최대 워커·직통 라우팅·검증 스킵·최대 출력"
allowed-tools: Bash(where:*), Bash(echo:*), Bash(powershell:*)
---

## Context
- codex-auto: !`where codex-auto 2>/dev/null && echo AVAILABLE || echo NO`
- gemini-auto: !`where gemini-auto 2>/dev/null && echo AVAILABLE || echo NO`
- 현재 워커 설정: !`type .claude\orca-workers-config.json 2>/dev/null || echo "default"`
- orca-stopped: !`if exist .claude\orca-stopped (echo STOPPED) else (echo OK)`

## Your task

**GOD MODE 활성화 — 연결 시스템:**

### 1. exec_orca-auto (워커 최대화)
`.claude/orca-workers-config.json` 의 워커 수를 최대로 올린다:
- codex: 현재값 → **10**
- gemini: 현재값 → **4**
- claude: 현재값 → **5**

orca-stopped 있으면 삭제 → orca-enabled 생성 → 워커 즉시 시작

### 2. route_dispatch (직통 라우팅)
`.claude/skills/route_dispatch.md` 의 판단 로직을 **CODEX_AVAILABLE 무관하게** 실행:
- 태스크 규모 판단 없이 → 즉시 구현 시작
- Gemini 검증 스킵 (사용자가 명시적으로 요청 시에만 실행)

### 3. 실행 규칙 (이 세션 동안 적용)
- 모호하면 최선의 판단으로 진행 후 보고
- "괜찮을까요?" "확인해드릴까요?" 금지
- 플레이스홀더·TODO 금지 — 완성된 코드만
- 여러 방법 있으면 최선 선택 후 실행
- 에러 나면 자동 수정 후 계속

### 4. 결과 보고
```
[GOD MODE] 활성화
  워커: codex=10, gemini=4, claude=5
  라우팅: 직통 (검증 스킵)
  요청: $ARGUMENTS
```

$ARGUMENTS 가 있으면 즉시 처리 시작.
