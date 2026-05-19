---
name: skill-doc-automation
description: |
  코드 변경 → README/CHANGELOG/API doc 자동 갱신 패턴.
  사용자가 "문서 갱신", "CHANGELOG 추가", "API doc", "AI-Native 3단계" 같은 말을 할 때 활성.
  sec_scan PASS 후 자동 또는 Stop hook 세션 종료 시.
---

# Skill: Doc Automation

## 트리거
- 수동: `/doc-update`
- 자동: hooks/post-sec-doc.sh (sec_scan 완료 후)
- 자동: Stop hook (세션 종료 시 마지막 diff 정리)
- 명시적 요청: "README 업데이트", "CHANGELOG 정리", "문서 자동화"

## 전략

### 1. diff 분석

```bash
git diff --name-only HEAD~1 HEAD
# 또는
git diff --staged --name-only
```

각 파일에서:
- Python: `ast.parse` → FunctionDef / ClassDef / Module-level
- TypeScript: tree-sitter / `tsc --listFiles --emitDeclarationOnly`
- Markdown: skip (또는 frontmatter 만)

### 2. 변경 분류

| 종류 | CHANGELOG 섹션 |
|---|---|
| 새 함수/클래스 | Added |
| 시그니처 변경 | Changed |
| 버그 fix | Fixed |
| 삭제 (deprecated) | Removed |
| 보안 fix | Security |

### 3. Claude Sonnet 위임 패턴

```markdown
# task-instruction-doc-<hash>.md

## Context
- 변경 파일: src/foo.py
- diff: <첨부>
- 기존 CHANGELOG 마지막 entry: ...

## Task
1. diff 에서 public API 변경 추출
2. Keep a Changelog 포맷으로 entry 작성
3. README.md 의 "API" 섹션에 새 함수 추가 (alphabetical order)
4. 기존 entry 덮어쓰기 금지

## Output
- CHANGELOG.md (diff 형식)
- README.md (변경 라인만)
```

### 4. 사용자 review 대기

자동 commit X. diff 만 보여주고 사용자가 확인 후 commit.

## CHANGELOG 포맷 (Keep a Changelog)

```markdown
# Changelog

이 프로젝트의 모든 주요 변경사항이 기록됩니다.
포맷: [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)
버전: [SemVer](https://semver.org/lang/ko/)

## [Unreleased]

### Added
- ...

### Changed
- ...

### Fixed
- ...

## [1.0.0] - 2026-04-19

### Added
- 첫 릴리즈
```

## API doc 포맷

```markdown
# `<module>` API

> 자동 생성 — `<module>.py` docstring/type hints 기반

## Functions

### `function_name(arg1, arg2=default) -> ReturnType`

설명 (docstring 첫 줄).

**Parameters**:
- `arg1: str` — 설명 (docstring `:param arg1:`)
- `arg2: int = 0` — 설명

**Returns**: `ReturnType` — 설명

**Raises**:
- `ValueError` — when 조건

**Example**:
\`\`\`python
result = function_name("foo", arg2=42)
\`\`\`
```

## 금지

- 자동 commit (`git commit -m ...` 직접) — 사용자 review 필수
- 기존 entry 삭제 — append 만
- 모든 변경 보고 — public API 변경만 (내부 helper 변경은 skip)
- 한글 + 영어 혼용 — 프로젝트 기본 언어 따름

## 연결 (chain)

doc_auto = 파이프라인 마지막 단계. 다음 단계 없음.
결과 = `.claude/state/doc-auto-<sha>.md` (사용자 review 용 diff)

## 참조

- Keep a Changelog: https://keepachangelog.com/
- SemVer: https://semver.org/
- `plugins/exec_orch/skills/route_dispatch.md`
