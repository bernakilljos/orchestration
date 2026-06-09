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
 'compass':'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#c4915a" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M16.24 7.76l-2.12 6.36-6.36 2.12 2.12-6.36z" fill="rgba(196,145,90,.2)"/></svg>',
 'target':'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#e07a2f" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2" fill="#e07a2f"/></svg>',
 'clock':'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#8b7355" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
 'medal':'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#e8c36a" stroke-width="1.5"><circle cx="12" cy="8" r="5" fill="rgba(232,195,106,.12)"/><path d="M8.21 13.89L7 23l5-3 5 3-1.21-9.12"/></svg>',
 'mountain':'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#6b8e5a" stroke-width="1.5"><path d="M4 20l4-10 3 4 5-8 4 14z" fill="rgba(107,142,90,.08)"/></svg>',
 'lamp':'<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#c4915a" stroke-width="1.5"><path d="M9 18h6M10 22h4"/><circle cx="12" cy="9" r="5" fill="rgba(240,192,64,.12)"/><path d="M12 2v2"/></svg>',
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
  --color-card:rgba(252,244,228,.55);
  --color-card-dim:rgba(252,244,228,.45);
  --color-tag-bg:rgba(196,145,90,.18);
  --color-tag-border:rgba(196,145,90,.4);
  --color-tag-text:#7a5a3a;
  --gap-section:1px;
  --gap-card:1px;
  --gap-tag:2px;
  --pad-card:3px 5px;
  --pad-btm:3px 4px;
  --radius-card:5px;
  --radius-tag:8px;
  --font-h3:12px;
  --font-body-size:9px;
  --font-small:8px;
  --font-tag:8.5px;
  --line-height:1.4;
  --shadow-card:1px 2px 6px rgba(0,0,0,.05)
}
/* === BASE === */
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@300;400;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
body{font-family:var(--font-body);overflow:hidden;color:var(--color-text)}
/* === CARD SYSTEM === */
.card{background:var(--color-card);border:1.2px solid var(--color-border);border-radius:var(--radius-card);padding:var(--pad-card);box-shadow:none;overflow:hidden}
.card h3{font-family:var(--font-title);font-size:var(--font-h3);font-weight:700;color:var(--color-accent);margin-bottom:2px;border-bottom:1px solid rgba(180,150,120,.25);padding-bottom:1px;display:flex;align-items:center;gap:var(--gap-tag)}
.auto-badge{font-family:'Gaegu',cursive;font-size:9px;font-weight:700;color:#fff;background:#c4915a;padding:0 5px;border-radius:8px;margin-left:auto}
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
body{{width:850px;height:1100px;background:#efe7d6;
  background-image:radial-gradient(ellipse at 15% 85%,rgba(196,145,90,.14) 0%,transparent 55%),
  radial-gradient(ellipse at 85% 15%,rgba(139,69,19,.10) 0%,transparent 45%),
  radial-gradient(circle at 50% 50%,rgba(180,160,130,.08) 0%,transparent 70%);
  padding:3px 4px;display:flex;flex-direction:column;justify-content:flex-start;gap:1px;overflow:hidden}}
.header{{display:flex;justify-content:space-between;align-items:flex-start;flex-shrink:0}}
.header-left h1{{font-family:'Gaegu',cursive;font-size:26px;font-weight:700;color:#2c2418;line-height:1.22}}
.header-left .sub{{font-size:11px;color:#7a6b5a;margin-top:3px;display:flex;align-items:center;gap:4px}}
.header-right{{display:flex;gap:6px;max-width:360px}}
.mid{{display:grid;grid-template-columns:230px 1fr 230px;gap:1px;flex:1 1 auto;margin:1px 0;min-height:0}}
.mid-left,.mid-right{{display:flex;flex-direction:column;gap:1px;justify-content:space-between;min-height:0}}
.mid-left .card,.mid-right .card{{flex:1 1 auto;display:flex;flex-direction:column;min-height:0}}
.mid-left .card ul,.mid-right .card ul,.mid-left .card .tags,.mid-right .card .tags{{flex:1 1 auto;display:flex;flex-direction:column;justify-content:space-around}}
.mid-left .card .tags,.mid-right .card .tags{{flex-direction:row;flex-wrap:wrap;align-content:space-around}}
.center{{display:flex;flex-direction:column;align-items:center;justify-content:space-between;gap:5px;padding:3px 0;min-height:0}}
.photo{{width:100%;max-width:300px;height:180px;border-radius:10px;object-fit:cover;border:2.5px solid #c4b49a;flex-shrink:0}}
.name-area{{text-align:center;flex-shrink:0}}
.name-area .nm{{font-family:'Gaegu',cursive;font-size:22px;font-weight:700;color:#2c2418}}
.name-area .inf{{font-size:9px;color:#8a7a68;margin-top:1px}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:3px;width:100%;flex-shrink:0}}
.stat{{background:rgba(252,244,228,.55);border:1.2px solid #d4c4a8;border-radius:5px;padding:4px;text-align:center}}
.stat .n{{font-family:'Gaegu',cursive;font-size:18px;font-weight:700;color:#8b4513;line-height:1;display:flex;align-items:center;justify-content:center;height:22px}}
.stat .l{{font-size:8px;color:#7a6b5a;line-height:1.3;margin-top:2px}}
.bottom{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;flex-shrink:0}}
.btm-card{{background:rgba(252,244,228,.4);border:1.2px solid #d4c4a8;border-radius:5px;padding:3px 5px;display:flex;flex-direction:column;overflow:hidden}}
.btm-card ul{{flex:1 1 auto;display:flex;flex-direction:column;justify-content:space-around;list-style:none;padding:0}}
.btm-card h4{{font-family:'Gaegu',cursive;font-size:11px;color:#8b4513;margin-bottom:3px;display:flex;align-items:center;gap:3px}}
.btm-card li{{font-size:9px;line-height:1.5;color:#5a4f42}}
</style></head><body>

<div class="header">
  <div class="header-left">
    <h1>혼자 다 하지 마,<br>AI 네 명이 한 팀이 되어<br>당신 옆에 있다</h1>
    <div class="sub">{I['cpu']} orchestration_v1 — Claude + Codex + Gemini 멀티AI 킷</div>
  </div>
  <div class="header-right">
    <div class="card" style="width:160px">
      <h3>{I['lamp']} 당신의 한 마디</h3>
      <ul>
        <li>&middot; 음성으로 부탁하면 — 받는다</li>
        <li>&middot; 한 줄 텍스트로도 — 답이 온다</li>
        <li>&middot; 이미지·PDF 던지면 — 풀린다</li>
        <li>&middot; 폴더 통째로 줘도 — 정리된다</li>
      </ul>
    </div>
    <div class="card" style="width:185px">
      <h3>{I['star']} 당신에게 오는 것</h3>
      <div class="tags">
        <span class="tag">보고서</span><span class="tag">발표자료</span><span class="tag">제안서</span>
        <span class="tag">분석표</span><span class="tag">홈페이지</span><span class="tag">랜딩</span>
        <span class="tag">그림</span><span class="tag">영상</span><span class="tag">노래</span>
        <span class="tag">자막</span><span class="tag">번역</span><span class="tag">코드</span>
      </div>
    </div>
  </div>
</div>

<div class="mid">
  <div class="mid-left">
    <div class="card">
      <h3>{I['heart']} AI 네 형제가 한 팀</h3>
      <ul>
        <li>&middot; <b>Claude</b> — 머리, 설계와 판단</li>
        <li>&middot; <b>Codex</b> — 손, 코드·문서 만든다</li>
        <li>&middot; <b>Haiku</b> — 눈, 잘못된 곳 잡는다</li>
        <li>&middot; <b>Gemini</b> — 발, 멀리까지 본다</li>
        <li>&middot; 4 명이 한 명처럼 움직인다</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['shield']} ChatGPT 와 다른 점</h3>
      <ul>
        <li>&middot; 답만 주지 않는다 — 만들어 준다</li>
        <li>&middot; 한 번 묻고 끝 아니다</li>
        <li>&middot; AI 가 AI 를 검토한다</li>
        <li>&middot; 결과까지 책임진다</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['code']} Cursor·Copilot 과 다른 점</h3>
      <ul>
        <li>&middot; 코드만 아니다 — 모든 산출물</li>
        <li>&middot; 음성·이미지·영상까지 입력</li>
        <li>&middot; IDE 없어도 된다</li>
        <li>&middot; 무료, 무제한, 영원</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['star']} Gamma·Canva 와 다른 점</h3>
      <ul>
        <li>&middot; PPT·디자인만 아니다</li>
        <li>&middot; 코드·영상·음악·문서까지</li>
        <li>&middot; 한 도구로 모든 산출물</li>
        <li>&middot; 산출물끼리 연동 자동</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['cpu']} 잠도 일한다</h3>
      <ul>
        <li>&middot; 자는 동안에도 만든다</li>
        <li>&middot; 24 시간 무인 운영</li>
        <li>&middot; 출근 전 산출물 도착</li>
        <li>&middot; VPS · tmux · watchdog</li>
        <li>&middot; 폰으로도 명령 가능</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['compass']} 잘못 되면 알아서 잡는다</h3>
      <ul>
        <li>&middot; 빌드 후 자가 점검 자동</li>
        <li>&middot; 잘림·여백·오타 잡는다</li>
        <li>&middot; 실패 시 최대 3회 재시도</li>
        <li>&middot; 검토 없이 완료 보고 X</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['target']} 위험은 사람 손에</h3>
      <ul>
        <li>&middot; 삭제·배포 등 위험 명령 차단</li>
        <li>&middot; HITL 사전 승인 게이트</li>
        <li>&middot; 시크릿 commit 차단</li>
        <li>&middot; 보안 25 패턴 사전 막음</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['plant']} 비싸지면 알아서 줄인다</h3>
      <ul>
        <li>&middot; 일일 비용 상한 자동 fallback</li>
        <li>&middot; Quota 초과 지수 backoff</li>
        <li>&middot; 비싼 모델 안 써도 되면 안 쓴다</li>
        <li>&middot; Prompt 캐싱 90% 절감</li>
        <li>&middot; 무료 시작, 영원 오픈소스</li>
      </ul>
    </div>
  </div>

  <div class="center">
    <div style="position:relative">
      <img class="photo" src="data:image/png;base64,{orch_b64}" />
      <div style="position:absolute;top:6px;left:8px;background:rgba(255,255,255,.85);border-radius:4px;padding:2px 6px;font-size:9px;color:#8b4513;font-family:'Gaegu',cursive">주제 → AI → 산출물</div>
    </div>
    <div class="name-area">
      <div class="nm">orchestration_v1</div>
      <div style="font-size:11px;color:#8b4513;font-family:serif">"주제만 던지면 만들어 준다"</div>
      <div class="inf">음성·텍스트·이미지·PDF 어떤 입력도 OK</div>
    </div>
    <div class="stats">
      <div class="stat"><div class="n">{I['cpu']}</div><div class="l"><b>입력</b><br>음성·텍스트<br>이미지·PDF</div></div>
      <div class="stat"><div class="n">{I['gear']}</div><div class="l"><b>처리</b><br>Claude·Codex<br>Haiku·Gemini</div></div>
      <div class="stat"><div class="n">{I['star']}</div><div class="l"><b>출력</b><br>모든 산출물<br>한 번에</div></div>
    </div>
    <div class="card" style="padding:5px 7px;margin-top:2px">
      <h3 style="font-size:10px;border:none;padding:0;margin-bottom:3px">{I['rocket']} 어떻게 쓰나</h3>
      <div style="font-size:9px;color:#5a4f42;line-height:1.5">
        · <b>1. 던지기</b> — "주제 X 로 PPT 만들어줘"<br>
        · <b>2. AI 처리</b> — Claude → Codex → Haiku 자동 분배<br>
        · <b>3. 받기</b> — pptx·docx·mp4·jpg 산출물<br>
        · <b>4. 자가 점검</b> — 잘림·여백·오타 자동 잡음<br>
        · <b>5. 다듬어진 결과</b> — 사용자는 그냥 받기만
      </div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:2px;width:100%;margin-top:2px">
      <div class="card" style="padding:4px 5px">
        <h3 style="font-size:9px;margin-bottom:2px;border:none;padding:0">{I['cpu']} 입력</h3>
        <div style="font-size:8px;color:#5a4f42;line-height:1.45">
          · 음성 (mp3/wav)<br>
          · 텍스트 한 줄<br>
          · 이미지·PDF<br>
          · 영상·폴더
        </div>
      </div>
      <div class="card" style="padding:4px 5px">
        <h3 style="font-size:9px;margin-bottom:2px;border:none;padding:0">{I['gear']} 처리</h3>
        <div style="font-size:8px;color:#5a4f42;line-height:1.45">
          · Claude (설계)<br>
          · Codex (구현)<br>
          · Haiku (점검)<br>
          · Gemini (장문)
        </div>
      </div>
      <div class="card" style="padding:4px 5px">
        <h3 style="font-size:9px;margin-bottom:2px;border:none;padding:0">{I['star']} 출력</h3>
        <div style="font-size:8px;color:#5a4f42;line-height:1.45">
          · pptx·docx·pdf<br>
          · mp4·mp3·jpg<br>
          · html·xlsx<br>
          · 코드·테스트
        </div>
      </div>
    </div>
    <div class="card" style="padding:5px 7px;margin-top:2px">
      <h3 style="font-size:10px;border:none;padding:0;margin-bottom:3px">{I['bulb']} 실제 사용 예</h3>
      <div style="font-size:9px;color:#5a4f42;line-height:1.5">
        · "회의 녹음 mp3 보내" → 회의록·요약·할 일<br>
        · "이 영상" → 쇼츠 + 자막 + 썸네일<br>
        · "RFP PDF 보내" → 제안서 PPT<br>
        · "이 사진 흐려" → 4K 초해상도 복원<br>
        · "월간 매출 csv" → Excel·차트·분석 보고
      </div>
    </div>
    <div style="background:rgba(196,145,90,.18);border:1px dashed #c4915a;border-radius:5px;padding:5px 7px;margin-top:2px;text-align:center">
      <div style="font-family:'Gaegu',cursive;font-size:14px;color:#8b4513;font-weight:700">"주제만 던져라"</div>
      <div style="font-size:10px;color:#5a4f42;margin-top:2px;line-height:1.5;font-weight:700">
        세부 지시 없이도 알아서 자동으로<br>
        무료·오픈소스·24/7 무인 운영
      </div>
    </div>
  </div>

  <div class="mid-right">
    <div class="card">
      <h3>{I['star']} 이런 분께 좋다</h3>
      <ul>
        <li>&middot; 자료 만들기에 지친 분</li>
        <li>&middot; 매번 같은 보고서 반복하는 분</li>
        <li>&middot; AI 어떻게 쓸지 모르는 분</li>
        <li>&middot; 혼자 너무 많은 걸 하는 분</li>
        <li>&middot; 빨리 결과가 필요한 분</li>
        <li>&middot; 디자인·코딩이 어려운 분</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['bulb']} 이런 주제가 잘 풀린다</h3>
      <ul>
        <li>&middot; 보고서·제안서·기획서</li>
        <li>&middot; 교육 자료·교재·강의 노트</li>
        <li>&middot; 마케팅·랜딩·SNS 콘텐츠</li>
        <li>&middot; 분석·데이터·차트·통계</li>
        <li>&middot; 영상 편집·쇼츠·자막</li>
        <li>&middot; 이미지·디자인·인포그래픽</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['rocket']} 일은 이렇게 흐른다</h3>
      <ul>
        <li>&middot; 던지면 — Claude 가 풀어 본다</li>
        <li>&middot; 풀리면 — Codex 가 만든다</li>
        <li>&middot; 만들면 — Haiku 가 살펴 본다</li>
        <li>&middot; 살펴 본 뒤 — 다듬어 보낸다</li>
        <li>&middot; 사람은 — 받기만 하면 된다</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['shield']} 약속하는 것</h3>
      <ul>
        <li>&middot; 검토 없이 완료 보고는 없다</li>
        <li>&middot; 잘림·여백·오타는 자동으로 잡힌다</li>
        <li>&middot; 위험한 일은 사람 손에 묻는다</li>
        <li>&middot; 비싸지면 알아서 줄인다</li>
        <li>&middot; 시크릿은 결코 새지 않는다</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['plant']} 점점 커지는 것</h3>
      <ul>
        <li>&middot; 매주 새 도구가 들어 온다</li>
        <li>&middot; 사용한 만큼 똑똑해진다</li>
        <li>&middot; 실패는 학습으로 쌓인다</li>
        <li>&middot; 32 → 50 → 100 플러그인</li>
        <li>&middot; 무료·오픈소스 영원</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['heart']} 이어지는 인연</h3>
      <ul>
        <li>&middot; Slack · Notion · Jira</li>
        <li>&middot; Gmail · Google · YouTube</li>
        <li>&middot; Figma · Canva · Gamma</li>
        <li>&middot; GitHub · Vercel · Firebase</li>
        <li>&middot; MySQL · BigQuery · MongoDB</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['compass']} 시작은 한 줄로</h3>
      <ul>
        <li>&middot; <b>1.</b> 깃 클론 한 줄</li>
        <li>&middot; <b>2.</b> install.sh 한 번</li>
        <li>&middot; <b>3.</b> Claude Code 켜기</li>
        <li>&middot; <b>4.</b> 주제만 던지기</li>
        <li>&middot; 그 다음은 — 받기만</li>
      </ul>
    </div>
  </div>
</div>

<div class="bottom">
  <div class="btm-card">
    <h4>{I['cpu']} 받는 입력</h4>
    <ul>
      <li>&middot; 음성 (mp3·wav·m4a)</li>
      <li>&middot; 텍스트 한 줄 ("주제 X")</li>
      <li>&middot; 이미지·스크린샷</li>
      <li>&middot; PDF·docx·xlsx</li>
      <li>&middot; 영상 파일·YT 링크</li>
      <li>&middot; 회사 자료 폴더</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['star']} 내보내는 출력</h4>
    <ul>
      <li>&middot; PPT (pptx)·Google Slides</li>
      <li>&middot; Word (docx)·PDF</li>
      <li>&middot; Excel (xlsx)·Sheets</li>
      <li>&middot; 영상 (mp4)·쇼츠·자막</li>
      <li>&middot; 이미지 (jpg·png·SVG)</li>
      <li>&middot; 음악·오디오 (mp3·wav)</li>
      <li>&middot; 웹사이트 (HTML)</li>
      <li>&middot; 코드·테스트·문서</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['gear']} 작동 환경</h4>
    <ul>
      <li>&middot; Windows·macOS·Linux</li>
      <li>&middot; 로컬 PC 한 줄 install</li>
      <li>&middot; VPS 24/7 무인 운영</li>
      <li>&middot; Oracle Free Tier 가능</li>
      <li>&middot; 스마트폰 SSH 접속</li>
      <li>&middot; 오프라인 모드 (Ollama)</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['water']} 연결되는 도구</h4>
    <ul>
      <li>&middot; Slack·Notion·Jira·Trello</li>
      <li>&middot; Gmail·Google Calendar</li>
      <li>&middot; YouTube·Instagram</li>
      <li>&middot; Figma·Canva·Gamma</li>
      <li>&middot; GitHub·Vercel·Firebase</li>
      <li>&middot; MySQL·BigQuery·MongoDB</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['compass']} 자동 안전장치</h4>
    <ul>
      <li>&middot; 위험 명령 사전 승인 (HITL)</li>
      <li>&middot; 보안 25 패턴 자동 차단</li>
      <li>&middot; 일일 비용 상한 자동 fallback</li>
      <li>&middot; Quota 초과 지수 backoff</li>
      <li>&middot; 빌드 후 자동 자가 점검</li>
      <li>&middot; 시크릿 commit 차단</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['rocket']} 시작하기</h4>
    <ul>
      <li>&middot; <b>1.</b> 깃 클론 한 줄</li>
      <li>&middot; <b>2.</b> install.sh 실행</li>
      <li>&middot; <b>3.</b> Claude Code 켜기</li>
      <li>&middot; <b>4.</b> "주제 X" 던지기</li>
      <li>&middot; 사용자 액션 0 (Zero-touch)</li>
      <li>&middot; 무료·오픈소스</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['fire']} AI 엔진</h4>
    <ul>
      <li>&middot; Claude Opus 4.8 (설계)</li>
      <li>&middot; Claude Sonnet 4.6 (구현)</li>
      <li>&middot; Codex (코드 500줄+)</li>
      <li>&middot; Haiku 4.5 (점검)</li>
      <li>&middot; Gemini Flash (장문)</li>
      <li>&middot; Whisper (음성→텍스트)</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['plant']} 사용하면 일어나는 일</h4>
    <ul>
      <li>&middot; 야근이 줄어 든다</li>
      <li>&middot; 보고서 두려움이 사라진다</li>
      <li>&middot; 진짜 중요한 일에 집중한다</li>
      <li>&middot; 잠을 더 잘 수 있다</li>
      <li>&middot; 자료 만들기 스트레스 0</li>
      <li>&middot; 같은 일 두 번 안 한다</li>
    </ul>
  </div>
</div>

</body></html>'''


# ===================== SSJ-SUMMARY (타겟.jpg 손그림 + 고밀도 하이브리드) =====================
def build_ssj_summary():
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
{COMMON_CSS}
body{{width:990px;height:1320px;background:#f5efe6;
  background-image:radial-gradient(ellipse at 15% 85%,rgba(210,180,140,.10) 0%,transparent 50%),
  radial-gradient(ellipse at 85% 15%,rgba(180,160,130,.06) 0%,transparent 40%);
  padding:5px;display:flex;flex-direction:column;gap:4px;overflow:hidden}}
.header{{display:flex;justify-content:space-between;align-items:flex-start}}
.header-left h1{{font-family:'Gaegu',cursive;font-size:26px;font-weight:700;color:#2c2418;line-height:1.15}}
.header-left .sub{{font-size:10px;color:#7a6b5a;margin-top:2px;display:flex;align-items:center;gap:3px}}
.header-right{{display:flex;gap:3px}}
.mid{{display:grid;grid-template-columns:240px 1fr 235px;gap:3px;flex:1 1 0;min-height:0;overflow:hidden}}
.mid-left,.mid-right{{display:flex;flex-direction:column;gap:3px;min-height:0;overflow:hidden}}
.center{{display:flex;flex-direction:column;align-items:center;gap:3px;min-height:0;overflow:hidden}}
.mid-right>.card{{flex:1 1 0;min-height:0}}
.svg-deco{{flex:1 1 0;min-height:60px;background:rgba(255,255,255,.45);border:1.5px solid #d4c4a8;border-radius:5px;padding:4px;display:flex;align-items:stretch;justify-content:center;box-shadow:1px 2px 6px rgba(0,0,0,.05);overflow:hidden}}
.svg-deco svg{{width:100%;height:100%;display:block}}
.center .quote:last-child{{margin-top:auto}}
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
.bottom{{display:grid;grid-template-columns:repeat(4,1fr);gap:3px;align-items:stretch}}
.btm-card{{background:rgba(255,255,255,.4);border:1.5px solid #d4c4a8;border-radius:4px;padding:3px 5px 4px;display:flex;flex-direction:column}}
.btm-card h4{{font-family:'Gaegu',cursive;font-size:10px;color:#8b4513;margin-bottom:2px;display:flex;align-items:center;gap:2px}}
.btm-card li{{font-size:8.5px;line-height:1.3;color:#5a4f42;display:flex;align-items:flex-start;gap:3px;margin-bottom:0}}
.btm-card li svg{{flex-shrink:0;margin-top:1px;width:11px;height:11px}}
.btm-card ul{{list-style:none;padding:0;margin:0}}
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
    <div class="svg-deco">
      <svg viewBox="0 0 240 290" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
        <defs>
          <radialGradient id="glow" cx="50%" cy="38%">
            <stop offset="0%" stop-color="#f0c040" stop-opacity=".65"/>
            <stop offset="60%" stop-color="#f0c040" stop-opacity=".15"/>
            <stop offset="100%" stop-color="#f0c040" stop-opacity="0"/>
          </radialGradient>
          <radialGradient id="halo" cx="50%" cy="35%">
            <stop offset="0%" stop-color="#fff4d4" stop-opacity=".5"/>
            <stop offset="100%" stop-color="#fff4d4" stop-opacity="0"/>
          </radialGradient>
          <linearGradient id="candle-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#d4a570"/>
            <stop offset="100%" stop-color="#a87a48"/>
          </linearGradient>
          <linearGradient id="ground-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#c4915a" stop-opacity=".25"/>
            <stop offset="100%" stop-color="#c4915a" stop-opacity="0"/>
          </linearGradient>
        </defs>
        <!-- 배경 halo + glow -->
        <ellipse cx="120" cy="105" rx="130" ry="110" fill="url(#halo)"/>
        <circle cx="120" cy="115" r="92" fill="url(#glow)"/>
        <!-- 좌측 식물 (3개 줄기) -->
        <path d="M28 230 Q26 165 22 105" stroke="#6b8e5a" stroke-width="2.5" fill="none" opacity=".7"/>
        <ellipse cx="14" cy="125" rx="14" ry="5" fill="#6b8e5a" opacity=".55" transform="rotate(-35 14 125)"/>
        <ellipse cx="32" cy="160" rx="13" ry="4.5" fill="#6b8e5a" opacity=".55" transform="rotate(25 32 160)"/>
        <ellipse cx="10" cy="175" rx="11" ry="4" fill="#6b8e5a" opacity=".45" transform="rotate(-45 10 175)"/>
        <ellipse cx="34" cy="200" rx="10" ry="4" fill="#6b8e5a" opacity=".5" transform="rotate(15 34 200)"/>
        <path d="M50 230 Q48 190 50 165" stroke="#6b8e5a" stroke-width="2" fill="none" opacity=".55"/>
        <ellipse cx="44" cy="190" rx="8" ry="3" fill="#6b8e5a" opacity=".45" transform="rotate(-25 44 190)"/>
        <ellipse cx="56" cy="175" rx="7" ry="3" fill="#6b8e5a" opacity=".4" transform="rotate(30 56 175)"/>
        <!-- 우측 식물 -->
        <path d="M212 230 Q214 165 218 105" stroke="#6b8e5a" stroke-width="2.5" fill="none" opacity=".7"/>
        <ellipse cx="226" cy="125" rx="14" ry="5" fill="#6b8e5a" opacity=".55" transform="rotate(35 226 125)"/>
        <ellipse cx="208" cy="160" rx="13" ry="4.5" fill="#6b8e5a" opacity=".55" transform="rotate(-25 208 160)"/>
        <ellipse cx="230" cy="175" rx="11" ry="4" fill="#6b8e5a" opacity=".45" transform="rotate(45 230 175)"/>
        <ellipse cx="206" cy="200" rx="10" ry="4" fill="#6b8e5a" opacity=".5" transform="rotate(-15 206 200)"/>
        <path d="M190 230 Q192 190 190 165" stroke="#6b8e5a" stroke-width="2" fill="none" opacity=".55"/>
        <ellipse cx="196" cy="190" rx="8" ry="3" fill="#6b8e5a" opacity=".45" transform="rotate(25 196 190)"/>
        <ellipse cx="184" cy="175" rx="7" ry="3" fill="#6b8e5a" opacity=".4" transform="rotate(-30 184 175)"/>
        <!-- 바닥 그라데이션 -->
        <rect x="0" y="218" width="240" height="20" fill="url(#ground-grad)"/>
        <ellipse cx="120" cy="218" rx="46" ry="7" fill="#8b7355" opacity=".4"/>
        <!-- 촛불 받침 + 본체 + 심지 + 불꽃 -->
        <ellipse cx="120" cy="222" rx="34" ry="4" fill="#a87a48" opacity=".7"/>
        <rect x="96" y="140" width="48" height="82" rx="4" fill="url(#candle-grad)"/>
        <rect x="96" y="140" width="48" height="7" fill="#8b6035" opacity=".6"/>
        <path d="M96 150 Q120 156 144 150" stroke="#8b6035" stroke-width="1" fill="none" opacity=".4"/>
        <rect x="118" y="126" width="4" height="16" fill="#3a3226"/>
        <ellipse cx="120" cy="105" rx="15" ry="24" fill="#e8a836" opacity=".75"/>
        <ellipse cx="120" cy="99" rx="9" ry="15" fill="#f0c040"/>
        <ellipse cx="120" cy="96" rx="4" ry="8" fill="#fff" opacity=".8"/>
        <!-- 별 / 반짝이 분포 -->
        <path d="M60 50 l3 6 6 1 -4.5 4 1 6 -5.5 -3 -5.5 3 1 -6 -4.5 -4 6 -1z" fill="#e8c36a" opacity=".65"/>
        <path d="M180 60 l2.5 5 5 .7 -3.7 3.5 1 5 -4.8 -2.5 -4.8 2.5 1 -5 -3.7 -3.5 5 -.7z" fill="#e8c36a" opacity=".55"/>
        <path d="M50 95 l2 3 3 .5 -2.5 2.5 .5 3 -3 -1.5 -3 1.5 .5 -3 -2.5 -2.5 3 -.5z" fill="#e8c36a" opacity=".5"/>
        <path d="M190 90 l1.8 3 3 .4 -2.4 2.4 .6 3 -3 -1.5 -3 1.5 .6 -3 -2.4 -2.4 3 -.4z" fill="#e8c36a" opacity=".45"/>
        <path d="M30 70 l1.5 2.5 2.5 .4 -2 2 .4 2.5 -2.4 -1.2 -2.4 1.2 .4 -2.5 -2 -2 2.5 -.4z" fill="#e8c36a" opacity=".45"/>
        <path d="M210 35 l1.5 2.5 2.5 .4 -2 2 .4 2.5 -2.4 -1.2 -2.4 1.2 .4 -2.5 -2 -2 2.5 -.4z" fill="#e8c36a" opacity=".4"/>
        <circle cx="85" cy="35" r="1.6" fill="#e8c36a" opacity=".6"/>
        <circle cx="155" cy="40" r="1.4" fill="#e8c36a" opacity=".55"/>
        <circle cx="120" cy="28" r="1.8" fill="#e8c36a" opacity=".7"/>
        <circle cx="200" cy="120" r="1.4" fill="#e8c36a" opacity=".5"/>
        <circle cx="40" cy="115" r="1.4" fill="#e8c36a" opacity=".5"/>
        <!-- 메인 텍스트 -->
        <text x="120" y="255" text-anchor="middle" font-family="Gaegu,cursive" font-size="18" font-weight="700" fill="#8b4513">빛을 밝히는 사람</text>
        <text x="120" y="275" text-anchor="middle" font-family="'Noto Sans KR',sans-serif" font-size="10" fill="#7a6b5a">묵묵히 자기 길을 걷는다</text>
      </svg>
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
        <li>&middot; 약속한 것은 반드시 지킨다</li>
        <li>&middot; 성장의 씨앗을 심고 기다린다</li>
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
        <li>{I['gear']} 감정+이성 동시 구동, 직감과 분석</li>
        <li>{I['water']} 동안 유지, 나이 들수록 신뢰감 ↑</li>
        <li>{I['shield']} 원칙이 있되 유연하게 적용</li>
        <li>{I['fire']} 불꽃 같은 열정, 바다 같은 포용</li>
      </ul>
    </div>
    <div class="card" style="width:100%;text-align:left">
      <h3>{I['person']} 관계 패턴</h3>
      <ul>
        <li>&middot; 첫인상 부드럽고 편안, 압박감 없음</li>
        <li>&middot; 웃을 때 분위기 밝아지는 타입</li>
        <li>&middot; 감정 몰입 빠르지만 에너지 소모 큼</li>
        <li>&middot; 편안한 관계에서 최고 퍼포먼스</li>
        <li>&middot; 사람·정보·아이디어 연결이 장기</li>
        <li>&middot; 눈빛 변화와 감정 흐름이 살아있음</li>
        <li>&middot; 진심이 통하면 강한 유대감 형성</li>
        <li>&middot; 갈등은 회피 X, 대화로 해결 추구</li>
      </ul>
    </div>
    <div class="svg-deco">
      <svg viewBox="0 0 320 220" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
        <defs>
          <radialGradient id="tree-glow" cx="50%" cy="35%">
            <stop offset="0%" stop-color="#fff4d4" stop-opacity=".45"/>
            <stop offset="100%" stop-color="#fff4d4" stop-opacity="0"/>
          </radialGradient>
          <linearGradient id="trunk-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#a87a48"/>
            <stop offset="100%" stop-color="#6b4a28"/>
          </linearGradient>
          <radialGradient id="canopy-grad" cx="50%" cy="40%">
            <stop offset="0%" stop-color="#8fb478"/>
            <stop offset="100%" stop-color="#5a7a48"/>
          </radialGradient>
          <linearGradient id="ground-tree" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#c4915a" stop-opacity=".35"/>
            <stop offset="100%" stop-color="#c4915a" stop-opacity="0"/>
          </linearGradient>
        </defs>
        <!-- 배경 halo -->
        <ellipse cx="160" cy="80" rx="150" ry="70" fill="url(#tree-glow)"/>
        <!-- 바람 라인 (왼쪽에서) -->
        <path d="M10 50 Q40 48 70 52" stroke="#b8a890" stroke-width="1.2" fill="none" opacity=".55" stroke-dasharray="3 3"/>
        <path d="M10 70 Q45 68 80 72" stroke="#b8a890" stroke-width="1.2" fill="none" opacity=".5" stroke-dasharray="3 3"/>
        <path d="M5 95 Q40 93 75 96" stroke="#b8a890" stroke-width="1.2" fill="none" opacity=".45" stroke-dasharray="3 3"/>
        <path d="M15 115 Q50 113 85 116" stroke="#b8a890" stroke-width="1" fill="none" opacity=".4" stroke-dasharray="2 3"/>
        <!-- 바람 라인 (오른쪽으로) -->
        <path d="M250 55 Q280 53 310 57" stroke="#b8a890" stroke-width="1.2" fill="none" opacity=".55" stroke-dasharray="3 3"/>
        <path d="M245 75 Q280 73 315 77" stroke="#b8a890" stroke-width="1.2" fill="none" opacity=".5" stroke-dasharray="3 3"/>
        <path d="M250 100 Q285 98 315 101" stroke="#b8a890" stroke-width="1.2" fill="none" opacity=".45" stroke-dasharray="3 3"/>
        <!-- 별/반짝이 (하늘) -->
        <circle cx="40" cy="25" r="1.6" fill="#e8c36a" opacity=".7"/>
        <circle cx="280" cy="30" r="1.8" fill="#e8c36a" opacity=".7"/>
        <circle cx="100" cy="15" r="1.4" fill="#e8c36a" opacity=".6"/>
        <circle cx="220" cy="20" r="1.5" fill="#e8c36a" opacity=".65"/>
        <path d="M160 18 l1.8 3 3 .4 -2.4 2.4 .6 3 -3 -1.5 -3 1.5 .6 -3 -2.4 -2.4 3 -.4z" fill="#e8c36a" opacity=".55"/>
        <!-- 바닥 그라데이션 (지면) -->
        <rect x="0" y="155" width="320" height="20" fill="url(#ground-tree)"/>
        <ellipse cx="160" cy="158" rx="90" ry="6" fill="#8b7355" opacity=".35"/>
        <!-- 나무 뿌리 (깊고 넓게 뻗은) -->
        <path d="M160 155 Q140 170 115 180 Q95 188 75 200" stroke="#6b4a28" stroke-width="3" fill="none" opacity=".75"/>
        <path d="M160 155 Q145 172 130 185 Q120 195 105 210" stroke="#6b4a28" stroke-width="2.4" fill="none" opacity=".65"/>
        <path d="M160 155 Q155 175 150 195 Q148 205 145 215" stroke="#6b4a28" stroke-width="2" fill="none" opacity=".6"/>
        <path d="M160 155 Q180 170 205 180 Q225 188 245 200" stroke="#6b4a28" stroke-width="3" fill="none" opacity=".75"/>
        <path d="M160 155 Q175 172 190 185 Q200 195 215 210" stroke="#6b4a28" stroke-width="2.4" fill="none" opacity=".65"/>
        <path d="M160 155 Q165 175 170 195 Q172 205 175 215" stroke="#6b4a28" stroke-width="2" fill="none" opacity=".6"/>
        <path d="M160 155 Q120 175 85 190" stroke="#6b4a28" stroke-width="2" fill="none" opacity=".55"/>
        <path d="M160 155 Q200 175 235 190" stroke="#6b4a28" stroke-width="2" fill="none" opacity=".55"/>
        <!-- 줄기 (튼튼한 본체) -->
        <path d="M150 155 Q148 110 152 80 L168 80 Q172 110 170 155 Z" fill="url(#trunk-grad)"/>
        <path d="M155 145 Q156 120 158 95" stroke="#3a2818" stroke-width=".8" fill="none" opacity=".4"/>
        <path d="M163 145 Q162 120 161 95" stroke="#3a2818" stroke-width=".6" fill="none" opacity=".3"/>
        <!-- 가지 -->
        <path d="M152 100 Q138 90 122 85" stroke="#6b4a28" stroke-width="2.2" fill="none" opacity=".7"/>
        <path d="M168 100 Q182 90 198 85" stroke="#6b4a28" stroke-width="2.2" fill="none" opacity=".7"/>
        <path d="M155 88 Q145 78 132 70" stroke="#6b4a28" stroke-width="1.8" fill="none" opacity=".6"/>
        <path d="M165 88 Q175 78 188 70" stroke="#6b4a28" stroke-width="1.8" fill="none" opacity=".6"/>
        <!-- 캐노피 (넓은 잎 덮개) -->
        <ellipse cx="160" cy="65" rx="68" ry="42" fill="url(#canopy-grad)" opacity=".85"/>
        <ellipse cx="120" cy="72" rx="32" ry="26" fill="#7aa066" opacity=".75"/>
        <ellipse cx="200" cy="72" rx="32" ry="26" fill="#7aa066" opacity=".75"/>
        <ellipse cx="140" cy="50" rx="28" ry="22" fill="#8fb478" opacity=".8"/>
        <ellipse cx="180" cy="50" rx="28" ry="22" fill="#8fb478" opacity=".8"/>
        <ellipse cx="160" cy="42" rx="32" ry="22" fill="#a0c088" opacity=".7"/>
        <!-- 떨어지는 잎 (몇 개) -->
        <ellipse cx="100" cy="120" rx="5" ry="2.5" fill="#8fb478" opacity=".55" transform="rotate(-30 100 120)"/>
        <ellipse cx="220" cy="125" rx="5" ry="2.5" fill="#8fb478" opacity=".5" transform="rotate(35 220 125)"/>
        <ellipse cx="85" cy="145" rx="4" ry="2" fill="#7aa066" opacity=".45" transform="rotate(-45 85 145)"/>
        <ellipse cx="240" cy="140" rx="4" ry="2" fill="#7aa066" opacity=".45" transform="rotate(40 240 140)"/>
      </svg>
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
    <div class="card">
      <h3>{I['clock']} 핵심 습관</h3>
      <ul>
        <li>{I['lamp']} 매일 아침 감사 · 목표 정리</li>
        <li>{I['book']} AI와 대화하며 생각 구조화</li>
        <li>{I['plant']} 걷기 · 운동으로 에너지 전환</li>
        <li>{I['candle']} 하루 끝 3가지 성찰 기록</li>
        <li>{I['bulb']} 새로운 것 하나는 꼭 배우기</li>
        <li>{I['target']} 주간 점검으로 방향 재조정</li>
      </ul>
    </div>
    <div class="card">
      <h3>{I['compass']} 의사결정 스타일</h3>
      <ul>
        <li>{I['gear']} 데이터 + 직감 하이브리드</li>
        <li>{I['bulb']} 핵심 질문으로 본질 파악</li>
        <li>{I['rocket']} 작은 실험 → 빠른 피드백</li>
        <li>{I['person']} 관계자 의견 충분히 청취</li>
        <li>{I['shield']} 결정 후엔 끝까지 밀고 나감</li>
        <li>{I['water']} 불확실할 때 멈추고 관찰</li>
      </ul>
    </div>
  </div>
</div>

<div class="bottom">
  <div class="btm-card">
    <h4>{I['rocket']} 나를 움직이게 하는 것</h4>
    <ul>
      <li>{I['bulb']} 복잡한 문제를 해결하는 쾌감</li>
      <li>{I['star']} 배움을 실제 결과로 연결</li>
      <li>{I['cpu']} AI와 협업으로 더 나은 결과</li>
      <li>{I['heart']} 누군가에게 도움되는 도구</li>
      <li>{I['fire']} 새로운 도전에서 오는 기쁨</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['heart']} 미래에 이루고 싶은 것</h4>
    <ul>
      <li>{I['target']} 독립적·주도적 전문가</li>
      <li>{I['shield']} 스스로 판단하고 책임짐</li>
      <li>{I['book']} 다음 세대 위한 교육 멘토</li>
      <li>{I['compass']} AI 시대 방향 제시자</li>
      <li>{I['star']} 선한 영향력 확장</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['plant']} 나의 가능성</h4>
    <ul>
      <li>{I['candle']} 어둠을 밝히는 지혜</li>
      <li>{I['gear']} 분석력+실행력 전문가</li>
      <li>{I['heart']} 기술과 감성의 융합력</li>
      <li>{I['person']} 멘토로 사람을 성장시킴</li>
      <li>{I['mountain']} 위기에서 더 강해지는 힘</li>
    </ul>
  </div>
  <div class="btm-card">
    <h4>{I['check']} 인생 체크리스트</h4>
    <ul>
      <li>{I['target']} 전문성 강화 — 매일 깊이</li>
      <li>{I['heart']} 건강 관리 — 몸과 마음</li>
      <li>{I['rocket']} 영향력 확장 — 더 넓게</li>
      <li>{I['person']} 가족과 시간 — 소중히</li>
      <li>{I['lamp']} 배움의 불꽃을 나누기</li>
    </ul>
  </div>
</div>
<!-- 코너 데코 SVG (식물·촛불·별) -->
<svg style="position:fixed;bottom:2px;left:4px;opacity:.4" width="40" height="35" viewBox="0 0 40 35"><rect x="14" y="22" width="12" height="12" rx="2" fill="#c4915a" opacity=".3"/><path d="M20 22c-3-8 0-18 0-18s3 10 0 18" fill="#6b8e5a" opacity=".6"/><ellipse cx="14" cy="16" rx="6" ry="4" fill="#6b8e5a" opacity=".3" transform="rotate(-30,14,16)"/><ellipse cx="26" cy="14" rx="6" ry="4" fill="#6b8e5a" opacity=".3" transform="rotate(30,26,14)"/></svg>
<svg style="position:fixed;bottom:2px;right:4px;opacity:.4" width="40" height="35" viewBox="0 0 40 35"><rect x="14" y="22" width="12" height="12" rx="2" fill="#8b7355" opacity=".3"/><path d="M20 22c-3-8 0-18 0-18s3 10 0 18" fill="#6b8e5a" opacity=".5"/><circle cx="20" cy="5" r="3" fill="#e8c36a" opacity=".4"/><ellipse cx="12" cy="18" rx="5" ry="3" fill="#6b8e5a" opacity=".3" transform="rotate(-40,12,18)"/><ellipse cx="28" cy="16" rx="5" ry="3" fill="#6b8e5a" opacity=".3" transform="rotate(40,28,16)"/></svg>

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

    # orch-promo — viewport = body (850x1100), scale=4 → output 3400x4400 (sharp, no padding)
    pg = br.new_page(viewport={"width":850,"height":1100}, device_scale_factor=4)
    pg.goto((DIR / "orch-promo.html").as_uri())
    pg.wait_for_timeout(3000)
    pg.screenshot(path=str(DIR / "orch-promo.jpg"), full_page=False, type="jpeg", quality=95)
    print("  orch-promo.jpg OK")
    pg.close()

    # ssj-summary (body 990×1320 ratio 1.333 = target 1.332, exact fit no pad)
    pg = br.new_page(viewport={"width":990,"height":1320}, device_scale_factor=2)
    pg.goto((DIR / "ssj-infographic.html").as_uri())
    pg.wait_for_timeout(3000)
    pg.screenshot(path=str(DIR / "ssj-summary.jpg"), full_page=False, type="jpeg", quality=95)
    print("  ssj-summary.jpg OK")
    pg.close()

    br.close()

# Post-process: resize ssj-summary.jpg to target 1320×1758 preserving aspect (pad with bg)
from PIL import Image
ssj_path = DIR / "ssj-summary.jpg"
img = Image.open(ssj_path)
print(f"  pre-resize: {img.size}  ratio={img.size[1]/img.size[0]:.3f}")
TGT_W, TGT_H = 1320, 1758
src_ratio = img.size[1] / img.size[0]
tgt_ratio = TGT_H / TGT_W  # 1.332
if abs(src_ratio - tgt_ratio) < 0.01:
    img2 = img.resize((TGT_W, TGT_H), Image.LANCZOS)
else:
    # aspect-preserving fit + pad with bg color
    src_w, src_h = img.size
    if src_ratio > tgt_ratio:  # source taller than target -> fit by height
        new_h = TGT_H; new_w = int(src_w * TGT_H / src_h)
    else:  # source wider/shorter -> fit by width
        new_w = TGT_W; new_h = int(src_h * TGT_W / src_w)
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new('RGB', (TGT_W, TGT_H), (245, 239, 230))
    canvas.paste(resized, ((TGT_W - new_w) // 2, (TGT_H - new_h) // 2))
    img2 = canvas
img2.save(ssj_path, "JPEG", quality=95)
print(f"  post-resize: {img2.size} -> target 1320x1758 OK")

print("Done: orch-promo.jpg + ssj-summary.jpg")
