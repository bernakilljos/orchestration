# 창·테스트 프로세스 예방 룰 (No Visible Windows)

> **근거**: 2026-10-14 사용자 — "다른 섹션에서 테스트했으면 닫아 · 왜 정의 안 되어 있고 전파 안 했어 · ICM 만이 아니라 · 예방을 하라고".
> 세션이 검증하며 서버 기동 bat 을 돌렸고, bat **안의** `start "…" cmd /k …` 줄이 서버 콘솔 창을 열어 둔 채 남겼다.
> 종전 hook 은 명령어 글자만 봐서 bat 안을 못 봤고, «테스트로 띄운 것은 닫는다» 는 규칙이 kit 에 없었다.

## 절대 룰 (모든 프로젝트 · 모든 세션)

1. **보이는 창을 띄우지 않는다.** 테스트·검증·서버 재기동은 창 없이:
   `run_in_background` 로 직접 실행 (`python run.py …`) · `start "" /b …` · PowerShell `-WindowStyle Hidden`.
2. **테스트로 띄운 프로세스는 끝나면 닫는다.** 원래 떠 있던 서버는 원래 방식(서비스·숨김)으로 되돌린다.
3. **스크립트를 돌리기 전에 안에서 창을 여는지 본다.** (`start` 에 `/b` 가 없거나 `cmd /k` 가 있으면 창이 뜬다)
4. 사용자가 창을 원할 때만 `ALLOW_VISIBLE_WINDOW=1` 로 우회한다.

## 강제 (예방 — 띄우기 전에 막는다)

`.claude/hooks/block-visible-windows.sh` (PreToolUse Bash):
- 명령 자체의 `start`(/b·/min 없이) · `cmd /k` · `Start-Process`(Hidden·NoNewWindow 없이) → 차단
- 명령이 실행하는 `.bat`/`.cmd`/`.ps1` **파일 안** 을 읽어 같은 줄이 있으면 → 차단 + `파일:줄` 안내
- 무관 명령은 프로세스 0개로 즉시 통과 · 시험 12/12 (ICM start_all.bat:108 차단 · /b·Hidden·echo 통과 · 우회 통과)

관련: `complete-output.md` (D21 — 사례 하나가 아니라 같은 종류 전체 · 수정 = 검증→commit→push→전파 한 세트)
