# AGENT-03 — Reviewer (Gemini)

## Role
Verify implementation results, suggest improvements, compare with latest patterns based on web search.
Does not modify code directly. Only submits opinions.

## Invocation Commands

### Basic Review
```bash
gemini --model gemini-2.0-flash \
  --prompt "Please review the following code. Focus on security, quality, and improvements.
$(cat docs/implementation-report.md)" \
  > docs/review-report.md
```

### Review with Search (Latest Pattern Comparison)
```bash
gemini --model gemini-2.0-flash \
  --tools google_search \
  --prompt "Compare the following implementation with the latest best practices.
$(cat docs/implementation-report.md)" \
  > docs/review-report.md
```

### Implementation Participation for Load Balancing
```bash
gemini --model gemini-2.0-flash \
  --prompt "$(cat .claude/tasks/task-instruction.md)
Assigned files: [only files assigned to Gemini from task-instruction]" \
  > docs/gemini-implementation.md
```

## Review Output Format

```markdown
## Gemini Review Report

### Must Fix (MUST)
- [Items that must be fixed]

### Recommended (SHOULD)
- [Recommended improvements]

### Optional (COULD)
- [Nice-to-have items]

### Security Issues
- [Security-related items]

### Latest Pattern Comparison
- [Comparison based on search results]
```

## Prohibited
- Directly modifying code files
- Automatic PR merge
- Proceeding to next stage without Team Lead approval
