---
name: skill-test-generation
description: |
  코드 변경 후 자동으로 pytest/jest 테스트 케이스 생성하는 패턴.
  사용자가 "테스트 생성", "테스트 자동화", "AI-Native 1단계" 같은 말을 할 때 활성.
  PostToolUse Edit/Write on .py/.js/.ts files 자동 트리거.
---

# Skill: Test Generation

## 트리거
- 수동: `/test-gen <file>`
- 자동: hooks/post-edit-test-gen.sh
- 명시적 요청: "테스트 만들어줘", "이 함수 테스트 케이스 작성"

## 전략 (3단계)

### 1. 정적 분석
```python
import ast
tree = ast.parse(source)
functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
```

### 2. task-instruction 생성
Codex 가 정확한 테스트를 작성하도록 명세:
- 함수 시그니처 (인자 타입·반환 타입)
- 예상 동작 (Claude 가 코드 읽고 추론)
- 엣지 케이스 hint (빈 값·음수·overflow)
- 예외 처리 (raises)

### 3. Codex 위임
```bash
echo "<task>" > .claude/tasks/test-gen-<hash>.md
# orca-auto 가 codex worker 에 라우팅
```

## 출력 위치 규칙

| 코드 파일 | 테스트 위치 |
|---|---|
| `src/<module>.py` | `tests/test_<module>.py` |
| `<module>.py` (root) | `tests/test_<module>.py` |
| `src/<module>.ts` | `__tests__/<module>.test.ts` |
| `src/<comp>.tsx` | `__tests__/<comp>.test.tsx` |

## 우선순위 (시간 분배)

| 코드 종류 | 테스트 비중 |
|---|---|
| 비즈니스 로직 | 70% (해피·엣지·예외) |
| 유틸 헬퍼 | 20% (해피·엣지) |
| I/O 래퍼 | 10% (mock 기반) |

## 금지

- 기존 테스트 파일 덮어쓰기 X — append 또는 신규 클래스 추가
- mock 의존성 무제한 X — 1 테스트 당 mock 3개 이하
- 단순 assertion 만 X — 메시지·context 포함

## 연결 (chain)

테스트 생성 → `review_qa` 또는 `eval_quality` 가 실행 → PASS 시 → `sec_scan` 호출.

체인 스크립트: `.claude/scripts/ai-native-chain.sh`

## 참조

- `plugins/exec_orch/skills/route_dispatch.md`
- `plugins/review_qa/`
- `plugins/eval_quality/`
