"""detect-user-emotion.sh 이식 — 감정·상황 어휘 감지 -> 매핑된 자동 대응 안내.

패턴·문구 표는 원본 .sh 에서 기계 추출 (SoT: plugins/exec_orch/skills/user-emotion-auto-response.md).
"""
from __future__ import annotations

from _common import bash_strip, head_bytes, is_loop_prompt, search

HEADER = "[감정-상황 자동 매핑]\n"
FOOTER = "\n★ 매핑 SoT: plugins/exec_orch/skills/user-emotion-auto-response.md\n★ 개별 감지 hook: detect-deflection.sh (회피), detect-repeat-request.sh (반복), detect-asset-creation.sh (자산 생성)"
TABLE = [
    ("답답|빨리|빠르게|fast|서둘|급함", False, "[답답 감지] -> /fast 모드 권장 (Opus 4.7/4.8/5 Fast). 짧은 응답 우선.\n"),
    ("짜증|짱나|엉망|대충|장난|매번이래|또 이래|하지말라", False, "[짜증 감지] -> 시스템 결함 신호. 자동 진단 5단계:\n  1) 관련 hook-rule-memory 실측 (grep 아닌 100% Read)\n  2) 놓친 부분 등재 (feedback + hook + rule + CLAUDE.md § 7)\n  3) 감지 시스템 강화\n  4) 원인 사용자에게 짧게 보고\n  5) 반복 방지 게이트 추가\n"),
    ("중복|또 요청|같은 지시|반복", False, "[반복 감지] -> /loop 자동 발동. 감지 hook: detect-repeat-request.sh (별도).\n"),
    ("design.*별로|디자인.*별로|UI.*이상|화면.*못생|design 이 별로|디자인이 별로", False, "[design 불만] -> 관련 command md 자동 수정. plugins/design_*/commands/*.md grep -> 사용자 지적 반영 후 sync-plugins.\n"),
    ("방향.*오해|또.*방향|target.*아니|대상.*아니", False, "[방향 오해] -> direction-first.md 재적용. statusline 확인. 첫 응답 첫 줄 '대상: <path>' 명시.\n"),
    ("하드코딩|하드 경로|박아|hardcod", False, "[하드코딩 지적] -> 자동 grep 감사 (사용자명-Python버전-OS경로-%-상수). 대상 4갈래 (kit/설정/target/글로벌) 중 어디 대상인지 먼저 명시.\n"),
    ("안뒤져|뒤져봐|안봤|다른건|다 확인|전부|모든", False, "[전수조사 지시] -> 100% Read (failure-mode.md § 전수조사 위반). N 파일 = Read N회+. subagent 병렬 (Agent Explore) 강권.\n"),
    ("매번.*까먹|또.*까먹|왜.*까먹|기억.*못", False, "[망각 지적] -> Claude 세션 간 학습 X. 시스템 (hook/statusline/rule/memory) 에 강제 박기. 이번 지적을 hook 감지 -> systemMessage 로 발동하도록 매핑.\n"),
    ("install|배포|deploy|sync-team|install-to", False, "[install 언급] -> install 순서 (kit 편집 -> commit -> sync -> install -> 검증). pre-install-lock.sh 감지. best-practices.md § install 순서.\n"),
    ("미쳐|미치겠|미치긋|돌아버|답답해 죽|막혀|안 풀|안풀려|막막|어떻게 해야", False, "[격한 감정 감지] -> /brainstorm 또는 /go 자동 발동. 혼자 결과 내지 말고 설계 옵션 2~3개 + trade-off + 추천 1개 제시. 사용자 결정 받고 그 다음 실행.\n"),
    ("모르겠|이해.*안|뭔 소리|무슨 말|쉽게|어려워", False, "[이해 어려움 감지] -> /explainlikeim5 자동 발동. 5살 톤·일상 비유·고급 용어 X. 긴 essay 금지.\n"),
    ("vs |대 |비교|뭐가 좋|어떤 게|차이", False, "[비교 요청] -> /compare 자동 (장단점·추천·근거 표).\n"),
    ("확신|괜찮을|리스크|위험|걱정|문제 없|안전", False, "[리스크 질문] -> /devil 자동 (악마의 변호인 · 모든 가정 반론).\n"),
    ("복잡해|처음부터|기초|기본부터|차근차근", False, "[단계별 교육 필요] -> /teacher 자동 (단계별 · 이해 확인).\n"),
    ("어떻게 해야|접근 방식|어떻게 할까|방법론|전략", False, "[접근 방식 질문] -> /ooda 또는 /brainstorm 자동 (상황 분석·설계 옵션).\n"),
    ("내 생각|피드백|평가|어때\\?|의견", False, "[피드백 요청] -> /critique 자동 (냉정 비판 · 칭찬 X).\n"),
    ("리서치|조사|알아봐|뭐가 있나|후보", False, "[리서치] -> /scout 자동 (정찰 · breadth 먼저 · WebSearch 병행).\n"),
    ("요약|짧게|3줄|한 줄|초간결", False, "[요약 요청] -> /brief 자동 (3줄 이내).\n"),
    ("발표|보고|피치|PT|임원|PL|설득", False, "[보고/발표] -> /pitch 자동 (설득력 있는 투자자 피치 포맷).\n"),
    ("AI 티|사람처럼|자연스럽게|natural|AI 글", False, "[AI 티 제거] -> /ghost 자동 (AI 글쓰기 패턴 제거).\n"),
    ("상태|지금 어때|현황|대시보드|dashboard", False, "[상태 조회] -> /exec_status 자동 (워커·큐·heartbeat·sync 통합).\n"),
    ("승인|approve|대기|pending|waiting", False, "[승인 체크] -> /approvals 자동 (대기 task 전부 보기).\n"),
    ("비용|얼마나 썼|지출|토큰 통계|token stat", False, "[비용 조회] -> /token-stats 자동.\n"),
    ("완료|끝났|다 됐|마무리|끝", False, "[완료 처리] -> /validate 자동 (테스트·스크린샷·증거 저장).\n"),
    ("commit|push|PR|배포 전|릴리스", False, "[배포 전] -> /sec-scan 자동 (semgrep·gitleaks·bandit).\n"),
    ("다 해줘|알아서|god ?mode|모든 것", False, "[God mode] -> /godmode 자동 (최대 자율 · 직통 라우팅).\n"),
    ("최고 성능|초난도|어려운 문제|mythos|fable", False, "[Mythos] -> /effort-mythos 자동 (Fable 5.1 라우팅 · budget 게이트).\n"),
    ("다이어그램|그림|시각화|구조도|마인드맵", False, "[시각화] -> /arch-auto 자동 (마인드맵·레이어·치트 중 적합).\n"),
    ("루틴|루틴화|시스템화|반복.*자동|자동화 체인|AI 시스템|6단계|자가발전", False, "[루틴/시스템화] -> /ai-system-stages 자동 (Prompt→Agent→Orchestration→Automation→Autonomous→Platform · 우리 kit 자가발전 계층 매핑 · WebSearch 실측 Step 0).\n"),
    ("MCP|플러그인|install mcp|mcp 설치", True, "[MCP 설치 top1] -> /install-mcp 또는 /mcp_dev-install·/mcp_data-install·/mcp_web-install·/mcp_collab-install·/mcp_docs-install·/mcp_media-install 자동.\n"),
    ("보안|security|리뷰|review|테스트|QA|audit", True, "[보안·QA top2] -> /security·/sec-scan·/review_qa·/test-gen·/score-task 자동 (최적 하나).\n"),
    ("10x|최대 효율|ship it|군더더기|빠르게 끝", True, "[10x top3] -> /10x 자동 (prose 제거 · 바로 solution · one-shot).\n"),
    ("PDF|pdf|엑셀|xlsx|워드|docx|pptx|문서 만들|스프레드", True, "[문서 top4] -> /pdf-generate·/excel-make·/word-make·/make-ppt 자동 (유형별).\n"),
    ("빠른 체크|지금 상태|ping|status check", False, "[종합 체크] -> /check·/check-agents·/check-services·/claude-status 자동.\n"),
    ("학습해|저장해|기억해|recall|회상", False, "[학습·기억] -> /learn·/recall·/gemini-recap 자동.\n"),
    ("install-to|다른 머신|다른 폴더|배포 대상", False, "[install-to] -> /install-to <path> 자동 (kit 전수 복사).\n"),
    ("다이어그램|마인드맵|레이어|치트|artifact|랜딩|포트폴리오", False, "[디자인] -> /arch-mindmap·/arch-layered·/arch-cheatsheet·/claude-artifact·/design_web-landing·/design_web-portfolio 자동.\n"),
    ("copilot|cursor|GPT|gpt-|grok|gemini-verify", True, "[AI dispatch] -> /copilot-dispatch·/cursor-dispatch·/gpt-dispatch·/grok-dispatch·/gemini-verify 자동.\n"),
    ("녹음|음성|영상|비디오|이미지|썸네일|쇼츠|복원", False, "[미디어] -> /audio-restore·/video-restore·/video-shorts·/video-subtitle·/image-generate·/image-restore 자동.\n"),
    ("유튜브|youtube|인스타|instagram|릴스|쇼츠", True, "[소셜] -> /yt-upload·/yt-research·/yt-analytics·/ig-upload·/ig-research·/ig-analytics 자동.\n"),
    ("스케줄|cron|매일|매주|예약|원격|VPS|SSH|tmux", False, "[스케줄·원격] -> /exec_scheduler-cron·/exec_scheduler-status·/exec_remote-status·/exec_remote-tmux·/exec_remote-ssh 자동.\n"),
    ("로컬 모델|오프라인|ollama|llama|gemma|mistral", False, "[로컬 모델] -> /exec_offline-model·/exec_offline-setup·/exec_offline-route·/exec_offline-vector 자동.\n"),
    ("분석해|개선 포인트|기술 추천|아키 분석", False, "[분석·개선] -> /analyze-improve 자동.\n"),
    ("워크스루|투어|안내|처음 쓰|어떻게 쓰", False, "[워크스루] -> /walkthrough 자동 (기능 투어).\n"),
    ("음성 명령|말로 지시|voice|voice task", True, "[음성 명령] -> /voice-task 자동 (STT → task-instruction).\n"),
    ("회의 녹음|회의록|meeting", False, "[회의] -> /meeting 자동 (STT → 요약 → 회의록).\n"),
    ("MCP 상태|MCP 체크|MCP 재점검", False, "[MCP 상태] -> /mcp_dev-status·/mcp_data-status·/mcp_web-status·/mcp_collab-status·/mcp_docs-status·/mcp_media-status 자동.\n"),
    ("수정해|고쳐|바꿔|변경해|고쳐줘|수정 해|바꿔줘", False, "[수정 지시] -> 증명 체인 강제 (verify-after-edit-mandatory.md). 5단계: ① pre-snapshot (md5/Read/sqlite SELECT/curl) ② 수정 실행 ③ post-snapshot ④ diff + 작동 테스트 ⑤ 보고 (증거 첨부). '수정했습니다' 만 보고 X.\n"),
    ("왜.*안 됐|왜 안됐|수정했다며|적용 안 됨|적용 안됨|효과 없|안 되어있|안되어있|안 되어 있|실제 안|증명해", False, "[재검증 재지시] -> 자가 진단 5단계 (verify-after-edit-mandatory.md): ① 파일 Read 재확인 ② cascade override ③ 캐시·재시작 ④ 엉뚱한 파일 ⑤ 실행 테스트. 원인 1줄 + 수정 + 재검증 결과 첨부.\n"),
    ("에러|오류|error|exception|traceback|fail|실패", False, "[에러 감지] -> recent-error-count·.claude/logs tail 자동 조회 + 원인 분석 + 수정 체인.\n"),
    ("느려|느리|slow|성능|응답 안 와|끊김|렉", False, "[성능 저하] -> /performance 자동 (응답시간·메모리·번들·Lighthouse).\n"),
    ("원복|되돌려|revert|롤백|rollback|undo|돌려놔", False, "[원복] -> git revert 또는 .bak restore 자동 (사용자 승인 후).\n"),
    ("리뷰해|코드 리뷰|review|PR 리뷰|점검해", False, "[리뷰] -> code-reviewer agent 자동 dispatch (격리 · 구조화 반환).\n"),
    ("스크린샷|캡처|screenshot|화면 찍|screen capture", False, "[스크린샷] -> /screenshot 자동 (Playwright headless).\n"),
    ("번역|translate|영어로|한글로|일본어로|중국어로", False, "[번역] -> /translate 자동.\n"),
    ("녹음|음성|회의|meeting|회의록|STT", False, "[회의/녹음] -> /meeting·/transcribe 자동 (Whisper STT).\n"),
    ("말로|읽어줘|speak|TTS|음성 출력", False, "[TTS] -> /speak 자동 (edge-tts).\n"),
    ("예시 보여|artifact|바로 쓸|샘플|즉시 실행", False, "[예시] -> /artifacts 자동 (실행 가능 산출물).\n"),
    ("데모|mock|가짜|시연용|dummy", False, "[목업 트리거] -> 사용자 명시 (목업·mock·demo) 있는지 재확인. 없으면 feedback_no_mock_default 룰 적용 (실전 강제 · DB 연결 요구).\n"),
]


def run(ctx):
    prompt = bash_strip(head_bytes(ctx.prompt_jq(), 500))
    if not prompt or is_loop_prompt(prompt):  # /loop·배경 알림 제외
        return None
    actions = "".join(txt for rx, ic, txt in TABLE if search(rx, prompt, ic))
    if not actions:
        return None
    return HEADER + actions + FOOTER
