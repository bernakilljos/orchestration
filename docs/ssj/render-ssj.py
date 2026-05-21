#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64, pathlib

DIR = pathlib.Path(__file__).parent
char_b64 = base64.b64encode((DIR / "caricature.png").read_bytes()).decode()

# SVG 아이콘들 (인라인)
svg_bulb = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#c4915a" stroke-width="1.5"><path d="M9 21h6M12 3a6 6 0 0 0-4 10.5V17h8v-3.5A6 6 0 0 0 12 3z"/></svg>'
svg_rocket = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#c4915a" stroke-width="1.5"><path d="M12 2C6 8 6 16 12 22c6-6 6-14 0-20zM5 16l-2 4 4-2M19 16l2 4-4-2"/></svg>'
svg_star = '<svg viewBox="0 0 24 24" width="16" height="16" fill="#e8c36a" stroke="none"><path d="M12 2l3 6.5 7 1-5 5 1.2 7L12 18l-6.2 3.5L7 14.5l-5-5 7-1z"/></svg>'
svg_heart = '<svg viewBox="0 0 24 24" width="15" height="15" fill="#c4915a" stroke="none"><path d="M12 21C8 17 2 13 2 8a5 5 0 0 1 10 0 5 5 0 0 1 10 0c0 5-6 9-10 13z"/></svg>'
svg_fire = '<svg viewBox="0 0 24 24" width="16" height="16" fill="#e07a2f" stroke="none"><path d="M12 23c-4 0-7-3-7-7 0-3 2-5 4-7 0 2 1 3 2 3 0-4 3-8 5-10 0 3 1 5 2 6 2 2 3 4 3 6 0 5-4 9-9 9z"/></svg>'
svg_water = '<svg viewBox="0 0 24 24" width="16" height="16" fill="#5a9ec4" stroke="none"><path d="M12 2C8 8 5 12 5 16a7 7 0 0 0 14 0c0-4-3-8-7-14z"/></svg>'
svg_plant = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#6b8e5a" stroke-width="1.5"><path d="M12 22V8M8 12c-3 0-5-2-5-5 3 0 5 2 5 5M16 10c3 0 5-2 5-5-3 0-5 2-5 5M9 18c-2.5 0-4.5-2-4.5-4.5 2.5 0 4.5 2 4.5 4.5"/></svg>'
svg_coffee = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#8b7355" stroke-width="1.5"><path d="M18 8h1a4 4 0 0 1 0 8h-1M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8zM6 1v3M10 1v3M14 1v3"/></svg>'
svg_book = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#8b4513" stroke-width="1.5"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 4.5A2.5 2.5 0 0 1 6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15z"/></svg>'
svg_check = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#6b8e5a" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>'

html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Gaegu:wght@300;400;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{
  width:850px;height:1100px;
  font-family:'Noto Sans KR',sans-serif;
  background:#f5efe6;
  background-image:radial-gradient(ellipse at 15% 85%,rgba(210,180,140,.12) 0%,transparent 50%),
    radial-gradient(ellipse at 85% 15%,rgba(180,160,130,.08) 0%,transparent 40%);
  color:#3a3226;overflow:hidden;padding:20px;
}}
.header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px}}
.header-left h1{{font-family:'Gaegu',cursive;font-size:30px;font-weight:700;color:#2c2418;line-height:1.25}}
.header-left .sub{{font-size:12px;color:#7a6b5a;margin-top:4px}}
.header-right{{display:flex;gap:8px}}
.card{{background:rgba(255,255,255,.6);border:1.5px solid #c4b49a;border-radius:5px;padding:10px 12px;box-shadow:1px 2px 6px rgba(0,0,0,.05)}}
.card h3{{font-family:'Gaegu',cursive;font-size:14px;font-weight:700;color:#8b4513;margin-bottom:5px;border-bottom:1px solid rgba(180,150,120,.25);padding-bottom:3px;display:flex;align-items:center;gap:4px}}
.card li,.card p{{font-size:11px;line-height:1.65;color:#4a3f33}}
.card ul{{list-style:none;padding:0}}
.mid{{display:grid;grid-template-columns:235px 340px 235px;gap:10px;margin-bottom:10px}}
.mid-left,.mid-right{{display:flex;flex-direction:column;gap:8px}}
.center{{display:flex;flex-direction:column;align-items:center;gap:6px}}
.char-img{{width:320px;height:280px;border-radius:8px;object-fit:cover;border:2.5px solid #c4b49a;box-shadow:3px 3px 10px rgba(0,0,0,.1)}}
.name-area{{text-align:center;width:100%}}
.name-area .nm{{font-family:'Gaegu',cursive;font-size:22px;font-weight:700;color:#2c2418}}
.name-area .inf{{font-size:9px;color:#8a7a68;margin-top:1px}}
.goal-review{{display:grid;grid-template-columns:1fr 1fr;gap:6px;width:100%}}
.goal-box{{background:rgba(255,255,255,.5);border:1px solid #d4c4a8;border-radius:5px;padding:6px 8px;text-align:center}}
.goal-box h4{{font-family:'Gaegu',cursive;font-size:11px;color:#8b4513;margin-bottom:2px}}
.goal-box p{{font-size:9px;color:#5a4f42;line-height:1.5}}
.bottom{{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;margin-top:8px}}
.btm-card{{background:rgba(255,255,255,.45);border:1.5px solid #d4c4a8;border-radius:5px;padding:8px 10px}}
.btm-card h4{{font-family:'Gaegu',cursive;font-size:11px;color:#8b4513;margin-bottom:3px;display:flex;align-items:center;gap:3px}}
.btm-card li{{font-size:9px;line-height:1.5;color:#5a4f42}}
.btm-card ul{{list-style:none;padding:0}}
.tags{{display:flex;flex-wrap:wrap;gap:3px}}
.tag{{background:rgba(196,145,90,.12);border:1px solid rgba(196,145,90,.3);color:#7a5a3a;font-size:9px;padding:1px 6px;border-radius:8px;font-family:'Gaegu',cursive;font-weight:700}}
.deco{{position:absolute;opacity:.15}}
</style></head><body>

<!-- 장식 SVG -->
<div style="position:absolute;top:15px;right:20px;opacity:.12">{svg_plant}</div>
<div style="position:absolute;bottom:15px;left:20px;opacity:.12">{svg_coffee}</div>
<div style="position:absolute;bottom:15px;right:25px;opacity:.12">{svg_book}</div>

<!-- 상단 -->
<div class="header">
  <div class="header-left">
    <h1>촛불처럼 밝히고,<br>바다처럼 품으며,<br>함께 성장하는 사람</h1>
    <div class="sub">{svg_fire} 丁火(촛불) + {svg_water} 亥水(바다) = 만능 멘토의 사주</div>
  </div>
  <div class="header-right">
    <div class="card" style="width:155px">
      <h3>{svg_heart} 행동 원칙</h3>
      <ul>
        <li>&middot; 은은하게 비추되 꺼지지 않는다</li>
        <li>&middot; 깊이 품되 휩쓸리지 않는다</li>
        <li>&middot; 함께 성장하되 중심을 잃지 않는다</li>
      </ul>
      <p style="font-size:9px;color:#8a7a68;margin-top:3px">丁火+亥水+辛酉=나만의 경쟁력</p>
    </div>
    <div class="card" style="width:175px">
      <h3>{svg_star} 사주 강점 키워드</h3>
      <div class="tags">
        <span class="tag">촛불 지혜</span>
        <span class="tag">바다 포용</span>
        <span class="tag">멘토십</span>
        <span class="tag">직관력</span>
        <span class="tag">분석력</span>
        <span class="tag">끈기</span>
        <span class="tag">섬세함</span>
        <span class="tag">창의융합</span>
        <span class="tag">실행력</span>
        <span class="tag">공감력</span>
        <span class="tag">학습력</span>
        <span class="tag">리더십</span>
      </div>
    </div>
  </div>
</div>

<!-- 중앙 3단 -->
<div class="mid">
  <div class="mid-left">
    <div class="card" style="flex:1">
      <h3>{svg_bulb} 丁亥 일주 핵심 특성</h3>
      <ul>
        <li>&middot; <b>촛불의 집중력</b> (丁火)<br><span style="font-size:9px;color:#8a7a68">은은하지만 꺼지지 않는 불. 한 가지에 깊이 몰입하고 본질을 꿰뚫는 통찰력이 있다.</span></li>
        <li>&middot; <b>바다의 포용력</b> (亥水)<br><span style="font-size:9px;color:#8a7a68">모든 것을 받아들이는 깊은 물. 사람의 마음을 읽고 감싸주는 능력이 뛰어나다.</span></li>
        <li>&middot; <b>만능 멘토 기질</b><br><span style="font-size:9px;color:#8a7a68">가르치고 이끄는 재능이 타고남. 복잡한 것을 쉽게 풀어주는 능력이 있다.</span></li>
        <li>&middot; <b>아이디어 연결사</b><br><span style="font-size:9px;color:#8a7a68">水生木의 기운으로 새로운 것을 싹틔우고, 火의 열정으로 실행한다.</span></li>
        <li>&middot; <b>직관과 논리의 균형</b><br><span style="font-size:9px;color:#8a7a68">丁의 직관 + 亥의 지혜 = 감각적이면서도 논리적인 판단력.</span></li>
        <li>&middot; <b>실행 중심 (官星 활용)</b><br><span style="font-size:9px;color:#8a7a68">계획에 머무르지 않고 행동으로 옮기며, 작은 성과를 쌓아 큰 변화를 만든다.</span></li>
      </ul>
    </div>
    <div class="card">
      <h3>{svg_rocket} 일을 대하는 방식</h3>
      <p style="font-size:10px;color:#8b4513;font-family:'Gaegu',cursive;margin-bottom:4px">탐구 &#8594; 분석 &#8594; 설계 &#8594; 실행</p>
      <ul>
        <li>&middot; <b>1. 탐구</b> &#8212; 촛불처럼 어둠 속 핵심을 비춘다</li>
        <li>&middot; <b>2. 분석</b> &#8212; 바다처럼 깊이 파고든다</li>
        <li>&middot; <b>3. 설계</b> &#8212; 금(辛) 기운으로 날카롭게 구조화</li>
        <li>&middot; <b>4. 실행</b> &#8212; 결과를 만들어 증명한다</li>
      </ul>
    </div>
  </div>

  <div class="center">
    <div style="position:relative">
      <img class="char-img" src="data:image/png;base64,{char_b64}" />
      <div style="position:absolute;top:6px;left:8px;background:rgba(255,255,255,.75);border-radius:4px;padding:2px 6px;font-size:8px;color:#8b4513;font-family:'Gaegu',cursive">丁亥 &#183; 촛불+바다</div>
    </div>
    <div class="name-area">
      <div class="nm">&#xC11C; &#xC131; &#xC885;</div>
      <div style="font-size:12px;color:#8b4513;font-family:serif">&#x5F90; &#x8056; &#x9418;</div>
      <div class="inf">&#xC815;&#xD574;(&#x4E01;&#x4EA5;) &#xC77C;&#xC8FC; &#183; &#xC2E0;&#xC720;(&#x8F9B;&#x9149;) &#xB300;&#xC6B4; &#183; &#xB9CC;&#xB2A5; &#xBA58;&#xD1A0; &#xC0AC;&#xC8FC;</div>
    </div>
    <div class="goal-review">
      <div class="goal-box">
        <h4>{svg_fire} &#xC624;&#xB298;&#xC758; &#xBAA9;&#xD45C;</h4>
        <p>&#xB9E4;&#xC77C; &#xCD1B;&#xBD88;&#xCC98;&#xB7FC; &#xD55C; &#xAC00;&#xC9C0;&#xC5D0; &#xC9D1;&#xC911;<br>&#xBC29;&#xD5A5; &#xBC1C;&#xACAC; &#x2192; &#xAE4A;&#xC774; &#xD30C;&#xACE0; &#x2192; &#xC2E4;&#xD589;</p>
        <p style="font-size:8px;color:#aaa;margin-top:2px">&#xC791;&#xC740; &#xBD88;&#xBE5B;&#xC774; &#xBAA8;&#xC5EC;<br>&#xD070; &#xBC29;&#xD5A5;&#xC744; &#xBC1D;&#xD78C;&#xB2E4;</p>
      </div>
      <div class="goal-box">
        <h4>{svg_water} &#xB9AC;&#xBDF0; (&#xD558;&#xB8E8; &#xB05D;)</h4>
        <p>&#x2192; &#xBC1C;&#xACAC; &#xB9E4;&#xB2EC;&#xC74C; &#xC815;&#xB9AC;<br>&#x2192; &#xBABB;&#xD55C; &#xC810; &#xC815;&#xC9C1;&#xD558;&#xAC8C;<br>&#x2192; &#xB2E4;&#xC74C; &#xC2E4;&#xD589; &#xCCB4;&#xD06C;</p>
        <p style="font-size:8px;color:#8b4513;margin-top:3px;font-family:'Gaegu',cursive">&#xC791;&#xC740; &#xAC1C;&#xC120;&#xC758; &#xC624;&#xB298;,<br>&#xD559;&#xC2B5;&#xC740; &#xB0B4;&#xC77C;!</p>
      </div>
    </div>
  </div>

  <div class="mid-right">
    <div class="card">
      <h3>{svg_star} &#xC8FC;&#xC694; &#xAC15;&#xC810; (&#xC0AC;&#xC8FC; &#xAE30;&#xBC18;)</h3>
      <ul>
        <li>&middot; &#xC740;&#xC740;&#xD55C; &#xBE5B;&#xC73C;&#xB85C; &#xBC29;&#xD5A5;&#xC744; &#xC81C;&#xC2DC; (&#x4E01;&#xD654;)</li>
        <li>&middot; &#xAE4A;&#xC740; &#xC9C0;&#xD61C;&#xC640; &#xD3EC;&#xC6A9;&#xB825; (&#x4EA5;&#xC218;)</li>
        <li>&middot; &#xAFC0;&#xC900;&#xD55C; &#xC2E4;&#xD589;&#xB825;&#xACFC; &#xACB0;&#xC2E4; (&#x8F9B;&#x9149; &#xB300;&#xC6B4;)</li>
        <li>&middot; &#xACF5;&#xAC10; &#xAE30;&#xBC18; &#xBA58;&#xD1A0;&#xD615; &#xB9AC;&#xB354;&#xC2ED;</li>
        <li>&middot; &#xB192;&#xC740; &#xCC45;&#xC784;&#xAC10;&#xACFC; &#xC2E0;&#xB8B0; &#xAD6C;&#xCD95;&#xB825;</li>
        <li>&middot; &#xB2E4;&#xC7AC;&#xB2E4;&#xB2A5; &#x2014; &#xAE30;&#xC220;&#xB7A5;&#xAD00;&#xB9AC;&#xB7A5;&#xC18C;&#xD1B5; &#xAC78;&#xCE68;</li>
      </ul>
    </div>
    <div class="card">
      <h3>{svg_heart} &#xAC00;&#xCE58;&#xAD00; (&#x4E01;&#xD654;&#xC758; &#xB530;&#xB73B;&#xD568;)</h3>
      <ul>
        <li>&middot; &#xC0AC;&#xB78C;&#xC744; &#xBA3C;&#xC800; &#xC0DD;&#xAC01;&#xD55C;&#xB2E4; (&#x4E01;&#xD654;&#xC758; &#xBE5B;)</li>
        <li>&middot; &#xC9C0;&#xC18D;&#xC801;&#xC778; &#xC131;&#xC7A5;&#xC744; &#xCD94;&#xAD6C; (&#x4EA5;&#xC218;&#xC758; &#xD750;&#xB984;)</li>
        <li>&middot; &#xC2E0;&#xC2E4;&#xACFC; &#xC815;&#xC9C1;&#xC744; &#xC911;&#xC694;&#xC2DC; (&#x8F9B;&#xAE08;&#xC758; &#xACB0;&#xB2E8;)</li>
        <li>&middot; &#xC758;&#xBBF8; &#xC788;&#xB294; &#xACB0;&#xACFC;&#xB97C; &#xB9CC;&#xB4E0;&#xB2E4;</li>
        <li>&middot; &#xAC00;&#xC871;&#xACFC; &#xC0B6;&#xC758; &#xADE0;&#xD615;&#xC744; &#xC18C;&#xC911;&#xD788;</li>
      </ul>
    </div>
    <div class="card">
      <h3>{svg_fire}{svg_water} &#xC0AC;&#xC8FC; &#xC5D0;&#xB108;&#xC9C0; &#xC694;&#xC57D;</h3>
      <ul>
        <li>&middot; <b>&#x4E01;&#xD654;(&#xC815;&#xD654;)</b> &#x2014; &#xCD1B;&#xBD88;&#xC758; &#xC9D1;&#xC911;&#xACFC; &#xB530;&#xB73B;&#xD568;</li>
        <li>&middot; <b>&#x4EA5;&#xC218;(&#xD574;&#xC218;)</b> &#x2014; &#xAE4A;&#xC740; &#xBC14;&#xB2E4;&#xC758; &#xC9C0;&#xD61C;&#xC640; &#xD3EC;&#xC6A9;</li>
        <li>&middot; <b>&#xC2E0;&#xC720; &#xB300;&#xC6B4;</b> &#x2014; &#xAE08;(&#x91D1;) &#xAE30;&#xC6B4;, &#xACB0;&#xC2E4;&#xACFC; &#xC815;&#xB9AC;</li>
        <li>&middot; <b>&#xB9CC;&#xB2A5; &#xBA58;&#xD1A0;</b> &#x2014; &#xB2E4;&#xC7AC;&#xB2E4;&#xB2A5;, &#xAC00;&#xB974;&#xCE68;&#xC758; &#xC7AC;&#xB2A5;</li>
      </ul>
      <p style="font-size:8px;color:#8a7a68;margin-top:3px">&#xCD1B;&#xBD88;&#xC774; &#xAE4A;&#xC740; &#xBC14;&#xB2E4; &#xC704;&#xC5D0; &#xB5A0; &#xC788;&#xB294; &#xD615;&#xC0C1; &#x2014;<br>&#xC5B4;&#xB460; &#xC18D;&#xC5D0;&#xC11C;&#xB3C4; &#xBC29;&#xD5A5;&#xC744; &#xC81C;&#xC2DC;&#xD558;&#xB294; &#xB4F1;&#xB300;</p>
    </div>
  </div>
</div>

<!-- 하단 4칸 -->
<div class="bottom">
  <div class="btm-card">
    <h4>{svg_rocket} &#xB098;&#xB97C; &#xC6C0;&#xC9C1;&#xC774;&#xAC8C; &#xD558;&#xB294; &#xAC83;</h4>
    <ul>
      <li>&middot; &#xBCF5;&#xC7A1;&#xD55C; &#xBB38;&#xC81C;&#xB97C; &#xCD1B;&#xBD88;&#xCC98;&#xB7FC; &#xBC1D;&#xD788;&#xB294; &#xCF8C;&#xAC10;</li>
      <li>&middot; &#xBC30;&#xC6C0;&#xC744; &#xC2E4;&#xC81C; &#xACB0;&#xACFC;&#xB85C; &#xC5F0;&#xACB0;&#xD558;&#xB294; &#xAC83;</li>
      <li>&middot; AI&#xC640; &#xD611;&#xC5C5;&#xD558;&#xC5EC; &#xB354; &#xB098;&#xC740; &#xACB0;&#xACFC;</li>
      <li>&middot; &#xC9C0;&#xC18D;&#xC801;&#xC73C;&#xB85C; &#xC131;&#xC7A5;&#xD558;&#xBA70; &#xAE30;&#xC5EC;&#xD558;&#xB294; &#xAC83;</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{svg_heart} &#xBBF8;&#xB798;&#xC5D0; &#xC774;&#xB8E8;&#xACE0; &#xC2F6;&#xC740; &#xAC83;</h4>
    <ul>
      <li>&middot; &#xB3C5;&#xB9BD;&#xC801;&#xC774;&#xACE0; &#xC8FC;&#xB3C4;&#xC801;&#xC778; &#xC804;&#xBB38;&#xAC00;</li>
      <li>&middot; &#xC2A4;&#xC2A4;&#xB85C; &#xD310;&#xB2E8;&#xD558;&#xACE0; &#xCC45;&#xC784;&#xC9C0;&#xBA70;</li>
      <li>&middot; &#xB05D;&#xAE4C;&#xC9C0; &#xACB0;&#xACFC;&#xB97C; &#xB9CC;&#xB4E4;&#xC5B4;&#xB0B8;&#xB2E4;</li>
    </ul>
    <p style="font-size:8px;color:#8a7a68;margin-top:3px">&#xC0AC;&#xB78C;&#xC744; &#xC18C;&#xC911;&#xD788; &#xC5EC;&#xAE30;&#xB294; &#xAD00;&#xACC4; &#xC911;&#xC2EC;<br>&#xC9C4;&#xC2E4;&#xACFC; &#xC2E0;&#xB8B0;&#xB97C; &#xD1B5;&#xD574; &#xC131;&#xC7A5;</p>
  </div>
  <div class="btm-card">
    <h4>{svg_plant} &#xB098;&#xC758; &#xAC00;&#xB2A5;&#xC131;</h4>
    <ul>
      <li>&middot; &#xCD1B;&#xBD88;&#xCC98;&#xB7FC; &#xC5B4;&#xB460;&#xC744; &#xBC1D;&#xD788;&#xB294; &#xC9C0;&#xD61C;</li>
      <li>&middot; &#xBD84;&#xC11D;&#xB825;&#xACFC; &#xC2E4;&#xD589;&#xB825;&#xC744; &#xAC96;&#xCDA4; &#xC804;&#xBB38;&#xAC00;</li>
      <li>&middot; &#xAE30;&#xC220;&#xACFC; &#xAC10;&#xC131;&#xC744; &#xC5F0;&#xACB0;&#xD558;&#xB294; &#xC735;&#xD569;&#xB825;</li>
    </ul>
    <p style="font-size:8px;color:#8a7a68;margin-top:3px">&#xBA58;&#xD1A0;&#xB85C;&#xC11C; &#xC0AC;&#xB78C;&#xC744; &#xC131;&#xC7A5;&#xC2DC;&#xD0A4;&#xB294; &#xD798;&#xC744;<br>&#xB9CC;&#xB4E4;&#xC5B4;&#xB0BC; &#xC218; &#xC788;&#xB2E4;!</p>
  </div>
  <div class="btm-card">
    <h4>{svg_check} &#xC778;&#xC0DD; &#xCCB4;&#xD06C;&#xB9AC;&#xC2A4;&#xD2B8;</h4>
    <ul>
      <li>&#x25A1; &#xC804;&#xBB38;&#xC131; &#xAC15;&#xD654;</li>
      <li>&#x25A1; &#xAC74;&#xAC15; &#xAD00;&#xB9AC;</li>
      <li>&#x25A1; &#xC601;&#xD5A5;&#xB825; &#xD655;&#xC7A5;</li>
      <li>&#x25A1; &#xC5ED;&#xD560; &#xC218;&#xD589;</li>
      <li>&#x25A1; &#xAC00;&#xC871;&#xACFC; &#xC2DC;&#xAC04;</li>
      <li>&#x25A1; &#xC7AC;&#xD14C;&#xD06C; &#xC548;&#xC815;</li>
    </ul>
  </div>
</div>

</body></html>'''

(DIR / "ssj-infographic.html").write_text(html, encoding="utf-8")

from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page(viewport={"width":850,"height":1100})
    pg.goto((DIR / "ssj-infographic.html").as_uri())
    pg.wait_for_timeout(3000)
    pg.screenshot(path=str(DIR / "ssj-summary.jpg"), full_page=False, type="jpeg", quality=95)
    br.close()
print("Done!")
