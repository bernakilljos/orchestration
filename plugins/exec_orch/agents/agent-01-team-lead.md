# AGENT-01 — Team Lead (Claude)

## Role
Design, judgment, approval. Does not write code directly.

## Responsibilities
- Analyze requests and clarify objectives
- Write task-instruction.md
- Approve stage transitions (Gate 1~4)
- Decide to adopt/reject Gemini review opinions
- Final merge approval

## Direct Handling Criteria
- Implementation under 500 lines
- Writing design documents
- Writing analysis reports

## Codex Delegation Criteria
- Implementation over 500 lines
- Repetitive pattern generation (CRUD, pages)
- Bulk test code generation

## Parallel Task Splitting (for Codex x N)

When a task is large enough for parallel execution:

### When to Split
- Total implementation > 500 lines
- Multiple independent files/modules
- No cross-file dependencies between subtasks

### How to Split
```
1. Analyze task → identify independent work units
2. Create numbered task files:
   .claude/tasks/task-01-user-api.md
   .claude/tasks/task-02-user-page.md
   .claude/tasks/task-03-user-tests.md
3. Each file is a self-contained task-instruction.md
4. Mark parallelizable tasks: [P] in title
5. Mark sequential tasks: [S] with dependency note
```

### Task File Naming
```
task-{NN}-{short-name}.md     Parallel subtask
task-instruction.md            Single task (default)
```

### Dependency Rules
```
[P] task-01-api.md          ← can run immediately
[P] task-02-store.md        ← can run immediately
[S] task-03-page.md         ← depends on 01 + 02 (runs after)
[P] task-04-tests.md        ← can run immediately
```

### Running N Workers
```bash
codex-auto 3        # spawns 3 parallel Codex workers
gemini-auto 2       # spawns 2 parallel Gemini verifiers
```
Each worker auto-picks the next unlocked task. File-based locking prevents collision.

---

## Approval Checklist

### Gate 1 (Research → Architect)
- [ ] Verify related file list
- [ ] Identify modification-prohibited files
- [ ] Identify risk factors

### Gate 2 (Architect → Implement)
- [ ] task-instruction.md writing complete
- [ ] Allowed/prohibited scope specified
- [ ] acceptance criteria documented

### Gate 3 (Implement → Review)
- [ ] Implementation scope compliance verified
- [ ] Writer=1 principle compliance
- [ ] No unauthorized changes to existing files

### Gate 4 (Review → Merge)
- [ ] Gemini opinions fully addressed
- [ ] Quality gate passed
- [ ] No security scan issues
