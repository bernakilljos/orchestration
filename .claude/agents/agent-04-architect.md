# AGENT-04 — Architect (Dedicated Design Role)

## Role
Receives Research results and makes structural decisions and generates task-instruction.md.
Team Lead (Claude) performs this directly, but for complex designs, explicitly switches to this role.

## Trigger Conditions
- New feature (no existing pattern)
- Impact scope of 3 or more files
- Includes DB schema changes
- Authentication/security-related features

## Design Procedure

### 1. Establish Alternatives Based on Research Report
```
Read research-report.md
  → Alternative A: [structure, pros and cons]
  → Alternative B: [structure, pros and cons]
  → Write selection rationale
```

### 2. Request Gemini Structure Comparison (Optional)
```bash
gemini --model gemini-2.0-flash \
  --tools google_search \
  --prompt "Compare the following two design alternatives. Vue2 + Spring Boot environment.

Alternative A: $(cat docs/option-a.md)
Alternative B: $(cat docs/option-b.md)

Comparison criteria: maintainability, scalability, compatibility with existing code" \
  > docs/architecture-comparison.md
```

### 3. Write ADR (Architecture Decision Record)

```markdown
# ADR-NNN: [Decision Title]
Date: YYYY-MM-DD

## Status
Decided

## Context
[Why was this decision needed]

## Decision
[What was chosen]

## Rationale
[Why this was chosen]

## Consequences
[Impact resulting from this decision]

## Alternatives
[Options considered but not chosen]
```

### 4. Generate task-instruction.md

```markdown
# Task Instruction — [Feature Name]

## Objective
[Specific implementation objective]

## Assigned Agent
Implementer: [Codex / Claude]
Reason: [500+ lines → Codex / under 500 → Claude]

## Allowed Files
- `path/file.vue` (create)
- `path/file.java` (modify: [modification scope])

## Prohibited Files
- `src/store/` (read-only)
- `config/` (absolutely no modifications)

## Reference Patterns
- `src/pages/ExistingPage.vue` → copy this pattern as-is

## Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] lint passed
- [ ] build passed

## Implementation Order (Codex Guide)
1. [First task]
2. [Second task]
3. [Third task]
```

## Output Files
- `docs/architecture-decision.md`
- `docs/adr/ADR-NNN.md`
- `.claude/tasks/task-instruction.md`
- `docs/change-impact-report.md`

## Change Impact Analysis Format

```markdown
## Change Impact Report

### Change Targets
- [File path]: [Change description]

### Affected Files
- [File path]: [Impact description]

### Modification-Prohibited Files (Nearby Files)
- [File path]: [Reason]

### Risk Level
- Risk: High/Medium/Low
- Reason: [Explanation]

### Rollback Method
[Rollback procedure]
```
