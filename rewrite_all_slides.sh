#!/bin/bash
# PPT 슬라이드 25개 전면 재작성

set -e

SLIDES_DIR="outputs/ppt/html-source/slides"

echo "Starting PPT rewrite (25 slides)..."

# Slide 03: 프로젝트 루트
echo "Rewriting slide-03..."
sed -i '
s/PART 01 · YOUR DESIGN · THE 14-DAY JOURNEY/PART 01 · INSTALLED STRUCTURE/
s/<h1 class="heading-1">.*<\/h1>/<h1 class="heading-1">프로젝트 루트<\/h1>/
s/<p class="heading-2[^>]*>.*<\/p>/<p class="heading-2 text-stone" style="font-weight: 400;">최상위 디렉토리 + 핵심 파일<\/p>/
' "$SLIDES_DIR/slide-03.html"

# Slide 04: .claude/ 상세
echo "Rewriting slide-04..."
sed -i '
s/PART 01 · YOUR DESIGN · THE 14-DAY JOURNEY/PART 01 · INSTALLED STRUCTURE/
s/<h1 class="heading-1">.*<\/h1>/<h1 class="heading-1">.claude\/ 상세<\/h1>/
s/<p class="heading-2[^>]*>.*<\/p>/<p class="heading-2 text-stone" style="font-weight: 400;">Claude Code 런타임 — 9개 하위 폴더<\/p>/
' "$SLIDES_DIR/slide-04.html"

# Slide 05: SoT 원칙
echo "Rewriting slide-05..."
sed -i '
s/PART 01 · YOUR DESIGN · THE 14-DAY JOURNEY/PART 01 · INSTALLED STRUCTURE/
s/<h1 class="heading-1">.*<\/h1>/<h1 class="heading-1">Source of Truth 원칙<\/h1>/
s/<p class="heading-2[^>]*>.*<\/p>/<p class="heading-2 text-stone" style="font-weight: 400;">plugins\/ 원본 → sync → .claude\/ 결과물<\/p>/
' "$SLIDES_DIR/slide-05.html"

# Slide 06: plugins/ 구조
echo "Rewriting slide-06..."
sed -i '
s/PART 01 · YOUR DESIGN · THE 14-DAY JOURNEY/PART 01 · INSTALLED STRUCTURE/
s/<h1 class="heading-1">.*<\/h1>/<h1 class="heading-1">plugins\/ 구조<\/h1>/
s/<p class="heading-2[^>]*>.*<\/p>/<p class="heading-2 text-stone" style="font-weight: 400;">25 플러그인 · 5 카테고리<\/p>/
' "$SLIDES_DIR/slide-06.html"

# Slide 07: exec_orch
echo "Rewriting slide-07..."
sed -i '
s/PART 0[0-9].*YOUR DESIGN.*/PART 02 · CORE SYSTEMS/
s/<h1 class="heading-1">.*<\/h1>/<h1 class="heading-1">exec_orch 엔진<\/h1>/
s/<p class="heading-2[^>]*>.*<\/p>/<p class="heading-2 text-stone" style="font-weight: 400;">멀티AI 오케스트레이션 — 코어 플러그인<\/p>/
' "$SLIDES_DIR/slide-07.html"

# Slide 08: SQLite 상태
echo "Rewriting slide-08..."
sed -i '
s/PART 0[0-9].*YOUR DESIGN.*/PART 02 · CORE SYSTEMS/
s/<h1 class="heading-1">.*<\/h1>/<h1 class="heading-1">중앙 상태 저장소<\/h1>/
s/<p class="heading-2[^>]*>.*<\/p>/<p class="heading-2 text-stone" style="font-weight: 400;">.claude\/state\/orca.db · 8 테이블<\/p>/
' "$SLIDES_DIR/slide-08.html"

# Slide 09: Watchdog
echo "Rewriting slide-09..."
sed -i '
s/PART 0[0-9].*YOUR DESIGN.*/PART 02 · CORE SYSTEMS/
s/<h1 class="heading-1">.*<\/h1>/<h1 class="heading-1">감시자와 자동부활<\/h1>/
s/<p class="heading-2[^>]*>.*<\/p>/<p class="heading-2 text-stone" style="font-weight: 400;">2분 주기 · 지수 backoff · quota-aware<\/p>/
' "$SLIDES_DIR/slide-09.html"

# Slide 10: Router
echo "Rewriting slide-10..."
sed -i '
s/PART 0[0-9].*YOUR DESIGN.*/PART 02 · CORE SYSTEMS/
s/<h1 class="heading-1">.*<\/h1>/<h1 class="heading-1">지능형 라우터<\/h1>/
s/<p class="heading-2[^>]*>.*<\/p>/<p class="heading-2 text-stone" style="font-weight: 400;">task_type + quota + budget → AI 결정<\/p>/
' "$SLIDES_DIR/slide-10.html"

# Slide 11: Caching
echo "Rewriting slide-11..."
sed -i '
s/PART 0[0-9].*YOUR DESIGN.*/PART 02 · CORE SYSTEMS/
s/<h1 class="heading-1">.*<\/h1>/<h1 class="heading-1">캐싱으로 85% 절감<\/h1>/
s/<p class="heading-2[^>]*>.*<\/p>/<p class="heading-2 text-stone" style="font-weight: 400;">5m\/1h TTL · Anthropic ephemeral cache<\/p>/
' "$SLIDES_DIR/slide-11.html"

# Slide 12: exec_ 계열
echo "Rewriting slide-12..."
sed -i '
s/PART 0[0-9].*YOUR DESIGN.*/PART 03 · PLUGIN CATEGORIES/
s/<h1 class="heading-1">.*<\/h1>/<h1 class="heading-1">exec_ 실행 계열<\/h1>/
s/<p class="heading-2[^>]*>.*<\/p>/<p class="heading-2 text-stone" style="font-weight: 400;">실행·코어·오케스트레이션 (5개)<\/p>/
' "$SLIDES_DIR/slide-12.html"

# Slide 13: mcp_ 계열
echo "Rewriting slide-13..."
sed -i '
s/PART 0[0-9].*YOUR DESIGN.*/PART 03 · PLUGIN CATEGORIES/
s/<h1 class="heading-1">.*<\/h1>/<h1 class="heading-1">mcp_ MCP 통합<\/h1>/
s/<p class="heading-2[^>]*>.*<\/p>/<p class="heading-2 text-stone" style="font-weight: 400;">외부 서비스 연결 (9개)<\/p>/
' "$SLIDES_DIR/slide-13.html"

# Slide 14: design_ 계열
echo "Rewriting slide-14..."
sed -i '
s/PART 0[0-9].*YOUR DESIGN.*/PART 03 · PLUGIN CATEGORIES/
s/<h1 class="heading-1">.*<\/h1>/<h1 class="heading-1">design_ 문서 생성<\/h1>/
s/<p class="heading-2[^>]*>.*<\/p>/<p class="heading-2 text-stone" style="font-weight: 400;">PPT·Excel·Word·PDF·Web·Video (6개)<\/p>/
' "$SLIDES_DIR/slide-14.html"

# Slide 15: review_qa
echo "Rewriting slide-15..."
sed -i '
s/PART 0[0-9].*YOUR DESIGN.*/PART 03 · PLUGIN CATEGORIES/
s/<h1 class="heading-1">.*<\/h1>/<h1 class="heading-1">review_qa + 기타<\/h1>/
s/<p class="heading-2[^>]*>.*<\/p>/<p class="heading-2 text-stone" style="font-weight: 400;">검증·RAG·수익화·음악 (5개)<\/p>/
' "$SLIDES_DIR/slide-15.html"

# Slide 16-20: PART 04 (플로우)
echo "Rewriting slides 16-20..."
for i in 16 17 18 19 20; do
  sed -i 's/PART 0[0-9].*YOUR DESIGN.*/PART 04 · EXECUTION FLOW/' "$SLIDES_DIR/slide-$(printf "%02d" $i).html"
done

# Slide 21-25: PART 05 (참조)
echo "Rewriting slides 21-25..."
for i in 21 22 23 24 25; do
  sed -i 's/PART 0[0-9].*YOUR DESIGN.*/PART 05 · REFERENCE/' "$SLIDES_DIR/slide-$(printf "%02d" $i).html"
done

echo "✓ All slides patched with new PART titles"
echo "Next step: Manually edit content for each slide or use generate-final-ppt.py"
