# doc_auto task — C:\\pjt\\orchestration_v1\\docs\\ssj\\render-ssj.py

## Diff (HEAD)
```
diff --git a/docs/ssj/render-ssj.py b/docs/ssj/render-ssj.py
index 9f3be98..043498b 100644
--- a/docs/ssj/render-ssj.py
+++ b/docs/ssj/render-ssj.py
@@ -92,24 +92,28 @@ def build_orch_promo():
 body{{width:850px;height:1100px;background:#f5efe6;
   background-image:radial-gradient(ellipse at 15% 85%,rgba(210,180,140,.1) 0%,transparent 50%),
   radial-gradient(ellipse at 85% 15%,rgba(180,160,130,.06) 0%,transparent 40%);
-  padding:6px 8px;display:flex;flex-direction:column;justify-content:space-between}}
-.header{{display:flex;justify-content:space-between;align-items:flex-start}}
+  padding:6px 8px;display:flex;flex-direction:column;justify-content:flex-start;gap:3px;overflow:hidden}}
+.header{{display:flex;justify-content:space-between;align-items:flex-start;flex-shrink:0}}
 .header-left h1{{font-family:'Gaegu',cursive;font-size:28px;font-weight:700;color:#2c2418;line-height:1.25}}
 .header-left .sub{{font-size:11px;color:#7a6b5a;margin-top:3px;display:flex;align-items:center;gap:4px}}
 .header-right{{display:flex;gap:6px;max-width:360px}}
-.mid{{display:grid;grid-template-columns:230px 1fr 230px;gap:3px;flex:1;margin:3px 0}}
-.mid-left,.mid-right{{display:flex;flex-direction:column;gap:2px}}
-.center{{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px}}
-.photo{{width:200px;height:240px;border-radius:10px;object-fit:cover;border:2.5px solid #c4b49a;box-shadow:3px 3px 10px rgba(0,0,0,.1)}}
-.name-area{{text-align:center}}
+.mid{{display:grid;grid-template-columns:230px 1fr 230px;gap:3px;flex:1 1 auto;margin:3px 0;min-height:0}}
+.mid-left,.mid-right{{display:flex;flex-direction:column;gap:3px;justify-content:space-between;min-height:0}}
+.mid-left .card,.mid-right .card{{flex:1 1 auto;display:flex;flex-direction:column;min-height:0}}
+.mid-left .card ul,.mid-right .card ul,.mid-left .card .tags,.mid-right .card .tags{{flex:1 1 auto;display:flex;flex-direction:column;justify-content:space-around}}
+.mid-left .card .tags,.mid-right .card .tags{{flex-direction:row;flex-wrap:wrap;align-content:space-around}}
+.center{{display:flex;flex-direction:column;align-items:center;justify-content:space-between;gap:6px;padding:4px 0;min-height:0}}
+.photo{{width:200px;height:240px;border-radius:10px;object-fit:cover;border:2.5px solid #c4b49a;box-shadow:3px 3px 10px rgba(0,0,0,.1);flex-shrink:0}}
+.name-area{{text-align:center;flex-shrink:0}}
 .name-area .nm{{font-family:'Gaegu',cursive;font-size:20px;font-weight:700;color:#2c2418}}
 .name-area .inf{{font-size:9px;color:#8a7a68;margin-top:1px}}
-.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;width:100%}}
+.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;width:100%;flex-shrink:0}}
 .stat{{background:rgba(255,255,255,.5);border:1px solid #d4c4a8;border-radius:5px;padding:4px;text-align:center}}
 .stat .n{{font-family:'Gaegu',cursive;font-size:18px;font-weight:700;color:#8b4513}}
 .stat .l{{font-size:8px;color:#7a6b5a}}
-.bottom{{display:grid;grid-template-columns:repeat(4,1fr);gap:2px}}
-.btm-card{{background:rgba(255,255,255,.45);border:1.5px solid #d4c4a8;border-radius:5px;padding:4px 6px}}
+.bottom{{display:grid;grid-template-columns:repeat(4,1fr);gap:2px;flex-shrink:0}}
+.btm-card{{background:rgba(255,255,255,.45);border:1.5px solid #d4c4a8;border-radius:5px;padding:4px 6px;display:flex;flex-direction:column}}
+.btm-card ul{{flex:1 1 auto;display:flex;flex-direction:column;justify-content:space-around}}
 .btm-card h4{{font-family:'Gaegu',cursive;font-size:11px;color:#8b4513;margin-bottom:3px;display:flex;align-items:center;gap:3px}}
 .btm-card li{{font-size:9px;line-height:1.5;color:#5a4f42}}
 .btm-card ul{{list-style:none;padding:0}}
@@ -282,7 +286,7 @@ body{{width:850px;height:1100px;background:#f5efe6;
     <div class="card">
       <h3>{I['gear']} \uae30\uc220 \uc544\ud0a4\ud14d\ucc98</h3>
       <ul>
-        <li>&middot; Claude Opus 4.7 (\uc124\uacc4\u00b7\ubcf5\uc7a1\ucd94\ub860\u00b71M ctx)</li>
+        <li>&middot; Claude Opus 4.8 (\uc124\uacc4\u00b7\ubcf5\uc7a1\ucd94\ub860\u00b71M ctx)</li>
         <li>&middot; Claude Sonnet 4.6 (\ub2e8\uc21c\uad6c\ud604 200\uc904-)</li>
         <li>&middot; Codex \u00d74 \ubcd1\ub82c (\ucf54\ub4dc 500\uc904+)</li>
         <li>&middot; Haiku 4.5 \u00d72 (\uac80\uc99d 90% \uc808\uac10)</li>
@@ -305,7 +309,7 @@ body{{width:850px;height:1100px;background:#f5efe6;
     <div class="card">
       <h3>{I['compass']} AI 라우팅 정책</h3>
       <ul>
-        <li>{I['gear']} 복잡추론·1M ctx → Claude Opus 4.7</li>
+        <li>{I['gear']} 복잡추론·1M ctx → Claude Opus 4.8</li>
         <li>{I['code']} 코드 500줄+ → Codex ×4 병렬</li>
         <li>{I['check']} 검증 기본 → Haiku 4.5 ×2 (90% 절감)</li>
         <li>{I['water']} 초장문 500k+ → Gemini Flash</li>
```

## Action
1. 변경된 public API 추출 (함수·클래스·exports)
2. CHANGELOG.md `[Unreleased]` 섹션에 entry 추가:
   - Added/Changed/Fixed/Removed/Security 분류
3. README.md 의 API 섹션 갱신 (있을 시)
4. docs/api/<module>.md 갱신 (있을 시)

## Constraints
- 기존 entry 덮어쓰기 X (append)
- 자동 commit X (사용자 review 대기)
- 내부 helper 변경 skip (public API 만)
