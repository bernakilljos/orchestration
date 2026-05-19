# doc_auto — 문서 자동 갱신

> **AI-Native 파이프라인 3단계 (마지막)**: 코드 + 테스트 + 보안 통과 후 README/CHANGELOG 자동 갱신

## 동작

1. **트리거**: sec_scan PASS 또는 PostToolUse Edit/Write (체인 끝)
2. **diff 분석**: 변경된 함수·클래스·exports 추출
3. **갱신 대상**:
   - `README.md` — 사용 예시·API 섹션
   - `CHANGELOG.md` — Keep a Changelog 포맷
   - `docs/api/<module>.md` — JSDoc/docstring → markdown
   - `CLAUDE.md` — 프로젝트 구조 변경 시
4. **Claude Sonnet 위임** — diff 짧으면 직접, 길면 task-instruction
5. **결과**: PR 또는 직접 commit (사용자 정책)

## 명령

```bash
/doc-update                # 변경된 모든 파일
/doc-update --readme       # README 만
/doc-update --changelog    # CHANGELOG 만
/doc-update --api          # docs/api/ 만
/doc-update --since HEAD~5 # 5 커밋 전부터
```

## 자동 트리거

- `hooks/post-sec-doc.sh` — sec_scan 완료 후
- Stop hook — 세션 종료 시 마지막 diff 일괄 정리

## 의존성

- `exec_orch` (route_dispatch)
- `sec_scan` (PASS 후만 실행)
- Claude Sonnet 4.6 (단가 효율)

## 정책

- 자동 commit X — diff append 후 사용자가 review 후 commit
- 기존 섹션 보존 — 새 내용 추가만 (덮어쓰기 X)
- Korean + English 혼용 X — 프로젝트 기본 언어 따름

## 포맷

### CHANGELOG.md (Keep a Changelog)

```markdown
## [Unreleased] - 2026-05-19

### Added
- test_gen, sec_scan, doc_auto 3 플러그인 (AI-Native 파이프라인)

### Changed
- .claude-plugin/plugin.json 에 doc_ prefix 추가

### Fixed
- (없음)
```

### docs/api/<module>.md (JSDoc/docstring 추출)

```markdown
# <module> API

## class FooBar

### `method(arg1, arg2) -> ReturnType`

설명 (docstring 첫 줄)

**Parameters**:
- `arg1: str` — 설명
- `arg2: int = 0` — 설명

**Returns**: `ReturnType` — 설명

**Raises**: `ValueError` — when ...
```
