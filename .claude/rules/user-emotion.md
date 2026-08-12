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
