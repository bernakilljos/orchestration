# 운영 grade 파일 관리 룰 (Production File Management)

> **근거**: 2026-09-02 사용자 지적 — "100% 운영이라 운영스럽게 파일 관리 필요 · 1.jpg 2.jpg 무분별 사용 · 현행화 안 됨".
> **이유**: 실전 운영 = 명명·lifecycle·retention·audit·백업·롤백. 아마추어 패턴 (숫자만·copy·final) 은 금지.

## 절대 룰

**모든 파일 생성 = 의미있는 명명 + audit 로그 + lifecycle 정책 + retention 정책.**

## 명명 강제 매트릭스 (금지 → 대체)

| 금지 패턴 | 예 | 대체 |
|---|---|---|
| **순수 숫자** | `1.jpg` `2.png` `01.pdf` | `<의미>-<YYYYMMDD>.jpg` or `<의미>-<카테고리>.jpg` |
| **copy·final·v2·v3** | `report copy.docx` `final_v2.pptx` `report_final_final.xlsx` | 원본명 그대로 · `.bak` 백업 후 덮어쓰기 (feedback_no_version_suffix) |
| **untitled·new·temp** | `untitled.md` `new_file.py` `temp.txt` | 의미있는 이름 필수 |
| **한글 파일명 (선택 예외)** | `보고서.docx` | 실전 운영 산출물 = 한글 허용 (사용자 명시) · 코드·config 는 kebab-case 강제 |
| **공백 포함** | `my file.md` | kebab-case (`my-file.md`) |
| **대문자 시작 (예외)** | `MyPlugin.md` | 소문자 시작 (전통 규약 `CLAUDE.md`·`README.md` 만 예외) |

## Lifecycle 4 단계

```text
[생성] → [사용/현행화] → [아카이브] → [삭제/파기]
   ↓          ↓             ↓            ↓
  audit    freshness      archive/    retention
  로그     체크·갱신      YYYY-MM      만료 삭제
```

## Retention 매트릭스 (파일 유형별)

| 유형 | 경로 pattern | 사용 기간 | 아카이브 후 | 완전 삭제 |
|---|---|---|---|---|
| 실전 산출물 (docx·pptx·pdf) | `docs/**/*` | 무기한 | 90일 후 archive/ | 사용자 명시만 |
| 강의·교재 | `docs/lecture-*.docx` | 무기한 | 180일 후 archive | 사용자 명시만 |
| 백업 파일 | `*.bak` `*.orig` `_backup*` | **3일** | 즉시 archive | **3일 후 자동 삭제** |
| 임시 파일 | `*.tmp` `*.swp` `*~` | 즉시 | X | **즉시 삭제** |
| 로그 | `.claude/logs/*.log` | 14일 | X | **14일 후 자동 삭제** |
| 완료 task | `.claude/tasks/done/*` | 30일 | X | **30일 후 자동 삭제** |
| 이미지 캐시 | `image-cache/*` | 7일 | X | **7일 후 자동 삭제** |
| 세션 스냅샷 | `.claude/context-cache/*` | 최근 5개 | X | 5개 초과 오래된 것 삭제 |
| conversations (DB) | `orca.db.conversations` | **30일** | session_summary 로 압축 | 30일 후 개별 rows 삭제 |
| DB backup | `orca.db.bak.*` | 매일 1개 | 30일 rolling | 30일 후 자동 삭제 |

## Audit Trail (누가 언제 뭐 만들었나)

**`orca.db.file_audit` 테이블 신설**:
```sql
CREATE TABLE file_audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  session_id TEXT,
  action TEXT CHECK(action IN ('create','write','rename','archive','delete')),
  path TEXT NOT NULL,
  size INTEGER,
  hash TEXT,
  actor TEXT,   -- 'claude'|'codex'|'gemini'|'user'|'watchdog'
  reason TEXT
);
```

- PostToolUse Write/Edit hook 이 자동 기록
- 파일 삭제·rename 시 audit 로그 남김
- 사용자 언제든 조회: `SELECT * FROM file_audit WHERE path LIKE ? ORDER BY ts DESC`

## 자동 백업 정책

| 대상 | 백업 방식 |
|---|---|
| 소스 코드 | **git** (기본) |
| 실전 산출물 (docx·pptx·pdf) | 편집 전 `.bak` 자동 생성 (block-version-suffix.sh 확장) |
| DB (orca.db) | 매일 03:00 `.bak.YYYYMMDD` 생성 · 30일 rolling |
| 설정 (settings.json·CLAUDE.md) | git (매 편집 commit 권장) |
| 시크릿 (.env) | git X · 별도 안전 저장소 (사용자 책임) |

## 무분별 파일 감지 · 자동 감지

`.claude/hooks/enforce-file-naming.sh` (PostToolUse Write):
- 새 파일 생성 시 파일명 검사
- 금지 패턴 매치 시 warning + rename 제안
- 실제 rename 은 사용자 승인 후

`.claude/scripts/detect-numbered-files.py` (주 1회):
- 프로젝트 안 순수 숫자 파일명 (1.jpg·01.png) 감지
- 리스트업 + 의미있는 이름 제안 (LLM 활용)

## 현행화 자동 감지 (기존 확장)

- `.claude/rules/artifact-freshness-check.md` (기존) 확장
- OVERDUE 산출물 = SessionStart 시 systemMessage 알림 (이미 있음)
- 신규: **파일 종류별 유통기한 매트릭스 확장** (강의·계약·감사·공시 등)

## 중복·유사 파일 자동 통합

`.claude/scripts/detect-duplicate-files.py` (주 1회):
- md5sum 기반 완전 중복 감지
- 이름 유사도 (Levenshtein) 기반 유사 감지
- 통합 제안 · 사용자 승인 후 실행

## 롤백 정책

| 실수 | 롤백 방법 |
|---|---|
| 파일 삭제 | git · `orca.db.file_audit` 로 hash 조회 · `.bak` 복원 |
| DB row 삭제 | orca.db 매일 백업 · 이전 백업 복원 |
| 설정 파일 손상 | git revert |
| 대량 rename | audit_trail 역순 실행 (rename 이력 저장됨) |

## 금지

1. **순수 숫자 파일명 생성 X** (1.jpg·01.png 등)
2. **copy·final·v2 접미사 X** (feedback_no_version_suffix 정합)
3. **audit_trail 없이 대량 파일 조작 X**
4. **retention 만료 파일 방치 X** (cleanup-pollution.sh 매 SessionStart 자동)
5. **git 밖 산출물 백업 없이 편집 X** (`.bak` 자동)
6. **DB 백업 없이 스키마 변경 X**
7. **사용자 명시 없이 실전 산출물 (docx·pptx) 삭제 X** (아카이브만)

## 관련

- `.claude/rules/file-naming.md` (기존 · 명명 세부)
- `.claude/rules/cleanup-policy.md` (기존 · 정리 세부)
- `.claude/rules/artifact-freshness-check.md` (기존 · 현행화)
- `.claude/rules/conversation-history.md` (2026-09-02 신설 · retention 통합)
- `.claude/hooks/enforce-file-naming.sh` (신설 · PostToolUse Write)
- `.claude/scripts/audit-file-write.py` (신설 · audit trail 기록)
- `orca.db.file_audit` (신설 · audit trail 저장)
- CLAUDE.md § 7 C·E 산출물 명명·파일 정리 조항
