"""
build-korean-html-diagrams.py v3 — 20 챕터 풍부한 HTML/CSS+SVG 일괄.
teaching-doc.md v2: 한글 대체 + SVG 화살표 + 풍부한 일러스트.
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "docs" / "screens" / "arch-kor"
OUT.mkdir(parents=True, exist_ok=True)


CSS = """
* { margin:0; padding:0; box-sizing:border-box; font-family:'Malgun Gothic','맑은 고딕','Pretendard',sans-serif; }
body { width:1300px; height:900px; padding:14px 22px; overflow:hidden;
       display:flex; flex-direction:column; justify-content:space-between;
       background:linear-gradient(135deg,#FAF6FF 0%,#F0F4FF 35%,#FFF8FA 70%,#FFFAF0 100%); }
.title { font-size:42px; font-weight:900; letter-spacing:-0.5px;
         background:linear-gradient(135deg,#3B1B5C 0%,#1F3864 35%,#3F6FB5 70%,#C00050 100%);
         -webkit-background-clip:text; -webkit-text-fill-color:transparent; text-align:center; margin-bottom:4px; }
.subtitle { font-size:18px; color:#5C6B84; text-align:center; margin-bottom:14px; font-weight:500; }

.grid2 { display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:24px; }
.grid3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:18px; margin-bottom:24px; }
.grid4 { display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:14px; margin-bottom:24px; }
.row5 { display:grid; grid-template-columns:repeat(5,1fr); gap:14px; margin-bottom:24px; }

.card { padding:13px 14px; border-radius:13px; box-shadow:0 5px 14px rgba(0,0,0,0.08);
        background:linear-gradient(135deg,#fff,#f7f9fc); border:2px solid #4472C4; position:relative; }
.card-icon { font-size:42px; margin-bottom:8px; display:block; }
.card-title { font-size:33px; font-weight:800; color:#1F3864; margin-bottom:8px; }
.card-desc { font-size:21px; color:#333; line-height:1.55; }
.card-num { position:absolute; top:10px; right:14px; font-size:48px; font-weight:900;
            opacity:0.12; color:#1F3864; }

.chip { display:inline-block; padding:5px 14px; background:rgba(31,56,100,0.08); color:#1F3864;
        border-radius:14px; font-size:22px; font-weight:600; margin:3px; }

.banner { margin-top:10px; padding:10px 16px; background:linear-gradient(135deg,#1F3864,#3F6FB5);
          color:white; border-radius:12px; box-shadow:0 6px 18px rgba(31,56,100,0.25); }
.banner-title { font-size:20px; font-weight:800; margin-bottom:4px; opacity:0.95; }
.banner-content { font-size:15px; line-height:1.5; opacity:0.94; }
.banner b { color:#FFE699; }

.flow-step { display:flex; align-items:center; gap:12px; padding:6px 12px; border-radius:10px;
             box-shadow:0 3px 10px rgba(0,0,0,0.07); margin-bottom:4px; position:relative; }
.flow-icon-box { width:42px; height:42px; border-radius:10px; display:flex; align-items:center;
                 justify-content:center; flex-shrink:0; font-size:30px; }
.flow-title { font-size:18px; font-weight:800; color:#1F3864; margin-bottom:2px; }
.flow-desc { font-size:13px; color:#444; line-height:1.35; }
.flow-num { font-size:34px; font-weight:900; opacity:0.15; color:#1F3864; margin-left:auto; }
.context-arrow { display:none }

.l1 { background:linear-gradient(135deg,#FFF5F5,#FFEBEB); border-left:6px solid #E53E3E; }
.l1 .flow-icon-box { background:linear-gradient(135deg,#FC8181,#E53E3E); color:white; font-size:32px; }
.l2 { background:linear-gradient(135deg,#FFFAF0,#FFF1D5); border-left:6px solid #DD6B20; }
.l2 .flow-icon-box { background:linear-gradient(135deg,#F6AD55,#DD6B20); color:white; font-size:32px; }
.l3 { background:linear-gradient(135deg,#FEFCBF,#FAF089); border-left:6px solid #D69E2E; }
.l3 .flow-icon-box { background:linear-gradient(135deg,#ECC94B,#D69E2E); color:white; font-size:32px; }
.l4 { background:linear-gradient(135deg,#F0FFF4,#C6F6D5); border-left:6px solid #38A169; }
.l4 .flow-icon-box { background:linear-gradient(135deg,#68D391,#38A169); color:white; font-size:32px; }
.l5 { background:linear-gradient(135deg,#EBF8FF,#BEE3F8); border-left:6px solid #3182CE; }
.l5 .flow-icon-box { background:linear-gradient(135deg,#63B3ED,#3182CE); color:white; font-size:32px; }
.l6 { background:linear-gradient(135deg,#FAF5FF,#E9D8FD); border-left:6px solid #805AD5; }
.l6 .flow-icon-box { background:linear-gradient(135deg,#B794F4,#805AD5); color:white; font-size:32px; }

.gradient-1 { background:linear-gradient(135deg,#FFF8E1,#FFE699); border-color:#D69E2E; }
.gradient-2 { background:linear-gradient(135deg,#E0E7FF,#C7D2FE); border-color:#4F46E5; }
.gradient-3 { background:linear-gradient(135deg,#DCFCE7,#A7F3D0); border-color:#10B981; }
.gradient-4 { background:linear-gradient(135deg,#FCE7F3,#FBCFE8); border-color:#DB2777; }
.gradient-5 { background:linear-gradient(135deg,#DBEAFE,#93C5FD); border-color:#2563EB; }
.danger { background:linear-gradient(135deg,#FFE4E1,#FFCCCC); border-color:#DC2626; }

.compare-tbl { width:100%; border-collapse:separate; border-spacing:5px; margin-top:12px; }
.compare-tbl th { background:linear-gradient(135deg,#1F3864,#3F6FB5); color:white; padding:10px 12px; text-align:left;
                  border-radius:8px; font-weight:700; font-size:21px; }
.compare-tbl td { padding:9px 12px; background:linear-gradient(135deg,#fff,#f8fafc); border-radius:8px;
                  vertical-align:top; font-size:19px; border:1px solid #e2e8f0; line-height:1.5; }
"""

PAGES = {}


def page(title, subtitle, body, w=1400, h=900):
    # h>900 무시 — viewport 1300×900 강제. 콘텐츠 자연 fit (body flex space-between).
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}
body {{ height:900px; }}</style></head><body>
<div class="title">{title}</div>
<div class="subtitle">{subtitle}</div>
{body}
</body></html>"""


# ============================================================
# Chapter 1 — Gen vs Agentic vs AI Agent (정보 축소 + 큰 글씨)
# ============================================================
PAGES["01-gen-vs-agentic-vs-agent.png"] = page(
    "Generative vs Agentic vs AI Agent",
    "글만 쓰는 AI -> 단계까지 짜는 AI -> 손까지 움직이는 AI",
    """
<style>
.big-card { padding:22px 18px; border-radius:18px; box-shadow:0 8px 22px rgba(0,0,0,0.10);
            text-align:center; position:relative; min-height:450px; }
.big-icon { font-size:62px; margin-bottom:10px; }
.big-title { font-size:30px; font-weight:900; color:#1F3864; margin-bottom:10px; }
.big-tag { display:inline-block; padding:5px 14px; background:rgba(31,56,100,0.12); color:#1F3864;
           border-radius:16px; font-size:20px; font-weight:700; margin:4px; }
.big-line { font-size:22px; color:#333; line-height:1.55; text-align:left; margin-top:12px; padding:0 8px; }
.big-line b { color:#1F3864; }
.big-num { position:absolute; top:12px; right:16px; font-size:60px; font-weight:900; opacity:0.1; color:#1F3864; }
</style>

<div class="grid3" style="margin-top:14px;">
  <div class="big-card gradient-1">
    <span class="big-num">①</span>
    <div class="big-icon">✏</div>
    <div class="big-title">Generative AI</div>
    <div class="big-tag">한 번 답하고 끝</div>
    <div class="big-line">
      <b>하는 일</b>: 글-그림 생성<br>
      <b>예시</b>: ChatGPT, DALL-E<br>
      <b>비유</b>: 카피라이터<br>
      <b>주도성</b>: 낮음
    </div>
  </div>

  <div class="big-card gradient-2">
    <span class="big-num">②</span>
    <div class="big-icon"></div>
    <div class="big-title">Agentic AI</div>
    <div class="big-tag">스스로 단계 짜기</div>
    <div class="big-line">
      <b>하는 일</b>: 작업 분해 + 계획<br>
      <b>예시</b>: 여행 자동 설계<br>
      <b>비유</b>: 신입 매니저<br>
      <b>주도성</b>: 중간
    </div>
  </div>

  <div class="big-card gradient-3">
    <span class="big-num">③</span>
    <div class="big-icon"></div>
    <div class="big-title">AI Agent ★</div>
    <div class="big-tag">외부 API 까지 실행</div>
    <div class="big-line">
      <b>하는 일</b>: 호출 + 자가 평가<br>
      <b>예시</b>: 자동 예약 - 정리<br>
      <b>비유</b>: 경력 매니저<br>
      <b>주도성</b>: 높음
    </div>
  </div>
</div>

<div class="banner" style="margin-top:14px;">
  <div class="banner-title" style="font-size:22px;"> 우리 orchestration_v1 = AI Agent + Multi-Agent System</div>
  <div class="banner-content" style="font-size:17px;">
    여러 에이전트 협력 — <b>Claude(설계) -> Codex×4(구현) -> Gemini×2(검증) -> Haiku×2(판정)</b>
  </div>
</div>
""")


# ============================================================
# Chapter 2 — 5 Cores (이미 풍부 버전 있음)
# ============================================================
PAGES["02-5-cores.png"] = page(
    "에이전트 5가지 핵심 부품",
    "User Request -> Agent Response — 5 레이어 필수",
    """
<div class="flow-step l1">
  <div class="flow-icon-box"></div>
  <div>
    <div class="flow-title">Guardrails & Gateway — 입구 경비실</div>
    <div class="flow-desc">잘못된 입력-개인정보-과도한 호출 차단</div>
    <div style="margin-top:6px"><span class="chip">Input Validation</span><span class="chip">PII Filtering</span><span class="chip">Rate Limiting</span><span class="chip">Output Sanitization</span></div>
  </div>
  <div class="flow-num">01</div>
</div>
<div class="context-arrow">↓ context passed ↓</div>

<div class="flow-step l2">
  <div class="flow-icon-box"></div>
  <div>
    <div class="flow-title">Orchestration — 작업 분장</div>
    <div class="flow-desc">큰 일을 잘게 나누고 어느 에이전트가 할지 정함</div>
    <div style="margin-top:6px"><span class="chip">Task Decomposition</span><span class="chip">Agent Routing</span><span class="chip">State Machine</span><span class="chip">Error Recovery</span></div>
  </div>
  <div class="flow-num">02</div>
</div>
<div class="context-arrow">↓ tool call ↓</div>

<div class="flow-step l3">
  <div class="flow-icon-box">[MCP]</div>
  <div>
    <div class="flow-title">Tool & MCP Integration — 도구함</div>
    <div class="flow-desc">GitHub-DB-API 같은 외부 도구를 안전하게 연결</div>
    <div style="margin-top:6px"><span class="chip">MCP Server</span><span class="chip">Tool Registry</span><span class="chip">Sandboxed</span><span class="chip">Audit Log</span></div>
  </div>
  <div class="flow-num">03</div>
</div>
<div class="context-arrow">↓ context passed ↓</div>

<div class="flow-step l4">
  <div class="flow-icon-box"></div>
  <div>
    <div class="flow-title">Memory & Context — 기억</div>
    <div class="flow-desc">짧은(대화)-중간(세션)-긴(벡터 DB) 기억 구분</div>
    <div style="margin-top:6px"><span class="chip">Short-Term</span><span class="chip">Mid-Term</span><span class="chip">Long-Term</span></div>
  </div>
  <div class="flow-num">04</div>
</div>
<div class="context-arrow">↓ context passed ↓</div>

<div class="flow-step l5">
  <div class="flow-icon-box">[STAT]</div>
  <div>
    <div class="flow-title">Observability — CCTV</div>
    <div class="flow-desc">왜 그렇게 답했는지 추적. Tracing - Token Metrics - Decision Logs - Alerting</div>
  </div>
  <div class="flow-num">05</div>
</div>

<div class="banner">
  <div class="banner-title"> 우리 orchestration_v1 의 5 핵심</div>
  <div class="banner-content"><b>①</b> Hook - <b>②</b> exec_orch - <b>③</b> MCP - <b>④</b> orca.db + memory - <b>⑤</b> watchdog</div>
</div>
""")


# ============================================================
# Chapter 3 — 8 모델 유형
# ============================================================
PAGES["08-8-models.png"] = page(
    "AI 에이전트의 8가지 두뇌",
    "작업에 맞는 뇌를 골라써야 비용-품질 최적",
    """
<div class="grid4">
  <div class="card gradient-5"><span class="card-icon">[NOTE]</span><div class="card-title">GPT</div>
    <div class="card-desc">글의 다음 단어 잘 맞춤. 가장 흔한 뇌.<br><b>예</b>: GPT-4, Claude</div></div>
  <div class="card gradient-2"><span class="card-icon"></span><div class="card-title">MoE</div>
    <div class="card-desc">전문가 뇌 모음. 질문 보고 골라 씀.<br><b>예</b>: Qwen 2</div></div>
  <div class="card gradient-1"><span class="card-icon"></span><div class="card-title">LRM</div>
    <div class="card-desc">긴 추론 펼침. 검증 강함.<br><b>예</b>: Gemini 1.5 Flash</div></div>
  <div class="card gradient-3"><span class="card-icon"></span><div class="card-title">VLM</div>
    <div class="card-desc">이미지 + 글 같이 처리.<br><b>예</b>: Claude 4.x, GPT-4V</div></div>
  <div class="card gradient-1"><span class="card-icon"></span><div class="card-title">SLM</div>
    <div class="card-desc">작고 빠른 뇌. 모바일-엣지.<br><b>예</b>: Gemma 2, Phi</div></div>
  <div class="card danger"><span class="card-icon">[FAST]</span><div class="card-title">LAM</div>
    <div class="card-desc">행동(API 호출) 결정 잘함.<br><b>예</b>: Salesforce X-LAM</div></div>
  <div class="card gradient-4"><span class="card-icon">[LIST]</span><div class="card-title">HRM</div>
    <div class="card-desc">계획->실행 분리. 복잡 분해.<br><b>예</b>: Sapient Planner</div></div>
  <div class="card" style="background:#F5F5F5;border-color:#999"><span class="card-icon"></span><div class="card-title">mHC</div>
    <div class="card-desc">여러 흐름 동시 (실험적).<br><b>예</b>: Deepseek mHC</div></div>
</div>

<div class="banner">
  <div class="banner-title"> 우리 시스템 = 6.5/8 활용</div>
  <div class="banner-content">
    <b>GPT</b>(Opus-Sonnet) - <b>MoE</b>(시스템 라우팅 — route_dispatch) -
    <b>LRM</b>(Extended Thinking) - <b>VLM</b>(이번 세션 이미지 24장 분석) -
    <b>SLM</b>(Haiku-Ollama) - <b>LAM</b>(MCP 도구 호출) - <b>HRM</b>(task-instruction -> codex)
  </div>
</div>
""", h=900)


# ============================================================
# Chapter 4 — 9 Silent Killers
# ============================================================
PAGES["09-9-killers.png"] = page(
    "9가지 숨은 함정 — 에이전트가 망하는 패턴",
    "이 9가지만 피하면 프로덕션 사고 80% 감소",
    """
<div class="grid3" style="margin-bottom:14px">""" + "".join(f"""
  <div class="card danger" style="padding:12px 14px">
    <span class="card-icon" style="font-size:32px;margin-bottom:4px">{ico}</span>
    <div class="card-title" style="font-size:17px">{num} {name}</div>
    <div class="card-desc" style="font-size:13px;line-height:1.45">{desc}<br><b style="color:#0F766E">✓</b> {fix}</div>
  </div>""" for ico, num, name, desc, fix in [
    ("[FIX]", "01", "Tool Bloat", "도구 많음->모델 헷갈림", "적게-날카롭게"),
    ("", "02", "Context Decay", "대화 길어지면 규칙 묻힘", "핵심 규칙 다시 박기"),
    ("☠", "03", "Retrieval Poison", "잘못 문서->틀림", "필터-랭킹-검증"),
    ("", "04", "Runaway Loop", "재시도 847번", "예산-중지 가드"),
    ("[NOTE]", "05", "Schema Drift", "v1->v2 못 봄", "스키마 버전-검증"),
    ("", "06", "Eval Blindness", "10 예시로만 검증", "실 트래픽 슬라이스"),
    ("", "07", "Non-Determinism", "같은 입력 다른 답", "랜덤 제어-추적"),
    ("", "08", "Cost Blind", "$48,200 청구", "작업당 비용 추적"),
    ("", "09", "No Failure", "모르면 거짓말", "거절-헤지 정책"),
]) + """
</div>

<div class="banner">
  <div class="banner-title"> 우리 시스템 — 9 함정 대응</div>
  <div class="banner-content">
    <b>#1</b> plugin 분리 - <b>#4</b> watchdog backoff - <b>#6</b> eval_quality - <b>#8</b> orca.db budget - <b>#9</b> failure-mode.md
  </div>
</div>
""")


# ============================================================
# Chapter 5 — AI Stack 5 layers
# ============================================================
PAGES["03-ai-stack-5layers.png"] = page(
    "AI 스택 5층 — 인프라부터 인터페이스까지",
    "AI 시스템은 5층 빌딩. 아래->위로",
    """
<div class="flow-step l5"><div class="flow-icon-box"></div>
  <div><div class="flow-title">5 Interface — 사용자 만남</div>
  <div class="flow-desc">FastAPI - Streamlit - React - Vue - Auth0 - MCP</div></div>
  <div class="flow-num">05</div></div>
<div class="context-arrow">↑ 사람과 닿는 곳 ↑</div>

<div class="flow-step l1"><div class="flow-icon-box"></div>
  <div><div class="flow-title">4 Orchestration — 여러 에이전트 흐름</div>
  <div class="flow-desc">LangGraph - CrewAI - mem0 - Claude Agent SDK - Google ADK</div></div>
  <div class="flow-num">04</div></div>
<div class="context-arrow">↑ 작업 분배 ↑</div>

<div class="flow-step l3"><div class="flow-icon-box"></div>
  <div><div class="flow-title">3 LLM — 진짜 뇌</div>
  <div class="flow-desc">Claude Opus 4.6 - Llama 4 - GPT 5.3 - Kimi K2.5 - OpenRouter</div></div>
  <div class="flow-num">03</div></div>
<div class="context-arrow">↑ 추론 ↑</div>

<div class="flow-step l4"><div class="flow-icon-box"></div>
  <div><div class="flow-title">2 Data — RAG 의 재료</div>
  <div class="flow-desc">Chroma - Pinecone - Weaviate - Qdrant - Neo4j</div></div>
  <div class="flow-num">02</div></div>
<div class="context-arrow">↑ 저장-검색 ↑</div>

<div class="flow-step l2"><div class="flow-icon-box"></div>
  <div><div class="flow-title">1 Infrastructure — 하드웨어-컨테이너</div>
  <div class="flow-desc">Docker - Kubernetes - AWS - GCP - Azure - RunPod</div></div>
  <div class="flow-num">01</div></div>

<div class="banner">
  <div class="banner-title"> 우리 = 5층 다 갖춤 (작은 규모)</div>
  <div class="banner-content">
    <b>1</b> 사용자 PC + VPS - <b>2</b> SQLite (orca.db) - <b>3</b> Claude/Codex/Gemini/Haiku -
    <b>4</b> exec_orch (자체) - <b>5</b> Claude Code CLI + VS Code
  </div>
</div>
""", h=1200)


# ============================================================
# Chapter 6 — Agent Dev Kit 5 Layers
# ============================================================
PAGES["04-dev-kit-5layers.png"] = page(
    "에이전트 개발킷 5레이어 — Claude Code 핵심",
    "이 5개를 잘 짜면 확장-안전-팀배포 모두 가능",
    """
<div class="flow-step l6"><div class="flow-icon-box"></div>
  <div><div class="flow-title">Layer 1 — CLAUDE.md (메모리 레이어)</div>
  <div class="flow-desc">프로젝트 규칙-코드 스타일-구조 지도. Global + Project + Folder 3 스코프.</div></div>
  <div class="flow-num">01</div></div>
<div class="context-arrow">↓ 규칙 적용 ↓</div>

<div class="flow-step l4"><div class="flow-icon-box"></div>
  <div><div class="flow-title">Layer 2 — Skills (지식 레이어)</div>
  <div class="flow-desc">description 매칭 -> 자동 호출 -> 작업별 컨텍스트 로드</div></div>
  <div class="flow-num">02</div></div>
<div class="context-arrow">↓ 자동 호출 ↓</div>

<div class="flow-step l2"><div class="flow-icon-box">⚙</div>
  <div><div class="flow-title">Layer 3 — Hooks (가드레일 레이어)</div>
  <div class="flow-desc">PreToolUse - PostToolUse - Stop - 결정론적 강제 (AI 아님)</div></div>
  <div class="flow-num">03</div></div>
<div class="context-arrow">↓ 안전 검증 ↓</div>

<div class="flow-step l5"><div class="flow-icon-box"></div>
  <div><div class="flow-title">Layer 4 — Subagents (위임 레이어)</div>
  <div class="flow-desc">code-reviewer - test-runner - explorer (격리 컨텍스트-자체 모델)</div></div>
  <div class="flow-num">04</div></div>
<div class="context-arrow">↓ 위임 결과 ↓</div>

<div class="flow-step l1"><div class="flow-icon-box"></div>
  <div><div class="flow-title">Layer 5 — Plugins (배포 레이어)</div>
  <div class="flow-desc">skills + agents + hooks + commands 묶음 -> 마켓 배포</div></div>
  <div class="flow-num">05</div></div>

<div class="banner">
  <div class="banner-title"> 우리 = 5 레이어 다 갖춘 본보기</div>
  <div class="banner-content">
    <b>1</b> CLAUDE.md (169줄) - <b>2</b> Skills 77개 - <b>3</b> Hooks 24개 등록 -
    <b>4</b> Agents 11개 - <b>5</b> Plugins 25개
  </div>
</div>
""", h=1200)


# ============================================================
# Chapter 7 — Zero-Cost AI 2026
# ============================================================
PAGES["10-zero-cost.png"] = page(
    "제로비용 AI 아키텍처 2026",
    "회사 카드 없어도 AI 띄움 — 무료 도구 묶음",
    """
<div style="display:grid;grid-template-columns:100px 1fr 60px;gap:8px;">""" + "".join(f"""
  <div class="card {gc}" style="text-align:center;display:flex;flex-direction:column;justify-content:center;padding:6px 8px">
    <span style="font-size:22px">{ico}</span>
    <div style="font-size:12px;font-weight:800;margin-top:2px">{layer}</div>
  </div>
  <div class="card" style="background:white;padding:6px 12px">
    <div style="font-size:14px;color:#444;line-height:1.4"><b>{tools}</b><br>{note}</div>
  </div>
  <div class="card" style="background:linear-gradient(135deg,#28A745,#1A7F3A);color:white;text-align:center;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:900;padding:6px">
    $0
  </div>""" for ico, gc, layer, tools, note in [
    ("", "gradient-5", "Frontend", "Next.js - Streamlit - Vercel", "Free tier 만으로 가능"),
    ("", "gradient-2", "Orchestrator", "LangGraph - CrewAI", "오픈소스 워크플로우"),
    ("", "gradient-1", "LLM (로컬)", "Ollama + Gemma - Llama - Mistral", "GPU 만 있으면 무료"),
    ("[SIG]", "gradient-3", "RAG", "LlamaIndex + ChromaDB - Qdrant", "벡터 DB 로컬"),
    ("[MCP]", "gradient-2", "Tool Use (MCP)", "GitHub - Slack - DB - 파일", "표준 오픈"),
    ("[NEW]", "gradient-4", "Code Agent", "Claude Code CLI - Aider", "코드 자동 생성"),
    ("", "gradient-3", "Data", "SQLite - DuckDB - Supabase free", "로컬 + 무료 티어"),
    ("[STAT]", "danger", "Observability", "Phoenix self-hosted", "관측-비용 추적"),
    ("", "gradient-5", "Deploy", "Docker - Cloudflare - HF Spaces", "전부 무료"),
]) + """
</div>

<div class="banner">
  <div class="banner-title"> 우리 = 거의 제로비용 스택 본보기</div>
  <div class="banner-content">Claude Code CLI + exec_orch + SQLite + 옵션 Ollama. 유료는 Claude API 만 (Pro $20/월).</div>
</div>
""")


# ============================================================
# Chapter 8 — AI Builder 6 Categories
# ============================================================
PAGES["05-ai-builder-6cat.png"] = page(
    "AI 빌더 6 카테고리 매트릭스",
    "각 카테고리 × 5 도구 = 30 도구. 본인 필요만 골라쓰기",
    """
<div style="display:flex;flex-direction:column;gap:6px">""" + "".join(f"""
  <div style="display:grid;grid-template-columns:160px repeat(5,1fr);gap:6px;align-items:stretch">
    <div class="card" style="background:linear-gradient(135deg,{bg1},{bg2});color:white;text-align:center;display:flex;flex-direction:column;justify-content:center;padding:6px 10px">
      <div style="font-size:12px;font-weight:600;opacity:0.85">{num}</div>
      <div style="font-size:17px;font-weight:800;margin-top:1px">{name}</div>
    </div>""" + "".join(f"""
    <div class="card" style="background:white;border-color:{bg1};padding:6px 10px;text-align:center;display:flex;flex-direction:column;justify-content:center">
      <div style="font-size:14px;font-weight:800;color:#1F3864">{t}</div>
      <div style="font-size:11px;color:#666;margin-top:2px">{d}</div>
    </div>""" for t, d in tools) + """
  </div>""" for num, name, intro, bg1, bg2, tools in [
    ("01", "모델-검색", "더 나은 답-인사이트", "#1F3864", "#2E75B6", [
        ("ChatGPT", "대화-코딩"), ("Claude", "긴 컨텍스트"), ("Gemini", "Google 통합"),
        ("Perplexity", "실시간 검색"), ("Grok", "X 연동")]),
    ("02", "코딩-에이전트", "코드 폭발 파트너", "#2E75B6", "#5B9BD5", [
        ("Cursor", "AI 에디터"), ("Claude Code", "터미널"), ("Windsurf", "페어 코딩"),
        ("Copilot", "자동완성"), ("Replit", "자연어->앱")]),
    ("03", "앱-프로토타입", "아이디어->제품", "#5B9BD5", "#70AD47", [
        ("Lovable", "풀스택"), ("Bolt", "스택 선택"), ("v0", "UI 컴포넌트"),
        ("Framer AI", "웹사이트"), ("Vercel SDK", "AI 연결")]),
    ("04", "데이터-인프라", "필수 인프라", "#70AD47", "#E69138", [
        ("HuggingFace", "모델 허브"), ("Replicate", "API-배포"), ("Modal", "서버리스 GPU"),
        ("RunPod", "저렴한 GPU"), ("Pinecone", "벡터 DB")]),
    ("05", "워크플로우", "복잡 작업 연결", "#E69138", "#C00000", [
        ("LangChain", "체인"), ("LlamaIndex", "RAG"), ("n8n", "오픈소스 자동화"),
        ("Make", "시나리오"), ("Browserbase", "헤드리스")]),
    ("06", "미디어-콘텐츠", "콘텐츠 생성", "#C00000", "#7B2D8E", [
        ("★Mirra", "AI 콘텐츠"), ("Midjourney", "이미지"), ("Runway", "영상"),
        ("ElevenLabs", "음성"), ("ComfyUI", "노드 워크플로우")]),
]) + """
</div>

<div class="banner">
  <div class="banner-title"> 사용자 단계별 추천</div>
  <div class="banner-content">초보 = <b>1+2</b> - MVP = <b>+3</b> - 회사 배포 = <b>+4-5</b> - 콘텐츠 = <b>6</b></div>
</div>
""")


# ============================================================
# Chapter 9 — RAG Intro (Classic vs Graph vs Agentic)
# ============================================================
PAGES["11-rag-intro.png"] = page(
    "RAG 입문 — 검색 + 생성 AI",
    "LLM 이 모르는 내용을 외부 문서에서 찾아 답하게 함",
    """
<div class="grid3">""" + "".join(f"""
  <div class="card {gc}">
    <span class="card-icon">{ico}</span>
    <div class="card-title">{name}</div>
    <div class="card-desc">""" + "<br>".join(f"<b>{i+1}</b>. {s}" for i, s in enumerate(steps)) + f"""
    <br><br><b>특징</b>: {feat}<br><b>장점</b>: {pro}<br><b>약점</b>: {con}</div>
  </div>""" for ico, gc, name, steps, feat, pro, con in [
    ("", "gradient-5", "Classic RAG", [
        "사용자 질문", "임베딩 변환", "벡터 DB Top-K 검색",
        "LLM 에 컨텍스트 같이", "답변 생성"
    ], "1-hop, 단순", "빠르고 단순", "관계 추론 X"),
    ("", "gradient-3", "Graph RAG", [
        "사용자 질문", "엔티티 추출", "지식 그래프 탐색",
        "연결된 문맥 모음", "LLM -> 답변"
    ], "관계 기반", "관계-다중 출처", "그래프 구축 비용"),
    ("", "gradient-2", "Agentic RAG ★", [
        "사용자 질문", "추론 에이전트",
        "벡터 + 그래프 + 웹 + 도구 자율",
        "Self-Evaluation", "최종 답"
    ], "자율-자가 검증", "가장 똑똑", "느림-비용 ↑"),
]) + """
</div>

<div class="banner">
  <div class="banner-title"> 우리 시스템 (RAG 미구현 — 메모리가 단순 RAG)</div>
  <div class="banner-content">
    현재: <b>~/.claude/projects/&lt;proj&gt;/memory/</b> 가 사실상 단순 RAG (세션 컨텍스트 로드).
    향후: ChromaDB + LlamaIndex (exec_offline-vector) -> Agentic RAG 최종 목표
  </div>
</div>
""", h=1100)


# ============================================================
# Chapter 10 — RAG 8 Architectures
# ============================================================
PAGES["12-rag-8.png"] = page(
    "RAG 8가지 아키텍처",
    "데이터 특성-정확도 요구에 따라 골라쓰기",
    """
<div class="grid4">""" + "".join(f"""
  <div class="card {gc}">
    <span class="card-icon">{ico}</span>
    <div class="card-title">{num} {name}</div>
    <div class="card-desc"><b>특징</b>: {feat}<br><b>강추</b>: {when}</div>
  </div>""" for ico, gc, num, name, feat, when in [
    ("", "gradient-5", "01", "Naive RAG", "기본형-1-hop", "PoC, 단순 사실"),
    ("[ART]", "gradient-3", "02", "Multimodal", "이미지+텍스트", "도식-표 많은 문서"),
    ("", "gradient-1", "03", "HyDE", "가상답 만들고 검색", "모호한 질문"),
    ("[OK]", "gradient-2", "04", "Corrective", "결과 채점-웹 fallback", "정확도 중요"),
    ("", "gradient-3", "05", "Graph", "지식 그래프", "관계-다중 출처"),
    ("", "gradient-4", "06", "Hybrid", "벡터+그래프 동시", "최고 정확도"),
    ("[TGT]", "gradient-5", "07", "Adaptive", "질문 분류 후 분기", "다양한 유형"),
    ("", "danger", "08", "Agentic ★", "ReAct+멀티에이전트", "복잡 추론"),
]) + """
</div>

<div class="banner">
  <div class="banner-title"> 진화 순서 — 처음엔 Naive, 나중에 Agentic</div>
  <div class="banner-content">
    Naive(시작) -> 정확도 부족 시 <b>Corrective</b> + <b>HyDE</b> ->
    관계 필요 시 <b>Graph</b> -> 최종 <b>Agentic</b> (우리 Multi-Agent 와 자연 매칭)
  </div>
</div>
""", h=900)


# ============================================================
# Chapter 11 — API Protocols
# ============================================================
PAGES["13-api-protocols.png"] = page(
    "API 프로토콜 한눈에 — 11가지 중 2개만 알면 80%",
    "REST + Webhooks 만 알면 AI 작업 거의 끝",
    """
<div class="grid3">""" + "".join(f"""
  <div class="card {gc}" style="{'border:3px solid #C00000;' if star else ''}">
    <span class="card-icon">{ico}</span>
    <div class="card-title">{name}{' ★' if star else ''}</div>
    <div class="card-desc"><b>특징</b>: {feat}<br><b>쓰는 곳</b>: {where}</div>
  </div>""" for ico, gc, name, feat, where, star in [
    ("", "gradient-5", "REST", "HTTP+JSON, 표준", "거의 모든 API", True),
    ("", "gradient-3", "Webhooks", "이벤트 콜백", "결제-메신저", True),
    ("", "gradient-2", "GraphQL", "원하는 필드만", "모바일-복잡 UI", False),
    ("[MCP]", "gradient-1", "WebSocket", "양방향 실시간", "채팅-게임", False),
    ("", "gradient-4", "SSE", "서버 푸시 단방향", "실시간 알림", False),
    ("[FAST]", "danger", "gRPC", "고성능 RPC", "내부 통신", False),
    ("", "gradient-5", "SOAP", "XML 전통", "은행-정부", False),
    ("", "gradient-3", "AMQP/MQTT", "메시지큐-IoT", "비동기", False),
    ("", "gradient-2", "EDA/EDI", "이벤트-기업 간", "MSA-발주서", False),
]) + """
</div>

<div class="banner">
  <div class="banner-title"> 우리 시스템 — REST + Webhooks 만 사용 - MCP=REST - 다른 프로토콜 불필요</div>
</div>
""")


# ============================================================
# Chapter 12 — MCP vs A2A
# ============================================================
PAGES["06-mcp-vs-a2a.png"] = page(
    "MCP vs A2A — 두 프로토콜의 차이",
    "MCP = LLM 이 도구 직접 호출 - A2A = 매니저가 부서장에게 위임",
    """
<div class="grid2">
  <div class="card gradient-5">
    <span class="card-icon">[MCP]</span>
    <div class="card-title">MCP — Model Context Protocol</div>
    <div class="card-desc">
      <b>주체</b>: LLM 한 명<br>
      <b>호출 대상</b>: 외부 도구 (API)<br>
      <b>제어권</b>: LLM 이 끝까지 통제<br>
      <b>비유</b>: 비서 + 도구함<br>
      <b>복잡도</b>: 낮음<br><br>
      <b>흐름</b>: User -> LLM -> MCP Client -> MCP Server -> API -> 결과 -> LLM<br><br>
      <b>언제 쓰나</b>: 도구 표준화 필요할 때
    </div>
  </div>
  <div class="card gradient-3">
    <span class="card-icon"></span>
    <div class="card-title">A2A — Agent-to-Agent</div>
    <div class="card-desc">
      <b>주체</b>: 여러 에이전트<br>
      <b>호출 대상</b>: 다른 에이전트<br>
      <b>제어권</b>: 각 에이전트가 자율<br>
      <b>비유</b>: 매니저 + 부서장<br>
      <b>복잡도</b>: 높음<br><br>
      <b>흐름</b>: User -> Orchestrator -> 도메인 Agent -> 도구 (Agent 가 알아서) -> 결과<br><br>
      <b>언제 쓰나</b>: 멀티 도메인 자율 협력
    </div>
  </div>
</div>

<div class="banner">
  <div class="banner-title"> 우리 시스템 = MCP + A2A 동시 사용</div>
  <div class="banner-content">
    <b>MCP</b>: GitHub - Playwright - Figma - Slack - Notion MCP 서버 호출.<br>
    <b>A2A 스타일</b>: Claude(설계) -> Codex(구현) -> Gemini(검증) -> Haiku(판정)
    인수인계 (hook-08-ai-handoff).
  </div>
</div>
""", h=1000)


# ============================================================
# Chapter 13 — Claude 14 Levels
# ============================================================
PAGES["07-14-levels.png"] = page(
    "Claude 마스터 로드맵 14 단계",
    "Lv5 까지만 가도 일상 작업 80% 자동화",
    """
<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin-bottom:14px">""" + "".join(f"""
  <div class="card" style="background:linear-gradient(135deg,#CFE2F3,#9FC5E8);border-color:#0B5394;text-align:center;padding:14px">
    <div style="font-size:16px;color:#666">Lv {num}</div>
    <div style="font-size:21px;font-weight:800;color:#1F3864;margin-top:4px">{ico} {name}</div>
  </div>""" for num, ico, name in [
    ("1", "[NOTE]", "가입"), ("2", "", "모델 선택"), ("3", "[NEW]", "프롬프트"),
    ("4", "[MCP]", "도구 연결"), ("5", "", "Cowork"), ("6", "", "컨텍스트"),
    ("7", "", "음성 입력"),
]) + """
</div>
<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin-bottom:14px">""" + "".join(f"""
  <div class="card" style="background:linear-gradient(135deg,{bg1},{bg2});border-color:{ec};text-align:center;padding:14px">
    <div style="font-size:16px;color:{tc}">Lv {num}</div>
    <div style="font-size:21px;font-weight:800;color:{tc};margin-top:4px">{ico} {name}</div>
  </div>""" for num, ico, name, bg1, bg2, ec, tc in [
    ("8", "", "Obsidian", "#CFE2F3", "#9FC5E8", "#0B5394", "#1F3864"),
    ("9", "⚙", "Skills", "#CFE2F3", "#9FC5E8", "#0B5394", "#1F3864"),
    ("10", "", "프로젝트", "#CFE2F3", "#9FC5E8", "#0B5394", "#1F3864"),
    ("11", "", "추가 도구", "#CFE2F3", "#9FC5E8", "#0B5394", "#1F3864"),
    ("12", "", "토큰 절약", "#CFE2F3", "#9FC5E8", "#0B5394", "#1F3864"),
    ("13", "", "팀 배포", "#CFE2F3", "#9FC5E8", "#0B5394", "#1F3864"),
    ("14", "", "본인 안목", "#FFE699", "#FFC700", "#C00000", "#C00000"),
]) + """
</div>

<div class="banner">
  <div class="banner-title"> 사용자 현재 위치 = Lv 9-10 추정 (Skills + 프로젝트 활용 중)</div>
  <div class="banner-content">
    Lv 14 ★ 본인 안목 = AI 가 10 버전 만들면 어느 걸 출시할지 — <b>대체 불가, 사람의 영역</b>
  </div>
</div>
""", h=900)


# ============================================================
# Chapter 14 — Decision Tree (Skills/Subagents/MCP/Hooks)
# ============================================================
PAGES["14-decision-tree.png"] = page(
    "Claude Code 결정 트리 — 4 도구 중 무엇?",
    "Skills - Subagents - MCP - Hooks 자동 선택",
    """
<div style="text-align:center;margin-bottom:24px">
  <div style="display:inline-block;padding:18px 32px;background:linear-gradient(135deg,#FFE699,#FFC700);border-radius:14px;border:2px solid #BF9000;font-size:27px;font-weight:800;color:#1F3864">
    Q1. 에이전트가 무엇이 필요?
  </div>
</div>

<div class="grid2" style="margin-bottom:24px">
  <div class="card gradient-5">
    <div class="card-title" style="text-align:center"> 지식 (Knowledge)</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px">
      <div style="text-align:center;padding:12px;background:#fff;border-radius:10px;border:2px solid #0B5394">
        <div style="font-size:16px;color:#666">항상 로드</div>
        <div style="font-size:24px;font-weight:800;color:#1F3864;margin-top:6px"> CLAUDE.md</div>
      </div>
      <div style="text-align:center;padding:12px;background:#fff;border-radius:10px;border:2px solid #0B5394">
        <div style="font-size:16px;color:#666">작업별 로드</div>
        <div style="font-size:24px;font-weight:800;color:#1F3864;margin-top:6px">⚙ SKILL</div>
      </div>
    </div>
  </div>

  <div class="card danger">
    <div class="card-title" style="text-align:center">[FAST] 행동 (Action)</div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:14px">
      <div style="text-align:center;padding:10px;background:#fff;border-radius:10px;border:2px solid #C00000">
        <div style="font-size:16px;color:#666">내부 격리</div>
        <div style="font-size:21px;font-weight:800;color:#C00000;margin-top:4px"> SUBAGENT</div>
      </div>
      <div style="text-align:center;padding:10px;background:#fff;border-radius:10px;border:2px solid #C00000">
        <div style="font-size:16px;color:#666">외부-모델결정</div>
        <div style="font-size:21px;font-weight:800;color:#C00000;margin-top:4px">[MCP] MCP</div>
      </div>
      <div style="text-align:center;padding:10px;background:#fff;border-radius:10px;border:2px solid #C00000">
        <div style="font-size:16px;color:#666">외부-강제</div>
        <div style="font-size:21px;font-weight:800;color:#C00000;margin-top:4px">⚙ HOOK</div>
      </div>
    </div>
  </div>
</div>

<table class="compare-tbl">
<tr><th>도구</th><th>트리거</th><th>특징</th><th>강추 예시</th></tr>
<tr><td><b>Skills</b></td><td>모델이 결정</td><td>지식-작업별</td><td>/pr-review-checklist</td></tr>
<tr><td><b>Subagents</b></td><td>명시 호출</td><td>격리 추론-자체 모델</td><td>code-reviewer - explorer</td></tr>
<tr><td><b>MCP</b></td><td>모델이 결정</td><td>외부 시스템 호출</td><td>GitHub - Slack - Postgres</td></tr>
<tr><td><b>Hooks</b></td><td>이벤트 강제</td><td>결정론-AI 아님</td><td>PreToolUse - Stop</td></tr>
</table>

<div class="banner">
  <div class="banner-title"> 우리 시스템 — 4 도구 다 활용</div>
  <div class="banner-content">
    <b>Skills</b> 77개 - <b>Subagents</b> 11개 - <b>MCP</b> 다수 - <b>Hooks</b> 24개 등록.
    위험 차단 = 반드시 <b>Hook</b> (모델 신뢰 X)
  </div>
</div>
""", h=1100)


# ============================================================
# Chapter 15 — Complete Guide 6 Steps Cycle
# ============================================================
PAGES["15-complete-guide.png"] = page(
    "Claude Code 완전 가이드 — 6 단계 사이클",
    "Install -> Configure -> Prompt -> Review -> Iterate -> Ship",
    """
<div style="display:flex;align-items:center;justify-content:center;gap:6px;margin-bottom:10px;flex-wrap:nowrap">""" + "".join(f"""
  <div class="card {gc}" style="text-align:center;padding:8px 10px;flex:1;min-width:0">
    <span style="font-size:24px">{ico}</span>
    <div style="font-size:11px;color:#666">Step {num}</div>
    <div style="font-size:15px;font-weight:800;color:#1F3864;margin-top:1px">{name}</div>
    <div style="font-size:11px;color:#666;margin-top:2px">{desc}</div>
  </div>""" + ("" if num == "6" else """
  <div style="font-size:18px;color:#999">-></div>""") for ico, gc, num, name, desc in [
    ("", "gradient-5", "1", "Install", "claude CLI 설치"),
    ("⚙", "gradient-3", "2", "Configure", "CLAUDE.md-hooks-skills"),
    ("[NEW]", "gradient-1", "3", "Prompt", "구체적 요청"),
    ("", "gradient-2", "4", "Review", "검토-수정"),
    ("", "gradient-4", "5", "Iterate", "반복 개선"),
    ("[GO]", "danger", "6", "Ship", "출시-배포"),
]) + """
</div>

<div style="text-align:center;color:#666;font-size:12px;font-style:italic;margin-bottom:8px">
  필요시 Step 6 -> Step 3 으로 루프 ↺
</div>

<table class="compare-tbl" style="font-size:11px">
<tr><th>단계</th><th>할 일</th><th>산출물</th></tr>
<tr><td><b>1 Install</b></td><td>Claude Code CLI 설치</td><td>claude 명령</td></tr>
<tr><td><b>2 Configure</b></td><td>CLAUDE.md - hooks - skills</td><td>.claude/ 폴더</td></tr>
<tr><td><b>3 Prompt</b></td><td>구체적 요청 작성</td><td>task-instruction.md</td></tr>
<tr><td><b>4 Review</b></td><td>결과 검토-수정 요청</td><td>리뷰 코멘트</td></tr>
<tr><td><b>5 Iterate</b></td><td>반복 개선</td><td>v2, v3...</td></tr>
<tr><td><b>6 Ship</b></td><td>출시-배포</td><td>merged PR</td></tr>
</table>

<div class="banner">
  <div class="banner-title"> 우리 시스템 — 6 단계 다 자동화 중</div>
  <div class="banner-content"><b>1</b> install.bat - <b>2</b> 169줄+24 hooks - <b>3</b> task-instruction - <b>4</b> eval_quality - <b>5</b> watchdog - <b>6</b> git+gh pr</div>
</div>
""")


# ============================================================
# Chapter 16 — Architecture Reference (5 Layers + 60sec)
# ============================================================
PAGES["16-arch-reference.png"] = page(
    "Claude Code 아키텍처 레퍼런스 — 5 레이어 + 60초 셋업",
    "두고두고 보는 치트시트",
    """
<div class="flow-step l1">
  <div class="flow-icon-box"></div>
  <div><div class="flow-title">Layer 5 — Orchestration</div>
  <div class="flow-desc">Hooks - 체크포인트 - 워크플로우</div></div>
  <div class="flow-num">L5</div>
</div>
<div class="flow-step l2">
  <div class="flow-icon-box">⌨</div>
  <div><div class="flow-title">Layer 4 — Commands & Shortcuts</div>
  <div class="flow-desc">/init - /clear - /reset - /compact 슬래시 명령</div></div>
  <div class="flow-num">L4</div>
</div>
<div class="flow-step l3">
  <div class="flow-icon-box">[MCP]</div>
  <div><div class="flow-title">Layer 3 — MCP Connections</div>
  <div class="flow-desc">GitHub - Slack - Postgres - Playwright - 200+ 도구</div></div>
  <div class="flow-num">L3</div>
</div>
<div class="flow-step l4">
  <div class="flow-icon-box"></div>
  <div><div class="flow-title">Layer 2 — Skills Engine</div>
  <div class="flow-desc">.claude/skills/ — description 매칭 자동 로드</div></div>
  <div class="flow-num">L2</div>
</div>
<div class="flow-step l5">
  <div class="flow-icon-box"></div>
  <div><div class="flow-title">Layer 1 — Memory System</div>
  <div class="flow-desc">CLAUDE.md — Global - Project - Folder 3 스코프</div></div>
  <div class="flow-num">L1</div>
</div>
<div class="flow-step l6">
  <div class="flow-icon-box">[FAST]</div>
  <div><div class="flow-title">Foundation — Runtime</div>
  <div class="flow-desc">claude 명령 - 파일 접근 - 실행 모드 - 시스템 접근</div></div>
  <div class="flow-num">F</div>
</div>

<div class="banner">
  <div class="banner-title"> 60초 셋업</div>
  <div class="banner-content">
    <b>1</b> npm install -g @anthropic-ai/claude-code - <b>2</b> claude 명령 - <b>3</b> /init - 끝!
  </div>
</div>
""", h=1200)


# ============================================================
# Chapter 17 — Project Structure
# ============================================================
PAGES["17-project-structure.png"] = page(
    "Claude Code 프로젝트 구조",
    "어디에 무엇을 두는가 표준 — 90점 시작",
    """
<div style="font-family:Consolas,'Courier New',monospace;background:#1E1E1E;color:#D4D4D4;padding:12px 16px;border-radius:11px;font-size:13px;line-height:1.4;box-shadow:0 5px 16px rgba(0,0,0,0.15);margin-bottom:10px">
<span style="color:#569CD6;font-weight:700">my_project/</span><br>
&nbsp;&nbsp;<span style="color:#CE9178"> CLAUDE.md</span> <span style="color:#6A9955">— 팀 공유 규칙 (git commit)</span><br>
&nbsp;&nbsp;<span style="color:#CE9178"> settings.json</span> <span style="color:#6A9955">— 권한 + hook 등록</span><br>
&nbsp;&nbsp;<span style="color:#569CD6"> .claude/</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#569CD6"> commands/</span> <span style="color:#6A9955">— 슬래시 명령 (/review - /test - /deploy)</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#569CD6"> skills/</span> <span style="color:#6A9955">— SKILL.md 자동 워크플로우</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#569CD6"> agents/</span> <span style="color:#6A9955">— subagent (code-reviewer.md 등)</span><br>
&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#569CD6"> hooks/</span> <span style="color:#6A9955">— PreToolUse.sh 가드레일</span><br>
&nbsp;&nbsp;<span style="color:#CE9178"> .mcp.json</span> <span style="color:#6A9955">— MCP 서버 설정 (GitHub - Postgres)</span><br>
&nbsp;&nbsp;<span style="color:#569CD6"> plugins/</span> <span style="color:#6A9955">— 원본 (sync 소스)</span><br>
&nbsp;&nbsp;<span style="color:#569CD6"> docs/</span> <span style="color:#6A9955">— 문서-가이드</span>
</div>

<table class="compare-tbl">
<tr><th>경로</th><th>역할</th><th>비고</th></tr>
<tr><td><b>CLAUDE.md</b></td><td>팀 공유 규칙</td><td>git commit</td></tr>
<tr><td><b>.claude/commands/</b></td><td>슬래시 명령</td><td>자동 sync</td></tr>
<tr><td><b>.claude/skills/</b></td><td>자동 워크플로우</td><td>description 매칭</td></tr>
<tr><td><b>.claude/agents/</b></td><td>subagent 정의</td><td>Task 도구로 호출</td></tr>
<tr><td><b>.claude/hooks/</b></td><td>가드레일</td><td>settings.json 에 등록</td></tr>
<tr><td><b>.mcp.json</b></td><td>MCP 서버</td><td>외부 도구 연결</td></tr>
<tr><td><b>plugins/</b></td><td>원본 SoT</td><td>sync 결과 -> .claude/</td></tr>
</table>

<div class="banner">
  <div class="banner-title"> 우리 구조 — commands 152 - skills 77 - agents 11 - hooks 21 + plugins 25 (SoT)</div>
</div>
""")


# ============================================================
# Chapter 18 — DK .claude Folder
# ============================================================
PAGES["18-dk-folder.png"] = page(
    ".claude 폴더 전체 구조 (DK 메소드)",
    "한글로 가장 친절한 폴더 트리",
    """
<style>
.dk-tbl { width:100%; border-collapse:separate; border-spacing:4px; margin-top:6px; }
.dk-tbl th { background:linear-gradient(135deg,#1F3864,#3F6FB5); color:white; padding:6px 10px;
             text-align:left; border-radius:6px; font-size:14px; }
.dk-tbl td { padding:5px 10px; background:linear-gradient(135deg,#fff,#f8fafc); border-radius:6px;
             box-shadow:0 2px 6px rgba(0,0,0,0.05); font-size:13px; }
.dk-card { padding:8px 12px; border-radius:10px; box-shadow:0 4px 10px rgba(0,0,0,0.08); }
.dk-card .ct { font-size:15px; font-weight:800; color:#1F3864; margin-bottom:2px; }
.dk-card .cd { font-size:12px; color:#444; line-height:1.4; }
</style>
<table class="dk-tbl">
<tr><th>파일-폴더</th><th>용도</th><th>git</th></tr>
<tr><td> <b>CLAUDE.md</b></td><td>팀 공유 기억</td><td style="color:#0B5394;font-weight:700">commit</td></tr>
<tr><td> <b>CLAUDE.local.md</b></td><td>나만의 기억</td><td style="color:#C00000;font-weight:700">gitignore</td></tr>
<tr><td> <b>.claude/settings.json</b></td><td>권한 설정 (공유)</td><td style="color:#0B5394;font-weight:700">commit</td></tr>
<tr><td> <b>.claude/settings.local</b></td><td>개인 권한</td><td style="color:#C00000;font-weight:700">gitignore</td></tr>
<tr><td> <b>.claude/commands/</b></td><td>나만의 / 명령어</td><td style="color:#0B5394;font-weight:700">commit</td></tr>
<tr><td> <b>.claude/rules/</b></td><td>항상 적용 규칙</td><td style="color:#0B5394;font-weight:700">commit</td></tr>
<tr><td> <b>.claude/skills/</b></td><td>자동 워크플로우</td><td style="color:#0B5394;font-weight:700">commit</td></tr>
<tr><td> <b>.claude/agents/</b></td><td>서브에이전트</td><td style="color:#0B5394;font-weight:700">commit</td></tr>
</table>

<div class="grid2" style="margin-top:8px;margin-bottom:6px;gap:14px;">
  <div class="dk-card gradient-3">
    <div class="ct">[OK] commit (팀 공유)</div>
    <div class="cd">CLAUDE.md - settings.json - commands/ - rules/ - skills/ - agents/ — 팀 규칙-도구 일관</div>
  </div>
  <div class="dk-card danger">
    <div class="ct"> gitignore (개인)</div>
    <div class="cd">CLAUDE.local.md - settings.local - .env — 시크릿-개인 환경 보호</div>
  </div>
</div>

<div class="banner" style="margin-top:4px;padding:6px 14px;">
  <div class="banner-title" style="font-size:16px;margin-bottom:1px;"> 우리 시스템</div>
  <div class="banner-content" style="font-size:13px;line-height:1.3;">
    CLAUDE.md ✓ 169줄 - settings.json ✓ 24 hooks - CLAUDE.local.md 미사용 - 시크릿 .env (gitignore)
  </div>
</div>
""")


# ============================================================
# Chapter 19 — CLAUDE.md Design Guide
# ============================================================
PAGES["19-claude-md-design.png"] = page(
    "CLAUDE.md 설계 가이드 — 3 Scopes + WHAT/WHY/HOW + 5 Rules",
    "사람용 README 아닌 AI 팀원 온보딩 문서",
    """
<div style="text-align:center;margin-bottom:6px;font-size:16px;color:#1F3864;font-weight:800">
  ① 3 SCOPES (가까운 게 이김)
</div>
<div class="grid3">
  <div class="card gradient-5" style="padding:8px 12px"><span style="font-size:22px"></span>
    <div style="font-size:14px;font-weight:800;color:#1F3864">GLOBAL</div>
    <div style="font-size:11px;color:#444"><b>위치</b>: ~/.claude/CLAUDE.md - 모든 프로젝트</div></div>
  <div class="card gradient-3" style="padding:8px 12px"><span style="font-size:22px"></span>
    <div style="font-size:14px;font-weight:800;color:#1F3864">PROJECT</div>
    <div style="font-size:11px;color:#444"><b>위치</b>: ./CLAUDE.md - 이 프로젝트</div></div>
  <div class="card gradient-1" style="padding:8px 12px"><span style="font-size:22px"></span>
    <div style="font-size:14px;font-weight:800;color:#1F3864">FOLDER</div>
    <div style="font-size:11px;color:#444"><b>위치</b>: ./src/CLAUDE.md - 모듈별</div></div>
</div>
<div style="text-align:center;color:#666;font-style:italic;margin:4px 0;font-size:11px">-> Folder > Project > Global</div>

<div style="text-align:center;margin:8px 0 6px;font-size:16px;color:#1F3864;font-weight:800">
  ② WHAT / WHY / HOW 프레임워크
</div>
<div class="grid3">
  <div class="card gradient-1" style="padding:8px 12px"><span style="font-size:22px">[LIST]</span>
    <div style="font-size:14px;font-weight:800;color:#1F3864">WHAT</div>
    <div style="font-size:11px;color:#444">목적-스택-구조</div></div>
  <div class="card danger" style="padding:8px 12px"><span style="font-size:22px">[FAST]</span>
    <div style="font-size:14px;font-weight:800;color:#1F3864">WHY</div>
    <div style="font-size:11px;color:#444">결정-스타일-금기</div></div>
  <div class="card gradient-3" style="padding:8px 12px"><span style="font-size:22px">⚙</span>
    <div style="font-size:14px;font-weight:800;color:#1F3864">HOW</div>
    <div style="font-size:11px;color:#444">build-test-lint-commit</div></div>
</div>

<div style="text-align:center;margin:8px 0 6px;font-size:16px;color:#1F3864;font-weight:800">
  ③ 5 RULES (실제로 작동하려면)
</div>
<div class="row5">""" + "".join(f"""
  <div class="card gradient-2" style="text-align:center;padding:8px 10px">
    <div style="font-size:22px;font-weight:900;color:#7B5BA6">{n}</div>
    <div style="font-size:12px;font-weight:700;color:#1F3864;margin-top:2px">{r}</div>
  </div>""" for n, r in [
    ("1", "/init 먼저"),
    ("2", "500줄 이하"),
    ("3", "Hooks 사용"),
    ("4", "월간 업데이트"),
    ("5", "참조 중심"),
]) + """
</div>

<div class="banner">
  <div class="banner-title"> 우리 시스템</div>
  <div class="banner-content">Global ✓ install 자동 - Project ./CLAUDE.md 169줄 - 5 Rules 다 준수 - 13개 금지 명시</div>
</div>
""")


# ============================================================
# Chapter 20 — 8 Prompt Frameworks
# ============================================================
PAGES["20-prompt-8.png"] = page(
    "8가지 프롬프트 프레임워크",
    "CLARITY 한 개만 외우면 80% 커버 — 결과 두 배",
    """
<div class="grid4">""" + "".join(f"""
  <div class="card {gc}" style="{'border:3px solid #C00000;' if star else ''}">
    <span class="card-icon">{ico}</span>
    <div class="card-title">{name}{' ★' if star else ''}</div>
    <div class="card-desc"><b>쓰는 곳</b>: {when}<br><b>구성</b>: {parts}</div>
  </div>""" for ico, gc, name, when, parts, star in [
    ("[NEW]", "gradient-1", "CLARITY", "처음-만능", "Context - Look - Ask - Rules - Input - Target - You", True),
    ("[LIST]", "gradient-5", "SOCRATES", "단계별 계획", "Situation - Objective - Constraints - Role - Action - Thinking - Evaluation - Summary", False),
    ("[TGT]", "gradient-3", "ANTICIPATE", "상품 기획", "Audience - Need - Task - Information - Plan - Act - Test - Enhance", False),
    ("", "gradient-2", "PARTNER", "콘텐츠 전략", "Purpose - Audience - Research - Think - Narrow - Execute - Review", False),
    ("[SIG]", "danger", "TRUST", "깊이 있는 분석", "Task - Reason - Understand - Structure - Tailor", False),
    ("[STAT]", "gradient-4", "RIPPLE", "데이터 분석", "Role - Input - Process - Points - Layout - Evaluate", False),
    ("", "gradient-5", "CATCH", "마케팅 카피", "Context - Aim - Tone - Criteria - Help", False),
    ("", "gradient-2", "MAGIC", "랜딩페이지", "Motivation - Audience - Goal - Input - Create", False),
]) + """
</div>

<div class="banner">
  <div class="banner-title"> 우리 시스템</div>
  <div class="banner-content">
    task-instruction.md 구조 = CLARITY 와 비슷 (Context - Rules - Target - Constraints).
    5중박기 원칙 = SOCRATES + ANTICIPATE 효과 자동.
  </div>
</div>
""", h=1100)


# ============================================================
# 실행
# ============================================================
async def main():
    """viewport 1300×900 (비율 0.69 페이지 일치) — 화면 표시 1.23배 ↑.
    docx 9.5 inch wide -> 137 DPI (이전 168). 같은 폰트 px = 화면 더 크게.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for name, html in PAGES.items():
            page = await browser.new_page(viewport={"width": 1300, "height": 900})
            await page.set_content(html)
            await page.wait_for_load_state("networkidle")
            out = OUT / name
            await page.screenshot(path=str(out), full_page=False,
                                  clip={"x": 0, "y": 0, "width": 1300, "height": 900})
            print(f"  [OK] {name}  {out.stat().st_size//1024}KB")
            await page.close()
        await browser.close()
    print(f"\n[Done] total {len(PAGES)} PNGs (1300×900, ratio 0.69)")


asyncio.run(main())
