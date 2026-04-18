# exec_session_guard 플러그인 규칙

## 목적
토큰 소진·컨텍스트 압축·세션 강제 종료 상황에서 작업 상태를 자동 저장.
다음 세션에서 CLAUDE.md의 Resume 로직(state_session RESTORE)이 읽고 이어받음.

## 저장 경로
- 세션 스냅샷: `.claude/context-cache/session-snapshot.md` (기존 경로 재사용)
- 가드 로그: `.claude/context-cache/guard.log` (훅 실행 이력)

## 2단 방어 구조
```
[1단] Stop / PreCompact hook (쉘)
   ↓ 턴 종료·압축 직전마다 자동 실행
   ↓ 타임스탬프·git status·최근 수정 파일 기록
   ↓ Claude 개입 없이 항상 남김 — 토큰 소진으로 끊겨도 안전

[2단] guard_snapshot skill (Claude)
   ↓ 컨텍스트 70% 이상 또는 주요 단계 완료 시
   ↓ 현재 작업·다음 명령·의사결정 풍부하게 기록
   ↓ 1단 기록을 덮어쓰지 않고 병합
```

## 트리거 매트릭스
| 시점 | 실행 주체 | 내용 |
|------|----------|------|
| 매 턴 종료 (Stop) | hook | 최소 메타 |
| PreCompact | hook | 압축 전 백업 |
| SessionEnd | hook | 최종 저장 |
| 컨텍스트 70%+ | Claude skill | 풍부 스냅샷 |
| `/guard-save` 명령 | Claude skill | 즉시 풍부 저장 |
| 파이프라인 단계 완료 | Claude skill | 체크포인트 |

## 금지
- 개인정보·API키·시크릿 기록 금지
- `.claude/context-cache/` 외부 경로에 저장 금지
- 스냅샷 파일을 git에 커밋하지 않음 (.gitignore 확인)

## 복구
세션 시작 시 CLAUDE.md의 Resume 로직이 `state_session` skill → RESTORE 실행.
이 플러그인은 저장만 책임지고 복구는 기존 skill이 담당.
