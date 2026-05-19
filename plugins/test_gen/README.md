# test_gen — 코드 → 테스트 자동 생성

> **AI-Native 파이프라인 1단계**: 코드 변경 감지 → Codex 가 보고 → pytest/jest/vitest 케이스 자동 생성

## 동작

1. **트리거**: `.py` / `.js` / `.ts` / `.tsx` 파일 PostToolUse Edit/Write
2. **분석**: 변경된 함수·클래스 추출 (AST)
3. **위임**: `.claude/tasks/test-gen-<hash>.md` 생성 → Codex 가 폴링 후 테스트 작성
4. **결과**: `tests/test_<module>.py` 또는 `__tests__/<module>.test.ts` 자동 추가
5. **다음 단계**: `review_qa` 또는 `eval_quality` 가 테스트 실행

## 명령

```bash
/test-gen <file>        # 수동: 특정 파일에 대해 테스트 생성 요청
/test-gen --batch       # 변경된 모든 파일 일괄
```

## 자동 트리거 (hook)

- `hooks/post-edit-test-gen.sh` — Edit/Write PostToolUse 에서 실행
- 코드 파일만 (md/json/yaml/png 스킵 — `ai_native_pipeline.skip_extensions`)

## 의존성

- `exec_orch` — task-instruction 큐 + Codex 라우팅
- Codex worker (×4 병렬)

## 정책

- 테스트 생성 실패 → log 만, 다음 단계 (sec_scan) 진행
- 테스트 통과율 80% 미만 → `auto-planner` 에 경고
- 기존 테스트 파일 있으면 append (덮어쓰기 X)
