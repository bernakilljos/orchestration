# Claude Code Environment Setup Guide

> Configuration document for setting up identical Claude Code environments across PCs  
> Created: 2026-04-07

---

## 1. Basic Installation

```bash
# Step 1: Remove npm version FIRST (before admin mode)
npm uninstall -g @anthropic-ai/claude-code

# Step 2: Install Claude Code native (requires admin)
# Windows: https://claude.ai/download/cli
# Or via command:
winget install Anthropic.ClaudeCode

# Step 3: Other AI CLIs
npm install -g @openai/codex
npm install -g @google/gemini-cli
```

---

## 2. Global Settings — Bypass Permissions

Path: `C:\Users\{username}\.claude\settings.json`

```json
{
  "autoUpdatesChannel": "latest",
  "skipDangerousModePermissionPrompt": true,
  "checkpointingEnabled": true,
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
```

| Setting | Value | Description |
|---|---|---|
| `skipDangerousModePermissionPrompt` | `true` | Skip dangerous mode permission confirmation popup |
| `defaultMode` | `bypassPermissions` | Auto-approve all tool calls (no need to click allow each time) |
| `autoUpdatesChannel` | `latest` | Auto-update to latest channel |
| `checkpointingEnabled` | `true` | Enable session checkpointing (rewind support) |

> Warning: bypassPermissions allows Claude to modify/delete files and execute commands without asking. Recommended for personal PCs only.

---

## 3. AI 역할 분담 및 도구 비교

### AI별 역할

| AI | 역할 | 비고 |
|---|---|---|
| **Codex** | 코드 1차 구현 | 500줄 이상 병렬 처리 |
| **Claude** | 코드 보완/고도화 + 문서/디자인/기획 | Codex 결과물 살 붙이기 |
| **Gemini** | 코드 검증 + 문서·이미지·다이어그램 생성 | MCP로 playwright/context7 활용 |

### 표준 개발 파이프라인

```
[코드 구현]
Codex → 1차 구현 (task-instruction.md 기반)
  ↓
Claude → 보완/고도화 (Codex 결과 + 지시서 참고)
  ↓
Gemini → 검증 + docs/diagram 생성

[문서·기획·디자인]
Claude 직접 처리 (Gamma/Canva/Figma MCP 활용)
```

### docs 날짜 폴더 규칙

생성되는 모든 md 파일은 `docs/YYYY-MM-DD/` 폴더 안에 저장합니다.

```
docs/
  2026-04-09/
    daily-report-2026-04-09.md
    task-review-task-01-login.md
    implementation-report.md
    review-result.md
  2026-04-10/
    ...
```

- 날짜별로 정리되어 이전 날짜 폴더 통째로 삭제 가능
- codex-auto, gemini-auto가 자동으로 오늘 날짜 폴더 생성
- Claude도 docs 파일 작성 시 `docs/오늘날짜/` 폴더에 저장

---

### AI별 가능한 도구

| 기능 | Claude | Gemini | Codex |
|---|:---:|:---:|:---:|
| MCP 서버 연결 | ✅ | ✅ | ❌ |
| context7 (공식문서) | ✅ | ✅ | ❌ |
| playwright (브라우저) | ✅ | ✅ | ❌ |
| Figma 읽기/코드연결 | ✅ | ❌ | ❌ |
| Gamma (PPT 생성) | ✅ | ❌ | ❌ |
| Canva (디자인) | ✅ | ❌ | ❌ |
| Gmail / Calendar | ✅ | ❌ | ❌ |
| Mermaid 다이어그램 | ✅ | ❌ | ❌ |
| 플러그인 시스템 | ✅ | ❌ | ❌ |

> 제안서·PPT·디자인·기획서 → **Claude 전담**
> 코드 검증·문서화·다이어그램 → **Gemini** (MCP 활용)
> 대량 코드 구현 → **Codex** (병렬)

---

## 4. MCP Server List

### claude.ai Official Integrations (auto-connected after login)

| MCP Server | Purpose |
|---|---|
| claude_ai_Figma | Read Figma designs / Code Connect |
| claude_ai_Gamma | AI presentation generation |
| claude_ai_Gmail | Read Gmail / draft creation |
| claude_ai_Google_Calendar | Google Calendar |
| claude_ai_Hugging_Face | HuggingFace models/datasets |
| claude_ai_Mermaid_Chart | Mermaid diagram validation/rendering |

### External MCP Servers — Auto-Install Commands

Run these `claude mcp add` commands to install external MCP servers.
install.bat이 자동 설치. Claude 세션 시작 시 누락된 항목만 보완.

```bash
# context7 - Library official documentation lookup
claude mcp add -s user context7 -- npx -y @upstash/context7-mcp

# playwright - Browser automation
claude mcp add -s user playwright -- npx @playwright/mcp@latest

# Sequential Thinking - Step-by-step reasoning for complex problems
claude mcp add -s user thinking -- npx -y @anthropic/thinking-mcp

# Gemini MCP - Direct Gemini model access (second opinion, code review, large context)
# API key is set separately after install (uses GEMINI_API_KEY)
claude mcp add gemini -s user -e GEMINI_API_KEY=your-key -- npx -y @rlabs-inc/gemini-mcp
```

> Note: claude.ai official integrations (Figma, Gamma, Gmail, Google Calendar, Hugging Face, Mermaid Chart, Canva) are auto-connected after login — no manual setup needed.
> Note: gemini MCP requires GEMINI_API_KEY from Google AI Studio (free tier available). Set after install.

**CLI 도구 vs MCP 서버 구분 (중복 아님):**
| 구분 | 설치 위치 | 역할 |
|------|-----------|------|
| `npm install -g @openai/codex` | 글로벌 npm | codex-auto.bat이 호출하는 CLI 도구 |
| `npm install -g @google/gemini-cli` | 글로벌 npm | gemini-auto.bat이 호출하는 CLI 도구 |
| `claude mcp add gemini npx @rlabs-inc/gemini-mcp` | Claude MCP | Claude Code 내부에서 직접 Gemini API 호출 |
→ CLI 도구(codex, gemini)와 MCP 서버(gemini-mcp)는 **완전히 다른 통합**. 중복 설치 아님.

### Claude Plugins — Auto-Install

install.bat이 자동 설치. Claude 세션 시작 시 누락된 항목만 보완.

```bash
# 기본 플러그인
claude plugin install claude-md-management   # CLAUDE.md 품질 관리 (/revise-claude-md)
claude plugin install code-review            # PR 코드리뷰 (/code-review)
claude plugin install commit-commands        # git commit/push (/commit, /commit-push-pr)

# Superpowers — TDD/계획/리뷰 자동화 프레임워크
claude plugin marketplace add obra/superpowers-marketplace
claude plugin install superpowers@superpowers-marketplace
```

### Superpowers Plugin 사용법

| 명령 | 기능 |
|------|------|
| `/superpowers:brainstorm` | 아이디어 브레인스토밍 → 설계 문서 생성 |
| `/superpowers:plan` | 작업을 2-5분 단위 태스크로 분해 |
| `/superpowers:code-review` | 2단계 코드 리뷰 (스펙 준수 → 품질) |
| TDD 자동 | RED-GREEN-REFACTOR 사이클 자동 적용 |

> 우리 파이프라인(Codex→Claude→Gemini)과 공존 가능. TDD 부분을 superpowers가 보강.

---

### Advisor 설정 (Sonnet + Opus)

claude-auto.bat이 자동으로 advisor 모드 사용:
- **실행**: claude-sonnet-4-6 (빠르고 저렴)
- **조언**: claude-opus-4-6 (복잡한 설계/판단 시 자동 호출)

```
claude -p "task..." --model claude-sonnet-4-6 --advisor claude-opus-4-6
```

수동으로 advisor 사용 시:
```bash
# CLI에서 직접
claude --model claude-sonnet-4-6 --advisor claude-opus-4-6

# API 호출 시 (Python)
import anthropic
client = anthropic.Anthropic()
response = client.beta.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    betas=["advisor-tool-2026-03-01"],
    tools=[{
        "type": "advisor_20260301",
        "name": "advisor",
        "model": "claude-opus-4-6"
    }],
    messages=[{"role": "user", "content": "..."}]
)
```

| 설정 | 값 | 설명 |
|------|-----|------|
| model | claude-sonnet-4-6 | 실행 모델 (빠름, 저렴) |
| advisor | claude-opus-4-6 | 조언 모델 (고지능, 설계/판단) |
| max_uses | 없음 (무제한) | 복잡한 작업에서 Opus 제한 없이 활용 |

---

## 4. Project-Specific Settings

### .claude Folder Structure

```
PROJECT/
  .claude/
    settings.json        # Hook configuration
    settings.local.json  # Allowed permission list
    hooks/               # Auto-execution scripts
    skills/              # Custom slash commands
    agents/              # Sub-agent configuration
```

### settings.json (Hooks)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/search-panel-guard.sh" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "bash .claude/hooks/check-secrets-lite.sh" }]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "bash .claude/hooks/check-page-performance.sh" }]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "bash .claude/hooks/check-page-performance.sh" }]
      }
    ]
  }
}
```

### Hook Roles

| Hook | Trigger | Role |
|---|---|---|
| search-panel-guard.sh | Before Edit/Write | Prevent search panel reset button insertion |
| check-secrets-lite.sh | After Edit/Write | Detect hardcoded passwords/tokens |
| check-page-performance.sh | After Edit/Write | Performance check for .vue files |
| java-guard.sh | After Edit/Write | Warn on Java file modifications in rms-ba/ |

### Custom Skills (Slash Commands)

| Skill | Purpose |
|---|---|
| /codex-run | Delegate Codex execution |
| /git-commit | Git commit |
| /test-run | Run tests |
| /page-performance-check | Page performance check |

---

## 5. Ultraplan (CLI ↔ Web Linked Planning) — Optional

> This is entirely optional. The pipeline works fine without it.
> Skip this section if you don't need web-based plan review.

### What is it
Heavy planning tasks from the terminal are handed off to the cloud (claude.ai web).
The user reviews/comments in the browser, then chooses to execute in cloud or send back to terminal.

### Requirements (only if you want to use it)
```
[ ] Claude Code v2.1.91+ (check: claude --version)
[ ] GitHub repository connected
[ ] Claude Code on the web account (claude.ai/code)
[ ] NOT using Bedrock/Vertex/Foundry (subscription-based only)
```

### Usage
```bash
# In terminal
/ultraplan Design the system architecture including frontend, backend, and DB layers

# Or just include "ultraplan" in your prompt
"ultraplan: Create deployment pipeline for the project"
```

### Flow
```
Terminal: /ultraplan [prompt]
    ↓
Cloud: Plan draft auto-generated (browser opens)
    ↓
Web: User reviews, adds inline comments/feedback
    ↓
Choose:
  A) Execute in cloud → Auto-create PR on GitHub
  B) Send back to terminal → Local execution
```

### Integration with Multi-Agent Pipeline
```
[Before]
  Claude (terminal) → designs alone → writes task-instruction.md

[After — with Ultraplan]
  Claude (terminal) → /ultraplan for complex designs
    → Web: User reviews architecture plan with visual UI
    → Approve: Plan comes back as structured spec
    → Claude writes task-instruction.md from approved plan
    → Codex/Gemini execute as usual
```

### When to Use
| Scenario | Use Ultraplan? |
|----------|---------------|
| Simple feature (<500 lines) | No — direct CLI |
| Complex architecture (multi-file, DB+API+UI) | Yes |
| Design review needed before implementation | Yes |
| Quick bug fix | No — direct CLI |
| New project initial setup | Yes |

---

## 6. Vibe Coding Multi-Agent Loop

```
Claude (design/orchestration)
  |
Codex x N (parallel implementation)
  |
Gemini x N (parallel verification + 1st error fix, max 3 retries)
  | On Gemini failure
Claude (2nd error fix escalation)
  |
Loop repeats...

Daily 09:00 -> Auto-generate completion report
User "stop" -> Immediately halt
```

### Loop Guard Conditions

| Condition | Action |
|---|---|
| Goal achieved | STOP |
| Gemini retries exceed 3 | Claude escalation |
| Code quality degradation | git rollback |
| User says "stop" | Immediately halt |

### Daily Report Format (auto-generated at 09:00)

```
[YYYY-MM-DD 09:00] Overnight Loop Completion Report
- Completed tasks: N
- Modified files: N
- Gemini pass rate: N%
- Claude escalations: N
- Next scheduled tasks: ...
```

---

## 7. PowerShell UTF-8 Encoding

Windows 기본 인코딩(CP949)으로 인한 한글 깨짐 방지. install.bat이 자동 적용.

PowerShell 프로필에 추가 (`$PROFILE`):
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

Claude 세션 시작 시 프로필에 없으면 자동 추가.

---

## 8. Bundled Slash Commands

install.bat이 `.claude/commands/`에 복사. `claude` 시작 시 자동 활성화.

| 커맨드 | 설명 |
|--------|------|
| `/vibe-loop` | codex-auto/gemini-auto 감지 후 멀티에이전트 루프 시작 |
| `/loop-stop` | `.claude/tasks/stop` 생성 → 모든 워커 중단 |
| `/check-agents` | codex-auto/gemini-auto 가용 여부 + 작업 현황 |
| `/check-services` | status-push/remote-agent 상태 확인 + 자동 재시작 |
| `/orcauto-start` | codex-auto/gemini-auto 자동 시작 활성화 + 즉시 실행 |
| `/orcauto-stop` | codex-auto/gemini-auto 자동 시작 비활성화 + 워커 종료 |
| `/revise-claude-md` | CLAUDE.md 품질 개선 (plugin) |
| `/code-review` | PR 코드리뷰 (plugin) |
| `/commit` | git commit 자동화 (plugin) |
| `/commit-push-pr` | commit + push + PR 생성 (plugin) |

---

## 9. New PC Setup Checklist

```
[ ] install.bat 실행 (관리자 권한으로)
    ※ 경로에 공백 있으면 반드시 폴더 이동 후 실행:
       cd /d "E:\PJT\orchestration_v1 2\orchestration_v1"
       install.bat E:\PJT\myproject
    → 아래 항목 자동 처리:
    [ ] Claude Code native 설치/업데이트
    [ ] npm install -g @openai/codex @google/gemini-cli
    [ ] MCP 서버 설치 (Section 3)
    [ ] Claude 플러그인 설치 (Section 3)
    [ ] settings.json 설정 (Section 2)
    [ ] PowerShell UTF-8 프로필 설정 (Section 7)
    [ ] status-push / remote-agent 등록 및 시작
    [ ] .claude/ 폴더 + bundled commands 복사

[ ] 수동 설정 (install.bat이 처리 못하는 항목):
    [ ] ANTHROPIC_API_KEY 환경변수 설정  → setx ANTHROPIC_API_KEY "sk-ant-..."
    [ ] OPENAI_API_KEY 환경변수 설정    → setx OPENAI_API_KEY "sk-..."
    [ ] GEMINI_API_KEY 환경변수 설정    → setx GEMINI_API_KEY "AI..."
    [ ] 새 터미널 열기 (환경변수 적용)
    [ ] claude.ai 로그인 (Figma/Gmail 등 공식 통합 활성화)

[ ] 설치 오류 시 → Section 12 참조
```

---

## 10. API Key Environment Variables

Windows 환경변수 설정 (CMD에서 실행, 설정 후 새 터미널 필요):

```bat
setx ANTHROPIC_API_KEY "sk-ant-..."
setx OPENAI_API_KEY "sk-..."
setx GEMINI_API_KEY "AI..."
```

설정 확인:
```bat
echo %ANTHROPIC_API_KEY%
echo %OPENAI_API_KEY%
echo %GEMINI_API_KEY%
```

---

## 11. Status-Push / Remote-Agent Auto-Setup

> Claude should execute these checks on first run automatically.
> If install.bat failed to start these services, Claude should retry here.

### Check and Start Services

```bash
# 1. Check if status-push is running
# Look for wscript.exe processes running status-push-silent.vbs
# If NOT running, start it:
wscript "%USERPROFILE%\.claude\status-push-silent.vbs"

# 2. Check if remote-agent is running
# Look for wscript.exe or powershell.exe processes running remote-agent
# If NOT running, start it:
wscript "%USERPROFILE%\.claude\remote-agent-silent.vbs"

# 3. Verify Registry Run keys exist
# Check: HKCU\Software\Microsoft\Windows\CurrentVersion\Run
#   OrchestrationStatusPush  → wscript.exe "...\.claude\status-push-silent.vbs"
#   OrchestrationRemoteAgent → wscript.exe "...\.claude\remote-agent-silent.vbs"
# If missing, register:
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "OrchestrationStatusPush" /t REG_SZ /d "wscript.exe \"%USERPROFILE%\.claude\status-push-silent.vbs\"" /f
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "OrchestrationRemoteAgent" /t REG_SZ /d "wscript.exe \"%USERPROFILE%\.claude\remote-agent-silent.vbs\"" /f
```

### When to Run
- On every Claude first session (CLAUDE_SETUP_GUIDE.md exists)
- If dashboard shows PC offline (status-push not running)
- After PC reboot if services didn't auto-start

---

## 10. Reference Paths

| Item | Path |
|---|---|
| Claude global settings | C:\Users\{username}\.claude\settings.json |
| Claude memory | C:\Users\{username}\.claude\projects\...\memory\ |
| Project root | {PROJECT_PATH}\ |
| Project .claude settings | {PROJECT_PATH}\.claude\ |
| Frontend | {PROJECT_PATH}\{frontend-dir}\ |
| Backend | {PROJECT_PATH}\{backend-dir}\ |

---

## 12. Troubleshooting — 회사 PC / 신규 PC 설치 시 알려진 문제

> 2026-04-10 회사 PC 설치 과정에서 발견된 이슈들 기록

### 12-1. install.bat 실행 방법 (경로에 공백이 있는 경우)

install.bat 폴더 경로에 공백이 있으면 반드시 따옴표로 감싸야 함:

```bat
rem 잘못된 예 (공백 있는 경로를 따옴표 없이 실행)
install.bat E:\PJT\ex          ← orchestration 폴더에 공백 있으면 오류

rem 올바른 방법 1: 폴더 이동 후 실행
cd /d "E:\PJT\orchestration_v1 2\orchestration_v1"
install.bat E:\PJT\ex

rem 올바른 방법 2: install.bat 우클릭 → 관리자 권한으로 실행
```

### 12-2. Windows Defender 서비스 비활성 (회사 PC)

회사 PC는 3rd-party 백신 사용으로 Windows Defender 서비스가 꺼져 있음.
`Add-MpPreference` 호출 시 오류 `0x800106ba` 발생하나 **설치에는 영향 없음** (자동 스킵).

```
Defender WARN: 0x800106ba → 무시해도 됨
```

### 12-3. `... was unexpected at this time.` 오류

**원인:** CMD 배치파일에서 `\"` (따옴표 이스케이프) 또는 `|| (` 패턴이 중첩 블록 안에서 파싱 오류를 일으킴.

**증상:** `[+] Installing status-push files...` 출력 후 오류 발생하며 멈춤.

**해결:** install.bat v2026-04-10 이후 버전에서 수정됨.
- `\"` → `('string ' + $var)` 방식으로 변경
- `if exist ... (` 대형 블록 → `goto` 라벨 방식으로 재구성
- `|| (` → `if errorlevel 1 (` 으로 변경

### 12-4. `winget` 미설치 (회사 PC)

회사 PC에 `winget`이 없는 경우 install.bat이 아래 항목을 건너뜀:
- cloudflared 설치 → **kit에 bundled된 cloudflared.exe 사용** (자동 대체됨)
- Claude Code 업데이트 → 수동 업데이트 필요

winget 설치: Microsoft Store → "앱 설치 관리자" 검색 후 설치

### 12-5. API 키 미설정

install.bat이 자동 설정 불가 — 반드시 수동으로 설정:

```bat
setx ANTHROPIC_API_KEY "sk-ant-..."
setx OPENAI_API_KEY "sk-..."
setx GEMINI_API_KEY "AI..."
```

설정 후 **새 터미널 창**을 열어야 적용됨.

### 12-6. MCP 서버 연결 실패 (sequentialthinking, filesystem, gemini)

**증상:** `claude mcp list`에서 MCP 서버가 `Failed` 상태이거나 아예 등록 안 됨.

**원인:** install-mcp.ps1 구버전이 `--` 뒤에 `cmd /c`를 강제 삽입하여 npx 명령어 인자가 깨짐.

| MCP 서버 | 증상 | 원인 |
|-----------|------|------|
| sequentialthinking | `cmd C:/` 경로 오타 | `cmd /c` 삽입 시 토큰 파싱 오류 |
| filesystem | 연결 실패 | `cmd /c` 삽입이 경로 인자 순서를 깨뜨림 |
| gemini | 미설치 | GEMINI_API_KEY 미설정 시 경고 없이 스킵 |

**해결:**
```bash
# 1. 잘못된 MCP 삭제
claude mcp remove sequentialthinking
claude mcp remove filesystem

# 2. 올바른 명령으로 재등록
claude mcp add -s user thinking -- npx -y @anthropic/thinking-mcp
claude mcp add -s user context7 -- npx -y @upstash/context7-mcp
claude mcp add -s user playwright -- npx @playwright/mcp@latest

# 3. gemini (API 키 설정 후)
setx GEMINI_API_KEY "AI..."
# 새 터미널 열고:
claude mcp add gemini -s user -e GEMINI_API_KEY=%GEMINI_API_KEY% -- npx -y @rlabs-inc/gemini-mcp

# 4. 확인
claude mcp list
```

**예방:** install-mcp.ps1 v2026-04-11 이후 버전에서 `cmd /c` 삽입 로직 제거됨. guide의 명령어를 그대로 실행.

### 12-7. install 후 codex-a / gemini-a를 못 찾는 경우

```
[X] codex-a   (auto-installed above)
[X] gemini-a  (auto-installed above)
```

현재 터미널에서만 인식 안 되는 것. **새 터미널 창**을 열면 정상 작동.

### 12-8. install 로그 확인 방법

install 중 오류가 발생하고 창이 닫힐 경우:

```bat
type %TEMP%\orchestration-install.log
```

각 단계별 타임스탬프와 오류 내용이 기록되어 있음.
