---
description: "README·CHANGELOG·API doc 자동 갱신 (diff 기반 Claude Sonnet 위임)"
allowed-tools: Bash, Read, Edit, Write
---

# /doc-update

코드 변경 → 문서 자동 갱신.

## 사용

```sql
/doc-update                    # 변경된 모든 파일
/doc-update --readme           # README.md 만
/doc-update --changelog        # CHANGELOG.md 만 (Keep a Changelog 포맷)
/doc-update --api              # docs/api/<module>.md 갱신
/doc-update --since HEAD~5     # 5 커밋 전부터의 변경
/doc-update --claude-md        # CLAUDE.md 구조 섹션
```

## 동작

1. `git diff --name-only` 또는 인자 파일 목록
2. 각 파일에서 추출:
   - 새 함수·클래스 (public API)
   - exports (TypeScript/ES module)
   - docstring·JSDoc
3. Claude Sonnet 4.6 위임 (단가 효율):
   - diff 짧으면 (< 100줄) 직접 처리
   - diff 길면 task-instruction.md 생성
4. 기존 문서에 append (덮어쓰기 X)
5. user review 대기 (자동 commit X)

## 출력 예시

```diff
# CHANGELOG.md

## [Unreleased] - 2026-05-19

### Added
+ - test_gen, sec_scan, doc_auto 3 플러그인 (AI-Native 파이프라인)
+ - ai-native-chain.sh — 3단계 연쇄 hook

### Changed
+ - .claude-plugin/plugin.json: doc_ prefix 추가
```

## 검증

```bash
python .claude/scripts/route.py --check doc_auto
```

세부: `skills/skill-doc-automation.md`
