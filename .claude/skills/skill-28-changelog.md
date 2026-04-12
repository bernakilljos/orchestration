# Skill 28: Changelog Generator

## 목적
git log에서 CHANGELOG.md를 자동 생성한다. 릴리즈 노트, 버전 히스토리 자동화.

## 트리거
- "changelog", "릴리즈 노트", "변경 이력", "버전 기록"
- 배포 전 자동 제안 (hook-04 pre-deploy)

## 실행 흐름

### 1. git log 파싱
```
커밋 메시지 분류:
  feat:     → ✨ 새 기능
  fix:      → 🐛 버그 수정
  docs:     → 📝 문서
  refactor: → ♻️ 리팩토링
  perf:     → ⚡ 성능 개선
  test:     → ✅ 테스트
  chore:    → 🔧 기타
  BREAKING: → 💥 호환성 변경
```

### 2. 출력 형식
```markdown
# Changelog

## [v3.1] - 2026-04-12

### ✨ 새 기능
- 미디어 화질 개선 도구 추가 (#25)
- AI Handoff 강제 연동 (#24)

### 🐛 버그 수정
- status-push rate limit 수정
- hook heartbeat 에러 해결

### 💥 Breaking Changes
- PAT 하드코딩 제거 — 환경변수 필수
```

### 3. CLI
```bash
# 마지막 태그 이후 변경
python -c "..." > CHANGELOG.md

# 특정 범위
git log v3.0..HEAD --oneline
```

## 출력
- `CHANGELOG.md` (프로젝트 루트)
- `docs/YYYY-MM-DD/release-notes.md`
