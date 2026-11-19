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
   - 요청 ID가 적힌 커밋이 없을 때만 범위 전체를 적고, 그 사실을 표시합니다.
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

## 정리 규칙

- 같은 요청, 같은 head 커밋으로는 보고서를 다시 만들지 않습니다.
- 검토가 끝난(`reviews/<요청ID>.md`가 있는) PASS 보고서는 `prune`으로 지웁니다. 내용은 Git 이력과 원장에 남습니다.
- 미완료(PARTIAL·BLOCKED)와 승인 대기 보고서는 남깁니다. 빈 보고서는 만들지 않습니다.
