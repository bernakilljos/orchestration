---
name: user-emotion-auto-response
description: 사용자 감정·상황별 자동 대응 매핑. 답답→fast, 짜증→시스템 결함 진단, 반복→loop, design 불만→command 수정, 방향 오해→direction-first, 하드코딩 지적→grep 감사, 전수조사 지시→100% Read, 망각 지적→hook 등재, install 언급→순서 확인. 매 사용자 프롬프트마다 detect-user-emotion.sh 가 자동 발동.
---

# 사용자 감정·상황 자동 대응 매핑

Claude 는 사용자 감정·상황을 감지하고 매핑된 자동 대응을 발동해야 함. 사용자가 매번 "fast 로 해줘"·"loop 발동해줘"·"design 수정해줘" 지시하는 게 아니라 kit 이 자동으로.

## 매핑 표

| 사용자 트리거 어휘 | 자동 대응 | 관련 자산 |
|---|---|---|
| **답답·빠름·fast·서두름** | `/fast` mode 활성 (Opus 4.7/4.8/5 Fast) + 짧은 응답 우선 | Claude Code built-in `/fast` |
| **짜증·짱나·엉망·대충·장난** | 시스템 결함 자동 진단 5단계 (실측·등재·강화·보고·게이트) | `feedback_verify_before_report.md` |
| **중복·또 요청·반복 지시** | `/loop` 자동 발동 검토 | `.claude/hooks/detect-repeat-request.sh` + `/loop` skill |
| **design 별로·UI 이상·화면 못생김** | 관련 command md 자동 수정 (`plugins/design_*/commands/*.md` grep + 반영 + sync) | `plugins/design_ppt`·`design_word`·`design_excel`·`design_web-*` |
| **또 방향 오해·target 아니** | direction-first 재적용 + statusline 확인 + 첫 응답 첫 줄 '대상' | `.claude/rules/direction-first.md` |
| **하드코딩·하드 경로·박아** | 자동 grep 감사 (사용자명·Python버전·OS경로·CSS 상수·산식 X %) | `.claude/rules/best-practices.md` § 하드 경로 |
| **안뒤져·뒤져봐·안봤·전부·모든** | 전수조사 100% Read 발동 (grep 아닌 Read N회+) | `.claude/rules/failure-mode.md` § 전수조사 |
| **매번 까먹·또 까먹·기억 못** | Claude 세션 간 학습 X 인정 → 시스템 (hook/statusline/rule/memory) 에 강제 박기 | `.claude/statusline.sh` + `hook-00-init.sh` |
| **install·배포·deploy·sync-team** | install 순서 확인 (kit → commit → sync → install → 검증) | `.claude/hooks/pre-install-lock.sh` |
| **회피·딴말·빙빙 돌림** | 직접 답 → 부연 → 행동 강제 | `.claude/hooks/detect-deflection.sh` |
| **비용·budget·quota·돈** | budget 상한·quota fallback 재확인 | `route.py --check` |
| **성능·느림·slow** | 캐싱·병렬·subagent Explore 검토 | Prompt caching TTL 전략 |

## 감지 hook (UserPromptSubmit)

매 프롬프트마다 다음 hook 이 병렬 발동:

1. `detect-user-emotion.sh` (이 스킬의 코어 감지) — 위 표 매핑
2. `detect-repeat-request.sh` — 최근 프롬프트 유사도 (반복 감지)
3. `detect-deflection.sh` — 회피 안티패턴
4. `user-prompt-auto-planner.sh` — 5단계 plan + MoE 자동 분류
5. `periodic-rules-reminder.sh` — 10번째마다 룰 리마인드

## 대응 원칙

- **자동화 우선**: 사용자가 "fast 로 해줘" 지시하기 전에 감지해서 발동
- **사용자 인지 부하 X**: 매번 사용자가 시스템에 요청하지 않아도 됨
- **로그 남기기**: 자동 대응 발동 시 `.claude/logs/emotion-response.log` 기록
- **명시 지시 우선**: 사용자가 명시적으로 반대 지시하면 자동 대응 skip

## 확장 방법

새 감정·상황 발견 시:
1. 위 매핑 표에 행 추가
2. `detect-user-emotion.sh` 의 `if ... grep` 블록 추가
3. 관련 자산 (hook·rule·memory) 정본 명시
4. 확장 시 `.claude/rules/consistency.md` § 함수·훅·룰 중복 확인

## 금지

1. 매핑 없는 감지 hook 별도 만들기 (이 스킬로 통합)
2. 감지 후 자동 대응 skip
3. 로그 없이 발동 (관측 불가)
4. 사용자 명시 반대 지시 무시

## 관련

- `.claude/hooks/detect-user-emotion.sh` (코어 감지)
- `.claude/rules/direction-first.md`
- `.claude/rules/failure-mode.md`
- `.claude/rules/consistency.md`
- `feedback_user_enfp_adhd_style.md`
- `feedback_verify_before_report.md`
