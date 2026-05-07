#requires -version 5.1
<#
.SYNOPSIS
  Codex 단독 환경 셋업 (standalone) — v1

.DESCRIPTION
  Claude 없이 Codex 만으로 작업할 수 있는 환경을 만듭니다.
  풀 orchestration 은 install.bat (Claude+Codex+Gemini) 를 사용.

.PARAMETER Target
  설치 대상 폴더. '.' 입력 시 현재 폴더.

.EXAMPLE
  install_codex.ps1 C:\work\myproject
  install_codex.ps1 .
#>

param(
  [Parameter(Mandatory = $false, Position = 0)]
  [string]$Target
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ScriptDir = $PSScriptRoot

if ([string]::IsNullOrWhiteSpace($Target)) {
  Write-Host "[ERROR] 대상 경로를 입력하세요." -ForegroundColor Red
  Write-Host "사용법: install_codex C:\work\myproject"
  exit 1
}
if ($Target -eq '.') { $Target = (Get-Location).Path }
$Target = [IO.Path]::GetFullPath($Target)

Write-Host ""
Write-Host "============================================================"
Write-Host "  Codex Standalone 환경 설치: $Target"
Write-Host "============================================================"
Write-Host "  * Claude 없이 Codex 단독으로 작업 가능"
Write-Host "  * 풀 orchestration 원하면 install.bat 사용"
Write-Host ""

# --- [1/6] 폴더 ---
Write-Host "[1/6] 폴더 구조..."
$folders = @('.codex', 'tasks', 'tasks\done', 'docs')
foreach ($d in $folders) {
  $p = Join-Path $Target $d
  if (-not (Test-Path $p)) {
    New-Item -ItemType Directory -Path $p -Force | Out-Null
    Write-Host "      created: $d"
  }
  else {
    Write-Host "      [OK] $d"
  }
}

# --- [2/6] AGENTS.md ---
Write-Host "[2/6] AGENTS.md (Codex 지시서)..."
$src = Join-Path $ScriptDir 'AGENTS.md'
if (Test-Path $src) {
  Copy-Item -Path $src -Destination (Join-Path $Target 'AGENTS.md') -Force
  Write-Host "      [OK] AGENTS.md"
}
else {
  Write-Host "[WARN] AGENTS.md 없음" -ForegroundColor Yellow
}

# --- [3/6] .env.example ---
Write-Host "[3/6] .env.example (API 키 및 설정 템플릿)..."
$envFile = Join-Path $Target '.env.example'
if (-not (Test-Path $envFile)) {
  $envContent = @'
# Codex Standalone 환경변수
# 필수: OPENAI_API_KEY 설정

OPENAI_API_KEY=sk-YOUR_API_KEY_HERE

# 선택: 일일 토큰 한도 (초과 시 경고, 기본값: 무제한)
# CODEX_DAILY_LIMIT_USD=10

# 선택: Codex 모델 선택 (기본값: gpt-4)
# CODEX_MODEL=gpt-4
'@
  Set-Content -Path $envFile -Value $envContent -Encoding UTF8
  Write-Host "      [OK] .env.example"
}
else {
  Write-Host "      [OK] .env.example 이미 존재"
}

# --- [4/6] .codex/config.toml ---
Write-Host "[4/6] .codex\config.toml (MCP 설정)..."
$tomlSrc = Join-Path $ScriptDir '.codex\config.toml'
if (Test-Path $tomlSrc) {
  Copy-Item -Path $tomlSrc -Destination (Join-Path $Target '.codex\config.toml') -Force
  Write-Host "      [OK] .codex\config.toml"
}
else {
  Write-Host "[WARN] .codex\config.toml 없음" -ForegroundColor Yellow
}

# --- [5/6] codex-go.bat ---
Write-Host "[5/6] codex-go.bat (자연어 -> 즉시 작업)..."
$codexGoContent = @'
@echo off
chcp 65001 >nul
rem codex-go - 자연어 한 줄로 코덱스 실행 (또는 인자 없으면 대화 모드)
rem 사용:  codex-go "회원가입 페이지 만들어줘"
rem        codex-go                       (대화 모드)

setlocal enabledelayedexpansion
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
cd /d "%PROJECT_ROOT%"

rem --- API 키 검증 ---
if "%OPENAI_API_KEY%"=="" (
  if exist "!PROJECT_ROOT!\.env" (
    for /f "usebackq tokens=2 delims==" %%I in (`findstr /B "OPENAI_API_KEY" "!PROJECT_ROOT!\.env"`) do set "OPENAI_API_KEY=%%I"
  )
)
if "%OPENAI_API_KEY%"=="" (
  echo [ERROR] OPENAI_API_KEY 설정되지 않음
  echo.
  echo 다음 중 하나를 실행하세요:
  echo   1. 환경변수 설정: setx OPENAI_API_KEY "sk-..."
  echo   2. .env 파일 편집: %PROJECT_ROOT%\.env
  echo   3. 직접 명령: set OPENAI_API_KEY=sk-... ^&^& codex-go "..."
  echo.
  exit /b 1
)

rem --- CLI 검증 ---
where codex >nul 2>&1 || (echo [ERROR] codex CLI 미설치 - npm i -g @openai/codex & exit /b 1)

rem --- 일일 예산 체크 (선택) ---
if not "%CODEX_DAILY_LIMIT_USD%"=="" (
  if exist "!PROJECT_ROOT!\.codex\usage.jsonl" (
    findstr /C """ts""" "!PROJECT_ROOT!\.codex\usage.jsonl" | find /c /v "" >nul
    if not errorlevel 1 echo [INFO] 오늘의 사용량은 .codex\usage.jsonl 확인
  )
)

if "%~1"=="" (
  echo [Codex 대화 모드 시작 - %CD%]
  codex
) else (
  echo [Codex 작업 시작] %~1
  codex %*
)
endlocal
'@
Set-Content -Path (Join-Path $Target 'codex-go.bat') -Value $codexGoContent -Encoding UTF8
Write-Host "      [OK] codex-go.bat"

# --- [6/6] tasks/README.md ---
Write-Host "[6/6] tasks\README.md (배치 처리 안내)..."
$readmePath = Join-Path $Target 'tasks\README.md'
if (-not (Test-Path $readmePath)) {
  $readmeContent = @'
# tasks/ — 배치 작업 폴더 (선택)

## 일반 사용 — 자연어 한 줄
그냥 이렇게 하면 됩니다, task 파일 만들 필요 없음:

```
codex-go "회원가입 페이지 만들어줘"
codex-go "이 모듈 리팩토링해줘 — DRY 원칙"
codex-go                           # 대화 모드
```

## 배치 처리 (여러 작업 한꺼번에)
여러 작업을 큐에 쌓아 자동 처리하고 싶을 때만 task 파일 작성.
Codex 에게 "task 파일 만들어줘" 라고 부탁해도 됩니다:

```
codex-go "다음 3개 작업을 tasks/task-001.md, task-002.md, task-003.md 로 정리해줘:
 1. 로그인 페이지
 2. 회원가입 페이지
 3. 비밀번호 리셋"

codex-a --auto    # 큐 자동 처리
```

## 폴더 의미
- `tasks/`        대기 중인 작업 (task-NNN.md)
- `tasks/done/`   완료된 작업 보관 (자동 이동)
'@
  Set-Content -Path $readmePath -Value $readmeContent -Encoding UTF8
  Write-Host "      [OK] tasks\README.md"
}
else {
  Write-Host "      [OK] tasks\README.md 이미 존재"
}

# --- 완료 메시지 ---
Write-Host ""
Write-Host "============================================================"
Write-Host "  [OK] Codex Standalone v1 설치 완료" -ForegroundColor Green
Write-Host "============================================================"
Write-Host ""
Write-Host "  대상: $Target"
Write-Host ""
Write-Host "============================================================"
Write-Host "  다음 단계 (필수)"
Write-Host "============================================================"
Write-Host ""
Write-Host "  1. API 키 설정 (3가지 방법):"
Write-Host ""
Write-Host "     a. 환경변수 (권장):"
Write-Host '        setx OPENAI_API_KEY "sk-YOUR_API_KEY"'
Write-Host ""
Write-Host "     b. .env 파일:"
Write-Host "        copy `"$Target\.env.example`" `"$Target\.env`""
Write-Host "        [편집기로 OPENAI_API_KEY 값 입력]"
Write-Host ""
Write-Host "     c. 명령줄에서:"
Write-Host '        set OPENAI_API_KEY=sk-YOUR_API_KEY && codex-go "작업"'
Write-Host ""
Write-Host "============================================================"
Write-Host "  사용 방법 (자연어 한 줄이면 끝)"
Write-Host "============================================================"
Write-Host ""
Write-Host "  1. 자연어 직시 (권장):"
Write-Host ""
Write-Host "     cd /d `"$Target`""
Write-Host '     codex-go "회원가입 페이지 만들어줘"'
Write-Host '     codex-go "이 모듈 리팩토링 — DRY 원칙"'
Write-Host "     codex-go                             # 대화 모드"
Write-Host ""
Write-Host "  2. 배치 처리 (여러 작업 한꺼번에):"
Write-Host ""
Write-Host '     codex-go "task-*.md 파일들을 만들어줘"'
Write-Host "     codex-a --auto"
Write-Host ""
Write-Host "============================================================"
Write-Host "  파일 및 설정"
Write-Host "============================================================"
Write-Host ""
Write-Host "  설치 파일:"
Write-Host "    AGENTS.md               Codex 지시서 (업무 규칙)"
Write-Host "    .codex\config.toml      MCP 설정"
Write-Host "    .codex\usage.jsonl      토큰 사용량 기록 (자동 생성)"
Write-Host "    .env.example            API 키 및 예산 설정 템플릿"
Write-Host "    codex-go.bat            자연어 명령 단축기"
Write-Host "    tasks\README.md         배치 사용법"
Write-Host ""
Write-Host "  선택 설정:"
Write-Host "    - 일일 예산 상한: .env 에 CODEX_DAILY_LIMIT_USD=10 추가"
Write-Host "    - 모델 선택: .env 에 CODEX_MODEL=gpt-4 추가"
Write-Host ""
Write-Host "============================================================"
Write-Host "  Full 모드로 업그레이드 (Claude + Codex + Gemini)"
Write-Host "============================================================"
Write-Host ""
Write-Host "  언제든 아래 명령으로 Full orchestration 추가 가능:"
Write-Host "    install.bat `"$Target`""
Write-Host ""
Write-Host "  -> 기존 .codex\ 유지 + .claude\ 레이어 추가"
Write-Host "  -> Claude 설계 -> Codex 구현 -> Gemini 검증 자동화"
Write-Host ""
Write-Host "============================================================"
Write-Host ""

exit 0
