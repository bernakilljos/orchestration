---
description: "문서처리 MCP·도구 설치 — PDF(MCP)·DOCX·OCR(Tesseract)"
allowed-tools: Bash(claude:*), Bash(pip:*), Bash(where:*), Bash(npm:*), Bash(winget:*)
---

## Context
- 설치된 MCP: !`claude mcp list 2>/dev/null || echo "(none)"`
- Python: !`python --version 2>/dev/null || echo "없음"`
- Node.js: !`node --version 2>/dev/null || echo "없음"`
- tesseract: !`where tesseract 2>/dev/null && echo "설치됨" || echo "없음"`

## Your task

미설치된 것만 설치한다.

### 1. PDF MCP (공식, 검증됨)
```bash
claude mcp add pdf -s user -- npx -y @modelcontextprotocol/server-pdf
```
- 패키지: `@modelcontextprotocol/server-pdf` v1.7.0 (공식)
- 기능: PDF → 텍스트/메타데이터 추출

### 2. DOCX 처리 (2가지 선택)
**옵션 A: 추천 — Safe Docx (추적 변경·이미지 지원)**
```bash
npm install -g @usejunior/docx-mcp
claude mcp add docx -s user -- npx -y @usejunior/docx-mcp
```

**옵션 B: 경량 — Basic DOCX**
```bash
npm install -g @docx-mcp/docx-mcp
claude mcp add docx -s user -- npx -y @docx-mcp/docx-mcp
```

또는 MCP 없이 Python 직접 사용:
```bash
pip install python-docx
python -c "from docx import Document; doc = Document('file.docx'); print(doc.core_properties.title)"
```

### 3. OCR (Tesseract) — 2가지 경로

**경로 A: MCP 사용 (권장)**
```bash
npm install -g @infrastellar/tesseract-mcp
claude mcp add tesseract -s user -- npx -y @infrastellar/tesseract-mcp
```
- 패키지: `@infrastellar/tesseract-mcp` v0.1.3

**경로 B: 로컬 CLI + Python (MCP 불필요)**
```bash
# Windows: Tesseract 바이너리 설치
winget install UB-Mannheim.TesseractOCR

# Python 래퍼 설치
pip install pytesseract pillow

# 테스트
python -c "import pytesseract; print(pytesseract.pytesseract.get_tesseract_version())"
```

---

## 결과 보고

| 도구 | 선택 | 상태 | 역할 |
|------|------|------|------|
| pdf | MCP | 설치됨/실패 | PDF → 텍스트/메타데이터 |
| docx | MCP(A) / MCP(B) / Bash | 설치됨/실패 | Word 문서 파싱 |
| tesseract | MCP / Bash+Python | 설치됨/실패 | 스캔·이미지 OCR |

---

## 팁

- **MCP vs Bash**: MCP = Claude 문맥 통합, Bash = 직접 제어. 팀 선호에 따라 선택.
- **한글 OCR**: Tesseract 바이너리 설치 시 한국어 모델 자동 포함.
- **대용량 PDF**: `@modelcontextprotocol/server-pdf` 는 스트리밍 지원.
