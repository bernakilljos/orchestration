---
paths:
  - "docs/SETUP_OTHER_PC.md"
  - "**/ask_web*"
  - "**/ask-web*"
  - ".claude/scripts/lib/repair_sandbox.py"
---
# 다중 세션 격리 룰 (Multi-Session Isolation)

> **전문**: `.claude/rules-ref/multi-session-isolation.md` — 이 규칙이 붙는 파일을 고치기 전에 반드시 Read (사례·매트릭스·이력·근거는 전문에만 있다).
> 2026-11-18 R310: 지시 파일 합계 250K자 > 권장 150K자 경고 해소 — 필수 조항만 여기 남기고 본문은 자동 로딩 밖으로 옮김 (내용 삭제 X).

## 절대 룰

1. **다중 세션 병행 시 `git worktree` 로 물리 폴더 분리** — `git checkout` 만으로 격리 X (같은 폴더 = 다른 세션도 파일 같이 바뀜, 에러 없이).
2. **세션 역할 사전 지정** (개발 / 검증) — 다른 세션이 만지는 파일 건드리지 마.
3. **저장소 경로 ASCII 강제** — 한글·한자 경로 X (인코딩 사고 이력).
4. **커밋 게이트는 CLI 가 쥔다** — Web 답도 Codex 코드도 실측 전 = 미완.

## 금지

1. 같은 폴더에서 두 세션 병행 (worktree 없이) — 조용한 유실
2. 한글·한자 경로에서 git clone / venv / python 실행
3. gitignore 파일 (`.env`·`local_data`) 워크트리에 안 복사한 채 서버 띄우기
4. Web 답을 실측 없이 커밋 (커밋 게이트 원칙)
5. 콜드부팅 15초 안 기다리고 "서버 안 뜬다" 오판
6. Extension `SEL_*` 깨짐 무시 (에코 답 그대로 사용)
7. 배경 탭에서 붙여넣기 발송 (탭 포커스 없이) — File 업로드 무성 실패
8. `document.querySelectorAll(...).length` 누적값을 새 요청 장수 (증분) 와 직접 비교 — 첫 회만 우연히 맞음
9. 진단을 `waitDone()` 답변 뒤에 보고 — 몇 분 지연으로 로그 0건 오독
10. 진단을 메모리 (`_diag[N]`) 에만 저장 — 재기동 시 소실
11. 빌드 토큰을 손으로 적힌 상수로 유지 — 낡은 코드가 최신 토큰 보고 가능
