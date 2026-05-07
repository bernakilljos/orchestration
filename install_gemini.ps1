#requires -version 5.1
<#
.SYNOPSIS
  Gemini 단독 환경 셋업 (standalone) — v1

.DESCRIPTION
  Claude 없이 Gemini 만으로 작업할 수 있는 환경을 만듭니다.
  검증 뿐 아니라 일반 작업 (구현·요약·문서화) 도 단독 수행.
  1M 토큰 컨텍스트를 활용한 대용량 문서 요약·처리 강점.

.PARAMETER Target
  설치 대상 폴더. '.' 입력 시 현재 폴더.

.EXAMPLE
  install_gemini.ps1 C:\work\myproject
  install_gemini.ps1 .
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
  Write-Host "사용법: install_gemini C:\work\myproject"
  exit 1
}
if ($Target -eq '.') { $Target = (Get-Location).Path }
$Target = [IO.Path]::GetFullPath($Target)

Write-Host ""
Write-Host "============================================================"
Write-Host "  Gemini Standalone 환경 설치: $Target"
Write-Host "============================================================"
Write-Host "  * Claude 없이 Gemini 단독으로 작업 가능"
Write-Host "  * 풀 orchestration 원하면 install.bat 사용"
Write-Host ""

# --- [1/6] 폴더 ---
Write-Host "[1/6] 폴더 구조..."
$folders = @('.gemini', 'tasks', 'tasks\done', 'docs')
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

# --- [2/6] GEMINI.md ---
Write-Host "[2/6] GEMINI.md (Gemini 지시서)..."
$src = Join-Path $ScriptDir 'GEMINI.md'
if (Test-Path $src) {
  Copy-Item -Path $src -Destination (Join-Path $Target 'GEMINI.md') -Force
  Write-Host "      [OK] GEMINI.md"
}
else {
  Write-Host "[WARN] GEMINI.md 없음" -ForegroundColor Yellow
}

# --- [3/6] .env.example ---
Write-Host "[3/6] .env.example (API 키 및 설정 템플릿)..."
$envFile = Join-Path $Target '.env.example'
if (-not (Test-Path $envFile)) {
  $envContent = @'
# Gemini Standalone 환경변수
# 필수: GOOGLE_API_KEY 설정

GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE

# 선택: Gemini 모델 선택 (기본값: gemini-2.0-flash)
# gemini-2.0-flash     — 최신, 빠르고 저단가
# gemini-1.5-pro       — 고성능, 1M 컨텍스트
# GEMINI_MODEL=gemini-2.0-flash

# 선택: 일일 토큰 한도 (초과 시 경고, 기본값: 무제한)
# GEMINI_DAILY_LIMIT_USD=20
'@
  Set-Content -Path $envFile -Value $envContent -Encoding UTF8
  Write-Host "      [OK] .env.example"
}
else {
  Write-Host "      [OK] .env.example 이미 존재"
}

# --- [4/6] .gemini/config.toml ---
Write-Host "[4/6] .gemini\config.toml (MCP 설정)..."
$tomlSrc = Join-Path $ScriptDir '.gemini\config.toml'
if (Test-Path $tomlSrc) {
  Copy-Item -Path $tomlSrc -Destination (Join-Path $Target '.gemini\config.toml') -Force
  Write-Host "      [OK] .gemini\config.toml"
}
else {
  Write-Host "[WARN] .gemini\config.toml 없음" -ForegroundColor Yellow
}

# --- [5/6] gemini-go.bat ---
Write-Host "[5/6] gemini-go.bat (자연어 -> 즉시 작업)..."
$geminiGoContent = @'
@echo off
chcp 65001 >nul
rem gemini-go - 자연어 한 줄로 제미니 실행 (또는 인자 없으면 대화 모드)
rem 사용:  gemini-go "이 코드 검증해줘"
rem        gemini-go "로그 100MB 요약해줘"      (1M 컨텍스트 활용)
rem        gemini-go                       (대화 모드)

setlocal enabledelayedexpansion
set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
cd /d "%PROJECT_ROOT%"

rem --- API 키 검증 ---
if "%GOOGLE_API_KEY%"=="" (
  if exist "!PROJECT_ROOT!\.env" (
    for /f "usebackq tokens=2 delims==" %%I in (`findstr /B "GOOGLE_API_KEY" "!PROJECT_ROOT!\.env"`) do set "GOOGLE_API_KEY=%%I"
  )
)
if "%GOOGLE_API_KEY%"=="" (
  echo [ERROR] GOOGLE_API_KEY 설정되지 않음
  echo.
  echo 다음 중 하나를 실행하세요:
  echo   1. 환경변수 설정: setx GOOGLE_API_KEY "..."
  echo   2. .env 파일 편집: %PROJECT_ROOT%\.env
  echo   3. 직접 명령: set GOOGLE_API_KEY=... ^&^& gemini-go "..."
  echo.
  exit /b 1
)

rem --- CLI 검증 ---
where gemini >nul 2>&1 || (echo [ERROR] gemini CLI 미설치 - npm i -g @google/gemini-cli & exit /b 1)

rem --- 모델 선택 (기본값: gemini-2.0-flash) ---
if "%GEMINI_MODEL%"=="" set "GEMINI_MODEL=gemini-2.0-flash"

rem --- 일일 예산 체크 (선택) ---
if not "%GEMINI_DAILY_LIMIT_USD%"=="" (
  if exist "!PROJECT_ROOT!\.gemini\usage.jsonl" (
    findstr /C """ts""" "!PROJECT_ROOT!\.gemini\usage.jsonl" | find /c /v "" >nul
    if not errorlevel 1 echo [INFO] 오늘의 사용량은 .gemini\usage.jsonl 확인
  )
)

if "%~1"=="" (
  echo [Gemini 대화 모드 시작 - %CD% - 모델: %GEMINI_MODEL%]
  gemini --model "%GEMINI_MODEL%"
) else (
  echo [Gemini 작업 시작 - 모델: %GEMINI_MODEL%] %~1
  gemini --model "%GEMINI_MODEL%" %*
)
endlocal
'@
Set-Content -Path (Join-Path $Target 'gemini-go.bat') -Value $geminiGoContent -Encoding UTF8
Write-Host "      [OK] gemini-go.bat"

# --- [6/6] tasks/README.md ---
Write-Host "[6/6] tasks\README.md (배치 처리 안내)..."
$readmePath = Join-Path $Target 'tasks\README.md'
if (-not (Test-Path $readmePath)) {
  $readmeContent = @'
# tasks/ — 배치 작업 폴더 (선택)

## 일반 사용 — 자연어 한 줄
그냥 이렇게 하면 됩니다, task 파일 만들 필요 없음:

```
gemini-go "이 코드 보안 검증해줘"
gemini-go "긴 로그 요약해줘"        # 1M 컨텍스트 활용
gemini-go "README 작성해줘"
gemini-go                            # 대화 모드
```

## 배치 처리 (여러 작업 한꺼번에)
여러 작업을 큐에 쌓아 자동 처리하고 싶을 때만 task 파일 작성.
Gemini 에게 "task 파일 만들어줘" 라고 부탁해도 됩니다:

```
gemini-go "다음 3개 작업을 tasks/task-001.md, task-002.md, task-003.md 로 정리해줘:
 1. 인증 모듈 보안 검증
 2. 로그 100MB 요약
 3. API 문서 자동 생성"

gemini-a --auto    # 큐 자동 처리
```

## Gemini 강점
- 1M 토큰 컨텍스트 (긴 문서·로그 한 번에)
- 저단가 (반복 검증·요약에 좋음)
- 빠른 응답 속도

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
Write-Host "  [OK] Gemini Standalone v1 설치 완료" -ForegroundColor Green
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
Write-Host '        setx GOOGLE_API_KEY "YOUR_API_KEY"'
Write-Host ""
Write-Host "     b. .env 파일:"
Write-Host "        copy `"$Target\.env.example`" `"$Target\.env`""
Write-Host "        [편집기로 GOOGLE_API_KEY 값 입력]"
Write-Host ""
Write-Host "     c. 명령줄에서:"
Write-Host '        set GOOGLE_API_KEY=... && gemini-go "작업"'
Write-Host ""
Write-Host "============================================================"
Write-Host "  사용 방법 (자연어 한 줄이면 끝)"
Write-Host "============================================================"
Write-Host ""
Write-Host "  1. 검증 (기본 역할):"
Write-Host ""
Write-Host "     cd /d `"$Target`""
Write-Host '     gemini-go "이 코드 보안 검증해줘"'
Write-Host '     gemini-go "PR 코드 리뷰해줘"'
Write-Host ""
Write-Host "  2. 1M 컨텍스트 활용 (Gemini 강점):"
Write-Host ""
Write-Host '     gemini-go "100MB 로그 파일 분석해줘"      # 1M 토큰으로 처리'
Write-Host '     gemini-go "긴 문서 요약해줘"              # 빠르고 저단가'
Write-Host ""
Write-Host "  3. 일반 작업 (구현·문서화 등):"
Write-Host ""
Write-Host '     gemini-go "회원가입 페이지 만들어줘"'
Write-Host '     gemini-go "README 작성해줘"'
Write-Host "     gemini-go                            # 대화 모드"
Write-Host ""
Write-Host "  4. 배치 처리 (여러 작업 한꺼번에):"
Write-Host ""
Write-Host '     gemini-go "task-*.md 파일들을 만들어줘"'
Write-Host "     gemini-a --auto"
Write-Host ""
Write-Host "============================================================"
Write-Host "  파일 및 설정"
Write-Host "============================================================"
Write-Host ""
Write-Host "  설치 파일:"
Write-Host "    GEMINI.md              Gemini 지시서 (업무 규칙)"
Write-Host "    .gemini\config.toml    MCP 설정"
Write-Host "    .gemini\usage.jsonl    토큰 사용량 기록 (자동 생성)"
Write-Host "    .env.example           API 키·모델·예산 설정 템플릿"
Write-Host "    gemini-go.bat          자연어 명령 단축기"
Write-Host "    tasks\README.md        배치 사용법"
Write-Host ""
Write-Host "  선택 설정:"
Write-Host "    - 모델 선택: .env 에 GEMINI_MODEL=gemini-1.5-pro 추가 (1M 컨텍스트)"
Write-Host "    - 일일 예산: .env 에 GEMINI_DAILY_LIMIT_USD=20 추가"
Write-Host ""
Write-Host "============================================================"
Write-Host "  Full 모드로 업그레이드 (Claude + Codex + Gemini)"
Write-Host "============================================================"
Write-Host ""
Write-Host "  언제든 아래 명령으로 Full orchestration 추가 가능:"
Write-Host "    install.bat `"$Target`""
Write-Host ""
Write-Host "  -> 기존 .gemini\ 유지 + .claude\ 레이어 추가"
Write-Host "  -> Claude 설계 -> Codex 구현 -> Gemini 검증 자동화"
Write-Host ""
Write-Host "============================================================"
Write-Host ""

exit 0
