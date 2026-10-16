---
description: 자동 검증 — 요구사항·git diff·build·test·lint·공통화·영향범위·증거 전수 확인
allowed-tools: Bash, Read, Grep, Glob
---

# /verify — 사용자 재지시 없이 Claude 가 자동 증명

> **근거**: 2026-10-16 사용자 지시 — "내가 '증명해' 라고 안 말해도 Claude 가 자동으로 증명해야 하는 구조로 바꾸는 거죠. /verify 하나로 요구사항 대조 → git diff → build → tests → lint/typecheck → 공통화 확인 → 영향범위 → 증거 출력."

## 발동 흐름 (의무 전부)

### 1. 요구사항 체크리스트 대조
- 사용자 이번 세션 지시 전부 추출 (`.claude/state/sessions.db` · `UserPromptSubmit` 로그)
- 각 지시별 완료 여부 O/X 표
- 누락 1건이라도 있으면 **"검증 FAIL · 요구 N/M"** 보고 (완료 금지)

### 2. git diff 전수 검토
```bash
git status -sb
git diff HEAD --stat
git diff HEAD -- <각 파일> | head -40    # 변경 요지
```
- 요구 외 파일 수정 여부 (Scope 위반 감지)
- 요구 안 한 리팩터·이름 변경·구조 변경 여부

### 3. Build (언어별 자동)
```bash
# Python
python -c "import ast; [ast.parse(open(f).read()) for f in <changed_py_files>]"
python -m py_compile <changed_py_files>

# Node
npm run build     # or pnpm build
# Java
mvn clean compile
# Go
go build ./...
# Rust
cargo build
```
언어 감지: `.claude/state/project-language.json` (language-standards.md § 자동 감지)

### 4. Tests
```bash
# Python
pytest --tb=short -q <관련 test 파일>
# Node
npm test
# Go
go test ./...
# Rust
cargo test
```

### 5. Lint / typecheck
```bash
# Python
ruff check <changed_files>
mypy --strict <changed_files>
# Node
npx eslint <changed_files>
npx tsc --noEmit
```

### 6. 공통화 확인 (디자인 일관성)
```bash
# 공통 컴포넌트 우회 감지
grep -rln "class.*Common\|CommonButton\|CommonModal\|PageHeader\|FormRow" src/
# 새 변경에 유사 패턴 있는데 공통 사용 X 감지

# CSS 중복 감지
# 동일 패턴 (margin·padding·display·flex) 재사용 vs 신규 작성
```

### 7. 영향 범위
```bash
# 변경 파일에서 export/function 변경 → import 하는 다른 파일 리스트
for f in $(git diff --name-only HEAD); do
  base=$(basename "$f" | sed 's/\..*//')
  grep -rln "import.*$base\|from.*$base" --include="*.{py,ts,tsx,js,jsx,go}" src/
done
```

### 8. 증거 출력 (완료 보고 포맷)
```markdown
## /verify 결과

| 축 | 결과 | 증거 |
|---|---|---|
| 요구 체크 | N/M (O/X 표) | 사용자 지시 → 커밋/코드 매핑 |
| git diff | +X -Y lines (N files) | file:line 리스트 |
| build | ✅ or ❌ | 명령 + stdout/stderr |
| tests | X passed · Y failed | pytest 결과 |
| lint | N warnings | ruff/eslint 결과 |
| 공통우회 | N 건 | grep 결과 |
| 영향파일 | N 건 | 의존 그래프 |

## Scope 위반 (범위 외 수정)
<리스트 or "없음">

## 미반영 (요구 체크 X)
<리스트 or "없음">

## 다음 액션
- 모두 PASS → "완료 보고 OK"
- FAIL 1개라도 → "완료 금지 · 자동 재수정 or 사용자 보고"
```

## Stop Hook 통합 (Phase 2)

`.claude/hooks/stop-verify-required.sh` (예정):
- Stop 이벤트 발생 시 자동 `/verify` 실행
- 결과 FAIL 시 Stop 거부 → Claude 재수정 강제
- Evidence Gate · Verification Gate 자동 enforce

## 금기

1. 요구 대조 없이 "완료" 보고 X
2. git diff 안 보고 "변경 없음" 가정 X
3. test 안 돌리고 "작동 OK" 단정 X
4. 공통우회 검사 skip X (디자인 일관성)
5. 영향 범위 모른 채 commit X

## 관련

- CLAUDE.md § 7 D21 (완전본 · 끝까지 한 세트)
- `.claude/rules/verify-after-edit-mandatory.md` (지금 룰 있지만 enforce X — Phase 1 Evidence Gate 로)
- `.claude/rules/screen-verify.md` (화면 검증)
- 사용자 호소 2026-10-16 "내가 확인하라고 안 해도 자동으로"
- Phase 1 Scope Lock + Evidence Gate + Verification Gate (`project_statusline_v3_design.md` · 다음 세션)
