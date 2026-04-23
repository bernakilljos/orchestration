# SPEC — exec_claude

## 1. 의도
Claude 의 고유 기능 4종(AskUserQuestion·Artifacts·Connectors·Extended Thinking)을 우리 킷에 1급(first-class) 패턴으로 흡수.

## 2. 비-목표 (Out of scope)
- Claude API 직접 호출 (Claude Code 가 처리)
- 멀티AI 라우팅 (exec_orch 담당)
- 배포·CI (별도 플러그인)

## 3. 컴포넌트

### 3.1 Commands
- `claude-status` — 가용성 점검·시나리오
- `claude-ask` — AskUserQuestion 패턴
- `claude-artifact` — 인터랙티브 HTML 출력
- `claude-connectors` — 외부 SaaS 통합 흐름
- `claude-thinking` — Extended Thinking 적용 가이드

### 3.2 Skills (auto-activate)
- `skill-claude-ask` — 구조화 질문 메소드론
- `skill-claude-artifact` — 인터랙티브 산출물 디자인 규칙
- `skill-claude-thinking` — 추론 단계 분해 패턴

### 3.3 Scripts
- `scripts/common.sh` — 공유 유틸 (확장용 자리)

## 4. 의존
- `exec_orch` (선행) — 라우팅 결정 컨텍스트 사용

## 5. 출력 경로
- `outputs/artifacts/<type>-<slug>-<date>.html`
- `outputs/asks/<topic>-<date>.json`

## 6. 수용 기준 (Acceptance)
- [ ] 5개 커맨드 모두 sync 후 `/help exec_claude` 에서 보임
- [ ] 3개 스킬 description 에 한국어 트리거 포함
- [ ] `/claude-status` 가 Claude vs Other AI 가용성 비교표 출력
- [ ] `/claude-artifact dashboard <topic>` 가 단일 HTML 파일 생성
- [ ] guide.txt 에 exec_claude 섹션 존재
