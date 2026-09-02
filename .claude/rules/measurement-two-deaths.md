# 계측 두 가지 죽음 룰 (Measurement Two Deaths)

> **근거**: 2026-08-20 postmortem — 계측 두 번 침묵으로 원인 규명 지연. ① 계측이 "가장 느린 단계 뒤" 라 몇 분 지연됨 → 로그 0건 오독. ② 계측이 메모리에만 있어 재기동에 3번 소실. § 4 게이트도 누적 vs 증분 혼동으로 실패 통과.
> **이유**: 계측을 만든 것과 그 계측이 필요한 시점에 말하는 것은 다른 명제다. 시점·보존·비교 축을 함께 봐야 계측이 작동한다.

## 절대 룰

**계측은 세 축을 모두 지켜야 살아있다.** ① 즉시 보고 (시점) ② 파일 append (보존) ③ 증분 비교 (측정 축).

## 세 가지 죽음

### 죽음 1 — 계측이 필요한 시점에 말하지 못했다 (시점)

**원본**:
```js
const [out] = await chrome.scripting.executeScript({ ... __icmAskWeb ... });
//   ↑ 이 함수는 내부에서 waitDone() 으로 답변을 수 분간 기다린다
await report('paste-diag', ...);   // ← 그래서 이 줄이 수 분 뒤에나 돈다
```

첨부는 이미 끝났는데 진단은 "답이 오거나 타임아웃될 때까지" 안 올라왔다.

**처방**:
- 진단은 **관측 직후 즉시 보고**. 답 대기·긴 작업 뒤 X
- content 가 붙인 직후 `chrome.runtime.sendMessage` 로 즉시 → background 는 파일 append
- 원 경로 (답 오면 완전 페이로드) 는 폴백으로 유지

**우리 kit 대응**:
| 상황 | 즉시 보고 |
|---|---|
| PostToolUse hook | 이벤트 발생 직후 log |
| codex-auto 실행 | task-instruction 시작·완료 각 line |
| MCP 호출 | request/response 별도 line |
| watchdog | health check 결과 즉시 write |

### 죽음 2 — 계측이 필요한 때까지 남아 있지 않았다 (보존)

**원본**: 진단이 메모리 (`_diag[2]`) 에만 있었다. `stop_all.bat` → `kill_venv_python.bat` 이 `.venv` python 전부 kill (relay 도 같은 venv). 3서버 재기동 3회 = 진단 3번 소실.

**처방**: `docs/ask_web/diag.log` 에 **append**. 메모리에만 두지 마.

**우리 kit 대응**:
| 잘못된 저장 | 올바른 저장 |
|---|---|
| Python module 전역 dict | `.claude/state/*.json` |
| 프로세스 in-memory list | `.claude/logs/*.log` append |
| Redis (재기동 시 flush) | SQLite `.claude/state/orca.db` |
| `sys.stderr` 만 | `.log` file + stderr |

**필수 파일 로그 대상**:
- watchdog · worker heartbeat
- MCP 호출 result
- approval-gate 상태
- codex/gemini hallucination 검출 (post-verify)
- Ask-Web relay diag (원본 사례)

### 죽음 3 — 계측 축이 잘못됐다 (누적 vs 증분)

**원본** § 4 게이트:
```js
_thumbs = document.querySelectorAll('...figure img, img[alt*="image"]...').length;
if (_thumbs >= _n) break;      // _n = 이번에 붙일 장수
```

`querySelectorAll` = 문서 전체 (누적). `_n` = 이번 장수 (증분).
**두 축을 비교했다.**

| 턴 | 지난 이미지 (누적) | 이번 요청 (증분) | 실제 붙음 | `_thumbs` | 옛 판정 |
|---|---|---|---|---|---|
| 1 | 0 | 2 | 2 | 2 | 통과 ✔ (지난 게 0이라 우연히 맞음) |
| 2 | 2 | 2 | 0 | 2 | 통과 ← 실패인데 |

★ **첫 회만 우연히 맞는다.**

**처방**: 기준선을 미리 찍고 증분으로 판정.
```js
const _baseline = document.querySelectorAll('...').length;  // 시작 스냅샷
// ... 첨부 시도 ...
const _increment = document.querySelectorAll('...').length - _baseline;
if (_increment >= _n) break;
```

**우리 kit 대응**:
| 잘못된 비교 | 올바른 비교 |
|---|---|
| `total_count >= new_count` | `(total_after - total_before) >= new_count` |
| `all_workers.count()` | `new_workers.since(baseline)` |
| `logs.size >= expected` | `logs.appended_since(start)` |
| `db.count >= expected` | `db.count_delta_since(pre_snapshot)` |

## 공통 문장 (원본 § 3-3)

> **장치를 만든 것과 그 장치가 필요할 때 말하는 것은 다른 명제다.**

- 죽음 1 = 필요한 **시점** 에 말하지 못했다
- 죽음 2 = 필요한 **때까지** 남아 있지 않았다
- 죽음 3 = 필요한 **축** 으로 재지 않았다

계측 넣고 「이제 원인 보인다」 라고 보고했는데 그 보고가 세 번 성립하지 않았다.

## 자가 점검 (계측 추가 시)

- [ ] 이 계측은 **관측 직후 즉시** 보고되는가? (답·큰 작업 뒤로 밀리지 않는가)
- [ ] 이 계측은 **재기동 후에도** 살아 있는가? (파일 append 인가)
- [ ] 이 계측은 **증분** 을 재는가? (누적을 다른 축과 비교하지 않는가)
- [ ] 계측 자체 실패 감지 있는가? (계측 침묵 = "괜찮음" 오독 방지)

## 위반 패턴 (안티)

| 패턴 | 위반 |
|---|---|
| 답변·타임아웃 뒤에 진단 보고 | 죽음 1 |
| 메모리 dict/list 에만 저장 | 죽음 2 |
| 재기동 후 로그 0건 = "정상" 판단 | 죽음 2 |
| `count()` = 누적을 기대값 (증분) 과 비교 | 죽음 3 |
| 첫 회만 통과 확인하고 배포 | 죽음 3 (우연히 첫 회만 맞음) |
| 계측 침묵 = "괜찮음" 오독 | 계측 자체 실패 감지 X |

## 관련

- postmortem 원본: `docs/postmortem/2026-08-20-claude-web-attach-6-hypotheses.md`
- `.claude/rules/investigation-discipline.md` — 3원칙 (같은 postmortem)
- `.claude/rules/environment-dependent-bug.md` — 조작자 행동 변수 (같은 postmortem)
- `.claude/rules/failure-mode.md` § 거절·confidence
- CLAUDE.md § 7 D16 (승격)
- memory: [[feedback_measurement_two_deaths]]
