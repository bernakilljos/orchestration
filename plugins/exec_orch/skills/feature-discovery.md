---
name: feature-discovery
description: 사용자가 모르는·미사용 kit 기능 proactive 발굴·제시. 매 세션 시작 시 미사용 3-5개 자동 브리핑. 사용자 도메인 (ISMS-P·RMS·ITCEN ESG) 매칭 · 관심 태그 우선. 사용 이력 기반 반복 제안 방지.
---

# Feature Discovery — 사용자 모르는 기능 자동 발굴

Kit 은 200+ commands · 250+ skills · 32 plugins 보유. 사용자가 매번 모든 것 기억 X → 자동 브리핑 필요.

## 발동 시점

1. **SessionStart** — `.claude/hooks/brief-unused-features.sh` 매일 1회 (`.claude/state/last-brief.timestamp` 로 중복 방지)
2. **UserPromptSubmit** — `detect-efficiency.sh` 지시 매칭 시 20 카테고리 command 제안
3. **사용자 명시 요청** — "뭐 있어?"·"기능 알려줘"·"내가 모르는거" → 즉시 카탈로그 참조

## 발굴 로직

```text
1. 사용 이력 로드 (.claude/state/feature-usage.log)
2. 카탈로그 (outputs/install/kit-catalog.md) 순회
3. 미사용 command·skill 필터
4. 사용자 도메인 (memory reference_company_context) 매칭 우선순위
5. 최근 로드맵 (docs/2026-04-19/로드맵.md) 신규 우선순위
6. 3-5개 선정 → systemMessage
```

## 도메인 매칭

| 사용자 도메인 | 매칭 command·skill |
|---|---|
| **ISMS-P (보안·감사)** | `/security` · `/sec-scan` · `/analyze-improve` · `/pdf-sign` · `/pdf-secure` |
| **RMS (리스크)** | `/analyze-improve` (Zero Trust·XAI) · `/rag-graph` · `/exec_offline-observe` |
| **ITCEN ESG (지속가능성)** | `/design_ppt` · `/design_word` · `/pdf-generate` · `/arch-mindmap` |
| **개발팀 리더** | `/godmode` · `/exec_orch` · `/review_qa` · `/vibe-loop` · `/graph-run` |
| **콘텐츠 (유튜브·인스타)** | `/yt-upload` · `/ig-upload` · `/video-shorts` · `/music_studio-*` |
| **회의·문서** | `/meeting` · `/transcribe` · `/design_word` · `/pdf-fill` |
| **원격·모바일** | `/exec_remote-*` · `/exec_remote-mobile` (Termius·Blink Shell) |

## 사용 이력 트래킹

`.claude/state/feature-usage.log`:
```text
/design_ppt 2026-08-12
/exec_remote-setup 2026-08-05
/rag-agentic 2026-07-30
...
```

30일 이내 사용 = "익숙" · 브리핑에서 제외.

## 반복 제안 방지

- **일 1회** — `last-brief.timestamp` 로 중복 방지
- **미사용 우선** — 이미 쓴 것 skip
- **랜덤 순환** — 매일 다른 3-5개

## 사용자가 관심 표현 시

사용자가 "그거 어떻게 써?"·"자세히"·"예시" 등 관심 표현 감지 → 해당 command 상세 안내:
1. 사용법 (인자·옵션)
2. 예시 3개
3. 관련 command·skill
4. 도메인 활용 case

## Web (claude.ai) 에서도

session-bootstrap-prompt.md § 10~11 에 카탈로그 링크 + 효율화 원칙 포함 → Web 이 사용자 지시 시 자동 매칭.

## 금지

1. 사용 이력 없이 상위 3개만 반복 (지루)
2. 사용자 도메인 무시 (연관 없는 command 브리핑)
3. 브리핑 후 사용자 관심 표현 무시
4. 카탈로그 없는 command 제시 (hallucination)

## 관련

- `.claude/hooks/brief-unused-features.sh` (SessionStart)
- `.claude/hooks/detect-efficiency.sh` (UserPromptSubmit)
- `outputs/install/kit-catalog.md` (SoT)
- `feedback_daily_toolkit_gap_check.md`
- `reference_company_context.md`
