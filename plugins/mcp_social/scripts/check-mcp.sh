#!/usr/bin/env bash
# mcp_social plugin — Social MCP 서버 등록 상태 체크
set -e
echo "[mcp_social] MCP 서버 체크:"
if command -v claude >/dev/null 2>&1; then
  echo "  ✅ Claude CLI 있음 — /mcp 로 등록 가능"
  echo "  설치 예: claude mcp add youtube npx -y @anaisbetts/mcp-youtube"
  echo "          claude mcp add instagram ..."
else
  echo "  ❌ Claude CLI 없음"
fi
echo "  Phase 1 권장: YouTube MCP 우선 (수익화)"
