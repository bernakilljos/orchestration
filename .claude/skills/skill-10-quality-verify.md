# SKILL-10 — Quality & Performance Verification

## Purpose
Comprehensive quality and performance verification across all layers.
Runs after implementation, before review (between SKILL-02 and SKILL-03).

---

## 1. Frontend Performance

### Bundle Size Check
```bash
# Vue/Nuxt/React — analyze build output size
npm run build 2>&1 | tee docs/build-result.txt

# Check bundle size (warn if any chunk > 500KB)
# Windows
powershell -Command "Get-ChildItem dist/js/*.js | Where-Object { $_.Length -gt 512000 } | ForEach-Object { Write-Host '[WARN] Large chunk:' $_.Name ($_.Length/1KB) 'KB' }"

# Linux/Mac
find dist/js -name "*.js" -size +500k -exec ls -lh {} \; 2>/dev/null
```

### Render Performance Indicators
```
Claude checks (code review):
1. v-for without :key                        → FAIL
2. v-for + v-if on same element              → WARN (move v-if to wrapper)
3. Unnecessary watchers (computed preferred)  → WARN
4. Large inline styles or deep nesting (>5)  → WARN
5. Missing lazy-load on route components     → WARN for pages > 200 lines
6. Unthrottled scroll/resize event handlers  → WARN
7. v-html with user input                    → FAIL (XSS risk)
```

### Frontend Metrics (when Lighthouse/Playwright available)
```bash
# If playwright MCP is available, run lighthouse
# Target thresholds:
#   Performance: >= 70
#   Accessibility: >= 80
#   Best Practices: >= 80
#   First Contentful Paint: < 2s
#   Largest Contentful Paint: < 4s
```

---

## 2. Backend Performance

### API Response Time Check
```bash
# Smoke test — each API endpoint must respond < 3s
# test.sh already does basic smoke; this adds timing

# Windows (PowerShell)
powershell -Command "$urls = @('http://localhost:8080/api/health'); foreach ($u in $urls) { $sw = [System.Diagnostics.Stopwatch]::StartNew(); try { Invoke-WebRequest $u -TimeoutSec 5 | Out-Null; $sw.Stop(); $ms = $sw.ElapsedMilliseconds; if ($ms -gt 3000) { Write-Host '[WARN] Slow:' $u $ms'ms' } else { Write-Host '[OK]' $u $ms'ms' } } catch { Write-Host '[FAIL]' $u $_.Exception.Message } }"

# Linux/Mac
for url in http://localhost:8080/api/health; do
  start_time=$(date +%s%N)
  status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url")
  end_time=$(date +%s%N)
  elapsed=$(( (end_time - start_time) / 1000000 ))
  if [ "$elapsed" -gt 3000 ]; then
    echo "[WARN] Slow: $url ${elapsed}ms"
  else
    echo "[OK] $url ${elapsed}ms (HTTP $status)"
  fi
done
```

### DB Query Review
```
Claude checks (code review):
1. SELECT * without WHERE clause              → FAIL
2. N+1 query pattern (loop inside loop)       → FAIL
3. Missing @Transactional on write operations → WARN
4. No pagination on list endpoints            → WARN (if result > 100 rows possible)
5. Raw SQL without parameterized binding      → FAIL (SQL injection risk)
6. Missing index hint for large table joins   → WARN
7. LIKE '%keyword%' on large tables           → WARN (full table scan)
```

### JPA/Hibernate Specific
```
Claude checks:
1. FetchType.EAGER on @ManyToOne/@OneToMany   → WARN (prefer LAZY)
2. Missing @BatchSize on collections          → WARN
3. Entity without @ToString(exclude=...)      → WARN (lazy-load trigger)
4. No DTO projection (returning Entity to API)→ WARN
```

---

## 3. Code Quality

### Complexity Check
```
Claude checks (code review):
1. Method > 50 lines                          → WARN (suggest split)
2. Method > 100 lines                         → FAIL (must split)
3. Cyclomatic complexity > 10 (nested if/for) → WARN
4. File > 500 lines                           → WARN
5. File > 1000 lines                          → FAIL (must split)
6. Function parameters > 5                    → WARN (use object/DTO)
7. Deeply nested callbacks (> 3 levels)       → WARN
```

### Duplication Check
```bash
# Quick duplication scan — find repeated code blocks
# Windows
powershell -Command "$files = Get-ChildItem -Recurse -Include *.js,*.vue,*.java -Exclude node_modules,dist,target; $hashes = @{}; foreach ($f in $files) { $lines = Get-Content $f.FullName; for ($i=0; $i -lt $lines.Count-5; $i++) { $block = ($lines[$i..($i+4)] -join '`n').Trim(); if ($block.Length -gt 50) { $h = [System.Security.Cryptography.SHA256]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes($block)); $key = [BitConverter]::ToString($h).Substring(0,16); if ($hashes.ContainsKey($key)) { Write-Host '[DUP]' $f.Name ':' ($i+1) '~' $hashes[$key] } else { $hashes[$key] = \"$($f.Name):$($i+1)\" } } } }"
```

### Lint Summary
```bash
# Frontend
npm run lint 2>&1 | tee docs/lint-result.txt
# Count errors vs warnings
grep -c "error" docs/lint-result.txt
grep -c "warning" docs/lint-result.txt

# Backend (if checkstyle configured)
mvnw checkstyle:check -q 2>&1 | tee docs/checkstyle-result.txt
```

---

## 4. Integration Metrics

### Build Time
```bash
# Measure build duration
# Windows
powershell -Command "$sw = [System.Diagnostics.Stopwatch]::StartNew(); npm run build 2>&1 | Out-Null; $sw.Stop(); Write-Host 'Build time:' $sw.Elapsed.TotalSeconds 'seconds'; if ($sw.Elapsed.TotalSeconds -gt 120) { Write-Host '[WARN] Build > 2 min' }"

# Linux/Mac
start=$(date +%s)
npm run build > /dev/null 2>&1
elapsed=$(( $(date +%s) - start ))
echo "Build time: ${elapsed}s"
[ "$elapsed" -gt 120 ] && echo "[WARN] Build > 2 min"
```

### Test Coverage
```bash
# Vue/React (Jest)
npx jest --coverage --coverageReporters=text-summary 2>&1 | tee docs/coverage-result.txt
# Thresholds:
#   Statements: >= 60%
#   Branches:   >= 50%
#   Functions:  >= 60%
#   Lines:      >= 60%

# Spring Boot (JaCoCo)
mvnw test jacoco:report -q 2>&1
# Check target/site/jacoco/index.html for coverage %
```

### Dependency Check
```bash
# Check for known vulnerabilities
npm audit --production 2>&1 | tee docs/audit-result.txt
# FAIL if critical/high vulnerabilities found

# Check outdated packages (info only)
npm outdated 2>&1 | head -20
```

---

## Quality Report Template

```
## Quality & Performance Report

### Frontend Performance
| Item                    | Result    | Detail           |
|-------------------------|-----------|------------------|
| Bundle Size             | PASS/WARN | max chunk: XXX KB|
| Render Anti-patterns    | PASS/WARN | N issues found   |
| Lighthouse (if avail)   | PASS/WARN | score: XX        |

### Backend Performance
| Item                    | Result    | Detail           |
|-------------------------|-----------|------------------|
| API Response Time       | PASS/WARN | avg: XXX ms      |
| DB Query Anti-patterns  | PASS/WARN | N issues found   |
| N+1 Detection           | PASS/FAIL | N occurrences    |

### Code Quality
| Item                    | Result    | Detail           |
|-------------------------|-----------|------------------|
| Lint                    | PASS/FAIL | errors: N        |
| Complexity              | PASS/WARN | N methods > 50L  |
| Duplication             | PASS/WARN | N blocks found   |
| Secret Scan             | CLEAN/FOUND| N items          |

### Integration
| Item                    | Result    | Detail           |
|-------------------------|-----------|------------------|
| Build Time              | PASS/WARN | XX seconds       |
| Test Coverage           | PASS/WARN | XX% statements   |
| Dependency Audit        | PASS/FAIL | N vulnerabilities|

### Verdict: PASS / CONDITIONAL PASS / FAIL
```

---

## Failure Handling

| Severity | Items | Action |
|----------|-------|--------|
| FAIL | Secret, SQL injection, XSS, N+1, >100L method, lint errors | Block. Fix before proceeding |
| WARN | Bundle size, complexity, missing lazy-load, slow API | Proceed with note. Fix in next sprint |
| INFO | Outdated deps, build time | Log only |

## When to Run
- After every implementation (SKILL-02 → SKILL-10 → HOOK-02)
- Before deployment (HOOK-04 pre-deploy)
- On user request: "run quality check"
