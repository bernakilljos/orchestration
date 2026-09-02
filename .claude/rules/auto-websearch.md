# WebSearch 자동 발동 룰 (Auto WebSearch)

> **근거**: 2026-09-02 사용자 지시 — "내가 요청하면 설렁설렁 해주지말고 web search를 기본으로 해서 해. 그것도 분명 있을텐데 발동을 안해".
> **이유**: 최신 기술·신기능·모델·라이브러리·가격·changelog·감사 규제 정보는 학습 컷오프 이후 변경. WebSearch 없이 답 = 오래된 정보 답변. 사용자 매번 재요청 = 시간 낭비.

## 절대 룰

**다음 트리거 감지 시 WebSearch 자동 발동 (사용자 명시 없어도).**

## 트리거 매트릭스

| 트리거 어휘 · 상황 | WebSearch 발동 |
|---|---|
| "최신"·"신기능"·"신기술"·"changelog"·"릴리스"·"릴리즈"·"업데이트" | ✅ |
| "얼마"·"가격"·"cost"·"응시료"·"수강료"·"학비" | ✅ |
| "언제 나와"·"출시"·"발표"·"공개" | ✅ |
| "요즘"·"트렌드"·"동향"·"화제"·"인기" | ✅ |
| "vs"·"비교"·"차이"·"어떤 게 좋아" (여러 제품·모델·기술) | ✅ |
| 모델명 (Claude Opus 5·GPT-5·Gemini 3.x·Llama 4 등) + "어때"·"어떻게"·"얼마" | ✅ |
| 라이브러리·프레임워크 이름 + "설치"·"쓰는 법"·"버전" | ✅ |
| 규제·법규·정책 (CISA·CFE·개보법·GDPR 등) + 세부 정보 | ✅ |
| MCP·플러그인 이름 검토 | ✅ |
| 특정 제품·회사·서비스 이름 조사 | ✅ |
| 사용자가 URL·링크 언급 (직접 확인 요청) | WebFetch |
| 코드베이스 내부만 관련 질문 (kit 자체 감사·수정) | ❌ (grep·Read) |
| 파일 경로·이름·구조 질문 | ❌ (Glob) |
| 논리 추론·설계 결정 | ❌ (자체 판단) |

## 발동 방법

1. **1차 감지** (UserPromptSubmit hook): 트리거 어휘 매치 → systemMessage 로 "WebSearch 권장" 힌트
2. **2차 실행** (Claude): 답변 시작 전 WebSearch tool 자동 호출
3. **결과 인용**: 답변에 출처 명시 (Anthropic docs · GitHub release notes 등)

## 최소 발동 횟수

- **모델·라이브러리 신규 정보 질문** → 최소 1회
- **비교 (vs)** → 각 항목당 1회 (2~3회)
- **가격·응시료·비용** → 공식 소스 1회 + 최신 후기 1회

## 발동 안 하는 경우 (금지 예외)

| 상황 | 이유 |
|---|---|
| Kit 내부 파일 감사 | grep·Read 로 충분 |
| 사용자가 이미 최신 정보 제공 | 중복 |
| Trivial 계산·논리 | 낭비 |
| 응답 속도가 극한 중요 (fast mode) | 사용자 명시 fast 우선 |

## 우리 kit 활용

- SessionStart hook: `changelog-check.sh` 는 이미 있음 (Anthropic changelog 자동 감지)
- 신설 hook: `.claude/hooks/websearch-trigger-detect.sh` (UserPromptSubmit) — 위 트리거 매치 시 systemMessage 주입
- Rule 참조: `feedback_official_features_auto_check.md` (⭐⭐ 이상 자율 반영) — WebSearch 로 최신 사양 확인 후 반영

## 금지

1. **최신 정보 요청 받고 학습 데이터로만 답** — 사용자가 "정확하게 알려줘" 반복 트리거
2. **WebSearch 결과 없이 "정확히는 모르겠다"** — 도구 있는데 안 씀 = 농땡이
3. **WebSearch 후 출처 명시 없이 답** — 신뢰도 낮음
4. **Trivial 질문에 매번 WebSearch** — quota 낭비

## 관련

- `.claude/rules/failure-mode.md` § 확신 없으면 거절 (WebSearch 로 확신 확보)
- `.claude/rules/best-practices.md` § Extended Thinking (WebSearch + 추론 병행)
- `feedback_official_features_auto_check.md` (⭐⭐ 이상 자동 반영)
- `.claude/hooks/changelog-check.sh` (기존 SessionStart)
- `.claude/hooks/websearch-trigger-detect.sh` (신설)
