# SKILL-09 - Memory Reset (Session Interruption/Recovery)

## Purpose
When a session is interrupted or context exceeds 80%,
save the current state to a file so the next session can resume exactly where it left off.

---

## Auto-Trigger Conditions

| Condition | Action |
|-----------|--------|
| Context 80% or above detected | Save snapshot + recommend /reset |
| Pipeline step completed | Save checkpoint |
| User requests "save and disconnect" / "/reset" | Immediately save snapshot |

---

## STEP 1 - Save Snapshot

Save to `.claude/context-cache/session-snapshot.md` in the following format:

```markdown
## Session Snapshot - [YYYY-MM-DD HH:MM]

### Current Task
- Title: [task title]
- Goal: [what is being implemented]
- task-instruction.md: .claude/tasks/task-instruction.md

### Pipeline Progress Status
- [x] HOOK-01 pre-task
- [x] SKILL-01 research
- [x] SKILL-02 implement (Codex complete)
- [ ] SKILL-03 review (next step)
- [ ] HOOK-02 quality-gate
- [ ] SKILL-05 deploy

### Next Command to Execute
gemini-a --verify

### Modified Files
- src/pages/NewPage.vue (newly created)
- src/router/index.js (router registration)

### Key Decisions
- API endpoint: /api/v1/[endpoint]
- Component pattern: reference ReferencePage.vue
- Environment variable: process.env.VUE_APP_API_URL

### Pending Items / Cautions
- Gemini review results not yet adopted
- [other cautions]

### Reference Files (need to reload)
.claude/skills/skill-01-research.md
.claude/skills/skill-02-implement.md
.claude/skills/skill-03-review.md
.claude/hooks/hook-02-post-impl.md
```

---

## STEP 2 - User Guidance

```
[SKILL-09] Context limit reached - Snapshot saved
Save location: .claude/context-cache/session-snapshot.md

Next step: gemini-a --verify

To resume in a new session:
  After /reset, restart Claude and it will auto-recover.
```

---

## On New Session Start - Auto Recovery

When Claude starts fresh, it checks the following according to CLAUDE.md loading order:

```
1. Check if .claude/context-cache/session-snapshot.md exists
2. If exists: output snapshot content summary
   - Current task
   - Completed steps
   - Next command to execute
3. Ask user "Shall we continue from where we left off?"
4. Upon approval: resume from the next step
```

Recovery output example:
```
[Recovery] Previous session snapshot found
  Task:      [task title]
  Completed: research, implement
  Next:      gemini-a --verify
  Shall we continue?
```

---

## Checkpoint Save Timing (Per Pipeline Step)

| After Step Completion | Saved Content |
|----------------------|---------------|
| HOOK-01 pre-task | Task registration complete, locked file list |
| SKILL-01 research | Analysis results summary, risk factors |
| Codex execution complete | Implemented file list, next=gemini-a --verify |
| Gemini review complete | Review results summary, awaiting Claude adoption decision |
| HOOK-04 pre-deploy | Pre-deployment state |

---

## Snapshot Cleanup

Auto-cleanup in HOOK-05 post-deploy after successful deployment:
```bat
del .claude\context-cache\session-snapshot.md
```
