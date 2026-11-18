---
paths:
  - "docs/**"
  - ".claude/scripts/cleanup*"
  - ".claude/config/retention*"
  - ".claude/scripts/audit_file_write.py"
---
# 운영 grade 파일 관리 룰 (Production File Management)

> **전문**: `.claude/rules-ref/production-file-management.md` — 이 규칙이 붙는 파일을 고치기 전에 반드시 Read (사례·매트릭스·이력·근거는 전문에만 있다).
> 2026-11-18 R310: 지시 파일 합계 250K자 > 권장 150K자 경고 해소 — 필수 조항만 여기 남기고 본문은 자동 로딩 밖으로 옮김 (내용 삭제 X).

## 절대 룰

**모든 파일 생성 = 의미있는 명명 + audit 로그 + lifecycle 정책 + retention 정책.**

## 금지

1. **순수 숫자 파일명 생성 X** (1.jpg·01.png 등)
2. **copy·final·v2 접미사 X** (feedback_no_version_suffix 정합)
3. **audit_trail 없이 대량 파일 조작 X**
4. **retention 만료 파일 방치 X** (cleanup-pollution.sh 매 SessionStart 자동)
5. **git 밖 산출물 백업 없이 편집 X** (`.bak` 자동)
6. **DB 백업 없이 스키마 변경 X**
7. **사용자 명시 없이 실전 산출물 (docx·pptx) 삭제 X** (아카이브만)
