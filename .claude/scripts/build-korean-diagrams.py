"""
build-korean-diagrams.py — matplotlib 으로 한글 다이어그램 PNG 생성.

7개 핵심 다이어그램을 영어 인포그래픽 옆에 붙일 한글 버전으로 생성.
폰트: Malgun Gothic (Windows 기본).

출력: docs/screens/arch-kor/*.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.font_manager as fm
from pathlib import Path

# 한글 폰트
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "docs" / "screens" / "arch-kor"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# --------- helpers ---------
def new_fig(w=12, h=7):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def title(ax, text, y=95):
    ax.text(50, y, text, ha="center", va="center", fontsize=18, fontweight="bold", color="#203864")


def box(ax, x, y, w, h, text, fc="#DCE6F1", ec="#4472C4", text_color="#1F3864", fontsize=11, bold=False):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=2",
                        facecolor=fc, edgecolor=ec, linewidth=1.5)
    ax.add_patch(p)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center",
            fontsize=fontsize, color=text_color, fontweight=("bold" if bold else "normal"), wrap=True)


def arrow(ax, x1, y1, x2, y2, color="#666"):
    ar = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->,head_length=8,head_width=6",
                          color=color, linewidth=1.5)
    ax.add_patch(ar)


def save(fig, name):
    p = OUT_DIR / name
    fig.savefig(p, dpi=120, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  [OK] {p.name}  ({p.stat().st_size//1024}KB)")


# --------- 1. Generative vs Agentic vs AI Agent ---------
def fig_gen_agentic_agent():
    fig, ax = new_fig(13, 7)
    title(ax, "Generative vs Agentic vs AI Agent — 한눈에")
    cols = [
        ("Generative AI", "#FFF2CC", "#D6B656", [
            "글·그림 만들어 주는 AI",
            "한 번 답 만들고 끝",
            "예: ChatGPT, DALL-E",
            "→ 카피라이터",
        ]),
        ("Agentic AI", "#E2D5F0", "#7B5BA6", [
            "스스로 단계 짜는 AI",
            "LLM 골라 계획 → 실행",
            "예: 여행 계획 자동 설계",
            "→ 신입 매니저",
        ]),
        ("AI Agent", "#D5E8D4", "#82B366", [
            "외부 API·도구 직접 호출",
            "자기 결과 평가까지",
            "예: 예약·캘린더 자동화",
            "→ 경력 매니저",
        ]),
    ]
    x_starts = [4, 36, 68]
    for (name, fc, ec, items), xs in zip(cols, x_starts):
        box(ax, xs, 78, 28, 10, name, fc=fc, ec=ec, fontsize=14, bold=True)
        for i, t in enumerate(items):
            box(ax, xs, 64-i*14, 28, 10, t, fc="white", ec=ec, fontsize=10)
    save(fig, "01-gen-vs-agentic-vs-agent.png")


# --------- 2. 5 Cores (에이전트 5 핵심) ---------
def fig_5_cores():
    fig, ax = new_fig(13, 8)
    title(ax, "에이전트 5가지 핵심 부품 (위→아래 흐름)")
    layers = [
        ("1 가드레일·게이트웨이", "입력 검증 · 개인정보 필터 · 호출 제한", "#F4CCCC", "#CC0000"),
        ("2 오케스트레이션", "작업 분해 · 라우팅 · 상태 관리 · 에러 복구", "#FCE5CD", "#E69138"),
        ("3 도구·MCP 통합", "MCP 서버 · 도구 레지스트리 · 샌드박스 · 감사 로그", "#FFF2CC", "#BF9000"),
        ("4 메모리·컨텍스트", "단기(대화) · 중기(세션) · 장기(벡터 DB)", "#D9EAD3", "#38761D"),
        ("5 관측·추적", "분산 추적 · 토큰 메트릭 · 결정 로그 · 알람", "#CFE2F3", "#0B5394"),
    ]
    h = 12
    for i, (name, sub, fc, ec) in enumerate(layers):
        y = 75 - i * (h + 2)
        box(ax, 8, y, 50, h, name, fc=fc, ec=ec, fontsize=14, bold=True)
        ax.text(62, y + h/2, sub, ha="left", va="center", fontsize=11, color="#444")
    # 화살표
    for i in range(4):
        y = 75 - i * 14 - 1
        arrow(ax, 33, y, 33, y-2.5)
    # 입출력 화살표
    ax.text(2, 75 + 6, "User\nRequest", ha="center", va="center", fontsize=10, color="#666")
    ax.text(98, 75 + 6, "Agent\nResponse", ha="center", va="center", fontsize=10, color="#666")
    save(fig, "02-5-cores.png")


# --------- 3. AI 스택 5층 ---------
def fig_5_stack():
    fig, ax = new_fig(13, 8)
    title(ax, "AI 스택 5층 — 인프라부터 인터페이스까지")
    layers = [
        ("5 인터페이스", "사용자와 만남", "FastAPI · Streamlit · React · Vue · Auth0 · MCP", "#CFE2F3", "#0B5394"),
        ("4 오케스트레이션", "워크플로우·여러 에이전트", "LangGraph · CrewAI · mem0 · Claude Agent SDK · Google ADK", "#F4CCCC", "#CC0000"),
        ("3 LLM", "진짜 뇌", "Claude Opus 4.6 · Llama 4 · GPT 5.3 · Kimi K2.5 · OpenRouter", "#FFF2CC", "#BF9000"),
        ("2 데이터", "RAG 의 재료·벡터 저장", "Chroma · Pinecone · Weaviate · Qdrant · Neo4j", "#D9EAD3", "#38761D"),
        ("1 인프라", "하드웨어·컨테이너", "Docker · Kubernetes · AWS · GCP · Azure · RunPod", "#D5D5D5", "#666"),
    ]
    h = 13
    for i, (name, sub, ex, fc, ec) in enumerate(layers):
        y = 75 - i * (h + 1.5)
        box(ax, 5, y, 26, h, name + "\n" + sub, fc=fc, ec=ec, fontsize=12, bold=True)
        box(ax, 33, y, 62, h, ex, fc="white", ec=ec, fontsize=10)
    save(fig, "03-ai-stack-5layers.png")


# --------- 4. 에이전트 개발킷 5레이어 ---------
def fig_dev_kit_5layers():
    fig, ax = new_fig(13, 8.5)
    title(ax, "에이전트 개발킷 5레이어 — Claude Code 의 부품")
    layers = [
        ("Layer 1 — CLAUDE.md", "메모리 레이어", "프로젝트 규칙 · 코드 스타일 · 구조 지도", "#D9D2E9", "#674EA7"),
        ("Layer 2 — Skills", "지식 레이어", "description 매칭 → 자동 호출 → 작업별 컨텍스트", "#D9EAD3", "#38761D"),
        ("Layer 3 — Hooks", "가드레일 레이어", "PreToolUse · PostToolUse · Stop · 결정론적 강제", "#FCE5CD", "#E69138"),
        ("Layer 4 — Subagents", "위임 레이어", "code-reviewer · test-runner · explorer (격리 컨텍스트)", "#CFE2F3", "#0B5394"),
        ("Layer 5 — Plugins", "배포 레이어", "skills + agents + hooks + commands → 마켓 배포", "#F4CCCC", "#CC0000"),
    ]
    h = 12
    for i, (name, role, sub, fc, ec) in enumerate(layers):
        y = 78 - i * (h + 2)
        box(ax, 5, y, 24, h, name + "\n" + role, fc=fc, ec=ec, fontsize=11, bold=True)
        box(ax, 31, y, 64, h, sub, fc="white", ec=ec, fontsize=11)
    save(fig, "04-dev-kit-5layers.png")


# --------- 5. AI 빌더 6 카테고리 매트릭스 ---------
def fig_builder_matrix():
    fig, ax = new_fig(14, 8)
    title(ax, "AI 빌더 6 카테고리 매트릭스 (각 칸 = 한 도구)")
    cats = [
        ("1 모델·검색", "#1F3864", ["ChatGPT", "Claude", "Gemini", "Perplexity", "Grok"]),
        ("2 코딩·에이전트", "#2E75B6", ["Cursor", "Claude Code", "Windsurf", "Copilot", "Replit"]),
        ("3 앱·프로토타입", "#5B9BD5", ["Lovable", "Bolt", "v0", "Framer AI", "Vercel SDK"]),
        ("4 데이터·인프라", "#70AD47", ["HuggingFace", "Replicate", "Modal", "RunPod", "Pinecone"]),
        ("5 워크플로우", "#E69138", ["LangChain", "LlamaIndex", "n8n", "Make", "Browserbase"]),
        ("6 미디어·콘텐츠", "#C00000", ["★Mirra", "Midjourney", "Runway", "ElevenLabs", "ComfyUI"]),
    ]
    rh = 12
    for i, (name, color, items) in enumerate(cats):
        y = 78 - i * (rh + 1)
        box(ax, 3, y, 22, rh, name, fc=color, ec=color, text_color="white", fontsize=12, bold=True)
        for j, it in enumerate(items):
            x = 27 + j * 14
            box(ax, x, y, 12, rh, it, fc="white", ec=color, fontsize=10)
    save(fig, "05-ai-builder-6cat.png")


# --------- 6. MCP vs A2A ---------
def fig_mcp_vs_a2a():
    fig, ax = new_fig(14, 8)
    title(ax, "MCP vs A2A — 같은 일, 다른 두 방식")

    # MCP (위)
    ax.text(8, 87, "MCP — LLM 이 도구를 직접 호출", ha="left", va="center", fontsize=13, fontweight="bold", color="#0B5394")
    box(ax, 5, 70, 12, 8, "사용자", fc="#EEE", ec="#666")
    box(ax, 25, 70, 14, 8, "LLM", fc="#CFE2F3", ec="#0B5394", bold=True)
    box(ax, 47, 70, 14, 8, "MCP 클라이언트", fc="#CFE2F3", ec="#0B5394")
    box(ax, 69, 78, 14, 6, "MCP 서버\n(항공)", fc="#FFF2CC", ec="#BF9000")
    box(ax, 69, 67, 14, 6, "MCP 서버\n(캘린더)", fc="#FFF2CC", ec="#BF9000")
    box(ax, 89, 78, 10, 6, "항공 API", fc="white", ec="#999")
    box(ax, 89, 67, 10, 6, "캘린더 API", fc="white", ec="#999")
    arrow(ax, 17, 74, 25, 74)
    arrow(ax, 39, 74, 47, 74)
    arrow(ax, 61, 75, 69, 81)
    arrow(ax, 61, 73, 69, 70)
    arrow(ax, 83, 81, 89, 81)
    arrow(ax, 83, 70, 89, 70)

    # A2A (아래)
    ax.text(8, 55, "A2A — 에이전트끼리 위임", ha="left", va="center", fontsize=13, fontweight="bold", color="#C00000")
    box(ax, 5, 38, 12, 8, "사용자", fc="#EEE", ec="#666")
    box(ax, 25, 38, 18, 8, "오케스트레이터\n에이전트", fc="#F4CCCC", ec="#C00000", bold=True)
    box(ax, 53, 46, 16, 6, "항공 에이전트", fc="#F4CCCC", ec="#C00000")
    box(ax, 53, 35, 16, 6, "캘린더 에이전트", fc="#F4CCCC", ec="#C00000")
    box(ax, 75, 46, 10, 6, "항공 API", fc="white", ec="#999")
    box(ax, 75, 35, 10, 6, "캘린더 API", fc="white", ec="#999")
    arrow(ax, 17, 42, 25, 42)
    arrow(ax, 43, 44, 53, 49)
    arrow(ax, 43, 40, 53, 38)
    arrow(ax, 69, 49, 75, 49)
    arrow(ax, 69, 38, 75, 38)

    # 핵심 메시지
    ax.text(50, 18, "MCP: 비서 하나가 외부 도구를 직접 부른다.   |   A2A: 매니저가 부서장에게 통째로 위임한다.",
            ha="center", va="center", fontsize=11, color="#444", style="italic")
    save(fig, "06-mcp-vs-a2a.png")


# --------- 7. Claude 14 레벨 로드맵 ---------
def fig_14_levels():
    fig, ax = new_fig(14, 8)
    title(ax, "Claude 마스터 로드맵 14단계 (시작 → 목표)")
    levels = [
        "1 가입", "2 모델선택", "3 프롬프트", "4 도구연결",
        "5 Cowork", "6 컨텍스트폴더", "7 음성입력", "8 Obsidian",
        "9 Skills", "10 프로젝트", "11 추가도구", "12 토큰절약",
        "13 팀배포", "14 본인 안목 ★",
    ]
    # 2 row × 7
    for i, lv in enumerate(levels):
        row = i // 7
        col = i % 7
        x = 3 + col * 13.5
        y = 60 - row * 25
        ec = "#0B5394" if i < 13 else "#C00000"
        fc = "#CFE2F3" if i < 13 else "#FFE699"
        box(ax, x, y, 12, 16, lv, fc=fc, ec=ec, fontsize=11, bold=(i == 13))
        # 화살표 (다음 레벨로)
        if col < 6:
            arrow(ax, x + 12, y + 8, x + 13.5, y + 8)
    # 줄 사이 화살표 (7 → 8)
    arrow(ax, 3 + 6 * 13.5 + 6, 60, 3 + 6 * 13.5 + 6, 35 + 16)
    ax.text(3 + 6 * 13.5 + 9, 50, "↓", ha="center", va="center", fontsize=18, color="#666")
    ax.text(50, 12, "처음엔 1-5단계만 — 일상 작업 80% 자동화. 14단계 (본인 안목) 는 사람만의 영역.",
            ha="center", va="center", fontsize=11, color="#444", style="italic")
    save(fig, "07-14-levels.png")


# --------- 추가 13개 다이어그램 (전수 한글화) ---------

# 8. AI 8가지 모델 유형
def fig_8_models():
    fig, ax = new_fig(13, 9)
    title(ax, "AI 에이전트 8가지 모델 유형")
    models = [
        ("GPT", "글의 다음 단어 잘 맞춤", "GPT-4, Claude", "#CFE2F3"),
        ("MoE", "여러 전문가 뇌, 골라 씀", "Qwen 2", "#D9D2E9"),
        ("LRM", "긴 추론, 검증", "Gemini 1.5", "#FCE5CD"),
        ("VLM", "이미지+글 같이", "Claude 4.x", "#D9EAD3"),
        ("SLM", "작고 빠른, 모바일", "Gemma 2", "#FFF2CC"),
        ("LAM", "행동 결정 잘함", "X-LAM", "#F4CCCC"),
        ("HRM", "계획→실행 분리", "Sapient", "#E2D5F0"),
        ("mHC", "다층 흐름 (실험)", "Deepseek mHC", "#D5D5D5"),
    ]
    for i, (n, d, e, fc) in enumerate(models):
        row, col = i // 2, i % 2
        x, y = 5 + col * 47, 78 - row * 18
        box(ax, x, y+8, 43, 8, n, fc=fc, ec="#444", fontsize=14, bold=True)
        box(ax, x, y+0, 43, 8, d, fc="white", ec="#444", fontsize=10)
        ax.text(x+21.5, y-3, "예: "+e, ha="center", va="center", fontsize=9, color="#666", style="italic")
    save(fig, "08-8-models.png")

# 9. 9 Silent Killers
def fig_9_killers():
    fig, ax = new_fig(14, 9)
    title(ax, "AI 에이전트 9가지 숨은 함정")
    killers = [
        ("1 Tool Bloat", "도구 너무 많음", "#F4CCCC"),
        ("2 Context Decay", "맥락 부패", "#FCE5CD"),
        ("3 Retrieval Poisoning", "검색 오염", "#FFF2CC"),
        ("4 Runaway Loop", "무한 재시도 847번", "#D9EAD3"),
        ("5 Schema Drift", "v1→v2 못 봄", "#CFE2F3"),
        ("6 Eval Blindness", "10개로만 검증", "#D9D2E9"),
        ("7 Non-Determinism", "같은 입력 다른 답", "#E2D5F0"),
        ("8 Cost Blind", "$48,200 청구", "#F4CCCC"),
        ("9 No Failure Mode", "모르면 거짓말", "#D5D5D5"),
    ]
    for i, (n, d, fc) in enumerate(killers):
        row, col = i // 3, i % 3
        x, y = 4 + col * 31, 72 - row * 22
        box(ax, x, y+8, 28, 8, n, fc=fc, ec="#CC0000", fontsize=12, bold=True)
        box(ax, x, y+0, 28, 8, d, fc="white", ec="#CC0000", fontsize=10)
    ax.text(50, 8, "이 9가지만 피하면 프로덕션 사고 80% 감소",
            ha="center", va="center", fontsize=12, color="#444", style="italic", fontweight="bold")
    save(fig, "09-9-killers.png")

# 10. 제로비용 AI 스택
def fig_zero_cost():
    fig, ax = new_fig(14, 8.5)
    title(ax, "제로비용 AI 스택 2026 — 무료 도구 묶음")
    rows = [
        ("Frontend", "Next.js / Streamlit / Vercel free", "#CFE2F3"),
        ("Orchestrator", "LangGraph / CrewAI", "#E2D5F0"),
        ("LLM (로컬)", "Ollama + Gemma / Llama / Mistral", "#FFF2CC"),
        ("RAG", "LlamaIndex + ChromaDB / Qdrant", "#D9EAD3"),
        ("Tool Use", "MCP (open) — GitHub·Slack·DB", "#FCE5CD"),
        ("Code Agent", "Claude Code CLI / Aider", "#F4CCCC"),
        ("Data", "SQLite / DuckDB / Supabase free", "#D5D5D5"),
        ("Observability", "Phoenix self-hosted", "#FFCCCC"),
        ("Deploy", "Docker / Cloudflare / HF Spaces", "#CCFFCC"),
    ]
    rh = 8
    for i, (layer, tools, fc) in enumerate(rows):
        y = 80 - i * (rh + 0.5)
        box(ax, 5, y, 24, rh, layer, fc=fc, ec="#444", fontsize=12, bold=True)
        box(ax, 31, y, 64, rh, tools, fc="white", ec="#444", fontsize=11)
        ax.text(98, y + rh/2, "$0", ha="right", va="center", fontsize=14, color="#0B5394", fontweight="bold")
    save(fig, "10-zero-cost.png")

# 11. RAG 입문 (Classic vs Graph vs Agentic)
def fig_rag_intro():
    fig, ax = new_fig(14, 8)
    title(ax, "RAG 입문 — 검색 + 생성으로 답하는 AI")
    cols = [
        ("Classic RAG", "#CFE2F3", "#0B5394", [
            "질문", "임베딩", "벡터DB Top-K", "LLM", "답변",
            "─────", "특징: 빠름·단순", "1-hop"
        ]),
        ("Graph RAG", "#D9EAD3", "#38761D", [
            "질문", "엔티티 추출", "지식 그래프", "Connected Context",
            "LLM", "답변", "─────", "관계·다중 출처"
        ]),
        ("Agentic RAG", "#E2D5F0", "#7B5BA6", [
            "질문", "Reasoning Agent", "벡터+그래프+Web+Tools",
            "Self-Evaluation", "최종 답", "─────",
            "자율·자가 검증", "가장 똑똑·느림"
        ]),
    ]
    x_starts = [4, 36, 68]
    for (name, fc, ec, items), xs in zip(cols, x_starts):
        box(ax, xs, 80, 28, 8, name, fc=fc, ec=ec, fontsize=14, bold=True)
        for i, t in enumerate(items):
            y = 72 - i * 8
            color_t = "#444" if not t.startswith("─") else "#999"
            ax.text(xs + 14, y, t, ha="center", va="center", fontsize=10, color=color_t)
    save(fig, "11-rag-intro.png")

# 12. RAG 8 architectures
def fig_rag_8():
    fig, ax = new_fig(14, 9)
    title(ax, "RAG 8가지 아키텍처 — 상황별 선택")
    rags = [
        ("1 Naive", "기본형·1-hop", "PoC", "#CFE2F3"),
        ("2 Multimodal", "이미지+텍스트", "도식 많은 문서", "#D9EAD3"),
        ("3 HyDE", "가상 답 만들고 검색", "모호한 질문", "#FFF2CC"),
        ("4 Corrective", "결과 채점·웹 fallback", "정확도 중요", "#FCE5CD"),
        ("5 Graph", "지식 그래프", "관계·다중 출처", "#F4CCCC"),
        ("6 Hybrid", "벡터+그래프", "최고 정확도", "#E2D5F0"),
        ("7 Adaptive", "질문 분류 후 분기", "다양한 유형", "#D5D5D5"),
        ("8 Agentic", "ReAct+멀티에이전트", "복잡 추론", "#FFCCCC"),
    ]
    for i, (n, d, when, fc) in enumerate(rags):
        row, col = i // 4, i % 4
        x, y = 3 + col * 24, 72 - row * 28
        box(ax, x, y+16, 22, 8, n, fc=fc, ec="#444", fontsize=12, bold=True)
        box(ax, x, y+8, 22, 8, d, fc="white", ec="#444", fontsize=10)
        ax.text(x+11, y+3, "쓰는 곳: "+when, ha="center", va="center", fontsize=9, color="#666", style="italic")
    save(fig, "12-rag-8.png")

# 13. API Protocols
def fig_api_protocols():
    fig, ax = new_fig(14, 8)
    title(ax, "API 프로토콜 — 11가지 중 REST + Webhooks 만 알아도 80%")
    protos = [
        ("REST", "HTTP+JSON", "거의 모든 API", "#0B5394", True),
        ("Webhooks", "이벤트 알림", "결제·메신저", "#38761D", True),
        ("GraphQL", "원하는 필드만", "모바일·복잡 UI", "#7B5BA6", False),
        ("WebSocket", "양방향 실시간", "채팅·게임", "#E69138", False),
        ("SSE", "서버 푸시 단방향", "실시간 알림", "#BF9000", False),
        ("gRPC", "고성능 RPC", "내부 통신", "#CC0000", False),
        ("SOAP", "XML 전통", "은행·정부", "#888", False),
        ("AMQP/MQTT", "메시지큐·IoT", "비동기", "#666", False),
        ("EDA/EDI", "이벤트·기업 간", "MSA·발주서", "#999", False),
    ]
    for i, (n, d, when, c, top) in enumerate(protos):
        row, col = i // 3, i % 3
        x, y = 3 + col * 31, 75 - row * 22
        is_top = top
        text_c = "white" if is_top else "#444"
        ax.text(x+15.5, y+12, "★ 핵심" if is_top else "", ha="center", fontsize=9, color="#CC0000", fontweight="bold")
        box(ax, x, y+5, 30, 7, n+" — "+d, fc=c, ec=c, text_color=text_c, fontsize=11, bold=True)
        box(ax, x, y-1, 30, 5, "쓰는 곳: "+when, fc="white", ec=c, fontsize=10)
    save(fig, "13-api-protocols.png")

# 14. Decision Tree (Skills/Subagents/MCP/Hooks)
def fig_decision_tree():
    fig, ax = new_fig(14, 8.5)
    title(ax, "Claude Code 결정 트리 — 4 도구 중 무엇?")
    # 트리 노드
    box(ax, 35, 78, 30, 6, "에이전트가 무엇이 필요?", fc="#FFE699", ec="#BF9000", fontsize=12, bold=True)
    box(ax, 8, 65, 22, 6, "지식 (Knowledge)", fc="#CFE2F3", ec="#0B5394", fontsize=11, bold=True)
    box(ax, 70, 65, 22, 6, "행동 (Action)", fc="#F4CCCC", ec="#CC0000", fontsize=11, bold=True)
    arrow(ax, 45, 78, 22, 71); arrow(ax, 55, 78, 81, 71)

    # 지식 → Skills / CLAUDE.md
    box(ax, 0, 50, 16, 6, "항상 로드", fc="#D9D2E9", ec="#674EA7", fontsize=10)
    box(ax, 20, 50, 16, 6, "작업별 로드", fc="#D9D2E9", ec="#674EA7", fontsize=10)
    arrow(ax, 13, 65, 8, 56); arrow(ax, 25, 65, 28, 56)
    box(ax, 0, 38, 16, 6, "CLAUDE.md", fc="#FCE5CD", ec="#E69138", fontsize=11, bold=True)
    box(ax, 20, 38, 16, 6, "SKILL", fc="#FCE5CD", ec="#E69138", fontsize=11, bold=True)
    arrow(ax, 8, 50, 8, 44); arrow(ax, 28, 50, 28, 44)

    # 행동 → Subagent / MCP / Hook
    box(ax, 50, 50, 14, 6, "내부 추론", fc="#D5E8D4", ec="#82B366", fontsize=10)
    box(ax, 66, 50, 14, 6, "외부, 모델결정", fc="#D5E8D4", ec="#82B366", fontsize=10)
    box(ax, 82, 50, 14, 6, "외부, 강제", fc="#D5E8D4", ec="#82B366", fontsize=10)
    arrow(ax, 77, 65, 57, 56); arrow(ax, 81, 65, 73, 56); arrow(ax, 85, 65, 89, 56)
    box(ax, 50, 38, 14, 6, "SUBAGENT", fc="#FCE5CD", ec="#E69138", fontsize=11, bold=True)
    box(ax, 66, 38, 14, 6, "MCP", fc="#FCE5CD", ec="#E69138", fontsize=11, bold=True)
    box(ax, 82, 38, 14, 6, "HOOK", fc="#FCE5CD", ec="#E69138", fontsize=11, bold=True)
    arrow(ax, 57, 50, 57, 44); arrow(ax, 73, 50, 73, 44); arrow(ax, 89, 50, 89, 44)

    # 한 줄 정리
    ax.text(50, 20, "지식 = Skill / CLAUDE.md     |     행동 = Subagent / MCP / Hook",
            ha="center", va="center", fontsize=12, color="#444", fontweight="bold")
    ax.text(50, 12, "위험 차단 = 반드시 HOOK (AI 가 아닌 결정론적 강제)",
            ha="center", va="center", fontsize=11, color="#CC0000", style="italic")
    save(fig, "14-decision-tree.png")

# 15. Complete Guide 6 steps
def fig_complete_guide():
    fig, ax = new_fig(14, 7)
    title(ax, "Claude Code 완전 가이드 — 6 단계 사이클")
    steps = [
        ("1 Install", "claude CLI 설치", "#CFE2F3"),
        ("2 Configure", "CLAUDE.md·hooks·skills", "#D9EAD3"),
        ("3 Prompt", "구체적 요청 작성", "#FFF2CC"),
        ("4 Review", "결과 검토·수정 요청", "#FCE5CD"),
        ("5 Iterate", "반복 개선", "#E2D5F0"),
        ("6 Ship", "출시·배포", "#F4CCCC"),
    ]
    for i, (n, d, fc) in enumerate(steps):
        x = 3 + i * 16
        box(ax, x, 50, 14, 18, n+"\n"+d, fc=fc, ec="#444", fontsize=11, bold=True)
        if i < 5:
            arrow(ax, x + 14, 59, x + 16, 59)
    # 루프 화살표 (6 → 3)
    arrow(ax, 91, 50, 91, 30)
    arrow(ax, 91, 30, 38, 30)
    arrow(ax, 38, 30, 38, 50)
    ax.text(65, 25, "필요시 3 으로 루프", ha="center", va="center", fontsize=10, color="#666", style="italic")
    save(fig, "15-complete-guide.png")

# 16. Architecture Reference (60-sec setup + 5 layer)
def fig_arch_ref():
    fig, ax = new_fig(14, 8.5)
    title(ax, "Claude Code 아키텍처 — 60초 셋업 + 5 레이어")
    layers = [
        ("Layer 5", "Orchestration", "Hooks·체크포인트", "#CC0000"),
        ("Layer 4", "Commands", "/init·/clear·/compact", "#E69138"),
        ("Layer 3", "MCP Connections", "GitHub·Slack·Postgres 200+", "#BF9000"),
        ("Layer 2", "Skills Engine", ".claude/skills/ — 자동 로드", "#38761D"),
        ("Layer 1", "Memory System", "CLAUDE.md (Global·Project·Folder)", "#0B5394"),
        ("Foundation", "Runtime", "claude 명령·파일 접근", "#666"),
    ]
    for i, (l, n, d, c) in enumerate(layers):
        y = 72 - i * 10
        box(ax, 5, y, 18, 8, l+"\n"+n, fc="white", ec=c, fontsize=11, bold=True, text_color=c)
        box(ax, 25, y, 70, 8, d, fc="white", ec=c, fontsize=11)
    ax.text(50, 8, "60초 셋업: npm install → claude → /init → 끝",
            ha="center", va="center", fontsize=12, color="#444", fontweight="bold")
    save(fig, "16-arch-reference.png")

# 17. Project Structure
def fig_project_structure():
    fig, ax = new_fig(13, 8.5)
    title(ax, "Claude Code 프로젝트 구조")
    items = [
        ("📄 CLAUDE.md", "팀 공유 규칙 (git commit)", "#FFE699"),
        ("📁 .claude/commands/", "슬래시 명령 (/review·/test)", "#CFE2F3"),
        ("📁 .claude/skills/", "자동 워크플로우 (SKILL.md)", "#D9EAD3"),
        ("📁 .claude/agents/", "subagent (code-reviewer.md)", "#FCE5CD"),
        ("📁 .claude/hooks/", "가드레일 (PreToolUse.sh)", "#F4CCCC"),
        ("📄 .mcp.json", "MCP 서버 설정 (GitHub·Postgres)", "#E2D5F0"),
        ("📄 settings.json", "권한 + hook 등록", "#D5D5D5"),
        ("📁 plugins/", "원본 (sync 소스)", "#FFCCCC"),
    ]
    for i, (n, d, fc) in enumerate(items):
        y = 78 - i * 9
        box(ax, 5, y, 35, 7, n, fc=fc, ec="#444", fontsize=12, bold=True)
        box(ax, 42, y, 53, 7, d, fc="white", ec="#444", fontsize=11)
    save(fig, "17-project-structure.png")

# 18. DK .claude folder
def fig_dk_folder():
    fig, ax = new_fig(13, 8.5)
    title(ax, ".claude 폴더 전체 구조 (DK 메소드)")
    items = [
        ("CLAUDE.md", "팀 공유 기억", "git commit", "#FFE699"),
        ("CLAUDE.local.md", "나만의 기억", "gitignore", "#FFD1DC"),
        (".claude/settings.json", "권한 설정 (공유)", "commit", "#CFE2F3"),
        (".claude/settings.local", "개인 권한", "gitignore", "#D9D2E9"),
        (".claude/commands/", "나만의 / 명령어", "commit", "#D9EAD3"),
        (".claude/rules/", "항상 적용 규칙", "commit", "#FCE5CD"),
        (".claude/skills/", "자동 워크플로우", "commit", "#F4CCCC"),
        (".claude/agents/", "서브에이전트", "commit", "#E2D5F0"),
    ]
    for i, (n, d, g, fc) in enumerate(items):
        y = 78 - i * 9
        box(ax, 5, y, 28, 7, n, fc=fc, ec="#444", fontsize=11, bold=True)
        box(ax, 35, y, 38, 7, d, fc="white", ec="#444", fontsize=10)
        gc = "#CC0000" if "ignore" in g else "#0B5394"
        box(ax, 75, y, 20, 7, g, fc="white", ec=gc, text_color=gc, fontsize=10, bold=True)
    save(fig, "18-dk-folder.png")

# 19. CLAUDE.md design
def fig_claude_md_design():
    fig, ax = new_fig(14, 8.5)
    title(ax, "CLAUDE.md 설계 가이드 — 3 Scopes + WHAT/WHY/HOW + 5 Rules")
    # 3 Scopes
    ax.text(50, 86, "3 SCOPES (가까운 게 이김)", ha="center", fontsize=12, color="#0B5394", fontweight="bold")
    box(ax, 3, 73, 28, 8, "GLOBAL\n~/.claude/CLAUDE.md", fc="#CFE2F3", ec="#0B5394", fontsize=10, bold=True)
    box(ax, 36, 73, 28, 8, "PROJECT\n./CLAUDE.md", fc="#D9EAD3", ec="#38761D", fontsize=10, bold=True)
    box(ax, 69, 73, 28, 8, "FOLDER\n./src/CLAUDE.md", fc="#FFE699", ec="#BF9000", fontsize=10, bold=True)
    arrow(ax, 31, 77, 36, 77); arrow(ax, 64, 77, 69, 77)
    ax.text(50, 67, "→ Folder > Project > Global", ha="center", fontsize=10, color="#666", style="italic")

    # WHAT/WHY/HOW
    ax.text(50, 60, "WHAT / WHY / HOW", ha="center", fontsize=12, color="#0B5394", fontweight="bold")
    box(ax, 3, 47, 30, 10, "WHAT (컨텍스트)\n목적·기술스택·구조", fc="#FCE5CD", ec="#E69138", fontsize=10)
    box(ax, 35, 47, 30, 10, "WHY (원칙)\n아키텍처·스타일·금기", fc="#F4CCCC", ec="#CC0000", fontsize=10)
    box(ax, 67, 47, 30, 10, "HOW (워크플로우)\nbuild·test·commit", fc="#D5E8D4", ec="#82B366", fontsize=10)

    # 5 Rules
    ax.text(50, 38, "5 RULES", ha="center", fontsize=12, color="#0B5394", fontweight="bold")
    rules = ["1. /init 먼저", "2. 500줄 이하", "3. Hooks 사용", "4. 월간 업데이트", "5. 참조 중심"]
    for i, r in enumerate(rules):
        x = 3 + i * 19
        box(ax, x, 22, 18, 10, r, fc="#E2D5F0", ec="#7B5BA6", fontsize=10, bold=True)

    ax.text(50, 10, "CLAUDE.md = AI 팀원 온보딩 문서 (사람용 README 아님)",
            ha="center", va="center", fontsize=11, color="#CC0000", style="italic", fontweight="bold")
    save(fig, "19-claude-md-design.png")

# 20. Prompt Frameworks
def fig_prompt_8():
    fig, ax = new_fig(14, 8.5)
    title(ax, "8가지 프롬프트 프레임워크 — CLARITY 만으로 80%")
    frameworks = [
        ("CLARITY ★", "처음·만능", "Context·Look·Ask·Rules·Input·Target·You", "#FFE699"),
        ("SOCRATES", "단계별 계획", "Situation·Objective·Constraints·Role·Action·Thinking·Evaluation·Summary", "#CFE2F3"),
        ("ANTICIPATE", "상품 기획", "Audience·Need·Task·Information·Plan·Act·Test·Enhance", "#D9EAD3"),
        ("PARTNER", "콘텐츠 전략", "Purpose·Audience·Research·Think·Narrow·Execute·Review", "#FCE5CD"),
        ("TRUST", "깊이 있는 분석", "Task·Reason·Understand·Structure·Tailor", "#F4CCCC"),
        ("RIPPLE", "데이터 분석", "Role·Input·Process·Points·Layout·Evaluate", "#E2D5F0"),
        ("CATCH", "마케팅 카피", "Context·Aim·Tone·Criteria·Help", "#D9D2E9"),
        ("MAGIC", "랜딩페이지", "Motivation·Audience·Goal·Input·Create", "#FFCCCC"),
    ]
    for i, (n, when, full, fc) in enumerate(frameworks):
        y = 78 - i * 9
        box(ax, 5, y, 22, 7, n, fc=fc, ec="#CC0000" if "★" in n else "#444",
            fontsize=11, bold=True)
        box(ax, 29, y, 16, 7, "쓰는 곳: "+when, fc="white", ec="#444", fontsize=10)
        box(ax, 47, y, 48, 7, full, fc="white", ec="#444", fontsize=9)
    save(fig, "20-prompt-8.png")


# --------- 실행 (전수 20개) ---------
print("[+] 한글 다이어그램 전수 생성 (20개)...")
fig_gen_agentic_agent()
fig_5_cores()
fig_5_stack()
fig_dev_kit_5layers()
fig_builder_matrix()
fig_mcp_vs_a2a()
fig_14_levels()
fig_8_models()
fig_9_killers()
fig_zero_cost()
fig_rag_intro()
fig_rag_8()
fig_api_protocols()
fig_decision_tree()
fig_complete_guide()
fig_arch_ref()
fig_project_structure()
fig_dk_folder()
fig_claude_md_design()
fig_prompt_8()
print(f"\n총 20개 PNG 생성 완료: {OUT_DIR}")
