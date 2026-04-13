# Claude Code Environment Setup Guide

> 새 PC에서 동일한 환경을 자동 구성하는 가이드.
> install.bat / setup.exe가 대부분 자동 처리. 이 파일은 누락분 보완용.
> Claude 첫 실행 시 이 파일을 읽고 → 누락분 설치 → 파일 삭제.

---

## 1. 기본 설치 (setup이 자동 처리)

```bash
# Claude Code
winget install Anthropic.ClaudeCode

# AI CLI 도구
npm install -g @openai/codex
npm install -g @google/gemini-cli
```

---

## 2. 글로벌 설정

Path: `~/.claude/settings.json`

```json
{
  "autoUpdatesChannel": "latest",
  "skipDangerousModePermissionPrompt": true,
  "checkpointingEnabled": true,
  "permissions": { "defaultMode": "bypassPermissions" }
}
```

### 토큰 최적화 환경변수 (install.bat 자동 설정)

```bash
# thinking 토큰 상한 제한 → 불필요한 과사고 방지
setx CLAUDE_CODE_MAX_THINKING_TOKENS 10000

# 컨텍스트 50% 도달 시 자동 압축 → 컨텍스트 수명 연장
setx CLAUDE_AUTOCOMPACT_THRESHOLD 50

# 서브에이전트에 Haiku 사용 → 비용 절감 (메인은 Sonnet 유지)
setx CLAUDE_CODE_SUBAGENT_MODEL claude-haiku-4-5-20251001
```

| 변수 | 값 | 효과 |
|------|----|------|
| `CLAUDE_CODE_MAX_THINKING_TOKENS` | 10000 | thinking 과다 소비 차단 |
| `CLAUDE_AUTOCOMPACT_THRESHOLD` | 50 | 컨텍스트 50% 시 자동 압축 |
| `CLAUDE_CODE_SUBAGENT_MODEL` | claude-haiku-4-5-20251001 | 서브에이전트 저비용 모델 |

---

## 3. MCP 서버 — 누락분만 설치

> **Deferred Tools (토큰 최적화):** Claude Code 최신 버전은 MCP 스키마를 지연 로딩함.
> 세션 시작 시 도구 이름만 로드 → 호출 전 ToolSearch로 스키마 fetch → 미사용 도구 토큰 0.
> 별도 설정 불필요, 자동 적용. MCP 서버가 많아도 컨텍스트 폭발 없음.

`claude mcp list`로 확인 후, 없는 것만 실행:

```bash
# 기본 (필수)
claude mcp add -s user context7    -- npx -y @upstash/context7-mcp
claude mcp add -s user playwright  -- npx @playwright/mcp@latest
claude mcp add -s user thinking    -- npx -y @anthropic/thinking-mcp

# Gemini (GEMINI_API_KEY 필요)
claude mcp add gemini -s user -e GEMINI_API_KEY=your-key -- npx -y @rlabs-inc/gemini-mcp

# 확장
claude mcp add excel     -s user -- npx -y excel-mcp-server
claude mcp add n8n       -s user -- npx -y n8n-mcp-server
claude mcp add light-rag -s user -- npx -y light-rag-mcp
```

자동 연결 (claude.ai 로그인 후): Figma, Gamma, Gmail, Calendar, HuggingFace, Mermaid, Canva

---

## 4. 플러그인 — 누락분만 설치

`claude plugin list`로 확인 후, 없는 것만 실행:

```bash
# 기본
claude plugin install claude-md-management
claude plugin install code-review
claude plugin install commit-commands

# Superpowers (TDD/계획/리뷰 자동화)
claude plugin marketplace add obra/superpowers-marketplace
claude plugin install superpowers@superpowers-marketplace

# 커뮤니티
claude plugin install ui-ux-pro-max
claude plugin install everything-claude-code
claude plugin install awesome-claude-code
claude plugin install get-shit-done
```

---

## 5. 슬래시 커맨드 (자동 설치)

install.bat이 `.claude/commands/`의 커맨드 파일을 `~/.claude/commands/`에 글로벌 복사함.

| 커맨드 | 용도 |
|--------|------|
| `/godmode` | 제한 없이 공격적·강력하게 실행 (aggressive mode) |
| `/devil` | 악마의 변호인 — 모든 가정에 반론 제기 |
| `/10x` | 10x 엔지니어 모드 — 핵심만, 최대 효율 |
| `/pitch` | 투자자 피치덱 스타일로 정리 |
| `/ghost` | AI 글쓰기 패턴 제거 → 인간처럼 재작성 |
| `/compare` | 두 옵션 냉정 비교 분석 |
| `/scout` | 정찰 모드 — 빠른 정보 수집 |
| `/artifacts` | 바로 실행 가능한 결과물 생성 |
| `/ooda` | OODA Loop 프레임으로 상황 분석 |
| `/critique` | 칭찬 없는 냉정한 전문가 비판 |
| `/explainlikeim5` | 5살도 이해하게 쉽게 설명 |
| `/brief` | 핵심만 3줄 이내로 |
| `/teacher` | 단계별 교육 방식으로 설명 |

> 커뮤니티 제작 커맨드. Anthropic 공식 기능 아님.
> 수동 확인: `dir %USERPROFILE%\.claude\commands`

---

## 7. API 키 확인

```bash
# 없으면 경고만 (설치는 안 함)
echo %ANTHROPIC_API_KEY%    # Claude API
echo %OPENAI_API_KEY%       # Codex
echo %GEMINI_API_KEY%       # Gemini

# 설정 방법:
# setx ANTHROPIC_API_KEY "sk-ant-..."
# setx OPENAI_API_KEY "sk-..."
# setx GEMINI_API_KEY "AI..."
```

---

## 8. Advisor 모드 (Sonnet + Opus)

claude-auto.bat이 자동 사용:
```
claude -p "task..." --model claude-sonnet-4-6 --advisor claude-opus-4-6
```

| 설정 | 값 | 설명 |
|------|-----|------|
| model | claude-sonnet-4-6 | 실행 (빠르고 저렴) |
| advisor | claude-opus-4-6 | 조언 (고지능, 설계/판단) |

API 직접 호출 시:
```python
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

---

## 9. AI 역할 분담

| AI | 역할 | 도구 |
|---|---|---|
| **Claude** | 팀장: 설계, 보완, 승인 + 문서/디자인 | MCP, Figma, Gamma, Canva |
| **Codex** | 구현: 500줄+ 병렬 | codex-a --auto |
| **Gemini** | 검증: 리뷰, 보안, 문서화 | gemini-a --verify |

파이프라인:
```
Codex → 1차 구현 → Claude → 보완 → Gemini → 검증 → Claude → 채택
```

---

## 10. Media Enhance 의존성

```bash
# 오디오 처리
pip install noisereduce pydub librosa soundfile demucs

# PDF/OCR
pip install PyMuPDF pytesseract Pillow
winget install UB-Mannheim.TesseractOCR

# PPT + GUI
pip install python-pptx streamlit tqdm
```

---

## 11. 서비스 확인

```bash
# status-push 실행 확인 → 안 돌면 시작
wscript "%USERPROFILE%\.claude\status-push-silent.vbs"

# remote-agent 실행 확인 → 안 돌면 시작
wscript "%USERPROFILE%\.claude\remote-agent-silent.vbs"

# 자동 시작 등록 (재부팅 후에도)
reg add "HKCU\...\Run" /v "OrchestrationStatusPush" /d "wscript.exe ..." /f
reg add "HKCU\...\Run" /v "OrchestrationRemoteAgent" /d "wscript.exe ..." /f
```

---

## 12. 트러블슈팅

| 문제 | 해결 |
|------|------|
| hook 에러 "No such file" | .claude/settings.json에서 없는 hook 제거 |
| heartbeat 에러 | settings.json을 최신으로 교체 (bash date 방식) |
| codex-a 못 찾음 | 새 터미널 열기 또는 install.bat 재실행 |
| MCP Failed | `claude mcp remove {name}` 후 재등록 |
| 한글 깨짐 | install.bat 재실행 (UTF-8 자동 적용) |
| Defender 0x800106ba | 무시 (설치 영향 없음) |
| winget 없음 | MS Store → "앱 설치 관리자" 설치 |

---

> 이 파일은 Claude 첫 실행 시 자동으로 읽히고, 처리 완료 후 삭제됩니다.
