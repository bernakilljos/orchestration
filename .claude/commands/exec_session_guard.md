---
description: "토큰 소진·세션 종료 대비 자동 스냅샷"
allowed-tools: Bash, Read, Edit
---

# /exec_session_guard — 세션 가드 허브

## 포함 커맨드
- `/guard-save` — 즉시 스냅샷 저장 (**기본 액션**)

## 자동 동작 (커맨드 불필요)
- Stop / PreCompact / SessionEnd 이벤트 시 훅이 자동 기록
- 저장 위치: `.claude/context-cache/session-snapshot.md`

## 기본 실행
`/guard-save` — 지금 즉시 상태 스냅샷. 토큰 여유 있을 때 방어적으로 호출.
