#!/usr/bin/env bash
# file_lock_poller.sh — 파일 잠금 / 외부 의존 fail 시 자동 폴링 라이브러리
#
# 룰: .claude/rules/best-practices.md § 멈춤 방지
#      feedback_no_user_stop.md
#
# 사용 (source 또는 직접 호출):
#   . file_lock_poller.sh
#   wait_unlock <file_path> [max_sec=60] [interval=2]
#   exp_backoff <retries> <command...>

# wait_unlock — 파일 잠금 해제까지 폴링
wait_unlock() {
  local path="$1"
  local max_sec="${2:-60}"
  local interval="${3:-2}"
  local elapsed=0

  while [ "$elapsed" -lt "$max_sec" ]; do
    # write 가능 테스트 (rename trick)
    local test_path="${path}.lock-test-$$"
    if mv "$path" "$test_path" 2>/dev/null; then
      mv "$test_path" "$path" 2>/dev/null
      return 0
    fi

    if [ "$elapsed" -eq 0 ]; then
      echo "[WAIT] $path 잠김 — ${max_sec}초 폴링 (interval=${interval}s)" >&2
    fi
    sleep "$interval"
    elapsed=$((elapsed + interval))
  done

  echo "[FAIL] $path 잠금 풀리지 않음 (${max_sec}초 경과)" >&2
  return 1
}

# exp_backoff — 명령 실행 + 지수 backoff retry
# Usage: exp_backoff <max_retries> <command...>
exp_backoff() {
  local max_retries="$1"
  shift
  local i=0
  local delay=2

  while [ "$i" -lt "$max_retries" ]; do
    if "$@"; then
      return 0
    fi
    i=$((i + 1))
    if [ "$i" -lt "$max_retries" ]; then
      echo "[RETRY $i/$max_retries] sleep ${delay}s" >&2
      sleep "$delay"
      delay=$((delay * 2))
    fi
  done

  echo "[FAIL] ${max_retries} retries 후 실패: $*" >&2
  return 1
}

# install_tool_if_missing — 도구 자동 설치
install_tool_if_missing() {
  local tool="$1"
  local install_cmd="$2"

  if command -v "$tool" >/dev/null 2>&1; then
    return 0
  fi

  echo "[INSTALL] $tool 자동 설치 시도: $install_cmd" >&2
  eval "$install_cmd" >&2 2>&1 || {
    echo "[FAIL] $tool 설치 실패" >&2
    return 1
  }

  command -v "$tool" >/dev/null 2>&1
}

# 모듈로 source 되면 함수만 export. 직접 실행 시 demo.
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  echo "file_lock_poller.sh — library (source 해서 사용)"
  echo ""
  echo "functions:"
  echo "  wait_unlock <path> [max_sec=60] [interval=2]"
  echo "  exp_backoff <max_retries> <command...>"
  echo "  install_tool_if_missing <tool> <install_cmd>"
fi
