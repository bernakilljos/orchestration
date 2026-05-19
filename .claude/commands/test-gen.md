---
description: "변경된 코드에 대해 pytest/jest 테스트 자동 생성 (Codex 위임)"
allowed-tools: Bash, Read, Write, Edit
---

# /test-gen

코드 파일 → Codex 가 pytest/jest 테스트 케이스 생성.

## 사용

```text
/test-gen <file>          # 특정 파일
/test-gen --batch         # 현재 세션 변경 파일 일괄
/test-gen --diff HEAD~1   # 마지막 commit 기준 변경
```

## 동작

1. 대상 파일 AST 파싱 → 함수·클래스·메서드 추출
2. `task-instruction-test-gen-<hash>.md` 생성:
   - 함수 시그니처
   - docstring/JSDoc
   - 기대 동작 (Claude 가 코드 보고 추론)
3. Codex 큐에 push → 4개 워커 중 1개 픽업
4. 결과 = `tests/test_<module>.py` 또는 `__tests__/<module>.test.ts`
5. PASS → `sec_scan` 트리거 (체인)

## 출력 형식

```python
# tests/test_<module>.py
import pytest
from <module> import <fn>

class Test<Fn>:
    def test_happy_path(self): ...
    def test_edge_case_empty(self): ...
    def test_raises_on_invalid(self): ...
```

## 검증

```bash
python .claude/scripts/route.py --check test_gen
```

세부 로직: `skills/skill-test-generation.md`
