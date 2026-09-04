# Agent Communication Protocols — MCP·A2A·ACP·AG-UI 4대 프로토콜

> **목적**: AI 에이전트 간 통신 프로토콜 총정리 (2025~2026 표준화)

---

## 1. MCP (Model Context Protocol) — Anthropic

### 개요
- **만든 곳**: Anthropic (2024.11 발표)
- **목적**: LLM ↔ 외부 도구/데이터 연결 (USB-C 같은 표준 인터페이스)
- **방향**: 단방향 (LLM이 도구 호출)
- **전송**: JSON-RPC 2.0 over stdio/SSE/Streamable HTTP
- **현재**: Claude Code, Cursor, Windsurf, Cline 등 채택

### 핵심 개념
| 개념 | 설명 |
|------|------|
| **Host** | MCP 클라이언트 실행하는 앱 (Claude Code, Cursor) |
| **Client** | 호스트 안에서 MCP 서버와 1:1 연결 |
| **Server** | 도구/데이터/프롬프트 제공 (npm 패키지) |
| **Tools** | 서버가 노출하는 함수 (API 호출, DB 쿼리 등) |
| **Resources** | 서버가 노출하는 데이터 (파일, DB 테이블) |
| **Prompts** | 서버가 제공하는 프롬프트 템플릿 |

### 설치
```bash
# Claude Code
claude mcp add <name> -- cmd /c npx -y <package>

# 예시
claude mcp add github -- cmd /c npx -y @modelcontextprotocol/server-github
claude mcp add filesystem -- cmd /c npx -y @modelcontextprotocol/server-filesystem C:\pjt
```

### 주요 MCP 서버
| 서버 | 패키지 | 용도 |
|------|--------|------|
| GitHub | @modelcontextprotocol/server-github | PR/이슈/코드 |
| Filesystem | @modelcontextprotocol/server-filesystem | 파일 접근 |
| Playwright | @playwright/mcp | 브라우저 자동화 |
| Fetch | @tokenizin/mcp-npx-fetch | HTTP 요청 |
| Slack | claude.ai 내장 | 채널/메시지 |
| Notion | claude.ai 내장 | 페이지/DB |
| Figma | claude.ai 내장 | 디자인 |
| Canva | claude.ai 내장 | 디자인 생성 |

### MCP 레지스트리
- **Smithery.ai** — MCP 서버 검색·설치 (128,000+ skills)
- **mcp.run** — MCP 서버 카탈로그
- **glama.ai/mcp/servers** — MCP 서버 목록

---

## 2. A2A (Agent-to-Agent) — Google

### 개요
- **만든 곳**: Google (2025.04 발표)
- **목적**: AI 에이전트 ↔ AI 에이전트 통신 (에이전트끼리 대화)
- **방향**: 양방향 (에이전트 간 협업)
- **전송**: HTTP + JSON-RPC + SSE/WebSocket
- **핵심 차이**: MCP는 "도구 호출", A2A는 "에이전트 간 태스크 위임"

### 핵심 개념
| 개념 | 설명 |
|------|------|
| **Agent Card** | 에이전트 자기소개 (이름, 능력, endpoint) — `/.well-known/agent.json` |
| **Task** | 에이전트에게 요청하는 작업 단위 |
| **Message** | 에이전트 간 대화 메시지 |
| **Artifact** | 태스크 결과물 (파일, 데이터) |
| **Push Notification** | 장기 태스크 완료 알림 |

### Agent Card 예시
```json
{
  "name": "Image Restoration Agent",
  "description": "90년대 저화질 영상을 고화질로 복원합니다",
  "url": "https://api.example.com/agent",
  "capabilities": {
    "streaming": true,
    "pushNotifications": true
  },
  "skills": [
    {"name": "upscale", "description": "이미지 초해상도"},
    {"name": "denoise", "description": "노이즈 제거"}
  ],
  "authentication": {"type": "bearer"}
}
```

### 태스크 흐름
```text
Client Agent                    Remote Agent
    │                               │
    ├── POST /tasks (create) ──────►│
    │                               ├── 작업 시작
    │◄── SSE (progress) ───────────┤
    │◄── SSE (artifact) ───────────┤
    │◄── SSE (complete) ───────────┤
    │                               │
    ├── GET /tasks/{id} (조회) ────►│
    │◄── Task status ──────────────┤
```

### Python SDK
```python
pip install a2a-sdk  # Google A2A SDK

from a2a import A2AClient

client = A2AClient("https://remote-agent.example.com")
card = client.get_agent_card()
print(card.skills)

task = client.create_task(
    skill="upscale",
    input={"image_url": "https://..."},
)
result = await task.wait()
```

### 참고
- 스펙: github.com/google/A2A
- 50+ 파트너 (Salesforce, SAP, MongoDB, LangChain, CrewAI 등)

---

## 3. ACP (Agent Communication Protocol) — IBM / Linux Foundation

### 개요
- **만든 곳**: IBM + BeeAI + Linux Foundation (2025.05 발표)
- **목적**: 에이전트 ↔ 에이전트 (프레임워크 독립적)
- **방향**: 양방향 (A2A와 유사하지만 더 개방적)
- **전송**: HTTP + SSE
- **핵심 차이**: A2A보다 **단순** + **프레임워크 독립** (LangGraph, CrewAI, AutoGen 다 호환)

### 핵심 개념
| 개념 | 설명 |
|------|------|
| **Agent** | ACP 호환 에이전트 (어떤 프레임워크든) |
| **Run** | 에이전트 실행 세션 |
| **Message** | 멀티모달 메시지 (텍스트, 이미지, 파일) |
| **Await** | 에이전트가 사용자/다른 에이전트 입력 대기 |
| **Agent Card** | 에이전트 능력 선언 (A2A와 유사) |

### API (OpenAPI 기반)
```sql
POST   /agents                    # 에이전트 목록
POST   /agents/{agent_id}/runs    # 실행 시작
GET    /agents/{agent_id}/runs/{run_id}  # 상태 조회
POST   /agents/{agent_id}/runs/{run_id}/continue  # 재개
DELETE /agents/{agent_id}/runs/{run_id}  # 취소
```

### Python SDK
```python
pip install acp-sdk  # IBM ACP SDK

from acp_sdk.client import Client

async with Client("http://localhost:8000") as client:
    agents = await client.agents()
    print(agents)
    
    run = await client.run(
        agent_id="image-restorer",
        input=[{"type": "text", "text": "이 이미지를 4x 업스케일해줘"}],
    )
    
    async for event in run.stream():
        print(event)
```

### BeeAI — ACP 구현체
```bash
pip install beeai-framework  # BeeAI 에이전트 프레임워크
# 또는
npm install bee-agent-framework
```

### 참고
- 스펙: github.com/i-am-bee/acp
- BeeAI: github.com/i-am-bee/beeai
- Linux Foundation AI & Data 산하

---

## 4. AG-UI (Agent-User Interface Protocol) — CopilotKit

### 개요
- **만든 곳**: CopilotKit (2025.05 발표)
- **목적**: AI 에이전트 ↔ 프론트엔드 UI 연결 (에이전트가 UI 직접 조작)
- **방향**: 에이전트 → UI (실시간 렌더링)
- **전송**: HTTP + SSE (이벤트 스트리밍)
- **핵심 차이**: MCP/A2A/ACP는 백엔드 간 통신, AG-UI는 **프론트엔드 렌더링**

### 핵심 개념
| 개념 | 설명 |
|------|------|
| **Event** | 에이전트→UI 이벤트 스트림 (16종) |
| **Text Message** | 텍스트 청크 스트리밍 |
| **Tool Call** | 에이전트가 UI 도구 호출 (폼 채우기, 버튼 클릭 등) |
| **State** | 에이전트 ↔ UI 공유 상태 (실시간 동기화) |
| **Lifecycle** | run_started → messages → tool_calls → run_finished |

### 16가지 이벤트
```text
RUN_STARTED          실행 시작
RUN_FINISHED         실행 종료
RUN_ERROR            에러

TEXT_MESSAGE_START    텍스트 시작
TEXT_MESSAGE_CONTENT  텍스트 청크 (스트리밍)
TEXT_MESSAGE_END     텍스트 완료

TOOL_CALL_START      도구 호출 시작
TOOL_CALL_ARGS       도구 인자 (스트리밍)
TOOL_CALL_END        도구 호출 완료

STATE_SNAPSHOT       전체 상태 스냅샷
STATE_DELTA          상태 변경 (JSON Patch)

MESSAGES_SNAPSHOT    메시지 히스토리

STEP_STARTED         단계 시작
STEP_FINISHED        단계 완료

CUSTOM               커스텀 이벤트
RAW                  Raw 데이터
```

### JavaScript SDK
```bash
npm install @ag-ui/client    # 클라이언트
npm install @ag-ui/encoder   # 이벤트 인코더
npm install @copilotkit/react-core   # React 통합
```

```typescript
// AG-UI 이벤트 수신 (프론트엔드)
import { AGUIClient } from '@ag-ui/client';

const client = new AGUIClient('https://agent.example.com');
const stream = client.runAgent({
  threadId: 'thread-1',
  messages: [{ role: 'user', content: '대시보드 만들어줘' }],
});

for await (const event of stream) {
  switch (event.type) {
    case 'TEXT_MESSAGE_CONTENT':
      appendToChat(event.content);
      break;
    case 'STATE_DELTA':
      applyStatePatch(event.delta);
      break;
    case 'TOOL_CALL_START':
      showToolExecution(event.toolName);
      break;
  }
}
```

### Python SDK (에이전트 측)
```bash
pip install ag-ui-protocol   # AG-UI Python SDK
pip install copilotkit        # CopilotKit Python
```

```python
from ag_ui.encoder import EventEncoder

encoder = EventEncoder()

# 에이전트가 UI에 이벤트 스트리밍
async def agent_handler(request):
    async def generate():
        yield encoder.encode({"type": "RUN_STARTED", "runId": "run-1"})
        yield encoder.encode({"type": "TEXT_MESSAGE_START", "messageId": "msg-1"})
        yield encoder.encode({"type": "TEXT_MESSAGE_CONTENT", "content": "분석 중..."})
        yield encoder.encode({"type": "TEXT_MESSAGE_END"})
        yield encoder.encode({"type": "RUN_FINISHED"})
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### CopilotKit (AG-UI 활용 프레임워크)
```bash
npm install @copilotkit/react-core @copilotkit/react-ui
```

```tsx
// React에서 AI 에이전트 통합
import { CopilotKit, CopilotSidebar } from '@copilotkit/react-core';

function App() {
  return (
    <CopilotKit runtimeUrl="/api/copilot">
      <CopilotSidebar>
        <YourApp />
      </CopilotSidebar>
    </CopilotKit>
  );
}
```

### 참고
- 스펙: github.com/ag-ui-protocol/ag-ui
- CopilotKit: github.com/CopilotKit/CopilotKit (30k+ stars)
- 호환: LangGraph, CrewAI, AutoGen, Mastra, AG2

---

## 5. 4대 프로토콜 비교

| 항목 | **MCP** | **A2A** | **ACP** | **AG-UI** |
|------|---------|---------|---------|-----------|
| 만든 곳 | Anthropic | Google | IBM / LF | CopilotKit |
| 발표 | 2024.11 | 2025.04 | 2025.05 | 2025.05 |
| 방향 | LLM→도구 | 에이전트↔에이전트 | 에이전트↔에이전트 | 에이전트→UI |
| 용도 | 도구/데이터 접근 | 태스크 위임·협업 | 프레임워크 독립 협업 | 프론트엔드 렌더링 |
| 전송 | JSON-RPC / stdio / SSE | HTTP / JSON-RPC / SSE | HTTP / SSE / OpenAPI | HTTP / SSE |
| 스트리밍 | SSE | SSE + WebSocket | SSE | SSE (16 이벤트) |
| 채택 | Claude, Cursor, Windsurf | Google, 50+ 파트너 | IBM, LangGraph, CrewAI | CopilotKit, 30k+ stars |
| 보완 관계 | **도구 연결** | **에이전트 협업** | **프레임워크 통합** | **UI 렌더링** |
| 우리 킷 |  14개 MCP 연결 |  레퍼런스 |  레퍼런스 |  레퍼런스 |

### 관계도
```text
┌─────────────────────────────────────────┐
│              AI Application             │
│                                         │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │ Agent A  │  │ Agent B  │  │Agent C ││
│  │(Claude)  │  │(Gemini)  │  │(GPT)   ││
│  └──┬───┬───┘  └──┬───┬───┘  └──┬─────┘│
│     │   │         │   │         │       │
│     │   └────A2A──┘   └──ACP───┘       │
│     │         or ACP                    │
│     │                                   │
│     └──────MCP──────┐                   │
│                     │                   │
│  ┌──────────────────┴───────────────┐   │
│  │           도구 / 서비스            │   │
│  │  DB  │  API  │  Slack  │  GitHub │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**MCP** = 에이전트가 도구를 쓰는 방법
**A2A/ACP** = 에이전트끼리 협업하는 방법
→ **세 가지는 경쟁이 아니라 보완 관계**

---

## 5. 우리 킷 적용 현황

| 프로토콜 | 현재 | 계획 |
|---------|------|------|
| **MCP** |  14개 서버 연결 (Slack·Notion·Figma·GitHub 등) | 유지 + 자동 점검 |
| **A2A** |  exec_orch 라우팅이 유사 패턴 (Claude→Codex→Gemini) | Agent Card 표준 채택 가능 |
| **ACP** |  미구현 | BeeAI 프레임워크 검토 |

### 우리 exec_orch 가 이미 A2A/ACP 패턴
```text
사용자 요청 → Claude (설계) → task-instruction.md
                                    ↓
                              Codex (구현) → 결과
                                    ↓
                              Gemini (검증) → 최종
```

이건 본질적으로 **A2A 패턴**. 공식 프로토콜 채택하면 외부 에이전트와도 연동 가능.
