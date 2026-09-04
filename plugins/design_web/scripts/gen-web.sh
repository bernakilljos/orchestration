#!/usr/bin/env bash
# design_web plugin — HTML/Tailwind 웹사이트 자동 생성
# Claude 가 직접 생성. 이 wrapper 는 템플릿 인자만 받음.
set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT_DIR="${OUT_DIR:-$PROJECT_ROOT/outputs/web}"
mkdir -p "$OUT_DIR"

TYPE="${1:-landing}"   # landing | blog | docs
NAME="${2:-untitled}"

echo "[design_web] $TYPE 페이지 생성 — output: $OUT_DIR/$NAME"
echo "Claude 가 HTML/Tailwind 코드 직접 생성. 다음 templates 활용:"
echo "  - landing: 헤더-hero-features-cta-footer (5 섹션)"
echo "  - blog:    title-meta-content-comments"
echo "  - docs:    sidebar-content-toc"
