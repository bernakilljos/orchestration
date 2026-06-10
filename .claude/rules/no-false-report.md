# 거짓 보고 차단 룰 (No False-Report)

> **근거**: CLAUDE.md § 7-25. 사용자 지적 (2026-06-10): "agent 보고 PASS 거짓 — 본문 여전히 깨짐 (`24 꿇룷`·`Rule 꿇룷`). 다른 백업 폴더 확인. 거짓으로 보고하는 경우가 많다".
> **이유**: 자동 도구 PASS = 사용자 만족 보장 X. agent (subagent) 가 자기 결과를 PASS 라고 보고해도 실제 본문은 깨져있을 수 있음. AI 는 보고 직전 raw 직접 확인 의무.

## 절대 룰

**자동 도구·agent 의 "PASS" 보고만으로 사용자에게 보고 X.** 이중 검증 후 보고.

## 이중 검증 흐름

```text
1. 자동 도구 실행 (verify-*.py / smoke-test-*.sh)
2. 결과 raw 출력 직접 Read (단순 exit code 만 보지 마)
3. 산출물 본문 Read → mojibake/깨짐 직접 grep
4. 백업 폴더 (.bak, _backup, _v2, _old, archive/) 도 같은 검증
5. 깨짐 0건 확인 → PASS 보고
6. 깨짐 발견 → FAIL → 자동 재시도 (max 3) → 그래도 안 되면 솔직히 보고
```

## Mojibake 패턴 (직접 grep)

| 패턴 | 의미 |
|---|---|
| `U+FFFD` (replacement char) | UTF-8 디코딩 실패 — 가장 확실한 깨짐 신호 |
| `꿇룷` `꿇` `룷` `꿿` `괓` | 사용자 보고된 실제 깨짐 |
| `?곸` `?쒕` `?대` | EUC-KR ↔ UTF-8 변환 실패 |
| `Ã` `â€` `ï¿½` | UTF-8 → Latin-1 깨짐 |
| `\xc3\x83` `\xc2` | byte sequence 잘못 디코딩 |

검증 도구: `.claude/scripts/verify-no-mojibake.py` (위 6 카테고리 패턴 전수 grep)

## 백업 폴더도 검증 의무

산출물 메인 + 백업 폴더 (`.bak`, `_backup`, `_v2`, `_old`, `archive/`, `_coverage/`) 모두 같은 mojibake 패턴 검사.

예 (위반 사례):
- `docs/ssj/orch-promo.html` ← 메인 검증 OK
- `docs/ssj/orch-promo.html.bak` ← 백업 검증 skip → 사용자가 백업에서 깨짐 발견 = 위반

## Agent 결과 신뢰 정책

| Agent 보고 | 행동 |
|---|---|
| "PASS — 깨짐 0" | 신뢰 X — 직접 raw 확인 |
| "PASS — 깨짐 0 + raw 인용 첨부" | raw 일부 재확인 → 그제야 신뢰 |
| "FAIL" | 신뢰, fix 진행 |
| 단순 exit 0 | 본문 직접 Read |

근거: `.claude/rules/failure-mode.md` § 거절·confidence. agent confidence ≤ 7 = INCONCLUSIVE 처리.

## 거짓 보고 안티 패턴

| 패턴 | 위반 |
|---|---|
| "전부 PASS" + 실제 본문 깨짐 | 거짓 |
| "검증 통과" + raw 인용 없음 | 신뢰 부족 |
| "재시도 3회 후 OK" + 본문 미확인 | 거짓 위험 |
| 백업 폴더 skip + "다 확인했다" | 거짓 |
| agent 결과 그대로 전달 + 직접 검증 X | 책임 회피 |

## 강추 패턴

```bash
# 1. 자동 도구 실행 (메인 + 백업 모두)
python .claude/scripts/verify-no-mojibake.py docs/ssj/

# 2. exit code + raw 모두 확인
RC=$?
[ "$RC" = "0" ] || exit 1

# 3. 백업 파일도 명시 검사
find docs/ssj/ -name "*.bak" -o -name "*_backup*" -o -name "*_v2*" | while read f; do
  python .claude/scripts/verify-no-mojibake.py "$f"
done

# 4. 본문 grep 직접 (강추 패턴)
grep -rE "꿇룷|꿿|괓|점쇙올" docs/ssj/

# 5. 깨짐 0건 확인 후 PASS 보고
```

## 금지

1. **agent PASS 보고만 보고 사용자에게 전달** — 직접 raw 확인 의무
2. **백업 폴더 검증 skip** — 메인만 보고 전체 PASS 라고 X
3. **단순 exit 0 = PASS 가정** — 본문 직접 Read 필수
4. **mojibake 패턴 1개만 검사** — 위 6 카테고리 전부
5. **"검증했다" 만 보고** — 어떻게 검증했는지 명시

## 강제 (4중)

1. CLAUDE.md § 7-25 (금지)
2. 이 룰 (`.claude/rules/no-false-report.md`)
3. `.claude/scripts/verify-no-mojibake.py` (강화 패턴)
4. memory `feedback_no_false_pass_report.md`

## 참조

- `CLAUDE.md § 7-25` (절대 룰)
- `CLAUDE.md § 7-21` (수정·빌드 후 자동 검증) — 정합
- `.claude/rules/failure-mode.md` § 회피·confidence
- `.claude/rules/best-practices.md` § 검증 후 보고
- 메모리: `feedback_no_false_pass_report.md`
