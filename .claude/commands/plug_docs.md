---
description: "문서 처리 MCP 설치 — PDF·DOCX·OCR(Tesseract)"
allowed-tools: Bash(claude:*), Bash(pip:*), Bash(where:*)
---

## Context
- 설치된 MCP: !`claude mcp list 2>/dev/null || echo "(none)"`
- Python: !`python --version 2>/dev/null || echo "없음"`
- tesseract: !`where tesseract 2>/dev/null && echo "설치됨" || echo "없음"`

## Your task

미설치된 것만 설치한다.

```
# PDF parser
claude mcp add pdf -s user -- npx -y @modelcontextprotocol/server-pdf

# DOCX processor
claude mcp add docx -s user -- npx -y docx-mcp-server
```

OCR (Tesseract) — MCP가 아닌 로컬 툴 설치:
```
# Python 있으면 pytesseract 설치
pip install pytesseract pillow

# Windows winget으로 Tesseract 엔진 설치
winget install UB-Mannheim.TesseractOCR
```

결과 보고:

| 도구 | 상태 | 역할 |
|------|------|------|
| pdf (MCP) | 설치됨/실패 | PDF → 텍스트/데이터 |
| docx (MCP) | 설치됨/실패 | 계약서·보고서 파싱 |
| tesseract | 설치됨/없음 | 이미지·스캔 문서 OCR |
