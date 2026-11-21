# .ai-collab — Claude CLI ↔ ChatGPT 협업 폴더

사용자 1명이 쓰는 개인 오케스트레이션의 검토 통로입니다. Claude CLI가 개발을 마치고 push하면 보고서가 여기에 올라오고, ChatGPT는 이 폴더와 변경 커밋을 읽고 검토합니다.

| 경로 | 쓰는 쪽 | 내용 |
|---|---|---|
| `reports/<요청ID>.md` | Claude CLI | 작업 보고 (요청 1건 = 파일 1개 · 갱신 시 덮어씀) |
| `requests/<요청ID>.md` | ChatGPT | 검토 후 개선 지시 |
| `reviews/<요청ID>.md` | ChatGPT | 검토 결과와 증거 |
| `state.json` | Claude CLI | 요청별 head 커밋·상태·보고 시각 (중복 분석 방지용) |

## ChatGPT가 볼 순서

1. `state.json`의 `last_head`가 지난번 확인과 같으면 새 작업이 없는 것이므로 아무것도 만들지 않습니다.
   - `last_head`는 마지막 **작업** 커밋입니다.
   - 보고서를 올리는 게시 커밋(`.ai-collab/`만, 또는 그와 함께 `guide.txt` 기록 한 줄만 바꾼 커밋)은 그 뒤에 생기므로, GitHub 최신 커밋과 다를 수 있습니다. 게시 커밋은 검토 대상이 아닙니다.
2. 바뀌었으면 `requests` 항목 중 `head_commit`이 새로 바뀐 요청만 `reports/<요청ID>.md`를 읽습니다.
3. 보고서의 `## 커밋` 목록만 검토합니다.
   - 이 목록에는 **커밋 메시지에 그 요청 ID가 적힌 커밋만** 들어갑니다.
   - 한 커밋이 여러 요청을 처리했다면 그 요청들의 보고서에 함께 나옵니다.
   - 요청 ID가 적힌 커밋이 없으면 범위 전체를 추측해 적지 않습니다. 대신 `commit_link: "unverified"`와 "검증 불가"로 표시하고, 상태는 PARTIAL을 넘지 않습니다.
4. 보고서의 `status`는 원장보다 좋게 적을 수 없습니다. 예를 들어 원장이 PARTIAL이면 PASS로 보고할 수 없습니다.

## 보고서 머리 (YAML)

`request_id` · `repository` · `branch` · `base_commit` · `head_commit` · `status`(PASS·PARTIAL·BLOCKED) · `created_at`(UTC) · `review_required`

## 개선 지시(`requests/`) 형식

```yaml
---
request_id: "R400"
base_commit: "<검토한 head 커밋 SHA>"
---
(지시 내용)
```

- Claude CLI는 `python .claude/scripts/ai-collab-report.py check-requests`로 형식, 기준 커밋, 중복 여부만 확인합니다.
- **GitHub에 올라온 문서는 사용자 승인이 아닙니다.** 실제 실행은 사용자가 대화에서 지시할 때만 하고, 기존 승인 게이트를 그대로 따릅니다.

## 검토 결과(`reviews/`) 형식

```yaml
---
request_id: "R325"
verdict: "approved"          # approved | changes_requested
reviewed_commit: "<검토한 보고서의 head_commit SHA>"
---
(검토 내용·증거)
```

- 보고서를 지우는 조건은 하나뿐입니다. `verdict: approved`이고, `reviewed_commit`이 그 보고서의 `head_commit`과 같아야 합니다.
- 두 값은 **문서 맨 앞의 YAML 머리(`---` 사이)에서만** 읽습니다. 본문 예시나 인용문(`>`)에 쓴 값, 중복 키, 닫는 `---`가 없는 머리는 승인으로 보지 않습니다.
- `reviewed_commit`은 전체 40자 SHA여야 합니다.
- 수정 요청(`changes_requested`), 형식이 없는 파일, 이전 커밋에 대한 승인이면 보고서를 남깁니다.

## 응답 확인 주기 (Claude CLI)

- Claude CLI가 보고서를 push하면 `python .claude/scripts/ai-collab-report.py wait`를 Bash 백그라운드로 실행합니다.
  - 셸이 5분마다 `requests/`와 `reviews/`를 확인하고, 새 파일이 생겼을 때만 끝나서 Claude를 한 번 깨웁니다.
  - 기다리는 동안에는 모델을 호출하지 않습니다. 예전 방식(세션 cron이 5분마다 모델 턴으로 poll)은 하룻밤에 192턴, 모델 호출 397번, 캐시 읽기 약 1.37억 토큰을 "새 요청 없음" 확인에만 썼습니다(R333 실측).
  - Claude Code 세션이 열려 있는 동안만 돕니다. 상주 서비스가 아니며, 세션을 닫으면 멈춥니다.
  - 실환경 첫 종단 확인(R334): ChatGPT push 10:58:58 → `wait` 감지 10:59:30(32초 · 확인 주기 안에서 운이 좋은 경우 · 최악 5분) → 같은 세션의 Claude가 백그라운드 완료 알림으로 10:59:42에 자동으로 깨어나 지시를 읽고 작업 시작. 대기 약 1시간 10분 동안 셸 확인 14회(모델 호출 0) · 그 사이 모델 턴은 사용자가 직접 보낸 질문 1건뿐이었습니다.
  - 한계: 알림은 그 Claude 세션이 열려 있고 다른 턴을 처리 중이 아닐 때 바로 들어갑니다(처리 중이면 그 턴이 끝난 뒤). 세션이 닫히면 감지도 재개도 없습니다.
- 새 파일을 받으면 그 내용을 처리하고, 다음 보고서를 push한 뒤 `wait`를 다시 실행합니다.
- 세션 cron으로 주기 확인을 쓸 때는 프롬프트를 `[LOOP] `로 시작합니다. 그래야 사용자 요청으로 원장에 쌓이지 않습니다.
- 알린 파일은 먼저 `state.json`의 `inflight`(처리 중)에 파일 해시와 시각으로 적습니다. **알렸다고 처리된 것은 아닙니다.**
  - 처리 중인 동안(기본 20분)에는 다음 주기가 같은 파일을 다시 넘기지 않습니다. 같은 요청을 두 번 동시에 처리하지 않기 위해서입니다.
  - 그 시간이 지나도록 처리 확정이 없으면(세션 중단·처리 실패·재시작) 다시 넘깁니다(`"redelivery": true`).
- 처리 확정은 `seen`에 적습니다. 확정된 내용은 다시 알리지 않고, 내용이 바뀌면 다시 알립니다.
  - 지시(`requests/`)는 그 요청 ID를 제목에 적은 작업 커밋을 `report`하면 자동으로 확정됩니다.
  - 검토(`reviews/`)나 커밋 없이 끝낸 건은 검증을 마친 뒤 `python .claude/scripts/ai-collab-report.py ack <요청ID>`로 확정합니다.
  - `ack`는 다음을 모두 만족할 때만 확정합니다(R333).
    - 협업 폴더의 `requests/`·`reviews/` 경로일 것.
    - poll로 전달받은 파일이고, 전달받은 뒤 내용이 바뀌지 않았을 것. 바뀌었으면 새 판을 다시 받아 처리해야 합니다.
    - 처리 완료 증거가 있을 것. 지시는 제목에 그 ID를 적은 작업 커밋이나 원장의 completed 기록이 있어야 하고, 승인 대기나 미완료면 확정하지 않습니다. 검토는 머리에 명시 판정(`approved`·`changes_requested`와 저장소에 있는 40자 커밋)이 있어야 합니다.
  - 이전에 처리해 `handled`에만 남은 지시(R329 등)는 다시 넘기지 않습니다.

## 보고 뒤 남은 일 (R354)

- PARTIAL·BLOCKED 보고 뒤 남은 일은 보고서 본문이 아니라 **원장 하위 항목**에 둡니다: `python .claude/scripts/request-ledger.py item-add <요청ID> "<남은 일>" --owner claude|external`.
  - `claude` = Claude 가 지금 실행할 수 있는 일 · `external` = 사용자 화면 캡처·결정·운영 증거가 있어야 진행 (실행하지 않고 차단 사유로 보고).
  - 외부 증거만 남은 요청은 원장에 BLOCKED 로 기록합니다 (PASS 로 맞추지 않음).
- `python .claude/scripts/ai-collab-report.py queue` 가 열린 항목을 모아 `.claude/state/next-actions.md` 의 collab 블록에 적습니다. `report`·`poll` 이 자동으로 갱신합니다.
  - 세션을 다시 열면(compact·clear·재부팅 포함) 이 큐가 나이와 무관하게 맨 위에 주입되어 [claude] 항목부터 이어서 합니다.
  - 보고된 PARTIAL 을 poll 이 다시 깨우지 않는 규칙(R346 후속 9)은 그대로입니다. 깨우는 대신 큐에 남깁니다.
- 한계: 세션이 닫혀 있는 동안에는 아무것도 실행되지 않습니다. 다음 세션이 열릴 때 이어서 합니다(상주 실행 X).

## 상태 의미 구분 (서로 대신하지 않음)

| 상태 | 뜻 | 기록 위치 |
|---|---|---|
| 수신 (inflight) | poll 이 지시를 전달함 | state.json `inflight` |
| 처리 확정 (seen) | 지시를 처리한 작업 커밋 보고 또는 ack | state.json `seen` |
| push | 원격에 반영됨 | Git |
| CI success | 원격 시험 통과 | GitHub Actions |
| 작업 PASS | 원장 하위 항목 전부 done·na + 검증 | request-ledger.json |
| 독립 검토 승인 | ChatGPT 가 `reviews/<ID>.md` 에 `verdict: approved` 를 씀 | reviews/ |

- `reviews/` 가 비어 있고 `reviewed: false` 인 것은 ChatGPT 쪽이 지금까지 `requests/` 만 쓰고 `reviews/` 문서를 만든 적이 없기 때문입니다 (2026-11-21 확인: `.gitkeep` 외 0건).
  예약된 ChatGPT 검토가 실행돼도 그 결과를 이 폴더에 파일로 쓰지 않으면 저장소에는 남지 않습니다.
- Claude 는 `reviews/` 를 대신 쓰거나 승인으로 간주하지 않습니다. 독립 검토가 필요하면 보고서에 «검토 대기» 로 적고, 다른 실행 가능한 일은 멈추지 않고 계속합니다.

## 정리 규칙

- 같은 요청, 같은 head 커밋으로는 보고서를 다시 만들지 않습니다.
- 같은 커밋을 명시 승인한(`verdict: approved`) PASS 보고서만 `prune`으로 지웁니다. 내용은 Git 이력과 원장에 남습니다.
- 미완료(PARTIAL·BLOCKED)와 승인 대기 보고서는 남깁니다. 빈 보고서는 만들지 않습니다.
