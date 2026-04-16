---
description: "회의 녹음 → 텍스트 변환 → 요약 → 회의록 자동 생성"
allowed-tools: Bash(python:*), Bash(where:*), Write
---

## Context
- Whisper: !`python -c "import whisper; print('OK')" 2>/dev/null || echo 없음`
- 오늘 날짜: !`date /t 2>/dev/null || date +%Y-%m-%d`

## Your task

### Step 1 — STT 변환
입력: `$ARGUMENTS` (음성 파일 경로)

```python
import whisper, os, datetime

model = whisper.load_model("base")
result = model.transcribe("$ARGUMENTS", language="ko")
transcript = result["text"]
```

### Step 2 — Claude가 회의록 작성
변환된 텍스트를 분석해서 아래 형식으로 회의록 작성:

```markdown
# 회의록

**날짜:** YYYY-MM-DD  
**참석자:** (음성에서 추출 가능한 경우)  
**주제:** (내용 기반 자동 추출)

## 안건
1. ...
2. ...

## 논의 내용
(핵심 내용 요약)

## 결정 사항
- [ ] ...
- [ ] ...

## 액션 아이템
| 담당 | 할 일 | 기한 |
|------|-------|------|
| ... | ... | ... |

## 전체 텍스트
(원본 STT 결과)
```

### Step 3 — 저장
- 회의록: `docs/YYYY-MM-DD/meetings/meeting-HHMMSS.md`
- 텍스트 원본: `docs/YYYY-MM-DD/transcripts/meeting-HHMMSS.txt`

### Step 4 — 후속 처리 안내
- `/speak` → 회의록 TTS 읽기
- task-instruction.md 자동 생성 여부 확인 (액션 아이템 기반)
