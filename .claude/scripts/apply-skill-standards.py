#!/usr/bin/env python3
"""스킬 표준화 일괄 적용 (PDF Anthropic 가이드 기준)

작업:
  1. plugins/*/skills/*.md 에 frontmatter (name-description) 추가
  2. plugin.json metadata 에 triggers 배열 추가
  3. plugins/*/SPEC.md 에 트러블슈팅 섹션 추가 (없으면)
"""
import json, re, sys
from pathlib import Path

try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

plugins_dir = Path("plugins")

# ─────────────────────────────────────────────
# 1. 스킬 frontmatter 추가
# ─────────────────────────────────────────────
skill_updated = 0
for p in plugins_dir.iterdir():
    if not p.is_dir() or p.name.startswith('_'):
        continue
    skills_dir = p / "skills"
    if not skills_dir.exists():
        continue

    for skill_file in skills_dir.glob("*.md"):
        txt = skill_file.read_text(encoding="utf-8")

        # 이미 frontmatter 있으면 skip
        if txt.startswith("---\n"):
            continue

        skill_name = skill_file.stem  # skill-03-review
        # 제목 추출 (첫 # 또는 스킬 이름 사용)
        first_line = txt.split("\n")[0] if txt else ""
        title = first_line.lstrip("# ").strip() if first_line.startswith("#") else skill_name

        # 본문에서 "목적" 또는 "Purpose" 또는 첫 문장 추출
        body_summary = ""
        for line in txt.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith(">") and not line.startswith("-") and not line.startswith("*"):
                body_summary = line[:150]
                break

        # description = 목적 + 트리거 안내
        desc_lines = []
        if body_summary:
            desc_lines.append(body_summary)
        desc_lines.append(f"사용자가 관련 키워드 언급 시 또는 {p.name} 플러그인 관련 작업 시 활성화.")
        description = " ".join(desc_lines)[:1024]

        # frontmatter 삽입
        fm = f"""---
name: {skill_name}
description: |
  {description}
---

"""
        skill_file.write_text(fm + txt, encoding="utf-8")
        skill_updated += 1

print(f"✓ 스킬 frontmatter 추가: {skill_updated} 파일")

# ─────────────────────────────────────────────
# 2. plugin.json metadata.triggers 추가 (있으면 skip)
# ─────────────────────────────────────────────
# 각 플러그인의 트리거 문구 (display 에서 유추 + 플러그인 용도 기반)
TRIGGERS = {
    "exec_orch":          ["오케스트레이션", "멀티AI", "워커 시작", "codex 실행"],
    "exec_learning":      ["학습", "패턴 저장", "recall", "summarize"],
    "exec_session_guard": ["스냅샷", "세션 저장", "guard-save", "토큰 소진 대비"],
    "exec_voice":         ["음성", "녹음", "STT", "TTS", "회의록", "whisper"],
    "exec_scheduler":     ["크론", "스케줄", "정기 실행", "workflow", "DAG"],
    "exec_offline":       ["로컬 LLM", "Ollama", "오프라인", "$0 AI"],
    "mcp_dev":            ["GitHub", "Docker", "AWS", "Vercel", "개발 MCP"],
    "mcp_collab":         ["Slack", "Notion", "Jira", "Gmail", "협업 MCP"],
    "mcp_data":           ["MySQL", "MongoDB", "BigQuery", "Sheets", "데이터 MCP"],
    "mcp_docs":           ["PDF", "DOCX", "OCR", "문서 처리"],
    "mcp_media":          ["Whisper", "TTS", "FFmpeg", "미디어"],
    "mcp_web":            ["Playwright", "Puppeteer", "크롤링", "웹 자동화"],
    "mcp_social":         ["YouTube API", "Instagram", "TikTok", "소셜"],
    "mcp_queue":          ["Kafka", "RabbitMQ", "Redis", "SQS", "메시지 큐"],
    "design_excel":       ["Excel 생성", "xlsx", "차트", "스프레드시트"],
    "design_ppt":         ["PPT", "슬라이드", "프레젠테이션", "Gamma"],
    "design_word":        ["Word", "docx", "계약서", "보고서"],
    "design_web":         ["랜딩", "웹사이트", "블로그 템플릿", "SEO", "포트폴리오"],
    "design_pdf":         ["PDF 생성", "양식 채우기", "전자서명", "암호화"],
    "design_video":       ["영상 편집", "자막", "쇼츠", "유튜브 썸네일"],
    "cost_youtube":       ["YouTube 수익화", "트렌드 리서치", "업로드", "analytics"],
    "ai_rag":             ["RAG", "임베딩", "벡터DB", "retrieval", "chromadb", "qdrant"],
    "review_qa":          ["코드 리뷰", "보안", "품질", "테스트", "OWASP"],
}

pj_updated = 0
for p in plugins_dir.iterdir():
    if not p.is_dir() or p.name.startswith('_'):
        continue
    pj_path = p / "plugin.json"
    if not pj_path.exists():
        continue
    pj = json.loads(pj_path.read_text(encoding="utf-8"))
    meta = pj.setdefault("metadata", {})
    if "triggers" in meta:
        continue
    meta["triggers"] = TRIGGERS.get(p.name, [p.name])
    pj_path.write_text(json.dumps(pj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pj_updated += 1

print(f"✓ plugin.json triggers 추가: {pj_updated} 파일")

# ─────────────────────────────────────────────
# 3. SPEC.md 트러블슈팅 섹션 추가 (없으면)
# ─────────────────────────────────────────────
TROUBLESHOOT_TEMPLATE = """

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 커맨드 인식 안 됨 | sync 미실행 | `bash .claude/scripts/sync-plugins.sh` |
| 환경변수 누락 | `.env` 미설정 | `.env.example` 복사 후 값 입력 |
| API 호출 실패 | 쿼터-네트워크-토큰 | `scripts/common.sh` 의 retry 로직 확인 |
| 한글 깨짐 | 인코딩 | `.claude/hooks/check-mojibake.sh` 가 차단. UTF-8 로 재저장 |
| 드라이런 실패 | 인자 미지원 | `is_dry_run "$@"` 헬퍼 검사 |

## 참조

- `.claude/rules/skill-design.md` (Anthropic 가이드 적용)
- `.claude/rules/plugin-structure.md`
"""

spec_updated = 0
for p in plugins_dir.iterdir():
    if not p.is_dir() or p.name.startswith('_'):
        continue
    spec_path = p / "SPEC.md"
    if not spec_path.exists():
        continue
    txt = spec_path.read_text(encoding="utf-8")
    if "## 트러블슈팅" in txt:
        continue
    spec_path.write_text(txt.rstrip() + TROUBLESHOOT_TEMPLATE, encoding="utf-8")
    spec_updated += 1

print(f"✓ SPEC.md 트러블슈팅 추가: {spec_updated} 파일")

print("\nDone.")
