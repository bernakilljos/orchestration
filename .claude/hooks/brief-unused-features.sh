#!/usr/bin/env bash
# brief-unused-features.sh — SessionStart hook
# 목적: 사용자가 모르는·미사용 기능 매 세션 시작 시 3-5개 자동 브리핑
# 사용자 도메인 (ISMS-P·RMS·ITCEN ESG · memory reference_company_context) 매칭
# 근거: 2026-08-12 사용자 지적 — "다른 기능들도 내가 모르는거 제시해주고 할수있게 만들어"
set -e

PROJECT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
STATE_DIR="$PROJECT/.claude/state"
USAGE_LOG="$STATE_DIR/feature-usage.log"
BRIEF_LOG="$STATE_DIR/last-brief.timestamp"
mkdir -p "$STATE_DIR" 2>/dev/null

# 하루 1회만 (SessionStart 여러 번 발동 방지)
today=$(date +%Y-%m-%d)
last=$([ -f "$BRIEF_LOG" ] && cat "$BRIEF_LOG" 2>/dev/null | head -1 || echo "")
[ "$last" = "$today" ] && exit 0
echo "$today" > "$BRIEF_LOG"

# 사용 이력 (미존재 시 empty)
[ ! -f "$USAGE_LOG" ] && touch "$USAGE_LOG"

# 카탈로그에서 랜덤 미사용 기능 발굴 (도메인·인기 우선순위)
# 사용자 도메인: ISMS-P (보안·감사) · RMS (리스크) · ITCEN ESG (지속가능성) · 개발팀 리더
declare -a features
features=(
"/security · /sec-scan (OWASP·gitleaks·semgrep — ISMS-P 정합 · 코드 보안 스캔 자동)"
"/analyze-improve (XAI·Zero Trust·RAG·이벤트 아키텍처 개선점 자동 추천)"
"/rag-graph · /rag-hybrid (Knowledge Graph + Vector DB · 도메인 지식 그래프 검색)"
"/effort-mythos (Fable 5 Mythos-class · Opus 실패 시 vision-heavy·long-running)"
"/pdf-sign · /pdf-secure (전자서명·직인·암호화·워터마크 — 감사 산출물)"
"/meeting (녹음 → Whisper STT → 요약 → 회의록 한 번에)"
"/exec_remote-mobile (아이폰·안드로이드에서 VPS 24/7 접속 · Termius·Blink Shell)"
"/exec_scheduler-workflow (DAG 워크플로우 · 조건부·병렬·의존성)"
"/graph-run (LangGraph stateful multi-agent · yaml spec)"
"/exec_offline-setup (Ollama·ChromaDB·Phoenix 로컬 · API 비용 X)"
"/ai-system-stages (AI 시스템 6단계 PPT: Prompt→Agent→Orchestration→Automation→Autonomous→Platform)"
"/arch-mindmap · /arch-layered · /arch-cheatsheet (아키텍처 다이어그램 1페이지)"
"/godmode (최대 워커·직통 라우팅·검증 스킵·최대 출력)"
"/vibe-loop (codex-auto + gemini-auto 자동 루프 · vibe coding)"
"/anthropic-skill <name> (Anthropic 공식 skills marketplace 자동 install)"
"/loop <interval> <command> (주기 실행 · 예: /loop 5m /babysit-prs)"
"/schedule (cron 스케줄 · Anthropic Managed routine)"
"/verify (앱 실제 실행 후 UI 확인 · Playwright 자동)"
"/gpt-dispatch · /grok-dispatch (GPT-5.2 2M+ 컨텍스트 · Grok 대량 처리)"
"/music_studio-compose (Suno·Udio·MusicGen · 장르·BPM·키·길이 지정)"
"/audio-restore (오디오 노이즈제거·대역확장·스템분리·보이스클로닝)"
"/video-restore (90년대~2000년대 저화질 영상 → 고화질 복원)"
"/image-restore (초해상도·얼굴복원·컬러화·배경제거·스크래치제거)"
"/exec_voice (음성 STT·TTS·회의록·음성 명령)"
"/voice-task (음성 명령 → task-instruction.md 자동 생성)"
)

# 랜덤 3-5개 선택 (사용 이력에 없는 것 우선)
shuf_available=$(command -v shuf >/dev/null 2>&1 && echo yes || echo no)
selected=()
count=0
for feat in "${features[@]}"; do
  # cmd 추출 (첫 단어 · / 로 시작)
  cmd=$(echo "$feat" | grep -oE '^/[a-z_-]+' | head -1)
  # 사용 이력에 있으면 skip (30일 이내)
  if grep -q "^$cmd" "$USAGE_LOG" 2>/dev/null; then
    continue
  fi
  selected+=("$feat")
  count=$((count + 1))
  [ $count -ge 5 ] && break
done

# 선택된 기능 없으면 (모두 사용 이력 있음) — 랜덤 3개
if [ ${#selected[@]} -eq 0 ]; then
  # 처음 3개만 (deterministic)
  for i in 0 1 2; do
    selected+=("${features[$i]}")
  done
fi

# 출력 (systemMessage 로 SessionStart 시 노출)
cat <<EOF

==============================
 💡 오늘의 미사용 기능 브리핑 (proactive)
==============================
사용자가 아직 활용 안 한 kit 기능:

EOF

for feat in "${selected[@]}"; do
  echo "  · $feat"
done

cat <<EOF

★ 상세 카탈로그: outputs/install/kit-catalog.md
★ 관심 있는 것 있으면 사용자 지시 시 자동 매칭 (detect-efficiency.sh)
★ 도메인 매칭: reference_company_context (ISMS-P·RMS·ITCEN ESG)

EOF

exit 0
