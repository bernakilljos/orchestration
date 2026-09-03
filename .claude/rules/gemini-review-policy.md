# Gemini 리뷰 정책

> **근거**: CLAUDE.md § 7-2 (`Gemini 리뷰 자동 채택 금지` — Claude 가 결정).
> **이유**: Gemini 강점 (1M+ 토큰·멀티모달·저단가) vs 약점 (한국어 미묘함·우리 kit 도메인 모름) 분리 운영.

## 절대 룰

**Gemini 리뷰 결과를 코드에 자동 반영 X.** Claude 가 review → 채택 여부 결정 → 사용자 보고.

## 언제 Gemini 쓰나

| 상황 | Gemini? | 이유 |
|---|---|---|
| 1M+ 토큰 리서치 (대량 문서) |  | 컨텍스트 윈도우 |
| 멀티모달 (이미지·PDF·영상) |  | Flash 의 비전 강력 |
| 단순 검증 (코드 < 200k) |  | Haiku 4.5 가 2x 빠름·11x 저렴 |
| 한국어 미묘함 |  | Claude 가 더 정확 |
| 우리 kit 도메인 (CLAUDE.md·rules) |  | Claude 가 컨텍스트 보유 |
| 보안·money·DB 결정 |  | Self-consistency Haiku ×2 + Opus 결정 |

## 호출 전 체크

```bash
# .claude/state/orca.db 에서 quota·budget 확인
python .claude/scripts/route.py --check gemini
# Output: quota_ok=1 budget_ok=1 → 호출 가능
```

## 호출 패턴 (task-instruction 의무 — codex 와 동일)

```bash
gemini exec --task .claude/tasks/task-<slug>.md \
            --model gemini-2.0-flash
```

## 리뷰 결과 처리 (Claude 책임)

1. **Gemini 출력 읽기** — `.claude/tasks/done/task-<slug>-gemini.md`
2. **PASS/FAIL/INCONCLUSIVE 분류**
   - Gemini 가 PASS → Claude 가 spot check (코드 직접 read)
   - Gemini 가 FAIL → 원인 식별 → fix 결정
   - INCONCLUSIVE → 보강 후 재호출 또는 Claude 직접
3. **자동 반영 X** — 사용자에게 "Gemini 가 X 라고 했다. 적용할까?" 보고
4. **승인 후 fix** — 사용자 yes 받은 후만

## 금지

1. **Gemini PASS 받자마자 commit** — 사용자 review 단계 건너뜀
2. **Gemini FAIL 받자마자 코드 변경** — 원인 분석 없음
3. **task-instruction 없이 호출** — 컨텍스트 부족 → 환각
4. **Gemini 결과 raw 보존 X** — 추적성 손실

## 결과 검증 (`post-codex-verify.md` 동일 적용)

Gemini 호출도 pre/post snapshot:
```bash
bash plugins/exec_orch/hooks/post-codex-verify.sh pre <slug>
gemini exec --task .claude/tasks/task-<slug>.md
bash plugins/exec_orch/hooks/post-codex-verify.sh post <slug>
```

변경 0 = `[HALLUCINATION]` 표시. 3회 누적 = 임시 disable.

## RAG 강화 (#12)

Gemini 의 강점 = RAG. `external-trends-sync.sh` 가 매시간 fetch 한 트렌드 +
`references/` 49개 toolkit 을 prompt 에 cite 형식 주입.

```python
# pseudo
context = read("plugins/exec_orch/references/<relevant>.md")
prompt = f"""
You are a senior researcher.
Source 1 (kit toolkit): {context}
Source 2 (recent trends): {read_external_trends()}
Question: {user_input}
Answer with [source: ...] citations.
"""
```

## 참조

- `CLAUDE.md § 7-2` (금지)
- `plugins/exec_orch/skills/route_dispatch.md` (라우팅)
- `plugins/exec_orch/skills/prompt-techniques.md` § RAG (#12)
- `.claude/rules/post-codex-verify.md` (사후 검증)
- `.claude/rules/codex-rules.md` (외부 워커 공통 룰)
