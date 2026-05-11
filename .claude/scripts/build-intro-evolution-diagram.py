"""AI 4단계 진화 다이어그램 — 0. 들어가며 자투리 fix 용.
Generative → Agentic → Agent → Multi-Agent (우리 위치 강조).
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "docs" / "screens" / "arch-kor"
OUT.mkdir(parents=True, exist_ok=True)

HTML = """<!DOCTYPE html><html><head><meta charset='utf-8'><style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Malgun Gothic','맑은 고딕',sans-serif}
body{width:1300px;height:900px;padding:24px 36px;overflow:hidden;
     background:radial-gradient(ellipse at top,#F8FAFC 0%,#E8EFF8 100%)}
.title{font-size:38px;font-weight:900;background:linear-gradient(135deg,#1F3864,#3F6FB5);
       -webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin-bottom:4px}
.subtitle{font-size:20px;color:#637488;text-align:center;margin-bottom:24px;font-style:italic}
.flow{display:flex;gap:14px;align-items:stretch;margin-bottom:30px;position:relative}
.step{flex:1;padding:12px 10px;border-radius:14px;box-shadow:0 6px 18px rgba(0,0,0,0.08);
      background:linear-gradient(135deg,#fff,#f7f9fc);position:relative;border:2px solid #ccc;
      min-height:310px;display:flex;flex-direction:column}
.s1{border-color:#FC8181;background:linear-gradient(135deg,#FFF5F5,#FFEBEB)}
.s2{border-color:#F6AD55;background:linear-gradient(135deg,#FFFAF0,#FFF1D5)}
.s3{border-color:#68D391;background:linear-gradient(135deg,#F0FFF4,#C6F6D5)}
.s4{border-color:#3182CE;background:linear-gradient(135deg,#EBF8FF,#BEE3F8);
    box-shadow:0 10px 30px rgba(49,130,206,0.35);transform:scale(1.03)}
.s4::before{content:'★ 우리';position:absolute;top:-16px;left:50%;transform:translateX(-50%);
            background:linear-gradient(135deg,#FFE699,#F6AD55);padding:4px 14px;border-radius:14px;
            font-weight:900;color:#7C2D12;font-size:18px;box-shadow:0 4px 10px rgba(0,0,0,0.15);white-space:nowrap}
.s-icon{font-size:40px;margin-bottom:6px;display:block;text-align:center}
.s-title{font-size:24px;font-weight:900;color:#1F3864;margin-bottom:4px;text-align:center}
.s-eng{font-size:15px;color:#666;text-align:center;margin-bottom:10px;font-style:italic}
.s-desc{font-size:17px;color:#333;line-height:1.4;margin-bottom:8px;flex-grow:1}
.s-ex{font-size:14px;color:#555;line-height:1.4;padding-top:8px;border-top:1px dashed #aaa}
.s-ex b{color:#1F3864;display:block;margin-bottom:2px}
.arrow-row{display:flex;justify-content:space-around;margin:-22px 0 14px;font-size:14px;color:#3F6FB5;font-weight:700}
.arrow-row span{background:#fff;padding:3px 10px;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,0.1)}
.banner{margin-top:8px;padding:16px 22px;background:linear-gradient(135deg,#1F3864,#3F6FB5);
        color:white;border-radius:14px;box-shadow:0 8px 24px rgba(31,56,100,0.25)}
.banner-title{font-size:20px;font-weight:800;margin-bottom:10px}
.bn-grid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px}
.bn-cell{background:rgba(255,255,255,0.12);padding:10px 12px;border-radius:8px;font-size:15px;line-height:1.4}
.bn-cell b{color:#FFE699;display:block;margin-bottom:4px;font-size:16px}
</style></head><body>
<div class='title'>AI 4단계 진화 — 우리가 어디 있나</div>
<div class='subtitle'>Generative → Agentic → Agent → Multi-Agent (가장 진화된 형태)</div>

<div class='flow'>
  <div class='step s1'>
    <span class='s-icon'>✍️</span>
    <div class='s-title'>1. Generative</div>
    <div class='s-eng'>생성 AI</div>
    <div class='s-desc'>글·그림·코드를 한 번에 생성. 사람이 매번 시켜야.</div>
    <div class='s-ex'><b>예시</b>ChatGPT 단발 질문<br>DALL-E 이미지</div>
  </div>
  <div class='step s2'>
    <span class='s-icon'>🗺️</span>
    <div class='s-title'>2. Agentic</div>
    <div class='s-eng'>스스로 계획</div>
    <div class='s-desc'>목표 주면 단계를 직접 짜고 도구 호출.</div>
    <div class='s-ex'><b>예시</b>AutoGPT<br>ReAct/CoT 에이전트</div>
  </div>
  <div class='step s3'>
    <span class='s-icon'>🤖</span>
    <div class='s-title'>3. AI Agent</div>
    <div class='s-eng'>실제 API 호출</div>
    <div class='s-desc'>외부 API 호출 + 자가 평가. 24/7 운영.</div>
    <div class='s-ex'><b>예시</b>Devin<br>MCP 도구 호출 봇</div>
  </div>
  <div class='step s4'>
    <span class='s-icon'>🏢</span>
    <div class='s-title'>4. Multi-Agent</div>
    <div class='s-eng'>회사형 협업</div>
    <div class='s-desc'>여러 AI 가 역할 분담·인수인계. 자율 운영.</div>
    <div class='s-ex'><b>예시</b>orchestration_v1<br>(Claude+Codex+Gemini+Haiku)</div>
  </div>
</div>

<div class='arrow-row'>
  <span>→ + 자율 계획</span>
  <span>→ + 외부 API·자가 평가</span>
  <span>→ + 다중 협업·역할 분담</span>
</div>

<div class='banner'>
  <div class='banner-title'>🎯 우리 orchestration_v1 = 4단계 Multi-Agent — 가장 진화된 형태</div>
  <div class='bn-grid'>
    <div class='bn-cell'><b>설계·복잡 추론</b>Claude Opus 4.7<br>(Extended Thinking)</div>
    <div class='bn-cell'><b>코드 500줄+</b>Codex CLI<br>(×4 병렬)</div>
    <div class='bn-cell'><b>장문·멀티모달</b>Gemini Flash<br>(>500k 토큰)</div>
    <div class='bn-cell'><b>빠른 검증</b>Haiku 4.5<br>(prompt cache 90%↓)</div>
  </div>
</div>
</body></html>"""


async def main():
    out = OUT / "00-ai-evolution.png"
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": 1300, "height": 900})
        await page.set_content(HTML)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=str(out), full_page=False,
                              clip={"x": 0, "y": 0, "width": 1300, "height": 900})
        await b.close()
    print(f"[OK] {out}")


if __name__ == "__main__":
    asyncio.run(main())
