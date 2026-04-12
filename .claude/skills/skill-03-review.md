# SKILL-03 — Review (Verification & Enhancement)

## Purpose
Verify implementation results with Gemini and collect improvement points.
Team Lead decides whether to adopt the findings.

## Basic Review Call

```bash
gemini --model gemini-2.0-flash \
  --prompt "Review the following implementation results.

[task-instruction]
$(cat .claude/tasks/task-instruction.md)

[implementation]
$(cat docs/implementation-report.md)

Review items:
1. Security issues (OWASP standards)
2. Code quality (readability, maintainability)
3. Performance issues
4. Missing features
5. Improvement recommendations

Output format:
MUST: [must be applied]
SHOULD: [recommended to apply]
COULD: [optional to apply]
SECURITY: [security issues]" \
  > docs/review-report.md
```

## In-Depth Review with Search

```bash
gemini --model gemini-2.0-flash \
  --tools google_search \
  --prompt "Compare whether the following implementation aligns with 2025 best practices.
$(cat docs/implementation-report.md)" \
  >> docs/review-report.md
```

## Security-Only Scan

```bash
# Secret scan
grep -rE "(password|secret|api_key|token)\s*=\s*['\"][^'\"]{5,}" \
  src/ --include="*.js" --include="*.vue" --include="*.java" \
  | grep -v "process.env" | grep -v "config\." \
  > docs/security-report.md

# Gemini security review
gemini --model gemini-2.0-flash \
  --prompt "Find security vulnerabilities in the following code. Based on OWASP Top 10.
$(cat src/pages/NewPage.vue)" \
  >> docs/security-report.md
```

## Team Lead Adoption Decision Format

Read the review results and decide using the following format:

```markdown
## Review Adoption Decision

### Adopted (Request Codex to Apply)
- [adopted items from MUST]

### Rejected (with reasons)
- [rejected item]: [reason]

### Next Steps
- [ ] Instruct Codex to fix adopted items
- [ ] Re-review needed: Y/N
```

## Korean (UTF-8) Preservation
- When reviewing files containing Korean text, do NOT flag Korean strings as issues
- Do NOT suggest re-encoding or modifying Korean characters
- Review diffs must preserve all non-ASCII characters exactly as-is

## Extension Points
- High complexity features: repeat review 2 times
- Security-sensitive features: add security-only scan
- New technology adoption: in-depth review with search required
