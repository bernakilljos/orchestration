# status-push.ps1 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| 1 | UTF-8 BOM 인코딩 | **PASS** | 첫 3바이트 `EF BB BF` 확인됨 |
| 2 | PowerShell 문법 에러 | **PASS** | `Parser::ParseFile` 결과 ERROR_COUNT=0 |
| 3 | try/catch/finally 줄바꿈 파싱 에러 | **PASS** | 모든 try/catch/finally 블록이 같은 줄 또는 올바른 위치에 여는 중괄호 배치. 파싱 에러 가능성 없음 |
| 4 | 자동 업데이트 로직 | **PASS** | L3-26: git clone --depth 1 -> MD5 해시 비교 -> Copy-Item 자기 교체 -> 재실행(& $selfPath) -> exit 0. 임시 디렉토리 정리도 성공/실패 양쪽에서 수행 |
| 5 | DPI-aware 스크린 캡처 | **PASS** | L287-289 `Push-ScreenToDashboard`와 L372-374 `Capture-Screen` 양쪽 모두 `SetProcessDPIAware()` 호출. 중복 호출 방지를 위해 클래스명을 `DpiAware` / `DpiAware2`로 구분 |
| 6 | click/key 명령 처리 (Add-Type MemberDefinition) | **PASS** | L435-436: `$csDef` 변수에 `SetCursorPos` + `mouse_event` DllImport 저장 후 `Add-Type -MemberDefinition $csDef`. key 명령은 L446에서 `SendKeys::SendWait` 사용 |
| 7 | stale lock 정리 (30분 초과) | **PASS** | L163-168: `LastWriteTime` 기준 30분 초과 lock 파일 자동 삭제. `Remove-Item -Force -ErrorAction SilentlyContinue` 사용 |
| 8 | git push fallback 임시 디렉토리 정리 | **PASS** | L466: `finally` 블록에서 `Remove-Item $tmpDir -Recurse -Force` 수행. `Fetch-UrlsFromGitHub` (L79-81)도 finally에서 정리 |
| 9 | PAT 토큰 로그 노출 | **FAIL** | L8, L37: PAT 토큰이 하드코딩되어 소스에 평문 노출 (`[REMOVED]`). git clone URL에 PAT가 포함되어(L11, L69, L403) 에러 발생 시 `catch` 블록의 `$_` 출력(L465)으로 PAT가 로그에 노출될 수 있음 |
| 10 | $GH_REFETCH_INTERVAL = 10초 | **PASS** | L62: `$GH_REFETCH_INTERVAL = 10` 확인 |

---

## 상세 소견

### FAIL #9 - PAT 하드코딩 및 로그 노출 위험

**심각도: CRITICAL**

1. **하드코딩된 PAT** (L8, L37):
   ```powershell
   if (-not $pat0) { $pat0 = '[REMOVED]' }
   if (-not $pat) { $pat = '[REMOVED]' }
   ```
   환경 변수 `GITHUB_PERSONAL_ACCESS_TOKEN`이 없을 때 하드코딩된 PAT로 폴백. 이 파일이 공개 저장소에 포함되면 토큰 유출.

2. **로그 노출 경로**:
   - L465: `Write-Host "[WARN] git push failed: $_"` -- `$_`에 git clone URL(PAT 포함)이 포함될 수 있음
   - L404: `Write-Host "[WARN] git clone failed"` -- 이것은 안전하지만, git 자체 stderr 출력이 콘솔에 보일 수 있음 (L403의 `2>&1 | Out-Null`로 억제 중)

**권장 수정:**
- 하드코딩된 PAT 제거, 환경 변수 미설정 시 에러 메시지 출력 후 해당 기능 스킵
- L465의 에러 출력에서 URL/PAT 마스킹 처리

### 기타 참고 사항

- **WARN**: `$ErrorActionPreference = 'SilentlyContinue'` (L1)가 전역으로 설정되어 예상치 못한 에러가 무시될 수 있음
- **WARN**: 자동 업데이트(L20 `& $selfPath`)에서 무한 루프 방지 로직 없음. 원격 파일이 매번 다른 해시를 반환하면 무한 재시작 가능 (실제로는 교체 후 해시가 같아지므로 1회만 재시작되지만, 네트워크/파일시스템 이슈 시 위험)
- L454 `Set-Location $tmpDir` 후 실패 시 L463 `Set-Location $env:TEMP`로 복구하지만, finally 블록이 아닌 catch 이후에 위치하여 예외 경로에서 작업 디렉토리가 복구되지 않을 수 있음 (실제로는 L463이 finally 전에 실행되므로 문제 없음)

---

## 종합

| 결과 | 건수 |
|------|------|
| PASS | 9 |
| FAIL | 1 |
| WARN | 0 (상세 소견에 참고용 WARN 2건) |

**핵심 조치 필요: PAT 하드코딩 제거 및 로그 마스킹 처리**
