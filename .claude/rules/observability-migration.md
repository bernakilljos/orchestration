# Observability + Structured Logging 마이그레이션 가이드

## ✓ 완료: 기초 구성

- **structured_logger.py** — JSON 포맷 · trace_id 상관 · dual output (console/file)
- **trace.py** — OpenTelemetry 영감 · Span 관리 · 순수 Python (외부 의존성 0)
- **common.py** — structured_logger 로 위임 (기존 `log()` 호환)

## 마이그레이션 대상 (top 15 파일)

| 파일 | print() 수 | 상태 |
|---|---|---|
| audit-tokens.py | 12 | 대기 |
| audit-all.py | 12 | 대기 |
| analyze-itcen-ppt.py | 11 | 대기 |
| audit-escape-helpers.py | 8 | 대기 |
| approval-gate.py | 8 | 대기 |
| audit-install-dryrun.py | 6 | 대기 |
| add-itcen-sheets.py | 5 | 대기 |
| audit-mojibake.py | 4 | 대기 |
| audit-hardcoded.py | 4 | 대기 |
| apply-skill-standards.py | 4 | 대기 |
| audit-bat-lines.py | 3 | 대기 |
| artifact-freshness-report.py | 3 | 대기 |
| audit_file_write.py | 2 | 대기 |
| aggregate-rule-adherence.py | 2 | 대기 |
| add-how-to-100.py | 1 | 대기 |

**총 print() 수**: 898개 across 139 파일

## 변환 패턴 3가지

### 패턴 1: 단순 정보성 print → logger.info()

**Before**:
```python
print(f"Processing {file_count} files")
print(f"Total: {total} items")
```

**After**:
```python
from lib.structured_logger import get_logger

logger = get_logger(__name__)
logger.info("Processing files", file_count=file_count)
logger.info("Total items", total=total)
```

### 패턴 2: 구분선·포맷팅 print → logger.info() + 간결

**Before**:
```python
print()
print(f"── {title} " + "─" * 60)
print("─" * 62)
print(f"  Total: {total}")
```

**After**:
```python
logger.info(f"Section: {title}", total=total, section_type="separator")
```

### 패턴 3: 에러 print(stderr) → logger.error()

**Before**:
```python
print(f"ERROR: {error_msg}", file=sys.stderr)
sys.exit(1)
```

**After**:
```python
logger.error("Operation failed", error_msg=error_msg)
sys.exit(1)
```

## 구조화 필드 가이드

**좋은 예**:
```python
logger.info("User login", user_id=42, session_id="abc123", duration_ms=150)
# Output: {"level":"INFO", "message":"User login", "user_id":42, "session_id":"abc123", "duration_ms":150, "timestamp":"..."}
```

**피할 것**:
```python
logger.info(f"User {user_id} login, session {session_id}, took {duration_ms}ms")
# 구조화되지 않음 — 나중에 필드 추출 어려움
```

## Trace ID 활용

**매 script 시작시**:
```python
from lib.structured_logger import get_logger, new_trace_id, set_trace_id
from lib.trace import Tracer

# SessionStart 또는 script 진입점
trace_id = new_trace_id()  # 또는 전달된 trace_id 사용
set_trace_id(trace_id)

# 모든 log() 호출이 자동으로 이 trace_id 포함
logger = get_logger(__name__)
logger.info("Script started", trace_id=trace_id)
```

**Span 기반 추적**:
```python
tracer = Tracer(__name__)

with tracer.span("process_files", file_count=100):
    # 여기서 작동
    for file in files:
        logger.debug("Processing", filename=file)
    # span 자동 종료 (duration_ms 계산)

tracer.save_spans()  # .claude/logs/traces-<trace_id>.json
```

## 성능 vs 가독성

**print() 장점**: 즉시 화면에 표시 (버퍼링 X)
**logger.info() 장점**: 구조화 + 필터링 + 추적

→ 단순 디버깅용 한 줄은 print() 유지 가능. 운영 정보는 logger.

## 마이그레이션 체크리스트 (파일별)

- [ ] Import 추가: `from lib.structured_logger import get_logger`
- [ ] Logger 초기화: `logger = get_logger(__name__)`
- [ ] print() 자리에 logger.info/debug/warning/error
- [ ] 가변 데이터는 **kwargs 로: `logger.info("msg", key=value)`
- [ ] 테스트: 실행 후 `.claude/logs/structured.log` 확인
- [ ] JSON 포맷 확인: `cat .claude/logs/structured.log | python3 -m json.tool`

## 자동 마이그레이션 스크립트 (예정)

```bash
python3 .claude/scripts/lib/migrate-print-to-logger.py <filename>
# Before/after diff 보여줌 (수동 승인)
```

## 관련 규칙

- `.claude/rules/language-standards.md` § Python
- `.claude/rules/consistency.md` (로깅 일관성)
- `.claude/rules/auto-optimization.md` (log rotation + retention)

## 로그 파일 위치

| 파일 | 용도 |
|---|---|
| `.claude/logs/structured.log` | 모든 structured logs (JSON) |
| `.claude/logs/traces-<trace_id>.json` | Span 추적 (OpenTelemetry 호환) |

## 다음 단계

1. **Phase 1** (이번): top 15 파일 converter 테스트
2. **Phase 2**: 자동 마이그레이션 스크립트 작성
3. **Phase 3**: 대량 마이그레이션 + 100% print() 회피
4. **Phase 4**: Honeycomb/Datadog 통합 (JSON 수신 준비 완료)

---

**생성일**: 2026-10-13  
**상태**: ✓ 기초 완료, Phase 1 대기
