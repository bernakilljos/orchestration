#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render orch-promo.jpg + ssj-summary.jpg in 타겟.jpg infographic style."""
import base64, pathlib
from playwright.sync_api import sync_playwright

DIR = pathlib.Path(__file__).parent
char_b64 = base64.b64encode((DIR / "내캐릭터.png").read_bytes()).decode()
# 서재+촛불+맥북 캐릭터 (있으면 사용)
_laptop = DIR / "character-laptop.png"
laptop_b64 = base64.b64encode(_laptop.read_bytes()).decode() if _laptop.exists() and _laptop.stat().st_size > 10000 else char_b64
photo_b64 = base64.b64encode((DIR / "\ub0b4\uc0ac\uc9c4.jpg").read_bytes()).decode()
# 멀티AI 오케스트레이션 캐릭터 (orch-promo 전용)
_orch = DIR / "orch-character.png"
orch_b64 = base64.b64encode(_orch.read_bytes()).decode() if _orch.exists() and _orch.stat().st_size > 10000 else laptop_b64

# --- SVG icons ---
I = {
 'bulb':'<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#c4915a" stroke-width="1.5"><path d="M9 21h6M12 3a6 6 0 0 0-4 10.5V17h8v-3.5A6 6 0 0 0 12 3z"/></svg>',
 'rocket':'<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#c4915a" stroke-width="1.5"><path d="M12 2C6 8 6 16 12 22c6-6 6-14 0-20zM5 16l-2 4 4-2M19 16l2 4-4-2"/></svg>',
 'star':'<svg viewBox="0 0 24 24" width="15" height="15" fill="#e8c36a" stroke="none"><path d="M12 2l3 6.5 7 1-5 5 1.2 7L12 18l-6.2 3.5L7 14.5l-5-5 7-1z"/></svg>',
 'heart':'<svg viewBox="0 0 24 24" width="14" height="14" fill="#c4915a" stroke="none"><path d="M12 21C8 17 2 13 2 8a5 5 0 0 1 10 0 5 5 0 0 1 10 0c0 5-6 9-10 13z"/></svg>',
 'fire':'<svg viewBox="0 0 24 24" width="15" height="15" fill="#e07a2f" stroke="none"><path d="M12 23c-4 0-7-3-7-7 0-3 2-5 4-7 0 2 1 3 2 3 0-4 3-8 5-10 0 3 1 5 2 6 2 2 3 4 3 6 0 5-4 9-9 9z"/></svg>',
 'water':'<svg viewBox="0 0 24 24" width="15" height="15" fill="#5a9ec4" stroke="none"><path d="M12 2C8 8 5 12 5 16a7 7 0 0 0 14 0c0-4-3-8-7-14z"/></svg>',
 'gear':'<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#8b7355" stroke-width="1.5"><path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
 'check':'<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="#6b8e5a" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>',
 'code':'<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#6b7b8e" stroke-width="1.5"><path d="M16 18l6-6-6-6M8 6l-6 6 6 6"/></svg>',
 'cpu':'<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#7a6b8e" stroke-width="1.5"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/></svg>',
 'plant':'<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#6b8e5a" stroke-width="1.5"><path d="M12 22V8M8 12c-3 0-5-2-5-5 3 0 5 2 5 5M16 10c3 0 5-2 5-5-3 0-5 2-5 5"/></svg>',
 'candle':'<svg viewBox="0 0 24 24" width="14" height="14"><rect x="10" y="12" width="4" height="9" rx="1" fill="#c4915a"/><ellipse cx="12" cy="9" rx="3" ry="4" fill="#e8a836" opacity=".7"/><ellipse cx="12" cy="8" rx="1.5" ry="2.5" fill="#f0c040"/></svg>',
 'person':'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#8b7355" stroke-width="1.5"><circle cx="12" cy="7" r="4"/><path d="M5.5 21c0-3.5 3-6.5 6.5-6.5s6.5 3 6.5 6.5"/></svg>',
 'shield':'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#6b8e5a" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
 'book':'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#8b7355" stroke-width="1.5"><path d="M4 19V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v14H6a2 2 0 0 0 0 4h14"/></svg>',
}

COMMON_CSS = """
/* === DESIGN TOKENS === */
:root{
  --font-title:'Gaegu',cursive;
  --font-body:'Noto Sans KR',sans-serif;
  --color-bg:#f5efe6;
  --color-text:#3a3226;
  --color-text-sub:#4a3f33;
  --color-text-muted:#8a7a68;
  --color-accent:#8b4513;
  --color-accent-warm:#c4915a;
  --color-border:#c4b49a;
  --color-border-light:#d4c4a8;
  --color-card:rgba(255,255,255,.6);
  --color-card-dim:rgba(255,255,255,.45);
  --color-tag-bg:rgba(196,145,90,.12);
  --color-tag-border:rgba(196,145,90,.3);
  --color-tag-text:#7a5a3a;
  --gap-section:3px;
  --gap-card:3px;
  --gap-tag:3px;
  --pad-card:8px 10px;
  --pad-btm:4px 6px;
  --radius-card:5px;
  --radius-tag:8px;
  --font-h3:13px;
  --font-body-size:10px;
  --font-small:9px;
  --font-tag:9px;
  --line-height:1.55;
  --shadow-card:1px 2px 6px rgba(0,0,0,.05)
}
/* === BASE === */
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@300;400;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
body{font-family:var(--font-body);overflow:hidden;color:var(--color-text)}
/* === CARD SYSTEM === */
.card{background:var(--color-card);border:1.5px solid var(--color-border);border-radius:var(--radius-card);padding:var(--pad-card);box-shadow:var(--shadow-card)}
.card h3{font-family:var(--font-title);font-size:var(--font-h3);font-weight:700;color:var(--color-accent);margin-bottom:4px;border-bottom:1px solid rgba(180,150,120,.25);padding-bottom:2px;display:flex;align-items:center;gap:var(--gap-tag)}
.card li,.card p{font-size:var(--font-body-size);line-height:var(--line-height);color:var(--color-text-sub)}
.card ul{list-style:none;padding:0}
/* === TAG SYSTEM === */
.tags{display:flex;flex-wrap:wrap;gap:var(--gap-tag)}
.tag{background:var(--color-tag-bg);border:1px solid var(--color-tag-border);color:var(--color-tag-text);font-size:var(--font-tag);padding:1px 5px;border-radius:var(--radius-tag);font-family:var(--font-title);font-weight:700}
"""

# ===================== ORCH-PROMO =====================
def build_orch_promo():
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{COMMON_CSS}
body{{width:850px;height:1100px;background:#f5efe6;
  background-image:radial-gradient(ellipse at 15% 85%,rgba(210,180,140,.1) 0%,transparent 50%),
  radial-gradient(ellipse at 85% 15%,rgba(180,160,130,.06) 0%,transparent 40%);
  padding:16px 18px;display:flex;flex-direction:column;justify-content:space-between}}
.header{{display:flex;justify-content:space-between;align-items:flex-start}}
.header-left h1{{font-family:'Gaegu',cursive;font-size:28px;font-weight:700;color:#2c2418;line-height:1.25}}
.header-left .sub{{font-size:11px;color:#7a6b5a;margin-top:3px;display:flex;align-items:center;gap:4px}}
.header-right{{display:flex;gap:6px;max-width:360px}}
.mid{{display:grid;grid-template-columns:230px 1fr 230px;gap:8px;flex:1;margin:8px 0}}
.mid-left,.mid-right{{display:flex;flex-direction:column;gap:6px}}
.center{{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px}}
.photo{{width:200px;height:240px;border-radius:10px;object-fit:cover;border:2.5px solid #c4b49a;box-shadow:3px 3px 10px rgba(0,0,0,.1)}}
.name-area{{text-align:center}}
.name-area .nm{{font-family:'Gaegu',cursive;font-size:20px;font-weight:700;color:#2c2418}}
.name-area .inf{{font-size:9px;color:#8a7a68;margin-top:1px}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;width:100%}}
.stat{{background:rgba(255,255,255,.5);border:1px solid #d4c4a8;border-radius:5px;padding:4px;text-align:center}}
.stat .n{{font-family:'Gaegu',cursive;font-size:18px;font-weight:700;color:#8b4513}}
.stat .l{{font-size:8px;color:#7a6b5a}}
.bottom{{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px}}
.btm-card{{background:rgba(255,255,255,.45);border:1.5px solid #d4c4a8;border-radius:5px;padding:7px 9px}}
.btm-card h4{{font-family:'Gaegu',cursive;font-size:11px;color:#8b4513;margin-bottom:3px;display:flex;align-items:center;gap:3px}}
.btm-card li{{font-size:9px;line-height:1.5;color:#5a4f42}}
.btm-card ul{{list-style:none;padding:0}}
</style></head><body>

<div class="header">
  <div class="header-left">
    <h1>AI\ub97c \uc124\uacc4\ud558\uace0,<br>\ucf54\ub4dc\ub97c \ub9cc\ub4e4\uba70,<br>\ud568\uaed8 \uc131\uc7a5\ud558\ub294 \uac1c\ubc1c\uc790</h1>
    <div class="sub">{I['cpu']} Claude + Codex + Gemini = \uba40\ud2f0AI \uc624\ucf00\uc2a4\ud2b8\ub808\uc774\uc158</div>
  </div>
  <div class="header-right">
    <div class="card" style="width:160px">
      <h3>{I['heart']} \ud589\ub3d9 \uc6d0\uce59</h3>
      <ul>
        <li>&middot; \ubcf5\uc7a1\ud55c \uac83\uc744 \ub2e8\uc21c\ud558\uac8c \uad6c\uc870\ud654</li>
        <li>&middot; \uc790\ub3d9\ud654\ud560 \uc218 \uc788\uc73c\uba74 \uc790\ub3d9\ud654</li>
        <li>&middot; \ub370\uc774\ud130\ub85c \uac80\uc99d, \uacb0\uacfc\ub85c \uc99d\uba85</li>
      </ul>
    </div>
    <div class="card" style="width:185px">
      <h3>{I['star']} \ud575\uc2ec \ud0a4\uc6cc\ub4dc</h3>
      <div class="tags">
        <span class="tag">Multi-AI</span><span class="tag">Python</span><span class="tag">Zero-touch</span>
        <span class="tag">\uc790\ub3d9\ud654</span><span class="tag">MCP</span><span class="tag">\ud480\uc2a4\ud0dd</span>
        <span class="tag">\uba58\ud1a0\ub9c1</span><span class="tag">RAG</span><span class="tag">\uc2dc\uc2a4\ud15c\uc124\uacc4</span>
        <span class="tag">\uc624\ucf00\uc2a4\ud2b8\ub808\uc774\uc158</span><span class="tag">\ud488\uc9c8\uac80\uc99d</span>
      </div>
    </div>
  </div>
</div>

<div class="mid">
  <div class="mid-left">
    <div class="card" style="flex:1">
      <h3>{I['bulb']} \ud575\uc2ec \uc5ed\ub7c9</h3>
      <ul>
        <li>&middot; <b>\uba40\ud2f0AI \uc624\ucf00\uc2a4\ud2b8\ub808\uc774\uc158</b><br><span style="font-size:9px;color:#8a7a68">Claude \uc124\uacc4 \u2192 Codex \uad6c\ud604 \u2192 Gemini \uac80\uc99d. \uac01 AI\uc758 \uac15\uc810\uc744 \uadf9\ub300\ud654\ud558\ub294 \ub77c\uc6b0\ud305.</span></li>
        <li>&middot; <b>Zero-touch \uc790\ub3d9\ud654</b><br><span style="font-size:9px;color:#8a7a68">\uc0ac\uc6a9\uc790 \uc561\uc158 0\uac1c. SessionStart\ubd80\ud130 MCP \uc5f0\uacb0, \uc6cc\ucee4 \uad00\ub9ac\uae4c\uc9c0 \uc644\uc804 \uc790\ub3d9.</span></li>
        <li>&middot; <b>\ud480\uc2a4\ud0dd \uc2dc\uc2a4\ud15c \uc124\uacc4</b><br><span style="font-size:9px;color:#8a7a68">\ud504\ub860\ud2b8(HTML/CSS) \u00b7 \ubc31\uc5d4\ub4dc(Python) \u00b7 \uc778\ud504\ub77c(\uc2a4\ud06c\ub9bd\ud2b8) \u00b7 AI(\ud504\ub86c\ud504\ud2b8).</span></li>
        <li>&middot; <b>49\uac1c \uc0b0\uc5c5\ubcc4 \uacf5\ud1b5 \ub808\ud37c\ub7f0\uc2a4</b><br><span style="font-size:9px;color:#8a7a68">\uae08\uc735\u00b7\uc758\ub8cc\u00b7\uad50\uc721\u00b7\ubcf4\uc548\u00b7IoT \ub4f1 \ubaa8\ub4e0 \uc0b0\uc5c5\uc758 \uacf5\ud1b5 \ub3c4\uad6c \uc815\ub9ac.</span></li>
        <li>&middot; <b>\ud488\uc9c8 \uc790\ub3d9 \uac80\uc99d</b><br><span style="font-size:9px;color:#8a7a68">\ube4c\ub4dc\u2192\uac80\uc99d\u2192\ubcf4\uace0 \uc790\ub3d9 \ud30c\uc774\ud504\ub77c\uc778. \uc0ac\ub78c \ud655\uc778 \uc5c6\uc774\ub3c4 \ud488\uc9c8 \ubcf4\uc7a5.</span></li>
        <li>&middot; <b>\uc2e4\ud589 \uc911\uc2ec (Bias for Action)</b><br><span style="font-size:9px;color:#8a7a68">\uacc4\ud68d\uc5d0 \uba38\ubb34\ub974\uc9c0 \uc54a\uace0 \uc989\uc2dc \uad6c\ud604. \uc791\uc740 \ubcc0\ud654\ub97c \ube60\ub974\uac8c \ubc18\ubcf5.</span></li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['rocket']} \uc77c\uc744 \ub300\ud558\ub294 \ubc29\uc2dd</h3>
      <p style="font-size:10px;color:#8b4513;font-family:'Gaegu',cursive;margin-bottom:3px">\ud0d0\uad6c &#8594; \ubd84\uc11d &#8594; \uc124\uacc4 &#8594; \uc2e4\ud589</p>
      <ul>
        <li>&middot; <b>1. \ud0d0\uad6c</b> \u2014 \ubb38\uc81c\uc758 \ubcf8\uc9c8\uc744 \ud30c\uc545</li>
        <li>&middot; <b>2. \ubd84\uc11d</b> \u2014 \ub370\uc774\ud130\ub85c \uae4a\uc774 \uac80\uc99d</li>
        <li>&middot; <b>3. \uc124\uacc4</b> \u2014 AI\uc640 \ud568\uaed8 \ucd5c\uc801 \uad6c\uc870</li>
        <li>&middot; <b>4. \uc2e4\ud589</b> \u2014 \uc790\ub3d9\ud654\ub85c \uacb0\uacfc\ub97c \ub9cc\ub4e0\ub2e4</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['shield']} \uc790\ub3d9\ud654 \ucca0\ud559</h3>
      <ul>
        <li>&middot; \uc0ac\ub78c\uc740 \ud310\ub2e8\ub9cc, \ubc18\ubcf5\uc740 \uae30\uacc4\uc5d0\uac8c</li>
        <li>&middot; \ud55c \ubc88\ub9cc \ud558\uba74 \ub05d\ub098\ub294 \uc2dc\uc2a4\ud15c</li>
        <li>&middot; Zero-touch = \uc0ac\uc6a9\uc790 \uc561\uc158 0</li>
        <li>&middot; \uac80\uc99d \uc5c6\uc774 \uc644\ub8cc \ubcf4\uace0 \uae08\uc9c0</li>
      </ul>
    </div>
  </div>

  <div class="center">
    <div style="position:relative">
      <img class="photo" src="data:image/png;base64,{orch_b64}" />
      <div style="position:absolute;top:6px;left:8px;background:rgba(255,255,255,.8);border-radius:4px;padding:2px 6px;font-size:8px;color:#8b4513;font-family:'Gaegu',cursive">Multi-AI Orchestration</div>
    </div>
    <div class="name-area">
      <div class="nm">orchestration_v1</div>
      <div style="font-size:11px;color:#8b4513;font-family:serif">Multi-AI Orchestration Kit</div>
      <div class="inf">Claude + Codex + Gemini \u00b7 \uc124\uacc4\u2192\uad6c\ud604\u2192\uac80\uc99d \uc790\ub3d9\ud654</div>
    </div>
    <div class="stats">
      <div class="stat"><div class="n">31</div><div class="l">\ud50c\ub7ec\uadf8\uc778</div></div>
      <div class="stat"><div class="n">49</div><div class="l">\ub808\ud37c\ub7f0\uc2a4</div></div>
      <div class="stat"><div class="n">165</div><div class="l">\ucee4\ub9e8\ub4dc</div></div>
      <div class="stat"><div class="n">87</div><div class="l">\uc2a4\ud0ac</div></div>
      <div class="stat"><div class="n">92</div><div class="l">\uc2a4\ud06c\ub9bd\ud2b8</div></div>
      <div class="stat"><div class="n">27</div><div class="l">\ud6c5</div></div>
    </div>
  </div>

  <div class="mid-right">
    <div class="card">
      <h3>{I['star']} \ud504\ub85c\uc81d\ud2b8 \uc8fc\uc694 \uc131\uacfc</h3>
      <ul>
        <li>&middot; \uc138\uacc4 \ucd5c\ucd08 \uba40\ud2f0AI \ub3d9\uc2dc \uc624\ucf00\uc2a4\ud2b8\ub808\uc774\uc158</li>
        <li>&middot; 23,203\uc904 \uacf5\ud1b5 \ub3c4\uad6c \ucf54\ub4dc</li>
        <li>&middot; 92\uac1c \uc790\ub3d9\ud654 \uc2a4\ud06c\ub9bd\ud2b8</li>
        <li>&middot; 27\uac1c \ud6c5 (Pre/Post ToolUse)</li>
        <li>&middot; SQLite \uae30\ubc18 \ud1b5\ud569 \uc0c1\ud0dc \uad00\ub9ac</li>
        <li>&middot; 11\uac1c \ud488\uc9c8 \uaddc\uce59 \uc790\ub3d9 \uac15\uc81c</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['heart']} \ud575\uc2ec \uac00\uce58</h3>
      <ul>
        <li>&middot; \uc790\ub3d9\ud654 \uc6b0\uc120 \u2014 \ubc18\ubcf5\uc740 \uae30\uacc4\uc5d0\uac8c</li>
        <li>&middot; \ud488\uc9c8 = \uc2e0\ub8b0 \u2014 \uac80\uc99d \uc5c6\uc774 \uc644\ub8cc \ubcf4\uace0 X</li>
        <li>&middot; \uacf5\uc720\uc640 \uc131\uc7a5 \u2014 \ud0b7\uc740 \ubaa8\ub450\ub97c \uc704\ud55c \uac83</li>
        <li>&middot; \ub2e8\uc21c\ud568\uc758 \ud798 \u2014 \ubcf5\uc7a1\ud568\uc740 \uc801</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['gear']} \uae30\uc220 \uc544\ud0a4\ud14d\ucc98</h3>
      <ul>
        <li>&middot; Claude Opus 4.6 (\uc124\uacc4\u00b7\ucd94\ub860)</li>
        <li>&middot; Codex \u00d74 \ubcd1\ub82c (\uad6c\ud604)</li>
        <li>&middot; Haiku \u00d72 \ubcd1\ub82c (\uac80\uc99d)</li>
        <li>&middot; Gemini Flash (\ucd08\uc7a5\ubb38)</li>
        <li>&middot; \uc790\ub3d9 \ub77c\uc6b0\ud305 + \ube44\uc6a9 \ucd5c\uc801\ud654</li>
        <li>&middot; SQLite + watchdog 24/7</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['code']} \ub3c4\uad6c \uc2a4\ud0dd</h3>
      <div class="tags">
        <span class="tag">Python</span><span class="tag">Playwright</span><span class="tag">SQLite</span>
        <span class="tag">MCP</span><span class="tag">HTML/CSS</span><span class="tag">Git</span>
        <span class="tag">Bash</span><span class="tag">Node.js</span><span class="tag">Docker</span>
      </div>
    </div>
  </div>
</div>

<div class="bottom">
  <div class="btm-card">
    <h4>{I['rocket']} \ub098\ub97c \uc6c0\uc9c1\uc774\uac8c \ud558\ub294 \uac83</h4>
    <ul>
      <li>&middot; \ubcf5\uc7a1\ud55c \ubb38\uc81c\ub97c \uad6c\uc870\ud654\ud558\ub294 \ucfe0\uac10</li>
      <li>&middot; AI\uc640 \ud611\uc5c5\ud558\uc5ec \ub354 \ub098\uc740 \uacb0\uacfc</li>
      <li>&middot; \ub204\uad70\uac00\uc5d0\uac8c \ub3c4\uc6c0\ub418\ub294 \ub3c4\uad6c</li>
      <li>&middot; \uc9c0\uc18d\uc801\uc73c\ub85c \uc131\uc7a5\ud558\ub294 \uac83</li>
      <li>&middot; \ub9e4\uc77c \uc870\uae08\uc529 \ub354 \ub098\uc544\uc9c0\ub294 \uac83</li>
      <li>&middot; \uc0c8\ub85c\uc6b4 \uae30\uc220\uc744 \ud0d0\uad6c\ud558\ub294 \ud765\ubd84</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['heart']} \ubbf8\ub798\uc5d0 \uc774\ub8e8\uace0 \uc2f6\uc740 \uac83</h4>
    <ul>
      <li>&middot; \uc138\uacc4\uc801 AI \uc624\ucf00\uc2a4\ud2b8\ub808\uc774\uc158 \ud50c\ub7ab\ud3fc</li>
      <li>&middot; \ub204\uad6c\ub098 \uc0ac\uc6a9\ud560 \uc218 \uc788\ub294 \uc790\ub3d9\ud654 \ud0b7</li>
      <li>&middot; AI \uc2dc\ub300\uc758 \uba58\ud1a0\uc774\uc790 \uc120\uad6c\uc790</li>
      <li>&middot; \uae30\uc220\ub85c \uc0ac\ud68c\uc801 \uac00\uce58\ub97c \ub9cc\ub4dc\ub294 \uc77c</li>
      <li>&middot; \ub2e4\uc74c \uc138\ub300\ub97c \uc704\ud55c \uad50\uc721 \ucee8\ud150\uce20</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['plant']} \ub098\uc758 \uac00\ub2a5\uc131</h4>
    <ul>
      <li>&middot; \uae30\uc220\uacfc \uac10\uc131\uc744 \uc5f0\uacb0\ud558\ub294 \uc735\ud569\ub825</li>
      <li>&middot; \ubcf5\uc7a1\ud55c \uc2dc\uc2a4\ud15c\uc744 \ub2e8\uc21c\ud654\ud558\ub294 \uc124\uacc4\ub825</li>
      <li>&middot; \uba58\ud1a0\ub85c\uc11c \uc0ac\ub78c\uc744 \uc131\uc7a5\uc2dc\ud0a4\ub294 \ud798</li>
      <li>&middot; \ub370\uc774\ud130\ub85c \uc758\uc0ac\uacb0\uc815\ud558\ub294 \ub2a5\ub825</li>
      <li>&middot; \uc804\uccb4 \uc2dc\uc2a4\ud15c\uc744 \ubcf4\ub294 \ub208</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['check']} \uac1c\ubc1c \uccb4\ud06c\ub9ac\uc2a4\ud2b8</h4>
    <ul>
      <li>\u25a1 \ud50c\ub7ec\uadf8\uc778 50\uac1c \ub2ec\uc131</li>
      <li>\u25a1 \ub808\ud37c\ub7f0\uc2a4 100\uac1c</li>
      <li>\u25a1 24/7 \uc790\ub3d9 \uc6b4\uc601</li>
      <li>\u25a1 \uc624\ud508\uc18c\uc2a4 \ubc30\ud3ec</li>
      <li>\u25a1 1000 \uc0ac\uc6a9\uc790</li>
      <li>\u25a1 AI \uba58\ud1a0\ub9c1 \ud50c\ub7ab\ud3fc</li>
    </ul>
  </div>
</div>

</body></html>'''


# ===================== SSJ-SUMMARY (타겟.jpg 손그림 + 고밀도 하이브리드) =====================
def build_ssj_summary():
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{COMMON_CSS}
body{{width:850px;height:1100px;background:#f5efe6;
  background-image:radial-gradient(ellipse at 15% 85%,rgba(210,180,140,.10) 0%,transparent 50%),
  radial-gradient(ellipse at 85% 15%,rgba(180,160,130,.06) 0%,transparent 40%);
  padding:4px;display:grid;grid-template-rows:auto 1fr auto;gap:3px;overflow:hidden}}
.header{{display:flex;justify-content:space-between;align-items:flex-start}}
.header-left h1{{font-family:'Gaegu',cursive;font-size:26px;font-weight:700;color:#2c2418;line-height:1.15}}
.header-left .sub{{font-size:10px;color:#7a6b5a;margin-top:2px;display:flex;align-items:center;gap:3px}}
.header-right{{display:flex;gap:3px}}
.mid{{display:grid;grid-template-columns:225px 1fr 218px;gap:3px}}
.mid-left,.mid-right{{display:flex;flex-direction:column;gap:3px}}
.mid-left .card,.mid-right .card{{flex:1}}
.center{{display:flex;flex-direction:column;align-items:center;gap:2px;justify-content:flex-start}}
.char-img{{width:240px;height:230px;border-radius:8px;object-fit:cover;border:2px solid #c4b49a;box-shadow:2px 2px 8px rgba(0,0,0,.1)}}
.name-area{{text-align:center}}
.name-area .nm{{font-family:'Gaegu',cursive;font-size:18px;font-weight:700;color:#2c2418}}
.name-area .inf{{font-size:9px;color:#8a7a68}}
.quote{{background:rgba(196,145,90,.06);border:1px dashed rgba(196,145,90,.3);border-radius:4px;padding:3px 6px;text-align:center;width:100%}}
.quote p{{font-family:'Gaegu',cursive;font-size:10px;color:#8b4513;line-height:1.2}}
.goal-review{{display:grid;grid-template-columns:1fr 1fr;gap:3px;width:100%}}
.goal-box{{background:rgba(255,255,255,.45);border:1px solid #d4c4a8;border-radius:4px;padding:3px 5px;text-align:center}}
.goal-box h4{{font-family:'Gaegu',cursive;font-size:10px;color:#8b4513;margin-bottom:1px;display:flex;align-items:center;justify-content:center;gap:2px}}
.goal-box p{{font-size:8.5px;color:#5a4f42;line-height:1.25}}
.step{{display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;border-radius:50%;background:#c4915a;color:#fff;font-size:8px;font-weight:700;flex-shrink:0}}
.bottom{{display:grid;grid-template-columns:repeat(4,1fr);gap:3px}}
.btm-card{{background:rgba(255,255,255,.4);border:1.5px solid #d4c4a8;border-radius:4px;padding:4px 6px}}
.btm-card h4{{font-family:'Gaegu',cursive;font-size:10px;color:#8b4513;margin-bottom:2px;display:flex;align-items:center;gap:2px}}
.btm-card li{{font-size:9px;line-height:1.35;color:#5a4f42;display:flex;align-items:flex-start;gap:2px}}
.btm-card li svg{{flex-shrink:0;margin-top:1px}}
.btm-card ul{{list-style:none;padding:0}}
</style></head><body>

<div class="header">
  <div class="header-left">
    <h1>생각을 구조화하고,<br>변화를 만들며,<br>함께 성장하는 사람</h1>
    <div class="sub">{I['bulb']} 지혜 + {I['water']} 포용 + {I['gear']} 실행 = 만능 멘토 기질</div>
  </div>
  <div class="header-right">
    <div class="card" style="width:148px">
      <h3>{I['heart']} 행동 원칙</h3>
      <ul>
        <li>&middot; 생각을 구조화한다</li>
        <li>&middot; 깊이 품되 휘쓸리지 않는다</li>
        <li>&middot; 함께 성장한다</li>
      </ul>
      <p style="font-size:8px;color:#8a7a68;margin-top:2px">지혜+포용+실행력=나만의 경쟁력</p>
    </div>
    <div class="card" style="width:220px">
      <h3>{I['star']} 한눈에 보는 강점 키워드</h3>
      <div class="tags">
        <span class="tag">목표지향</span><span class="tag">분석력</span><span class="tag">멘토십</span>
        <span class="tag">직관력</span><span class="tag">공감력</span><span class="tag">실행력</span>
        <span class="tag">섬세함</span><span class="tag">창의융합</span><span class="tag">문제해결</span>
        <span class="tag">구조화력</span><span class="tag">신뢰감</span><span class="tag">리더십</span>
      </div>
    </div>
  </div>
</div>

<div class="mid">
  <div class="mid-left">
    <div class="card">
      <h3>{I['bulb']} 핵심 행동 특성</h3>
      <ul>
        <li>{I['fire']} <span><b>깊이 있는 탐구형 실무자</b><br><span style="font-size:9px;color:#8a7a68">호기심이 많고, 문제의 본질을 끝까지 파고듦. 현상이 아닌 원인과 구조를 이해하려는 노력.</span></span></li>
        <li>{I['cpu']} <span><b>AI &amp; 도구 활용 중심 학습자</b><br><span style="font-size:9px;color:#8a7a68">AI를 활용해 새로운 것을 배우고, 질문과 피드백을 통해 사고의 깊이를 높여감.</span></span></li>
        <li>{I['bulb']} <span><b>아이디어 연결형 사고자</b><br><span style="font-size:9px;color:#8a7a68">다양한 관점을 연결해 새로운 관점과 가치를 만들어냄.</span></span></li>
        <li>{I['gear']} <span><b>분석적 · 논리적 문제 해결자</b><br><span style="font-size:9px;color:#8a7a68">복잡한 문제를 구조화하고, 데이터 기반으로 명쾌하게 정리.</span></span></li>
        <li>{I['person']} <span><b>협업 중심 실무자</b><br><span style="font-size:9px;color:#8a7a68">다양한 관점을 존중하며, 사람과 AI 모두와 열린 실무 태도.</span></span></li>
        <li>{I['rocket']} <span><b>실행 중심 (Bias for Action)</b><br><span style="font-size:9px;color:#8a7a68">계획에 머무르지 않고 실행으로 옮기며, 작은 성과를 반복해 큰 변화를 만든다.</span></span></li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['heart']} 사람을 키우는 즐거움</h3>
      <ul>
        <li>&middot; 누군가의 성장을 돕는 것에서 가장 큰 기쁨</li>
        <li>&middot; 꾸준히 지켜보며 기다려주는 멘토링</li>
        <li>&middot; 복잡한 것을 쉽게 풀어주는 능력</li>
        <li>&middot; 성장하는 기쁨을 가까이에서 지켜봄</li>
        <li>&middot; 작은 변화가 큰 결과로 이어지는 순간</li>
        <li>&middot; 배움의 불꽃이 옮겨붙는 경험</li>
        <li>&middot; 함께 고민하고 함께 해결하는 과정</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['water']} 대인 관계 스타일</h3>
      <ul>
        <li>{I['heart']} <b>경청</b> — 말보다 듣기를 먼저</li>
        <li>{I['gear']} <b>구조화</b> — 복잡한 이야기도 정리해주는 힘</li>
        <li>{I['candle']} <b>진심</b> — 표면이 아닌 근본을 다루는 대화</li>
        <li>{I['shield']} <b>인내</b> — 끝까지 들어주는 자세</li>
        <li>{I['star']} <b>존중</b> — 다름을 인정하고 배우는 자세</li>
        <li>{I['bulb']} <b>솔직</b> — 불편해도 진실을 말하는 용기</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['fire']} 내면의 기질 (金+火)</h3>
      <ul>
        <li>{I['gear']} <b>金</b> — 구조·분석·디테일 민감, 정리 욕구</li>
        <li>{I['fire']} <b>火</b> — 좋아하면 에너지 급상승, 몰입형</li>
        <li>{I['bulb']} 생각 회전수 빠름, 여러 가능성 동시 조망</li>
        <li>{I['heart']} 감정을 깊게 쓰는 타입, 표현이 살아 있음</li>
        <li>{I['water']} 겉은 부드럽고 편안, 속은 날카로운 분석</li>
        <li>{I['shield']} 기준치와 자기검열 성향, 혼자 의미 분석</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['plant']} 에너지 흐름</h3>
      <ul>
        <li>&middot; 축적형 성장 — 꾸준한 시스템이 맞음</li>
        <li>&middot; 과열 후 급소모 패턴 주의</li>
        <li>&middot; 수면 상태가 전체 컨디션 좌우</li>
        <li>&middot; 걷기·근력운동 시 생각 정리 효과 큼</li>
        <li>&middot; 나이 들수록 신뢰감과 안정감 상승</li>
        <li>&middot; 사람·정보·아이디어 연결이 핵심 장점</li>
      </ul>
    </div>
  </div>

  <div class="center">
    <img class="char-img" src="data:image/png;base64,{laptop_b64}" />
    <div class="name-area">
      <div class="nm">서 성 종</div>
      <div style="font-size:10px;color:#8b4513;font-family:serif">\u5f90\u8056\u9418</div>
      <div class="inf">만능 멘토 기질 · 탐구 · 분석 · 실행의 사람</div>
      <div style="margin-top:2px;display:flex;gap:3px;justify-content:center">
        <span class="tag" style="background:rgba(90,158,196,.12);border-color:rgba(90,158,196,.3);color:#3a6a8a">ENFP</span>
        <span class="tag" style="background:rgba(196,90,90,.10);border-color:rgba(196,90,90,.25);color:#8a3a3a">O형</span>
        <span class="tag">丁火</span>
        <span class="tag">연결형</span>
        <span class="tag">金+火</span>
      </div>
    </div>
    <div class="quote">
      <p>\u201c작은 촛불 하나가 어둠을 밝히듯,<br>나의 한 걸음이 누군가의 방향이 된다\u201d</p>
    </div>
    <div class="card" style="width:100%;text-align:left">
      <h3>{I['gear']} 독립적이고 주도적인 전문가</h3>
      <ul>
        <li>&middot; 스스로 판단하고 책임진다</li>
        <li>&middot; 끝까지 결과를 만들어낸다</li>
        <li>&middot; 관계 중심이되 흔들리지 않는다</li>
        <li>&middot; 묵묵히 빛을 내는 등대</li>
        <li>&middot; 위기 속에서도 냉정하게 구조화</li>
      </ul>
    </div>
    <div class="goal-review">
      <div class="goal-box">
        <h4>{I['fire']} 오늘의 목표</h4>
        <p>매일 한 가지에 집중<br>방향 발견 → 깊이 파고 → 실행<br>작은 불빛이 모여 큰 방향을 밝힌다</p>
      </div>
      <div class="goal-box">
        <h4>{I['water']} 하루정리 (하루 끝)</h4>
        <p>→ 발견한 것 매달음 정리<br>→ 못한 점 정직하게<br>→ 다음 실행 체크<br>작은 개선의 오늘, 성과는 내일!</p>
      </div>
    </div>
    <div class="card" style="width:100%;text-align:left">
      <h3>{I['fire']} 성격 요약</h3>
      <ul>
        <li>{I['candle']} 따뜻함과 날카로움 공존</li>
        <li>{I['star']} 분석·공감·실행 3박자</li>
        <li>{I['heart']} 관계 중심 + 결과 중심</li>
        <li>{I['bulb']} 만능형 융합 인재</li>
        <li>{I['gear']} 감정+이성 동시 구동, 직감과 분석 병행</li>
        <li>{I['water']} 동안 유지형, 나이 들수록 신뢰감 상승</li>
      </ul>
    </div>
    <div class="card" style="width:100%;text-align:left">
      <h3>{I['person']} 관계 패턴</h3>
      <ul>
        <li>&middot; 첫인상 부드럽고 편안, 압박감 없음</li>
        <li>&middot; 웃을 때 분위기 밝아지는 타입</li>
        <li>&middot; 감정 몰입 빠르지만 에너지 소모도 큼</li>
        <li>&middot; 편안한 관계에서 최고 퍼포먼스</li>
        <li>&middot; 사람·정보·아이디어 연결이 장기</li>
        <li>&middot; 눈빛 변화와 감정 흐름이 살아 있음</li>
      </ul>
    </div>
    <div class="quote" style="width:100%">
      <p style="font-size:9px">{I['candle']} 뿌리 깊은 나무는 바람에 흔들리지 않는다 {I['plant']}</p>
    </div>
  </div>

  <div class="mid-right">
    <div class="card">
      <h3>{I['star']} 주요 강점</h3>
      <ul>
        <li>&middot; 깊이 있는 사고와 구조화 능력</li>
        <li>&middot; 빠른 학습력과 AI 활용 능력</li>
        <li>&middot; 꾸준한 실행력과 결실 중심 사고</li>
        <li>&middot; 공감 기반 멘토형 리더십</li>
        <li>&middot; 높은 책임감과 신뢰 구축력</li>
        <li>&middot; 다재다능 — 기술·관리·소통 걸침</li>
        <li>&middot; 복잡한 것을 단순하게 구조화하는 힘</li>
        <li>&middot; 위기에서 냉정한 판단력</li>
        <li>&middot; 배움을 즉시 실무에 적용하는 속도</li>
        <li>&middot; 감정과 이성을 동시에 활용하는 힘</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['heart']} 소중한 것들</h3>
      <ul>
        <li>&middot; 사람을 먼저 생각한다</li>
        <li>&middot; 지속적인 성장을 추구한다</li>
        <li>&middot; 신실과 정직을 중요시</li>
        <li>&middot; 의미 있는 결과를 만든다</li>
        <li>&middot; 가족과 삶의 균형을 소중히</li>
        <li>&middot; 배움의 즐거움을 나눈다</li>
        <li>&middot; 과정을 즐기며 결과를 만든다</li>
        <li>&middot; 작은 것에도 감사하는 마음</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['rocket']} 일을 대하는 방식</h3>
      <p style="font-size:10px;color:#8b4513;font-family:'Gaegu',cursive;margin-bottom:2px">탐구 &#8594; 분석 &#8594; 설계 &#8594; 실행</p>
      <ul>
        <li><span class="step">1</span> <b>탐구</b> — 더 나은 질문을 던진다</li>
        <li><span class="step">2</span> <b>분석</b> — 근본 원인과 패턴 발견</li>
        <li><span class="step">3</span> <b>설계</b> — 최적의 해결 방법 구조화</li>
        <li><span class="step">4</span> <b>실행</b> — 결과를 만들어 증명한다</li>
      </ul>
      <p style="font-size:8.5px;color:#8a7a68;margin-top:2px">작은 반복이 큰 변화를 만든다</p>
    </div>
    <div class="card">
      <h3>{I['plant']} 성장 엔진</h3>
      <ul>
        <li>{I['bulb']} <b>호기심</b> — 새로운 것을 배우는 즐거움</li>
        <li>{I['shield']} <b>책임감</b> — 맡은 일은 끝까지</li>
        <li>{I['heart']} <b>공감력</b> — 사람의 마음을 읽는 힘</li>
        <li>{I['code']} <b>연결력</b> — 서로 다른 것을 잇는 능력</li>
        <li>{I['star']} <b>끈기</b> — 흔들려도 다시 일어서는 회복력</li>
        <li>{I['fire']} <b>몰입</b> — 좋아하면 에너지 급상승</li>
      </ul>
    </div>
  </div>
</div>

<!-- 촛불 · 해바라기 · 무지개 SVG 트리오 -->
<div style="display:flex;justify-content:center;gap:20px;padding:2px 0;align-items:center">
  <!-- 촛불 -->
  <svg width="60" height="40" viewBox="0 0 60 40">
    <ellipse cx="30" cy="36" rx="18" ry="3" fill="rgba(196,145,90,.12)"/>
    <rect x="27" y="20" width="6" height="16" rx="1.5" fill="#c4915a"/>
    <ellipse cx="30" cy="15" rx="5" ry="8" fill="#e8a836" opacity=".6"/>
    <ellipse cx="30" cy="13" rx="3" ry="5" fill="#f0c040"/>
    <line x1="20" y1="12" x2="8" y2="6" stroke="#e8c36a" stroke-width=".6" opacity=".3"/>
    <line x1="40" y1="12" x2="52" y2="6" stroke="#e8c36a" stroke-width=".6" opacity=".3"/>
    <line x1="20" y1="18" x2="5" y2="22" stroke="#e8c36a" stroke-width=".5" opacity=".2"/>
    <line x1="40" y1="18" x2="55" y2="22" stroke="#e8c36a" stroke-width=".5" opacity=".2"/>
    <text x="14" y="38" font-size="7" fill="#8a7a68" font-family="'Gaegu',cursive" font-weight="700">丁火</text>
  </svg>
  <!-- 해바라기 -->
  <svg width="60" height="40" viewBox="0 0 60 40">
    <line x1="30" y1="40" x2="30" y2="22" stroke="#6b8e5a" stroke-width="2"/>
    <line x1="30" y1="30" x2="20" y2="34" stroke="#6b8e5a" stroke-width="1.2"/>
    <ellipse cx="20" cy="34" rx="4" ry="2" fill="#6b8e5a" opacity=".5"/>
    <circle cx="30" cy="15" r="5" fill="#8b6a13"/>
    <ellipse cx="30" cy="8" rx="3" ry="5" fill="#e8c36a" transform="rotate(0,30,15)"/>
    <ellipse cx="37" cy="11" rx="3" ry="5" fill="#e8c36a" transform="rotate(50,37,11)"/>
    <ellipse cx="37" cy="19" rx="3" ry="5" fill="#e8c36a" transform="rotate(100,37,19)"/>
    <ellipse cx="30" cy="22" rx="3" ry="5" fill="#e8c36a" transform="rotate(0,30,22)"/>
    <ellipse cx="23" cy="19" rx="3" ry="5" fill="#e8c36a" transform="rotate(-100,23,19)"/>
    <ellipse cx="23" cy="11" rx="3" ry="5" fill="#e8c36a" transform="rotate(-50,23,11)"/>
    <text x="14" y="38" font-size="7" fill="#8a7a68" font-family="'Gaegu',cursive" font-weight="700">성장</text>
  </svg>
  <!-- 무지개 -->
  <svg width="80" height="40" viewBox="0 0 80 40">
    <path d="M5 38 Q40 -5 75 38" fill="none" stroke="#e07a2f" stroke-width="2.5" opacity=".5"/>
    <path d="M10 38 Q40 0 70 38" fill="none" stroke="#e8c36a" stroke-width="2.5" opacity=".5"/>
    <path d="M15 38 Q40 5 65 38" fill="none" stroke="#6b8e5a" stroke-width="2.5" opacity=".5"/>
    <path d="M20 38 Q40 10 60 38" fill="none" stroke="#5a9ec4" stroke-width="2.5" opacity=".5"/>
    <path d="M25 38 Q40 15 55 38" fill="none" stroke="#7a6b8e" stroke-width="2.5" opacity=".5"/>
    <circle cx="8" cy="36" r="3" fill="#e8c36a" opacity=".3"/>
    <circle cx="72" cy="36" r="3" fill="#e8c36a" opacity=".3"/>
    <text x="22" y="38" font-size="7" fill="#8a7a68" font-family="'Gaegu',cursive" font-weight="700">가능성</text>
  </svg>
</div>

<div class="bottom">
  <div class="btm-card">
    <h4>{I['rocket']} 나를 움직이게 하는 것</h4>
    <ul>
      <li>&middot; 복잡한 문제를 해결하는 쾌감</li>
      <li>&middot; 배움을 실제 결과로 연결</li>
      <li>&middot; AI와 협업으로 더 나은 결과</li>
      <li>&middot; 지속적으로 성장하며 기여하는 것</li>
      <li>&middot; 매일 한 뼘씩 앞으로 나아가는 것</li>
      <li>&middot; 새로운 도전에서 배우는 기쁨</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['heart']} 미래에 이루고 싶은 것</h4>
    <ul>
      <li>&middot; 독립적이고 주도적인 전문가</li>
      <li>&middot; 스스로 판단하고 책임지며</li>
      <li>&middot; 끝까지 결과를 만들어낸다</li>
      <li>&middot; 사람을 소중히 여기는 관계 중심</li>
      <li>&middot; 다음 세대를 위한 교육 멘토</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['plant']} 나의 가능성</h4>
    <ul>
      <li>&middot; 어둠을 밝히는 지혜</li>
      <li>&middot; 분석력+실행력 전문가</li>
      <li>&middot; 기술과 감성의 융합력</li>
      <li>&middot; 멘토로 사람을 성장시키는 힘</li>
      <li>&middot; 데이터 기반 의사결정의 힘</li>
      <li>&middot; 전체 시스템을 조율하는 능력</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['check']} 인생 체크리스트</h4>
    <ul>
      <li>&middot; 전문성 강화</li>
      <li>&middot; 건강 관리</li>
      <li>&middot; 영향력 확장</li>
      <li>&middot; 역할 수행</li>
      <li>&middot; 가족과 시간</li>
      <li>&middot; 겸손하되 꾸준히</li>
    </ul>
  </div>
</div>

</body></html>'''


# ===================== RENDER =====================
print("Building HTML...")
orch_html = build_orch_promo()
ssj_html = build_ssj_summary()
(DIR / "orch-promo.html").write_text(orch_html, encoding="utf-8")
(DIR / "ssj-infographic.html").write_text(ssj_html, encoding="utf-8")

print("Rendering with Playwright...")
with sync_playwright() as pw:
    br = pw.chromium.launch()

    # orch-promo
    pg = br.new_page(viewport={"width":850,"height":1100})
    pg.goto((DIR / "orch-promo.html").as_uri())
    pg.wait_for_timeout(3000)
    pg.screenshot(path=str(DIR / "orch-promo.jpg"), full_page=False, type="jpeg", quality=95)
    print("  orch-promo.jpg OK")
    pg.close()

    # ssj-summary
    pg = br.new_page(viewport={"width":850,"height":1100})
    pg.goto((DIR / "ssj-infographic.html").as_uri())
    pg.wait_for_timeout(3000)
    pg.screenshot(path=str(DIR / "ssj-summary.jpg"), full_page=False, type="jpeg", quality=95)
    print("  ssj-summary.jpg OK")
    pg.close()

    br.close()

print("Done: orch-promo.jpg + ssj-summary.jpg")
