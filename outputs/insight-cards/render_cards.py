"""Render 10 individual family cards (1080x1080) for learning."""
import asyncio
from pathlib import Path

HERE = Path(__file__).parent
OUT_DIR = HERE
OUT_DIR.mkdir(exist_ok=True)

FAMILIES = [
    {
        "num": "01", "emoji": "🧠", "name": "뇌화", "color": "#ef476f",
        "subtitle": "AI 를 진짜 뇌처럼",
        "metaphor": "🖥️ 계산기 → 🪆 인형 → 👶 진짜 아기",
        "steps": [
            ("GPU", "~2020", "past"),
            ("Neuromorphic 칩", "2026 ★", "now"),
            ("Wetware (진짜 뇌세포)", "2026 ★", "now"),
            ("BCI (사람 뇌 직접)", "2028+", "future"),
        ],
        "why": "AI 전력 위기 → 진짜 뇌 효율 (전구 하나) 추격",
        "real": "IBM NorthPole, Cortical Labs CL1, Neuralink",
    },
    {
        "num": "02", "emoji": "💾", "name": "기억", "color": "#06d6a0",
        "subtitle": "AI 가 어떻게 기억하나",
        "metaphor": "📖 책장 → 📓 일기장 → 🧠 두뇌 자체",
        "steps": [
            ("RAG (외부 책장)", "~2024", "past"),
            ("mem0 (개인 일기장)", "2026 ★", "now"),
            ("Liquid AI (두뇌 변함)", "2026 ★", "now"),
            ("Wetware 메모리", "2030+", "future"),
        ],
        "why": "정보가 외부 → 옆 → 안 으로 점점 깊이 들어감",
        "real": "LangChain, Mem0 (YC W24), Liquid AI LFM",
    },
    {
        "num": "03", "emoji": "📝", "name": "생성", "color": "#ffd166",
        "subtitle": "AI 가 답을 만드는 방식",
        "metaphor": "✍️ 한 글자씩 → 🎨 그림처럼 한 방에",
        "steps": [
            ("Autoregressive (한 글자씩)", "~2025", "past"),
            ("Diffusion LLM", "2026 ★", "now"),
            ("Hybrid 결합", "2027", "future"),
        ],
        "why": "Agent 시대 = 긴 답 폭증 → 10배 빠르게 + 비용 1/10",
        "real": "Inception Mercury 2, LLaDA-8B (open-source)",
    },
    {
        "num": "04", "emoji": "🔌", "name": "연결", "color": "#118ab2",
        "subtitle": "GPU 끼리 데이터 이동",
        "metaphor": "🚗 자동차 도로 → ✈️ 비행기 (빛)",
        "steps": [
            ("구리 전선", "~2025", "past"),
            ("Photonic (실리콘 포토닉스)", "2026 ★", "now"),
            ("광+양자 하이브리드", "2028+", "future"),
        ],
        "why": "GPU 100만대 80% idle = 통신이 진짜 병목. 빛이 풀음",
        "real": "Lightmatter Passage L200, Ayar Labs TeraPHY",
    },
    {
        "num": "05", "emoji": "🌐", "name": "표현", "color": "#a78bfa",
        "subtitle": "세상을 이해하는 차원",
        "metaphor": "📚 글 잘 쓰는 작가 → 🏗️ 3D 짓는 건축가",
        "steps": [
            ("언어 (인간 뇌의 5%)", "~2025", "past"),
            ("Spatial AI (3D 공간)", "2026 ★", "now"),
            ("시간·인과 추가", "2028+", "future"),
        ],
        "why": "인간 뇌 70% 가 공간 처리. 언어만 모방하면 얕은 지능",
        "real": "World Labs Marble (Fei-Fei Li, $1.23B)",
    },
    {
        "num": "06", "emoji": "⚛️", "name": "연산", "color": "#ff8c42",
        "subtitle": "계산 방식 자체",
        "metaphor": "⚪⚫ 0/1 → 🔄 동시 → 🔗 여러 대 합치기",
        "steps": [
            ("고전 GPU (0 or 1)", "~2025", "past"),
            ("NISQ 양자 (수십~수천 큐비트)", "2026 ★", "now"),
            ("Cockatoo (분산 양자)", "2027 ★", "now"),
            ("Fault-tolerant 양자", "2029+", "future"),
        ],
        "why": "QUBO·포트폴리오 최적화 양자 우위 첫 검증 시작",
        "real": "IBM Quantum, D-Wave, Allstate (production)",
    },
    {
        "num": "07", "emoji": "⚡", "name": "전기", "color": "#fcbf49",
        "subtitle": "AI 의 밥",
        "metaphor": "🔌 콘센트 → ☢️ 미니 원전 → ☀️ 핵융합",
        "steps": [
            ("일반 전기", "~2025", "past"),
            ("SMR (소형 모듈 원자로)", "2027 ★", "now"),
            ("핵융합 (Fusion)", "2030+", "future"),
        ],
        "why": "데이터센터 1개 = 도시 1개 전기. 빅테크 $10B 약속",
        "real": "Microsoft TMI, Amazon, Meta+Oklo, Google+Kairos",
    },
    {
        "num": "08", "emoji": "🛡️", "name": "신뢰", "color": "#f72585",
        "subtitle": "AI 생성물·계산 증명",
        "metaphor": "❓ 누가 만들었나 → 🔏 cryptographic 도장",
        "steps": [
            ("Watermark (제거 가능)", "~2025", "past"),
            ("C2PA (출처 증명)", "2026 ★", "now"),
            ("PQC (양자내성 암호)", "2026-28 ★", "now"),
            ("동형암호·ZKP", "2028+", "future"),
        ],
        "why": "가짜 콘텐츠 폭증 + 양자가 곧 기존 암호 다 깸",
        "real": "Adobe C2PA, NIST FIPS 203/204/205",
    },
    {
        "num": "09", "emoji": "🤝", "name": "협업", "color": "#4cc9f0",
        "subtitle": "AI 끼리 팀워크",
        "metaphor": "🧑 혼자 → 👨‍👩‍👧 팀 → 🏛️ AI Society",
        "steps": [
            ("단일 LLM (ChatGPT)", "~2024", "past"),
            ("Multi-agent (team)", "2026 ★", "now"),
            ("Autonomous agent", "2026-27 ★", "now"),
            ("AI Society", "2028+", "future"),
        ],
        "why": "17% 배포 → 60% 2년내 (Gartner 가장 공격적 채택)",
        "real": "Anthropic Claude Code, OpenAI Swarm, AutoGen",
    },
    {
        "num": "10", "emoji": "🦾", "name": "감각·몸", "color": "#b5179e",
        "subtitle": "AI 가 몸을 얻는다",
        "metaphor": "📝 글 → 🎨 그림 → 🎬 영상 → 🤖 로봇",
        "steps": [
            ("텍스트·이미지", "~2024", "past"),
            ("멀티모달 (영상까지)", "2026 ★", "now"),
            ("Physical AI (로봇)", "2026 ★", "now"),
            ("가정 휴머노이드 $20K", "2028+", "future"),
        ],
        "why": "1956 지능 모방 시작 → 70년 만에 신체성 시작",
        "real": "LG CLOiD, Apptronik, Figure AI, Tesla Optimus",
    },
]

CARD_TPL = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><title>{name}</title><style>
* {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Pretendard', 'Malgun Gothic', sans-serif; }}
body {{
  width: 1080px; height: 1080px;
  background: linear-gradient(135deg, #0f1419 0%, #1a2540 100%);
  color: #e8eef5; padding: 50px 55px;
  display: flex; flex-direction: column;
  position: relative; overflow: hidden;
}}
body::before {{
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 10px;
  background: {color};
}}
.head {{ display: flex; align-items: center; gap: 24px; margin-bottom: 28px; }}
.num {{ font-size: 70px; font-weight: 900; color: {color}; line-height: 1; }}
.emoji {{ font-size: 110px; line-height: 1; }}
.title-block {{ display: flex; flex-direction: column; gap: 6px; flex: 1; }}
.name {{ font-size: 70px; font-weight: 900; color: #fff; line-height: 1; }}
.subtitle {{ font-size: 26px; color: #8a9bb0; }}
.metaphor {{
  background: rgba(255, 255, 255, 0.05);
  border-left: 5px solid {color};
  padding: 20px 28px;
  border-radius: 6px;
  font-size: 30px;
  font-weight: 600;
  margin-bottom: 30px;
  color: #fff;
}}
.steps {{ display: flex; flex-direction: column; gap: 18px; margin-bottom: 30px; flex: 1; }}
.step {{
  display: flex; align-items: center; gap: 18px;
  padding: 16px 22px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 12px;
  border-left: 4px solid #3a4660;
}}
.step.now {{
  background: rgba(255, 255, 255, 0.09);
  border-left-color: {color};
  box-shadow: 0 0 24px {color}33;
}}
.step.past {{ opacity: 0.5; }}
.step.future {{ opacity: 0.7; border-left-style: dashed; }}
.step .dot {{ width: 16px; height: 16px; border-radius: 50%; background: #5a6a85; flex-shrink: 0; }}
.step.now .dot {{ background: {color}; box-shadow: 0 0 12px {color}; }}
.step.future .dot {{ background: transparent; border: 2px dashed #8a9bb0; }}
.step-text {{ font-size: 28px; font-weight: 700; color: #fff; flex: 1; }}
.step.past .step-text {{ color: #8a9bb0; font-weight: 500; }}
.step.future .step-text {{ color: #b8c3d6; font-style: italic; }}
.step-year {{ font-size: 20px; color: #8a9bb0; font-weight: 600; }}
.step.now .step-year {{ color: {color}; font-weight: 800; }}
.why {{
  background: rgba(255, 209, 102, 0.08);
  border-left: 4px solid {color};
  padding: 18px 24px;
  border-radius: 6px;
  font-size: 22px;
  color: #fff;
  margin-bottom: 14px;
  line-height: 1.45;
}}
.why-label {{ color: {color}; font-weight: 800; margin-right: 6px; }}
.real {{ font-size: 17px; color: #8a9bb0; font-style: italic; }}
.real-label {{ color: #aab8cc; font-style: normal; font-weight: 700; margin-right: 4px; }}
.footer {{ display: flex; justify-content: space-between; align-items: center; margin-top: auto; padding-top: 16px; border-top: 1px solid #2a3548; font-size: 16px; color: #6a7a90; }}
.brand {{ color: {color}; font-weight: 700; }}
</style></head><body>
  <div class="head">
    <div class="num">{num}</div>
    <div class="emoji">{emoji}</div>
    <div class="title-block">
      <div class="name">{name}</div>
      <div class="subtitle">{subtitle}</div>
    </div>
  </div>
  <div class="metaphor">{metaphor}</div>
  <div class="steps">{steps_html}</div>
  <div class="why"><span class="why-label">왜?</span>{why}</div>
  <div class="real"><span class="real-label">대표:</span>{real}</div>
  <div class="footer">
    <span>AI 진화 10가족 · 학습 카드</span>
    <span class="brand">{num} · 2026-2030</span>
  </div>
</body></html>"""

STEP_TPL = '<div class="step {state}"><div class="dot"></div><div class="step-text">{text}</div><div class="step-year">{year}</div></div>'


def render_html(fam):
    steps_html = "".join(
        STEP_TPL.format(state=state, text=text, year=year) for text, year, state in fam["steps"]
    )
    return CARD_TPL.format(steps_html=steps_html, **fam)


async def main():
    from playwright.async_api import async_playwright
    png_files = []
    pdf_files = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for fam in FAMILIES:
            html_path = OUT_DIR / f"family-{fam['num']}-{fam['name']}.html"
            png_path  = OUT_DIR / f"family-{fam['num']}-{fam['name']}.png"
            pdf_path  = OUT_DIR / f"family-{fam['num']}-{fam['name']}.pdf"
            html_path.write_text(render_html(fam), encoding="utf-8")
            page = await browser.new_page(viewport={"width": 1080, "height": 1080})
            await page.goto(html_path.resolve().as_uri())
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path=str(png_path), full_page=False,
                                  clip={"x": 0, "y": 0, "width": 1080, "height": 1080})
            await page.pdf(path=str(pdf_path), width="1080px", height="1080px",
                           print_background=True, margin={"top":"0","right":"0","bottom":"0","left":"0"})
            await page.close()
            png_files.append(png_path)
            pdf_files.append(pdf_path)
            print(f"  OK -> {png_path.name} + {pdf_path.name}")
        await browser.close()

    # Merge all PDFs into one combined file
    try:
        from pypdf import PdfWriter
        writer = PdfWriter()
        for pdf in pdf_files:
            writer.append(str(pdf))
        merged = OUT_DIR / "ai-evolution-10families-all.pdf"
        with open(merged, "wb") as f:
            writer.write(f)
        print(f"\n  Merged -> {merged.name}")
    except ImportError:
        print("\n  (pypdf not installed — skipping merge. Run: pip install pypdf)")

    print(f"\nDone. {len(FAMILIES)} cards generated in {OUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
