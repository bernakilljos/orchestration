---
name: auto-planner
description: 사용자가 한 줄 요청 (예 "문서 만들어줘", "버그 고쳐줘", "이미지 짤려") 받으면 자동 활성화. 5단계 plan (전수조사·분석·실행·확인·보고) 생성 + rule 위반 자가점검 + 막히면 codex/gemini 위임. Generative→Agentic 약점 보완 의 핵심 skill.
---

# Auto Planner — 자율 5단계 계획 skill

사용자 요청을 받자마자 자동 활성화. Claude 가 매번 사용자 지시 기다리지 않고 끝까지 진행하도록.

## 적용 시점 (자동 활성)

다음 패턴의 사용자 메시지 받으면 즉시 활성:
- "X 해줘", "X 만들어줘", "X 고쳐줘"
- "이미지 짤려", "여백 큰데", "글씨 안 보여" 같은 결함 지적
- "전수조사 해", "정리해" 같은 작업 명령
- 신규 기능·산출물·rule 요청

## 5단계 자율 plan (사용자 노동 0)

### Step 1. 전수조사 (Inventory)
- 작업 범위 파악 — 어느 파일·디렉토리·시스템 영향?
- 관련 기존 코드·rule·memory feedback 검색
- 사용자 명시 안 한 인접 시스템도 포함 (예: doc 만들면 → 빌더 + 검증 + 페이지 fit + 5중박기 위치)

### Step 2. 분석 (Verification)
- 인벤토리 결과 분류: 정상 / 누락 / 이상
- 가장 큰 위험·함정 식별
- 관련 rule 매핑 (30+ 개 중 어느 게 적용?)

### Step 3. 실행 (Execution)
- Plan 한 항목씩 실행
- 큰 작업 = codex/gemini 한테 task-instruction.md 로 위임
- 메타 분석 (우리 시스템 매핑 등) 은 Claude 직접

### Step 4. 확인 (Verification)
- smoke test, dry-run, 로그 점검
- 자동 검증 hook 발동 (verify-image-fit, hook-09 등)
- 사용자가 짚을 필요 없게 — Claude 가 결과 확인 후 보고

### Step 5. 보고 (Reporting)
- 표·목록으로 결과 명시
- Before/After 비교
- 남은 결정사항 (사용자만 답 가능한 것) 만 묻기

## 자가 점검 — rule 위반 가능성 사전 확인

작업 시작 전 다음 30+ rule 자동 체크 (CLAUDE.md § 7 + .claude/rules/):

| 카테고리 | 항목 |
|---|---|
| **농땡이** | 전수조사·분석·확인·보고 5단계 모두? 일부 샘플로 단정 X? |
| **Zero-touch** | 사용자 액션 요구 0? 알림은 크리티컬 5가지만? |
| **하드 경로** | 사용자명·Python버전·OS 절대경로 박았나? `where`/`tempfile` 동적? |
| **Template kit** | `~/.claude/` 직접 수정 X, `setup/templates/` 통해서? |
| **교재 8섹션** | 핵심·표·흐름·강점·약점·강추·우리매핑·점검 다 있나? |
| **버전 접미사** | 자동 -v2/-v3 폴백 X, .bak 백업? |
| **페이지 fit** | PIL 비율 측정·페이지 비율 일치·콘텐츠 합산 ≤ 페이지 한계? |
| **멈춤 방지** | 60초 폴링·지수 backoff·대안 도구? |
| **외국어 이미지** | 한글로 대체 (영어+한글 같이 X)? |
| **다이어그램 품질** | SVG/HTML+화살표+흐름 (단순 박스/표만 = 위반)? |

## codex/gemini 위임 기준

다음 작업은 Claude 가 직접 X, task-instruction.md 로 위임:
- 코드 500줄+ 작성
- 반복 패턴 적용 (예: 20 챕터 동일 강화)
- 외부 도구 자동화 스크립트
- 테스트·검증 코드 작성

위임 X (Claude 직접):
- 우리 시스템 매핑·메타 분석
- rule 설계·5중박기 박기
- 사용자 의도 추론
- 디자인 결정

## 출력 형식 (각 turn 시작)

```text
[auto-planner] 사용자 요청: <요약>

[plan]
1. 전수조사: <범위>
2. 분석: <위험·rule 매핑>
3. 실행: <단계 목록>
4. 확인: <검증 방법>
5. 보고: <기대 산출물>

[자가 점검 결과] 위반 가능성: <없음 | 항목 리스트>
[위임]: <Claude 직접 | codex/gemini 위임 — 사유>
```

## 강화 (5중 박기)

- memory: `feedback_auto_planner_required.md`
- CLAUDE.md § 5 Rules 또는 § 7 추가
- `.claude/rules/best-practices.md` § 자율 plan 의무
- `setup/templates/global-CLAUDE.md` 글로벌
- `plugins/exec_orch/hooks/hook-00-init.sh` 매 세션 출력

## 트리거 키워드

자동 활성화 트리거 (description 매칭):
- 한국어: "해줘", "만들어줘", "고쳐줘", "정리해", "추가해", "보완해", "전수조사", "강화", "수정"
- 결함 지적: "안 보여", "짤려", "여백", "이상해", "농땡이", "대충", "엉망"
- 영어: "make", "build", "fix", "improve", "extend"

## Generative → Agentic 약점 보완

이 skill 이 사용자가 짚은 "1-2단계 (Generative + Agentic) 약함" 의 직접 해결:
- Generative — 단순 응답 X, 5단계 plan 으로 풍부한 산출물
- Agentic — Claude 가 매번 사용자 지시 기다림 X, 한 줄 요청 → 끝까지 자율
