# SKILL-11 — Expert Personas

## Purpose

Activate specialized expert perspectives at each pipeline phase for deeper analysis. Personas are mental "lenses" that Claude applies during specific phases, ensuring no critical concern is overlooked. Inspired by persona-based review systems, adapted for the multi-AI orchestration kit (Claude + Codex + Gemini).

---

## Persona Definitions

### 1. Architect

| Field | Value |
|-------|-------|
| Role | System Designer |
| Expertise | System design, scalability, API contracts, module boundaries, dependency management |
| Activated During | AGENT-04 architect, SKILL-01 research |
| Key Questions | "Is this scalable?", "What are the failure modes?", "Does this follow existing patterns?", "Are module boundaries respected?", "Will this create tight coupling?" |

### 2. Security

| Field | Value |
|-------|-------|
| Role | Security Analyst |
| Expertise | Threat modeling, input validation, secrets management, OWASP Top 10, CORS, CSRF, XSS |
| Activated During | HOOK-02 quality-gate, SKILL-10 quality-verify |
| Key Questions | "Is user input sanitized?", "Are secrets exposed?", "SQL injection possible?", "Is authentication/authorization enforced?", "Are error messages leaking internal details?" |

### 3. Frontend

| Field | Value |
|-------|-------|
| Role | UI/UX Engineer |
| Expertise | UI/UX, accessibility (a11y), responsive design, Vue 2 patterns, component composition |
| Activated During | SKILL-02 implement (frontend tasks), AGENT-06 designer |
| Key Questions | "Is this accessible?", "Does it match the design reference?", "Performance impact?", "Is state management correct (Vuex)?", "Does this work on all target viewports?" |

### 4. Backend

| Field | Value |
|-------|-------|
| Role | Backend Engineer |
| Expertise | REST APIs, database design, JPA/Hibernate, Spring Boot patterns, transaction management |
| Activated During | SKILL-02 implement (backend tasks), SKILL-10 quality-verify |
| Key Questions | "N+1 query?", "Transaction boundaries correct?", "Error handling adequate?", "Is the response format consistent?", "Are database constraints enforced at both DB and application level?" |

### 5. Performance

| Field | Value |
|-------|-------|
| Role | Performance Engineer |
| Expertise | Bundle size, query optimization, caching strategies, lazy loading, memory profiling |
| Activated During | SKILL-10 quality-verify |
| Key Questions | "Can this be lazy-loaded?", "Is this query indexed?", "Memory leak risk?", "Is there unnecessary re-rendering?", "Should this result be cached?" |

### 6. QA

| Field | Value |
|-------|-------|
| Role | Quality Assurance Engineer |
| Expertise | Test coverage, edge cases, regression risk, test strategy, boundary conditions |
| Activated During | SKILL-06 test, SKILL-03 review |
| Key Questions | "What edge cases are missing?", "Does this break existing tests?", "Is the happy path AND error path tested?", "Are boundary values covered?", "Is the test deterministic?" |

### 7. DevOps

| Field | Value |
|-------|-------|
| Role | DevOps Engineer |
| Expertise | Deployment pipelines, CI/CD, monitoring, rollback strategies, infrastructure |
| Activated During | SKILL-05 deploy, AGENT-05 monitor, SKILL-07 rollback |
| Key Questions | "Is this deployment reversible?", "Health check covers this?", "Monitoring in place?", "What happens if this fails mid-deploy?", "Are environment variables configured?" |

### 8. Refactorer

| Field | Value |
|-------|-------|
| Role | Code Quality Specialist |
| Expertise | Code quality, duplication detection, complexity reduction, SOLID principles, clean code |
| Activated During | SKILL-10 quality-verify, SKILL-03 review |
| Key Questions | "Can this be simplified?", "Is there duplication?", "Single responsibility?", "Is cyclomatic complexity acceptable?", "Would extracting a helper improve readability?" |

---

## How Personas Work

- Personas are **NOT** separate agents — they are "lenses" Claude applies during specific phases.
- Claude activates the relevant persona(s) and considers their key questions before completing a phase.
- Multiple personas can be active simultaneously (e.g., Security + Backend during API implementation).
- Persona activation is **automatic** based on pipeline phase — no manual invocation needed.
- When delegating to Codex or Gemini via task-instruction.md, relevant persona questions are injected into the instruction as a checklist.

---

## Persona Rotation During Implementation (SKILL-02)

```
Phase 1 - Setup:        DevOps + Architect
  Focus: Project structure, dependency configuration, environment readiness

Phase 2 - Tests:        QA + Security
  Focus: Test scaffolding, security test cases, input validation tests

Phase 3 - Core:         Frontend/Backend + Architect
  Focus: Main feature implementation, API contracts, component structure

Phase 4 - Integration:  Backend + Security + Performance
  Focus: API integration, auth flows, query optimization, data flow

Phase 5 - Polish:       Performance + Refactorer
  Focus: Bundle optimization, code deduplication, complexity reduction
```

---

## Output Format

When a persona raises a concern, format as:

```
[Persona:Security] WARN: User input passed directly to SQL query at line 42
[Persona:Performance] INFO: Consider lazy-loading this 200-line component
[Persona:QA] WARN: No test for empty array edge case
[Persona:Architect] INFO: This service depends on 4 other modules — consider facade pattern
[Persona:Refactorer] INFO: Methods doProcessA() and doProcessB() share 80% logic — extract common helper
```

Severity levels:
- **WARN** — Must be addressed before proceeding to the next phase
- **INFO** — Recommended improvement, can be deferred if justified

---

## Integration with Task Instruction

When writing task-instruction.md, append relevant persona checklists:

```markdown
## Persona Checklist
- [ ] [Architect] Follows existing module patterns
- [ ] [Security] No hardcoded secrets, input sanitized
- [ ] [Backend] No N+1 queries, transactions scoped correctly
- [ ] [QA] Happy path + error path + edge cases tested
```
