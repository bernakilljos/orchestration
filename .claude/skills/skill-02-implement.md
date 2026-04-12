# SKILL-02 — Implement (Implementation Execution)

## Purpose
Execute implementation based on task-instruction.md.
Decide between Claude direct handling vs Codex delegation based on the 500-line threshold.

## Decision Criteria

```
Implementation < 500 lines   → Claude direct handling
Implementation >= 500 lines  → Codex delegation
Repetitive pattern generation → Codex delegation
Bulk CRUD generation          → Codex delegation
UI assets needed              → Run SKILL-08 first, then implement
```

## Claude Direct Handling

Read task-instruction.md and implement directly within the allowed scope.

## Codex Delegation

After writing task-instruction.md, request execution from the user:

```
Run in user terminal:
  codex-a --auto                          (with confirmation)
  codex-a --full-auto                     (fully automatic)
  codex-a --auto .claude\tasks\custom.md  (custom task)
```

Direct reference commands:

```bat
codex exec --dangerously-bypass-approvals-and-sandbox "task"
codex exec --full-auto "task"
```

## Additional Procedure for UI Implementation

```
1. Run SKILL-08 → check design reference
2. Copy layouts/ pattern (do not modify)
3. Reuse components/ (do not change structure)
4. Start implementation after confirming HOOK-07 pass
```

## Post-Implementation Check

```bat
rem Vue build/lint
npm run build
npm run lint

rem Spring Boot
mvnw compile
```

## Output: `docs/implementation-report.md`

```markdown
## Implementation Report

### Implementation Details
- [what was implemented]

### Created/Modified Files
- Created: [file list]
- Modified: [file list]

### Acceptance Criteria Achievement
- [ ] [criterion 1]
- [ ] [criterion 2]

### Build Results
- lint: pass/fail
- build: pass/fail
```

## Mandatory Rules for Windows .bat Files

Execute CRLF conversion immediately after creating or modifying a .bat file.
LF (Unix) line endings cause parsing errors in CMD multiline if/for blocks.

```bash
sed -i 's/\r//' "file.bat" && sed -i 's/$/\r/' "file.bat"
```

- Execute the above command immediately after writing/editing .bat files with Write/Edit tools
- Apply the same when other AIs (Codex, etc.) generate .bat files
- When task-instruction.md includes .bat creation instructions, also specify the CRLF conversion command

## Hardcoding Prohibition (Absolute Rule)

This orchestration kit is copied to multiple projects via install.bat.
All code must work universally without modification.

```
STRICTLY PROHIBITED:
  - Absolute paths          (C:\work\myapp, /home/user/app)
  - Hardcoded usernames     (ja205, ec2-user — use %REMOTE_USER%)
  - Hardcoded IPs/hostnames (use %REMOTE_HOST% or config)
  - Hardcoded API keys      (use process.env or %ENV_VAR%)
  - Hardcoded port numbers  (use %SERVICE_PORT% or config)

MUST USE INSTEAD:
  - %~dp0          → script's own directory
  - %TARGET%       → install target path
  - %SCRIPT_DIR%   → orchestration kit source path
  - process.env.*  → environment variables (Node.js)
  - deploy-config.env → server/deployment settings
```

Applies to: skills, hooks, scripts, task-instruction.md, and all generated code.
Violating this rule blocks the quality gate (HOOK-02).

## Korean (UTF-8) Preservation Rules

- Source files may contain UTF-8 Korean text (comments, strings, messages)
- NEVER change, remove, or re-encode Korean strings
- Keep all non-ASCII characters exactly as-is
- Use diff-based edits only — do NOT rewrite entire files containing Korean
- When generating .bat files, always include `chcp 65001 >nul` after `@echo off`
- When task-instruction.md includes Korean, pass it through without modification

## Failure Handling

```
1st failure: Analyze error → fix → retry
2nd failure: Stop → write docs/change-proposal.md → report to Team Lead
```

## 5-Phase Implementation Order

When implementing features, follow this phase order for maximum quality:

### Phase 1 — Setup (DevOps + Architect perspective)
```
- Create/update config files
- Set up folder structure
- Prepare test fixtures and mock data
- Configure environment variables
- Tasks in this phase are parallelizable [P]
```

### Phase 2 — Tests (QA + Security perspective)
```
- Write failing tests FIRST (red phase)
- Define expected behavior before implementation
- Cover: happy path, error path, edge cases
- Skip this phase only for UI-only changes with no logic
```

### Phase 3 — Core Implementation (Frontend/Backend + Architect perspective)
```
- Implement until tests pass (green phase)
- Follow existing code patterns
- One file at a time (Writer=1 rule)
- Frontend: components, pages, store modules
- Backend: controller, service, repository, DTO
```

### Phase 4 — Integration (Backend + Security perspective)
```
- Connect frontend ↔ backend
- Verify API contracts match
- Test authentication/authorization flows
- Verify error handling end-to-end
```

### Phase 5 — Polish (Performance + Refactorer perspective)
```
- Refactor for clarity (rename, extract, simplify)
- Remove dead code and console.log
- Optimize queries and rendering
- Final lint pass
- Do NOT add new features in this phase
```

### Phase Selection
```
Full feature:     All 5 phases
Bug fix:          Phase 2 (reproduce) → Phase 3 (fix) → Phase 5
Refactor:         Phase 2 (safety net) → Phase 5
UI-only:          Phase 3 → Phase 5
Config change:    Phase 1 only
```
