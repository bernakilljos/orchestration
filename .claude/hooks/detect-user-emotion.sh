#!/usr/bin/env bash
# detect-user-emotion.sh — UserPromptSubmit hook
# 목적: 사용자 감정-상황 감지 -> 매핑된 자동 대응 systemMessage 주입
# 근거: 2026-08-12 사용자 지적 — "짜증나면 hook에게 등록"-"답답하시면 fast"-"design 별로면 command 수정"
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

# 1. 답답-빠름 -> fast mode 안내
if echo "$PROMPT" | grep -qE '답답|빨리|빠르게|fast|서둘|급함'; then
  actions="${actions}[답답 감지] -> /fast 모드 권장 (Opus 4.7/4.8/5 Fast). 짧은 응답 우선.\\n"
fi

# 2. 짜증-엉망-대충 -> 시스템 결함 자동 진단 + hook 등재
if echo "$PROMPT" | grep -qE '짜증|짱나|엉망|대충|장난|매번이래|또 이래|하지말라'; then
  actions="${actions}[짜증 감지] -> 시스템 결함 신호. 자동 진단 5단계:\\n  1) 관련 hook-rule-memory 실측 (grep 아닌 100% Read)\\n  2) 놓친 부분 등재 (feedback + hook + rule + CLAUDE.md § 7)\\n  3) 감지 시스템 강화\\n  4) 원인 사용자에게 짧게 보고\\n  5) 반복 방지 게이트 추가\\n"
fi

# 3. 반복 지시 -> /loop 발동 (detect-repeat-request.sh 이 별도 감지 - 여기서는 loop 안내 강화)
if echo "$PROMPT" | grep -qE '중복|또 요청|같은 지시|반복'; then
  actions="${actions}[반복 감지] -> /loop 자동 발동. 감지 hook: detect-repeat-request.sh (별도).\\n"
fi

# 4. design/UI 불만 -> command 수정 대응
if echo "$PROMPT" | grep -qE 'design.*별로|디자인.*별로|UI.*이상|화면.*못생|design 이 별로|디자인이 별로'; then
  actions="${actions}[design 불만] -> 관련 command md 자동 수정. plugins/design_*/commands/*.md grep -> 사용자 지적 반영 후 sync-plugins.\\n"
fi

# 5. 방향 오해 지적 -> direction-first + statusline 강제
if echo "$PROMPT" | grep -qE '방향.*오해|또.*방향|target.*아니|대상.*아니'; then
  actions="${actions}[방향 오해] -> direction-first.md 재적용. statusline 확인. 첫 응답 첫 줄 '대상: <path>' 명시.\\n"
fi

# 6. 하드코딩 지적 -> 자동 grep 감사
if echo "$PROMPT" | grep -qE '하드코딩|하드 경로|박아|hardcod'; then
  actions="${actions}[하드코딩 지적] -> 자동 grep 감사 (사용자명-Python버전-OS경로-%-상수). 대상 4갈래 (kit/설정/target/글로벌) 중 어디 대상인지 먼저 명시.\\n"
fi

# 7. "안뒤져"-"뒤져봐"-"안봤어" -> 전수조사 100% Read
if echo "$PROMPT" | grep -qE '안뒤져|뒤져봐|안봤|다른건|다 확인|전부|모든'; then
  actions="${actions}[전수조사 지시] -> 100% Read (failure-mode.md § 전수조사 위반). N 파일 = Read N회+. subagent 병렬 (Agent Explore) 강권.\\n"
fi

# 8. "매번 까먹" -> 시스템 강제 (hook-statusline-systemMessage) 재확인
if echo "$PROMPT" | grep -qE '매번.*까먹|또.*까먹|왜.*까먹|기억.*못'; then
  actions="${actions}[망각 지적] -> Claude 세션 간 학습 X. 시스템 (hook/statusline/rule/memory) 에 강제 박기. 이번 지적을 hook 감지 -> systemMessage 로 발동하도록 매핑.\\n"
fi

# 9. install-배포 관련 -> install-order.sh 룰 상기
if echo "$PROMPT" | grep -qE 'install|배포|deploy|sync-team|install-to'; then
  actions="${actions}[install 언급] -> install 순서 (kit 편집 -> commit -> sync -> install -> 검증). pre-install-lock.sh 감지. best-practices.md § install 순서.\\n"
fi

# 10. 격한 감정 (미쳐·답답해 죽겠·막혀·안 풀려) -> /brainstorm 또는 /go 자동 발동
if echo "$PROMPT" | grep -qE '미쳐|미치겠|미치긋|돌아버|답답해 죽|막혀|안 풀|안풀려|막막|어떻게 해야'; then
  actions="${actions}[격한 감정 감지] -> /brainstorm 또는 /go 자동 발동. 혼자 결과 내지 말고 설계 옵션 2~3개 + trade-off + 추천 1개 제시. 사용자 결정 받고 그 다음 실행.\\n"
fi

# 11. 같은 질문 3회+ 반복 (detect-repeat-request.sh 가 similarity_score 측정)
#     여기서는 "모르겠다·이해 안 돼·뭔 소리" 어휘 감지 시 explainlikeim5 트리거
if echo "$PROMPT" | grep -qE '모르겠|이해.*안|뭔 소리|무슨 말|쉽게|어려워'; then
  actions="${actions}[이해 어려움 감지] -> /explainlikeim5 자동 발동. 5살 톤·일상 비유·고급 용어 X. 긴 essay 금지.\\n"
fi

# 12. 비교·결정 트리거
if echo "$PROMPT" | grep -qE 'vs |대 |비교|뭐가 좋|어떤 게|차이'; then
  actions="${actions}[비교 요청] -> /compare 자동 (장단점·추천·근거 표).\\n"
fi

# 13. 확신·리스크 질문
if echo "$PROMPT" | grep -qE '확신|괜찮을|리스크|위험|걱정|문제 없|안전'; then
  actions="${actions}[리스크 질문] -> /devil 자동 (악마의 변호인 · 모든 가정 반론).\\n"
fi

# 14. 복잡·기초부터
if echo "$PROMPT" | grep -qE '복잡해|처음부터|기초|기본부터|차근차근'; then
  actions="${actions}[단계별 교육 필요] -> /teacher 자동 (단계별 · 이해 확인).\\n"
fi

# 15. 접근 방식·brainstorming
if echo "$PROMPT" | grep -qE '어떻게 해야|접근 방식|어떻게 할까|방법론|전략'; then
  actions="${actions}[접근 방식 질문] -> /ooda 또는 /brainstorm 자동 (상황 분석·설계 옵션).\\n"
fi

# 16. 피드백·평가 요청
if echo "$PROMPT" | grep -qE '내 생각|피드백|평가|어때\?|의견'; then
  actions="${actions}[피드백 요청] -> /critique 자동 (냉정 비판 · 칭찬 X).\\n"
fi

# 17. 리서치·조사
if echo "$PROMPT" | grep -qE '리서치|조사|알아봐|뭐가 있나|후보'; then
  actions="${actions}[리서치] -> /scout 자동 (정찰 · breadth 먼저 · WebSearch 병행).\\n"
fi

# 18. 요약·짧게
if echo "$PROMPT" | grep -qE '요약|짧게|3줄|한 줄|초간결'; then
  actions="${actions}[요약 요청] -> /brief 자동 (3줄 이내).\\n"
fi

# 19. 발표·보고·PL
if echo "$PROMPT" | grep -qE '발표|보고|피치|PT|임원|PL|설득'; then
  actions="${actions}[보고/발표] -> /pitch 자동 (설득력 있는 투자자 피치 포맷).\\n"
fi

# 20. AI 티·natural
if echo "$PROMPT" | grep -qE 'AI 티|사람처럼|자연스럽게|natural|AI 글'; then
  actions="${actions}[AI 티 제거] -> /ghost 자동 (AI 글쓰기 패턴 제거).\\n"
fi

# 21. 상태·대시보드
if echo "$PROMPT" | grep -qE '상태|지금 어때|현황|대시보드|dashboard'; then
  actions="${actions}[상태 조회] -> /exec_status 자동 (워커·큐·heartbeat·sync 통합).\\n"
fi

# 22. 승인·대기
if echo "$PROMPT" | grep -qE '승인|approve|대기|pending|waiting'; then
  actions="${actions}[승인 체크] -> /approvals 자동 (대기 task 전부 보기).\\n"
fi

# 23. 비용·토큰
if echo "$PROMPT" | grep -qE '비용|얼마나 썼|지출|토큰 통계|token stat'; then
  actions="${actions}[비용 조회] -> /token-stats 자동.\\n"
fi

# 24. 완료·마무리
if echo "$PROMPT" | grep -qE '완료|끝났|다 됐|마무리|끝'; then
  actions="${actions}[완료 처리] -> /validate 자동 (테스트·스크린샷·증거 저장).\\n"
fi

# 25. commit·push·PR 전
if echo "$PROMPT" | grep -qE 'commit|push|PR|배포 전|릴리스'; then
  actions="${actions}[배포 전] -> /sec-scan 자동 (semgrep·gitleaks·bandit).\\n"
fi

# 26. God mode·알아서
if echo "$PROMPT" | grep -qE '다 해줘|알아서|god ?mode|모든 것'; then
  actions="${actions}[God mode] -> /godmode 자동 (최대 자율 · 직통 라우팅).\\n"
fi

# 27. 초난도·Mythos
if echo "$PROMPT" | grep -qE '최고 성능|초난도|어려운 문제|mythos|fable'; then
  actions="${actions}[Mythos] -> /effort-mythos 자동 (Fable 5.1 라우팅 · budget 게이트).\\n"
fi

# 28. 다이어그램·시각화
if echo "$PROMPT" | grep -qE '다이어그램|그림|시각화|구조도|마인드맵'; then
  actions="${actions}[시각화] -> /arch-auto 자동 (마인드맵·레이어·치트 중 적합).\\n"
fi

# 29. 수정 지시 -> 증명 체인 강제 (수정 후 자동 pre/post snapshot + 작동 테스트 + 보고)
if echo "$PROMPT" | grep -qE '수정해|고쳐|바꿔|변경해|고쳐줘|수정 해|바꿔줘'; then
  actions="${actions}[수정 지시] -> 증명 체인 강제 (verify-after-edit-mandatory.md). 5단계: ① pre-snapshot (md5/Read/sqlite SELECT/curl) ② 수정 실행 ③ post-snapshot ④ diff + 작동 테스트 ⑤ 보고 (증거 첨부). '수정했습니다' 만 보고 X.\\n"
fi

# 30. "왜 안 됐어" 재지시 -> 자가 진단 5단계
if echo "$PROMPT" | grep -qE '왜.*안 됐|왜 안됐|수정했다며|적용 안 됨|적용 안됨|효과 없|안 되어있|안되어있|안 되어 있|실제 안|증명해'; then
  actions="${actions}[재검증 재지시] -> 자가 진단 5단계 (verify-after-edit-mandatory.md): ① 파일 Read 재확인 ② cascade override ③ 캐시·재시작 ④ 엉뚱한 파일 ⑤ 실행 테스트. 원인 1줄 + 수정 + 재검증 결과 첨부.\\n"
fi

# 감지된 게 있으면 systemMessage
if [ -n "$actions" ]; then
  cat <<EOF
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[감정-상황 자동 매핑]\\n${actions}\\n★ 매핑 SoT: plugins/exec_orch/skills/user-emotion-auto-response.md\\n★ 개별 감지 hook: detect-deflection.sh (회피), detect-repeat-request.sh (반복), detect-asset-creation.sh (자산 생성)"}}
EOF
fi
exit 0
