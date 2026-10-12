"""detect-efficiency.sh 이식 — 여러 단계 지시 감지 -> kit command 하나로 줄이는 제안.

패턴·문구 표는 원본 .sh 에서 기계 추출 (SoT: docs/install/README.md § Section 4).
"""
from __future__ import annotations

from _common import bash_strip, head_bytes, is_loop_prompt_raw, search

HEADER = "[효율화 제안 — 이렇게 하면 줄일 수 있습니다]\n"
FOOTER = "\n★ 상세 카탈로그: docs/install/README.md § Section 4\n★ 사용자 지시가 여러 단계면 위 command 로 통합 제안 — 사용자가 몰라서 놓치지 않도록 (2026-08-12 사용자 강조)"
TABLE = [
    ("PPT|슬라이드|프레젠테이션|발표.*자료|pptx|파워포인트", False, "★ /design_ppt (HTML/CSS -> Playwright -> PPTX - 잘림 방지 + OCR 검증 자동)\n"),
    ("Word|워드|문서.*작성|보고서|docx|python-docx", False, "★ /design_word (python-docx + Mermaid + PDF export)\n"),
    ("Excel|엑셀|스프레드시트|xlsx|openpyxl|Google Sheets", False, "★ /design_excel (openpyxl + 차트 + Google Sheets 연동)\n"),
    ("PDF.*생성|PDF.*만들|PDF.*변환|A4.*PDF|Letter.*PDF", False, "★ /pdf-generate (HTML/CSS -> Playwright -> PDF - A4-Letter-Digital)\n"),
    ("회의.*녹음|회의록|녹음.*텍스트|녹음.*요약|meeting", False, "★ /meeting (녹음 -> Whisper STT -> 요약 -> 회의록 한 번에)\n"),
    ("유튜브|YouTube|영상.*업로드|채널.*분석", False, "★ /yt-upload - /yt-research - /yt-analytics\n"),
    ("인스타|Instagram|Reels|피드|캐러셀|스토리", False, "★ /ig-upload - /ig-research - /ig-analytics (Graph API v22)\n"),
    ("랜딩|랜딩페이지|landing|포트폴리오|portfolio|SEO|메타태그", False, "★ /design_web-landing - /design_web-portfolio - /design_web-seo-meta\n"),
    ("아키텍처|architecture|마인드맵|레이어.*케이크|치트시트|cheatsheet|다이어그램", False, "★ /arch-auto (자동 판단) - /arch-mindmap - /arch-layered - /arch-cheatsheet\n"),
    ("RAG|의미.*검색|semantic search|벡터.*검색|Vector DB|Graph DB|HyDE", False, "★ /rag-naive - /rag-hybrid - /rag-hyde - /rag-graph - /rag-multimodal - /rag-adaptive - /rag-corrective - /rag-agentic (8종 - 상황별)\n"),
    ("코드.*리뷰|보안.*검사|성능.*측정|OWASP|security scan|Lighthouse", False, "★ /review_qa + /security + /performance + /sec-scan (병렬 검증)\n"),
    ("24.?7|원격.*운영|VPS|클라우드.*Claude|Oracle Free|무료.*서버", False, "★ /exec_remote-setup (Oracle Free Tier 4 OCPU-24GB) -> /exec_remote-deploy -> /exec_remote-mobile\n"),
    ("크론|cron|스케줄|매일.*자동|매주.*자동|주기.*실행", False, "★ /exec_scheduler-cron (YAML 선언형) - /exec_scheduler-workflow (DAG)\n"),
    ("영상.*편집|자막.*생성|쇼츠|Shorts|썸네일|영상.*복원", False, "★ /video-shorts - /video-subtitle - /video-thumbnail - /video-restore\n"),
    ("AI.*작곡|음악.*생성|믹싱|마스터링|MIDI|Suno|Udio", False, "★ /music_studio-compose - /music_studio-mix - /music_studio-master\n"),
    ("이미지.*생성|이미지.*복원|초해상도|얼굴.*복원|배경.*제거", False, "★ /image-generate (Pollinations 무료) - /image-restore\n"),
    ("MCP.*설치|Figma|Canva|Gamma|GitHub|Docker|AWS|MongoDB|PostgreSQL|Slack|Notion", False, "★ /mcp_dev - /mcp_data - /mcp_collab - /mcp_web - /mcp_docs - /mcp_media - /plug_all (전체)\n"),
    ("로컬.*LLM|오프라인|Ollama|Llama|Gemma|Mistral|ChromaDB", False, "★ /exec_offline-setup (Ollama + ChromaDB + Phoenix) - /exec_offline-model - /exec_offline-vector\n"),
    ("500줄|1000줄|대량.*코드|긴.*코드|500 lines", False, "★ Codex ×4 병렬 (task-instruction.md -> codex-auto) — 대용량 코드 자동 위임\n"),
    ("멀티AI|여러.*AI|워커.*자동|orchestration|godmode", False, "★ /exec_orch - /godmode - /orcauto-start - /exec_status\n"),
]


def run(ctx):
    if is_loop_prompt_raw(ctx.raw_stripped):  # /loop·배경 알림 제외 (원문 매칭)
        return None
    prompt = bash_strip(head_bytes(ctx.prompt_jq(), 500))
    if not prompt:
        return None
    suggestions = "".join(txt for rx, ic, txt in TABLE if search(rx, prompt, ic))
    if not suggestions:
        return None
    return HEADER + suggestions + FOOTER
