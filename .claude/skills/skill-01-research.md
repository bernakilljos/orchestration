# SKILL-01 — Research (Exploration & Analysis)

## Purpose
Understand the project structure and identify risk points before implementation.

## Execution Order

### 1. Understand Project Structure
```bash
find . -type f \( -name "*.vue" -o -name "*.js" -o -name "*.java" -o -name "*.ts" \) \
  | grep -v node_modules | grep -v .git | sort > docs/file-list.txt
```

### 2. Check Packages/Dependencies
```bash
cat package.json 2>/dev/null || cat pom.xml 2>/dev/null || cat build.gradle 2>/dev/null
```

### 3. Identify Existing Patterns
```bash
# Vue project example
grep -r "export default" src/ --include="*.vue" -l | head -20
grep -r "axios\|fetch\|api" src/ --include="*.js" -l | head -10
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
- Frontend: [Vue2/Vue3/React]
- Backend: [Spring Boot/Node]
- DB: [MSSQL/MySQL/Oracle]

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
