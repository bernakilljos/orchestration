# doc_auto task — C:\\pjt\\orchestration_v1\\.claude\\scripts\\build-itcen-ppt-proposal.py

## Diff (HEAD)
```
diff --git a/.claude/scripts/build-itcen-ppt-proposal.py b/.claude/scripts/build-itcen-ppt-proposal.py
new file mode 100644
index 0000000..50f42e3
--- /dev/null
+++ b/.claude/scripts/build-itcen-ppt-proposal.py
@@ -0,0 +1,736 @@
+"""아이티센코어 부서 AI 신사업 제안 PPT 15장 자동 생성
+
+청중: 임원·본부장 (가정)
+목적: AI Risk Lighthouse + 부서 IP 신사업 승인·예산 요청
+산출물: outputs/itcen/itcen-business-proposal.pptx
+"""
+import os
+from pptx import Presentation
+from pptx.util import Inches, Pt, Emu
+from pptx.dml.color import RGBColor
+from pptx.enum.shapes import MSO_SHAPE
+from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
+
+ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
+OUT = os.path.join(ROOT, 'outputs', 'itcen', 'itcen-business-proposal.pptx')
+
+# 색상 팔레트
+PRIMARY = RGBColor(0x1F, 0x4E, 0x79)      # 진한 파랑
+ACCENT = RGBColor(0xC0, 0x00, 0x00)       # 빨강 (강조)
+LIGHT = RGBColor(0xD9, 0xE1, 0xF2)        # 연한 파랑 (배경)
+GRAY = RGBColor(0x59, 0x59, 0x59)         # 본문 그레이
+WHITE = RGBColor(0xFF, 0xFF, 0xFF)
+GOLD = RGBColor(0xC4, 0x91, 0x5A)         # 금색
+
+prs = Presentation()
+prs.slide_width = Inches(13.333)
+prs.slide_height = Inches(7.5)
+SW, SH = prs.slide_width, prs.slide_height
+
+BLANK = prs.slide_layouts[6]
+
+
+def add_text(slide, x, y, w, h, text, *, size=14, bold=False, color=None, align=PP_ALIGN.LEFT, font='맑은 고딕'):
+    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
+    tf = box.text_frame
+    tf.word_wrap = True
+    tf.margin_left = Emu(0)
+    tf.margin_right = Emu(0)
+    tf.margin_top = Emu(0)
+    tf.margin_bottom = Emu(0)
+    if isinstance(text, list):
+        for i, line in enumerate(text):
+            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
+            p.alignment = align
+            r = p.add_run()
+            r.text = line
+            r.font.name = font
+            r.font.size = Pt(size)
+            r.font.bold = bold
+            if color:
+                r.font.color.rgb = color
+    else:
+        p = tf.paragraphs[0]
+        p.alignment = align
+        r = p.add_run()
+        r.text = text
+        r.font.name = font
+        r.font.size = Pt(size)
+        r.font.bold = bold
+        if color:
+            r.font.color.rgb = color
+    return box
+
+
+def add_bg(slide, x, y, w, h, color, *, outline=None):
+    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
+    shape.fill.solid()
+    shape.fill.fore_color.rgb = color
+    if outline:
+        shape.line.color.rgb = outline
+        shape.line.width = Pt(0.5)
+    else:
+        shape.line.fill.background()
+    shape.shadow.inherit = False
+    return shape
+
+
+def add_card(slide, x, y, w, h, title, bullets, *, title_color=None, bullet_size=11, title_size=14):
+    add_bg(slide, x, y, w, h, WHITE, outline=RGBColor(0xC0, 0xC0, 0xC0))
+    add_bg(slide, x, y, w, 0.35, title_color or PRIMARY)
+    add_text(slide, x + 0.1, y + 0.05, w - 0.2, 0.3, title, size=title_size, bold=True, color=WHITE)
+    lines = ['• ' + b for b in bullets]
+    add_text(slide, x + 0.15, y + 0.45, w - 0.3, h - 0.5, lines, size=bullet_size, color=GRAY)
+
+
+def add_table(slide, x, y, w, h, headers, rows, *, header_color=None, header_text_color=None,
+              first_col_bold=False, col_widths=None, font_size=10):
+    table_shape = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(x), Inches(y), Inches(w), Inches(h))
+    table = table_shape.table
+    if col_widths:
+        total = sum(col_widths)
+        for i, cw in enumerate(col_widths):
+            table.columns[i].width = Inches(w * cw / total)
+    for i, hdr in enumerate(headers):
+        cell = table.cell(0, i)
+        cell.fill.solid()
+        cell.fill.fore_color.rgb = header_color or PRIMARY
+        cell.text = hdr
+        for p in cell.text_frame.paragraphs:
+            p.alignment = PP_ALIGN.CENTER
+            for r in p.runs:
+                r.font.name = '맑은 고딕'
+                r.font.size = Pt(font_size + 1)
+                r.font.bold = True
+                r.font.color.rgb = header_text_color or WHITE
+    for ri, row in enumerate(rows, start=1):
+        for ci, val in enumerate(row):
+            cell = table.cell(ri, ci)
+            cell.text = str(val)
+            for p in cell.text_frame.paragraphs:
+                p.alignment = PP_ALIGN.LEFT if ci > 0 or not first_col_bold else PP_ALIGN.CENTER
+                for r in p.runs:
+                    r.font.name = '맑은 고딕'
+                    r.font.size = Pt(font_size)
+                    r.font.color.rgb = GRAY
+                    if ci == 0 and first_col_bold:
+                        r.font.bold = True
+                        r.font.color.rgb = PRIMARY
+    return table
+
+
+def add_title(slide, num, title, subtitle=None):
+    # 상단 띠
+    add_bg(slide, 0, 0, 13.333, 0.7, PRIMARY)
+    add_text(slide, 0.3, 0.15, 0.7, 0.4, f'#{num:02d}', size=18, bold=True, color=GOLD)
+    add_text(slide, 1.0, 0.12, 8, 0.45, title, size=18, bold=True, color=WHITE)
+    if subtitle:
+        add_text(slide, 1.0, 0.42, 11, 0.25, subtitle, size=10, color=LIGHT)
+    add_text(slide, 11.3, 0.2, 1.8, 0.35, 'ITCEN CORE', size=10, color=GOLD, align=PP_ALIGN.RIGHT)
+    add_text(slide, 11.3, 0.42, 1.8, 0.25, 'AI Risk Monitoring', size=8, color=LIGHT, align=PP_ALIGN.RIGHT)
+
+
+def add_footer(slide, page_num):
+    add_bg(slide, 0, 7.2, 13.333, 0.3, LIGHT)
+    add_text(slide, 0.3, 7.27, 8, 0.2, '아이티센코어 · 리스크모니터링·행동위험분석 부서 · AI 신사업 제안', size=8, color=PRIMARY)
+    add_text(slide, 11.5, 7.27, 1.5, 0.2, f'{page_num} / 15', size=8, color=PRIMARY, align=PP_ALIGN.RIGHT)
+
+
+# ════════════════════════════════════════════════════════════
+# Slide 1 — 표지
+# ════════════════════════════════════════════════════════════
+s = prs.slides.add_slide(BLANK)
+add_bg(s, 0, 0, 13.333, 7.5, PRIMARY)
+add_bg(s, 0, 5.0, 13.333, 0.05, GOLD)
+
+# 메인 타이틀
+add_text(s, 0.8, 1.5, 11.7, 0.8, 'AI Risk Lighthouse', size=54, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
+add_text(s, 0.8, 2.5, 11.7, 0.5, '한국 표준 행동위험·내부통제 자동 감사 플랫폼', size=22, color=LIGHT, align=PP_ALIGN.CENTER)
+add_text(s, 0.8, 3.2, 11.7, 0.4, '2027-2030 AI 메가트렌드를 활용한 부서 핵심 IP 사업', size=14, color=GOLD, align=PP_ALIGN.CENTER)
+
+# 4 패러다임 박스
+for i, (txt, x) in enumerate([('양자모델', 1.8), ('LLM', 4.6), ('피지컬 AI', 7.4), ('생성형 AI', 10.2)]):
+    add_bg(s, x, 4.3, 2.3, 0.6, GOLD)
+    add_text(s, x, 4.4, 2.3, 0.4, txt, size=16, bold=True, color=PRIMARY, align=PP_ALIGN.CENTER)
+
+# 하단 정보
+add_text(s, 0.8, 5.5, 11.7, 0.4, '아이티센코어  ·  리스크모니터링·행동위험분석 부서', size=18, color=WHITE, align=PP_ALIGN.CENTER)
+add_text(s, 0.8, 6.0, 11.7, 0.3, '2026년 6월', size=14, color=LIGHT, align=PP_ALIGN.CENTER)
+add_text(s, 0.8, 6.8, 11.7, 0.3, 'Multi-AI Orchestration 기반 신사업 제안', size=10, color=GOLD, align=PP_ALIGN.CENTER)
+
+
+# ════════════════════════════════════════════════════════════
+# Slide 2 — Executive Summary
+# ════════════════════════════════════════════════════════════
+s = prs.slides.add_slide(BLANK)
+add_title(s, 2, 'Executive Summary', '한 페이지 핵심 — 무엇·왜·언제·얼마')
+
+# 4 박스
+boxes = [
+    (' 무엇 (WHAT)', '한국 최초 AI Risk Lighthouse — 회사의 AI·내부통제·행동위험을 자동 감사·점수화하는 표준 플랫폼',
+     'Google Lighthouse 가 웹페이지 점수 매기듯, 8 카테고리 가중 점수 산정'),
+    ('💡 왜 (WHY)', 'EU AI Act 2027·금감원 AI 거버넌스 2026·ISO 42001 2026-27 의무화로 모든 한국 기업이 AI 위험 정량화 필수',
+     '한국 표준 선점 = 영구 매출 + 부서 IP 확보'),
+    ('⏰ 언제 (WHEN)', '2026-Q4 IP 확보 → 2027-Q3 한국 표준 등록 → 2028+ 5,000社 의무 도입',
+     '3년 사업화 로드맵'),
+    ('💰 얼마 (HOW MUCH)', '초기 자본: 2-5억 (부서 자체 추진)\n2028+ 매출: 5,000社 × 1억 = 5,000억 영구',
+     '글로벌 수출 2029+: K-Standard'),
+]
+for i, (title, body, sub) in enumerate(boxes):
+    x = 0.3 + (i % 2) * 6.5
+    y = 1.0 + (i // 2) * 2.9
+    add_bg(s, x, y, 6.2, 2.7, WHITE, outline=PRIMARY)
+    add_bg(s, x, y, 6.2, 0.5, PRIMARY)
+    add_text(s, x + 0.2, y + 0.1, 6.0, 0.35, title, size=16, bold=True, color=WHITE)
+    add_text(s, x + 0.25, y + 0.7, 5.9, 1.3, body, size=12, color=GRAY)
+    add_text(s, x + 0.25, y + 2.1, 5.9, 0.5, sub, size=10, color=ACCENT, bold=True)
+
+add_footer(s, 2)
+
+
+# ════════════════════════════════════════════════════════════
+# Slide 3 — 2027-2030 메가트렌드
+# ════════════════════════════════════════════════════════════
+s = prs.slides.add_slide(BLANK)
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
