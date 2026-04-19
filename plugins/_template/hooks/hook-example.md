# HOOK-XX — Example Hook

> **이벤트**: PreToolUse | PostToolUse | Stop | SessionEnd
> **매처**: Write|Edit | Bash | (tool name)
> **실행 스크립트**: `hook-xx-yyyy.sh`

## 목적

왜 이 훅이 필요한지.

## 로직

- 입력 (stdin JSON): tool_name, tool_input, tool_response
- 처리: ...
- 출력 (stdout JSON): systemMessage, continue, decision, ...

## 스크립트 예시

```bash
#!/bin/bash
set -euo pipefail
input=$(cat)
# ... logic ...
echo '{"continue": true}'
```
