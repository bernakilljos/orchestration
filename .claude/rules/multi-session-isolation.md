# 다중 세션 격리 룰 (Multi-Session Isolation)

> **근거**: 2026-08-13 `docs/SETUP_OTHER_PC.md` 실전 검증 패턴. 두 세션 (개발·검증) 이 같은 폴더에서 같은 파일 편집 → **조용한 유실** (에러도 안 남).
> **이유**: 세션끼리는 실시간으로 서로를 못 봄. 겹침 방지는 **범위 분리** 뿐. 논리 브랜치 (`git checkout`) 만으로는 부족 — 물리 폴더 분리 필요.

## 절대 룰

1. **다중 세션 병행 시 `git worktree` 로 물리 폴더 분리** — `git checkout` 만으로 격리 X (같은 폴더 = 다른 세션도 파일 같이 바뀜, 에러 없이).
2. **세션 역할 사전 지정** (개발 / 검증) — 다른 세션이 만지는 파일 건드리지 마.
3. **저장소 경로 ASCII 강제** — 한글·한자 경로 X (인코딩 사고 이력).
4. **커밋 게이트는 CLI 가 쥔다** — Web 답도 Codex 코드도 실측 전 = 미완.

## 세션 역할 분리 매트릭스

| | 검증 세션 | 개발 세션 |
|---|---|---|
| 폴더 | `<repo>` (release/main branch) | `<repo>-dev` (worktree · dev branch) |
| 루프 | CLI ↔ Web 왕복 (판정) | CLI ↔ Codex 왕복 (구현) |
| 커밋 | 검증 통과분만 | Codex 산출물 |
| 병합 방향 | 개발 dev → 검증 phase → merge → 재확인 | — |

## Git worktree 표준 흐름

```bash
# 개발 세션 부팅 시
git worktree add <repo>-dev -b dev
cd <repo>-dev

# 나중에 정리
git worktree remove <repo>-dev
git branch -d dev  # merge 후에만
```

- 새 폴더 = 새 워킹 트리 (물리적으로 안 겹침)
- `.env` · `local_data/` · gitignore 대상은 **워크트리에 안 따라옴** → 수동 복사
- 포트 (예: 9077~9079 제품 서버) 는 하나만 bind 가능 → 한쪽 세션은 `.env` 에서 포트 오프셋

## ASCII 경로 강제

| ❌ 금지 | ✅ 허용 |
|---|---|
| `C:\프로젝트\...` | `C:\pjt\...` |
| `C:\사용자\...\Documents\` | `%USERPROFILE%\Documents\` |
| `~/문서/repo` | `~/docs/repo` |

**Why**: Windows / PowerShell / Python encoding 사고 다발. 특히 `subprocess`·`git`·`python.exe` 조합에서 cp949 ↔ utf-8 변환 실패.

**검증 grep**:
```bash
git config --get-all safe.directory | grep -P '[가-힣]|[一-龯]'
find . -name '*.env' -exec grep -l '[가-힣]' {} \;
```

## Ask-Web Relay 구체 구현 (CLI ↔ Web 자동화)

기존 `feedback_web_cli_dialogue.md` 의 "Chrome Extension 필요" 를 **구체화**:

### 아키텍처

```text
CLI (Claude Code)
  └─→ relay.py ask "<question>"       (127.0.0.1:9080 POST)
       └─→ SQLite queue (.claude/state/ask-web/)
            └─→ Extension content.js polls
                 └─→ claude.ai develop tab 자동 입력 + submit
                      └─→ 답변 회수 → relay.py answer <id>
```

### 포트 예약

| 포트 | 용도 | 비고 |
|---|---|---|
| 9080 | ask-web relay | 로컬 전용 (127.0.0.1) |
| 9077~9079 | 제품 서버 (프로젝트별) | 건드리지 마 |

### Extension 로드 (Edge / Chrome 공통 · manifest v3)

1. `edge://extensions` 또는 `chrome://extensions`
2. 개발자 모드 ON
3. 「압축을 풀린 항목 로드」→ 확장 소스 폴더 선택
4. 확장 팝업 → relay 주소 `127.0.0.1:9080` 확인
5. claude.ai develop 프로젝트 탭 열어두기
6. 「지금 보내기 (1회)」 = 수동 · 「자동 전송」 = 상시 (레이트 리밋 주의)

### 회수 실패 감지

돌아온 답 == 보낸 질문 (에코) → `content.js` 의 `SEL_*` 셀렉터 깨짐. claude.ai UI 변경 시 유지보수 필요.

## 배경 탭 제약 (2026-08-20 postmortem)

**claude.ai 붙여넣기 업로드는 배경 탭에서 동작하지 않는다.** 브라우저 탭이 포커스돼 있어야 File 업로드 시작. 다른 탭 활성 상태에서는 붙여넣기 이벤트는 발생하지만 파일이 로드되지 않음.

### 필수 처방 6종

| # | 무엇 | 어디 |
|---|---|---|
| 1 | 첨부 시 확장이 탭·창을 스스로 활성화, 끝나면 원래대로 복귀 | `background.js` (`chrome.tabs.update` + `chrome.windows.update`) |
| 2 | 진단에 `focus`·`visibilityState` 병기 → 재발을 로그 한 줄로 판별 | `content.js` + `background.js` |
| 3 | 진단 즉시 보고 (답변 대기 앞으로) — `chrome.runtime.sendMessage` | `content.js` → `background.js` |
| 4 | 진단 파일 기록 (`docs/ask_web/diag.log`) — 메모리 dict X | `ask_web_relay.py` |
| 5 | 썸네일 판정 증분화 (기준선 찍고 delta 비교, 누적 X) | `content.js` |
| 6 | 빌드 토큰 파일 내용에서 도출 · manifest 버전 자동 증가 | `stamp_ext_build.py` |

### 성공 조건 명시

- 발송 시점에 탭이 활성화되어 있어야 함
- 확장은 발송 직전 자동 activate (사용자 개입 최소화)
- 발송 후 원래 활성 탭으로 복귀

### 조사 채널 (실물 우선)

- claude.ai DOM 조사 = Playwright 새 창 X (재인증 실패) → **이미 붙어 있는 확장으로 조사** (`dom-probe` mode)

## 콜드부팅 대기 (waitress · uvicorn 등)

- Python 웹 서버 cold boot bind = **~15초** 소요
- 9초 만에 curl 확인 = 오판 (`Connection refused` 지만 실제로는 부팅 중)
- 검증 스크립트는 `retry: 15s / interval: 1s` 필수

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

## 참조

- `docs/SETUP_OTHER_PC.md` (실전 셋업 원본)
- `docs/postmortem/2026-08-20-claude-web-attach-6-hypotheses.md` (배경 탭 제약 발견 회고)
- `feedback_web_cli_dialogue.md` (CLI ↔ Web 개념)
- `reference_claude_web_projects_setup.md` (Web Projects 세팅)
- `feedback_multi_session_worktree.md` (memory 인덱스)
- `.claude/rules/environment-dependent-bug.md` · `measurement-two-deaths.md` · `investigation-discipline.md` (같은 postmortem 승격)
- CLAUDE.md § 7-C8 (파일 잠금 Writer=1) · § 7-A1 (하드 경로 금지) · § 7-D15~D18 (postmortem 승격)
