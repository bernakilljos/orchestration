#!/usr/bin/env bash
# detect-user-emotion.sh — UserPromptSubmit hook
# 목적: 사용자 감정·상황 감지 → 매핑된 자동 대응 systemMessage 주입
# 근거: 2026-08-12 사용자 지적 — "짜증나면 hook에게 등록"·"답답하시면 fast"·"design 별로면 command 수정"
# 매핑 SoT: plugins/exec_orch/skills/user-emotion-auto-response.md
set -e

INPUT="$(cat)"
if command -v jq >/dev/null 2>&1; then
  PROMPT="$(echo "$INPUT" | jq -r '.prompt // ""' 2>/dev/null | head -c 500)"
else
  PROMPT="$(echo "$INPUT" | grep -oE '"prompt"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*: *"\(.*\)"$/\1/' | head -c 500)"
fi
[ -z "$PROMPT" ] && exit 0

# 감정/상황 매핑 (SoT: user-emotion-auto-response.md 표)
actions=""

# 1. 답답·빠름 → fast mode 안내
if echo "$PROMPT" | grep -qE '답답|빨리|빠르게|fast|서둘|급함'; then
  actions="${actions}[답답 감지] → /fast 모드 권장 (Opus 4.7/4.8/5 Fast). 짧은 응답 우선.\\n"
fi

# 2. 짜증·엉망·대충 → 시스템 결함 자동 진단 + hook 등재
if echo "$PROMPT" | grep -qE '짜증|짱나|엉망|대충|장난|매번이래|또 이래|하지말라'; then
  actions="${actions}[짜증 감지] → 시스템 결함 신호. 자동 진단 5단계:\\n  1) 관련 hook·rule·memory 실측 (grep 아닌 100% Read)\\n  2) 놓친 부분 등재 (feedback + hook + rule + CLAUDE.md § 7)\\n  3) 감지 시스템 강화\\n  4) 원인 사용자에게 짧게 보고\\n  5) 반복 방지 게이트 추가\\n"
fi

# 3. 반복 지시 → /loop 발동 (detect-repeat-request.sh 이 별도 감지 · 여기서는 loop 안내 강화)
if echo "$PROMPT" | grep -qE '중복|또 요청|같은 지시|반복'; then
  actions="${actions}[반복 감지] → /loop 자동 발동. 감지 hook: detect-repeat-request.sh (별도).\\n"
fi

# 4. design/UI 불만 → command 수정 대응
if echo "$PROMPT" | grep -qE 'design.*별로|디자인.*별로|UI.*이상|화면.*못생|design 이 별로|디자인이 별로'; then
  actions="${actions}[design 불만] → 관련 command md 자동 수정. plugins/design_*/commands/*.md grep → 사용자 지적 반영 후 sync-plugins.\\n"
fi

# 5. 방향 오해 지적 → direction-first + statusline 강제
if echo "$PROMPT" | grep -qE '방향.*오해|또.*방향|target.*아니|대상.*아니'; then
  actions="${actions}[방향 오해] → direction-first.md 재적용. statusline 확인. 첫 응답 첫 줄 '대상: <path>' 명시.\\n"
fi

# 6. 하드코딩 지적 → 자동 grep 감사
if echo "$PROMPT" | grep -qE '하드코딩|하드 경로|박아|hardcod'; then
  actions="${actions}[하드코딩 지적] → 자동 grep 감사 (사용자명·Python버전·OS경로·%·상수). 대상 4갈래 (kit/설정/target/글로벌) 중 어디 대상인지 먼저 명시.\\n"
fi

# 7. "안뒤져"·"뒤져봐"·"안봤어" → 전수조사 100% Read
if echo "$PROMPT" | grep -qE '안뒤져|뒤져봐|안봤|다른건|다 확인|전부|모든'; then
  actions="${actions}[전수조사 지시] → 100% Read (failure-mode.md § 전수조사 위반). N 파일 = Read N회+. subagent 병렬 (Agent Explore) 강권.\\n"
fi

# 8. "매번 까먹" → 시스템 강제 (hook·statusline·systemMessage) 재확인
if echo "$PROMPT" | grep -qE '매번.*까먹|또.*까먹|왜.*까먹|기억.*못'; then
  actions="${actions}[망각 지적] → Claude 세션 간 학습 X. 시스템 (hook/statusline/rule/memory) 에 강제 박기. 이번 지적을 hook 감지 → systemMessage 로 발동하도록 매핑.\\n"
fi

# 9. install·배포 관련 → install-order.sh 룰 상기
if echo "$PROMPT" | grep -qE 'install|배포|deploy|sync-team|install-to'; then
  actions="${actions}[install 언급] → install 순서 (kit 편집 → commit → sync → install → 검증). pre-install-lock.sh 감지. best-practices.md § install 순서.\\n"
fi

# 감지된 게 있으면 systemMessage
if [ -n "$actions" ]; then
  cat <<EOF
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[감정·상황 자동 매핑]\\n${actions}\\n★ 매핑 SoT: plugins/exec_orch/skills/user-emotion-auto-response.md\\n★ 개별 감지 hook: detect-deflection.sh (회피), detect-repeat-request.sh (반복), detect-asset-creation.sh (자산 생성)"}}
EOF
fi
exit 0
