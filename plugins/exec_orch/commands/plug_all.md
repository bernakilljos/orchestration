---
description: "전체 플러그인 설치 — 7개 그룹 순차 (각 독립, idempotent)"
allowed-tools: Bash(claude:*)
---

## Context

- 현재 설치 상태: `claude mcp list 2>/dev/null || echo "(목록 없음)"`
- 필수 환경변수: `.env` 확인 필요

## Your task

7개 플러그인 그룹을 **순차 실행**. 각 단계는 **독립적**이므로 실패해도 다음으로 진행.

**설치 그룹 순서**:
1. `/plug_design` — Canva·Figma·Gamma·PowerPoint·Google Slides·Mermaid (내장 MCP 활용)
2. `/plug_dev` — GitHub·Docker·AWS·Vercel·Netlify·공식 MCP
3. `/plug_data` — PostgreSQL·MySQL·BigQuery·Sheets (DB 커넥터)
4. `/plug_web` — Playwright·Fetch (웹 자동화)
5. `/plug_collab` — Slack·Notion·Gmail (OAuth 인증)
6. `/plug_docs` — PDF·DOCX (문서 처리)
7. `/plug_media` — Bash CLI 기반 오디오/비디오

**각 단계별 처리**:

```bash
echo "=== 1⃣ 디자인 MCP ==="
# /plug_design 실행 후 결과 수집

echo "=== 2⃣ 개발 MCP ==="
# /plug_dev 실행 후 결과 수집

echo "=== 3⃣ 데이터 MCP ==="
# /plug_data 실행 후 결과 수집

echo "=== 4⃣ 웹 자동화 ==="
# /plug_web 실행 후 결과 수집

echo "=== 5⃣ 협업 MCP ==="
# /plug_collab 실행 후 결과 수집

echo "=== 6⃣ 문서 처리 ==="
# /plug_docs 실행 후 결과 수집

echo "=== 7⃣ 미디어 MCP ==="
# /plug_media 실행 후 결과 수집
```

## 최종 보고 (요약)

| 순서 | 그룹 | 대상 | 상태 |
|------|------|------|------|
| 1⃣ | 디자인 | Canva·Figma·Gamma·PPT·Slides·Mermaid | 완료/실패 |
| 2⃣ | 개발 | GitHub·Docker·AWS·Vercel·Netlify | 완료/실패 |
| 3⃣ | 데이터 | PostgreSQL·MySQL·BigQuery·Sheets | 완료/실패 |
| 4⃣ | 웹 | Playwright·Fetch | 완료/실패 |
| 5⃣ | 협업 | Slack·Notion·Gmail | 완료/실패 |
| 6⃣ | 문서 | PDF·DOCX | 완료/실패 |
| 7⃣ | 미디어 | 오디오·비디오 처리 | 완료/실패 |

## 주의사항

- 🔐 **인증 필수**: Slack·Notion·Gmail·GitHub는 `.env`에 토큰/키 먼저 설정
- ⏭ **한 단계 실패해도 계속**: 다음 단계로 진행 (idempotent 설계)
- 📋 **상태 확인**: 각 플러그인 install 후 상태 로그 자동 생성
- 🔄 **재시도**: 실패한 항목은 개별 `/plug_*` 커맨드로 재실행
