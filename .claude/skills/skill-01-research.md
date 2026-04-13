# SKILL-01 — Research (Exploration & Analysis)

## Purpose
Understand the project structure and identify risk points before implementation.

## Execution Order

### 1. Understand Project Structure
```bash
# Auto-detect stack from project root
find . -type f \( -name "*.vue" -o -name "*.jsx" -o -name "*.tsx" -o -name "*.svelte" \
  -o -name "*.js" -o -name "*.ts" -o -name "*.java" -o -name "*.py" \
  -o -name "*.go" -o -name "*.cs" -o -name "*.rb" \) \
  | grep -v node_modules | grep -v .git | grep -v dist | grep -v target | sort > docs/file-list.txt
```

### 2. Check Packages/Dependencies
```bash
# Detect package manager / build tool
cat package.json 2>/dev/null \
  || cat pom.xml 2>/dev/null \
  || cat build.gradle 2>/dev/null \
  || cat requirements.txt 2>/dev/null \
  || cat go.mod 2>/dev/null \
  || cat Gemfile 2>/dev/null \
  || cat *.csproj 2>/dev/null \
  || echo "[INFO] No package manifest found — check project root manually"
```

### 3. Identify Existing Patterns
```bash
# Adapt search to detected stack
# Frontend (Vue/React/Svelte): grep -r "export default" src/ -l | head -20
# Backend (Java/Spring): grep -r "@RestController" src/ -l | head -20
# Node.js: grep -r "require\|import" src/ --include="*.js" -l | head -10
# Python: grep -r "def \|class " src/ --include="*.py" -l | head -10
```

### 4. Identify Do-Not-Modify Files
- Production config: `config/production`, `.env.production`
- Common utilities: `src/utils/`, `src/store/`
- External integrations: `src/api/`

### 5. Identify Risk Factors
- Files over 500 lines → run context-summary first
- Files with many connections to other files → high change impact
- Files without tests → smoke test required after implementation

## Output: `docs/research-report.md`

```markdown
## Research Report

### Project Stack
- Frontend: [Vue/React/Svelte/Angular/Next.js/etc.]
- Backend: [Spring Boot/Node.js/Python/Go/Ruby/etc.]
- DB: [MSSQL/MySQL/Oracle/PostgreSQL/MongoDB/etc.]

### Related File List
- [file path]: [role]

### Do-Not-Modify Files
- [file path]: [reason]

### Risk Factors
- [risk item]: [mitigation plan]

### Alternative Candidates
1. [Option 1]: [pros and cons]
2. [Option 2]: [pros and cons]
```

## Extension Points
- When parallel exploration with Gemini is needed → call AGENT-03
- Files over 500 lines → save summary in `.claude/context-cache/`
