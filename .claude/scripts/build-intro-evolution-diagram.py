"""들어가며 다이어그램 v4 — 풍부한 데이터 + 미관 강화.
viewport 1300×910 (A4 landscape inside 비율 0.70).
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "docs" / "screens" / "arch-kor"
OUT.mkdir(parents=True, exist_ok=True)

HTML = """<!DOCTYPE html><html><head><meta charset='utf-8'><style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Malgun Gothic','맑은 고딕','Pretendard',sans-serif}
body{width:1300px;height:910px;padding:16px 22px;overflow:hidden;
     background:linear-gradient(135deg,#FFF5F8 0%,#F0F4FF 50%,#FFFAF0 100%);
     display:grid;grid-template-rows:auto 2fr 1fr;gap:14px}

/* Title */
.head{text-align:center;flex-shrink:0}
.title{font-size:42px;font-weight:900;letter-spacing:-0.5px;
       background:linear-gradient(135deg,#B91C1C 0%,#3B1B5C 40%,#1F3864 70%,#2563EB 100%);
       -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:4px}
.subtitle{font-size:16px;color:#555;font-weight:500}
.subtitle b{color:#B91C1C;font-weight:800}

/* Main grid — 4 steps */
.flow{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;flex:1;min-height:0;align-items:stretch}

.step{background:white;border-radius:18px;padding:14px 12px;box-shadow:0 8px 24px rgba(31,56,100,0.10);
      display:flex;flex-direction:column;justify-content:space-between;
      border:3px solid;position:relative}
.step::after{content:'';position:absolute;top:0;left:0;right:0;height:5px}
.s1{border-color:#FC8181;background:linear-gradient(170deg,#FFFFFF 0%,#FFE4E4 100%)}
.s1::after{background:linear-gradient(90deg,#FC8181,#F87171)}
.s2{border-color:#F6AD55;background:linear-gradient(170deg,#FFFFFF 0%,#FED7AA 100%)}
.s2::after{background:linear-gradient(90deg,#F6AD55,#FB923C)}
.s3{border-color:#68D391;background:linear-gradient(170deg,#FFFFFF 0%,#BBF7D0 100%)}
.s3::after{background:linear-gradient(90deg,#68D391,#4ADE80)}
.s4{border-color:#3F6FB5;background:linear-gradient(170deg,#FFFFFF 0%,#BFDBFE 100%);
    box-shadow:0 16px 40px rgba(63,111,181,0.40);transform:scale(1.04)}
.s4::after{background:linear-gradient(90deg,#3F6FB5,#FFD700,#3F6FB5)}
.s4::before{content:' 우리 ';position:absolute;top:-14px;left:50%;transform:translateX(-50%);
            background:linear-gradient(135deg,#FFD700,#FFA500);padding:5px 18px;border-radius:14px;
            font-weight:900;color:#7C2D12;font-size:14px;white-space:nowrap;letter-spacing:1px;
            box-shadow:0 4px 14px rgba(255,165,0,0.50);z-index:2;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{box-shadow:0 4px 14px rgba(255,165,0,0.5)}50%{box-shadow:0 4px 24px rgba(255,165,0,0.8)}}

.s-top{display:flex;align-items:center;gap:8px;margin-bottom:6px;margin-top:4px}
.s-icon{font-size:38px;filter:drop-shadow(0 4px 6px rgba(0,0,0,0.12))}
.s-meta{flex:1}
.s-num{font-size:10px;color:#888;font-weight:800;letter-spacing:1.5px}
.s-title{font-size:19px;font-weight:900;color:#1F3864;line-height:1.1}
.s-eng{font-size:11px;color:#888;font-style:italic;margin-bottom:8px;border-bottom:1px dashed #ccc;padding-bottom:6px}
.s-desc{font-size:13px;color:#222;line-height:1.45;margin-bottom:7px;font-weight:500}

/* SVG illustration in middle */
.s-svg{flex-grow:1;display:flex;align-items:center;justify-content:center;padding:4px 0;margin-bottom:4px}
.s-svg svg{width:100%;max-width:180px;max-height:130px}

.s-block{background:rgba(255,255,255,0.7);padding:6px 8px;border-radius:7px;margin-bottom:5px;font-size:11px;line-height:1.4}
.s-block b{color:#B91C1C;display:block;font-size:9.5px;letter-spacing:0.5px;margin-bottom:1px;font-weight:800}
.s-block.ex b{color:#1F3864}
.s-block.pro b{color:#0F766E}
.s-block.con b{color:#B45309}

/* Bottom: Our workers */
.foot{background:linear-gradient(135deg,#1F3864 0%,#3F6FB5 60%,#5B7BB8 100%);border-radius:16px;
      padding:18px 22px;color:white;box-shadow:0 12px 32px rgba(31,56,100,0.40);position:relative;overflow:hidden;
      display:flex;flex-direction:column}
.foot::after{content:'';position:absolute;top:-50%;right:-10%;width:400px;height:400px;
             background:radial-gradient(circle,rgba(255,215,0,0.22) 0%,transparent 60%);pointer-events:none}
.foot-head{font-size:22px;font-weight:900;margin-bottom:14px;text-align:center;position:relative;z-index:1}
.foot-head b{color:#FFD700}
.foot-head .arrow{color:#FFD700;margin:0 8px}
.foot-sub{font-size:13px;text-align:center;margin-bottom:14px;opacity:0.92;font-style:italic;position:relative;z-index:1}
.workers{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;position:relative;z-index:1;flex:1}
.wk{background:rgba(255,255,255,0.13);padding:14px 14px;border-radius:12px;display:flex;flex-direction:column;gap:7px;
    border:1px solid rgba(255,255,255,0.18);backdrop-filter:blur(8px)}
.wk-row{display:flex;align-items:center;gap:10px;margin-bottom:4px}
.wk-icon{font-size:34px;filter:drop-shadow(0 3px 6px rgba(0,0,0,0.25))}
.wk-meta{flex:1;min-width:0}
.wk-name{font-size:15px;font-weight:900;color:#FFD700;margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.wk-eng{font-size:10px;opacity:0.7;font-style:italic}
.wk-role{font-size:12px;line-height:1.45;opacity:0.95}
.wk-tags{display:flex;gap:5px;flex-wrap:wrap;margin-top:5px}
.wk-tag{font-size:9.5px;padding:2px 7px;background:rgba(255,215,0,0.18);border-radius:8px;color:#FFE699;font-weight:700;border:1px solid rgba(255,215,0,0.3)}
</style></head><body>

<div class='head'>
  <div class='title'>AI 4단계 진화 — 우리는 어디 있나</div>
  <div class='subtitle'>Generative -> Agentic -> AI Agent -> <b>Multi-Agent (가장 진화된 형태 - ★우리 위치)</b></div>
</div>

<div class='flow'>
  <!-- STEP 1 -->
  <div class='step s1'>
    <div class='s-top'>
      <div class='s-icon'>✍</div>
      <div class='s-meta'>
        <div class='s-num'>STEP 1</div>
        <div class='s-title'>Generative</div>
      </div>
    </div>
    <div class='s-eng'>생성 AI - 한 번 답 하고 끝</div>
    <div class='s-desc'>글-그림-코드를 한 번에 만들어 주는 AI. 사람이 매번 시켜야 움직임.</div>
    <div class='s-svg'><svg viewBox='0 0 130 80'><defs><linearGradient id='sv1' x1='0' x2='1'><stop offset='0' stop-color='#FECACA'/><stop offset='1' stop-color='#F87171'/></linearGradient></defs><circle cx='25' cy='40' r='15' fill='#FCA5A5'/><circle cx='25' cy='32' r='6' fill='#7C2D12'/><rect x='18' y='42' width='14' height='10' rx='2' fill='#7C2D12'/><line x1='42' y1='40' x2='80' y2='40' stroke='url(#sv1)' stroke-width='4' marker-end='url(#ar1)'/><defs><marker id='ar1' markerWidth='10' markerHeight='10' refX='8' refY='5' orient='auto'><polygon points='0,0 10,5 0,10' fill='#F87171'/></marker></defs><rect x='85' y='25' width='40' height='30' rx='3' fill='white' stroke='#F87171' stroke-width='2'/><line x1='90' y1='32' x2='120' y2='32' stroke='#888' stroke-width='1.5'/><line x1='90' y1='38' x2='115' y2='38' stroke='#888' stroke-width='1.5'/><line x1='90' y1='44' x2='118' y2='44' stroke='#888' stroke-width='1.5'/><line x1='90' y1='50' x2='110' y2='50' stroke='#888' stroke-width='1.5'/></svg></div>
    <div class='s-block ex'><b>EXAMPLES</b>ChatGPT - DALL-E - Copilot</div>
  </div>

  <!-- STEP 2 -->
  <div class='step s2'>
    <div class='s-top'>
      <div class='s-icon'></div>
      <div class='s-meta'>
        <div class='s-num'>STEP 2</div>
        <div class='s-title'>Agentic</div>
      </div>
    </div>
    <div class='s-eng'>스스로 계획 - 신입 매니저</div>
    <div class='s-desc'>목표 주면 단계를 직접 짜고 도구를 골라 호출. 사람 검토 가능.</div>
    <div class='s-svg'><svg viewBox='0 0 130 80'><circle cx='25' cy='40' r='12' fill='#FED7AA' stroke='#F59E0B' stroke-width='2'/><text x='25' y='44' text-anchor='middle' font-size='14' font-weight='900' fill='#7C2D12'>1</text><line x1='37' y1='40' x2='55' y2='22' stroke='#F59E0B' stroke-width='2'/><line x1='37' y1='40' x2='55' y2='58' stroke='#F59E0B' stroke-width='2'/><circle cx='65' cy='22' r='10' fill='#FFE4B5' stroke='#F59E0B' stroke-width='2'/><text x='65' y='26' text-anchor='middle' font-size='11' font-weight='800' fill='#7C2D12'>2a</text><circle cx='65' cy='58' r='10' fill='#FFE4B5' stroke='#F59E0B' stroke-width='2'/><text x='65' y='62' text-anchor='middle' font-size='11' font-weight='800' fill='#7C2D12'>2b</text><line x1='75' y1='22' x2='95' y2='40' stroke='#F59E0B' stroke-width='2'/><line x1='75' y1='58' x2='95' y2='40' stroke='#F59E0B' stroke-width='2'/><circle cx='105' cy='40' r='12' fill='#FED7AA' stroke='#F59E0B' stroke-width='2'/><text x='105' y='44' text-anchor='middle' font-size='12' font-weight='900' fill='#7C2D12'>✓</text></svg></div>
    <div class='s-block ex'><b>EXAMPLES</b>AutoGPT - ReAct - CoT</div>
  </div>

  <!-- STEP 3 -->
  <div class='step s3'>
    <div class='s-top'>
      <div class='s-icon'></div>
      <div class='s-meta'>
        <div class='s-num'>STEP 3</div>
        <div class='s-title'>AI Agent</div>
      </div>
    </div>
    <div class='s-eng'>API 직접 - 경력 매니저</div>
    <div class='s-desc'>외부 API 호출 + 결과 자가 평가. 사람 손 없이 24/7 운영.</div>
    <div class='s-svg'><svg viewBox='0 0 130 80'><circle cx='65' cy='40' r='22' fill='#BBF7D0' stroke='#22C55E' stroke-width='3'/><text x='65' y='45' text-anchor='middle' font-size='20'></text><circle cx='65' cy='40' r='30' fill='none' stroke='#22C55E' stroke-width='2' stroke-dasharray='4 3'/><circle cx='35' cy='40' r='5' fill='#22C55E'/><circle cx='95' cy='40' r='5' fill='#22C55E'/><circle cx='65' cy='10' r='5' fill='#22C55E'/><circle cx='65' cy='70' r='5' fill='#22C55E'/><text x='15' y='44' font-size='9' fill='#15803D' font-weight='700'>API</text><text x='102' y='44' font-size='9' fill='#15803D' font-weight='700'>API</text><text x='55' y='8' font-size='9' fill='#15803D' font-weight='700'>EVAL</text><text x='55' y='80' font-size='9' fill='#15803D' font-weight='700'>LOOP</text></svg></div>
    <div class='s-block ex'><b>EXAMPLES</b>Devin - MCP - 자가 복구</div>
  </div>

  <!-- STEP 4 -->
  <div class='step s4'>
    <div class='s-top'>
      <div class='s-icon'></div>
      <div class='s-meta'>
        <div class='s-num'>STEP 4</div>
        <div class='s-title'>Multi-Agent</div>
      </div>
    </div>
    <div class='s-eng'>회사형 협업 - 진화 최고</div>
    <div class='s-desc'>여러 AI 가 역할 분담-인수인계. 사람 회사처럼 자율 운영.</div>
    <div class='s-svg'><svg viewBox='0 0 130 80'><circle cx='25' cy='25' r='13' fill='#BFDBFE' stroke='#3F6FB5' stroke-width='2.5'/><text x='25' y='29' text-anchor='middle' font-size='14'></text><circle cx='105' cy='25' r='13' fill='#BFDBFE' stroke='#3F6FB5' stroke-width='2.5'/><text x='105' y='29' text-anchor='middle' font-size='14'>[FAST]</text><circle cx='25' cy='60' r='13' fill='#BFDBFE' stroke='#3F6FB5' stroke-width='2.5'/><text x='25' y='64' text-anchor='middle' font-size='14'></text><circle cx='105' cy='60' r='13' fill='#BFDBFE' stroke='#3F6FB5' stroke-width='2.5'/><text x='105' y='64' text-anchor='middle' font-size='14'>✓</text><line x1='38' y1='25' x2='92' y2='25' stroke='#FFD700' stroke-width='2.5'/><line x1='38' y1='60' x2='92' y2='60' stroke='#FFD700' stroke-width='2.5'/><line x1='25' y1='38' x2='25' y2='47' stroke='#FFD700' stroke-width='2.5'/><line x1='105' y1='38' x2='105' y2='47' stroke='#FFD700' stroke-width='2.5'/><line x1='38' y1='35' x2='92' y2='50' stroke='#FFD700' stroke-width='2' stroke-dasharray='3 2'/><line x1='92' y1='35' x2='38' y2='50' stroke='#FFD700' stroke-width='2' stroke-dasharray='3 2'/><rect x='55' y='38' width='20' height='10' rx='3' fill='#FFD700'/><text x='65' y='46' text-anchor='middle' font-size='8' font-weight='900' fill='#7C2D12'>★우리</text></svg></div>
    <div class='s-block ex'><b style='color:#B91C1C'>★ orchestration_v1 (우리)</b>4 워커 협업 구조</div>
  </div>
</div>

<div class='foot'>
  <div class='foot-head'>[TGT] 우리 <b>orchestration_v1</b> = STEP 4 Multi-Agent <span class='arrow'>▸</span> 4 워커 역할 분담</div>
  <div class='foot-sub'>Claude 설계 -> Codex 구현 -> Gemini 검토 -> Haiku 빠른 검증 (자동 인수인계)</div>
  <div class='workers'>
    <div class='wk'>
      <div class='wk-row'>
        <div class='wk-icon'></div>
        <div class='wk-meta'><div class='wk-name'>Claude Opus 4.7</div><div class='wk-eng'>설계자 - Designer</div></div>
      </div>
      <div class='wk-role'>복잡 추론 + 시스템 설계. Extended Thinking 1M ctx 로 큰 그림 파악.</div>
      <div class='wk-tags'><span class='wk-tag'>설계</span><span class='wk-tag'>추론</span><span class='wk-tag'>1M ctx</span></div>
    </div>
    <div class='wk'>
      <div class='wk-row'>
        <div class='wk-icon'>[FAST]</div>
        <div class='wk-meta'><div class='wk-name'>Codex CLI</div><div class='wk-eng'>구현자 - Builder</div></div>
      </div>
      <div class='wk-role'>코드 500줄+ 대용량 구현. ×4 병렬 워커 동시 실행 가능.</div>
      <div class='wk-tags'><span class='wk-tag'>구현</span><span class='wk-tag'>×4 병렬</span><span class='wk-tag'>대용량</span></div>
    </div>
    <div class='wk'>
      <div class='wk-row'>
        <div class='wk-icon'></div>
        <div class='wk-meta'><div class='wk-name'>Gemini Flash</div><div class='wk-eng'>검토자 - Reviewer</div></div>
      </div>
      <div class='wk-role'>장문-멀티모달 검토. 500k+ 토큰 docx/PDF/이미지 분석.</div>
      <div class='wk-tags'><span class='wk-tag'>검토</span><span class='wk-tag'>장문</span><span class='wk-tag'>멀티모달</span></div>
    </div>
    <div class='wk'>
      <div class='wk-row'>
        <div class='wk-icon'>✓</div>
        <div class='wk-meta'><div class='wk-name'>Haiku 4.5</div><div class='wk-eng'>검증자 - Verifier</div></div>
      </div>
      <div class='wk-role'>빠른 검증 + 저비용. prompt cache 90% 절감으로 대량 처리.</div>
      <div class='wk-tags'><span class='wk-tag'>검증</span><span class='wk-tag'>저비용</span><span class='wk-tag'>cache 90%↓</span></div>
    </div>
  </div>
</div>

</body></html>"""


async def main():
    out = OUT / "00-ai-evolution.png"
    async with async_playwright() as p:
        b = await p.chromium.launch()
        page = await b.new_page(viewport={"width": 1300, "height": 910})
        await page.set_content(HTML)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=str(out), full_page=False,
                              clip={"x": 0, "y": 0, "width": 1300, "height": 910})
        await b.close()
    print(f"[OK] {out}")


if __name__ == "__main__":
    asyncio.run(main())
