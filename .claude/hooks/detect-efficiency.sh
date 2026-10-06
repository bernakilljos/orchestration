#!/usr/bin/env bash
# detect-efficiency.sh — UserPromptSubmit hook
# 목적: 사용자 지시 안 여러 단계 감지 -> kit command 하나로 줄이는 제안
# 근거: 2026-08-12 사용자 지적 — "감지해서 이렇게 하면 줄일 수 있습니다"
# 매핑 SoT: docs/install/README.md § Section 4
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

# 효율화 제안 매핑 (사용자 지시 패턴 -> 줄일 수 있는 command)
suggestions=""

# 1. PPT - 슬라이드 - 발표
if _m 'PPT|슬라이드|프레젠테이션|발표.*자료|pptx|파워포인트'; then
  suggestions="${suggestions}★ /design_ppt (HTML/CSS -> Playwright -> PPTX - 잘림 방지 + OCR 검증 자동)\\n"
fi

# 2. Word - 문서 - 보고서
if _m 'Word|워드|문서.*작성|보고서|docx|python-docx'; then
  suggestions="${suggestions}★ /design_word (python-docx + Mermaid + PDF export)\\n"
fi

# 3. Excel - 스프레드시트
if _m 'Excel|엑셀|스프레드시트|xlsx|openpyxl|Google Sheets'; then
  suggestions="${suggestions}★ /design_excel (openpyxl + 차트 + Google Sheets 연동)\\n"
fi

# 4. PDF 생성-변환
if _m 'PDF.*생성|PDF.*만들|PDF.*변환|A4.*PDF|Letter.*PDF'; then
  suggestions="${suggestions}★ /pdf-generate (HTML/CSS -> Playwright -> PDF - A4-Letter-Digital)\\n"
fi

# 5. 회의 녹음 -> 텍스트 -> 요약
if _m '회의.*녹음|회의록|녹음.*텍스트|녹음.*요약|meeting'; then
  suggestions="${suggestions}★ /meeting (녹음 -> Whisper STT -> 요약 -> 회의록 한 번에)\\n"
fi

# 6. 유튜브 업로드-리서치-분석
if _m '유튜브|YouTube|영상.*업로드|채널.*분석'; then
  suggestions="${suggestions}★ /yt-upload - /yt-research - /yt-analytics\\n"
fi

# 7. 인스타 게시-리서치
if _m '인스타|Instagram|Reels|피드|캐러셀|스토리'; then
  suggestions="${suggestions}★ /ig-upload - /ig-research - /ig-analytics (Graph API v22)\\n"
fi

# 8. 랜딩페이지-포트폴리오
if _m '랜딩|랜딩페이지|landing|포트폴리오|portfolio|SEO|메타태그'; then
  suggestions="${suggestions}★ /design_web-landing - /design_web-portfolio - /design_web-seo-meta\\n"
fi

# 9. 아키텍처 다이어그램
if _m '아키텍처|architecture|마인드맵|레이어.*케이크|치트시트|cheatsheet|다이어그램'; then
  suggestions="${suggestions}★ /arch-auto (자동 판단) - /arch-mindmap - /arch-layered - /arch-cheatsheet\\n"
fi

# 10. RAG - 검색-의미 검색
if _m 'RAG|의미.*검색|semantic search|벡터.*검색|Vector DB|Graph DB|HyDE'; then
  suggestions="${suggestions}★ /rag-naive - /rag-hybrid - /rag-hyde - /rag-graph - /rag-multimodal - /rag-adaptive - /rag-corrective - /rag-agentic (8종 - 상황별)\\n"
fi

# 11. 코드 리뷰 - 보안 - 성능 (병렬 가능)
if _m '코드.*리뷰|보안.*검사|성능.*측정|OWASP|security scan|Lighthouse'; then
  suggestions="${suggestions}★ /review_qa + /security + /performance + /sec-scan (병렬 검증)\\n"
fi

# 12. 24/7 원격-VPS-클라우드
if _m '24.?7|원격.*운영|VPS|클라우드.*Claude|Oracle Free|무료.*서버'; then
  suggestions="${suggestions}★ /exec_remote-setup (Oracle Free Tier 4 OCPU-24GB) -> /exec_remote-deploy -> /exec_remote-mobile\\n"
fi

# 13. 크론-스케줄-자동화
if _m '크론|cron|스케줄|매일.*자동|매주.*자동|주기.*실행'; then
  suggestions="${suggestions}★ /exec_scheduler-cron (YAML 선언형) - /exec_scheduler-workflow (DAG)\\n"
fi

# 14. 영상 편집-자막-쇼츠-복원
if _m '영상.*편집|자막.*생성|쇼츠|Shorts|썸네일|영상.*복원'; then
  suggestions="${suggestions}★ /video-shorts - /video-subtitle - /video-thumbnail - /video-restore\\n"
fi

# 15. 음악-작곡-믹싱
if _m 'AI.*작곡|음악.*생성|믹싱|마스터링|MIDI|Suno|Udio'; then
  suggestions="${suggestions}★ /music_studio-compose - /music_studio-mix - /music_studio-master\\n"
fi

# 16. 이미지 생성-복원-초해상도
if _m '이미지.*생성|이미지.*복원|초해상도|얼굴.*복원|배경.*제거'; then
  suggestions="${suggestions}★ /image-generate (Pollinations 무료) - /image-restore\\n"
fi

# 17. MCP 설치 (카테고리 언급)
if _m 'MCP.*설치|Figma|Canva|Gamma|GitHub|Docker|AWS|MongoDB|PostgreSQL|Slack|Notion'; then
  suggestions="${suggestions}★ /mcp_dev - /mcp_data - /mcp_collab - /mcp_web - /mcp_docs - /mcp_media - /plug_all (전체)\\n"
fi

# 18. 로컬 LLM-오프라인
if _m '로컬.*LLM|오프라인|Ollama|Llama|Gemma|Mistral|ChromaDB'; then
  suggestions="${suggestions}★ /exec_offline-setup (Ollama + ChromaDB + Phoenix) - /exec_offline-model - /exec_offline-vector\\n"
fi

# 19. Codex-Gemini 대용량 위임
if _m '500줄|1000줄|대량.*코드|긴.*코드|500 lines'; then
  suggestions="${suggestions}★ Codex ×4 병렬 (task-instruction.md -> codex-auto) — 대용량 코드 자동 위임\\n"
fi

# 20. 오케스트레이션-워커
if _m '멀티AI|여러.*AI|워커.*자동|orchestration|godmode'; then
  suggestions="${suggestions}★ /exec_orch - /godmode - /orcauto-start - /exec_status\\n"
fi

# 감지된 게 있으면 systemMessage
if [ -n "$suggestions" ]; then
  cat <<EOF
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"[효율화 제안 — 이렇게 하면 줄일 수 있습니다]\\n$suggestions\\n★ 상세 카탈로그: docs/install/README.md § Section 4\\n★ 사용자 지시가 여러 단계면 위 command 로 통합 제안 — 사용자가 몰라서 놓치지 않도록 (2026-08-12 사용자 강조)"}}
EOF
fi
exit 0
