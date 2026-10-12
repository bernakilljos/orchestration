#!/usr/bin/env bash
# .claude/scripts/mcp-autostart.sh — DEPRECATED 2026-10-12
# Headroom + claude-mem 완전 삭제됨 (설치만 되고 실제 압축 X · RAM 2.5GB 낭비).
# 지금은 noop. Anthropic 네이티브 prompt caching (90% 절감) 만으로 충분.
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0
exit 0
