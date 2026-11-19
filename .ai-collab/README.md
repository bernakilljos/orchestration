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
   - 보고서를 올리는 게시 커밋(`.ai-collab/`만 바꾼 커밋)은 그 뒤에 생기므로, GitHub 최신 커밋과 다를 수 있습니다. 게시 커밋은 검토 대상이 아닙니다.
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
- 수정 요청(`changes_requested`), 형식이 없는 파일, 이전 커밋에 대한 승인이면 보고서를 남깁니다.

## 응답 확인 주기 (Claude CLI)

- Claude CLI가 보고서를 push하면 5분마다 `python .claude/scripts/ai-collab-report.py poll`로 `requests/`와 `reviews/`의 새 파일을 확인합니다.
- 새 파일을 읽으면 주기 확인을 끄고 그 내용을 처리합니다. 다음 보고서를 push하면 다시 켭니다.
- 주기 확인은 Claude Code 세션이 열려 있는 동안만 돕니다. 상주 프로세스가 아니며, 세션을 닫으면 멈춥니다.
- 주기 확인 프롬프트는 `[LOOP] `로 시작합니다. 그래야 사용자 요청으로 원장에 쌓이지 않습니다.
- 읽은 파일은 `state.json`의 `seen`에 파일 해시로 기록합니다. 같은 내용은 다시 알리지 않고, 내용이 바뀌면 다시 알립니다.

## 정리 규칙

- 같은 요청, 같은 head 커밋으로는 보고서를 다시 만들지 않습니다.
- 같은 커밋을 명시 승인한(`verdict: approved`) PASS 보고서만 `prune`으로 지웁니다. 내용은 Git 이력과 원장에 남습니다.
- 미완료(PARTIAL·BLOCKED)와 승인 대기 보고서는 남깁니다. 빈 보고서는 만들지 않습니다.
