# Claude Web ↔ CLI 브릿지 (4가지 방식)

> **용도**: Web (claude.ai) 에서 계획·질문·리서치 → CLI 에서 실행·파일·shell. 애매한 것만 사용자에게 보고.
> **원칙**: 명령 프롬프트 (`session-bootstrap-prompt.md`) 를 web·CLI 양쪽에 로드 → 헌장 A~F 공통 준수.

---

## 개요

```text
[Web]                    [사용자]                    [CLI]
계획·질문·리서치            결정·감독                    실행·파일·shell
자율 판단                  애매만 답                    자율 실행
    │                        │                          │
    │   task 생성             │                          │
    ├────────────────────────────────────────────────>  │
    │     (파일/MCP/API)                                 │
    │                        │                          │
    │                        │  결과 stream              │
    │  <──────────────────────────────────────────────  │
    │                        │                          │
    │   요약·다음 계획         │                          │
    ├─── 애매 보고 ─────────>  │                          │
    │                        ├─ 결정 ──────────────>    │
    │                                                   │
```

---

## 방식 1: 파일 브릿지 (기존 `~/.claude/orca/` — 즉시 사용 가능)

**추천**: kit 에 이미 구축됨. 추가 설치 X.

### 활성화

1. **web** 이 `~/.claude/orca/` 폴더에 task 파일 작성 (예: `~/.claude/orca/task-<slug>.md`)
2. **CLI** worker (`codex-auto-global` / `gemini-auto-global`) 가 폴링 → 실행 → 결과 저장
3. **web** 이 결과 파일 read

### 사용 흐름

**Web 세션 (사람이 대신 붙이거나 Copy)**:
```text
[web] 사용자 지시 접수
  ↓
[web] 헌장 A~F 준수 판단
  ↓
[web] 명확 → task 파일 생성:
  ~/.claude/orca/task-<slug>.md
  (task-instruction-template.md 형식: Role/Context/Files/Acceptance/CoT/Negative/ReAct/완료검증/Confidence)
  ↓
[cli-worker] 폴링 (5s) → task 실행
  ↓
[cli-worker] 결과 저장:
  ~/.claude/orca/results/<slug>.json
  ↓
[web] 결과 read → 사용자 요약·다음 계획
```

### 명령

```bash
# CLI 측: 전역 워커 활성화
python .claude/scripts/route.py --enable-global-worker

# 또는 orca-dispatch 로 직접 큐잉
orca-dispatch task-instruction.md codex
```

### 장점·단점
- ✅ 즉시 사용 (kit 에 이미 있음)
- ✅ 여러 프로젝트 공통 (`~/.claude/orca/`)
- ✅ SQLite 상태 관리 (`orca.db`)
- ⚠️ web ↔ 파일 시스템 직접 접근 필요 (Managed Agents API 사용 시 file 대신 API)

---

## 방식 2: MCP Server (Anthropic 공식 표준)

**추천**: 프로덕션·팀 협업.

### 설치

```bash
# CLI 측: MCP server 로 kit 기능 export
npm install -g @anthropic-ai/mcp-server-filesystem
# 또는 우리 kit 자체를 MCP server 로 wrap (향후)
```

### 등록

**Web 측 (Claude.ai)**: Settings → Connectors → Add MCP Server → CLI 측 endpoint 입력.

**CLI 측 (`.mcp.json`)**:
```json
{
  "mcpServers": {
    "orchestration-kit": {
      "command": "python",
      "args": ["-m", "orchestration_kit.mcp_server"],
      "env": {}
    }
  }
}
```

### 흐름

```text
[web] Claude.ai 대화 → MCP 커넥터로 CLI kit 도구 호출
   → orca-dispatch·file read·bash 등 실제 실행
   → 결과 stream 으로 web 에 반환
```

### 장점·단점
- ✅ Anthropic 공식 표준 (long-term 지원)
- ✅ 도구 단위 세밀 권한
- ✅ 여러 web 사용자 공유 가능
- ⚠️ MCP server 코드 작성 필요 (Python·Node)
- ⚠️ CLI 는 항상 실행 중이어야 (Remote Agent 로 해결 가능)

---

## 방식 3: Managed Agents API (2026-07-22+)

**추천**: 팀·프로덕션·SDK 통합.

### 활성화

```python
# Anthropic Managed Agents API
from anthropic import Anthropic
client = Anthropic()

agent = client.agents.create(
  name="orchestration-kit-agent",
  model="claude-opus-5",
  system_prompt=open("outputs/install/session-bootstrap-prompt.md").read(),
  tools=[...],  # kit 도구 매핑
)

# session 생성 (initial_events 로 kit 원칙 seed · up to 50)
session = client.agents.sessions.create(
  agent_id=agent.id,
  initial_events=[
    {"type": "user.message", "content": "orchestration_v1 헌장 준수"}
  ],
)

# session thread event stream (실시간 관측)
for event in client.agents.sessions.threads.stream(session_id=session.id, thread_id=thread.id):
    ...

# webhooks (환경·메모리 lifecycle 반응)
client.agents.webhooks.create(
  url="https://your-endpoint/webhook",
  events=["environment.created", "memory_store.updated"],
)
```

### 흐름

- Web·CLI 모두 같은 agent 세션 참조 → 상태 공유
- Session thread event stream 으로 실시간 관측
- Webhooks 로 lifecycle 반응 (polling X)

### 장점·단점
- ✅ 공식 API (Anthropic 지원)
- ✅ Effort·session·thread 세밀 제어
- ✅ 30일 data retention
- ⚠️ API 비용 (agent + session)
- ⚠️ 코드 통합 필요

---

## 방식 4: Remote Agent (VPS + SSH)

**추천**: 24/7 원격 운영·PC 꺼져도 작동.

### 활성화 (이미 kit 에 있음)

```bash
# 처음 세팅
claude → /exec_remote-setup    # Oracle Free Tier VPS 4 OCPU · 24GB
claude → /exec_remote-ssh       # SSH 키 생성 + Host 등록
claude → /exec_remote-deploy    # VPS 부트스트랩 + Claude Code 설치
```

### 흐름

- **Web** (스마트폰 브라우저·PC 브라우저) → https://claude.ai → 사용자가 지시
- **VPS** (Oracle Cloud) 는 24/7 Claude Code CLI 실행 · tmux 세션 유지
- **CLI** 는 SSH 로 접근 (Termius·Blink Shell·iSH)
- **파일 브릿지** (`~/.claude/orca/`) 를 VPS 에 유지 → web·모바일에서 pull

### 장점·단점
- ✅ 24/7 작동 (PC 꺼져도)
- ✅ 스마트폰에서도 접근 (`/exec_remote-mobile`)
- ✅ Oracle Free Tier 무료
- ⚠️ VPS 초기 세팅 필요 (kit `/exec_remote-*` 자동화)

---

## 방식 비교

| 항목 | 파일 브릿지 | MCP Server | Managed Agents | Remote Agent |
|---|---|---|---|---|
| **설치 필요?** | ❌ 즉시 사용 | ⚠️ MCP wrap 필요 | ⚠️ SDK 통합 | ✅ VPS 세팅 |
| **비용** | 무료 | 무료 | Agent + Session API | Oracle Free Tier |
| **실시간성** | 5s 폴링 | 즉시 | Event stream 실시간 | SSH tunnel 실시간 |
| **여러 사용자** | ❌ (단일) | ✅ | ✅ | ⚠️ SSH 계정별 |
| **PC 꺼져도?** | ❌ | ❌ | ⚠️ CLI 서버 필요 | ✅ |
| **모바일** | ⚠️ SSH 로 | ⚠️ 커넥터 | ✅ web | ✅ Termius·Blink |
| **성숙도** | ✅ 즉시 | ✅ 표준 | ✅ 최신 (2026-07) | ✅ kit v2 |

---

## 지금 즉시 시작하는 법 (파일 브릿지)

```bash
# 1. 전역 워커 활성화 (CLI 측)
cd <kit_root>
python .claude/scripts/route.py --enable-global-worker

# 2. Web 사용자에게 session-bootstrap-prompt.md 붙임
# 3. Web 에서 task 지시 → task 파일 생성 (직접 or ChatGPT/Web 이 대신)
# 4. CLI 워커가 자동 폴링·실행
# 5. 결과 확인:
ls ~/.claude/orca/results/
```

---

## 자율 vs 사용자 보고 (session-bootstrap-prompt.md § 9 정합)

Web·CLI 모두 이 판정 따름:

- **명확** → 자율 실행 (Zero-touch F3)
- **애매** → 사용자 보고
- **위험** → approval-gate (C6)

즉 web 이 명령 프롬프트 준수 시 web 이 대부분 자율 판단하고 애매·위험한 것만 사용자에게 넘김 → 사용자 인지 부하 최소.

---

## 참조

- `outputs/install/session-bootstrap-prompt.md` (명령 프롬프트)
- `outputs/install/orchestration-kit-total-guide.md` (총망라)
- `plugins/exec_remote/*` (VPS 24/7 원격 운영)
- `plugins/exec_orch/skills/route_dispatch.md` (라우팅)
- `.claude/scripts/route.py` (전역 워커)
- `.mcp.json` (MCP 등록)
