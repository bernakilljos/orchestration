# HOOK-02 — Post-Impl (Auto-run after implementation)

## Trigger
Auto-run immediately after Codex or Claude finishes implementation.

## Steps

### 1. Build gate

**Frontend (Vue/React)**
```bat
call npm run lint 2>&1 | tee docs\lint-result.txt
call npm run build 2>&1 | tee docs\build-result.txt
```

**Backend (Spring Boot)**
```bat
call mvnw compile 2>&1 | tee docs\build-result.txt
call mvnw test 2>&1 | tee docs\test-result.txt
```

**Node.js**
```bat
node --check src\index.js 2>&1 | tee docs\build-result.txt
call npm test 2>&1 | tee docs\test-result.txt
```

### 2. Hardcoding scan
```bat
rem Scan for hardcoded absolute paths in source and scripts
findstr /s /i /r /c:"C:\\Users\\" /c:"C:\\work\\" /c:"D:\\" /c:"/home/" src\*.js src\*.vue src\*.java .claude\scripts\*.bat > docs\hardcode-scan.txt 2>nul
for /f %%i in ('type docs\hardcode-scan.txt 2^>nul ^| find /c /v ""') do set HC_COUNT=%%i
if %HC_COUNT% GTR 0 (
  echo [BLOCK] Hardcoded path detected - fix before proceeding
  type docs\hardcode-scan.txt
) else (
  echo [OK] Hardcoding scan passed
)
```

### 3. Secret scan
```bat
rem Scan for hardcoded credentials
findstr /s /i /r /c:"password\s*=" /c:"api_key\s*=" /c:"secret\s*=" /c:"token\s*=" src\*.js src\*.vue src\*.java > docs\secret-scan.txt
findstr /v "process.env\|config\." docs\secret-scan.txt > docs\secret-scan-filtered.txt
for /f %%i in ('type docs\secret-scan-filtered.txt ^| find /c /v ""') do set SECRET_COUNT=%%i
if %SECRET_COUNT% GTR 0 (
  echo [BLOCK] Secret detected - abort immediately
) else (
  echo [OK] Secret scan passed
)
```

### 3. Writer rule check
```bat
git diff --name-only HEAD 2>nul > docs\changed-files.txt
type docs\changed-files.txt
```

### 4. Update current-tasks.json status
Change status: `in_progress` → `review`

Claude does this by reading and rewriting the JSON file.

### 5. Run Gemini verify
```bat
.claude\scripts\gemini.bat --verify
```

### 6. Post-Codex Structure Verification
Codex may change architecture (add files, rename modules, restructure). Verify before running Gemini:

```
Claude checks:
1. List all files Codex created/modified
2. Verify imports are consistent (no broken references)
3. Check if Codex added new routes → update store/router accordingly
4. Check if Codex renamed props → update parent components
5. List any NEW files Codex created that weren't in task-instruction.md
```

If structure changed significantly:
- Update task-instruction.md to reflect actual structure
- Update Vue pages to match new component contracts
- Notify: [STRUCTURE CHANGED] Codex reorganized - reviewed and aligned

---

## Quality Gate Summary Template

```
## Quality Gate Report

| Item        | Result |
|-------------|--------|
| Lint        | PASS/FAIL |
| Build       | PASS/FAIL |
| Test        | PASS/FAIL |
| Hardcoding  | CLEAN/FOUND |
| Secret Scan | CLEAN/FOUND |
| Writer Rule | OK/VIOLATION |

→ Next: gemini.bat --verify
```

## On Failure
- Build/Lint fail: instruct Codex to fix (1 attempt)
- Secret found: abort immediately, rollback file
- Writer violation: abort, rollback out-of-scope changes
