# Claude Code 회사/개인 계정 분리 가이드

> **근거**: 2026-10-28 사용자 지시 — 회사 계정 (`sjseo@itcen.com`) · 개인 계정 (`ja205502@gmail.com`) 분리 · 공통 프로젝트 (`C:\pjt\orchestration_v1`) 접근.
> **공식 지원**: Anthropic Claude Code docs — `CLAUDE_CONFIG_DIR` 환경 변수로 계정별 설정 디렉터리 분리.

## 설계 원칙

| 원칙 | 적용 |
|---|---|
| 인증·사용량 **분리** | 계정별 `CLAUDE_CONFIG_DIR` 독립 |
| 프로젝트 **공통** | `C:\pjt\orchestration_v1` 그대로 공유 (Git · Rules · Agents · Skills · Hooks · Ledger · Supervisor DB) |
| 토큰·쿠키·API 키 **미공유** | 두 계정 설정 디렉터리 간 복사 금지 (회사 정보보안 정책) |
| 자동 로그인·우회 **금지** | 사용자가 각 계정에 정상 `/login` |
| 동시 실행 **방지** | 같은 프로젝트 2 세션 X (Writer=1 룰 · 파일 잠금 충돌) |
| 미완료 작업 **복원** | `next-actions.md` · Request Ledger · Goal DB 자동 로드 |

## 구성 (Zero-touch)

### 1) 회사 Claude (기본 위치)

변경 없음. 기존 `%USERPROFILE%\.claude\` 사용.

```powershell
cd C:\pjt\orchestration_v1
claude   # 회사 계정으로 로그인된 상태 · 기본 사용
```

### 2) 개인 Claude (별도 설정 디렉터리)

```powershell
$env:CLAUDE_CONFIG_DIR = "$HOME\.claude-personal"
cd C:\pjt\orchestration_v1
claude   # 첫 실행 시 /login 으로 ja205502@gmail.com 인증
```

**첫 실행 체크리스트**:
1. `/login` → 개인 계정 OAuth 완료
2. `/status` → 현재 로그인 계정 확인
3. `/usage` → 개인 계정 사용 가능 플랜·토큰 확인
4. 미완료 작업 자동 복원 확인 (SessionStart hook)

### 3) PowerShell Profile 자동화 (옵션)

매번 `$env:CLAUDE_CONFIG_DIR` 입력 번거로우면 PowerShell profile 에 함수 등록:

```powershell
# $PROFILE 편집
function claude-personal {
    $env:CLAUDE_CONFIG_DIR = "$HOME\.claude-personal"
    cd C:\pjt\orchestration_v1
    claude @args
}
```

실행: `claude-personal`

## 계정 전환 시 자동 복원 (이미 작동)

Kit 의 SessionStart hook 이 **계정 무관** 로 다음을 자동 로드:

| 데이터 | 위치 | SessionStart 복원 |
|---|---|---|
| 미완료 작업 | `.claude/state/next-actions.md` | `resume-last-24h.py` 자동 로드 |
| Request Ledger | `.claude/state/request-ledger.json` | `request-ledger.py status` 자동 |
| Goal DB | `.claude/state/orca.db` | Supervisor advance-all 자동 |
| 최근 세션 요약 | `orca.db.session_summary` | `load-recent-conversations.sh` 자동 |
| 사용자 스타일 | `.claude/state/user_style_profile.md` | `inject-user-style.sh` 자동 |

**효과**: 회사 계정 작업 중단 → 개인 계정 로그인 → 미완료 작업 리스트 systemMessage 로 자동 노출 → 바로 이어서 개발.

## 동시 실행 방지 (Writer=1)

**금지**: 회사 계정 Claude 세션과 개인 계정 Claude 세션이 **같은 프로젝트를 동시에** 열고 수정.

이유: `orca.db` 쓰기 충돌 · Git 충돌 · 파일 잠금 (`.claude/tasks/locks/`) 꼬임.

**권장 흐름**:
1. 회사 계정 작업 → `/clear` 또는 Claude 종료
2. 개인 계정 Claude 실행 → 작업 이어받기
3. 완료 후 다시 회사 계정으로 복귀

## Windows Task Scheduler 영향

**중요**: Task Scheduler 는 **로그인 세션과 무관하게** 동작. 예약된 `Orca_*` 작업 (10MinLoop · DailyArtifactRefresh · WeeklyAudit) 은 등록된 Windows 계정으로 실행 (Claude 로그인 계정과 **별개**).

→ 계정 전환이 Scheduler 실행에 영향 X. 다만 Scheduler 가 호출하는 python 스크립트가 Ledger · Goal DB 를 수정하므로, 두 Claude 세션이 돌고 있으면 **3-way 쓰기 충돌** 가능.

**해결**: 세션은 1개만 유지 · Scheduler 는 그대로.

## 회사 정보보안 정책 체크리스트

개인 계정 전환 전 **반드시** 확인:

- [ ] 회사 소스를 개인 Claude 로 전송해도 되는 프로젝트인가? (프로젝트 라이선스·NDA)
- [ ] `.env` · 시크릿 · API 키 가 개인 계정 세션에서 **접근 금지** 설정 돼 있나?
- [ ] Git remote 가 회사 저장소면 개인 계정으로 push 시 사용자 식별 분리 (`git config user.email`)
- [ ] 회사 Claude 조직 (`sjseo@itcen.com`) 의 데이터 리텐션 정책과 개인 계정 다름

## 사용량 확인

| 명령 | 용도 |
|---|---|
| `/status` | 현재 로그인 계정 · 플랜 |
| `/usage` | 세션·일간·주간 사용량 |
| `/token-stats` (kit 명령) | kit 안 토큰 통계 · 세션별 비용 |

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 개인 계정에서 `/login` 후 회사 계정으로 로그인됨 | `CLAUDE_CONFIG_DIR` 미설정 | `$env:CLAUDE_CONFIG_DIR = "$HOME\.claude-personal"` 다시 설정 후 `claude` 재시작 |
| 미완료 작업 리스트 안 뜸 | SessionStart hook 미발동 | `.claude/state/next-actions.md` 수동 확인 또는 `python .claude/scripts/resume-last-24h.py --json` |
| 두 세션 동시 작업 후 orca.db 손상 | Writer=1 룰 위반 | `.claude/state/orca.db.bak.*` 에서 복구 · 세션 1개만 유지 |
| MCP 플러그인 개인 계정에서 미동작 | 사용자 전역 설정 분리 | 개인 계정 `CLAUDE_CONFIG_DIR` 안에 MCP 재등록 필요 (토큰 복사 X) |

## 관련

- `CLAUDE.md` § 3.1 Session Start (자동 복원 메커니즘)
- `.claude/rules/multi-session-isolation.md` (worktree 격리 · Writer=1)
- `.claude/state/next-actions.md` (미완료 작업)
- `.claude/scripts/request-ledger.py` (Request Ledger)
- Anthropic Claude Code Docs: `CLAUDE_CONFIG_DIR`
