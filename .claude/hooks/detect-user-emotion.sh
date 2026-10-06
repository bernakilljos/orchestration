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

# 2026-10-06: 검사마다 `echo | grep` 을 띄우던 것(프롬프트당 최대 59회 fork · Windows 에서 9.4초 →
#   3초 timeout 초과로 출력 폐기)을 bash 내장 정규식으로 교체. 패턴·출력은 그대로.
_m()  { local re="$1"; [[ $PROMPT =~ $re ]]; }
_mi() { local re="$1" r; shopt -s nocasematch; [[ $PROMPT =~ $re ]]; r=$?; shopt -u nocasematch; return $r; }

# 감정/상황 매핑 (SoT: user-emotion-auto-response.md 표)
actions=""

# 1. 답답-빠름 -> fast mode 안내
if _m '답답|빨리|빠르게|fast|서둘|급함'; then
  actions="${actions}[답답 감지] -> /fast 모드 권장 (Opus 4.7/4.8/5 Fast). 짧은 응답 우선.\\n"
fi

# 2. 짜증-엉망-대충 -> 시스템 결함 자동 진단 + hook 등재
if _m '짜증|짱나|엉망|대충|장난|매번이래|또 이래|하지말라'; then
  actions="${actions}[짜증 감지] -> 시스템 결함 신호. 자동 진단 5단계:\\n  1) 관련 hook-rule-memory 실측 (grep 아닌 100% Read)\\n  2) 놓친 부분 등재 (feedback + hook + rule + CLAUDE.md § 7)\\n  3) 감지 시스템 강화\\n  4) 원인 사용자에게 짧게 보고\\n  5) 반복 방지 게이트 추가\\n"
fi

# 3. 반복 지시 -> /loop 발동 (detect-repeat-request.sh 이 별도 감지 - 여기서는 loop 안내 강화)
if _m '중복|또 요청|같은 지시|반복'; then
  actions="${actions}[반복 감지] -> /loop 자동 발동. 감지 hook: detect-repeat-request.sh (별도).\\n"
fi

# 4. design/UI 불만 -> command 수정 대응
if _m 'design.*별로|디자인.*별로|UI.*이상|화면.*못생|design 이 별로|디자인이 별로'; then
  actions="${actions}[design 불만] -> 관련 command md 자동 수정. plugins/design_*/commands/*.md grep -> 사용자 지적 반영 후 sync-plugins.\\n"
fi

# 5. 방향 오해 지적 -> direction-first + statusline 강제
if _m '방향.*오해|또.*방향|target.*아니|대상.*아니'; then
  actions="${actions}[방향 오해] -> direction-first.md 재적용. statusline 확인. 첫 응답 첫 줄 '대상: <path>' 명시.\\n"
fi

# 6. 하드코딩 지적 -> 자동 grep 감사
if _m '하드코딩|하드 경로|박아|hardcod'; then
  actions="${actions}[하드코딩 지적] -> 자동 grep 감사 (사용자명-Python버전-OS경로-%-상수). 대상 4갈래 (kit/설정/target/글로벌) 중 어디 대상인지 먼저 명시.\\n"
fi

# 7. "안뒤져"-"뒤져봐"-"안봤어" -> 전수조사 100% Read
if _m '안뒤져|뒤져봐|안봤|다른건|다 확인|전부|모든'; then
  actions="${actions}[전수조사 지시] -> 100% Read (failure-mode.md § 전수조사 위반). N 파일 = Read N회+. subagent 병렬 (Agent Explore) 강권.\\n"
fi

# 8. "매번 까먹" -> 시스템 강제 (hook-statusline-systemMessage) 재확인
if _m '매번.*까먹|또.*까먹|왜.*까먹|기억.*못'; then
  actions="${actions}[망각 지적] -> Claude 세션 간 학습 X. 시스템 (hook/statusline/rule/memory) 에 강제 박기. 이번 지적을 hook 감지 -> systemMessage 로 발동하도록 매핑.\\n"
fi

# 9. install-배포 관련 -> install-order.sh 룰 상기
if _m 'install|배포|deploy|sync-team|install-to'; then
  actions="${actions}[install 언급] -> install 순서 (kit 편집 -> commit -> sync -> install -> 검증). pre-install-lock.sh 감지. best-practices.md § install 순서.\\n"
fi

# 10. 격한 감정 (미쳐·답답해 죽겠·막혀·안 풀려) -> /brainstorm 또는 /go 자동 발동
if _m '미쳐|미치겠|미치긋|돌아버|답답해 죽|막혀|안 풀|안풀려|막막|어떻게 해야'; then
  actions="${actions}[격한 감정 감지] -> /brainstorm 또는 /go 자동 발동. 혼자 결과 내지 말고 설계 옵션 2~3개 + trade-off + 추천 1개 제시. 사용자 결정 받고 그 다음 실행.\\n"
fi

# 11. 같은 질문 3회+ 반복 (detect-repeat-request.sh 가 similarity_score 측정)
#     여기서는 "모르겠다·이해 안 돼·뭔 소리" 어휘 감지 시 explainlikeim5 트리거
if _m '모르겠|이해.*안|뭔 소리|무슨 말|쉽게|어려워'; then
  actions="${actions}[이해 어려움 감지] -> /explainlikeim5 자동 발동. 5살 톤·일상 비유·고급 용어 X. 긴 essay 금지.\\n"
fi

# 12. 비교·결정 트리거
if _m 'vs |대 |비교|뭐가 좋|어떤 게|차이'; then
  actions="${actions}[비교 요청] -> /compare 자동 (장단점·추천·근거 표).\\n"
fi

# 13. 확신·리스크 질문
if _m '확신|괜찮을|리스크|위험|걱정|문제 없|안전'; then
  actions="${actions}[리스크 질문] -> /devil 자동 (악마의 변호인 · 모든 가정 반론).\\n"
fi

# 14. 복잡·기초부터
if _m '복잡해|처음부터|기초|기본부터|차근차근'; then
  actions="${actions}[단계별 교육 필요] -> /teacher 자동 (단계별 · 이해 확인).\\n"
fi

# 15. 접근 방식·brainstorming
if _m '어떻게 해야|접근 방식|어떻게 할까|방법론|전략'; then
  actions="${actions}[접근 방식 질문] -> /ooda 또는 /brainstorm 자동 (상황 분석·설계 옵션).\\n"
fi

# 16. 피드백·평가 요청
if _m '내 생각|피드백|평가|어때\?|의견'; then
  actions="${actions}[피드백 요청] -> /critique 자동 (냉정 비판 · 칭찬 X).\\n"
fi

# 17. 리서치·조사
if _m '리서치|조사|알아봐|뭐가 있나|후보'; then
  actions="${actions}[리서치] -> /scout 자동 (정찰 · breadth 먼저 · WebSearch 병행).\\n"
fi

# 18. 요약·짧게
if _m '요약|짧게|3줄|한 줄|초간결'; then
  actions="${actions}[요약 요청] -> /brief 자동 (3줄 이내).\\n"
fi

# 19. 발표·보고·PL
if _m '발표|보고|피치|PT|임원|PL|설득'; then
  actions="${actions}[보고/발표] -> /pitch 자동 (설득력 있는 투자자 피치 포맷).\\n"
fi

# 20. AI 티·natural
if _m 'AI 티|사람처럼|자연스럽게|natural|AI 글'; then
  actions="${actions}[AI 티 제거] -> /ghost 자동 (AI 글쓰기 패턴 제거).\\n"
fi

# 21. 상태·대시보드
if _m '상태|지금 어때|현황|대시보드|dashboard'; then
  actions="${actions}[상태 조회] -> /exec_status 자동 (워커·큐·heartbeat·sync 통합).\\n"
fi

# 22. 승인·대기
if _m '승인|approve|대기|pending|waiting'; then
  actions="${actions}[승인 체크] -> /approvals 자동 (대기 task 전부 보기).\\n"
fi

# 23. 비용·토큰
if _m '비용|얼마나 썼|지출|토큰 통계|token stat'; then
  actions="${actions}[비용 조회] -> /token-stats 자동.\\n"
fi

# 24. 완료·마무리
if _m '완료|끝났|다 됐|마무리|끝'; then
  actions="${actions}[완료 처리] -> /validate 자동 (테스트·스크린샷·증거 저장).\\n"
fi

# 25. commit·push·PR 전
if _m 'commit|push|PR|배포 전|릴리스'; then
  actions="${actions}[배포 전] -> /sec-scan 자동 (semgrep·gitleaks·bandit).\\n"
fi

# 26. God mode·알아서
if _m '다 해줘|알아서|god ?mode|모든 것'; then
  actions="${actions}[God mode] -> /godmode 자동 (최대 자율 · 직통 라우팅).\\n"
fi

# 27. 초난도·Mythos
if _m '최고 성능|초난도|어려운 문제|mythos|fable'; then
  actions="${actions}[Mythos] -> /effort-mythos 자동 (Fable 5.1 라우팅 · budget 게이트).\\n"
fi

# 28. 다이어그램·시각화
if _m '다이어그램|그림|시각화|구조도|마인드맵'; then
  actions="${actions}[시각화] -> /arch-auto 자동 (마인드맵·레이어·치트 중 적합).\\n"
fi

# 28-B. 루틴·시스템화·AI 시스템 → ai-system-stages 자동 발동
if _m '루틴|루틴화|시스템화|반복.*자동|자동화 체인|AI 시스템|6단계|자가발전'; then
  actions="${actions}[루틴/시스템화] -> /ai-system-stages 자동 (Prompt→Agent→Orchestration→Automation→Autonomous→Platform · 우리 kit 자가발전 계층 매핑 · WebSearch 실측 Step 0).\\n"
fi

# 29-M. MCP 설치 (top1 · 27회/30d)
if _mi 'MCP|플러그인|install mcp|mcp 설치'; then
  actions="${actions}[MCP 설치 top1] -> /install-mcp 또는 /mcp_dev-install·/mcp_data-install·/mcp_web-install·/mcp_collab-install·/mcp_docs-install·/mcp_media-install 자동.\\n"
fi

# 29-S. 보안·QA (top2 · 13회/30d)
if _mi '보안|security|리뷰|review|테스트|QA|audit'; then
  actions="${actions}[보안·QA top2] -> /security·/sec-scan·/review_qa·/test-gen·/score-task 자동 (최적 하나).\\n"
fi

# 29-X. 10x·효율 (top3 · 9회/30d)
if _mi '10x|최대 효율|ship it|군더더기|빠르게 끝'; then
  actions="${actions}[10x top3] -> /10x 자동 (prose 제거 · 바로 solution · one-shot).\\n"
fi

# 29-D. 문서 생성 (top4 · 8회/30d)
if _mi 'PDF|pdf|엑셀|xlsx|워드|docx|pptx|문서 만들|스프레드'; then
  actions="${actions}[문서 top4] -> /pdf-generate·/excel-make·/word-make·/make-ppt 자동 (유형별).\\n"
fi

# 30~44 전체 그룹 매핑 (사용자 명시: 다 반영)
if _m '빠른 체크|지금 상태|ping|status check'; then
  actions="${actions}[종합 체크] -> /check·/check-agents·/check-services·/claude-status 자동.\\n"
fi
if _m '학습해|저장해|기억해|recall|회상'; then
  actions="${actions}[학습·기억] -> /learn·/recall·/gemini-recap 자동.\\n"
fi
if _m 'install-to|다른 머신|다른 폴더|배포 대상'; then
  actions="${actions}[install-to] -> /install-to <path> 자동 (kit 전수 복사).\\n"
fi
if _m '다이어그램|마인드맵|레이어|치트|artifact|랜딩|포트폴리오'; then
  actions="${actions}[디자인] -> /arch-mindmap·/arch-layered·/arch-cheatsheet·/claude-artifact·/design_web-landing·/design_web-portfolio 자동.\\n"
fi
if _mi 'copilot|cursor|GPT|gpt-|grok|gemini-verify'; then
  actions="${actions}[AI dispatch] -> /copilot-dispatch·/cursor-dispatch·/gpt-dispatch·/grok-dispatch·/gemini-verify 자동.\\n"
fi
if _m '녹음|음성|영상|비디오|이미지|썸네일|쇼츠|복원'; then
  actions="${actions}[미디어] -> /audio-restore·/video-restore·/video-shorts·/video-subtitle·/image-generate·/image-restore 자동.\\n"
fi
if _mi '유튜브|youtube|인스타|instagram|릴스|쇼츠'; then
  actions="${actions}[소셜] -> /yt-upload·/yt-research·/yt-analytics·/ig-upload·/ig-research·/ig-analytics 자동.\\n"
fi
if _m '스케줄|cron|매일|매주|예약|원격|VPS|SSH|tmux'; then
  actions="${actions}[스케줄·원격] -> /exec_scheduler-cron·/exec_scheduler-status·/exec_remote-status·/exec_remote-tmux·/exec_remote-ssh 자동.\\n"
fi
if _m '로컬 모델|오프라인|ollama|llama|gemma|mistral'; then
  actions="${actions}[로컬 모델] -> /exec_offline-model·/exec_offline-setup·/exec_offline-route·/exec_offline-vector 자동.\\n"
fi
if _m '분석해|개선 포인트|기술 추천|아키 분석'; then
  actions="${actions}[분석·개선] -> /analyze-improve 자동.\\n"
fi
if _m '워크스루|투어|안내|처음 쓰|어떻게 쓰'; then
  actions="${actions}[워크스루] -> /walkthrough 자동 (기능 투어).\\n"
fi
if _mi '음성 명령|말로 지시|voice|voice task'; then
  actions="${actions}[음성 명령] -> /voice-task 자동 (STT → task-instruction).\\n"
fi
if _m '회의 녹음|회의록|meeting'; then
  actions="${actions}[회의] -> /meeting 자동 (STT → 요약 → 회의록).\\n"
fi
if _m 'MCP 상태|MCP 체크|MCP 재점검'; then
  actions="${actions}[MCP 상태] -> /mcp_dev-status·/mcp_data-status·/mcp_web-status·/mcp_collab-status·/mcp_docs-status·/mcp_media-status 자동.\\n"
fi

# 29. 수정 지시 -> 증명 체인 강제 (수정 후 자동 pre/post snapshot + 작동 테스트 + 보고)
if _m '수정해|고쳐|바꿔|변경해|고쳐줘|수정 해|바꿔줘'; then
  actions="${actions}[수정 지시] -> 증명 체인 강제 (verify-after-edit-mandatory.md). 5단계: ① pre-snapshot (md5/Read/sqlite SELECT/curl) ② 수정 실행 ③ post-snapshot ④ diff + 작동 테스트 ⑤ 보고 (증거 첨부). '수정했습니다' 만 보고 X.\\n"
fi

# 30. "왜 안 됐어" 재지시 -> 자가 진단 5단계
if _m '왜.*안 됐|왜 안됐|수정했다며|적용 안 됨|적용 안됨|효과 없|안 되어있|안되어있|안 되어 있|실제 안|증명해'; then
  actions="${actions}[재검증 재지시] -> 자가 진단 5단계 (verify-after-edit-mandatory.md): ① 파일 Read 재확인 ② cascade override ③ 캐시·재시작 ④ 엉뚱한 파일 ⑤ 실행 테스트. 원인 1줄 + 수정 + 재검증 결과 첨부.\\n"
fi

# 31. 에러·오류 -> 자동 로그 조회 + 디버깅
if _m '에러|오류|error|exception|traceback|fail|실패'; then
  actions="${actions}[에러 감지] -> recent-error-count·.claude/logs tail 자동 조회 + 원인 분석 + 수정 체인.\\n"
fi

# 32. 성능·느림
if _m '느려|느리|slow|성능|응답 안 와|끊김|렉'; then
  actions="${actions}[성능 저하] -> /performance 자동 (응답시간·메모리·번들·Lighthouse).\\n"
fi

# 33. 원복·revert·rollback
if _m '원복|되돌려|revert|롤백|rollback|undo|돌려놔'; then
  actions="${actions}[원복] -> git revert 또는 .bak restore 자동 (사용자 승인 후).\\n"
fi

# 34. 코드 리뷰
if _m '리뷰해|코드 리뷰|review|PR 리뷰|점검해'; then
  actions="${actions}[리뷰] -> code-reviewer agent 자동 dispatch (격리 · 구조화 반환).\\n"
fi

# 35. 스크린샷·캡처
if _m '스크린샷|캡처|screenshot|화면 찍|screen capture'; then
  actions="${actions}[스크린샷] -> /screenshot 자동 (Playwright headless).\\n"
fi

# 36. 번역
if _m '번역|translate|영어로|한글로|일본어로|중국어로'; then
  actions="${actions}[번역] -> /translate 자동.\\n"
fi

# 37. 회의·녹음·음성 입력
if _m '녹음|음성|회의|meeting|회의록|STT'; then
  actions="${actions}[회의/녹음] -> /meeting·/transcribe 자동 (Whisper STT).\\n"
fi

# 38. 말로·TTS
if _m '말로|읽어줘|speak|TTS|음성 출력'; then
  actions="${actions}[TTS] -> /speak 자동 (edge-tts).\\n"
fi

# 39. 예시·artifact
if _m '예시 보여|artifact|바로 쓸|샘플|즉시 실행'; then
  actions="${actions}[예시] -> /artifacts 자동 (실행 가능 산출물).\\n"
fi

# 40. 데모·mock·가짜 (명시 안 하면 실전 강제)
if _m '데모|mock|가짜|시연용|dummy'; then
  actions="${actions}[목업 트리거] -> 사용자 명시 (목업·mock·demo) 있는지 재확인. 없으면 feedback_no_mock_default 룰 적용 (실전 강제 · DB 연결 요구).\\n"
fi

# 감지된 게 있으면 systemMessage
if [ -n "$actions" ]; then
  cat <<EOF
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[감정-상황 자동 매핑]\\n${actions}\\n★ 매핑 SoT: plugins/exec_orch/skills/user-emotion-auto-response.md\\n★ 개별 감지 hook: detect-deflection.sh (회피), detect-repeat-request.sh (반복), detect-asset-creation.sh (자산 생성)"}}
EOF
fi
exit 0
