# Hook: post-edit-test-gen

> **트리거**: PostToolUse · matcher = `Edit|Write`
> **목적**: 코드 파일 변경 시 자동으로 test_gen 큐에 push

## 동작

1. tool_input 에서 file_path 추출
2. 확장자 확인 — `.py` / `.js` / `.ts` / `.tsx` 만 진행
3. skip_extensions (`.md`, `.json`, etc.) 매치 시 즉시 exit 0
4. `.claude/tasks/test-gen-<sha>.md` 생성
5. `.claude/scripts/ai-native-chain.sh test_gen <file>` 호출

## 스크립트

`hooks/post-edit-test-gen.sh` — 60초 timeout, 실패해도 차단 X

## 설정 (`.claude/settings.json`)

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "bash ${CLAUDE_PROJECT_DIR}/plugins/test_gen/hooks/post-edit-test-gen.sh",
        "timeout": 60
      }]
    }]
  }
}
```

## 다음 단계

체인 진행: test_gen → sec_scan → doc_auto
- `.claude/scripts/ai-native-chain.sh` 가 단계 관리
