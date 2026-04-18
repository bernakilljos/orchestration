---
description: "음성 명령 → task-instruction.md 자동 생성 — 말하면 태스크가 만들어짐"
allowed-tools: Bash(python:*), Write
---

## Context
- Whisper: !`python -c "import whisper; print('OK')" 2>/dev/null || echo 없음`
- 현재 태스크: !`ls .claude/tasks/task-*.md 2>/dev/null | wc -l || echo 0`개

## Your task

### Step 1 — 음성 입력 → 텍스트
`$ARGUMENTS` 가 파일 경로이면 Whisper로 변환.
텍스트면 바로 사용.

```python
import whisper, os

inp = "$ARGUMENTS"
if os.path.isfile(inp):
    model = whisper.load_model("base")
    result = model.transcribe(inp, language="ko")
    command_text = result["text"]
else:
    command_text = inp

print(command_text)
```

### Step 2 — Claude가 task-instruction.md 작성
음성 명령 내용을 분석해서 `.claude/tasks/task-instruction.md` 생성:

```markdown
# [음성 명령 기반 태스크]

## Goal
[음성에서 추출한 목표]

## Files
[구현 필요 파일 목록]

## Rules
- 하드코딩 금지
- 기존 파일 전체 재작성 금지
- 상대경로 사용

## Steps
1. [세부 구현 단계]

## Expected Output
[완성물 설명]
```

### Step 3 — 확인
생성된 task-instruction.md 미리보기 출력.
"Codex에 위임할까요?" 확인.

### Step 4 — 워커 시작 (확인 시)
```
start "Codex-Worker-1" cmd /c "cd /d %CD% && codex-auto 4"
```
