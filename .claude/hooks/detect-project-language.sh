#!/usr/bin/env bash
# detect-project-language.sh — SessionStart hook
# 목적: target 프로젝트 언어 자동 감지 · .claude/state/project-language.json 저장

set -e

# Guard: plugins 폴더 없으면 exit (다른 프로젝트에서 실행 방지)
[ -d "${CLAUDE_PROJECT_DIR:-$PWD}/plugins" ] || exit 0

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
STATE_DIR="$PROJECT_ROOT/.claude/state"
OUTPUT_FILE="$STATE_DIR/project-language.json"

# State 디렉토리 생성
mkdir -p "$STATE_DIR"

# 감지 매트릭스
detect_language() {
  local scan_dir="${1:-.}"
  local lang="unknown"
  local build_tool=""
  local deploy_format=""

  # pom.xml → Java Maven
  if find "$scan_dir" -maxdepth 3 -name "pom.xml" -type f 2>/dev/null | grep -q .; then
    lang="java"
    build_tool="maven"
    deploy_format="jar/war"
    echo "$lang|$build_tool|$deploy_format"
    return 0
  fi

  # build.gradle → Java Gradle
  if find "$scan_dir" -maxdepth 3 -name "build.gradle*" -type f 2>/dev/null | grep -q .; then
    lang="java"
    build_tool="gradle"
    deploy_format="jar/war"
    echo "$lang|$build_tool|$deploy_format"
    return 0
  fi

  # *.csproj → .NET
  if find "$scan_dir" -maxdepth 3 -name "*.csproj" -type f 2>/dev/null | grep -q .; then
    lang="csharp"
    build_tool="dotnet"
    deploy_format="dll/nupkg"
    echo "$lang|$build_tool|$deploy_format"
    return 0
  fi

  # Cargo.toml → Rust
  if find "$scan_dir" -maxdepth 3 -name "Cargo.toml" -type f 2>/dev/null | grep -q .; then
    lang="rust"
    build_tool="cargo"
    deploy_format="binary"
    echo "$lang|$build_tool|$deploy_format"
    return 0
  fi

  # go.mod → Go
  if find "$scan_dir" -maxdepth 3 -name "go.mod" -type f 2>/dev/null | grep -q .; then
    lang="go"
    build_tool="go"
    deploy_format="binary"
    echo "$lang|$build_tool|$deploy_format"
    return 0
  fi

  # pyproject.toml → Python
  if find "$scan_dir" -maxdepth 3 -name "pyproject.toml" -type f 2>/dev/null | grep -q .; then
    lang="python"
    build_tool="uv/pip"
    deploy_format="wheel/source"
    echo "$lang|$build_tool|$deploy_format"
    return 0
  fi

  # package.json → Node.js
  if find "$scan_dir" -maxdepth 3 -name "package.json" -type f 2>/dev/null | grep -q .; then
    lang="javascript"
    build_tool="npm/pnpm/yarn"
    deploy_format="npm/docker"
    echo "$lang|$build_tool|$deploy_format"
    return 0
  fi

  # Gemfile → Ruby
  if find "$scan_dir" -maxdepth 3 -name "Gemfile" -type f 2>/dev/null | grep -q .; then
    lang="ruby"
    build_tool="bundler"
    deploy_format="gem"
    echo "$lang|$build_tool|$deploy_format"
    return 0
  fi

  # pubspec.yaml → Flutter/Dart
  if find "$scan_dir" -maxdepth 3 -name "pubspec.yaml" -type f 2>/dev/null | grep -q .; then
    lang="dart"
    build_tool="flutter/pub"
    deploy_format="app/package"
    echo "$lang|$build_tool|$deploy_format"
    return 0
  fi

  # default
  echo "$lang|$build_tool|$deploy_format"
}

# 실행
RESULT=$(detect_language "$PROJECT_ROOT")
IFS='|' read -r LANG BUILD_TOOL DEPLOY_FORMAT <<< "$RESULT"

# JSON 저장
cat > "$OUTPUT_FILE" <<EOF
{
  "language": "$LANG",
  "build_tool": "$BUILD_TOOL",
  "deploy_format": "$DEPLOY_FORMAT",
  "detected_at": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "project_root": "$PROJECT_ROOT"
}
EOF

echo "[detect-language] $LANG detected · build_tool=$BUILD_TOOL · deploy_format=$DEPLOY_FORMAT"
