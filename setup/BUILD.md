# setup.exe 빌드 방법

> **현행화 2026-05-07** — exec_remote (4주차 VPS) + mcp_collab Telegram 추가 반영. v1 vs team 분기 명문화.

---

## 0. 두 가지 설치 모드 (v1 vs team)

같은 `setup.exe` 가 ini 파일 존재 여부로 자동 분기합니다 (`setup.iss § HasExistingPat`):

| 모드 | 조건 | PAT 입력 페이지 |
|---|---|---|
| **v1 (main)** | `docs/ini/github.ini` 가 있고 `GITHUB_PAT=ghp_...` 또는 `GITHUB_PAT=github_pat_...` 라인 존재 | **자동 SKIP** (이미 있으니 묻지 않음) |
| **team** | ini 없거나 placeholder | **마법사에서 직접 입력 받음** → ini 자동 생성 |

> v1 = 본인 PC 재설치, team = 팀 신규 멤버 onboarding. 두 시나리오 모두 동일 setup.exe 로 동작.

---

## 1. Inno Setup 설치

```text
winget install JRSoftware.InnoSetup
```

또는 https://jrsoftware.org/isdl.php 에서 다운로드.

## 2. setup.exe 컴파일

### GUI
1. `setup.iss` 파일을 더블클릭 (Inno Setup Compiler 열림)
2. Build > Compile (Ctrl+F9)
3. `setup\Output\OrchestrationKit-Setup.exe` 생성

### CLI
```bat
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" setup.iss
```

PATH 에 iscc 가 있으면:
```bat
iscc setup.iss
```

## 3. 결과물

```text
setup\Output\OrchestrationKit-Setup.exe
```

이 파일 하나만 배포. 더블클릭 시:
- 위자드 (한국어/영어 선택)
- 설치 경로 선택 (= 프로젝트 폴더, 기본 `%USERPROFILE%\pjt`)
- 모드 라디오 (Full / Codex 단독 / Gemini 단독 / 사용자 지정)
- **PAT 입력 페이지** (team 모드만, v1 모드는 자동 스킵)
- 프로그레스바 + 압축 해제 + 모듈 자동 실행
- 완료

## 4. 사일런트 설치 (자동화)

```bat
OrchestrationKit-Setup.exe /SILENT /DIR="C:\work\myproject"
```

완전 무음:
```bat
OrchestrationKit-Setup.exe /VERYSILENT /DIR="C:\work\myproject" /SUPPRESSMSGBOXES
```

## 5. setup.exe 없이 bat 으로 설치

```bat
cd setup
setup.bat C:\work\myproject
```

- bat 모드는 모든 모듈 (01~14) 순차 실행
- v1/team 분기는 `07-github.bat` 안에서 ini 존재 확인으로 처리

## 6. 모듈 구조 (현행)

`setup/modules/` 14개 모듈 (실행 순서):

| # | 모듈 | 역할 |
|---|---|---|
| 01 | core.bat | 폴더 구조 + .env 초기화 |
| 02 | defender.bat | Windows Defender 예외 |
| 03 | settings.bat | `.claude/settings.json` (bypassPermissions 강제) + `.vscode/settings.json` 자동 배포 (interpreter 동적 검색, file watcher exclude) |
| 04 | commands.bat | 글로벌 명령어 (codex-a, gemini-a) |
| 05 | services.bat | status-push, remote-agent |
| 06 | prereqs.bat | Node.js / Claude Code / Cloudflared |
| 07 | github.bat | Git 초기화 + PAT 등록 (v1/team 자동 분기) |
| 08 | plugins.bat | Claude 플러그인 (community + superpowers) |
| 09 | finalize.bat | 마무리 |
| 10 | video-restore.bat | 비디오 도구 복원 |
| 11 | media-enhance.bat | 미디어 의존성 |
| 12 | kit-sync.bat | sync-plugins.sh 실행 |
| 13 | init-state-db.bat | SQLite 통합 상태 DB 초기화 |
| 14 | mcp-figma.bat | ClaudeTalkToFigma MCP 등록 |
| 15 | auto-dev.bat | 24/7 자동 개발 에이전트 (Task Scheduler 4h + auto-dev flag) |

## 7. 설치 후 4주차로 가는 길

setup 끝나면 사용자에게 Claude 가 안내해야 할 다음 단계:

```text
1주차 완료 (MCP 기초)        → /plug_all 로 추가 카테고리
2주차 완료 (CLAUDE.md)        → 자동
3주차 (Telegram 알림)         → /mcp_collab-install
4주차 (VPS 24/7 원격)         → /exec_remote-setup    ⭐ 신규
```

## 8. 현행화 체크리스트

`setup.iss` / `setup-info.rtf` / 본 BUILD.md 수정 시 함께 갱신할 곳:

- [ ] `setup.iss` § `MyAppVersion` 버전 bump
- [ ] `setup-info.rtf` 플러그인 카운트 (현재 15 stable + 7 spec-only)
- [ ] `CLAUDE.md` § 1 — 플러그인 카운트
- [ ] `docs/2026-MM-DD/` 변경 노트
- [ ] `BUILD.md` § 6 모듈 표
