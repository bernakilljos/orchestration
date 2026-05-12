"""각 챕터 dict 에 '강사' 키 자동 주입 — 친근 톤 인트로 3-5줄.

각 챕터의 '핵심' + '강추' 활용 → 강사 톤 변환.
"""
import re
from pathlib import Path

LECT = Path(__file__).resolve().parent / "build-arch-lecture-doc.py"

# 챕터 prefix → 강사 인트로 (강사 톤, 친근, 일상 비유, 학습자 가정)
INTROS = {
    "1. AI 3종 세트": [
        "여러분, AI 라고 하면 보통 ChatGPT 만 떠올리시죠? 근데 AI 가 사실 진화 단계가 있어요.",
        "Generative 는 '글만 쓰는 카피라이터'. 시키는 대로 한 번 답하고 끝.",
        "Agentic 는 '신입 매니저' — 목표 주면 단계를 짜요. 단 실행은 사람이.",
        "AI Agent 는 '경력 매니저' — 외부 API 까지 직접 호출하고 24/7 돌아갑니다.",
        "**우리 orchestration_v1 = Multi-Agent (가장 진화)** — Claude+Codex+Gemini+Haiku 가 회사처럼 협업.",
    ],
    "2. AI 에이전트의 8가지": [
        "AI 뇌는 한 종류가 아니에요. 작업에 맞는 뇌를 골라써야 비용·품질이 최적이죠.",
        "비싼 모델 (Claude Opus) 만 쓰면 비용 폭증. 작은 모델 (Haiku) 로 80% 처리하고 큰 모델은 어려운 20% 만.",
        "**8개 모델 우리가 코드로 만드는 건 0개** — Claude·Codex·Gemini·Haiku 가 다 제공. 우리는 라우팅만 합니다.",
        "초보자 추천: GPT 계열 1개 (Claude or GPT-4) 로 시작 — 단순함 우선.",
    ],
    "3. 에이전트의 5가지": [
        "안전한 에이전트는 5부품 모두 필요해요. 회사로 비유하면:",
        "1) 입구 경비실 (Guardrails) — 잘못된 입력·민감정보 차단",
        "2) 부장님 (Orchestration) — 작업 분해·라우팅",
        "3) 도구함 (Tools/MCP) — GitHub·DB·API 안전 연결",
        "4) 서류 캐비넷 (Memory) — 단기/중기/장기 기억",
        "5) CCTV+회의록 (Observability) — 추적·비용 로그",
        "우리 시스템 = 5부품 모두 풍부. 24 hooks + 11 MCP + orca.db + recall-memory.",
    ],
    "4. 9가지 숨은 함정": [
        "성공한 에이전트는 다양하지만 망한 에이전트는 9가지 패턴 중 하나. 이거 피하면 사고 80% ↓.",
        "가장 무서운 3개: **#4 Runaway Loop** (재시도 847번), **#8 Cost Blind** ($48,200 청구), **#9 No Failure Mode** (모르면 거짓말).",
        "우리 시스템 대응: watchdog backoff + orca.db budget + failure-mode.md 5중박기.",
        "9 중 8 ✅ 대응 — 본보기 수준입니다.",
    ],
    "5. AI 스택 5층": [
        "AI 시스템은 빌딩 같아요. 아래부터 5층 올리세요:",
        "1 Infra (실행) → 2 Data (RAG) → 3 LLM (추론) → 4 Orchestration (워크플로우) → 5 Interface (UI)",
        "**GPU 0 으로도 5층 다 작동** — LLM 만 외부 API (Claude) 쓰면 GPU 부담 0.",
        "우리 = 5/5 작동. Data 층 = ChromaDB 로컬 RAG 추가 (이번 세션).",
    ],
    "6. 에이전트 개발킷": [
        "Claude Code 의 5 레이어 = CLAUDE.md + Skills + Hooks + Subagents + Plugins.",
        "각 레이어 책임 분명 — 어디서 결정됐는지 명확.",
        "**Hooks 가 결정론적 강제** — AI 신뢰 X. 위험 명령 차단은 무조건 Hook.",
        "우리 = **34 hooks + 145 skills + 44 subagents + 26 plugins** — 본보기 수준.",
    ],
    "7. 제로비용 AI": [
        "회사 카드 없어도 AI 띄울 수 있어요. 무료 도구만으로:",
        "Frontend (Next.js/Streamlit) · Orchestrator (LangGraph) · LLM (Ollama+Gemma 로컬) · RAG (ChromaDB) · Tool (MCP) · Deploy (Cloudflare)",
        "**우리 = 거의 제로비용 본보기** — Claude Code CLI + exec_orch + SQLite + 선택 Ollama. 유료는 Claude API ($20/월) 만.",
        "초보자: 1+2 만으로 80% 작업. 작은 모델 + 작은 폴더로 시작하세요.",
    ],
    "8. AI 빌더 도구": [
        "AI 도구 백화점. 6 카테고리 × 5 도구 = 30 개 중 본인 필요한 거만 골라쓰세요.",
        "초보 = 1+2 (Claude + Claude Code) 만으로 80% 작업.",
        "MVP 만들기 = 3 (Lovable·v0) 추가.",
        "회사 배포 = 4·5 (HuggingFace·LangChain).",
        "콘텐츠 = 6 (Mirra·Midjourney·Runway).",
        "우리 = 5/6 활용 + 1개 의도적 미사용 (앱·프로토타입은 우리 작업 외).",
    ],
    "9. RAG 입문": [
        "RAG = 검색(Retrieval) + 생성(Generation). LLM 이 모르는 내용을 외부 문서에서 찾아 답하게 합니다.",
        "장점: 출처 표시 가능 (감사·검증 강함) + Hallucination ↓.",
        "**우리 = ChromaDB + 한글 임베딩 (paraphrase-multilingual)** + 36 docs indexed.",
        "Hook 자동 통합 — 사용자 메시지 시 관련 memory 자동 recall.",
    ],
    "10. RAG 8가지": [
        "데이터 특성·정확도 요구에 따라 RAG 도 8가지 중 골라야:",
        "Naive (PoC) → Corrective (정확도) → HyDE (모호) → Graph (관계) → Adaptive (다양) → Agentic (최고).",
        "**우리 = 8/8 모두 구현** (rag-naive·corrective·hyde·adaptive·agentic·graph·multimodal·hybrid). 학계 표준 다 작동.",
    ],
    "11. API 프로토콜": [
        "프로토콜 11가지 중 AI 작업엔 **REST + Webhooks 만 알면 80%** 커버.",
        "REST = HTTP+JSON 표준. 거의 모든 API.",
        "Webhooks = 이벤트 콜백. GitHub·Slack 알림.",
        "토큰 스트리밍 = SSE (Claude API 자동).",
        "우리 = REST 11+ MCP + Webhooks (GitHub/Slack) + EDA (auto-dispatch).",
    ],
    "12. MCP vs A2A": [
        "MCP = LLM 한 명이 도구 호출. A2A = 여러 Agent 가 자율 협력.",
        "보통 = MCP (단순·디버깅 쉬움). 멀티 도메인 = A2A.",
        "**우리 = MCP 11 서버 + A2A-lite chain** (Claude 통제 + auto-dispatch). 둘 다 본보기.",
    ],
    "13. Claude 마스터": [
        "Claude Code 사용 능력 = 14 레벨로 나눌 수 있어요.",
        "Lv 1-5 (입문): 단일 명령·기본 hook.",
        "Lv 6-10 (중급): MCP·Skills·Subagents 활용.",
        "Lv 11-14 (마스터): plugin 개발·multi-agent chain·CI/CD 통합.",
        "우리 시스템 사용자 = Lv 9-10 추정. 본 강의 끝나면 Lv 11+ 가능.",
    ],
    "14. Claude Code 결정트리": [
        "4 도구 (Skills/Subagents/MCP/Hooks) 중 무엇을 쓸지 결정:",
        "지식 = Skills/CLAUDE.md. 외부 호출 = MCP. 강제 = Hooks. 격리 추론 = Subagent.",
        "**위험 차단 = 반드시 Hook** (AI 신뢰 X). rm -rf 차단은 PreToolUse hook 강제.",
        "우리 = 4/4 다 활용.",
    ],
    "15. Claude Code 완전 가이드": [
        "6 단계 사이클: Install → Configure → Prompt → Review → Iterate → Ship.",
        "각 단계 산출물 명확. 작은 PR 단위로 사이클 돌리세요.",
        "Review·Iterate 가 핵심 — 한 번에 완벽 X.",
        "우리 = 6/6 다 작동. install.bat (Zero-touch) + eval_quality + watchdog + auto-review CI.",
    ],
    "16. Claude Code 아키텍처": [
        "한 장에 5 레이어 + 60초 셋업 + 키 단축키 정리한 치트시트.",
        "60초 셋업: npm install -g claude-code → claude → /init → 끝.",
        "/compact (컨텍스트 압축), /clear (초기화) 외우면 비용 ↓.",
        "주 1회 봐주세요 — 새 단축키 발견 = 시간 절약.",
    ],
    "17. Claude Code 프로젝트": [
        "어디에 무엇을 두는가 표준 — 90점 시작.",
        "CLAUDE.md (팀 규칙) · settings.json (권한+hook) · .claude/ (commands/skills/agents/hooks) · plugins/ (원본 SoT).",
        "이 구조만 따르면 90점. 나머지 10점 = 팀 합의로 보완.",
    ],
    "18. .claude 폴더": [
        ".claude 폴더 = AI 팀원의 사무실.",
        "commit (팀 공유): CLAUDE.md · settings.json · commands/ · rules/ · skills/ · agents/",
        "gitignore (개인): CLAUDE.local.md · settings.local · .env",
        "시크릿은 절대 commit X — 우리 secret-scan hook 자동 차단.",
    ],
    "19. CLAUDE.md 설계": [
        "CLAUDE.md 는 사람용 README 가 아니라 **AI 팀원 온보딩 문서**.",
        "3 Scope: Global (~/.claude/) · Project (./CLAUDE.md) · Folder (./src/CLAUDE.md). 가까운 게 이김.",
        "5 Rules: /init 먼저 · 500줄 이하 · Hooks 사용 · 월간 갱신 · 참조 중심.",
        "우리 = 169줄 (한계의 33%, 충분히 짧음) + 5중박기 + 13 금지.",
    ],
    "20. 8가지 프롬프트": [
        "프롬프트는 '대충 쓰기' 아니라 '템플릿'. 8 중 1개 (CLARITY) 만 외워도 80%.",
        "CLARITY = Context+Look+Ask+Rules+Input+Target+Yardstick.",
        "복잡 작업 = TRUST. 데이터 분석 = RIPPLE.",
        "우리 task-instruction.md = CLARITY 구조와 일치. 다 활용.",
    ],
}


def inject():
    src = LECT.read_text(encoding="utf-8")
    added = 0
    for prefix, intro_lines in INTROS.items():
        # 각 챕터 dict 찾기 — "title": "<prefix> ..." 패턴
        pattern = rf'("title":\s*"{re.escape(prefix)}[^"]*",\s*)'
        if not re.search(pattern, src):
            continue
        # 이미 "강사" 키 있으면 skip
        # 챕터 dict 의 "핵심" 키 다음에 "강사" 키 주입
        intro_str = ", ".join(f'"{line}"' for line in intro_lines)
        # "핵심": "...", 패턴 → 그 뒤에 "강사": [...] 추가
        new_src, n = re.subn(
            rf'("title":\s*"{re.escape(prefix)}[^"]*",\s*\n\s*"image_eng"[^,]*,\s*\n\s*"image_kor"[^,]*,\s*\n\s*"핵심":\s*"[^"]*",\s*\n)(\s*)("표")',
            rf'\1\2"강사": [{intro_str}],\n\2\3',
            src,
        )
        if n > 0:
            src = new_src
            added += 1
    LECT.write_text(src, encoding="utf-8")
    return added


if __name__ == "__main__":
    n = inject()
    print(f"강사 인트로 주입: {n}/{len(INTROS)} 챕터")
