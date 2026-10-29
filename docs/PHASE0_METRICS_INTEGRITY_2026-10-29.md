# Phase 0 지표 무결성 수정 (2026-10-29 · 사용자 지적 5건 반영)

> **근거**: 사용자 지적 (687fed0 후속) "지표 무결성·실측 소스 교정부터". Statusline FROZEN · **데이터 계층만** 수정.
> **원칙**: Operating Principles § 9 "미측정 ≠ 정상".

## 수정 매트릭스

| # | 사용자 지적 | 수정 | 상태 |
|---|---|---|---|
| ① | Ledger 완료 집계 completed·deferred·out_of_scope 섞여 44 로 보임 | cmd_status 분리 출력: `완료 44 · 범위외 2 · 보류 0 · 진행중 1` | **VERIFIED** |
| ② | 통제 위반 0 측정 소스 없이 고정 | 5개 전부 `[36m⏳[0m` 미측정 청록 (0 X) | **VERIFIED** |
| ③ | test/build/lint/type ⏳ · 회귀 0 고정 | test/build/lint/type `⏳` (실행 X · dim) · 회귀 `⏳` (미측정 cyan) | **VERIFIED** |
| ④ | READY/HEALTH 공식 검증 | 공식은 올바름 (실 실패만 감점 · 미측정 상한만) · 입력 데이터 교정 필요 | **ANALYZED** |
| ⑤ | 하드코딩 47 · 재발 100% 과거 결함 중복 집계 | `.cursorrules`·`.windsurfrules` 안 **예시 문구가 false positive** 집계 확인 | **ANALYZED · 수정 범위 외** |

## 상세

### ① Ledger 집계 분리 (CHANGE 1)

**이전**:
```python
done = sum(1 for r in requests if r["status"] in ("completed", "deferred", "out_of_scope"))
print(f"=== Request Ledger · {done}/{total} 완료 ===")
```
→ 44/47 로 표시 (범위 외 포함 · "완료" 로 오해 유발)

**현재**:
```python
completed = ...  # == 44
out_of_scope = ...  # == 2
deferred = ...  # == 0
pending = ...  # == 1
print(f"=== Request Ledger · 완료 {completed}/{total} · 범위외 {out_of_scope} · 보류 {deferred} · 진행중 {pending} ===")
```
→ `완료 44/47 · 범위외 2 · 보류 0 · 진행중 1` (명확 분리)

**데이터 계약**:
- `completed` = 증거 포함 PASS 완료
- `out_of_scope` = 다른 프로젝트/세션 인계 (실 인계 증거 X · 사용자 책임)
- `deferred` = 사용자 명시 다음 세션 지연
- `pending` = 진행 중
- 분자 `completed` 만 "완료" (범위 외 ≠ 완료)

### ② 통제 라인 미측정 처리 (CHANGE 1 · statusline_context.py)

**이전** (주석 명시 "측정 소스 없음 · 모두 0"):
```python
control_line = ("범위위반 \x1b[1;32m0\x1b[0m · "    # 초록 0 (정상 운영 오해 유발)
                "임의변경 \x1b[1;32m0\x1b[0m · "
                ...)
```

**현재**:
```python
_unm = "\x1b[36m⏳\x1b[0m"  # 청록 ⏳ (UX-STATUS-COLOR-UNIFIED 미측정)
control_line = (f"범위위반 {_unm} · 임의변경 {_unm} · 승인누락 {_unm} · 추측수정 {_unm} · 검증skip {_unm}")
```

**실측 확인** (statusline 출력):
```text
🛑 통제 │ 범위위반 ⏳ · 임의변경 ⏳ · 승인누락 ⏳ · 추측수정 ⏳ · 검증skip ⏳
```

**Statusline FROZEN 준수**:
- 라벨·구분자·순서·이모지 **모두 유지**
- 색상만 초록(0 고정) → 청록(⏳ 미측정) · UX-STATUS-COLOR-UNIFIED 룰 안 "미측정 청록" 정합

### ③ 검증 라인 회귀 ⏳ (② 와 동일 CHANGE)

**이전**: `회귀 \x1b[1;32m0\x1b[0m` (초록 0 · 측정 소스 없이 고정)
**현재**: `회귀 \x1b[36m⏳\x1b[0m` (청록 ⏳ 미측정)

**test/build/lint/type** 는 `[90m⏳[0m` (회색 dim ⏳) 유지:
- 의미: "이번 세션 실행 X" (측정 미실행 vs 측정 결과 0 구분)

### ④ READY/HEALTH 공식 (ANALYZED)

**_compute_readiness 공식 (올바름 · 수정 불필요)**:
```text
감점 (실 실패만):
  - critical × -15 · error × -5
  - test FAIL × -25 · MCP failed × -3
  - hardcoded CRITICAL × -2 · OVERDUE × -5
감점 X:
  - 재발률 (관측용)
  - 미측정 (상한만 제한)

상한:
  - test ⏳ → cap 85
  - test ❌ → cap 60
  - Ledger 미완료 → cap 50
  - verify ⏳ → ⏳미평가 (A/B/C/D 금지)

등급 (verify ✅ 후만):
  A ≥90 · B+ ≥80 · B ≥70 · C ≥60 · D <60 · F verify=❌
```

**현재 READY 85/100** = test ⏳ 상한 85 정상 · 공식 올바름.

**문제점**: 입력 데이터 `hc_total=47` 가 false positive (⑤) → `crits` 과대 계산 가능. 입력 교정이 필요한 축.

### ⑤ 하드코딩 47 재집계 분석

**실측**:
- `audit-hardcoded.py` 결과: 47 (unchanged · 매번 같음)
- 집계 라인 상위:
  - `.cursorrules:318` match `C:\Users\ja205`
  - `.windsurfrules:318` match `C:\Users\ja205`
  - `.cursorrules:319` match `/home/ja205`
  - ...

**결론**: `.cursorrules`·`.windsurfrules` 는 **룰 문서 안 "하지 말라 예시"** . 즉:
```text
# .cursorrules L318 (금지 예시):
# ❌ C:\Users\ja205\AppData\Roaming\...   (하드코딩 X)
```

이것을 audit-hardcoded.py 가 **실제 하드코딩으로 집계** → **false positive 47 중 대부분**.

**실 운영 결함 수**: 알 수 없음 (false positive 제거 전) · 재집계 필요 (다음 세션 안건)

**조치 (수정 범위 외)**:
- audit-hardcoded.py 가 `.cursorrules`·`.windsurfrules`·주석 "예시" 라인 제외
- OR 결과 집계 시 category 분리 (실 운영 vs 문서 예시)

→ **다음 세션 R?** 로 등재 (지금 수정은 Phase 0 범위 지침 외).

## 회귀 (전수 PASS)

| 테스트 | 결과 |
|---|---|
| golden-test.py | **13/13 PASS** |
| test-h1-h2-h4-e2e.py | **68/68 PASS** |
| test-workflow-full-chain-e2e.py | **51/51 PASS** |
| statusline_context.py 실 출력 | 통제 ⏳ · 회귀 ⏳ 확인 · 디자인 유지 |
| Ledger status 새 집계 | `완료 44/47 · 범위외 2 · 보류 0 · 진행중 1` |

## 다음 세션 안건 (범위 명시)

| 우선 | 작업 | 예상 |
|---|---|---|
| **Phase 1-A** | audit-hardcoded.py false positive 제외 (`.cursorrules`·`.windsurfrules`·주석 예시 라인) | CHANGE 1 |
| **Phase 1-B** | 통제 위반 실 측정 소스 추가 (PreToolUse hook 로 범위위반·임의변경·승인누락·추측수정·검증skip 로그) | NEW 1 (hook) · CHANGE 1 (statusline 데이터 로드) |
| **Phase 1-C** | 재발률 100% 분모 검증 (recurrence 기간·표본) | ANALYZED |
| **Phase 1-D** | 동적 Goal 분해 (`[CMD:]` 마커 없는 자연어 지원) | NEW 1 · CHANGE 1 (supervisor.py decompose_goal) |
| **Phase 1-E** | 01-08 workflow 실 종단 (여러 요청 분해·분기·병렬·결과 통합) | NEW 2-3 · CHANGE 3-5 |
| Phase 2 | Self-Healing 실 연결 (diagnose + sandbox + REPAIRING 자동) | NEW 2 · CHANGE 3-5 |
| Phase 3 | Discovery WebSearch 연결 | NEW 1 · CHANGE 2 |
| Phase 4 | Multi-Agent Capability Registry | NEW 1 (yaml) · CHANGE 3 |

## 예산 (이번 세션)

- NEW 1 (이 문서)
- CHANGE 2 (request-ledger.py · statusline_context.py)
- Ledger R47 완료 (47/48)

## Operating Principles

- Statusline FROZEN: 라벨·구분자·순서·이모지 유지 · 색상만 데이터 계층 교정
- 승인 정책 X · 계정 전환 X
- Operating Principles § 9 "미측정 ≠ 정상" 준수
- 사용자 지적 ⑤ false positive 는 **분석만** · 수정은 범위 외 (다음 세션 승인 후)

## 관련

- `.claude/scripts/request-ledger.py` cmd_status 분리 집계
- `.claude/scripts/statusline_context.py` L1417-1442 통제·검증 라인 데이터 교정
- `.claude/scripts/statusline_context.py` L447 `_compute_readiness` 공식 (수정 X · 올바름)
- `.claude/state/hardcoded-audit.json` 47 (false positive 포함 · 다음 세션 교정)
