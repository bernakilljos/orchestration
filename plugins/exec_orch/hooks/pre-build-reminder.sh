#!/bin/bash
# pre-build-reminder.sh — PreToolUse Bash hook
#
# 빌더 명령 (build/generate/render-*.py) 실행 전 핵심 rule 강제 reminder.
# systemMessage 로 Claude 컨텍스트 주입 -> 까먹기 어려움.
#
# 트리거 패턴: build-*-doc.py / build-*-diagrams.py / generate-*-ppt.py / render-*-pdf.py

set -uo pipefail

INPUT="$(cat)"

if command -v jq >/dev/null 2>&1; then
  CMD="$(echo "$INPUT" | jq -r '.tool_input.command // ""')"
else
  CMD="$(echo "$INPUT" | grep -oE '"command"\s*:\s*"[^"]*"' | head -1 | sed 's/.*:"\(.*\)"/\1/')"
fi

# 빌더 명령 매칭
if ! echo "$CMD" | grep -qE '(build|generate|render)-[a-z-]+-(ppt|doc|diagrams|pdf|html)\.py|build-[a-z-]+-doc\.py'; then
  exit 0
fi

# systemMessage 형식 — Claude 컨텍스트 자동 주입
cat <<'EOF'
{
  "systemMessage": "[pre-build] 빌드 전 5중박기 reminder (놓치면 농땡이):\n1. 페이지 콘텐츠 fit — H1(0.55) + callout(0.5) + 이미지 ≤ 7.33 inch (landscape A4 사용)\n2. PNG 비율 = 페이지 비율 (landscape 0.69 / portrait 1.46 / pptx 16:9 0.54)\n3. 캡션 '(HTML/CSS+SVG)' 같은 메타 정보 노출 금지 (사용자 불필요)\n4. 글씨 가독성 — viewport 작을수록 docx 화면 표시 비율 ↑\n5. 빌드 후 verify-image-fit + hook-09 자동 검증 — 위반 시 즉시 알림\n6. PageLayoutTracker 사용 (auto-layout-fit skill) — 자동 max_height 계산\n7. 산출물 자동 -v2 폴백 X — .bak 백업 후 덮어쓰기\n8. 잠금 fail 시 60초 폴링 (즉시 sys.exit X)"
}
EOF

exit 0
