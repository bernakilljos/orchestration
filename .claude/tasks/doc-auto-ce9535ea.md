# doc_auto task — C:\\pjt\\orchestration_v1\\.claude\\scripts\\analyze-itcen-ppt.py

## Diff (HEAD)
```
diff --git a/.claude/scripts/analyze-itcen-ppt.py b/.claude/scripts/analyze-itcen-ppt.py
new file mode 100644
index 0000000..1939bc5
--- /dev/null
+++ b/.claude/scripts/analyze-itcen-ppt.py
@@ -0,0 +1,64 @@
+"""ITCEN CORE 실제 사업 PPT 분석 — 현대위아 연결내부회계관리시스템 구축"""
+import os, sys
+from pptx import Presentation
+from pptx.util import Emu
+
+src = os.path.join(
+    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
+    'outputs', 'itcen',
+    '현대위아_연결내부회계관리시스템 구축_아이티센코어.pptx'
+)
+print(f'[FILE] {os.path.basename(src)}')
+print(f'[SIZE] {os.path.getsize(src):,} bytes')
+print()
+
+prs = Presentation(src)
+print(f'[SLIDES] 총 {len(prs.slides)} 슬라이드')
+print(f'[SIZE] {prs.slide_width / 914400:.2f} x {prs.slide_height / 914400:.2f} inches')
+print()
+
+# 각 슬라이드 분석
+for i, slide in enumerate(prs.slides, 1):
+    print(f'━━━━━━━━━━ Slide {i:02d} ━━━━━━━━━━')
+    shape_count = len(slide.shapes)
+    text_shapes = 0
+    pic_shapes = 0
+    table_shapes = 0
+    chart_shapes = 0
+    grp_shapes = 0
+
+    title = ''
+    texts = []
+
+    for shape in slide.shapes:
+        if shape.has_text_frame:
+            text_shapes += 1
+            for para in shape.text_frame.paragraphs:
+                txt = para.text.strip()
+                if txt:
+                    texts.append(txt)
+                    if not title and len(txt) > 3 and len(txt) < 60:
+                        # 큰 폰트가 제목일 가능성
+                        for r in para.runs:
+                            if r.font.size and r.font.size.pt > 20:
+                                title = txt
+                                break
+        if shape.shape_type == 13:  # picture
+            pic_shapes += 1
+        if shape.has_table:
+            table_shapes += 1
+        if shape.has_chart:
+            chart_shapes += 1
+        if shape.shape_type == 6:  # group
+            grp_shapes += 1
+
+    print(f'  shapes: total={shape_count} text={text_shapes} pic={pic_shapes} table={table_shapes} chart={chart_shapes} group={grp_shapes}')
+    if title:
+        print(f'  TITLE: {title}')
+    if texts:
+        # 상위 5 텍스트 (긴 것)
+        sorted_texts = sorted(set(texts), key=lambda x: -len(x))[:8]
+        for t in sorted_texts:
+            short = t[:120].replace('\n', ' / ')
+            print(f'  · {short}')
+    print()
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
