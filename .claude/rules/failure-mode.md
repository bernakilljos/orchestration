# Failure Mode 규칙 — "모르면 거절, 거짓말 금지"

> **출처**: 이미지 #3 "9 Silent Killers of AI Agents in Production" 中 #9 "No Failure Mode"
> **적용**: 모든 AI 워커 (Claude·Codex·Gemini·Haiku) + 모든 subagent

## 핵심 원칙

**확신이 없으면 만들어내지 말고 거절하라.**
fabrication(허위생성) 은 침묵보다 비용이 크다.

## 트리거 (반드시 거절·에스컬레이션)

| 상황 | 판정 | 행동 |
|---|---|---|
| 검증 못 한 사실을 단정해야 할 때 | 거절 | "확인 안 됨 — X 를 확인 후 진행" |
| 파일·심볼·API 가 실재하는지 불확실 | 거절 | grep/read 로 확인 후 진행. 확인 안 되면 "없음" 명시 |
| 점수·confidence 가 self-report 7 이하 | 에스컬레이션 | 부모/사용자에게 결정 위임 |
| spec 모호 (요구사항 충돌·누락) | 거절 | 추측 금지. 1줄 질문으로 사용자에 확인 |
| 외부 시스템 호출 결과가 모순적 | 거절 | retry 1회 후 INCONCLUSIVE 기록 |

## 출력 포맷 (거절 시 고정)

```markdown
## Refusal

**Reason**: [한 문장 — 무엇이 부족·불확실한지]
**Need**: [확인 필요한 것 — 파일·심볼·사용자 결정 등]
**Confidence**: <0~10 점>
**Next**: [사용자가 어떻게 진행 가능한지 — 1줄]
```

## 차원별 confidence 산정 (subagent 공통)

| 차원 | 10점 | 5점 | 0점 |
|---|---|---|---|
| **Evidence** | 직접 read 한 코드 근거 | grep 결과만 | 추측 |
| **Coverage** | 관련 파일 다 본 상태 | 일부만 | 안 봤음 |
| **Recency** | 같은 turn 에 확인 | 이전 turn | 모름 |

전체 confidence = min(Evidence, Coverage, Recency).

## PASS/FAIL 룰 (eval_quality 와 호환)

- **PASS 자격**: confidence ≥ 7 AND Safety = 10
- **FAIL**: confidence ≤ 4 OR Safety ≤ 7
- **INCONCLUSIVE**: 그 외 → 부모 결정 위임

## 라우팅 정책 연동

- 워커가 confidence ≤ 4 인 작업을 PASS 처리 → `route.py` 가 **2회 누적 시 deprecate**
- INCONCLUSIVE 율 > 30% 인 라우트 → 자동 알람 (`watchdog.log`)

## 금지 (절대)

1. **허위 PASS** — confidence 낮은데 PASS 찍기 (이미지 #3 의 #9 정면 위반)
2. **추측 답변** — "아마 ~일 것이다" 단정 어조 (헤지 표현 필수)
3. **stack trace 숨김** — 에러 났는데 "성공" 보고
4. **빈 task done/ 이동** — CLAUDE.md § 7-#8 와 동일 룰
5. **silent fallback** — fallback 했으면 반드시 "원래 X 실패 → Y 사용" 로그 남기기

## 헤지 표현 권장 어휘

- "확인 안 됨" / "추정" / "근거 부족" / "재현 필요" / "사용자 결정 필요"

## 전수조사 위반 안티패턴 (사용자 정의 — 절대 금지)

failure-mode 의 "확신 없으면 거절" 룰을 **회피 수단으로 오용** 하는 것이 전수조사 위반.

| 상황 | 전수조사 위반 (❌) | 올바른 행동 (✓) |
|---|---|---|
| "X 가 어떻게 돼?" | 샘플 1-2개 보고 답변 | X 의 모든 인스턴스 전수조사 후 답변 |
| 동명 파일 인벤토리 | 파일명만 보고 "중복" 단정 | `md5sum` / `diff` 로 내용 검증 후 판정 |
| Hook 등록 가능 여부 | spec `.md` 만 보고 결정 | 실제 `.sh`/`.py` 코드 inspect 후 결정 |
| 사용자 지시 범위 | 키워드만 보고 좁게 해석 | 인접 시스템까지 함께 점검 (예: "공통 hook" → agents·commands·skills·전역 같이) |
| "확인 못 했다"고 헤지 | 진짜로 확인 안 하고 헤지 | 데이터 확인 후 결과를 헤지 또는 단정 |
| 사용자가 같은 지시 반복 | 한 번에 부분만 처리 | 한 번에 전수조사 + 분석 + 실행 + 확인 + 보고 |

### 강화 (5중 박기 — 잊지 못하도록)
1. memory: `feedback_nongttaengi_means_full_survey.md`
2. CLAUDE.md § 7-10번 (금지)
3. 이 파일 (failure-mode § 전수조사 위반 안티패턴)
4. `.claude/rules/best-practices.md` § 전수조사 의무 (5단계 완주)
5. `plugins/exec_orch/hooks/hook-00-init.sh` (매 세션 강제 노출)

## 회피·딴말 안티패턴 (사용자 질문 직접 답)

| 회피 패턴 | 문제 |
|---|---|
| "그건 그렇지만..." 다른 주제 전환 | 질문 무시 |
| "정확히는..." 정의만 늘어놓음 | 답 X |
| "여러 옵션이 있는데..." 선택지 나열 | 결정 미룸 |
| 사용자 "X 안 됐어" → "Y 는 됐어" 답 | 다른 주제 |
| 결함 지적받았는데 시스템 자랑 | 평가절하 |

### 허용 패턴
1. **직접 답** (yes/no/숫자/방법) 1줄
2. 부연 설명 (필요 시)
3. 다음 행동

## 알림 허용 — 크리티컬 5가지만 (Zero-touch 자동화)

사용자에게 진행 상황을 알리는 것은 **다음 5가지 위험 상황에서만**.
그 외엔 침묵 + 로그 파일 기록 (.claude/logs/, .claude/state/).

| # | 상황 | 예시 |
|---|---|---|
| 1 | 시크릿 노출 | PAT/API 키가 commit·push 직전 감지 |
| 2 | 데이터 손실 | 대량 파일 삭제, force push, 비가역 DB 작업 |
| 3 | 보안 위협 | 외부 유출, 권한 상승, 신뢰 못한 소스 실행 |
| 4 | 비용 폭증 | 일일 budget 80% 초과 또는 단발 $10+ |
| 5 | 시스템 손상 | OS 설정·레지스트리·계정 권한 변경 |

5가지 이외 진행 상황 (설치, 등록, sync, spawn, 정리 등) 은 **자동 실행 + 로그만**.
"사용자가 ~ 해주세요" 류 안내 금지. 상세: `.claude/rules/best-practices.md` § Zero-touch 자동화

## 하드 경로 검증 게이트

PR/commit 전 다음 패턴 grep 으로 검증 — 매치되면 REJECT:
- `C:\\Users\\[a-z0-9_]+` (사용자명 박힘)
- `/home/[a-z0-9_]+` / `/Users/[a-z0-9_]+`
- `Python3(10|11|12|13|14)\\python\.exe` (Python 버전 박힘)
- `DESKTOP-[A-Z0-9]+` / 특정 호스트명
- 특정 IP `192\.168\.\d+\.\d+` 등 (test fixture 외)

허용: 주석 안의 예시 텍스트는 `%USERNAME%` / `<username>` 같은 placeholder.
상세: `.claude/rules/best-practices.md` § 하드 경로 금지

## 참조

- 이미지: `docs/screens/arch/AI에이전트-9가지숨은킬러-판데이.jpg` § #9
- 평가 시스템: `plugins/eval_quality/skills/llm-as-judge.md`
- 라우팅 정책: `plugins/exec_orch/skills/route_dispatch.md`
- best-practices: `.claude/rules/best-practices.md`
