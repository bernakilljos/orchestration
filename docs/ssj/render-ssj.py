#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render orch-promo.jpg + ssj-summary.jpg in 타겟.jpg infographic style."""
import base64, pathlib
from playwright.sync_api import sync_playwright

DIR = pathlib.Path(__file__).parent
char_b64 = base64.b64encode((DIR / "caricature-candle.png").read_bytes()).decode()
photo_b64 = base64.b64encode((DIR / "\ub0b4\uc0ac\uc9c4.jpg").read_bytes()).decode()

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
}

COMMON_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@300;400;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
body{font-family:'Noto Sans KR',sans-serif;overflow:hidden;color:#3a3226}
.card{background:rgba(255,255,255,.6);border:1.5px solid #c4b49a;border-radius:5px;padding:8px 10px;box-shadow:1px 2px 6px rgba(0,0,0,.05)}
.card h3{font-family:'Gaegu',cursive;font-size:13px;font-weight:700;color:#8b4513;margin-bottom:4px;border-bottom:1px solid rgba(180,150,120,.25);padding-bottom:2px;display:flex;align-items:center;gap:3px}
.card li,.card p{font-size:10px;line-height:1.55;color:#4a3f33}
.card ul{list-style:none;padding:0}
.tags{display:flex;flex-wrap:wrap;gap:3px}
.tag{background:rgba(196,145,90,.12);border:1px solid rgba(196,145,90,.3);color:#7a5a3a;font-size:9px;padding:1px 5px;border-radius:8px;font-family:'Gaegu',cursive;font-weight:700}
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
  </div>

  <div class="center">
    <div style="position:relative">
      <img class="photo" src="data:image/jpeg;base64,{photo_b64}" />
      <div style="position:absolute;top:6px;left:8px;background:rgba(255,255,255,.8);border-radius:4px;padding:2px 6px;font-size:8px;color:#8b4513;font-family:'Gaegu',cursive">AI Orchestrator</div>
    </div>
    <div class="name-area">
      <div class="nm">\uc11c \uc131 \uc885</div>
      <div style="font-size:11px;color:#8b4513;font-family:serif">\u5F90\u8056\u9418</div>
      <div class="inf">Multi-AI Orchestration Kit v1 \uac1c\ubc1c\uc790</div>
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
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['heart']} \ubbf8\ub798\uc5d0 \uc774\ub8e8\uace0 \uc2f6\uc740 \uac83</h4>
    <ul>
      <li>&middot; \uc138\uacc4\uc801 AI \uc624\ucf00\uc2a4\ud2b8\ub808\uc774\uc158 \ud50c\ub7ab\ud3fc</li>
      <li>&middot; \ub204\uad6c\ub098 \uc0ac\uc6a9\ud560 \uc218 \uc788\ub294 \uc790\ub3d9\ud654 \ud0b7</li>
      <li>&middot; AI \uc2dc\ub300\uc758 \uba58\ud1a0\uc774\uc790 \uc120\uad6c\uc790</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['plant']} \ub098\uc758 \uac00\ub2a5\uc131</h4>
    <ul>
      <li>&middot; \uae30\uc220\uacfc \uac10\uc131\uc744 \uc5f0\uacb0\ud558\ub294 \uc735\ud569\ub825</li>
      <li>&middot; \ubcf5\uc7a1\ud55c \uc2dc\uc2a4\ud15c\uc744 \ub2e8\uc21c\ud654\ud558\ub294 \uc124\uacc4\ub825</li>
      <li>&middot; \uba58\ud1a0\ub85c\uc11c \uc0ac\ub78c\uc744 \uc131\uc7a5\uc2dc\ud0a4\ub294 \ud798</li>
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


# ===================== SSJ-SUMMARY =====================
def build_ssj_summary():
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{COMMON_CSS}
body{{width:850px;height:1100px;background:#f5efe6;
  background-image:radial-gradient(ellipse at 15% 85%,rgba(210,180,140,.12) 0%,transparent 50%),
  radial-gradient(ellipse at 85% 15%,rgba(180,160,130,.08) 0%,transparent 40%);
  padding:14px 16px;display:flex;flex-direction:column;justify-content:space-between}}
.header{{display:flex;justify-content:space-between;align-items:flex-start}}
.header-left h1{{font-family:'Gaegu',cursive;font-size:28px;font-weight:700;color:#2c2418;line-height:1.25}}
.header-left .sub{{font-size:11px;color:#7a6b5a;margin-top:3px}}
.header-right{{display:flex;gap:6px}}
.mid{{display:grid;grid-template-columns:228px 1fr 228px;gap:8px;flex:1;margin:6px 0}}
.mid-left,.mid-right{{display:flex;flex-direction:column;gap:5px}}
.center{{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px}}
.char-img{{width:280px;height:250px;border-radius:8px;object-fit:cover;border:2.5px solid #c4b49a;box-shadow:3px 3px 10px rgba(0,0,0,.1)}}
.name-area{{text-align:center}}
.name-area .nm{{font-family:'Gaegu',cursive;font-size:20px;font-weight:700;color:#2c2418}}
.name-area .inf{{font-size:9px;color:#8a7a68;margin-top:1px}}
.goal-review{{display:grid;grid-template-columns:1fr 1fr;gap:5px;width:100%}}
.goal-box{{background:rgba(255,255,255,.5);border:1px solid #d4c4a8;border-radius:5px;padding:5px 7px;text-align:center}}
.goal-box h4{{font-family:'Gaegu',cursive;font-size:11px;color:#8b4513;margin-bottom:2px}}
.goal-box p{{font-size:9px;color:#5a4f42;line-height:1.4}}
.bottom{{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px}}
.btm-card{{background:rgba(255,255,255,.45);border:1.5px solid #d4c4a8;border-radius:5px;padding:7px 9px}}
.btm-card h4{{font-family:'Gaegu',cursive;font-size:11px;color:#8b4513;margin-bottom:3px;display:flex;align-items:center;gap:3px}}
.btm-card li{{font-size:9px;line-height:1.45;color:#5a4f42}}
.btm-card ul{{list-style:none;padding:0}}
</style></head><body>

<div class="header">
  <div class="header-left">
    <h1>\ucd1b\ubd88\ucc98\ub7fc \ubc1d\ud788\uace0,<br>\ubc14\ub2e4\ucc98\ub7fc \ud488\uc73c\uba70,<br>\ud568\uaed8 \uc131\uc7a5\ud558\ub294 \uc0ac\ub78c</h1>
    <div class="sub">{I['fire']} \u4e01\u706b(\ucd1b\ubd88) + {I['water']} \u4ea5\u6c34(\ubc14\ub2e4) = \ub9cc\ub2a5 \uba58\ud1a0\uc758 \uc0ac\uc8fc</div>
  </div>
  <div class="header-right">
    <div class="card" style="width:155px">
      <h3>{I['heart']} \ud589\ub3d9 \uc6d0\uce59</h3>
      <ul>
        <li>&middot; \uc740\uc740\ud558\uac8c \ube44\ucd94\ub418 \uaebc\uc9c0\uc9c0 \uc54a\ub294\ub2e4</li>
        <li>&middot; \uae4a\uc774 \ud488\ub418 \ud718\uc4f8\ub9ac\uc9c0 \uc54a\ub294\ub2e4</li>
        <li>&middot; \ud568\uaed8 \uc131\uc7a5\ud558\ub418 \uc911\uc2ec\uc744 \uc783\uc9c0 \uc54a\ub294\ub2e4</li>
      </ul>
      <p style="font-size:8px;color:#8a7a68;margin-top:2px">\u4e01\u706b+\u4ea5\u6c34+\u8f9b\u9149=\ub098\ub9cc\uc758 \uacbd\uc7c1\ub825</p>
    </div>
    <div class="card" style="width:175px">
      <h3>{I['star']} \uc0ac\uc8fc \uac15\uc810 \ud0a4\uc6cc\ub4dc</h3>
      <div class="tags">
        <span class="tag">\ucd1b\ubd88 \uc9c0\ud61c</span><span class="tag">\ubc14\ub2e4 \ud3ec\uc6a9</span><span class="tag">\uba58\ud1a0\uc2ed</span>
        <span class="tag">\uc9c1\uad00\ub825</span><span class="tag">\ubd84\uc11d\ub825</span><span class="tag">\ub044\uae30</span>
        <span class="tag">\uc12c\uc138\ud568</span><span class="tag">\ucc3d\uc758\uc735\ud569</span><span class="tag">\uc2e4\ud589\ub825</span>
        <span class="tag">\uacf5\uac10\ub825</span><span class="tag">\ud559\uc2b5\ub825</span><span class="tag">\ub9ac\ub354\uc2ed</span>
      </div>
    </div>
  </div>
</div>

<div class="mid">
  <div class="mid-left">
    <div class="card" style="flex:1">
      <h3>{I['bulb']} \u4e01\u4ea5 \uc77c\uc8fc \ud575\uc2ec \ud2b9\uc131</h3>
      <ul>
        <li>&middot; <b>\ucd1b\ubd88\uc758 \uc9d1\uc911\ub825</b> (\u4e01\u706b)<br><span style="font-size:9px;color:#8a7a68">\uc740\uc740\ud558\uc9c0\ub9cc \uaebc\uc9c0\uc9c0 \uc54a\ub294 \ubd88. \ud55c \uac00\uc9c0\uc5d0 \uae4a\uc774 \ubab0\uc785\ud558\uace0 \ubcf8\uc9c8\uc744 \uafe0\ub6ab\ub294 \ud1b5\ucc30\ub825.</span></li>
        <li>&middot; <b>\ubc14\ub2e4\uc758 \ud3ec\uc6a9\ub825</b> (\u4ea5\u6c34)<br><span style="font-size:9px;color:#8a7a68">\ubaa8\ub4e0 \uac83\uc744 \ubc1b\uc544\ub4e4\uc774\ub294 \uae4a\uc740 \ubb3c. \uc0ac\ub78c\uc758 \ub9c8\uc74c\uc744 \uc77d\uace0 \uac10\uc2f8\uc8fc\ub294 \ub2a5\ub825.</span></li>
        <li>&middot; <b>\ub9cc\ub2a5 \uba58\ud1a0 \uae30\uc9c8</b><br><span style="font-size:9px;color:#8a7a68">\uac00\ub974\uce58\uace0 \uc774\ub044\ub294 \uc7ac\ub2a5\uc774 \ud0c0\uace0\ub0a8. \ubcf5\uc7a1\ud55c \uac83\uc744 \uc27d\uac8c \ud480\uc5b4\uc8fc\ub294 \ub2a5\ub825.</span></li>
        <li>&middot; <b>\uc544\uc774\ub514\uc5b4 \uc5f0\uacb0\uc0ac</b><br><span style="font-size:9px;color:#8a7a68">\u6c34\u751f\u6728\uc758 \uae30\uc6b4\uc73c\ub85c \uc0c8\ub85c\uc6b4 \uac83\uc744 \uc2f9\ud2f0\uc6b0\uace0, \u706b\uc758 \uc5f4\uc815\uc73c\ub85c \uc2e4\ud589.</span></li>
        <li>&middot; <b>\uc9c1\uad00\uacfc \ub17c\ub9ac\uc758 \uade0\ud615</b><br><span style="font-size:9px;color:#8a7a68">\u4e01\uc758 \uc9c1\uad00 + \u4ea5\uc758 \uc9c0\ud61c = \uac10\uac01\uc801\uc774\uba74\uc11c\ub3c4 \ub17c\ub9ac\uc801\uc778 \ud310\ub2e8\ub825.</span></li>
        <li>&middot; <b>\uc2e4\ud589 \uc911\uc2ec (\u5b98\u661f \ud65c\uc6a9)</b><br><span style="font-size:9px;color:#8a7a68">\uacc4\ud68d\uc5d0 \uba38\ubb34\ub974\uc9c0 \uc54a\uace0 \ud589\ub3d9\uc73c\ub85c \uc62e\uae30\uba70, \uc791\uc740 \uc131\uacfc\ub97c \uc313\uc544 \ud070 \ubcc0\ud654\ub97c.</span></li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['rocket']} \uc77c\uc744 \ub300\ud558\ub294 \ubc29\uc2dd</h3>
      <p style="font-size:10px;color:#8b4513;font-family:'Gaegu',cursive;margin-bottom:3px">\ud0d0\uad6c &#8594; \ubd84\uc11d &#8594; \uc124\uacc4 &#8594; \uc2e4\ud589</p>
      <ul>
        <li>&middot; <b>1. \ud0d0\uad6c</b> \u2014 \ucd1b\ubd88\ucc98\ub7fc \uc5b4\ub460 \uc18d \ud575\uc2ec\uc744 \ube44\ucd98\ub2e4</li>
        <li>&middot; <b>2. \ubd84\uc11d</b> \u2014 \ubc14\ub2e4\ucc98\ub7fc \uae4a\uc774 \ud30c\uace0\ub4e0\ub2e4</li>
        <li>&middot; <b>3. \uc124\uacc4</b> \u2014 \uae08(\u8f9b) \uae30\uc6b4\uc73c\ub85c \ub0a0\uce74\ub86d\uac8c \uad6c\uc870\ud654</li>
        <li>&middot; <b>4. \uc2e4\ud589</b> \u2014 \uacb0\uacfc\ub97c \ub9cc\ub4e4\uc5b4 \uc99d\uba85\ud55c\ub2e4</li>
      </ul>
    </div>
  </div>

  <div class="center">
    <div style="position:relative">
      <img class="char-img" src="data:image/png;base64,{char_b64}" />
      <div style="position:absolute;top:5px;left:7px;background:rgba(255,255,255,.75);border-radius:4px;padding:2px 5px;font-size:8px;color:#8b4513;font-family:'Gaegu',cursive">\u4e01\u4ea5 \u00b7 \ucd1b\ubd88+\ubc14\ub2e4</div>
    </div>
    <div class="name-area">
      <div class="nm">\uc11c \uc131 \uc885</div>
      <div style="font-size:11px;color:#8b4513;font-family:serif">\u5f90\u8056\u9418</div>
      <div class="inf">\uc815\ud574(\u4e01\u4ea5) \uc77c\uc8fc \u00b7 \uc2e0\uc720(\u8f9b\u9149) \ub300\uc6b4 \u00b7 \ub9cc\ub2a5 \uba58\ud1a0 \uc0ac\uc8fc</div>
    </div>
    <div class="goal-review">
      <div class="goal-box">
        <h4>{I['fire']} \uc624\ub298\uc758 \ubaa9\ud45c</h4>
        <p>\ub9e4\uc77c \ucd1b\ubd88\ucc98\ub7fc \ud55c \uac00\uc9c0\uc5d0 \uc9d1\uc911<br>\ubc29\ud5a5 \ubc1c\uacac \u2192 \uae4a\uc774 \ud30c\uace0 \u2192 \uc2e4\ud589</p>
        <p style="font-size:8px;color:#aaa;margin-top:1px">\uc791\uc740 \ubd88\ube5b\uc774 \ubaa8\uc5ec \ud070 \ubc29\ud5a5\uc744 \ubc1d\ud78c\ub2e4</p>
      </div>
      <div class="goal-box">
        <h4>{I['water']} \ub9ac\ubdf0 (\ud558\ub8e8 \ub05d)</h4>
        <p>\u2192 \ubc1c\uacac \ub9e4\ub2ec\uc74c \uc815\ub9ac<br>\u2192 \ubabb\ud55c \uc810 \uc815\uc9c1\ud558\uac8c<br>\u2192 \ub2e4\uc74c \uc2e4\ud589 \uccb4\ud06c</p>
        <p style="font-size:8px;color:#8b4513;margin-top:1px;font-family:'Gaegu',cursive">\uc791\uc740 \uac1c\uc120\uc758 \uc624\ub298, \ud559\uc2b5\uc740 \ub0b4\uc77c!</p>
      </div>
    </div>
  </div>

  <div class="mid-right">
    <div class="card">
      <h3>{I['star']} \uc8fc\uc694 \uac15\uc810 (\uc0ac\uc8fc \uae30\ubc18)</h3>
      <ul>
        <li>&middot; \uc740\uc740\ud55c \ube5b\uc73c\ub85c \ubc29\ud5a5\uc744 \uc81c\uc2dc (\u4e01\ud654)</li>
        <li>&middot; \uae4a\uc740 \uc9c0\ud61c\uc640 \ud3ec\uc6a9\ub825 (\u4ea5\uc218)</li>
        <li>&middot; \uafc0\uc900\ud55c \uc2e4\ud589\ub825\uacfc \uacb0\uc2e4 (\u8f9b\u9149 \ub300\uc6b4)</li>
        <li>&middot; \uacf5\uac10 \uae30\ubc18 \uba58\ud1a0\ud615 \ub9ac\ub354\uc2ed</li>
        <li>&middot; \ub192\uc740 \ucc45\uc784\uac10\uacfc \uc2e0\ub8b0 \uad6c\ucd95\ub825</li>
        <li>&middot; \ub2e4\uc7ac\ub2e4\ub2a5 \u2014 \uae30\uc220\u00b7\uad00\ub9ac\u00b7\uc18c\ud1b5 \uac78\uce68</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['heart']} \uac00\uce58\uad00 (\u4e01\ud654\uc758 \ub530\ub73b\ud568)</h3>
      <ul>
        <li>&middot; \uc0ac\ub78c\uc744 \uba3c\uc800 \uc0dd\uac01\ud55c\ub2e4 (\u4e01\ud654\uc758 \ube5b)</li>
        <li>&middot; \uc9c0\uc18d\uc801\uc778 \uc131\uc7a5\uc744 \ucd94\uad6c (\u4ea5\uc218\uc758 \ud750\ub984)</li>
        <li>&middot; \uc2e0\uc2e4\uacfc \uc815\uc9c1\uc744 \uc911\uc694\uc2dc (\u8f9b\uae08\uc758 \uacb0\ub2e8)</li>
        <li>&middot; \uc758\ubbf8 \uc788\ub294 \uacb0\uacfc\ub97c \ub9cc\ub4e0\ub2e4</li>
        <li>&middot; \uac00\uc871\uacfc \uc0b6\uc758 \uade0\ud615\uc744 \uc18c\uc911\ud788</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['fire']}{I['water']} \uc0ac\uc8fc \uc5d0\ub108\uc9c0 \uc694\uc57d</h3>
      <ul>
        <li>&middot; <b>\u4e01\ud654(\uc815\ud654)</b> \u2014 \ucd1b\ubd88\uc758 \uc9d1\uc911\uacfc \ub530\ub73b\ud568</li>
        <li>&middot; <b>\u4ea5\uc218(\ud574\uc218)</b> \u2014 \uae4a\uc740 \ubc14\ub2e4\uc758 \uc9c0\ud61c\uc640 \ud3ec\uc6a9</li>
        <li>&middot; <b>\uc2e0\uc720 \ub300\uc6b4</b> \u2014 \uae08(\u91d1) \uae30\uc6b4, \uacb0\uc2e4\uacfc \uc815\ub9ac</li>
        <li>&middot; <b>\ub9cc\ub2a5 \uba58\ud1a0</b> \u2014 \ub2e4\uc7ac\ub2e4\ub2a5, \uac00\ub974\uce68\uc758 \uc7ac\ub2a5</li>
      </ul>
      <p style="font-size:8px;color:#8a7a68;margin-top:2px">\ucd1b\ubd88\uc774 \uae4a\uc740 \ubc14\ub2e4 \uc704\uc5d0 \ub5a0 \uc788\ub294 \ud615\uc0c1 \u2014<br>\uc5b4\ub460 \uc18d\uc5d0\uc11c\ub3c4 \ubc29\ud5a5\uc744 \uc81c\uc2dc\ud558\ub294 \ub4f1\ub300</p>
    </div>
  </div>
</div>

<div class="bottom">
  <div class="btm-card">
    <h4>{I['rocket']} \ub098\ub97c \uc6c0\uc9c1\uc774\uac8c \ud558\ub294 \uac83</h4>
    <ul>
      <li>&middot; \ubcf5\uc7a1\ud55c \ubb38\uc81c\ub97c \ucd1b\ubd88\ucc98\ub7fc \ubc1d\ud788\ub294 \ucfe0\uac10</li>
      <li>&middot; \ubc30\uc6c0\uc744 \uc2e4\uc81c \uacb0\uacfc\ub85c \uc5f0\uacb0\ud558\ub294 \uac83</li>
      <li>&middot; AI\uc640 \ud611\uc5c5\ud558\uc5ec \ub354 \ub098\uc740 \uacb0\uacfc</li>
      <li>&middot; \uc9c0\uc18d\uc801\uc73c\ub85c \uc131\uc7a5\ud558\uba70 \uae30\uc5ec\ud558\ub294 \uac83</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['heart']} \ubbf8\ub798\uc5d0 \uc774\ub8e8\uace0 \uc2f6\uc740 \uac83</h4>
    <ul>
      <li>&middot; \ub3c5\ub9bd\uc801\uc774\uace0 \uc8fc\ub3c4\uc801\uc778 \uc804\ubb38\uac00</li>
      <li>&middot; \uc2a4\uc2a4\ub85c \ud310\ub2e8\ud558\uace0 \ucc45\uc784\uc9c0\uba70</li>
      <li>&middot; \ub05d\uae4c\uc9c0 \uacb0\uacfc\ub97c \ub9cc\ub4e4\uc5b4\ub0b8\ub2e4</li>
    </ul>
    <p style="font-size:8px;color:#8a7a68;margin-top:2px">\uc0ac\ub78c\uc744 \uc18c\uc911\ud788 \uc5ec\uae30\ub294 \uad00\uacc4 \uc911\uc2ec<br>\uc9c4\uc2e4\uacfc \uc2e0\ub8b0\ub97c \ud1b5\ud574 \uc131\uc7a5</p>
  </div>
  <div class="btm-card">
    <h4>{I['plant']} \ub098\uc758 \uac00\ub2a5\uc131</h4>
    <ul>
      <li>&middot; \ucd1b\ubd88\ucc98\ub7fc \uc5b4\ub460\uc744 \ubc1d\ud788\ub294 \uc9c0\ud61c</li>
      <li>&middot; \ubd84\uc11d\ub825\uacfc \uc2e4\ud589\ub825\uc744 \uac96\ucd98 \uc804\ubb38\uac00</li>
      <li>&middot; \uae30\uc220\uacfc \uac10\uc131\uc744 \uc5f0\uacb0\ud558\ub294 \uc735\ud569\ub825</li>
    </ul>
    <p style="font-size:8px;color:#8a7a68;margin-top:2px">\uba58\ud1a0\ub85c\uc11c \uc0ac\ub78c\uc744 \uc131\uc7a5\uc2dc\ud0a4\ub294 \ud798\uc744<br>\ub9cc\ub4e4\uc5b4\ub0bc \uc218 \uc788\ub2e4!</p>
  </div>
  <div class="btm-card">
    <h4>{I['check']} \uc778\uc0dd \uccb4\ud06c\ub9ac\uc2a4\ud2b8</h4>
    <ul>
      <li>\u25a1 \uc804\ubb38\uc131 \uac15\ud654</li>
      <li>\u25a1 \uac74\uac15 \uad00\ub9ac</li>
      <li>\u25a1 \uc601\ud5a5\ub825 \ud655\uc7a5</li>
      <li>\u25a1 \uc5ed\ud560 \uc218\ud589</li>
      <li>\u25a1 \uac00\uc871\uacfc \uc2dc\uac04</li>
      <li>\u25a1 \uc7ac\ud14c\ud06c \uc548\uc815</li>
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
