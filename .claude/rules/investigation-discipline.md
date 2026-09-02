# 조사 규율 룰 (Investigation Discipline)

> **근거**: 2026-08-20 postmortem — claude.ai 첨부 실패 6가설 헛짚음. 이력 조회를 마지막에 함 · Playwright 새 창으로 재인증 실패 · 코드 추론만 하다 30초 실측이 30분 추론 이김.
> **이유**: 재현 가능한 기록·실물 채널·30초 실측이 있는데 그것을 마지막에 하면 조사 시간이 배로 늘고 사용자가 지친다.

## 절대 룰

**가설 세우기 전에 다음 3가지 먼저 확인.** 이력 · 실물 채널 · 30초 실측.

## 3원칙

### 1. 이력을 먼저 세라

가설 3개를 한 번에 기각할 수 있는 조회가 있으면 그것부터.

| 원본 (postmortem) | 우리 kit 확장 |
|---|---|
| `docs/ask_web/*.json` 12건 세기 = 1분 → 가설 ①②③ 동시 기각 | `.claude/tasks/done/*` · `.claude/state/*.json` · `.claude/logs/*.log` · git log · SWEEP_LOG 먼저 훑기 |

**원칙**: 재현 가능한 기록이 있으면 **가설보다 그것을 먼저 읽는다.**

**실행 순서 표준**:
1. `git log --oneline -20 -- <관련_경로>` (최근 변경 원인 배제)
2. `.claude/logs/<관련>.log` tail (최근 실행 흔적)
3. `.claude/state/*.json` grep (직전 상태)
4. `.claude/tasks/done/` 최근 동종 task 결과 (이전 실행 유사도)
5. **그 다음에** 가설 수립

### 2. 실물에 이미 닿은 채널을 먼저 찾아라

새 채널 (새 창·새 프로세스·새 세션) 열면 새 문제 (재인증·상태 로드·race) 만든다.

| 원본 | 우리 kit 확장 |
|---|---|
| Playwright 새 창 → 재인증 실패 → 이미 붙어 있는 확장이 조사해야 했다 (`dom-probe` 확장) | Claude 안 tool (Bash·Grep·Read) 먼저 · MCP 는 이미 붙어 있는지 확인 · subagent 는 이미 컨텍스트 있는 게 우선 |

**원칙**: 새 채널 만들기 전에 실물에 이미 닿아 있는 채널을 찾는다.

**금지 예시**:
- 이미 열린 Claude Code 세션 있는데 `claude` CLI 별도 실행
- 이미 붙은 MCP 서버 있는데 별도 프로세스 spawn
- 이미 로드된 파일 read 가능한데 Playwright 브라우저 조작
- 이미 있는 Explore agent 결과 무시하고 새 grep 반복

### 3. 30초 실측이 30분 추론을 이긴다

코드 읽기·spec 문서·정황 추리로 결론 짓지 마. 브라우저·bash 한 줄로 실제 재현.

| 원본 | 우리 kit 확장 |
|---|---|
| `new ClipboardEvent('paste', {clipboardData: dt})` Chromium 무시 의심 → 브라우저에서 30초 직접 재현 → 실제 실림 확인 → 가설 기각 | 스크립트 동작 의심 시 `python script.py --dry` 실행 · shell script `bash -x` 로 실행 로그 · Playwright `--headed` 로 육안 |

**원칙**: 30초짜리 실측이 30분짜리 추론을 이긴다.

**실측 도구 매트릭스**:
| 대상 | 30초 실측 명령 |
|---|---|
| Python 스크립트 | `python -c "import sys; sys.path.insert(0,'.'); from mod import fn; print(fn(test_args))"` |
| Bash 스크립트 | `bash -x script.sh 2>&1 \| head -20` |
| API endpoint | `curl -sv <url> 2>&1 \| head -40` |
| DB 쿼리 | `sqlite3 .claude/state/orca.db "<query>"` |
| 브라우저 동작 | Playwright `--headed` 또는 사용자 브라우저 F12 |
| CSS/DOM | 브라우저 F12 콘솔 `document.querySelectorAll('...').length` |

## 관측 후 한 번 더 질문 (§ 2-2 확장)

```text
관측: "요청 2장 · File 2 · 이벤트 O · 신규썸네일 0"
     ↓
     상대가 안 받는다  ← 여기까지만 읽고 멈춘 게 실패
     ↓
     ★ 왜 안 받나?  ← 이 질문을 던져야 진짜 원인 나옴
```

**원칙**: 「A 가 아니다」 는 결론이 아니라 **다음 질문의 시작이다.**

## 위반 패턴 (안티)

| 패턴 | 위반 |
|---|---|
| 이력 조회 없이 가설 나열 | 시간 배 증가 |
| 새 창·새 프로세스·새 세션으로 조사 시작 | 새 문제 만들기 |
| "코드 상 이래야 한다" 로 결론 | 실물 안 봄 |
| 관측 결과 얻고 "A 아니다" 로 끝냄 | 다음 질문 X |
| 6가설 다 헛짚고 사용자가 원인 찾음 | 조사 방법론 결함 |

## 자가 점검 (auto-planner Step 1 통합)

작업 시작 전:
- [ ] 관련 기록 (git log · logs · state · tasks/done) 훑었나?
- [ ] 이미 실물에 닿은 채널이 있는가? (새 채널 만들기 전)
- [ ] 30초 실측 가능한가? (30분 추론 대신)
- [ ] 관측 결과 얻은 뒤 「왜?」 를 던지고 있나?

## 관련

- postmortem 원본: `docs/postmortem/2026-08-20-claude-web-attach-6-hypotheses.md`
- `.claude/rules/environment-dependent-bug.md` — 조작자 행동 변수 (같은 postmortem)
- `.claude/rules/measurement-two-deaths.md` — 계측 시점·보존 (같은 postmortem)
- `.claude/rules/failure-mode.md` § 전수조사 위반 안티패턴
- `.claude/rules/best-practices.md` § 검증 후 보고
- CLAUDE.md § 7 D15~D18 (헌장 승격)
- memory: [[feedback_history_before_hypothesis]]
