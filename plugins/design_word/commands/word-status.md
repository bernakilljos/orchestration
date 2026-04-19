---
description: "Word 관련 도구 설치 상태 확인"
allowed-tools: Bash(python:*)
---
## Context
- python-docx: !`python -c "import docx; print('OK')" 2>/dev/null || echo 없음`

## Your task
상태 표 출력. 없으면: `pip install python-docx`
