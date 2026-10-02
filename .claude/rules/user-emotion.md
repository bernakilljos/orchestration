# 사용자 감정·상황 자동 대응 룰

> **근거**: 2026-08-12 사용자 지적 — "짜증나면 hook 에게 등록하세요"·"답답하시면 fast"·"design 별로면 command 수정"·"loop 말고 뭐있어".
> **이유**: 사용자가 매번 상황별 대응 지시하는 게 아니라 kit 이 감정·상황 감지해 자동 대응 발동해야.

## 절대 룰

**사용자 프롬프트에서 감정·상황 어휘 감지 시 매핑된 자동 대응 발동.** 사용자가 명시 지시하기 전에 자동으로.

## 매핑 (SoT)

| 트리거 어휘 | 자동 대응 |
|---|---|
| **답답·빠름·fast·서두름** | `/fast` mode 활성 + 짧은 응답 |
| **짜증·짱나·엉망·대충·장난** | 시스템 결함 진단 5단계 (실측·등재·강화·보고·게이트) |
| **미쳐·미치겠·돌아버리·답답해 죽겠·막혀·안 풀려** | `/brainstorm` 또는 `/go` 자동 발동 (혼자 결과 내지 말고 설계 옵션 공유 · trade-off 제시 · 사용자 결정 받기) |
| **중복·또 요청·반복** | `/loop` 발동 |
| **design 별로·UI 이상·화면 못생김** | 관련 command md 자동 수정 (design_*/commands/*.md) |
| **또 방향 오해·target 아니** | direction-first 재적용 + statusline 확인 |
| **하드코딩·박아** | grep 감사 자동 실행 |
| **안뒤져·전부·모든·다** | 전수조사 100% Read + subagent 병렬 |
| **매번 까먹·기억 못** | 시스템 강제 (hook·statusline·rule·memory) 재확인·등재 |
| **install·배포·deploy** | install 순서 확인 (kit → commit → sync → install → 검증) |
| **회피·딴말·빙빙 돌림** | 직접 답 강제 |
| **비용·budget·quota·돈** | budget 상한·quota fallback 재확인 |
| **성능·느림·slow** | 캐싱·병렬·subagent Explore 검토 |
| **같은 질문 3회+ 반복** | `/explainlikeim5` 자동 (5살 톤·비유·짧게 재설명) |
| **응답에 고급 용어 (RAG·CoT·quorum·eventual consistency·byzantine 등)** | `/explainlikeim5` 자동 (일상 비유 치환) |
| **"A vs B"·"비교"·"뭐가 좋아"·"vs"** | `/compare` 자동 (장단점·추천·근거) |
| **"확신 안 서"·"괜찮을까"·"리스크"·"위험"·"걱정"** | `/devil` 자동 (악마의 변호인 · 모든 가정 반론) |
| **"복잡해"·"처음부터"·"기초"·"기본부터"** | `/teacher` 자동 (단계별 교육) |
| **"어떻게 해야 돼"·"접근 방식"·"어떻게 할까"** | `/ooda` 또는 `/brainstorm` 자동 (상황 분석·설계) |
| **"내 생각 어때"·"피드백"·"평가"** | `/critique` 자동 (냉정 비판 · 칭찬 X) |
| **세션 80%+ (statusline rate_limits.five_hour)** | `/guard-save` 자동 (스냅샷) |
| **"리서치"·"조사"·"알아봐"·"뭐가 있나"** | `/scout` 자동 (정찰 · breadth 먼저) |
| **"요약"·"짧게"·"3줄"·"한 줄"** | `/brief` 자동 (초간결) |
| **"발표"·"보고"·"피치"·"PT"·"임원"·"PL"** | `/pitch` 자동 (설득력 있는 투자자 피치 포맷) |
| **"AI 티나"·"사람처럼"·"자연스럽게"·"natural"** | `/ghost` 자동 (AI 글쓰기 패턴 제거) |
| **"상태"·"지금 어때"·"현황"·"대시보드"** | `/exec_status` 자동 (워커·큐·heartbeat·sync 통합) |
| **"승인"·"approve"·"대기"·"pending"** | `/approvals` 자동 (대기 task 전부 보기) |
| **"비용"·"얼마나 썼"·"token"·"지출"** | `/token-stats` 자동 (세션별 토큰 통계) |
| **"완료"·"끝났"·"다 됐"·"마무리"** | `/validate` 자동 (테스트·스크린샷·증거 저장) |
| **"commit"·"push"·"PR"·"배포 전"** | `/sec-scan` 자동 (semgrep·gitleaks·bandit) |
| **"다 해줘"·"알아서"·"God mode"** | `/godmode` 자동 (최대 자율) |
| **"최고 성능"·"초난도"·"어려운 문제"·"Mythos"** | `/effort-mythos` 자동 (Fable 5.1 라우팅) |
| **"다이어그램"·"그림"·"시각화"·"구조도"** | `/arch-auto` 자동 (마인드맵·레이어·치트 중 적합한 것) |
| **"수정해"·"고쳐"·"바꿔"·"변경"** | 증명 체인 강제 (pre-snapshot → 수정 → post-snapshot → 작동 테스트 → 보고 · verify-after-edit-mandatory.md) |
| **"왜 안 됐어"·"수정했다며 안 됨"·"적용 안 됨"·"효과 없"** | 자가 진단 5단계 (파일·cascade·캐시·다른 파일·실행 테스트 · verify-after-edit-mandatory.md) |
| **"에러"·"오류"·"error"·"exception"·"traceback"·"fail"** | 자동 로그 조회 (recent-error-count·.claude/logs tail) + 원인 분석 + 수정 |
| **"느려"·"slow"·"성능"·"응답 안 와"·"끊김"** | `/performance` 자동 (응답시간·메모리·번들·Lighthouse) |
| **"원복"·"되돌려"·"revert"·"롤백"·"rollback"·"undo"** | git revert 또는 `.bak` restore 자동 (사용자 승인 후) |
| **"리뷰해"·"코드 리뷰"·"review"·"PR 리뷰"** | code-reviewer agent 자동 dispatch (격리 · 구조화 반환) |
| **"스크린샷"·"캡처"·"screenshot"·"화면 찍어"** | `/screenshot` 자동 (Playwright headless) |
| **"번역"·"translate"·"영어로"·"한글로"·"일본어로"** | `/translate` 자동 |
| **"녹음"·"음성"·"회의"·"meeting"·"회의록"** | `/meeting`·`/transcribe` 자동 (Whisper STT) |
| **"말로"·"읽어줘"·"speak"·"TTS"** | `/speak` 자동 (edge-tts) |
| **"예시 보여"·"artifact"·"바로 쓸"·"샘플"** | `/artifacts` 자동 (실행 가능 산출물) |
| **"데모"·"mock"·"가짜"·"임시"·"시연용"** | feedback_no_mock_default 룰 재주입 (사용자 명시 없으면 실전 강제) |

## 강제

- **감지 hook**: `.claude/hooks/detect-user-emotion.sh` (UserPromptSubmit) — 자동 발동
- **매핑 SoT**: `plugins/exec_orch/skills/user-emotion-auto-response.md`
- **로그**: `.claude/logs/emotion-response.log`

## 확장 절차

새 감정·상황 발견 시:
1. 위 표에 행 추가
2. `detect-user-emotion.sh` 의 `if ... grep` 블록 추가
3. `user-emotion-auto-response.md` skill 도 동기 갱신
4. `feedback_user_emotion_mapping.md` memory 도 동기 갱신

## 금지

1. 감지 후 자동 대응 skip
2. 매핑 없는 감지 hook 별도 만들기 (consistency.md § 함수·훅·룰 중복 위반)
3. 사용자 명시 반대 지시 무시

## 관련

- `.claude/hooks/detect-user-emotion.sh`
- `plugins/exec_orch/skills/user-emotion-auto-response.md`
- `feedback_user_emotion_mapping.md`
- `feedback_user_enfp_adhd_style.md`
- `.claude/rules/failure-mode.md` § 회피 안티패턴
