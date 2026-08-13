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

## 참조

- `docs/SETUP_OTHER_PC.md` (실전 셋업 원본)
- `feedback_web_cli_dialogue.md` (CLI ↔ Web 개념)
- `reference_claude_web_projects_setup.md` (Web Projects 세팅)
- `feedback_multi_session_worktree.md` (memory 인덱스)
- CLAUDE.md § 7-C8 (파일 잠금 Writer=1) · § 7-A1 (하드 경로 금지)
